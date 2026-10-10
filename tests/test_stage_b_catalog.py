"""Stage B catalogue/index regressions; fixtures only, no remote calls."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_local import LocalFixture
import catalog_engine
import publish


class StageBCatalogTests(LocalFixture):
    def prepare(self, confirmed=True):
        self.lesson('1/1-真实课程.mp4')
        inventory = self.scan()
        self.ep = inventory['episodes'][0]
        self.config['phase'] = 'B'
        if confirmed:
            rights = self.work.read_json('rights.json')
            rights['episodes'][self.ep['episode_id']].update(video='confirmed', **{'zh-CN': 'confirmed', 'en': 'confirmed'})
            self.work.write_json('rights.json', rights)
        catalog_engine.build(self.work)
        return self.ep

    def manifest(self, paths):
        self.work.write_json('stage_b_stage_manifest.json', {'files': paths})

    def staged_audit(self, blobs, manifest=None, modes=None):
        self.manifest(list(blobs) if manifest is None else manifest)
        self.work.repo('.git').mkdir(exist_ok=True)
        def fake_git(args, **kwargs):
            self.assertIs(kwargs.get('shell'), False)
            if 'diff' in args:
                output = b'\0'.join(path.encode('utf-8') for path in blobs) + b'\0'
            elif 'ls-files' in args:
                output = b''.join((modes or {}).get(path, b'100644') + b' ' + b'0' * 40 + b' 0\t' +
                                  path.encode('utf-8') + b'\0' for path in blobs)
            elif 'show' in args:
                output = blobs[args[-1][1:]]
            else:
                raise AssertionError(args)
            return SimpleNamespace(returncode=0, stdout=output, stderr=b'')
        with patch.object(catalog_engine.shutil, 'which', return_value='fixture-git'), \
                patch.object(catalog_engine.subprocess, 'run', side_effect=fake_git):
            return catalog_engine.audit(self.work)

    def test_authorized_staged_catalogue_and_subtitle_are_allowed(self):
        ep = self.prepare()
        sub = f'subtitles/1/{ep["episode_id"]}.zh-CN.srt'
        result = self.staged_audit({'README.md': self.work.repo('README.md').read_bytes(), sub: self.work.repo(sub).read_bytes()})
        self.assertTrue(result['passed'], result['issues'])
        self.assertIn(sub, result['confirmed_subtitle_material_files'])

    def test_unconfirmed_subtitle_is_blocked_even_when_manifest_names_it(self):
        ep = self.prepare(confirmed=False)
        sub = f'subtitles/1/{ep["episode_id"]}.zh-CN.srt'
        result = self.staged_audit({sub: self.work.repo(sub).read_bytes()})
        self.assertFalse(result['passed'])
        self.assertIn(sub, result['unconfirmed_material_files'])
        self.assertIn('unauthorized_staged_file', json.dumps(result['issues']))

    def test_staged_owned_file_outside_exact_manifest_is_blocked(self):
        self.prepare()
        result = self.staged_audit({'README.md': self.work.repo('README.md').read_bytes()}, manifest=[])
        self.assertFalse(result['passed'])
        self.assertIn('unauthorized_staged_file', json.dumps(result['issues']))

    def test_confirmed_language_cannot_expand_exact_attachment_authorization(self):
        ep = self.prepare()
        approved = ep['subtitles']['.zh-CN.srt']['asset_name']
        excluded = ep['subtitles']['.zh-CN.vtt']['asset_name']
        self.work.write_json('authorization.json', {'approved_existing_asset_names': [approved]})
        approved_path = f'subtitles/1/{approved}'
        allowed = self.staged_audit({approved_path: self.work.repo(approved_path).read_bytes()})
        self.assertTrue(allowed['passed'], allowed['issues'])
        excluded_path = f'subtitles/1/{excluded}'
        blocked = self.staged_audit({excluded_path: self.work.repo(excluded_path).read_bytes()})
        self.assertFalse(blocked['passed'])
        self.assertIn('unauthorized_staged_file', json.dumps(blocked['issues']))

    def test_unmanaged_extra_file_is_filtered_and_cannot_be_authorized_by_manifest(self):
        self.prepare()
        self.work.repo('someone-else.txt').write_bytes(b'Unrelated material\n')
        self.manifest(['README.md'])
        result = catalog_engine.audit(self.work)
        self.assertTrue(result['passed'], result['issues'])
        self.assertIn('someone-else.txt', result['excluded_unmanaged_files'])
        result = self.staged_audit({'someone-else.txt': b'Unrelated material\n'})
        self.assertFalse(result['passed'])
        self.assertIn('unauthorized_stage_manifest_file', json.dumps(result['issues']))

    def test_staged_blob_is_scanned_even_if_working_copy_is_safe(self):
        self.prepare()
        private_path = 'C:' + chr(92) + chr(92).join(('Users', 'someone', 'Desktop', 'file'))
        result = self.staged_audit({'README.md': ('private: ' + private_path + '\n').encode('utf-8')})
        self.assertFalse(result['passed'])
        self.assertIn('private_path_or_credential_in_staged_blob', json.dumps(result['issues']))

    def test_staged_subtitle_must_match_original_sha256(self):
        ep = self.prepare()
        sub = f'subtitles/1/{ep["episode_id"]}.en.vtt'
        result = self.staged_audit({sub: self.work.repo(sub).read_bytes().replace(b'hello', b'changed')})
        self.assertFalse(result['passed'])
        self.assertIn('staged_subtitle_sha256_mismatch', json.dumps(result['issues']))

    def test_staged_link_mode_is_rejected(self):
        self.prepare()
        result = self.staged_audit({'README.md': b'other-file'}, modes={'README.md': b'120000'})
        self.assertFalse(result['passed'])
        self.assertIn('unsafe_staged_file_mode', json.dumps(result['issues']))

    def test_build_uses_fresh_confirmed_rights_and_api_returned_private_links(self):
        ep = self.prepare()
        repository = 'actual-owner/simpack-tutorial-series'
        video_url = f'https://github.com/{repository}/releases/download/api-tag/actual-video.mp4'
        subtitle_url = f'https://github.com/{repository}/releases/download/api-tag/actual-subtitle.srt'
        release_url = f'https://github.com/{repository}/releases/tag/api-tag'
        record = {'status': 'verified', 'verification': 'verified', 'draft': False, 'visibility': 'private'}
        self.work.write_json('upload_state.json', {
            'repository': repository, 'visibility': 'private',
            'assets': {f'{repository}/{ep["video"]["asset_name"]}': dict(record, browser_download_url=video_url),
                       f'{repository}/{ep["subtitles"][".zh-CN.srt"]["asset_name"]}': dict(record, browser_download_url=subtitle_url)},
            'releases': {f'{repository}/1': {'draft': False, 'html_url': release_url}}})
        catalog_engine.build(self.work)
        readme = self.work.repo('README.md').read_text(encoding='utf-8')
        series = self.work.repo('series/1/README.md').read_text(encoding='utf-8')
        self.assertIn('本轮已确认 1 课', readme)
        self.assertIn(f']({release_url})', readme)
        self.assertIn(f']({video_url})', series)
        self.assertIn(f']({subtitle_url})', series)
        self.assertIn('需仓库访问权限', series)
        data = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        self.assertEqual(7, len(data['series']))
        self.assertEqual(release_url, data['series'][0]['release_url'])
        self.assertIsNone(data['series'][1]['release_url'])

    def test_draft_or_unverified_subtitle_and_release_urls_never_render(self):
        ep = self.prepare()
        repository = 'owner/repository'
        hidden = f'https://github.com/{repository}/releases/download/tag/private-draft.srt'
        release_hidden = f'https://github.com/{repository}/releases/tag/private-draft'
        self.work.write_json('upload_state.json', {'repository': repository,
            'assets': {f'{repository}/{ep["subtitles"][".en.srt"]["asset_name"]}': {
                'status': 'verified', 'verification': 'verified', 'draft': True, 'browser_download_url': hidden}},
            'releases': {f'{repository}/1': {'draft': True, 'html_url': release_hidden}}})
        catalog_engine.build(self.work)
        public = self.work.repo('catalog.json').read_text(encoding='utf-8') + self.work.repo('README.md').read_text(encoding='utf-8')
        self.assertNotIn(hidden, public)
        self.assertNotIn(release_hidden, public)
        self.assertIn('草稿待发布', public)

    def test_stage_b_report_preserves_actual_pending_reason_and_partial_counts(self):
        ep = self.prepare()
        self.manifest(['README.md'])
        repository = 'owner/repository'
        self.work.write_json('authorization.json', {'series': ['1'], 'materials': ['video','zh-CN','en'], 'visibility': 'private'})
        self.work.write_json('stage_b_status.json', {'pending_reason': 'gh 尚未登录，停止远端写入。',
                                                   'catalog_push_verified': False})
        self.work.write_json('upload_state.json', {'repository': repository, 'assets': {
            f'{repository}/{ep["video"]["asset_name"]}': {'status': 'uploaded_verified', 'verification': 'verified'}}})
        result = publish.report(self.work)
        self.assertFalse(result['complete'])
        self.assertEqual(1, result['counts']['verified'])
        self.assertEqual(4, result['counts']['pending'])
        self.assertIsNone(result['repository_url'])
        for name in ('PROGRESS.md', 'acceptance_report.md'):
            text = self.work.local(name).read_text(encoding='utf-8')
            self.assertIn('阶段 B', text)
            self.assertIn('gh 尚未登录', text)
            self.assertNotIn('权利保持 unknown，allow_remote_write=false', text)
            self.assertNotIn('未创建远端仓库、未 push、未上传视频或字幕', text)
