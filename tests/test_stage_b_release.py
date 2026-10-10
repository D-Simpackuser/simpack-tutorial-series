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

    def hide_draft_by_tag(self):
        request = self.fake.request
        def hidden(endpoint, **kwargs):
            if "/releases/tags/" in endpoint:
                self.fake.calls.append(("GET", endpoint))
                raise engine.GHError(404, code=1)
            return request(endpoint, **kwargs)
        return patch.object(self.fake, "request", side_effect=hidden)

    def test_draft_missing_by_tag_is_reused_from_list_without_duplicate_creation(self):
        self.fake.make_release("1")
        with self.hide_draft_by_tag():
            result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertEqual(5, len(self.fake.assets[11]))
        self.assertFalse(any(call == ("POST", f"repos/{REPOSITORY}/releases") for call in self.fake.writes))
        self.assertTrue(any("releases?per_page=" in endpoint for _, endpoint in self.fake.calls))

    def test_draft_creation_by_tag_404_uploads_without_creating_second_release(self):
        with self.hide_draft_by_tag():
            result = self.apply_trial()
        self.assertTrue(result["trial_passed"])
        self.assertEqual(1, len([call for call in self.fake.writes
                                 if call == ("POST", f"repos/{REPOSITORY}/releases")]))
        self.assertEqual(5, len(self.fake.assets[11]))

    def test_created_draft_receipt_is_saved_even_when_first_upload_is_blocked(self):
        request = self.fake.request
        def blocked(endpoint, **kwargs):
            if "/assets?per_page=" in endpoint:
                raise engine.ReleaseError("Mock guard prevents first upload")
            return request(endpoint, **kwargs)
        with patch.object(self.fake, "request", side_effect=blocked):
            with self.assertRaisesRegex(engine.ReleaseError, "Mock guard"):
                self.apply_trial()
        state = self.work.read_json("upload_state.json")
        self.assertEqual(11, state["releases"][REPOSITORY + "/1"]["id"])
        self.assertTrue(state["releases"][REPOSITORY + "/1"]["draft"])
        self.assertEqual({}, state["assets"])
        self.assertEqual(1, len(self.fake.writes))

    def test_remote_observed_receipt_keeps_remote_values_and_missing_nulls(self):
        self.apply_trial()
        key = REPOSITORY + "/s01-e001.mp4"
        recorded = self.work.read_json("upload_state.json")["assets"][key]
        remote = self.fake.assets[11][0]
        self.assertEqual(remote["size"], recorded["remote_size_bytes"])
        self.assertEqual(remote["digest"], recorded["remote_digest"])
        self.assertEqual("uploaded", recorded["remote_asset_state"])
        local_size, local_sha = recorded["size_bytes"], recorded["sha256"]
        remote.update(size=1, digest="sha256:" + "f" * 64, state="starter")
        engine.verify(self.work, "1")
        recorded = self.work.read_json("upload_state.json")["assets"][key]
        self.assertEqual("conflict", recorded["status"])
        self.assertEqual(1, recorded["remote_size_bytes"])
        self.assertEqual("sha256:" + "f" * 64, recorded["remote_digest"])
        self.assertEqual("starter", recorded["remote_asset_state"])
        self.assertEqual(local_size, recorded["size_bytes"])
        self.assertEqual(local_sha, recorded["sha256"])
        self.fake.assets[11].pop(0)
        engine.verify(self.work, "1")
        recorded = self.work.read_json("upload_state.json")["assets"][key]
        self.assertEqual("missing_remote", recorded["status"])
        self.assertIsNone(recorded["remote_size_bytes"])
        self.assertIsNone(recorded["remote_digest"])
        self.assertIsNone(recorded["remote_asset_state"])

    def test_lost_draft_creation_response_is_reconciled_through_release_list(self):
        request = self.fake.request
        def lost(endpoint, **kwargs):
            if "/releases/tags/" in endpoint:
                self.fake.calls.append(("GET", endpoint))
                raise engine.GHError(404, code=1)
            value = request(endpoint, **kwargs)
            if kwargs.get("method") == "POST" and endpoint == f"repos/{REPOSITORY}/releases":
                raise engine.GHError(503, {"retry-after": "0"}, 1)
            return value
        with patch.object(self.fake, "request", side_effect=lost):
            self.assertTrue(self.apply_trial()["trial_passed"])
        self.assertEqual(1, len([call for call in self.fake.writes
                                 if call == ("POST", f"repos/{REPOSITORY}/releases")]))

    def test_draft_list_lookup_paginates_and_rejects_duplicate_exact_tag(self):
        remote = self.fake.make_release("1")
        first_page = [{"id": index + 1000, "tag_name": f"unrelated-{index}"} for index in range(100)]
        request = self.fake.request
        def paginated(endpoint, **kwargs):
            if "/releases/tags/" in endpoint:
                raise engine.GHError(404, code=1)
            if "releases?per_page=100&page=" in endpoint:
                self.fake.calls.append(("GET", endpoint))
                return copy.deepcopy(first_page if endpoint.endswith("page=1") else [remote])
            return request(endpoint, **kwargs)
        with patch.object(self.fake, "request", side_effect=paginated):
            found = engine._release(self.fake, REPOSITORY, COMMIT, "1", create=False)
            self.assertEqual(11, found["id"])
            first_page[0] = copy.deepcopy(remote)
            with self.assertRaisesRegex(engine.ReleaseError, "Multiple remote Releases"):
                engine._release(self.fake, REPOSITORY, COMMIT, "1", create=True)
        self.assertEqual([], self.fake.writes)

    def test_draft_list_lookup_still_rejects_foreign_marker_and_commit(self):
        remote = self.fake.make_release("1")
        # Drafts do not need a Git tag, but must target the authorized commit.
        request = self.fake.request
        def no_tag(endpoint, **kwargs):
            if "/git/ref/tags/" in endpoint or "/releases/tags/" in endpoint:
                raise engine.GHError(404, code=1)
            return request(endpoint, **kwargs)
        with patch.object(self.fake, "request", side_effect=no_tag):
            remote["body"] = "foreign material"
            with self.assertRaisesRegex(engine.ReleaseError, "not marked"):
                self.apply_trial()
            remote["body"] = engine.TASK_MARKER
            remote["target_commitish"] = "b" * 40
            with self.assertRaisesRegex(engine.ReleaseError, "explicit authorized commit"):
                self.apply_trial()
        self.assertEqual([], self.fake.writes)


if __name__ == "__main__":
    unittest.main()
