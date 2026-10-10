"""Conservative GitHub Release transport; dry runs never call GitHub.

Only standard-library Python and the existing authenticated GitHub CLI are used.
Every source path and all private state stay outside the public catalog fields.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import math
import mimetypes
import re
import subprocess
import time
import urllib.parse
import uuid
from pathlib import Path

import core

TASK_MARKER = "simpack-local-publish-v1"
MAX_ASSETS = 1000
SUFFIXES = (".zh-CN.srt", ".zh-CN.vtt", ".en.srt", ".en.vtt")
RETRIES = 3
READ_TIMEOUT = 60
UPLOAD_TIMEOUT = 3600


class ReleaseError(RuntimeError):
    pass


class GHError(ReleaseError):
    def __init__(self, status=None, headers=None, code=None):
        self.status = status
        self.headers = headers or {}
        self.code = code
        # Deliberately exclude stderr, request bodies, credentials and local paths.
        super().__init__(f"GitHub CLI request failed (HTTP {status or 'unknown'}, exit {code})")

    @property
    def transient(self):
        return self.code == "invalid_response" or self.status in (408, 429, 500, 502, 503, 504) or self.status is None or (
            self.status == 403 and (self.headers.get("x-ratelimit-remaining") == "0" or
                                    "retry-after" in self.headers))


class RetryDeferred(ReleaseError):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__(f"Server Retry-After requires waiting {math.ceil(seconds)} seconds; request deferred without an early retry")


def _delay(error, attempt):
    value = error.headers.get("retry-after")
    try:
        delay = float(value)
    except (TypeError, ValueError):
        try:
            from email.utils import parsedate_to_datetime
            delay = (parsedate_to_datetime(value) - dt.datetime.now(dt.timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            delay = 2 ** attempt
    if not math.isfinite(delay):
        delay = 2 ** attempt
    if delay > 60:
        raise RetryDeferred(delay)
    return max(0.0, delay)


def _response(data):
    """Parse gh api --include response headers without retaining sensitive output."""
    raw = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    status, headers = None, {}
    while raw.startswith("HTTP/"):
        head, separator, raw = raw.partition("\n\n")
        if not separator:
            raw = ""
        first, *lines = head.splitlines()
        match = re.match(r"HTTP/\S+\s+(\d+)", first)
        status = int(match.group(1)) if match else None
        headers = {k.strip().lower(): v.strip() for line in lines if ":" in line
                   for k, v in [line.split(":", 1)]}
    try:
        body = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        body = None
    return status, headers, body


class GHClient:
    """A test-replaceable CLI adapter. All commands are arrays with shell=False."""
    def _binary_download_options(self):
        cached = getattr(self, "_download_options", None)
        if cached is not None:
            return cached
        try:
            result = subprocess.run(["gh", "api", "--help"], shell=False, capture_output=True,
                                    check=False, timeout=READ_TIMEOUT)
        except (OSError, subprocess.TimeoutExpired):
            raise ReleaseError("Cannot inspect GitHub CLI binary-download capabilities")
        help_text = result.stdout.decode("utf-8", errors="replace")
        if result.returncode or "gh api" not in help_text or "--header" not in help_text:
            raise ReleaseError("Cannot inspect GitHub CLI binary-download capabilities")
        # New gh versions otherwise reject/alter non-JSON control bytes. Older
        # versions must not receive a flag that they do not support. This option
        # is used only with stdout bound to an exclusive private file.
        self._download_options = ["--allow-escape-sequences"] if re.search(
            r"(?m)^\s+--allow-escape-sequences\b", help_text) else []
        return self._download_options

    def auth(self):
        try:
            result = subprocess.run(["gh", "auth", "status", "--hostname", "github.com"],
                                    shell=False, capture_output=True, check=False, timeout=READ_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ReleaseError("GitHub authentication status check timed out")
        if result.returncode:
            raise ReleaseError("GitHub CLI is not authenticated; run gh auth login --hostname github.com --web")

    def request(self, endpoint, method="GET", payload=None, source=None, content_type=None):
        args = ["gh", "api", endpoint, "--hostname", "github.com", "--include", "--method", method,
                "--header", "Accept: application/vnd.github+json",
                "--header", "X-GitHub-Api-Version: 2026-03-10"]
        input_bytes = None
        if source is not None:
            args += ["--input", str(source), "--header", f"Content-Type: {content_type or 'application/octet-stream'}"]
        elif payload is not None:
            args += ["--input", "-", "--header", "Content-Type: application/json"]
            input_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            result = subprocess.run(args, input=input_bytes, shell=False, capture_output=True, check=False,
                                    timeout=UPLOAD_TIMEOUT if source is not None else READ_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise GHError(code="timeout")
        status, headers, body = _response(result.stdout)
        if status is None and result.returncode:
            # gh may print HTTP failures only to stderr. Extract only the number;
            # never log/store the raw message or command arguments.
            match = re.search(r"\bHTTP\s+(\d{3})\b", result.stderr.decode("utf-8", errors="replace"))
            if match:
                status = int(match.group(1))
        if result.returncode or status is None or status >= 400:
            raise GHError(status, headers, result.returncode)
        if not isinstance(body, (dict, list)):
            # A successful write may have completed even when its response is
            # truncated or malformed. Callers reconcile remote state before retry.
            raise GHError(status, headers, "invalid_response")
        return body

    def download(self, repository, asset_id, target):
        if not isinstance(asset_id, int) or asset_id <= 0:
            raise ReleaseError("Invalid remote asset ID")
        args = ["gh", "api", f"repos/{repository}/releases/assets/{asset_id}", "--hostname", "github.com",
                "--header", "Accept: application/octet-stream"]
        args += self._binary_download_options()
        # No shell redirection; an exclusively-created, private local file receives bytes.
        with target.open("xb") as output:
            try:
                result = subprocess.run(args, stdout=output, stderr=subprocess.PIPE, shell=False, check=False, timeout=UPLOAD_TIMEOUT)
            except subprocess.TimeoutExpired:
                raise GHError(code="timeout")
        if result.returncode:
            raise GHError(code=result.returncode)


def _get(client, endpoint, optional=False):
    for attempt in range(RETRIES):
        try:
            return client.request(endpoint)
        except GHError as error:
            if optional and error.status == 404:
                return None
            if not error.transient or attempt == RETRIES - 1:
                raise
            time.sleep(_delay(error, attempt))


def list_assets(client, repository, release_id):
    if not isinstance(release_id, int) or release_id <= 0:
        raise ReleaseError("Invalid Release ID")
    result, page = [], 1
    while True:
        batch = _get(client, f"repos/{repository}/releases/{release_id}/assets?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ReleaseError("Invalid paginated asset response")
        result.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 100:
            raise ReleaseError("Remote asset listing exceeded safety limit")
    names = [item.get("name") for item in result]
    if len(names) != len(set(names)):
        raise ReleaseError("Remote Release contains duplicate attachment names")
    if len(result) > MAX_ASSETS:
        raise ReleaseError("Remote Release exceeds 1000 attachments")
    return result


def _repository(work):
    github = work.config.get("github", {})
    owner, name = github.get("owner"), github.get("repository")
    if not isinstance(owner, str) or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", owner):
        raise ReleaseError("Set the GitHub owner from the authenticated GitHub identity")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ReleaseError("Invalid configured GitHub repository name")
    commit = github.get("commit_sha") or work.config.get("commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ReleaseError("An explicit pushed 40-character commit SHA is required")
    return f"{owner}/{name}", commit.lower()


def _authorization(work, identifier, selected):
    if work.config.get("github", {}).get("allow_remote_write") is not True:
        raise ReleaseError("Remote writes are disabled; Stage A only permits local preparation")
    repository, commit = _repository(work)
    authorization = work.read_json("authorization.json", {})
    if not identifier or identifier != authorization.get("authorization_id") or authorization.get("confirmed") is not True:
        raise ReleaseError("A matching explicit Stage B authorization record is required")
    try:
        issued = dt.datetime.fromisoformat(authorization["issued_at"].replace("Z", "+00:00"))
        expires = dt.datetime.fromisoformat(authorization["expires_at"].replace("Z", "+00:00"))
        now = dt.datetime.now(dt.timezone.utc)
        valid_time = (issued.tzinfo is not None and expires.tzinfo is not None and
                      issued <= now < expires and issued < expires)
    except (KeyError, TypeError, ValueError):
        valid_time = False
    if not valid_time:
        raise ReleaseError("Authorization is expired, future-dated or lacks timezone-aware validity dates")
    authorized_series = authorization.get("series", [])
    if not isinstance(authorized_series, list) or not authorized_series or any(s not in core.SERIES for s in authorized_series):
        raise ReleaseError("Authorization must enumerate the original series IDs")
    if not set(selected).issubset(authorized_series):
        raise ReleaseError("Requested series exceed the explicitly authorized scope")
    materials = authorization.get("materials", [])
    if not isinstance(materials, list) or not materials or not set(materials).issubset({"video", "zh-CN", "en"}):
        raise ReleaseError("Authorization must explicitly enumerate upload materials")
    if (authorization.get("repository") != repository or authorization.get("commit_sha", "").lower() != commit or
            authorization.get("rights_confirmed") is not True):
        raise ReleaseError("Authorization does not match repository, commit or confirmed rights")
    visibility = authorization.get("visibility")
    if visibility not in ("private", "public"):
        raise ReleaseError("Authorization must explicitly state repository visibility")
    if visibility == "public" and work.config.get("github", {}).get("allow_make_public") is not True:
        raise ReleaseError("Public publication needs a separate explicit public authorization")
    exclusions = authorization.get("excluded_assets", {})
    if not isinstance(exclusions, dict) or any(not isinstance(reason, str) or not reason.strip() for reason in exclusions.values()):
        raise ReleaseError("Partial-publication exclusions must map exact attachment names to explicit reasons")
    inventory = work.read_json("inventory.json", {})
    known = {item.get("asset_name") for episode in inventory.get("episodes", []) if episode.get("series_id") in authorized_series
             for item in [episode.get("video", {}), *episode.get("subtitles", {}).values()]}
    if any(name not in known for name in exclusions):
        raise ReleaseError("Excluded attachment names are not exact inventory names within the authorized series")
    if "approved_existing_asset_names" in authorization:
        approved = authorization["approved_existing_asset_names"]
        if (not isinstance(approved, list) or not approved or
                any(not isinstance(name, str) or not name.strip() for name in approved) or
                len(approved) != len(set(approved))):
            raise ReleaseError("Explicit approved attachment names must be a nonempty unique filename list")
    return authorization, repository, commit


def _preflight(client, repository, commit, authorization):
    client.auth()
    user = _get(client, "user")
    owner, name = repository.split("/")
    if user.get("login", "").casefold() != owner.casefold():
        raise ReleaseError("Authenticated GitHub account differs from the configured repository owner")
    remote = _get(client, f"repos/{repository}")
    if (remote.get("owner", {}).get("login", "").casefold() != owner.casefold() or remote.get("name") != name):
        raise ReleaseError("GitHub repository identity does not match configuration")
    visibility = "private" if remote.get("private") is True else "public"
    if visibility != authorization["visibility"]:
        raise ReleaseError("Repository visibility differs from this authorization; visibility is never changed automatically")
    resolved = _get(client, f"repos/{repository}/commits/{commit}")
    if resolved.get("sha", "").lower() != commit:
        raise ReleaseError("Explicit target commit is not present on the configured repository")
    provenance = _get(client, f"repos/{repository}/contents/PROVENANCE.md?ref={commit}")
    try:
        content = base64.b64decode(provenance["content"], validate=False).decode("utf-8")
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        raise ReleaseError("Cannot verify this task's committed provenance marker")
    if provenance.get("encoding") != "base64" or TASK_MARKER not in content.splitlines():
        raise ReleaseError("Remote repository lacks this task's committed provenance marker; no write is permitted")


def _tag_commit(client, repository, tag):
    reference = _get(client, f"repos/{repository}/git/ref/tags/{tag}", optional=True)
    if reference is None:
        return None
    obj = reference.get("object", {})
    for _ in range(5):
        if obj.get("type") == "commit":
            return obj.get("sha", "").lower()
        if obj.get("type") != "tag" or not re.fullmatch(r"[0-9a-fA-F]{40}", obj.get("sha", "")):
            break
        obj = _get(client, f"repos/{repository}/git/tags/{obj['sha']}").get("object", {})
    raise ReleaseError("Tag target cannot be resolved safely to a commit")


def _release(client, repository, commit, series_id, create, require_draft=True):
    tag = f"series-{series_id}-v1"
    target = _tag_commit(client, repository, tag)
    if target is not None and target != commit:
        raise ReleaseError(f"Existing tag {tag} targets another commit; no tag rewriting is permitted")
    remote = _get(client, f"repos/{repository}/releases/tags/{tag}", optional=True)
    if remote is None:
        if not create:
            return None
        payload = {"tag_name": tag, "target_commitish": commit, "name": f"系列 {series_id}",
                   "body": TASK_MARKER + "\n\n附件清单以已授权且已核验的资料为准。", "draft": True, "prerelease": False}
        try:
            remote = client.request(f"repos/{repository}/releases", method="POST", payload=payload)
        except GHError as error:
            # A lost creation response is reconciled before any retry or further mutation.
            remote = _get(client, f"repos/{repository}/releases/tags/{tag}", optional=True)
            if remote is None:
                raise error
    if remote.get("tag_name") != tag or TASK_MARKER not in (remote.get("body") or "").splitlines():
        raise ReleaseError(f"Release {tag} is not marked as this task's Release")
    if require_draft and (remote.get("draft") is not True or remote.get("immutable") is True):
        raise ReleaseError(f"Release {tag} is published or immutable; prepare a new version instead")
    target_after = _tag_commit(client, repository, tag)
    if target_after is not None and target_after != commit:
        raise ReleaseError("Release tag changed during preflight")
    if target_after is None and remote.get("target_commitish", "").lower() != commit:
        raise ReleaseError("Draft Release does not point to the explicit authorized commit")
    return remote


def _upload_url(remote, repository, name, label):
    value = remote.get("upload_url", "").split("{", 1)[0]
    parsed = urllib.parse.urlsplit(value)
    expected = f"/repos/{repository}/releases/{remote['id']}/assets"
    if (parsed.scheme != "https" or parsed.netloc != "uploads.github.com" or parsed.path != expected or
            parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ReleaseError("GitHub returned an unexpected upload URL; refusing to send source bytes")
    return value + "?" + urllib.parse.urlencode({"name": name, "label": label})


def _selection(work, series, limit):
    selected = tuple(core.select_series(series))
    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0):
        raise ReleaseError("--limit must be a positive number of complete lesson groups")
    inventory = work.read_json("inventory.json", {})
    episodes = [e for e in inventory.get("episodes", []) if e.get("series_id") in selected]
    # The inventory already records its stable natural ordering; never sort by numeric prefix alone.
    if limit is not None:
        # --limit counts whole lessons whose video can actually participate in a trial.
        episodes = [e for e in episodes if _trial_eligible(e)][:limit]
    return selected, episodes


def _trial_eligible(episode, exclusions=()):
    video = episode.get("video", {})
    if video.get("status") in ("missing", "invalid", "unreadable", "zero_byte", "blocked_reparse") or not (
            0 < (video.get("size_bytes") or 0) < core.MAX_BYTES):
        return False
    return not any(data.get("asset_name") not in exclusions and data.get("status") in ("invalid", "unreadable", "zero_byte", "blocked_reparse")
                   for data in episode.get("subtitles", {}).values())


def _unusable_present(episodes, materials):
    result = []
    for episode in episodes:
        for suffix, data, material in [("", episode.get("video", {}), "video")] + [
                (s, episode.get("subtitles", {}).get(s, {}), "zh-CN" if s.startswith(".zh-CN") else "en") for s in SUFFIXES]:
            if material not in materials or data.get("status") == "missing":
                continue
            status, size = data.get("status"), data.get("size_bytes") or 0
            if status in ("invalid", "unreadable", "zero_byte", "blocked_reparse") or size <= 0 or size >= core.MAX_BYTES:
                result.append({"asset_name": data.get("asset_name") or episode["episode_id"] + (suffix or ".mp4"),
                               "reason": "blocked_oversize" if size >= core.MAX_BYTES else status or "zero_byte"})
    return result


def _candidates(episodes):
    result = []
    for episode in episodes:
        video = episode.get("video", {})
        for suffix, data, material in [("", video, "video")] + [
                (s, episode.get("subtitles", {}).get(s, {}), "zh-CN" if s.startswith(".zh-CN") else "en") for s in SUFFIXES]:
            if not data or data.get("status") in ("missing", "invalid", "unreadable", "zero_byte", "blocked_reparse"):
                continue
            asset = {"episode_id": episode["episode_id"], "series_id": episode["series_id"], "material": material,
                     "suffix": suffix, "name": data.get("asset_name") or episode["episode_id"] + (suffix or ".mp4"),
                     "label": episode.get("title", episode["episode_id"]) + suffix, "data": data,
                     "relative_path": data.get("relative_path") or (episode.get("relative_path") if not suffix else None)}
            size = data.get("size_bytes", 0)
            asset["blocked"] = ("blocked_oversize" if size >= core.MAX_BYTES else "zero_byte" if size <= 0 else None)
            result.append(asset)
    names = [a["name"] for a in result]
    if len(names) != len(set(names)):
        raise ReleaseError("Local attachment names collide; repair the stable ID mapping")
    return result


def _path(work, asset):
    root = Path(work.config["video_root" if asset["material"] == "video" else "subtitle_root"])
    data = asset["data"]
    if data.get("path"):
        try:
            relative = Path(data["path"]).relative_to(root)
        except ValueError:
            raise ReleaseError("Inventory source path lies outside the configured read-only root")
    else:
        relative = asset["relative_path"]
    if relative is None:
        raise ReleaseError("Inventory source relative path is missing")
    return core.safe_source(root, relative)


def _hash_asset(work, asset, force=False):
    source = _path(work, asset)
    before = source.stat()
    if before.st_size != asset["data"]["size_bytes"] or before.st_mtime_ns != asset["data"]["mtime_ns"]:
        raise ReleaseError("Source changed since the inventory scan; run scan/build before upload")
    if before.st_size <= 0 or before.st_size >= core.MAX_BYTES:
        raise ReleaseError("Asset size is zero or not strictly below 2 GiB")
    cache = work.read_json("source_hash_cache.json", {})
    key = str(source)
    cached = cache.get(key, {})
    metadata = {"size_bytes": before.st_size, "mtime_ns": before.st_mtime_ns}
    actual_run = getattr(work, "_release_actual_hashes", {})
    same = all(cached.get(k) == v for k, v in metadata.items()) and bool(re.fullmatch(r"[0-9a-f]{64}", cached.get("sha256", "")))
    same_run = actual_run.get(key) == cached
    if same and (not force or same_run):
        digest = cached["sha256"]
        origin = "current_run_source_sha256" if same_run else "cached_source_sha256_metadata_unchanged"
    else:
        digest, origin = core.sha256(source), "source_sha256_computed"
        cached = {**metadata, "sha256": digest, "computed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        cache[key] = cached
        actual_run[key] = cached
        work._release_actual_hashes = actual_run
        work.write_json("source_hash_cache.json", cache)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ReleaseError("Source changed during SHA-256 hashing")
    if asset["material"] != "video" and asset["data"].get("sha256") not in (None, digest):
        raise ReleaseError("Subtitle SHA-256 differs from the inventory")
    asset.update(source=source, sha256=digest, sha256_origin=origin, size_bytes=before.st_size, mtime_ns=before.st_mtime_ns)
    return asset


def compare_asset(remote, local_hash, local_size, previous=None):
    if remote.get("state") != "uploaded" or remote.get("size") != local_size:
        return "conflict"
    digest = remote.get("digest")
    if digest:
        return "verified" if digest == "sha256:" + local_hash else "conflict"
    if (previous and previous.get("verification") == "download_verified" and previous.get("asset_id") == remote.get("id") and
            previous.get("sha256") == local_hash and previous.get("download_sha256") == local_hash and previous.get("size_bytes") == local_size):
        return "verified"
    return "metadata_only"


def _state(work):
    state = work.read_json("upload_state.json", {})
    for key in ("assets", "releases", "trial_gates"):
        state.setdefault(key, {})
        if not isinstance(state[key], dict):
            raise ReleaseError(f"Invalid existing upload state field: {key}")
    return state


def _state_key(repository, name):
    return repository + "/" + name


def _record(state, repository, remote_release, asset, remote, status, verification, error=None):
    previous = state["assets"].get(_state_key(repository, asset["name"]), {})
    record = {"episode_id": asset["episode_id"], "series_id": asset["series_id"], "material": asset["material"],
              "source_path": str(asset["source"]), "size_bytes": asset["size_bytes"], "mtime_ns": asset["mtime_ns"],
              "sha256": asset["sha256"], "sha256_origin": asset["sha256_origin"], "release_id": remote_release["id"], "asset_id": remote.get("id") if remote else None,
              "remote_name": remote.get("name") if remote else None, "status": status, "verification": verification,
              "browser_download_url": remote.get("browser_download_url") if remote else None,
              "release_url": remote_release.get("html_url"), "draft": remote_release.get("draft"),
              "visibility": state.get("visibility"), "error": error,
              "source_metadata_after": {"size_bytes": asset["source"].stat().st_size, "mtime_ns": asset["source"].stat().st_mtime_ns}}
    if previous.get("verification") == "download_verified" and verification == "download_verified":
        record["download_sha256"] = previous.get("download_sha256")
    state["assets"][_state_key(repository, asset["name"])] = record
    return record


def _rights(work, assets, materials):
    rights = work.read_json("rights.json", {})
    records = rights.get("episodes", {})
    unknown = [a["name"] for a in assets if a["material"] in materials and not a["blocked"] and
               records.get(a["episode_id"], {}).get(a["material"], rights.get("default", "unknown")) != "confirmed"]
    if unknown:
        raise ReleaseError("Rights are not confirmed for: " + ", ".join(unknown))


def _approved_assets(authorization, assets):
    """A rescan must not widen an explicit snapshot of authorized filenames."""
    if "approved_existing_asset_names" not in authorization:
        return
    approved = set(authorization["approved_existing_asset_names"])
    unapproved = sorted({asset["name"] for asset in assets if asset["name"] not in approved})
    if unapproved:
        raise ReleaseError("Attachment names exceed the explicit approved filename scope: " + ", ".join(unapproved))


def _gate_key(authorization, repository, commit):
    identity = {"authorization_id": authorization["authorization_id"], "repository": repository, "commit_sha": commit,
                "series": sorted(authorization["series"]), "materials": sorted(authorization["materials"]),
                "excluded_assets": authorization.get("excluded_assets", {})}
    if "approved_existing_asset_names" in authorization:
        identity["approved_existing_asset_names"] = sorted(authorization["approved_existing_asset_names"])
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def _trial_assets(work, authorization):
    first_series = next(s for s in core.SERIES if s in authorization["series"])
    _, lessons = _selection(work, first_series, None)
    for lesson in lessons:
        exclusions = authorization.get("excluded_assets", {})
        if not _trial_eligible(lesson, exclusions):
            continue
        assets = [a for a in _candidates([lesson]) if a["material"] in authorization["materials"] and not a["blocked"] and a["name"] not in exclusions]
        if assets and ("video" not in authorization["materials"] or any(a["material"] == "video" for a in assets)):
            _approved_assets(authorization, assets)
            return first_series, assets
    raise ReleaseError("Authorized scope has no complete available trial lesson group")


def _gate_valid(work, state, key, trial):
    gate = state["trial_gates"].get(key, {})
    if not gate or gate.get("passed") is not True:
        return False
    digests = {a["name"]: _hash_asset(work, a)["sha256"] for a in trial}
    return gate.get("digests") == digests


def _remote_trial_valid(client, repository, commit, state, trial):
    """Local gate records alone cannot prove previously-uploaded files still exist."""
    for series_id in sorted({a["series_id"] for a in trial}):
        remote_release = _release(client, repository, commit, series_id, create=False, require_draft=False)
        if remote_release is None:
            return False
        existing = {a["name"]: a for a in list_assets(client, repository, remote_release["id"])}
        for asset in trial:
            if asset["series_id"] != series_id:
                continue
            remote = existing.get(asset["name"])
            if remote is None or compare_asset(remote, asset["sha256"], asset["size_bytes"],
                    state["assets"].get(_state_key(repository, asset["name"]))) != "verified":
                return False
    return True


def upload(work, series="all", limit=None, apply=False, authorization=None):
    work._release_actual_hashes = {}
    selected, episodes = _selection(work, series, limit)
    assets = _candidates(episodes)
    per_series = {s: sum(1 for a in assets if a["series_id"] == s and not a["blocked"]) for s in selected}
    if any(number > MAX_ASSETS for number in per_series.values()):
        raise ReleaseError("Planned Release exceeds 1000 attachments")
    rights = work.read_json("rights.json", {})
    def right(asset):
        return rights.get("episodes", {}).get(asset["episode_id"], {}).get(asset["material"], rights.get("default", "unknown"))
    preview = {"mode": "apply" if apply else "dry_run", "remote_called": False, "series": list(selected),
               "lesson_groups": len(episodes), "available_assets": len(assets), "per_series": per_series,
               "blocked": _unusable_present(episodes, ("video", "zh-CN", "en")),
               "assets": [{"episode_id": a["episode_id"], "series_id": a["series_id"], "asset_name": a["name"],
                           "material": a["material"], "size_bytes": a["data"]["size_bytes"], "rights_state": right(a),
                           "status": a["blocked"] or ("planned" if right(a) == "confirmed" else "blocked_unknown_rights")} for a in assets],
               "note": "Dry run does not authenticate, hash videos, create Releases or upload bytes."}
    work.write_json("upload_preview.json", preview)
    state = _state(work)
    if not apply:
        work.write_json("upload_state.json", state)
        return preview
    auth, repository, commit = _authorization(work, authorization, selected)
    exclusions = auth.get("excluded_assets", {})
    trial_series, trial = _trial_assets(work, auth)
    if limit == 1 and tuple(selected) == (trial_series,):
        # Find the first usable whole group, including explicit partial-scope exclusions.
        _, all_lessons = _selection(work, trial_series, None)
        episodes = [e for e in all_lessons if e["episode_id"] == trial[0]["episode_id"]]
        assets = _candidates(episodes)
    _rights(work, [a for a in assets if a["name"] not in exclusions], auth["materials"])
    chosen = [a for a in assets if not a["blocked"] and a["material"] in auth["materials"] and a["name"] not in exclusions]
    _approved_assets(auth, chosen)
    _rights(work, trial, auth["materials"])
    gate_key = _gate_key(auth, repository, commit)
    is_trial = {a["name"] for a in chosen} == {a["name"] for a in trial}
    if not is_trial and not _gate_valid(work, state, gate_key, trial):
        raise ReleaseError(f"Complete a verified trial first: upload --series {trial_series} --limit 1 --apply --authorization {authorization}")
    if not chosen:
        raise ReleaseError("No authorized, available assets to upload")
    for asset in chosen:
        deferred = state.get("retry_deferred_until", {}).get(_state_key(repository, asset["name"]))
        if deferred and dt.datetime.fromisoformat(deferred) > dt.datetime.now(dt.timezone.utc):
            raise ReleaseError("Server Retry-After has not elapsed; this attachment remains deferred: " + asset["name"])
    chosen = [_hash_asset(work, a) for a in chosen]
    client = GHClient()
    _preflight(client, repository, commit, auth)
    if not is_trial and not _remote_trial_valid(client, repository, commit, state, trial):
        raise ReleaseError("Previously verified trial attachments changed or disappeared remotely; repeat the trial")
    state.update(repository=repository, commit_sha=commit, visibility=auth["visibility"])
    work.write_json("upload_state.json", state)
    results = []
    for series_id in selected:
        group = [a for a in chosen if a["series_id"] == series_id]
        if not group:
            continue
        remote_release = _release(client, repository, commit, series_id, create=True, require_draft=False)
        if remote_release.get("draft") is True and remote_release.get("immutable") is True:
            raise ReleaseError("Draft Release is immutable; no attachment write is permitted")
        state["releases"][repository + "/" + series_id] = {"id": remote_release["id"], "tag": remote_release["tag_name"],
                                                               "draft": remote_release.get("draft"), "html_url": remote_release.get("html_url")}
        remote_assets = list_assets(client, repository, remote_release["id"])
        existing = {a["name"]: a for a in remote_assets}
        if len(existing) + sum(a["name"] not in existing for a in group) > MAX_ASSETS:
            raise ReleaseError("Existing and planned assets together exceed the Release limit")
        # Published Releases can be resumed read-only. Validate the entire group
        # before any per-file work so no new bytes can be sent to a published set.
        if remote_release.get("draft") is not True:
            if any(asset["name"] not in existing or compare_asset(existing[asset["name"]], asset["sha256"],
                    asset["size_bytes"], state["assets"].get(_state_key(repository, asset["name"]))) != "verified"
                    for asset in group):
                raise ReleaseError("Published or immutable Release lacks matching verified attachments; no write is permitted")
        # Inspect every same-name attachment before the first upload in this series.
        for asset in group:
            if asset["name"] in existing and compare_asset(existing[asset["name"]], asset["sha256"], asset["size_bytes"],
                    state["assets"].get(_state_key(repository, asset["name"]))) == "conflict":
                _record(state, repository, remote_release, asset, existing[asset["name"]], "conflict", "conflict")
                work.write_json("upload_state.json", state)
                raise ReleaseError("Same-name remote content conflicts: " + asset["name"])
        for asset in group:
            key = _state_key(repository, asset["name"])
            remote = existing.get(asset["name"])
            uploaded = False
            if remote is None:
                url = _upload_url(remote_release, repository, asset["name"], asset["label"])
                # Persisted hash caches help resume; new uploads always read source bytes again.
                _hash_asset(work, asset, force=True)
                for attempt in range(RETRIES):
                    try:
                        # A Release may have been published since this group's
                        # initial inspection. Recheck before every byte-send.
                        writable = _release(client, repository, commit, series_id, create=False)
                        if writable is None or writable.get("id") != remote_release["id"]:
                            raise ReleaseError("Release identity changed before upload")
                        # Recheck metadata immediately before sending the source.
                        source_now = _path(work, asset)
                        stat = source_now.stat()
                        if (stat.st_size, stat.st_mtime_ns) != (asset["size_bytes"], asset["mtime_ns"]):
                            raise ReleaseError("Source changed before upload")
                        client.request(url, method="POST", source=source_now,
                                       content_type=mimetypes.guess_type(asset["name"])[0] or "application/octet-stream")
                        uploaded = True
                    except GHError as error:
                        state.setdefault("retry_events", []).append({"asset_name": asset["name"], "attempt": attempt + 1,
                                                                      "http_status": error.status})
                        work.write_json("upload_state.json", state)
                        if error.status in (401, 403) and not error.transient:
                            _record(state, repository, remote_release, asset, None, "failed", "not_verified", str(error))
                            work.write_json("upload_state.json", state)
                            raise
                        # Always reconcile a failed request before retrying bytes.
                        remote = next((a for a in list_assets(client, repository, remote_release["id"])
                                       if a.get("name") == asset["name"]), None)
                        if remote is not None:
                            uploaded = True
                            break
                        if not error.transient or attempt == RETRIES - 1:
                            _record(state, repository, remote_release, asset, None, "failed", "not_verified", str(error))
                            work.write_json("upload_state.json", state)
                            raise
                        try:
                            delay = _delay(error, attempt)
                        except RetryDeferred as deferred:
                            state.setdefault("retry_deferred_until", {})[key] = (
                                dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=deferred.seconds)).isoformat()
                            _record(state, repository, remote_release, asset, None, "deferred_retry_after", "not_verified", str(deferred))
                            work.write_json("upload_state.json", state)
                            raise
                        time.sleep(delay)
                        continue
                    # Do not trust only the upload response; list the actual asset.
                    remote = next((a for a in list_assets(client, repository, remote_release["id"])
                                   if a.get("name") == asset["name"]), None)
                    break
            if remote is None:
                _record(state, repository, remote_release, asset, None, "failed", "not_verified", "Uploaded asset is absent from remote listing")
                work.write_json("upload_state.json", state)
                raise ReleaseError("Uploaded attachment is not present in the remote listing")
            check = compare_asset(remote, asset["sha256"], asset["size_bytes"], state["assets"].get(key))
            old = state["assets"].get(key, {})
            verification = "download_verified" if check == "verified" and not remote.get("digest") and old.get("verification") == "download_verified" else check
            status = ("uploaded_verified" if uploaded else "skipped_verified") if check == "verified" else check
            record = _record(state, repository, remote_release, asset, remote, status, verification)
            work.write_json("upload_state.json", state)
            after = record["source_metadata_after"]
            if (after["size_bytes"], after["mtime_ns"]) != (asset["size_bytes"], asset["mtime_ns"]):
                record["status"] = "source_changed_after_upload"
                work.write_json("upload_state.json", state)
                raise ReleaseError("Source changed while uploading; remote bytes require investigation")
            results.append({"asset_name": asset["name"], "status": status, "verification": verification,
                            "browser_download_url": remote.get("browser_download_url"), "draft": remote_release.get("draft"), "visibility": auth["visibility"]})
            if check != "verified":
                raise ReleaseError("Attachment lacks matching SHA-256 verification; bulk gate remains closed. Use verify --download: " + asset["name"])
    if is_trial:
        state["trial_gates"][gate_key] = {"passed": True, "digests": {a["name"]: a["sha256"] for a in chosen},
                                        "authorization_id": authorization, "repository": repository, "commit_sha": commit,
                                        "verified_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        work.write_json("upload_state.json", state)
    return {"mode": "apply", "remote_called": True, "lesson_groups": len(episodes), "assets": results,
            "excluded_materials": sorted({a["material"] for a in assets if a["material"] not in auth["materials"]}),
            "blocked": preview["blocked"], "excluded_assets": exclusions, "trial_passed": is_trial}


def verify(work, series="all", download=False):
    work._release_actual_hashes = {}
    selected, episodes = _selection(work, series, None)
    if work.config.get("github", {}).get("allow_remote_write") is not True:
        return {"remote_called": False, "status": "not_executed_stage_a", "note": "Remote verification is deferred to authorized Stage B."}
    auth_record = work.read_json("authorization.json", {})
    auth, repository, commit = _authorization(work, auth_record.get("authorization_id"), selected)
    assets = [a for a in _candidates(episodes) if not a["blocked"] and a["material"] in auth["materials"] and
              a["name"] not in auth.get("excluded_assets", {})]
    _approved_assets(auth, assets)
    _rights(work, assets, auth["materials"])
    assets = [_hash_asset(work, a) for a in assets]
    client, state, results = GHClient(), _state(work), []
    _preflight(client, repository, commit, auth)
    state.update(repository=repository, commit_sha=commit, visibility=auth["visibility"])
    for series_id in selected:
        remote_release = _release(client, repository, commit, series_id, create=False, require_draft=False)
        group = [a for a in assets if a["series_id"] == series_id]
        if remote_release is None:
            for asset in group:
                previous = state["assets"].get(_state_key(repository, asset["name"]))
                if previous:
                    previous.update(status="missing_release", verification="not_verified", browser_download_url=None)
                results.append({"asset_name": asset["name"], "status": "missing_release"})
            work.write_json("upload_state.json", state)
            continue
        remote_assets = {a["name"]: a for a in list_assets(client, repository, remote_release["id"])}
        for asset in group:
            remote, key = remote_assets.get(asset["name"]), _state_key(repository, asset["name"])
            if remote is None:
                _record(state, repository, remote_release, asset, None, "missing_remote", "not_verified")
                work.write_json("upload_state.json", state)
                results.append({"asset_name": asset["name"], "status": "missing_remote"})
                continue
            check = compare_asset(remote, asset["sha256"], asset["size_bytes"], state["assets"].get(key))
            download_hash = None
            if download and check == "metadata_only":
                target = work.local("download_checks/" + uuid.uuid4().hex + ".bin")
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    client.download(repository, remote["id"], target)
                    download_hash = core.sha256(target)
                    size = target.stat().st_size
                    fresh = next((a for a in list_assets(client, repository, remote_release["id"])
                                  if a.get("name") == asset["name"]), None)
                    check = "download_verified" if (download_hash == asset["sha256"] and size == asset["size_bytes"] and
                            fresh and fresh.get("id") == remote.get("id") and fresh.get("size") == size) else "conflict"
                finally:
                    if target.is_file():
                        target.unlink()
            verification = check
            if check == "verified" and not remote.get("digest"):
                verification = "download_verified"
                download_hash = state["assets"].get(key, {}).get("download_sha256")
            status = "verified" if check in ("verified", "download_verified") else check
            record = _record(state, repository, remote_release, asset, remote, status, verification)
            if download_hash:
                record["download_sha256"] = download_hash
            work.write_json("upload_state.json", state)
            after = record["source_metadata_after"]
            if (after["size_bytes"], after["mtime_ns"]) != (asset["size_bytes"], asset["mtime_ns"]):
                record["status"] = "source_changed_during_verification"
                work.write_json("upload_state.json", state)
                raise ReleaseError("Source changed during remote verification")
            results.append({"asset_name": asset["name"], "status": status, "verification": verification,
                            "browser_download_url": remote.get("browser_download_url"), "draft": remote_release.get("draft"), "visibility": auth["visibility"]})
    return {"remote_called": True, "assets": results, "all_verified": bool(results) and all(r["status"] == "verified" for r in results)}


def release(work, series="all", apply=False, authorization=None):
    """Publish only fully verified authorized attachment sets; never change visibility."""
    if not apply:
        return {"mode": "dry_run", "remote_called": False, "series": list(core.select_series(series))}
    selected, episodes = _selection(work, series, None)
    auth, repository, commit = _authorization(work, authorization, selected)
    exclusions = auth.get("excluded_assets", {})
    unusable = [a for a in _unusable_present(episodes, auth["materials"]) if a["asset_name"] not in exclusions]
    if unusable:
        raise ReleaseError("Authorized series contains present unusable assets; record an explicit partial scope before publishing: " +
                           ", ".join(a["asset_name"] for a in unusable))
    _approved_assets(auth, [asset for asset in _candidates(episodes) if not asset["blocked"] and
                           asset["material"] in auth["materials"] and asset["name"] not in exclusions])
    outcome = verify(work, series, download=False)
    if not outcome.get("all_verified"):
        raise ReleaseError("All authorized available attachments must be verified before publishing")
    state = _state(work)
    _, trial = _trial_assets(work, auth)
    if not _gate_valid(work, state, _gate_key(auth, repository, commit), trial):
        raise ReleaseError("A verified trial gate is required before publishing")
    assets = _candidates(episodes)
    blocked = [{"asset_name": a["name"], "reason": a["blocked"]} for a in assets if a["blocked"] and
               a["material"] in auth["materials"] and a["name"] not in exclusions]
    if blocked:
        raise ReleaseError("Publication includes excluded oversized/empty assets; record explicit partial-publication exclusions first")
    authorized_assets = [_hash_asset(work, asset) for asset in assets if not asset["blocked"] and
                         asset["material"] in auth["materials"] and asset["name"] not in exclusions]
    client, results = GHClient(), []
    _preflight(client, repository, commit, auth)
    def check_scope(remote, series_id):
        group = [asset for asset in authorized_assets if asset["series_id"] == series_id]
        actual = {item["name"]: item for item in list_assets(client, repository, remote["id"])}
        expected = {asset["name"] for asset in group}
        if set(actual) != expected:
            raise ReleaseError("Remote Release attachment names differ from the exact authorized inventory; "
                               "no publication or deletion is permitted")
        if any(compare_asset(actual[asset["name"]], asset["sha256"], asset["size_bytes"],
                state["assets"].get(_state_key(repository, asset["name"]))) != "verified" for asset in group):
            raise ReleaseError("Remote attachment verification changed before publication")
        return actual

    # Check every selected series before the first PATCH. Unknown remote extras
    # must never be implicitly published, even if all expected files are present.
    for series_id in selected:
        remote = _release(client, repository, commit, series_id, create=False, require_draft=False)
        if remote is None:
            raise ReleaseError("Release is missing")
        if remote.get("draft") is True and remote.get("immutable") is True:
            raise ReleaseError("Draft Release is immutable; publication is refused")
        check_scope(remote, series_id)
    for series_id in selected:
        remote = _release(client, repository, commit, series_id, create=False, require_draft=False)
        if remote is None:
            raise ReleaseError("Release is missing")
        if remote.get("draft") is True and remote.get("immutable") is True:
            raise ReleaseError("Draft Release is immutable; publication is refused")
        check_scope(remote, series_id)
        if remote.get("draft") is False:
            published, result_status = remote, "skipped_published"
        else:
            payload = {"draft": False}
            if exclusions:
                payload["body"] = (remote.get("body") or TASK_MARKER) + "\n\n经本轮明确授权排除的附件与原因：\n" + "\n".join(
                    f"- {name}: {reason}" for name, reason in sorted(exclusions.items()) if name.startswith(f"s{int(series_id):02d}-"))
            published = client.request(f"repos/{repository}/releases/{remote['id']}", method="PATCH", payload=payload)
            result_status = "published"
        if published.get("draft") is not False or published.get("id") != remote["id"]:
            raise ReleaseError("GitHub did not confirm the intended Release publication")
        # The API response supplies real URLs; no guessed download links are constructed.
        state["releases"][repository + "/" + series_id] = {"id": published["id"], "tag": published["tag_name"],
                                                            "draft": published.get("draft"), "html_url": published.get("html_url"),
                                                            "status": result_status}
        for item in list_assets(client, repository, published["id"]):
            record = state["assets"].get(_state_key(repository, item.get("name", "")))
            if record and record.get("asset_id") == item.get("id"):
                record.update(browser_download_url=item.get("browser_download_url"), draft=False,
                              release_url=published.get("html_url"))
        work.write_json("upload_state.json", state)
        results.append(state["releases"][repository + "/" + series_id])
    return {"remote_called": True, "releases": results, "excluded_assets": exclusions}
