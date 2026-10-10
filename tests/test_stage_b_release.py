"""Stage B resume/publication safety checks; all GitHub responses are mocked."""
from __future__ import annotations

import copy
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import test_github_release as fixtures

engine = fixtures.engine
COMMIT = fixtures.COMMIT
REPOSITORY = fixtures.REPOSITORY


class StageBReleaseTests(unittest.TestCase):
    # Reuse the existing small source fixtures entirely inside _local.
    setUp = fixtures.ReleaseTests.setUp
    tearDown = fixtures.ReleaseTests.tearDown
    lesson = fixtures.ReleaseTests.lesson
    apply_trial = fixtures.ReleaseTests.apply_trial
    prepopulate_trial = fixtures.ReleaseTests.prepopulate_trial

    def bulk(self, series="1,2"):
        return engine.upload(self.work, series, apply=True,
                             authorization=self.authorization["authorization_id"])

    def publish(self, series="1,2"):
        return engine.release(self.work, series, apply=True,
                              authorization=self.authorization["authorization_id"])

    def test_published_immutable_verified_files_resume_without_writes(self):
        self.apply_trial()
        self.bulk("1")
        self.fake.releases["1"].update(draft=False, immutable=True)
        before = len(self.fake.writes)
        result = self.bulk("1")
        self.assertEqual(10, len(result["assets"]))
        self.assertTrue(all(item["status"] == "skipped_verified" and item["draft"] is False
                            for item in result["assets"]))
        self.assertEqual(before, len(self.fake.writes))

    def test_published_trial_gate_allows_remaining_draft_series(self):
        self.apply_trial()
        self.fake.releases["1"].update(draft=False, immutable=True)
        result = self.bulk("2")
        self.assertEqual(5, len(result["assets"]))
        self.assertTrue(all(item["status"] == "uploaded_verified" for item in result["assets"]))
        self.assertEqual(5, len(self.fake.assets[11]))

    def test_published_missing_requested_asset_refuses_every_new_upload(self):
        self.apply_trial()
        self.fake.releases["1"]["draft"] = False
        before = len(self.fake.writes)
        with self.assertRaisesRegex(engine.ReleaseError, "no write"):
            self.bulk("1")
        self.assertEqual(before, len(self.fake.writes))
        self.assertEqual(5, len(self.fake.assets[11]))

    def test_published_metadata_only_does_not_implicitly_accept_or_upload(self):
        self.prepopulate_trial(digest="none")
        self.fake.releases["1"].update(draft=False, immutable=True)
        with self.assertRaisesRegex(engine.ReleaseError, "matching verified"):
            self.apply_trial()
        self.assertEqual([], self.fake.writes)
        engine.verify(self.work, "1", download=True)
        result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertTrue(all(item["verification"] == "download_verified" for item in result["assets"]))
        self.assertEqual([], self.fake.writes)

    def test_partial_published_set_is_idempotent_and_records_actual_urls(self):
        self.apply_trial()
        self.bulk()
        self.fake.releases["1"].update(draft=False, immutable=True)
        self.fake.assets[11][0]["browser_download_url"] = "https://github.com/owner/demo/actual/new-url"
        before = len(self.fake.writes)
        result = self.publish()
        self.assertEqual(["skipped_published", "published"], [item["status"] for item in result["releases"]])
        writes = self.fake.writes[before:]
        self.assertEqual([("PATCH", f"repos/{REPOSITORY}/releases/12")], writes)
        state = self.work.read_json("upload_state.json")
        self.assertEqual("https://github.com/owner/demo/actual/new-url",
                         state["assets"][REPOSITORY + "/s01-e001.mp4"]["browser_download_url"])
        again = self.publish()
        self.assertTrue(all(item["status"] == "skipped_published" for item in again["releases"]))
        self.assertEqual(before + 1, len(self.fake.writes))

    def test_unexpected_extra_asset_in_later_series_blocks_all_publication(self):
        self.apply_trial()
        self.bulk()
        self.fake.add_asset(12, "unreviewed-material.bin", b"unapproved")
        before = len(self.fake.writes)
        with self.assertRaisesRegex(engine.ReleaseError, "exact authorized inventory"):
            self.publish()
        self.assertEqual(before, len(self.fake.writes))
        self.assertTrue(all(value["draft"] for value in self.fake.releases.values()))
        self.assertIn("unreviewed-material.bin", [item["name"] for item in self.fake.assets[12]])

    def test_explicit_exclusion_does_not_authorize_present_remote_copy(self):
        self.apply_trial()
        self.bulk("1")
        self.authorization["excluded_assets"] = {"s01-e002.mp4": "本轮明确排除"}
        self.work.write_json("authorization.json", self.authorization)
        self.apply_trial()
        before = len(self.fake.writes)
        with self.assertRaisesRegex(engine.ReleaseError, "exact authorized inventory"):
            self.publish("1")
        self.assertEqual(before, len(self.fake.writes))
        self.assertEqual(10, len(self.fake.assets[11]))

    def test_missing_subtitle_keeps_video_and_allows_exact_available_scope(self):
        episodes = copy.deepcopy(self.episodes)
        subtitle = episodes[1]["subtitles"][".en.vtt"]
        Path(subtitle["path"]).unlink()
        subtitle.update(status="missing", size_bytes=0)
        self.work.write_json("inventory.json", {"episodes": episodes})
        self.apply_trial()
        self.bulk("1")
        result = self.publish("1")
        self.assertEqual("published", result["releases"][0]["status"])
        self.assertEqual(9, len(self.fake.assets[11]))
        self.assertIn("s01-e002.mp4", [item["name"] for item in self.fake.assets[11]])

    def test_immutable_draft_never_accepts_upload_or_publication(self):
        self.apply_trial()
        self.bulk("1")
        self.fake.releases["1"]["immutable"] = True
        before = len(self.fake.writes)
        for action in (lambda: self.bulk("1"), lambda: self.publish("1")):
            with self.assertRaisesRegex(engine.ReleaseError, "immutable"):
                action()
        self.assertEqual(before, len(self.fake.writes))

    def test_draft_state_is_rechecked_before_each_byte_send(self):
        self.apply_trial()
        request = self.fake.request
        tag_reads = 0
        def changed(endpoint, **kwargs):
            nonlocal tag_reads
            if endpoint.endswith("releases/tags/series-1-v1"):
                tag_reads += 1
                # Bulk reads the remote gate, then the series, then before POST.
                if tag_reads == 3:
                    self.fake.releases["1"]["draft"] = False
            return request(endpoint, **kwargs)
        before = len(self.fake.writes)
        with patch.object(self.fake, "request", side_effect=changed):
            with self.assertRaisesRegex(engine.ReleaseError, "published or immutable"):
                self.bulk("1")
        self.assertEqual(before, len(self.fake.writes))
        self.assertEqual(5, len(self.fake.assets[11]))

    def test_malformed_success_response_reconciles_once_without_duplicate(self):
        request = self.fake.request
        first = True
        def malformed(endpoint, **kwargs):
            nonlocal first
            response = request(endpoint, **kwargs)
            if kwargs.get("source") is not None and first:
                first = False
                raise engine.GHError(201, {}, "invalid_response")
            return response
        with patch.object(self.fake, "request", side_effect=malformed):
            result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertTrue(all(item["status"] == "uploaded_verified" for item in result["assets"]))
        self.assertEqual(5, len([call for call in self.fake.writes if call[1].startswith("https://")]))
        self.assertEqual(1, len(self.work.read_json("upload_state.json")["retry_events"]))

    def test_cli_invalid_json_raises_sanitized_reconcilable_error(self):
        result = subprocess.CompletedProcess([], 0,
                 b'HTTP/2.0 201 Created\r\nContent-Type: application/json\r\n\r\n{"secret":"private', b'')
        with patch.object(engine.subprocess, "run", return_value=result):
            with self.assertRaises(engine.GHError) as context:
                fixtures.RealGHClient().request("repos/owner/demo/releases", method="POST", payload={})
        self.assertEqual("invalid_response", context.exception.code)
        self.assertTrue(context.exception.transient)
        self.assertNotIn("secret", str(context.exception))
        self.assertNotIn("private", str(context.exception))

    def test_secondary_rate_limit_403_retries_with_retry_after(self):
        request = self.fake.request
        first = True
        def limited(endpoint, **kwargs):
            nonlocal first
            if kwargs.get("source") is not None and first:
                first = False
                raise engine.GHError(403, {"retry-after": "0", "x-ratelimit-remaining": "4000"}, 1)
            return request(endpoint, **kwargs)
        with patch.object(self.fake, "request", side_effect=limited):
            self.assertTrue(self.apply_trial()["trial_passed"])
        self.assertEqual(1, len(self.work.read_json("upload_state.json")["retry_events"]))
        self.assertTrue(engine.GHError(403, {"retry-after": "10"}).transient)
        self.assertFalse(engine.GHError(403).transient)
        self.assertEqual(10, engine._delay(engine.GHError(403, {"retry-after": "10"}), 0))

    def approve_current_names(self):
        self.authorization["approved_existing_asset_names"] = [asset["name"] for asset in engine._candidates(self.episodes)]
        self.work.write_json("authorization.json", self.authorization)

    def add_rescanned_confirmed_lesson(self):
        episode = self.lesson("1", 3, "新增加但本轮未授权的课程")
        self.episodes.append(episode)
        self.work.write_json("inventory.json", {"episodes": self.episodes})
        rights = self.work.read_json("rights.json")
        rights["episodes"][episode["episode_id"]] = {"video": "confirmed", "zh-CN": "confirmed", "en": "confirmed"}
        self.work.write_json("rights.json", rights)

    def test_explicit_filename_scope_blocks_confirmed_new_lesson_before_remote(self):
        self.approve_current_names()
        self.apply_trial()
        self.add_rescanned_confirmed_lesson()
        before = len(self.fake.calls)
        with self.assertRaisesRegex(engine.ReleaseError, "explicit approved filename scope"):
            self.bulk("1")
        self.assertEqual(before, len(self.fake.calls))
        self.assertEqual(5, len(self.fake.assets[11]))

    def test_explicit_filename_scope_blocks_trial_and_malformed_allowlists(self):
        self.approve_current_names()
        self.authorization["approved_existing_asset_names"].remove("s01-e001.en.vtt")
        self.work.write_json("authorization.json", self.authorization)
        with self.assertRaisesRegex(engine.ReleaseError, "explicit approved filename scope"):
            self.apply_trial()
        for approved in (None, [], ["s01-e001.mp4", "s01-e001.mp4"], [123], [" "]):
            self.authorization["approved_existing_asset_names"] = approved
            self.work.write_json("authorization.json", self.authorization)
            with self.assertRaisesRegex(engine.ReleaseError, "approved attachment names"):
                self.apply_trial()
        self.assertEqual([], self.fake.calls)

    def test_explicit_filename_scope_blocks_publication_after_rescan(self):
        self.approve_current_names()
        self.apply_trial()
        self.bulk("1")
        self.add_rescanned_confirmed_lesson()
        before = len(self.fake.calls)
        with self.assertRaisesRegex(engine.ReleaseError, "explicit approved filename scope"):
            self.publish("1")
        self.assertEqual(before, len(self.fake.calls))
        self.assertTrue(self.fake.releases["1"]["draft"])

    def test_approved_filename_snapshot_is_part_of_trial_gate_identity(self):
        self.approve_current_names()
        self.apply_trial()
        # Even an unchanged requested group needs a renewed gate after scope changes.
        self.authorization["approved_existing_asset_names"].remove("s02-e001.en.vtt")
        self.work.write_json("authorization.json", self.authorization)
        before = len(self.fake.calls)
        with self.assertRaisesRegex(engine.ReleaseError, "trial first"):
            self.bulk("1")
        self.assertEqual(before, len(self.fake.calls))


if __name__ == "__main__":
    unittest.main()
