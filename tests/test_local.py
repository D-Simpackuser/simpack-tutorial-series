"""Local scan/build acceptance tests. No network and no real media writes.

All temporary fixtures live below this publishing workspace's _local/tests.
Each fixture has independent simulated source roots and a publishing root.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core
import catalog_engine


SERIES = ("1", "2", "3", "5", "6", "7", "8")
SUFFIXES = (".zh-CN.srt", ".zh-CN.vtt", ".en.srt", ".en.vtt")
SRT = b"1\r\n00:00:00,000 --> 00:00:01,250\r\nhello\r\n\r\n"
VTT = b"WEBVTT\r\n\r\n00:00:00.000 --> 00:00:01.250\r\nhello\r\n\r\n"


class LocalFixture(unittest.TestCase):
    def setUp(self):
        tests_root = Path(__file__).resolve().parents[2] / "_local" / "tests"
        tests_root.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="scan-build-", dir=tests_root)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.video_root = self.base / "视频（源） & readonly"
        self.subtitle_root = self.base / "字幕源"
        self.work_root = self.base / "publish"
        self.work_root.mkdir()
        for sid in SERIES:
            (self.video_root / sid).mkdir(parents=True)
            (self.subtitle_root / sid).mkdir(parents=True)
        self.config = {
            "schema_version": 1,
            "video_root": str(self.video_root),
            "subtitle_root": str(self.subtitle_root),
            "work_root": str(self.work_root),
            "repo_dir": "repo",
            "private_state_dir": "_local",
            "staging_dir": "staging",
            "ffprobe": None,
            "release_max_asset_bytes_exclusive": 2147483648,
            "release_max_assets": 1000,
            "rights_default": "unknown",
            "series": [
                {"id": sid, "display_name": f"系列 {sid}",
                 "release_tag": f"series-{sid}-v1"}
                for sid in SERIES
            ],
            "github": {"owner": None, "repository": "simpack-tutorial-series",
                       "allow_remote_write": False, "initial_visibility": "private"},
        }
        self.work = core.Workspace(self.work_root, self.config)

    def video(self, relative, data=b"fake mp4 fixture, never ffprobe"):
        path = self.video_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def subtitle(self, relative, data=None):
        path = self.subtitle_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            data = VTT if str(relative).endswith(".vtt") else SRT
        path.write_bytes(data)
        return path

    def lesson(self, relative, subtitles=True):
        path = self.video(relative)
        if subtitles:
            stem = str(Path(relative).with_suffix("")).replace("\\", "/")
            for suffix in SUFFIXES:
                self.subtitle(stem + suffix)
        return path

    def episodes(self, inventory):
        return {e["relative_path"].replace("\\", "/"): e for e in inventory["episodes"]}

    def scan(self):
        return catalog_engine.scan(self.work)

    def anomaly_text(self, inventory):
        return json.dumps(inventory.get("anomalies", []), ensure_ascii=False)

    def snapshot(self, root):
        return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns,
                                        core.sha256(p))
                for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


class ScanTests(LocalFixture):
    def test_full_stem_and_special_characters_match_all_four_formats(self):
        name = "1/3-Simpack 柔性（钢轨）(半角) & 连接.fbi生成.mp4"
        self.lesson(name)
        episode = self.episodes(self.scan())[name]
        self.assertEqual(episode["title"], Path(name).stem)
        self.assertEqual(set(episode["subtitles"]), set(SUFFIXES))
        self.assertTrue(all(episode["subtitles"][s]["status"] == "matched"
                            for s in SUFFIXES))
        self.assertEqual(episode["video"]["size_bytes"], len(b"fake mp4 fixture, never ffprobe"))
        self.assertIsNone(episode["duration_seconds"])

    def test_repeated_numeric_prefixes_are_independent_episodes(self):
        paths = ("8/9-11-第一标题.mp4", "8/9-11-第二标题.mp4",
                 "2/12-2-模型.mp4", "2/12-2-结果.mp4")
        for path in paths:
            self.lesson(path)
        episodes = self.episodes(self.scan())
        self.assertEqual(set(episodes), set(paths))
        self.assertEqual(len({e["episode_id"] for e in episodes.values()}), 4)
        self.assertEqual(len({e["video"]["asset_name"] for e in episodes.values()}), 4)
        for ep in episodes.values():
            self.assertTrue(all(s["status"] == "matched" for s in ep["subtitles"].values()))

    def test_subtitles_match_same_directory_only(self):
        self.video("1/subfolder/1-课程.mp4")
        for suffix in SUFFIXES:
            self.subtitle("1/1-课程" + suffix)
            self.subtitle("2/subfolder/1-课程" + suffix)
        episode = self.episodes(self.scan())["1/subfolder/1-课程.mp4"]
        self.assertTrue(all(s["status"] == "missing" for s in episode["subtitles"].values()))

    def test_series_five_missing_effect_lesson_is_retained(self):
        self.lesson("5/0-课程效果.mp4", subtitles=False)
        inventory = self.scan()
        episode = self.episodes(inventory)["5/0-课程效果.mp4"]
        self.assertEqual(episode["series_id"], "5")
        self.assertTrue(all(s["status"] == "missing" for s in episode["subtitles"].values()))
        self.assertIn("0-课程效果", self.anomaly_text(inventory))

    def test_case_and_unicode_variants_are_only_candidates(self):
        self.video("1/1-Courseé.mp4")
        self.subtitle("1/1-coursee\u0301.zh-CN.srt")
        inventory = self.scan()
        episode = self.episodes(inventory)["1/1-Courseé.mp4"]
        self.assertEqual(episode["subtitles"][".zh-CN.srt"]["status"], "missing")
        text = self.anomaly_text(inventory)
        self.assertIn("1-course", text)
        self.assertRegex(text.lower(), r"candidate|uncertain|候选|不确定")

    def test_orphan_zero_byte_and_invalid_subtitles_are_reported(self):
        self.lesson("1/1-课程.mp4", subtitles=False)
        self.subtitle("1/1-课程.zh-CN.srt", b"")
        self.subtitle("1/1-课程.zh-CN.vtt", b"not a VTT document")
        self.subtitle("1/1-课程.en.srt", b"\xff\xfe\xff")
        self.subtitle("1/孤立.en.vtt")
        inventory = self.scan()
        ep = self.episodes(inventory)["1/1-课程.mp4"]
        self.assertEqual(ep["subtitles"][".zh-CN.srt"]["status"], "zero_byte")
        self.assertEqual(ep["subtitles"][".zh-CN.vtt"]["status"], "invalid")
        self.assertEqual(ep["subtitles"][".en.srt"]["status"], "invalid")
        self.assertEqual(ep["subtitles"][".en.vtt"]["status"], "missing")
        self.assertIn("孤立.en.vtt", self.anomaly_text(inventory))

    def test_empty_video_is_reported_without_fabricated_hash(self):
        self.video("1/1-empty.mp4", b"")
        inventory = self.scan()
        ep = self.episodes(inventory)["1/1-empty.mp4"]
        self.assertEqual(ep["video"]["size_bytes"], 0)
        self.assertNotEqual(ep["video"]["status"], "ready")
        self.assertFalse(ep["video"].get("sha256"))
        self.assertIn("1-empty.mp4", self.anomaly_text(inventory))

    def test_overlap_is_reported_without_rewriting_valid_subtitle(self):
        self.lesson("1/1-overlap.mp4", subtitles=False)
        overlap = (b"1\r\n00:00:00,000 --> 00:00:02,000\r\none\r\n\r\n"
                   b"2\r\n00:00:01,000 --> 00:00:03,000\r\ntwo\r\n\r\n")
        source = self.subtitle("1/1-overlap.zh-CN.srt", overlap)
        inventory = self.scan()
        ep = self.episodes(inventory)["1/1-overlap.mp4"]
        self.assertEqual(ep["subtitles"][".zh-CN.srt"]["status"], "matched")
        self.assertRegex(self.anomaly_text(inventory).lower(), r"overlap|重叠")
        self.assertEqual(source.read_bytes(), overlap)
        self.assertIsNone(ep["duration_seconds"])

    def test_reversed_or_impossible_timestamp_is_invalid(self):
        self.lesson("1/1-invalid-time.mp4", subtitles=False)
        self.subtitle("1/1-invalid-time.zh-CN.srt",
                      b"1\n00:00:02,000 --> 00:00:01,000\nreverse\n")
        self.subtitle("1/1-invalid-time.en.vtt",
                      b"WEBVTT\n\n00:99:00.000 --> 00:99:01.000\nbad minute\n")
        ep = self.episodes(self.scan())["1/1-invalid-time.mp4"]
        self.assertEqual(ep["subtitles"][".zh-CN.srt"]["status"], "invalid")
        self.assertEqual(ep["subtitles"][".en.vtt"]["status"], "invalid")

    def test_scan_does_not_modify_sources_or_claim_video_hashes(self):
        self.lesson("1/1-课程.mp4")
        before = (self.snapshot(self.video_root), self.snapshot(self.subtitle_root))
        inventory = self.scan()
        self.assertEqual(before, (self.snapshot(self.video_root), self.snapshot(self.subtitle_root)))
        ep = next(iter(self.episodes(inventory).values()))
        self.assertFalse(ep["video"].get("sha256"))
        for filename in ("inventory.json", "inventory.csv", "id_map.json", "rights.json",
                         "scan_report.md"):
            self.assertTrue(self.work.local(filename).is_file(), filename)
        self.assertTrue(self.work.local("inventory.csv").read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_unreadable_sources_are_reported(self):
        video = self.lesson("1/1-unreadable.mp4")
        subtitle = self.subtitle_root / "1/1-unreadable.zh-CN.srt"
        original_open = Path.open

        def restricted_open(path, *args, **kwargs):
            if path in (video, subtitle):
                raise PermissionError("simulated read denial")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", restricted_open):
            inventory = self.scan()
        ep = self.episodes(inventory)["1/1-unreadable.mp4"]
        self.assertEqual(ep["video"]["status"], "unreadable")
        self.assertEqual(ep["subtitles"][".zh-CN.srt"]["status"], "unreadable")
        self.assertIn("unreadable", self.anomaly_text(inventory))

    def test_duration_bounds_checked_only_with_actual_duration(self):
        path = self.subtitle("1/1-duration.en.vtt")
        unknown = core.validate_subtitle(path, duration=None)
        self.assertTrue(unknown["valid"])
        self.assertFalse(unknown["bounds_checked"])
        short = core.validate_subtitle(path, duration=0.5)
        self.assertTrue(short["bounds_checked"])
        self.assertFalse(short["valid"])
        self.assertRegex(json.dumps(short["issues"]), r"beyond|duration|越界")

    def test_natural_sort_and_stable_ids_survive_insertion(self):
        paths = ("1/10-课程.mp4", "1/2-课程.mp4", "1/9-11-课程.mp4",
                 "1/9-9-课程.mp4", "1/9-2-课程.mp4", "1/1-课程.mp4")
        for path in paths:
            self.lesson(path)
        inventory = self.scan()
        first = self.episodes(inventory)
        expected = sorted(paths, key=core.natural_key)
        actual = [e["relative_path"].replace("\\", "/") for e in inventory["episodes"]]
        self.assertEqual(actual, expected)
        self.assertEqual([first[p]["episode_id"] for p in expected],
                         [f"s01-e{i:03d}" for i in range(1, len(paths) + 1)])
        self.lesson("1/0-新增.mp4")
        second = self.episodes(self.scan())
        for path in paths:
            self.assertEqual(first[path]["episode_id"], second[path]["episode_id"])
        self.assertEqual(second["1/0-新增.mp4"]["episode_id"], "s01-e007")

    def test_removed_or_renamed_path_is_reported_and_not_reused(self):
        self.lesson("1/1-旧名称.mp4")
        first = self.episodes(self.scan())["1/1-旧名称.mp4"]["episode_id"]
        (self.video_root / "1/1-旧名称.mp4").rename(self.video_root / "1/1-新名称.mp4")
        inventory = self.scan()
        new = self.episodes(inventory)["1/1-新名称.mp4"]["episode_id"]
        self.assertNotEqual(new, first)
        self.assertIn("1-旧名称.mp4", self.anomaly_text(inventory))

    def test_extra_series_four_is_not_invented_or_silently_absorbed(self):
        self.lesson("4/1-意外目录.mp4")
        self.lesson("5/1-真实课程.mp4")
        inventory = self.scan()
        self.assertEqual(set(e["series_id"] for e in inventory["episodes"]), {"5"})
        self.assertIn("4", self.anomaly_text(inventory))


class BoundaryTests(LocalFixture):
    def test_asset_size_limit_is_exclusive(self):
        self.assertTrue(core.asset_allowed(2147483647))
        self.assertFalse(core.asset_allowed(2147483648))
        self.assertFalse(core.asset_allowed(2147483649))
        self.assertFalse(core.asset_allowed(0))

    def test_relative_source_escape_is_rejected(self):
        self.lesson("1/1-课程.mp4")
        self.assertEqual(core.safe_source(self.video_root, "1/1-课程.mp4"),
                         (self.video_root / "1/1-课程.mp4").resolve())
        for rel in ("../outside.mp4", str(self.base / "outside.mp4"),
                    "1/../../../outside.mp4"):
            with self.subTest(relative=rel), self.assertRaises((ValueError, OSError)):
                core.safe_source(self.video_root, rel)

    def test_private_and_repo_write_escape_is_rejected(self):
        for method in (self.work.local, self.work.repo):
            for rel in ("../outside.txt", str(self.base / "outside.txt")):
                with self.subTest(method=method.__name__, relative=rel):
                    with self.assertRaises((ValueError, OSError)):
                        method(rel)
        with self.assertRaises((ValueError, OSError)):
            self.work.write_json("../outside.json", {"unsafe": True})
        self.assertFalse((self.base / "outside.json").exists())

    def test_source_root_cannot_overlap_work_root(self):
        bad = dict(self.config)
        bad["video_root"] = str(self.work_root / "video")
        with self.assertRaises((ValueError, OSError)):
            core.Workspace(self.work_root, bad)
        bad["video_root"] = str(self.base)
        with self.assertRaises((ValueError, OSError)):
            core.Workspace(self.work_root, bad)

    def test_reparse_escape_is_skipped_when_symlinks_supported(self):
        outside = self.base / "outside.mp4"
        outside.write_bytes(b"should not be scanned")
        link = self.video_root / "1/link.mp4"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"Windows account cannot create symlink: {exc}")
        inventory = self.scan()
        self.assertNotIn("1/link.mp4", self.episodes(inventory))
        self.assertIn("link.mp4", self.anomaly_text(inventory))
        with self.assertRaises((ValueError, OSError)):
            core.safe_source(self.video_root, "1/link.mp4")

    def test_write_link_escape_is_rejected_when_symlinks_supported(self):
        outside = self.base / "outside-dir"
        outside.mkdir()
        link = self.work.local("escape")
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Windows account cannot create symlink: {exc}")
        with self.assertRaises((ValueError, OSError)):
            self.work.write_json("escape/file.json", {"unsafe": True})
        self.assertFalse((outside / "file.json").exists())

    def test_mocked_reparse_file_is_skipped_and_source_access_rejected(self):
        link = self.video("1/reparse.mp4")
        original_is_link = core.is_link

        def reparse(path):
            return Path(path) == link or original_is_link(path)

        with patch.object(core, "is_link", reparse):
            inventory = self.scan()
            with self.assertRaises((ValueError, OSError)):
                core.safe_source(self.video_root, "1/reparse.mp4")
        self.assertNotIn("1/reparse.mp4", self.episodes(inventory))
        self.assertIn("reparse.mp4", self.anomaly_text(inventory))

    def test_mocked_reparse_parent_prevents_writes(self):
        parent = self.work.local("reparse-dir")
        parent.mkdir()
        original_is_link = core.is_link

        def reparse(path):
            return Path(path) == parent or original_is_link(path)

        with patch.object(core, "is_link", reparse):
            with self.assertRaises((ValueError, OSError)):
                self.work.write_json("reparse-dir/private.json", {})
        self.assertFalse((parent / "private.json").exists())


class BuildTests(LocalFixture):
    def test_build_rejects_changed_video_since_saved_scan(self):
        video = self.lesson("1/1-课程.mp4")
        self.scan()
        video.write_bytes(b"changed fixture bytes after saved scan")
        with self.assertRaisesRegex(ValueError, r"changed|scan"):
            catalog_engine.build(self.work)
        self.assertFalse(self.work.repo("README.md").exists())

    def test_build_rejects_new_source_file_since_saved_scan(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        self.video("2/1-新增.mp4")
        with self.assertRaisesRegex(ValueError, r"changed|scan"):
            catalog_engine.build(self.work)
        self.assertFalse(self.work.repo("README.md").exists())

    def test_build_rejects_removed_source_file_since_saved_scan(self):
        video = self.lesson("1/1-课程.mp4")
        self.scan()
        video.unlink()
        with self.assertRaisesRegex(ValueError, r"changed|scan"):
            catalog_engine.build(self.work)
        self.assertFalse(self.work.repo("README.md").exists())

    def test_provenance_contains_standalone_remote_preflight_marker(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        catalog_engine.build(self.work)
        lines = self.work.repo("PROVENANCE.md").read_text(encoding="utf-8").splitlines()
        self.assertIn("simpack-local-publish-v1", lines)

    def test_only_published_verified_repository_scoped_returned_links_render(self):
        for number in range(1, 8):
            self.lesson(f"1/{number}-链接状态.mp4", subtitles=False)
        inventory = self.scan()
        episodes = inventory["episodes"]
        repository = "actual-owner/simpack-tutorial-series"
        state = {"schema_version": 1, "repository": repository, "assets": {}}
        returned_urls = []
        for number, ep in enumerate(episodes, 1):
            # Remote URLs deliberately use different asset names and tag paths
            # from the local plan, proving the renderer uses API-returned URLs.
            url = f"https://github.com/{repository}/releases/download/actual-tag/API-returned-{number}.mp4"
            returned_urls.append(url)
            record = {"status": "verified", "verification": "verified", "draft": False,
                      "visibility": "public", "browser_download_url": url,
                      "remote_name": f"API-returned-{number}.mp4"}
            key = repository + "/" + ep["video"]["asset_name"]
            if number == 2:
                record.update(visibility="private", verification="download_verified")
            elif number == 3:
                record["draft"] = True
            elif number == 4:
                record.update(status="metadata_only", verification="metadata_only")
            elif number == 5:
                # Neither another repository's record nor legacy unscoped
                # state can supply a verified URL for this repository.
                state["assets"][ep["video"]["asset_name"]] = dict(record)
                key = "another-owner/another-repository/" + ep["video"]["asset_name"]
            elif number == 6:
                record.pop("draft")
            elif number == 7:
                record.pop("browser_download_url")
            state["assets"][key] = record
        self.work.write_json("upload_state.json", state)
        catalog_engine.build(self.work)
        public = self.work.repo("catalog.json").read_text(encoding="utf-8")
        output = json.loads(public)["episodes"]
        self.assertEqual([ep["download_url"] for ep in output],
                         returned_urls[:2] + [None] * 5)
        self.assertEqual(output[1]["download_visibility"], "private")
        self.assertRegex(output[1]["download_status"], r"访问权限|access")
        series = self.work.repo("series/1/README.md").read_text(encoding="utf-8")
        for number, ep in enumerate(output, 1):
            page = self.work.repo(f"lessons/{ep['episode_id']}.md").read_text(encoding="utf-8")
            if number <= 2:
                self.assertIn(f"]({returned_urls[number - 1]})", page)
                self.assertIn(f"]({returned_urls[number - 1]})", series)
            else:
                self.assertNotIn(returned_urls[number - 1], page)
                self.assertNotIn(returned_urls[number - 1], series)
                self.assertNotIn(returned_urls[number - 1], public)
                self.assertNotIn("[下载视频]", page)
        private_page = self.work.repo(f"lessons/{output[1]['episode_id']}.md").read_text(encoding="utf-8")
        self.assertRegex(private_page, r"访问权限|access")

    def test_fresh_legacy_guide_keeps_upload_controls_without_maintenance_dependencies(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        catalog_engine.build(self.work)
        guide = self.work.repo("docs/publishing.md").read_text(encoding="utf-8")
        self.assertNotIn("Maintaining the existing library", guide)
        self.assertNotIn("](architecture.md)", guide)
        self.assertNotIn("publish.py i18n-validate", guide)
        for retained_control in ("simpack-local-publish-v1", "approved_existing_asset_names",
                                 "阶段 B 前提", "同名内容不同不覆盖、不删除"):
            self.assertIn(retained_control, guide)
        result = catalog_engine.audit(self.work)
        self.assertTrue(result['passed'], result['issues'])

    def test_audit_does_not_add_unmanaged_benign_file_to_publish_manifest(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        catalog_engine.build(self.work)
        unrelated = self.work.repo("unrelated.txt")
        unrelated.write_bytes(b"Benign unrelated user file\n")
        audit = catalog_engine.audit(self.work)
        self.assertTrue(audit["passed"], audit["issues"])
        self.assertNotIn("unrelated.txt", audit["candidate_files"])
        self.assertIn("unrelated.txt", audit["excluded_unmanaged_files"])
        manifest = self.work.read_json("catalog_only_file_manifest.json")
        self.assertNotIn("unrelated.txt", manifest["files"])
        self.assertEqual(unrelated.read_bytes(), b"Benign unrelated user file\n")

    def test_failed_git_index_query_blocks_audit(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        catalog_engine.build(self.work)
        self.work.repo(".git").mkdir()
        failed = SimpleNamespace(returncode=128, stdout=b"", stderr=b"simulated git error")
        with patch.object(catalog_engine.shutil, "which", return_value="mock-git"), \
                patch.object(catalog_engine.subprocess, "run", return_value=failed) as run:
            audit = catalog_engine.audit(self.work)
        self.assertFalse(audit["passed"])
        self.assertTrue(audit["git_index_checked"])
        self.assertRegex(json.dumps(audit["issues"]), r"git_index_query_failed")
        self.assertFalse(self.work.read_json("catalog_only_file_manifest.json")["audit_passed"])
        command = run.call_args.args[0]
        self.assertIsInstance(command, list)
        self.assertIn("--cached", command)
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_invalid_ffprobe_duration_is_unknown(self):
        video = self.video("1/1-duration.mp4")
        self.work.config["ffprobe"] = "mock-ffprobe"
        for duration in ("-1", "NaN", "Infinity", "-Infinity"):
            with self.subTest(duration=duration):
                response = SimpleNamespace(returncode=0,
                    stdout=json.dumps({"format": {"duration": duration}}))
                with patch.object(catalog_engine.subprocess, "run", return_value=response) as run:
                    value, status = catalog_engine._duration(self.work, video)
                self.assertIsNone(value)
                self.assertEqual(status, "probe_failed")
                self.assertIs(run.call_args.kwargs["shell"], False)

    def test_build_has_seven_series_one_page_per_video_and_verbatim_subtitles(self):
        for sid in SERIES:
            self.lesson(f"{sid}/1-中文课程（{sid}） & .fbi生成.mp4")
        before = (self.snapshot(self.video_root), self.snapshot(self.subtitle_root))
        inventory = self.scan()
        catalog_engine.build(self.work)
        self.assertEqual(before, (self.snapshot(self.video_root), self.snapshot(self.subtitle_root)))
        self.assertEqual({p.parent.name for p in self.work.repo("series").glob("*/README.md")},
                         set(SERIES))
        self.assertFalse(self.work.repo("series/4").exists())
        self.assertEqual(len(list(self.work.repo("lessons").glob("*.md"))), 7)
        copied = list(self.work.repo("subtitles").rglob("*"))
        self.assertEqual(len([p for p in copied if p.is_file() and p.suffix in (".srt", ".vtt")]), 28)
        for episode in inventory["episodes"]:
            for suffix in SUFFIXES:
                source = self.subtitle_root / (str(Path(episode["relative_path"]).with_suffix("")) + suffix)
                target = self.work.repo(f"subtitles/{episode['series_id']}/{episode['episode_id']}{suffix}")
                self.assertEqual(source.read_bytes(), target.read_bytes())
                self.assertEqual(core.sha256(source), core.sha256(target))
        attributes = self.work.repo(".gitattributes").read_text(encoding="utf-8")
        self.assertRegex(attributes, r"\*\.srt\s+-text")
        self.assertRegex(attributes, r"\*\.vtt\s+-text")

    def test_no_video_private_path_or_private_config_is_emitted(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        inventory = self.work.read_json("inventory.json")
        inventory["future_private_field"] = "TEST_SECRET_NEVER_PUBLIC_7851"
        inventory["episodes"][0]["future_private_field"] = "TEST_SECRET_NEVER_PUBLIC_7851"
        inventory["episodes"][0]["video"]["future_private_field"] = "TEST_SECRET_NEVER_PUBLIC_7851"
        self.work.write_json("inventory.json", inventory)
        catalog_engine.build(self.work)
        for path in self.work.repo("").rglob("*"):
            if not path.is_file():
                continue
            self.assertNotIn(path.suffix.lower(), (".mp4", ".mkv", ".mov", ".avi", ".log"))
            self.assertNotIn(path.name, ("config.json", "rights.json", "upload_state.json", ".env"))
            if path.suffix.lower() in (".md", ".json", ".py", ".txt") or path.name.startswith("."):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("TEST_SECRET_NEVER_PUBLIC_7851", content, str(path))
                for private in (self.video_root, self.subtitle_root, self.work_root):
                    self.assertNotIn(str(private), content, str(path))
                    self.assertNotIn(str(private).replace("\\", "\\\\"), content, str(path))
        public = json.loads(self.work.repo("catalog.json").read_text(encoding="utf-8"))
        self.assertNotIn("video_root", json.dumps(public))
        self.assertNotIn("subtitle_root", json.dumps(public))

    def test_generated_markdown_relative_links_resolve_and_title_is_safe(self):
        # Angle brackets are forbidden in Windows file names. Inject an HTML
        # special title into this simulated inventory to test renderer escaping.
        self.lesson("1/1-[中文]（括号） & .fbi生成.mp4")
        self.scan()
        inventory = self.work.read_json("inventory.json")
        inventory["episodes"][0]["title"] += " <script>"
        self.work.write_json("inventory.json", inventory)
        catalog_engine.build(self.work)
        for path in self.work.repo("").rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("<script>", content, str(path))
            for target in re.findall(r"\]\(([^)]+)\)", content):
                target = target.strip().split(" ", 1)[0].strip("<>")
                url = urlsplit(target)
                if url.scheme or target.startswith("#") or not url.path:
                    continue
                resolved = (path.parent / unquote(url.path)).resolve()
                self.assertTrue(resolved.is_relative_to(self.work.repo("").resolve()), target)
                self.assertTrue(resolved.exists(), f"Broken link in {path.name}: {target}")

    def test_missing_subtitles_are_not_fabricated(self):
        self.lesson("5/0-课程效果.mp4", subtitles=False)
        inventory = self.scan()
        catalog_engine.build(self.work)
        ep = inventory["episodes"][0]
        self.assertTrue(self.work.repo(f"lessons/{ep['episode_id']}.md").is_file())
        self.assertEqual(list(self.work.repo("subtitles").rglob("*.srt")), [])
        self.assertEqual(list(self.work.repo("subtitles").rglob("*.vtt")), [])
        lesson = self.work.repo(f"lessons/{ep['episode_id']}.md").read_text(encoding="utf-8")
        self.assertRegex(lesson, r"缺失|missing")

    def test_repeat_build_backs_up_previously_generated_file(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        catalog_engine.build(self.work)
        original = self.work.repo("README.md").read_bytes()
        self.lesson("2/1-新增.mp4")
        self.scan()
        catalog_engine.build(self.work)
        backups = [p for p in self.work.local("backups").rglob("*") if p.is_file()]
        self.assertTrue(any(p.read_bytes() == original for p in backups),
                        "Previous generated README must be retained in _local/backups")

    def test_unowned_existing_file_is_not_overwritten(self):
        self.lesson("1/1-课程.mp4")
        self.scan()
        readme = self.work.repo("README.md")
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_bytes(b"Unrelated user document\n")
        try:
            catalog_engine.build(self.work)
        except (ValueError, OSError, RuntimeError):
            pass
        self.assertEqual(readme.read_bytes(), b"Unrelated user document\n")


if __name__ == "__main__":
    unittest.main()
