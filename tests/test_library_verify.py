"""No-network tests for the independent metadata-only verifier."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import library_verify as verifier
import github_release as transport


def temporary_fixture():
    """Keep every synthetic test write inside the publishing workspace."""
    tests_root = Path(__file__).resolve().parents[2] / "_local" / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="library-verify-", dir=tests_root)


def fixture(root):
    """A complete seven-series library, including the one missing subtitle group."""
    catalog = {"schema_version": 1, "episodes": []}
    baseline = {"repository": {"full_name": verifier.REPOSITORY,
                                "id": verifier.REPOSITORY_ID, "private": True},
                "remote_releases": []}
    asset_id, commit = 10, "a" * 40
    for sid in verifier.SERIES:
        release = {"id": 100 + int(sid), "tag_name": f"series-{sid}-v1",
                   "target_commitish": commit, "draft": False, "prerelease": False,
                   "immutable": False,
                   "html_url": f"https://github.com/{verifier.REPOSITORY}/releases/tag/series-{sid}-v1"}
        reference = {"ref": f"refs/tags/series-{sid}-v1",
                     "object": {"type": "commit", "sha": commit}}
        assets = []
        for number in range(1, verifier.LESSON_COUNTS[sid] + 1):
            eid = f"s{int(sid):02d}-e{number:03d}"
            ep = {"series_id": sid, "episode_id": eid,
                  "original_relative_path": f"{sid}/lesson-{number}.mp4",
                  "asset_name": eid + ".mp4", "size_bytes": 99,
                  "download_url": verifier.download_url(sid, eid + ".mp4"),
                  "subtitles": {}}
            assets.append({"name": ep["asset_name"], "id": asset_id,
                           "size": 99, "digest": "sha256:" + "b" * 64,
                           "browser_download_url": ep["download_url"], "state": "uploaded"})
            asset_id += 1
            for suffix in transport.SUFFIXES:
                name = eid + suffix
                if eid == "s05-e001":
                    ep["subtitles"][suffix] = {"status": "missing", "asset_name": name,
                                               "path": None, "download_url": None}
                    continue
                payload = (name + "\n").encode("utf-8")
                digest = hashlib.sha256(payload).hexdigest()
                relative = f"subtitles/{sid}/{name}"
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                url = verifier.download_url(sid, name)
                ep["subtitles"][suffix] = {"status": "matched", "asset_name": name,
                                           "path": relative, "sha256": digest,
                                           "download_url": url}
                assets.append({"name": name, "id": asset_id, "size": len(payload),
                               "digest": "sha256:" + digest,
                               "browser_download_url": url, "state": "uploaded"})
                asset_id += 1
            catalog["episodes"].append(ep)
        baseline["remote_releases"].append({"series_id": sid, "release": release,
                                           "tag_ref": reference, "tag_commit": commit,
                                           "assets": assets})
    return catalog, baseline


class FakeGitHub:
    """Emulate metadata responses; reject everything outside the production GET scope."""
    def __init__(self, baseline, private=True):
        self.records = copy.deepcopy(baseline["remote_releases"])
        self.repository = {"full_name": verifier.REPOSITORY, "id": verifier.REPOSITORY_ID,
                           "private": private, "default_branch": "main"}
        self.calls, self.tag_objects = [], {}

    def get(self, endpoint):
        verifier.check_endpoint(endpoint)
        self.calls.append(endpoint)
        if endpoint == verifier.PREFIX:
            return copy.deepcopy(self.repository)
        for record in self.records:
            tag = record["release"]["tag_name"]
            if endpoint == f"{verifier.PREFIX}/releases/tags/{tag}":
                return copy.deepcopy(record["release"])
            if endpoint == f"{verifier.PREFIX}/git/ref/tags/{tag}":
                return copy.deepcopy(record["tag_ref"])
        prefix = verifier.PREFIX + "/git/tags/"
        if endpoint.startswith(prefix):
            return copy.deepcopy(self.tag_objects[endpoint[len(prefix):]])
        raise AssertionError("Unexpected fake GET route")

    def assets(self, release_id):
        # Exercise production pagination with a page transport that still validates routes.
        record = next(r for r in self.records if r["release"]["id"] == release_id)
        client = verifier.ReadOnlyGitHub()

        def page_get(endpoint):
            verifier.check_endpoint(endpoint)
            self.calls.append(endpoint)
            page = int(endpoint.rsplit("=", 1)[1])
            return copy.deepcopy(record["assets"][(page - 1) * 100:page * 100])
        client.get = page_get
        return client.assets(release_id)


class TransportSafetyTests(unittest.TestCase):
    def test_mutation_and_bodies_rejected_before_process(self):
        client = verifier.ReadOnlyGitHub()
        with mock.patch.object(verifier.subprocess, "run") as run:
            for method in ("POST", "PATCH", "PUT", "DELETE", "HEAD", "get"):
                with self.subTest(method=method), self.assertRaises(verifier.VerificationError):
                    client.request(verifier.PREFIX, method=method)
            for option in ({"payload": {}}, {"source": Path("video.mp4")},
                           {"content_type": "application/octet-stream"}):
                with self.subTest(option=option), self.assertRaises(verifier.VerificationError):
                    client.request(verifier.PREFIX, **option)
            run.assert_not_called()

    def test_arbitrary_urls_queries_binary_endpoints_rejected(self):
        client = verifier.ReadOnlyGitHub()
        forbidden = ("user", "repos/other/project", verifier.PREFIX + "/issues",
                     verifier.PREFIX + "/releases/assets/1", verifier.PREFIX + "/releases/1",
                     verifier.PREFIX + "/releases/tags/series-4-v1",
                     verifier.PREFIX + "/git/ref/tags/series-1-v2",
                     verifier.PREFIX + "/releases/1/assets?per_page=100&page=1&token=private",
                     verifier.PREFIX + "/releases/1/assets?per_page=100&page=12",
                     "https://uploads.github.com/" + verifier.PREFIX + "/releases/1/assets",
                     "https://api.github.com/" + verifier.PREFIX,
                     verifier.PREFIX + "/../other", verifier.PREFIX + "#fragment")
        with mock.patch.object(verifier.subprocess, "run") as run:
            for endpoint in forbidden:
                with self.subTest(endpoint=endpoint), self.assertRaises(verifier.VerificationError):
                    client.get(endpoint)
            with self.assertRaises(verifier.VerificationError):
                client.download(verifier.REPOSITORY, 1, Path("download.mp4"))
            run.assert_not_called()

    def test_explicit_binary_get_only_and_debug_environment_removed(self):
        response = subprocess.CompletedProcess([], 0, b'HTTP/2.0 200 OK\r\n\r\n{"ok":true}', b"")
        with mock.patch.dict(verifier.os.environ, {"GH_DEBUG": "api", "GIT_TRACE": "1"}):
            client = verifier.ReadOnlyGitHub("custom-gh")
        with mock.patch.object(verifier.subprocess, "run", return_value=response) as run:
            self.assertEqual(client.get(verifier.PREFIX), {"ok": True})
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], "custom-gh")
        self.assertEqual(args[0][args[0].index("--method") + 1], "GET")
        self.assertNotIn("--input", args[0])
        self.assertFalse(kwargs["shell"])
        self.assertNotIn("GH_DEBUG", kwargs["env"])
        self.assertNotIn("GIT_TRACE", kwargs["env"])

    def test_finite_transient_retries_reuse_existing_policy(self):
        response = subprocess.CompletedProcess([], 1, b"", b"HTTP 503 SECRET_NEVER_ECHOED")
        client = verifier.ReadOnlyGitHub()
        with mock.patch.object(verifier.subprocess, "run", return_value=response) as run, \
                mock.patch.object(transport.time, "sleep") as sleep:
            with self.assertRaises(transport.GHError) as error:
                client.get(verifier.PREFIX)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertNotIn("SECRET_NEVER_ECHOED", str(error.exception))

    def test_404_and_403_are_distinct_and_not_retried(self):
        for status in (403, 404):
            response = subprocess.CompletedProcess([], 1, b"", f"HTTP {status}".encode())
            with self.subTest(status=status), mock.patch.object(verifier.subprocess, "run", return_value=response) as run:
                with self.assertRaises(transport.GHError) as error:
                    verifier.ReadOnlyGitHub().get(verifier.PREFIX)
                self.assertEqual(error.exception.status, status)
                self.assertEqual(run.call_count, 1)

    def test_retry_after_not_shortened(self):
        response = subprocess.CompletedProcess([], 1, b"HTTP/2.0 429 Error\r\nretry-after: 61\r\n\r\n{}", b"")
        with mock.patch.object(verifier.subprocess, "run", return_value=response) as run, \
                mock.patch.object(transport.time, "sleep") as sleep:
            with self.assertRaises(transport.RetryDeferred):
                verifier.ReadOnlyGitHub().get(verifier.PREFIX)
        self.assertEqual(run.call_count, 1)
        sleep.assert_not_called()


class LibraryInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = temporary_fixture()
        cls.root = Path(cls.temp.name)
        cls.catalog, cls.baseline = fixture(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def check(self, client=None, catalog=None, baseline=None):
        return verifier.verify(client or FakeGitHub(self.baseline),
                               catalog or self.catalog, baseline or self.baseline, self.root)

    def test_all_assets_paginated_with_no_media_reads(self):
        client = FakeGitHub(self.baseline)
        result = self.check(client)
        self.assertTrue(result["passed"])
        self.assertEqual(result["verified_assets"], 966)
        self.assertEqual(result["subtitle_copies_sha256_checked"], 772)
        self.assertEqual(result["video_full_hashes_recomputed"], 0)
        self.assertEqual(result["media_downloads"], 0)
        self.assertEqual(result["remote_writes"], 0)
        self.assertTrue(any("page=3" in call for call in client.calls))
        self.assertFalse(result["public_distribution_rights_verified"])
        self.assertFalse(result["public_access_verified"])

    def test_private_and_public_ignore_old_authorization_and_phase(self):
        baseline = copy.deepcopy(self.baseline)
        baseline.update(phase="B", authorization={"confirmed": False,
                        "expires_at": "2000-01-01T00:00:00Z", "visibility": "private"})
        with mock.patch.object(transport, "_authorization", side_effect=AssertionError("Upload gate called")), \
                mock.patch.object(transport.GHClient, "auth", side_effect=AssertionError("Upload auth called")):
            for private in (True, False):
                with self.subTest(private=private):
                    result = self.check(FakeGitHub(baseline, private), baseline=baseline)
                    self.assertTrue(result["passed"])
                    self.assertEqual(result["visibility_observation"]["visibility"], "private" if private else "public")

    def test_observation_schema_matches_renderer_and_is_timezone_aware(self):
        result = self.check()
        observation = result["visibility_observation"]
        self.assertEqual(observation["repository"], verifier.REPOSITORY)
        self.assertEqual(observation["repository_id"], verifier.REPOSITORY_ID)
        self.assertEqual(observation["id"], verifier.REPOSITORY_ID)
        self.assertTrue(observation["remote_read_only"])
        self.assertTrue(observation["read_only"])
        self.assertFalse(observation["remote_writes"])
        self.assertEqual(observation["observed_at"], observation["checked_at"])
        self.assertIsNotNone(dt.datetime.fromisoformat(observation["observed_at"]).tzinfo)

    def test_wrong_numeric_repository_identity_rejected(self):
        client = FakeGitHub(self.baseline)
        client.repository["id"] += 1
        with self.assertRaises(verifier.VerificationError):
            self.check(client)

    def test_baseline_identity_rejected_before_network(self):
        baseline = copy.deepcopy(self.baseline)
        baseline["repository"]["full_name"] = "another/project"
        client = FakeGitHub(self.baseline)
        with self.assertRaises(verifier.VerificationError):
            self.check(client, baseline=baseline)
        self.assertEqual(client.calls, [])

    def test_attachment_id_name_size_digest_url_conflicts(self):
        replacements = {"id": 999999, "name": "unexpected.mp4", "size": 100,
                        "digest": "sha256:" + "c" * 64,
                        "browser_download_url": "https://example.invalid/private-signature"}
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                client = FakeGitHub(self.baseline)
                client.records[0]["assets"][0][field] = replacement
                result = self.check(client)
                self.assertFalse(result["passed"])
                self.assertNotIn("private-signature", json.dumps(result))

    def test_missing_and_duplicate_attachment_sets_fail(self):
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate):
                client = FakeGitHub(self.baseline)
                item = client.records[0]["assets"].pop()
                if duplicate:
                    client.records[0]["assets"].append(copy.deepcopy(client.records[0]["assets"][0]))
                result = self.check(client)
                self.assertFalse(result["passed"])
                self.assertTrue(any(x["code"] == "remote_attachment_set_conflict" for x in result["issues"]))

    def test_release_identity_and_tag_commit_conflicts_fail(self):
        client = FakeGitHub(self.baseline)
        client.records[0]["release"]["id"] += 999
        client.records[0]["tag_ref"]["object"]["sha"] = "c" * 40
        result = self.check(client)
        codes = {x["code"] for x in result["issues"]}
        self.assertFalse(result["passed"])
        self.assertTrue({"release_invariant_conflict", "tag_object_conflict", "tag_target_commit_conflict"}.issubset(codes))

    def test_annotated_tag_resolution_and_object_identity(self):
        baseline = copy.deepcopy(self.baseline)
        baseline["remote_releases"][0]["tag_ref"]["object"] = {"type": "tag", "sha": "d" * 40}
        client = FakeGitHub(baseline)
        client.tag_objects["d" * 40] = {"sha": "d" * 40, "object": {"type": "commit", "sha": "a" * 40}}
        self.assertTrue(self.check(client, baseline=baseline)["passed"])
        client.tag_objects["d" * 40]["sha"] = "e" * 40
        with self.assertRaises(verifier.VerificationError):
            self.check(client, baseline=baseline)

    def test_natural_download_counts_and_display_notes_can_change(self):
        client = FakeGitHub(self.baseline)
        client.records[0]["assets"][0].update(download_count=900, updated_at="later")
        client.records[0]["release"].update(name="Editorial name", body="Editorial notes", updated_at="later")
        self.assertTrue(self.check(client)["passed"])

    def test_catalog_link_sha_and_stable_id_corruption_rejected(self):
        for change in ("link", "sha", "id"):
            catalog = copy.deepcopy(self.catalog)
            if change == "link":
                catalog["episodes"][0]["download_url"] += "?signature=private"
            elif change == "sha":
                catalog["episodes"][0]["subtitles"][".en.srt"]["sha256"] = "c" * 64
            else:
                catalog["episodes"][0]["episode_id"] = catalog["episodes"][1]["episode_id"]
            with self.subTest(change=change), self.assertRaises(verifier.VerificationError):
                self.check(catalog=catalog)

    def test_missing_subtitle_cannot_disappear_from_catalog(self):
        catalog = copy.deepcopy(self.catalog)
        course = next(x for x in catalog["episodes"] if x["episode_id"] == "s05-e001")
        course["subtitles"].pop(".en.srt")
        with self.assertRaises(verifier.VerificationError):
            self.check(catalog=catalog)

    def test_current_subtitle_bytes_are_checked(self):
        target = self.root / self.catalog["episodes"][0]["subtitles"][".en.srt"]["path"]
        before = target.read_bytes()
        try:
            target.write_bytes(before + b"changed")
            with self.assertRaises(verifier.VerificationError):
                self.check()
        finally:
            target.write_bytes(before)


class ReceiptBoundaryTests(unittest.TestCase):
    def test_public_output_and_existing_receipts_rejected(self):
        with temporary_fixture() as directory:
            root = Path(directory)
            private = root / "_local"
            private.mkdir()
            with self.assertRaises(verifier.VerificationError):
                verifier.private_output_path(root / "repo/result.json", private)
            target = verifier.private_output_path(private / "audit.json", private)
            verifier.write_private(target, {"passed": True}, private)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"passed": True})
            with self.assertRaises(verifier.VerificationError):
                verifier.private_output_path(target, private)

    def test_help_makes_read_only_scope_explicit_without_network(self):
        with mock.patch.object(verifier.subprocess, "run") as run, mock.patch("sys.stdout") as output:
            with self.assertRaises(SystemExit) as exit_status:
                verifier.main(["--help"])
        self.assertEqual(exit_status.exception.code, 0)
        text = "".join(str(args[0]) for args, _ in output.write.call_args_list if args)
        self.assertIn("Read-only", text)
        self.assertIn("no remote writes", text)
        self.assertIn("current", text)
        self.assertIn("--observation", text)
        run.assert_not_called()

    def test_cli_error_does_not_echo_private_input_paths(self):
        secret = "private_input_marker"
        with mock.patch("sys.stdout") as output:
            code = verifier.main(["--catalog", secret + "/missing.json"])
        text = "".join(str(args[0]) for args, _ in output.write.call_args_list if args)
        self.assertEqual(code, 2)
        self.assertNotIn(secret, text)
        self.assertIn("FileNotFoundError", text)


if __name__ == "__main__":
    unittest.main()
