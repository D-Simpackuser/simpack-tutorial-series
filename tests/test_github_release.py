"""Mock-only Release tests. Fixtures live entirely under the publishing workspace."""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core
import github_release as engine

RealGHClient = engine.GHClient

COMMIT = "a" * 40
REPOSITORY = "owner/demo"


class FakeGitHub:
    def __init__(self):
        self.calls, self.releases, self.assets, self.content = [], {}, {}, {}
        self.marker, self.owner, self.private = engine.TASK_MARKER, "owner", True
        self.tag_sha, self.digest_mode, self.upload_host = COMMIT, "correct", "uploads.github.com"
        self.fail_before, self.lose_response = 0, False
        self.retry_after = "0"
        self.auth_failure = False
        self.fail_get = 0

    def auth(self):
        self.calls.append(("AUTH", "github.com"))

    def make_release(self, series="1", draft=True):
        release_id = int(series) + 10
        value = {"id": release_id, "tag_name": f"series-{series}-v1", "target_commitish": COMMIT,
                 "name": f"系列 {series}", "body": engine.TASK_MARKER, "draft": draft, "immutable": False,
                 "html_url": f"https://github.com/{REPOSITORY}/releases/tag/series-{series}-v1",
                 "upload_url": f"https://{self.upload_host}/repos/{REPOSITORY}/releases/{release_id}/assets{{?name,label}}"}
        self.releases[series] = value
        self.assets.setdefault(release_id, [])
        return value

    def add_asset(self, release_id, name, raw, digest="correct"):
        asset_id = 100 + sum(map(len, self.assets.values()))
        value = {"id": asset_id, "name": name, "size": len(raw), "state": "uploaded",
                 "browser_download_url": f"https://github.com/{REPOSITORY}/releases/download/real/{name}"}
        if digest == "correct":
            value["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        elif digest == "incorrect":
            value["digest"] = "sha256:" + "f" * 64
        self.assets.setdefault(release_id, []).append(value)
        self.content[asset_id] = raw
        return value

    def request(self, endpoint, method="GET", payload=None, source=None, content_type=None):
        self.calls.append((method, endpoint))
        if method == "GET" and self.fail_get:
            self.fail_get -= 1
            raise engine.GHError(503, {"retry-after": "0"}, 1)
        if endpoint == "user":
            return {"login": self.owner}
        if endpoint == f"repos/{REPOSITORY}":
            return {"name": "demo", "owner": {"login": "owner"}, "private": self.private}
        if endpoint == f"repos/{REPOSITORY}/commits/{COMMIT}":
            return {"sha": COMMIT}
        if endpoint.startswith(f"repos/{REPOSITORY}/contents/"):
            return {"encoding": "base64", "content": base64.b64encode(self.marker.encode()).decode()}
        if "/git/ref/tags/" in endpoint:
            series = endpoint.split("series-", 1)[1].split("-", 1)[0]
            if series not in self.releases:
                raise engine.GHError(404, code=1)
            return {"object": {"type": "commit", "sha": self.tag_sha}}
        if "/releases/tags/" in endpoint:
            series = endpoint.split("series-", 1)[1].split("-", 1)[0]
            if series not in self.releases:
                raise engine.GHError(404, code=1)
            return copy.deepcopy(self.releases[series])
        if method == "POST" and endpoint == f"repos/{REPOSITORY}/releases":
            series = payload["tag_name"].split("-")[1]
            return copy.deepcopy(self.make_release(series))
        if method == "GET" and endpoint.startswith(f"repos/{REPOSITORY}/releases?per_page="):
            page = int(urllib.parse.parse_qs(urllib.parse.urlsplit(endpoint).query)["page"][0])
            return copy.deepcopy(list(self.releases.values())[(page - 1) * 100:page * 100])
        if "/assets?per_page=" in endpoint:
            release_id = int(endpoint.split("/releases/")[1].split("/")[0])
            page = int(urllib.parse.parse_qs(urllib.parse.urlsplit(endpoint).query)["page"][0])
            return copy.deepcopy(self.assets.get(release_id, [])[(page - 1) * 100:page * 100])
        if method == "POST" and endpoint.startswith("https://"):
            if self.auth_failure:
                raise engine.GHError(401, code=1)
            if self.fail_before:
                self.fail_before -= 1
                raise engine.GHError(503, {"retry-after": self.retry_after}, 1)
            parsed = urllib.parse.urlsplit(endpoint)
            release_id = int(parsed.path.split("/releases/")[1].split("/")[0])
            name = urllib.parse.parse_qs(parsed.query)["name"][0]
            if any(item["name"] == name for item in self.assets.get(release_id, [])):
                raise AssertionError("Duplicate upload was attempted")
            response = self.add_asset(release_id, name, Path(source).read_bytes(), self.digest_mode)
            if self.lose_response:
                self.lose_response = False
                raise engine.GHError(503, {"retry-after": "0"}, 1)
            return response
        if method == "PATCH":
            release_id = int(endpoint.rsplit("/", 1)[1])
            remote = next(value for value in self.releases.values() if value["id"] == release_id)
            remote["draft"] = payload["draft"]
            if "body" in payload:
                remote["body"] = payload["body"]
            return copy.deepcopy(remote)
        raise AssertionError(f"Unexpected mock endpoint: {method} {endpoint}")

    def download(self, repository, asset_id, target):
        self.calls.append(("DOWNLOAD", str(asset_id)))
        with Path(target).open("xb") as output:
            output.write(self.content[asset_id])

    @property
    def writes(self):
        return [call for call in self.calls if call[0] in ("POST", "PATCH")]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        fixture_root = Path(__file__).resolve().parents[2] / "_local" / "test-fixtures"
        fixture_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="release-test-", dir=fixture_root)
        self.base = Path(self.temp.name)
        self.video_root, self.subtitle_root, root = [self.base / name for name in ("videos", "subtitles", "work")]
        for path in (self.video_root, self.subtitle_root, root):
            path.mkdir()
        self.work = core.Workspace(root, {"work_root": str(root), "video_root": str(self.video_root),
                                         "subtitle_root": str(self.subtitle_root),
                                         "github": {"owner": "owner", "repository": "demo", "commit_sha": COMMIT,
                                                    "allow_remote_write": True, "allow_make_public": False}})
        self.episodes = [self.lesson("1", 1, "12-2 中文（全角）(space) & part.fbi"),
                         self.lesson("1", 2, "12-2 另一个标题"), self.lesson("2", 1, "9-11 测试")]
        self.work.write_json("inventory.json", {"episodes": self.episodes})
        self.work.write_json("rights.json", {"default": "unknown", "episodes": {
            episode["episode_id"]: {"video": "confirmed", "zh-CN": "confirmed", "en": "confirmed"} for episode in self.episodes}})
        now = dt.datetime.now(dt.timezone.utc)
        self.authorization = {"authorization_id": "test-explicit-scope", "confirmed": True,
                              "issued_at": (now - dt.timedelta(minutes=1)).isoformat(),
                              "expires_at": (now + dt.timedelta(hours=1)).isoformat(), "series": ["1", "2"],
                              "materials": ["video", "zh-CN", "en"], "repository": REPOSITORY,
                              "visibility": "private", "commit_sha": COMMIT, "rights_confirmed": True}
        self.work.write_json("authorization.json", self.authorization)
        self.fake = FakeGitHub()
        self.client_patch = patch.object(engine, "GHClient", return_value=self.fake)
        self.client_patch.start()
        self.sleep_patch = patch.object(engine.time, "sleep")
        self.sleep_patch.start()

    def tearDown(self):
        self.client_patch.stop()
        self.sleep_patch.stop()
        self.temp.cleanup()

    def lesson(self, series, number, title):
        episode_id = f"s{int(series):02d}-e{number:03d}"
        relative = Path(series) / (title + ".mp4")
        path = self.video_root / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(("mock video: " + title).encode("utf-8"))
        info = path.stat()
        video = {"path": str(path), "relative_path": relative.as_posix(), "size_bytes": info.st_size,
                 "mtime_ns": info.st_mtime_ns, "asset_name": episode_id + ".mp4", "status": "present"}
        subtitles = {}
        for suffix in engine.SUFFIXES:
            rel = Path(series) / (title + suffix)
            source = self.subtitle_root / rel
            source.parent.mkdir(exist_ok=True)
            source.write_bytes(b"WEBVTT\r\n\r\n00:00.000 --> 00:01.000\r\ntext\r\n" if suffix.endswith(".vtt") else
                               b"1\r\n00:00:00,000 --> 00:00:01,000\r\ntext\r\n")
            stat = source.stat()
            subtitles[suffix] = {"path": str(source), "relative_path": rel.as_posix(), "size_bytes": stat.st_size,
                                 "mtime_ns": stat.st_mtime_ns, "asset_name": episode_id + suffix,
                                 "status": "matched", "sha256": core.sha256(source)}
        return {"series_id": series, "episode_id": episode_id, "relative_path": relative.as_posix(),
                "title": title, "video": video, "subtitles": subtitles}

    def apply_trial(self):
        return engine.upload(self.work, "1", limit=1, apply=True, authorization=self.authorization["authorization_id"])

    def prepopulate_trial(self, digest="correct"):
        remote = self.fake.make_release()
        for asset in engine._candidates(self.episodes[:1]):
            self.fake.add_asset(remote["id"], asset["name"], engine._path(self.work, asset).read_bytes(), digest)

    def test_dry_run_has_zero_remote_calls_and_one_full_lesson(self):
        result = engine.upload(self.work, "1", limit=1)
        self.assertEqual(5, result["available_assets"])
        self.assertEqual(1, result["lesson_groups"])
        self.assertEqual([], self.fake.calls)
        self.assertIn("trial_gates", self.work.read_json("upload_state.json"))
        self.assertTrue(self.work.local("upload_preview.json").is_file())

    def test_dry_run_preserves_existing_state(self):
        self.work.write_json("upload_state.json", {"assets": {"existing": {"status": "keep"}}, "custom": "keep"})
        engine.upload(self.work, "1")
        state = self.work.read_json("upload_state.json")
        self.assertEqual("keep", state["assets"]["existing"]["status"])
        self.assertEqual("keep", state["custom"])

    def test_stage_a_apply_and_verify_never_call_remote(self):
        self.work.config["github"]["allow_remote_write"] = False
        with self.assertRaisesRegex(engine.ReleaseError, "disabled"):
            self.apply_trial()
        self.assertEqual("not_executed_stage_a", engine.verify(self.work)["status"])
        self.assertEqual([], self.fake.calls)

    def test_unknown_rights_block_before_authentication(self):
        self.work.write_json("rights.json", {"default": "unknown", "episodes": {}})
        with self.assertRaisesRegex(engine.ReleaseError, "Rights"):
            self.apply_trial()
        self.assertEqual([], self.fake.calls)

    def test_authorization_id_expiry_scope_commit_visibility(self):
        for field, value in [("authorization_id", "wrong"), ("expires_at", "2000-01-01T00:00:00+00:00"),
                             ("series", ["2"]), ("commit_sha", "b" * 40), ("visibility", "public")]:
            with self.subTest(field=field):
                authorization = dict(self.authorization)
                authorization[field] = value
                self.work.write_json("authorization.json", authorization)
                with self.assertRaises(engine.ReleaseError):
                    self.apply_trial()
                self.assertEqual([], self.fake.calls)

    def test_trial_uploads_five_verified_assets_and_records_real_urls(self):
        result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertEqual(5, len(result["assets"]))
        self.assertTrue(all(a["status"] == "uploaded_verified" for a in result["assets"]))
        state = self.work.read_json("upload_state.json")
        self.assertEqual(5, len(state["assets"]))
        self.assertEqual(1, len(state["trial_gates"]))
        self.assertTrue(all("/real/" in a["browser_download_url"] for a in state["assets"].values()))
        self.assertEqual(1, len([c for c in self.fake.writes if c[1] == f"repos/{REPOSITORY}/releases"]))
        names = [a["name"] for a in self.fake.assets[11]]
        self.assertIn("s01-e001.mp4", names)
        self.assertFalse(any("中文" in name for name in names))

    def test_full_bulk_requires_trial_before_any_remote_call(self):
        with self.assertRaisesRegex(engine.ReleaseError, "trial first"):
            engine.upload(self.work, "1", apply=True, authorization=self.authorization["authorization_id"])
        self.assertEqual([], self.fake.calls)

    def test_after_trial_bulk_reconciles_files_and_keeps_ids(self):
        self.apply_trial()
        result = engine.upload(self.work, "1,2", apply=True, authorization=self.authorization["authorization_id"])
        self.assertEqual(15, len(result["assets"]))
        self.assertEqual(5, sum(a["status"] == "skipped_verified" for a in result["assets"]))
        self.assertEqual(10, sum(a["status"] == "uploaded_verified" for a in result["assets"]))
        self.assertEqual(10, len(self.fake.assets[11]))
        self.assertEqual(5, len(self.fake.assets[12]))

    def test_trial_remote_disappearance_closes_bulk_gate(self):
        self.apply_trial()
        self.fake.assets[11].pop()
        before = len(self.fake.writes)
        with self.assertRaisesRegex(engine.ReleaseError, "disappeared"):
            engine.upload(self.work, "2", apply=True, authorization=self.authorization["authorization_id"])
        self.assertEqual(before, len(self.fake.writes))

    def test_same_hash_skips_but_same_name_conflict_never_overwrites(self):
        self.prepopulate_trial()
        result = self.apply_trial()
        self.assertEqual(5, sum(a["status"] == "skipped_verified" for a in result["assets"]))
        self.assertEqual([], self.fake.writes)
        self.fake.assets[11][0]["digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(engine.ReleaseError, "conflicts"):
            self.apply_trial()
        self.assertEqual([], self.fake.writes)

    def test_no_digest_is_metadata_only_until_download_verification(self):
        self.prepopulate_trial(digest="none")
        with self.assertRaisesRegex(engine.ReleaseError, "lacks matching"):
            self.apply_trial()
        state = self.work.read_json("upload_state.json")
        self.assertEqual("metadata_only", state["assets"][REPOSITORY + "/s01-e001.mp4"]["verification"])
        self.assertEqual({}, state["trial_gates"])
        result = engine.verify(self.work, "1", download=True)
        trial_results = [a for a in result["assets"] if a["asset_name"].startswith("s01-e001")]
        self.assertTrue(all(a["verification"] == "download_verified" for a in trial_results))
        self.assertEqual(5, len([c for c in self.fake.calls if c[0] == "DOWNLOAD"]))
        self.assertTrue(self.apply_trial()["trial_passed"])
        self.assertEqual([], self.fake.writes)

    def test_download_mismatch_reports_conflict(self):
        self.prepopulate_trial(digest="none")
        first = self.fake.assets[11][0]
        self.fake.content[first["id"]] = b"wrong remote bytes"
        result = engine.verify(self.work, "1", download=True)
        self.assertEqual("conflict", result["assets"][0]["status"])
        self.assertFalse(result["all_verified"])

    def test_lost_upload_response_is_reconciled_without_duplicate(self):
        self.fake.lose_response = True
        result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertEqual(5, len(self.fake.assets[11]))
        self.assertEqual(5, len([c for c in self.fake.writes if c[1].startswith("https://")]))
        self.assertEqual(1, len(self.work.read_json("upload_state.json")["retry_events"]))

    def test_transient_failures_are_bounded_and_retry_after_obeyed(self):
        self.fake.fail_before = 10
        with self.assertRaises(engine.GHError):
            self.apply_trial()
        self.assertEqual(3, len([c for c in self.fake.writes if c[1].startswith("https://")]))
        self.assertEqual(3, len(self.work.read_json("upload_state.json")["retry_events"]))
        self.assertEqual(0, engine._delay(engine.GHError(429, {"retry-after": "0"}), 0))
        with self.assertRaises(engine.RetryDeferred):
            engine._delay(engine.GHError(429, {"retry-after": "999"}), 0)

    def test_auth_failure_stops_without_retrying_other_assets(self):
        self.fake.auth_failure = True
        with self.assertRaises(engine.GHError):
            self.apply_trial()
        self.assertEqual(1, len([c for c in self.fake.writes if c[1].startswith("https://")]))

    def test_pagination_lists_all_pages(self):
        release = self.fake.make_release()
        for index in range(205):
            self.fake.add_asset(release["id"], f"asset-{index}", b"x")
        assets = engine.list_assets(self.fake, REPOSITORY, release["id"])
        self.assertEqual(205, len(assets))
        self.assertEqual(3, len([c for c in self.fake.calls if "per_page" in c[1]]))

    def test_oversize_boundary_is_exclusive_without_giant_fixture(self):
        for size in (core.MAX_BYTES, core.MAX_BYTES + 1):
            episode = copy.deepcopy(self.episodes[0])
            episode["video"]["size_bytes"] = size
            self.work.write_json("inventory.json", {"episodes": [episode]})
            result = engine.upload(self.work, "1")
            self.assertEqual("blocked_oversize", result["blocked"][0]["reason"])
            self.assertEqual(4, result["per_series"]["1"])
        self.assertEqual([], self.fake.calls)

    def test_source_change_or_escape_blocks_before_remote(self):
        path = Path(self.episodes[0]["video"]["path"])
        path.write_bytes(b"changed size")
        with self.assertRaisesRegex(engine.ReleaseError, "changed since"):
            self.apply_trial()
        self.assertEqual([], self.fake.calls)
        bad = engine._candidates(self.episodes[:1])[0]
        bad["data"]["path"] = str(self.base / "outside.mp4")
        with self.assertRaisesRegex(engine.ReleaseError, "outside"):
            engine._path(self.work, bad)

    def test_foreign_repo_owner_visibility_marker_and_tag_are_refused(self):
        self.fake.owner = "another-owner"
        with self.assertRaisesRegex(engine.ReleaseError, "account differs"):
            self.apply_trial()
        self.fake.owner = "owner"
        self.fake.private = False
        with self.assertRaisesRegex(engine.ReleaseError, "visibility"):
            self.apply_trial()
        self.fake.private = True
        self.fake.marker = "unrelated repository"
        with self.assertRaisesRegex(engine.ReleaseError, "marker"):
            self.apply_trial()
        self.fake.marker = engine.TASK_MARKER
        self.fake.make_release()
        self.fake.tag_sha = "b" * 40
        with self.assertRaisesRegex(engine.ReleaseError, "another commit"):
            self.apply_trial()
        self.assertEqual([], self.fake.writes)

    def test_published_verified_release_skips_but_immutable_draft_rejects_upload(self):
        self.prepopulate_trial()
        self.fake.releases["1"]["draft"] = False
        resumed = self.apply_trial()
        self.assertTrue(all(asset["status"] == "skipped_verified" for asset in resumed["assets"]))
        result = engine.verify(self.work, "1")
        self.assertFalse(result["assets"][0]["draft"])
        self.assertEqual([], self.fake.writes)
        self.fake.releases["1"].update(draft=True, immutable=True)
        with self.assertRaisesRegex(engine.ReleaseError, "immutable"):
            self.apply_trial()

    def test_unexpected_upload_host_is_never_sent_bytes(self):
        self.fake.upload_host = "attacker.invalid"
        self.fake.make_release()
        with self.assertRaisesRegex(engine.ReleaseError, "unexpected upload URL"):
            self.apply_trial()
        self.assertEqual([], self.fake.writes)

    def test_release_only_publishes_fully_verified_scope_and_refreshes_urls(self):
        self.apply_trial()
        with self.assertRaisesRegex(engine.ReleaseError, "All authorized"):
            engine.release(self.work, "1", apply=True, authorization=self.authorization["authorization_id"])
        engine.upload(self.work, "1", apply=True, authorization=self.authorization["authorization_id"])
        result = engine.release(self.work, "1", apply=True, authorization=self.authorization["authorization_id"])
        self.assertFalse(result["releases"][0]["draft"])
        self.assertTrue(all(a["draft"] is False for a in self.work.read_json("upload_state.json")["assets"].values()))

    def test_raw_api_uses_argument_arrays_explicit_name_and_input_path(self):
        source = Path(self.episodes[0]["video"]["path"])
        client = RealGHClient()
        # The class factory is patched; invoke the original adapter directly.
        method = RealGHClient.request
        response = subprocess.CompletedProcess([], 0, b'HTTP/2.0 201 Created\r\nContent-Type: application/json\r\n\r\n{"id":1}', b'')
        remote = self.fake.make_release()
        url = engine._upload_url(remote, REPOSITORY, "s01-e001.mp4", "中文（标题） & label")
        with patch.object(engine.subprocess, "run", return_value=response) as run:
            method(client, url, method="POST", source=source, content_type="video/mp4")
        args = run.call_args.args[0]
        self.assertIsInstance(args, list)
        self.assertIs(False, run.call_args.kwargs["shell"])
        self.assertIn("--input", args)
        self.assertIn(str(source), args)
        self.assertEqual("s01-e001.mp4", urllib.parse.parse_qs(urllib.parse.urlsplit(args[2]).query)["name"][0])
        self.assertNotIn("--clobber", args)
        self.assertGreater(run.call_args.kwargs["timeout"], 0)

    def test_generated_style_provenance_marker_is_accepted(self):
        self.fake.marker = "# 来源与权利\n工程标识：`simpack-local-publish-v1`。\n\nsimpack-local-publish-v1\n"
        self.assertTrue(self.apply_trial()["trial_passed"])

    def test_first_unusable_video_is_skipped_for_complete_trial_group(self):
        for status, size in (("unreadable", 5), ("zero_byte", 0), ("blocked_oversize", core.MAX_BYTES)):
            with self.subTest(status=status):
                episodes = copy.deepcopy(self.episodes)
                episodes[0]["video"].update(status=status, size_bytes=size)
                self.work.write_json("inventory.json", {"episodes": episodes})
                self.fake = FakeGitHub()
                self.client_patch.stop()
                self.client_patch = patch.object(engine, "GHClient", return_value=self.fake)
                self.client_patch.start()
                result = self.apply_trial()
                self.assertTrue(all(a["asset_name"].startswith("s01-e002") for a in result["assets"]))

    def test_missing_remote_and_release_clear_stale_verified_links(self):
        self.apply_trial()
        self.fake.assets[11].pop(0)
        result = engine.verify(self.work, "1")
        self.assertEqual("missing_remote", result["assets"][0]["status"])
        state = self.work.read_json("upload_state.json")
        self.assertIsNone(state["assets"][REPOSITORY + "/s01-e001.mp4"]["browser_download_url"])
        del self.fake.releases["1"]
        engine.verify(self.work, "1")
        state = self.work.read_json("upload_state.json")
        self.assertEqual("missing_release", state["assets"][REPOSITORY + "/s01-e001.zh-CN.srt"]["status"])
        self.assertIsNone(state["assets"][REPOSITORY + "/s01-e001.zh-CN.srt"]["browser_download_url"])

    def test_hash_cache_is_annotated_but_new_upload_reads_source_again(self):
        asset = engine._candidates(self.episodes[:1])[0]
        source = engine._path(self.work, asset)
        before = source.stat()
        engine._hash_asset(self.work, asset)
        self.work._release_actual_hashes = {}
        cached = engine._hash_asset(self.work, engine._candidates(self.episodes[:1])[0])
        self.assertEqual("cached_source_sha256_metadata_unchanged", cached["sha256_origin"])
        raw = source.read_bytes()
        changed = bytes([raw[0] ^ 1]) + raw[1:]
        source.write_bytes(changed)
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.apply_trial()
        remote = self.fake.assets[11][0]
        self.assertEqual("sha256:" + hashlib.sha256(changed).hexdigest(), remote["digest"])
        state = self.work.read_json("upload_state.json")
        self.assertEqual("source_sha256_computed", state["assets"][REPOSITORY + "/s01-e001.mp4"]["sha256_origin"])

    def test_retry_after_over_one_minute_is_persisted_and_not_retried_early(self):
        self.fake.fail_before, self.fake.retry_after = 1, "99"
        with self.assertRaises(engine.RetryDeferred):
            self.apply_trial()
        before = len(self.fake.calls)
        with self.assertRaisesRegex(engine.ReleaseError, "not elapsed"):
            self.apply_trial()
        self.assertEqual(before, len(self.fake.calls))
        self.assertEqual(1, len([c for c in self.fake.writes if c[1].startswith("https://")]))

    def test_subprocess_timeout_and_stderr_auth_status_are_sanitized(self):
        client = RealGHClient()
        with patch.object(engine.subprocess, "run", side_effect=subprocess.TimeoutExpired(["gh"], 60)):
            with self.assertRaises(engine.GHError) as context:
                client.request("user")
        self.assertTrue(context.exception.transient)
        result = subprocess.CompletedProcess([], 1, b"", b"HTTP 401: Bad credentials (example-secret)")
        with patch.object(engine.subprocess, "run", return_value=result):
            with self.assertRaises(engine.GHError) as context:
                client.request("user")
        self.assertEqual(401, context.exception.status)
        self.assertFalse(context.exception.transient)
        self.assertNotIn("example-secret", str(context.exception))

    def test_binary_download_detects_supported_flag_and_caches_local_help(self):
        raw = b"\x00\x1b[31m\xff\r\nMP4 bytes\x07"
        for supported in (True, False):
            with self.subTest(supported=supported):
                client, calls = RealGHClient(), []
                help_text = b"USAGE\n  gh api <endpoint> [flags]\nFLAGS\n  -H, --header key:value\n"
                if supported:
                    help_text += b"      --allow-escape-sequences  Allow binary escape bytes\n"
                def run(args, **kwargs):
                    calls.append((args, kwargs))
                    self.assertIs(False, kwargs["shell"])
                    self.assertGreater(kwargs["timeout"], 0)
                    if args == ["gh", "api", "--help"]:
                        self.assertEqual(engine.READ_TIMEOUT, kwargs["timeout"])
                        return subprocess.CompletedProcess(args, 0, help_text, b"")
                    self.assertEqual(supported, "--allow-escape-sequences" in args)
                    self.assertTrue(hasattr(kwargs["stdout"], "write"))
                    kwargs["stdout"].write(raw)
                    return subprocess.CompletedProcess(args, 0, None, b"")
                with patch.object(engine.subprocess, "run", side_effect=run):
                    for index in (1, 2):
                        target = self.work.local(f"mock-download-{supported}-{index}.bin")
                        client.download(REPOSITORY, index, target)
                        self.assertEqual(raw, target.read_bytes())
                self.assertEqual(1, sum(args == ["gh", "api", "--help"] for args, _ in calls))

    def test_binary_download_unknown_capabilities_stop_before_creating_file(self):
        failures = (subprocess.CompletedProcess([], 1, b"", b"private diagnostic"),
                    subprocess.CompletedProcess([], 0, b"unexpected help response", b""),
                    subprocess.TimeoutExpired(["gh", "api", "--help"], engine.READ_TIMEOUT))
        for index, failure in enumerate(failures):
            with self.subTest(failure=index):
                client = RealGHClient()
                target = self.work.local(f"no-download-{index}.bin")
                kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                with patch.object(engine.subprocess, "run", **kwargs) as run:
                    with self.assertRaisesRegex(engine.ReleaseError, "capabilities"):
                        client.download(REPOSITORY, 1, target)
                self.assertEqual(1, run.call_count)
                self.assertFalse(target.exists())

    def test_source_is_revalidated_just_before_sending_bytes(self):
        original = engine._path
        calls = 0
        def revalidate(work, asset):
            nonlocal calls
            if asset["name"] == "s01-e001.mp4":
                calls += 1
                if calls == 3:
                    raise ValueError("Link/reparse point target")
            return original(work, asset)
        with patch.object(engine, "_path", side_effect=revalidate):
            with self.assertRaisesRegex(ValueError, "reparse"):
                self.apply_trial()
        self.assertEqual([], [c for c in self.fake.writes if c[1].startswith("https://")])

    def test_present_invalid_asset_blocks_publish_unless_exactly_excluded(self):
        episodes = copy.deepcopy(self.episodes)
        episodes[1]["video"]["status"] = "unreadable"
        self.work.write_json("inventory.json", {"episodes": episodes})
        self.apply_trial()
        with self.assertRaisesRegex(engine.ReleaseError, "unusable"):
            engine.release(self.work, "1", apply=True, authorization=self.authorization["authorization_id"])
        authorization = dict(self.authorization)
        authorization["excluded_assets"] = {"s01-e002.mp4": "用户确认本轮排除此视频；字幕仍在授权范围"}
        self.work.write_json("authorization.json", authorization)
        self.apply_trial()  # Exclusions change the trial gate's authorized scope.
        engine.upload(self.work, "1", apply=True, authorization=authorization["authorization_id"])
        result = engine.release(self.work, "1", apply=True, authorization=authorization["authorization_id"])
        self.assertIn("s01-e002.mp4", result["excluded_assets"])
        self.assertIn("s01-e002.mp4", self.fake.releases["1"]["body"])
        self.assertFalse(any(a["name"] == "s01-e002.mp4" for a in self.fake.assets[11]))

    def test_partial_exclusions_require_exact_names_and_nonempty_reasons(self):
        for exclusions in ({"made-up.mp4": "reason"}, {"s01-e001.mp4": " "}):
            authorization = dict(self.authorization)
            authorization["excluded_assets"] = exclusions
            self.work.write_json("authorization.json", authorization)
            with self.assertRaises(engine.ReleaseError):
                self.apply_trial()
        self.assertEqual([], self.fake.calls)

    def test_response_parser_and_sanitized_error(self):
        status, headers, body = engine._response(b'HTTP/2.0 429 Too Many Requests\r\nRetry-After: 7\r\n\r\n{"message":"rate limit"}')
        self.assertEqual((429, "7", "rate limit"), (status, headers["retry-after"], body["message"]))
        self.assertNotIn("token", str(engine.GHError(401, code=1)).lower())
        self.assertFalse(engine.GHError(403, code=1).transient)
        self.assertTrue(engine.GHError(403, {"x-ratelimit-remaining": "0"}, 1).transient)


if __name__ == "__main__":
    unittest.main()
