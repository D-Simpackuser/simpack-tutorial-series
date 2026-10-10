"""Read-only verification of current Simpack library metadata; no remote writes.

GET-only, fixed repository identity, no media upload or download. Upload phase,
authorization expiry and historical visibility are deliberately not consulted.
SHA-256 checks compare remote metadata with the preserved baseline and catalog;
this command does not recompute complete video hashes or establish public rights.
Private receipts are written only with explicit --output / --observation options.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

sys.dont_write_bytecode = True
import core
import github_release as transport

REPOSITORY = "D-Simpackuser/simpack-tutorial-series"
REPOSITORY_ID = 1412669436
SERIES = ("1", "2", "3", "5", "6", "7", "8")
LESSON_COUNTS = dict(zip(SERIES, (18, 13, 16, 42, 8, 46, 51)))
ASSET_COUNTS = dict(zip(SERIES, (90, 65, 80, 206, 40, 230, 255)))
PREFIX = "repos/" + REPOSITORY
REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = REPO_ROOT.parent / "_local"
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
ASSET_NAME = re.compile(r"s(?:01|02|03|05|06|07|08)-e[0-9]{3}(?:\.mp4|\.(?:zh-CN|en)\.(?:srt|vtt))\Z")


class VerificationError(RuntimeError):
    """Messages contain safe fixed descriptions, never subprocess stderr."""


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def valid_id(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_endpoint(endpoint, method="GET", payload=None, source=None,
                   content_type=None):
    """Reject mutations, binary endpoints, other repos and arbitrary queries."""
    if method != "GET" or any(x is not None for x in (payload, source, content_type)):
        raise VerificationError("Only body-free metadata GET requests are permitted")
    if not isinstance(endpoint, str):
        raise VerificationError("Read endpoint is outside the metadata allowlist")
    tags = "(?:1|2|3|5|6|7|8)"
    routes = (
        re.escape(PREFIX),
        re.escape(PREFIX) + r"/releases/tags/series-" + tags + r"-v1",
        re.escape(PREFIX) + r"/releases/[1-9][0-9]*/assets\?per_page=100&page=(?:[1-9]|10|11)",
        re.escape(PREFIX) + r"/git/ref/tags/series-" + tags + r"-v1",
        re.escape(PREFIX) + r"/git/tags/[0-9a-f]{40}",
    )
    if not any(re.fullmatch(route, endpoint) for route in routes):
        raise VerificationError("Read endpoint is outside the metadata allowlist")


class ReadOnlyGitHub:
    """Restricted CLI adapter reusing the existing parser and finite retries."""
    def __init__(self, binary="gh"):
        if not isinstance(binary, str) or not binary or "\x00" in binary:
            raise VerificationError("Invalid GitHub CLI executable")
        self.binary = binary
        self.env = os.environ.copy()
        for name in list(self.env):
            if name.startswith("GIT_TRACE") or name == "GH_DEBUG":
                self.env.pop(name, None)

    def request(self, endpoint, method="GET", payload=None, source=None,
                content_type=None):
        check_endpoint(endpoint, method, payload, source, content_type)
        args = [self.binary, "api", endpoint, "--hostname", "github.com",
                "--include", "--method", "GET", "--header",
                "Accept: application/vnd.github+json", "--header",
                "X-GitHub-Api-Version: 2026-03-10"]
        try:
            result = subprocess.run(args, shell=False, capture_output=True,
                                    check=False, timeout=transport.READ_TIMEOUT,
                                    env=self.env)
        except (OSError, subprocess.TimeoutExpired):
            raise transport.GHError(code="transport_unavailable") from None
        status, headers, body = transport._response(result.stdout)
        if status is None and result.returncode:
            match = re.search(r"\bHTTP\s+(\d{3})\b",
                              result.stderr.decode("utf-8", errors="replace"))
            status = int(match.group(1)) if match else None
        if result.returncode or status is None or status >= 400:
            raise transport.GHError(status, headers, result.returncode)
        if not isinstance(body, (dict, list)):
            raise transport.GHError(status, headers, "invalid_response")
        return body

    def get(self, endpoint):
        check_endpoint(endpoint)
        return transport._get(self, endpoint)

    def download(self, *args, **kwargs):
        raise VerificationError("Media downloads are not permitted")

    def assets(self, release_id):
        if not valid_id(release_id):
            raise VerificationError("Invalid Release identity")
        result = []
        for page in range(1, 12):
            batch = self.get(f"{PREFIX}/releases/{release_id}/assets?per_page=100&page={page}")
            if (not isinstance(batch, list) or len(batch) > 100 or
                    any(not isinstance(item, dict) for item in batch)):
                raise VerificationError("Invalid paginated asset response")
            result.extend(batch)
            if len(result) > 1000:
                raise VerificationError("Asset pagination exceeds the Release limit")
            if len(batch) < 100:
                return result
        raise VerificationError("Asset pagination did not terminate safely")


def download_url(sid, name):
    return f"https://github.com/{REPOSITORY}/releases/download/series-{sid}-v1/{quote(name, safe='')}"


def baseline_releases(baseline):
    repo = baseline.get("repository", {})
    if repo.get("full_name") != REPOSITORY or repo.get("id") != REPOSITORY_ID:
        raise VerificationError("Baseline repository identity is not the fixed target")
    records = baseline.get("remote_releases")
    if not isinstance(records, list) or len(records) != len(SERIES):
        raise VerificationError("Baseline must contain all seven Releases")
    result, global_ids = {}, set()
    for record in records:
        sid = record.get("series_id")
        release, reference = record.get("release", {}), record.get("tag_ref", {})
        obj, assets = reference.get("object", {}), record.get("assets")
        if (sid not in SERIES or sid in result or not valid_id(release.get("id")) or
                release.get("tag_name") != f"series-{sid}-v1" or
                reference.get("ref") != f"refs/tags/series-{sid}-v1" or
                obj.get("type") not in ("tag", "commit") or
                not SHA1.fullmatch(obj.get("sha", "")) or
                not SHA1.fullmatch(record.get("tag_commit", "")) or
                not isinstance(assets, list) or len(assets) != ASSET_COUNTS[sid]):
            raise VerificationError("Baseline Release or tag metadata is incomplete")
        names = set()
        for asset in assets:
            name = asset.get("name", "")
            if (not isinstance(name, str) or not ASSET_NAME.fullmatch(name) or
                    not name.startswith(f"s{int(sid):02d}-") or name in names or
                    not valid_id(asset.get("id")) or asset["id"] in global_ids or
                    not valid_id(asset.get("size")) or asset["size"] >= 2 ** 31 or
                    not SHA256.fullmatch(asset.get("digest", "")) or
                    asset.get("browser_download_url") != download_url(sid, name)):
                raise VerificationError("Baseline attachment invariants are incomplete")
            names.add(name)
            global_ids.add(asset["id"])
        result[sid] = record
    if set(result) != set(SERIES):
        raise VerificationError("Baseline series scope differs from the fixed library")
    return result


def expected_assets(catalog, saved, repo_root):
    episodes = catalog.get("episodes")
    if catalog.get("schema_version") != 1 or not isinstance(episodes, list):
        raise VerificationError("Catalog interface is not schema version 1")
    expected, lesson_ids, source_keys = {}, set(), set()
    counts = dict.fromkeys(SERIES, 0)
    for episode in episodes:
        sid, eid = episode.get("series_id"), episode.get("episode_id")
        relative = episode.get("original_relative_path")
        if (sid not in SERIES or not isinstance(eid, str) or
                not re.fullmatch(f"s{int(sid):02d}-e[0-9]{{3}}", eid) or
                eid in lesson_ids or not isinstance(relative, str) or
                not relative.startswith(sid + "/") or (sid, relative) in source_keys):
            raise VerificationError("Catalog lesson identity or exact source mapping is invalid")
        counts[sid] += 1
        lesson_ids.add(eid)
        source_keys.add((sid, relative))
        entries = [(episode, ".mp4")] + [
            (episode.get("subtitles", {}).get(suffix, {}), suffix)
            for suffix in transport.SUFFIXES]
        for item, suffix in entries:
            if suffix != ".mp4" and item.get("status") == "missing":
                if eid != "s05-e001" or item.get("download_url") or item.get("path"):
                    raise VerificationError("Catalog missing-subtitle scope changed")
                continue
            name = item.get("asset_name")
            if name != eid + suffix or name in expected:
                raise VerificationError("Catalog attachment identity is invalid")
            old = next((a for a in saved[sid]["assets"] if a["name"] == name), None)
            if old is None or item.get("download_url") != download_url(sid, name):
                raise VerificationError("Catalog attachment link differs from the saved identity")
            size = item.get("size_bytes", old["size"])
            digest = item.get("sha256", old["digest"][7:])
            if size != old["size"] or "sha256:" + digest != old["digest"]:
                raise VerificationError("Catalog attachment size or SHA-256 differs from baseline")
            copy_checked = False
            if suffix != ".mp4":
                wanted_path = f"subtitles/{sid}/{name}"
                if item.get("path") != wanted_path:
                    raise VerificationError("Catalog subtitle path changed")
                try:
                    copy = core.safe_source(repo_root, wanted_path)
                    before = copy.stat()
                    copy_hash = core.sha256(copy)
                    after = copy.stat()
                except (OSError, ValueError):
                    raise VerificationError("Cannot read a confined subtitle copy") from None
                if (before.st_size != size or copy_hash != digest or
                        (before.st_size, before.st_mtime_ns) !=
                        (after.st_size, after.st_mtime_ns)):
                    raise VerificationError("Subtitle copy bytes differ from catalog or baseline")
                copy_checked = True
            expected[name] = {"series_id": sid, "episode_id": eid,
                              "size": size, "sha256": digest,
                              "download_url": item["download_url"],
                              "subtitle_copy_checked": copy_checked,
                              "sha256_source": "catalog" if item.get("sha256") else "preserved_remote_baseline"}
    if counts != LESSON_COUNTS or len(expected) != sum(ASSET_COUNTS.values()):
        raise VerificationError("Catalog course or attachment counts differ from the fixed library")
    for sid in SERIES:
        if {n for n, a in expected.items() if a["series_id"] == sid} != {a["name"] for a in saved[sid]["assets"]}:
            raise VerificationError("Catalog and baseline attachment sets differ")
    return expected


def resolve_tag(client, reference):
    obj = reference.get("object", {})
    seen = set()
    for _ in range(6):
        kind, sha = obj.get("type"), obj.get("sha", "")
        if not isinstance(sha, str) or not SHA1.fullmatch(sha):
            raise VerificationError("Tag object SHA is invalid")
        if kind == "commit":
            return sha
        if kind != "tag" or sha in seen:
            raise VerificationError("Tag target cannot be resolved safely")
        seen.add(sha)
        tagged = client.get(f"{PREFIX}/git/tags/{sha}")
        if not isinstance(tagged, dict) or tagged.get("sha") != sha:
            raise VerificationError("Annotated tag object identity is invalid")
        obj = tagged.get("object", {})
    raise VerificationError("Tag object chain exceeded its safety limit")


def verify(client, catalog, baseline, repo_root=REPO_ROOT):
    saved = baseline_releases(baseline)
    expected = expected_assets(catalog, saved, Path(repo_root))
    remote = client.get(PREFIX)
    if (not isinstance(remote, dict) or remote.get("full_name") != REPOSITORY or
            remote.get("id") != REPOSITORY_ID or
            remote.get("private") not in (True, False) or
            not isinstance(remote.get("private"), bool)):
        raise VerificationError("Observed repository identity or visibility is invalid")
    visibility = "private" if remote["private"] else "public"
    observed_at = now()
    observation = {"repository": REPOSITORY, "repository_id": REPOSITORY_ID,
                   "id": REPOSITORY_ID,
                   "visibility": visibility, "observed_at": observed_at,
                   "checked_at": observed_at, "remote_read_only": True,
                   "source": "github_rest_metadata_GET", "read_only": True,
                   "remote_writes": False, "public_access_verified": False}
    branch = remote.get("default_branch")
    if isinstance(branch, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", branch):
        observation["default_branch"] = branch
    report = {"schema_version": 1, "checked_at": observation["checked_at"],
              "repository": REPOSITORY, "repository_id": REPOSITORY_ID,
              "read_only": True, "remote_writes": 0, "media_downloads": 0,
              "visibility_observation": observation, "issues": [],
              "releases": [], "assets": [], "expected_assets": len(expected),
              "video_full_hashes_recomputed": 0,
              "subtitle_copies_sha256_checked": sum(a["subtitle_copy_checked"] for a in expected.values()),
              "sha256_evidence": "Remote digest metadata compared with preserved baseline; available catalog SHA-256 and local subtitle bytes also checked. No video bytes read.",
              "public_distribution_rights_verified": False,
              "public_access_verified": False}

    def require(condition, code, sid, name=None, fields=None):
        if not condition:
            issue = {"code": code, "series_id": sid}
            if name is not None:
                issue["asset_name"] = name
            if fields is not None:
                issue["fields"] = fields
            report["issues"].append(issue)

    observed_ids = set()
    for sid in SERIES:
        record, tag = saved[sid], f"series-{sid}-v1"
        release = client.get(f"{PREFIX}/releases/tags/{tag}")
        if not isinstance(release, dict) or not valid_id(release.get("id")):
            raise VerificationError("Observed Release identity is invalid")
        old_release = record["release"]
        release_fields = ("id", "tag_name", "target_commitish", "draft", "prerelease", "immutable", "html_url")
        changed = [f for f in release_fields if release.get(f) != old_release.get(f)]
        require(not changed, "release_invariant_conflict", sid, fields=changed)
        require(release.get("draft") is False, "release_not_published", sid)
        reference = client.get(f"{PREFIX}/git/ref/tags/{tag}")
        if not isinstance(reference, dict):
            raise VerificationError("Observed tag reference is invalid")
        old_reference = record["tag_ref"]
        current_object = reference.get("object", {})
        old_object = old_reference.get("object", {})
        require(reference.get("ref") == old_reference.get("ref") and
                current_object.get("type") == old_object.get("type") and
                current_object.get("sha") == old_object.get("sha"), "tag_object_conflict", sid)
        commit = resolve_tag(client, reference)
        require(commit == record["tag_commit"], "tag_target_commit_conflict", sid)
        items = client.assets(release["id"])
        names = [item.get("name") for item in items]
        wanted = {name for name, asset in expected.items() if asset["series_id"] == sid}
        require(len(names) == len(set(n for n in names if isinstance(n, str))) and
                set(n for n in names if isinstance(n, str)) == wanted,
                "remote_attachment_set_conflict", sid)
        require(len(items) == ASSET_COUNTS[sid], "remote_attachment_count_conflict", sid)
        report["releases"].append({"series_id": sid, "id": release["id"],
                                   "tag_name": tag, "target_commit": commit,
                                   "asset_count": len(items),
                                   "html_url": old_release.get("html_url") if release.get("html_url") == old_release.get("html_url") else None})
        by_name = {item.get("name"): item for item in items if isinstance(item.get("name"), str)}
        baseline_by_name = {item["name"]: item for item in record["assets"]}
        for name in sorted(wanted):
            item = by_name.get(name)
            if item is None:
                continue
            old, local = baseline_by_name[name], expected[name]
            fixed = ("id", "name", "size", "digest", "browser_download_url")
            changed = [field for field in fixed if item.get(field) != old.get(field)]
            require(not changed, "attachment_invariant_conflict", sid, name, changed)
            checks = {"state": item.get("state") == "uploaded",
                      "size": item.get("size") == local["size"],
                      "sha256": item.get("digest") == "sha256:" + local["sha256"],
                      "download_url": item.get("browser_download_url") == local["download_url"],
                      "release_id": release["id"] == old_release["id"],
                      "unique_asset_id": valid_id(item.get("id")) and item.get("id") not in observed_ids}
            if valid_id(item.get("id")):
                observed_ids.add(item["id"])
            passed = not changed and all(checks.values())
            require(all(checks.values()), "attachment_metadata_verification", sid, name,
                    [field for field, ok in checks.items() if not ok])
            report["assets"].append({"asset_name": name, "series_id": sid,
                                     "release_id": release["id"],
                                     "asset_id": item.get("id") if valid_id(item.get("id")) else None,
                                     "size": item.get("size") if valid_id(item.get("size")) else None,
                                     "sha256": local["sha256"] if checks["sha256"] else None,
                                     "browser_download_url": local["download_url"] if checks["download_url"] else None,
                                     "sha256_source": local["sha256_source"],
                                     "verified": passed})
    report["verified_assets"] = sum(a["verified"] for a in report["assets"])
    report["passed"] = not report["issues"] and report["verified_assets"] == len(expected)
    return report


def private_output_path(value, private_root=PRIVATE_ROOT):
    root = Path(os.path.abspath(private_root))
    candidate = Path(os.path.abspath(value))
    try:
        relative = candidate.relative_to(root)
        path = core.confined(root, relative)
    except ValueError:
        raise VerificationError("Receipt output must stay in the private _local directory") from None
    if path.exists():
        raise VerificationError("Receipt output already exists; choose a new private filename")
    return path


def write_private(path, document, private_root=PRIVATE_ROOT):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Recheck links after creating parent directories and before exclusive open.
    safe = private_output_path(path, private_root)
    with safe.open("xb") as stream:
        stream.write((json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gh", default="gh", help="Existing GitHub CLI executable (default: gh)")
    parser.add_argument("--catalog", type=Path, default=REPO_ROOT / "catalog.json", help="Existing schema-1 catalog")
    parser.add_argument("--baseline", type=Path, default=PRIVATE_ROOT / "stage_c/baseline.json", help="Preserved private Stage C baseline")
    parser.add_argument("--output", type=Path, help="Explicit new private _local JSON receipt; never overwritten")
    parser.add_argument("--observation", type=Path, help="Explicit new private _local visibility observation; never changes GitHub visibility")
    args = parser.parse_args(argv)
    try:
        output = private_output_path(args.output) if args.output else None
        observation = private_output_path(args.observation) if args.observation else None
        if output is not None and output == observation:
            raise VerificationError("Receipt and visibility observation must use different private files")
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        result = verify(ReadOnlyGitHub(args.gh), catalog, baseline, args.catalog.resolve().parent)
        if output:
            write_private(output, result)
        if observation:
            write_private(observation, result["visibility_observation"])
    except (VerificationError, transport.ReleaseError, OSError, ValueError, TypeError, KeyError) as error:
        message = str(error) if isinstance(error, (VerificationError, transport.ReleaseError)) else type(error).__name__
        print(json.dumps({"passed": False, "read_only": True, "remote_writes": 0,
                          "stopped": True, "reason": message}, ensure_ascii=False))
        return 2
    print(json.dumps({"passed": result["passed"], "read_only": True,
                      "repository": REPOSITORY, "repository_id": REPOSITORY_ID,
                      "visibility": result["visibility_observation"]["visibility"],
                      "verified_assets": result["verified_assets"],
                      "expected_assets": result["expected_assets"],
                      "issues": result["issues"], "remote_writes": 0,
                      "media_downloads": 0}, ensure_ascii=False))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
