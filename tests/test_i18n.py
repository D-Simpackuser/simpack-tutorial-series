"""Offline internationalization regressions using confined synthetic sources."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

from test_local import LocalFixture
import catalog_engine
import core
import i18n_engine as engine


class InternationalizationTests(LocalFixture):
    def prepare(self):
        # Same prefixes, same title across series and missing subtitles all
        # participate; translation IDs may never come from numeric prefixes.
        for relative in ('1/12-2-轮对.mp4', '1/12-2-构架.mp4',
                         '2/12-2-轮对.mp4', '5/0-课程效果.mp4'):
            self.lesson(relative, subtitles=not relative.startswith('5/'))
        self.scan()
        catalog_engine.build(self.work)
        self.catalog_bytes = self.work.repo('catalog.json').read_bytes()
        self.catalog = json.loads(self.catalog_bytes)
        self.original_media = self.snapshot(self.subtitle_root)
        self.original_videos = self.snapshot(self.video_root)
        self.original_copies = {p.relative_to(self.work.repo('')).as_posix(): p.read_bytes()
                                for p in self.work.repo('subtitles').rglob('*') if p.is_file()}
        # The retained catalogue is offline provenance, not new API results.
        for ep in self.catalog['episodes']:
            ep['download_url'] = f'https://github.com/{engine.REPOSITORY}/releases/download/actual-returned-tag/{ep["asset_name"]}'
            ep['download_visibility'] = 'private'
        self.work.write_repo('catalog.json', json.dumps(self.catalog, ensure_ascii=False, indent=2) + '\n')
        self.catalog_bytes = self.work.repo('catalog.json').read_bytes()
        definitions = {'schema_version': 1, 'locales': list(engine.LOCALES),
                       'target_repository': engine.REPOSITORY,
                       'target_repository_id': engine.REPOSITORY_ID, 'series': []}
        for sid in engine.SERIES:
            definitions['series'].append({
                'id': sid, 'release_tag': f'series-{sid}-v1',
                'titles': {locale: engine.FORMAL_NAMES[sid] if locale == 'zh-CN' else
                           f'{engine.LANGUAGE_NAMES[locale]} title {sid}' for locale in engine.LOCALES},
                'modules': {locale: [f'{engine.LANGUAGE_NAMES[locale]} example topic'] for locale in engine.LOCALES}})
        self.work.write_repo('i18n/series.json', json.dumps(definitions, ensure_ascii=False, indent=2) + '\n')
        for locale in engine.LOCALES:
            titles = {ep['episode_id']: {
                'title': ep['title'] if locale == 'zh-CN' else f'{engine.LANGUAGE_NAMES[locale]} / {ep["episode_id"]}',
                'original_title': ep['title'], 'original_relative_path': ep['original_relative_path'],
                'source_title_hash': engine.source_title_hash(ep['title']),
                'review_status': 'synthetic_editorial_test_fixture'} for ep in self.catalog['episodes']}
            self.work.write_repo(f'i18n/lessons/{locale}.json', json.dumps({
                'schema_version': 1, 'locale': locale, 'lessons': titles,
                'review_status': 'synthetic_editorial_test_fixture'}, ensure_ascii=False, indent=2) + '\n')
            name = engine.readme_name(locale)
            intro = ['# Complete fixture introduction', '', engine._navigation(locale), '',
                     'Fixture description. ' * 25, '', '**194** videos, **193** groups, **772** files, SRT and VTT.', '',
                     '## Series', '', '| Series | Subject | Lessons | Files |', '|---|---|---:|---|']
            intro += [f'| {sid} | [Fixture](https://github.com/{engine.REPOSITORY}/blob/main/series/{sid}/README.md) | 0 | Files |' for sid in engine.SERIES]
            intro += ['', '## Starting', '', 'Editorial learning suggestions.', '', '## Topics', '']
            for sid in engine.SERIES:
                intro += [f'### Series {sid} — Old topic title', '', '- Old topic', '']
            intro += ['## Download', '', 'Releases contain video files.', '', '## Languages', '',
                      'Documentation languages do not imply subtitle languages.', '', '## Sources', '',
                      f'[Sources](https://github.com/{engine.REPOSITORY}/blob/main/PROVENANCE.md)', '']
            self.work.write_repo('i18n/readme/' + name, '\n'.join(intro))
        for relative in ('CONTRIBUTING.md', 'docs/using-the-library.md', 'docs/learning-paths.md',
                         'docs/quality-and-versions.md', 'docs/terminology.md'):
            self.work.write_repo(relative, '# Fixture reader guide\n')

    def json_update(self, relative, transform):
        obj = json.loads(self.work.repo(relative).read_text(encoding='utf-8'))
        transform(obj)
        self.work.write_repo(relative, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

    def test_complete_locale_coverage_and_exact_formal_names_without_series_four(self):
        self.prepare()
        result = engine.render(self.work)
        self.assertEqual((8, 56, 4, 12), tuple(result[key] for key in
                                               ('project_readmes', 'series_pages', 'lessons', 'subtitle_copies')))
        updated = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        self.assertEqual(engine.FORMAL_NAMES, {item['id']: item['display_name'] for item in updated['series']})
        self.assertFalse(self.work.repo('series/4').exists())
        for locale in engine.LOCALES:
            for sid in engine.SERIES:
                page = self.work.repo(f'series/{sid}/{engine.readme_name(locale)}').read_text(encoding='utf-8')
                expected = [ep for ep in self.catalog['episodes'] if ep['series_id'] == sid]
                actual = re.findall(r'^\| (s\d{2}-e\d{3}) \|', page, re.M)
                self.assertEqual([ep['episode_id'] for ep in expected], actual)
                self.assertIn('EN / 中文', page)
                for target in engine.LOCALES:
                    self.assertIn(f']({engine.readme_name(target)})', page)

    def test_legacy_build_is_idempotent_offline_and_preserves_catalogue_and_media(self):
        self.prepare()
        with patch.object(catalog_engine.subprocess, 'run', side_effect=AssertionError('Network/process forbidden')):
            first = catalog_engine.build(self.work)
            before = {name: self.work.repo(name).read_bytes() for name in first['output_hashes']}
            second = catalog_engine.build(self.work)
        self.assertEqual(first, second)
        self.assertEqual(before, {name: self.work.repo(name).read_bytes() for name in second['output_hashes']})
        self.assertEqual(self.catalog_bytes, self.work.repo('catalog.json').read_bytes())
        self.assertEqual(self.original_media, self.snapshot(self.subtitle_root))
        self.assertEqual(self.original_videos, self.snapshot(self.video_root))
        for path, raw in self.original_copies.items():
            self.assertEqual(raw, self.work.repo(path).read_bytes())

    def test_statistics_are_computed_from_catalogue_and_missing_subtitles_remain_missing(self):
        self.prepare()
        engine.render(self.work)
        readme = self.work.repo('README.md').read_text(encoding='utf-8')
        self.assertIn('4 video lessons', readme)
        self.assertIn('12 subtitle files', readme)
        self.assertIn('3 lessons with all four', readme)
        self.assertNotIn('**194**', readme)
        self.assertEqual([], list(self.work.repo('subtitles/5').glob('*.srt')))
        detail = self.work.repo('lessons/s05-e001.md').read_text(encoding='utf-8')
        self.assertEqual(4, detail.count('Missing / 缺失'))
        self.assertIn('5/0-课程效果.mp4', detail)
        self.assertNotIn('Recorded duration', detail)
        self.assertNotIn('已记录时长', detail)

    def test_strict_translation_path_or_source_hash_change_blocks_before_rendering(self):
        self.prepare()
        original = self.work.repo('README.md').read_bytes()
        self.json_update('i18n/lessons/en.json', lambda obj:
                         obj['lessons']['s01-e001'].update(original_relative_path='1/12-2-另一个标题.mp4'))
        with self.assertRaisesRegex(ValueError, 'binding differs'):
            engine.render(self.work)
        self.assertEqual(original, self.work.repo('README.md').read_bytes())
        self.json_update('i18n/lessons/en.json', lambda obj:
                         obj['lessons']['s01-e001'].update(original_relative_path=self.catalog['episodes'][0]['original_relative_path'],
                                                         source_title_hash='0' * 64))
        with self.assertRaisesRegex(ValueError, 'binding differs'):
            engine.render(self.work)

    def test_missing_locale_or_foreign_id_cannot_fall_back_to_legacy_pages(self):
        self.prepare()
        self.json_update('i18n/lessons/ja.json', lambda obj: obj['lessons'].pop('s01-e001'))
        with self.assertRaisesRegex(ValueError, 'IDs differ'):
            catalog_engine.build(self.work)
        self.assertFalse(self.work.repo('README.ja.md').exists())

    def test_partial_input_tree_stops_instead_of_resetting_titles(self):
        self.lesson('1/1-课程.mp4')
        self.scan()
        catalog_engine.build(self.work)
        original = self.work.repo('README.md').read_bytes()
        self.work.repo('i18n').mkdir()
        with self.assertRaisesRegex(ValueError, 'Missing internationalization input'):
            catalog_engine.build(self.work)
        self.assertEqual(original, self.work.repo('README.md').read_bytes())

    def test_retained_subtitle_bytes_and_hashes_are_guarded_before_writes(self):
        self.prepare()
        path = self.catalog['episodes'][0]['subtitles']['.en.srt']['path']
        self.work.repo(path).write_bytes(b'changed subtitle')
        with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
            engine.render(self.work)

    def test_public_banner_refresh_requires_real_read_only_repository_observation(self):
        self.prepare()
        engine.render(self.work)
        self.assertIn('Private repository:', self.work.repo('README.md').read_text(encoding='utf-8'))
        self.work.write_json('stage_c/repository_observation.json', {
            'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'visibility': 'public', 'observed_at': '2026-10-10T01:00:00Z', 'remote_read_only': True})
        engine.render(self.work)
        self.assertNotIn('Private repository:', self.work.repo('README.md').read_text(encoding='utf-8'))
        self.assertEqual(self.catalog_bytes, self.work.repo('catalog.json').read_bytes())
        self.assertFalse(self.work.config['github']['allow_remote_write'])
        self.work.write_json('stage_c/repository_observation.json', {
            'repository': 'another/repository', 'repository_id': engine.REPOSITORY_ID,
            'visibility': 'public', 'observed_at': '2026-10-10T01:00:00Z', 'remote_read_only': True})
        with self.assertRaisesRegex(ValueError, 'repository observation'):
            engine.render(self.work)

    def test_wrong_case_link_and_missing_anchor_are_detected_on_windows(self):
        self.prepare()
        engine.render(self.work)
        result = engine.validate(self.work)
        self.assertTrue(result['passed'], result)
        self.work.write_repo('docs/case-fixture.md', '# Case check\n\n[Wrong case](../README.JA.md)\n\n[Missing](../README.md#nonexistent-anchor)\n')
        result = engine.markdown_links(self.work)
        self.assertFalse(result['passed'])
        self.assertEqual({'broken_or_wrong_case_link', 'missing_anchor'}, {item['kind'] for item in result['issues']})

    def test_reparse_document_is_skipped_and_reported_without_reading_it(self):
        self.prepare()
        engine.render(self.work)
        suspect = self.work.repo('docs/reparse-fixture.md')
        suspect.write_bytes(b'[Outside](outside-fixture.md)\n')
        original = core.is_link
        def reparse(path):
            return Path(path) == suspect or original(path)
        with patch.object(core, 'is_link', side_effect=reparse):
            result = engine.markdown_links(self.work)
        self.assertFalse(result['passed'])
        self.assertEqual([{'kind': 'repository_skipped_reparse_point',
                           'relative_path': 'docs/reparse-fixture.md'}], result['issues'])

    def test_bilingual_detail_navigation_preserves_exact_recorded_urls(self):
        self.prepare()
        engine.render(self.work)
        for ep in self.catalog['episodes']:
            page = self.work.repo(f'lessons/{ep["episode_id"]}.md').read_text(encoding='utf-8')
            self.assertIn(f']({ep["download_url"]})', page)
            self.assertIn('id="english"', page)
            self.assertIn('id="zh-cn"', page)
            self.assertIn(f'../series/{ep["series_id"]}/README.zh-CN.md', page)
        result = engine.validate(self.work)
        self.assertTrue(result['passed'], result)

    def test_provenance_marker_and_existing_release_tags_are_not_modified(self):
        self.prepare()
        original = self.work.repo('PROVENANCE.md').read_bytes()
        series = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        engine.render(self.work)
        updated = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        self.assertEqual(original, self.work.repo('PROVENANCE.md').read_bytes())
        self.assertIn(b'simpack-local-publish-v1', original)
        for before, after in zip(series['series'], updated['series']):
            self.assertEqual({k: v for k, v in before.items() if k != 'display_name'},
                             {k: v for k, v in after.items() if k != 'display_name'})

    def test_stage_c_manifest_does_not_grant_media_or_unmanaged_file_writes(self):
        self.prepare()
        engine.render(self.work)
        self.work.write_json('stage_c/stage_manifest.json', {
            'phase': 'C', 'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'authorization_scope': 'documentation_only', 'files': ['README.md']})
        result = catalog_engine.audit(self.work)
        self.assertTrue(result['passed'], result['issues'])
        self.assertEqual(['README.md'], result['stage_c_documentation_files'])
        sub = self.catalog['episodes'][0]['subtitles']['.en.srt']['path']
        self.work.write_json('stage_c/stage_manifest.json', {
            'phase': 'C', 'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'authorization_scope': 'documentation_only', 'files': [sub]})
        self.assertFalse(catalog_engine.audit(self.work)['passed'])
        self.assertFalse(self.work.config['github']['allow_remote_write'])

    def test_stage_c_staged_blob_still_requires_exact_manifest_and_regular_mode(self):
        self.prepare()
        engine.render(self.work)
        self.work.repo('.git').mkdir()
        def git(args, **kwargs):
            self.assertIs(kwargs.get('shell'), False)
            if 'diff' in args:
                return SimpleNamespace(returncode=0, stdout=b'README.md\0')
            if 'ls-files' in args:
                return SimpleNamespace(returncode=0, stdout=b'120000 ' + b'0' * 40 + b' 0\tREADME.md\0')
            raise AssertionError(args)
        self.work.write_json('stage_c/stage_manifest.json', {
            'phase': 'C', 'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'authorization_scope': 'documentation_only', 'files': ['README.md']})
        with patch.object(catalog_engine.shutil, 'which', return_value='git'), \
                patch.object(catalog_engine.subprocess, 'run', side_effect=git):
            result = catalog_engine.audit(self.work)
        self.assertFalse(result['passed'])
        self.assertIn('unsafe_staged_file_mode', json.dumps(result['issues']))


class OwnedCodeAuditTests(LocalFixture):
    """A fresh clone has no private record granting ownership to repo files."""

    verifier_sources = ('scripts/library_verify.py', 'tests/test_library_verify.py')

    def clone_file(self, relative, data=b'# Synthetic clone verifier source\n'):
        path = self.work.repo(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data

    def private_fixture(self, relative, value):
        # Do not create a managed-file record, just as on a fresh checkout.
        path = self.work.local(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')
        return path.read_bytes()

    def stage_c_manifest(self, paths):
        self.private_fixture('stage_c/stage_manifest.json', {
            'phase': 'C', 'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'authorization_scope': 'documentation_only', 'files': paths})

    def audit_index(self, blobs):
        self.assertFalse(self.work.local('managed_files.json').exists())
        self.assertEqual(set(), self.work.managed)
        self.work.repo('.git').mkdir()
        self.audit_git_commands = []

        def git(args, **kwargs):
            self.audit_git_commands.append(args)
            self.assertIs(kwargs.get('shell'), False)
            if 'diff' in args:
                output = b''.join(path.encode('utf-8') + b'\0' for path in blobs)
            elif 'ls-files' in args:
                output = b''.join(b'100644 ' + b'0' * 40 + b' 0\t' + path.encode('utf-8') + b'\0'
                                  for path in blobs)
            elif 'show' in args:
                output = blobs[args[-1][1:]]
            else:
                raise AssertionError(args)
            return SimpleNamespace(returncode=0, stdout=output, stderr=b'')

        with patch.object(catalog_engine.shutil, 'which', return_value='fixture-git'), \
                patch.object(catalog_engine.subprocess, 'run', side_effect=git):
            result = catalog_engine.audit(self.work)
        self.assertEqual(0, result['remote_calls'])
        self.assertFalse(any(path.startswith('repo/') for path in self.work.managed))
        return result

    def test_fresh_clone_verifier_and_branding_sources_pass_exact_stage_c_manifest_without_private_ownership(self):
        blobs = {path: self.clone_file(path) for path in (*self.verifier_sources, 'tests/test_branding.py')}
        self.config['phase'] = 'B'
        configuration = copy.deepcopy(self.config)
        authorization = self.private_fixture('authorization.json', {
            'authorization_id': 'retained-private-upload-scope', 'visibility': 'private',
            'approved_existing_asset_names': ['s01-e001.mp4']})
        self.stage_c_manifest(list(blobs))
        result = self.audit_index(blobs)
        self.assertTrue(result['passed'], result['issues'])
        self.assertEqual(sorted(blobs), result['candidate_files'])
        self.assertEqual(sorted(blobs), result['stage_c_documentation_files'])
        self.assertEqual([], result['excluded_unmanaged_files'])
        self.assertTrue(result['git_index_checked'])
        self.assertEqual(configuration, self.config)
        self.assertEqual(authorization, self.work.local('authorization.json').read_bytes())

    def test_unknown_source_and_owned_source_outside_exact_stage_c_manifest_remain_blocked(self):
        blobs = {path: self.clone_file(path) for path in self.verifier_sources}
        unknown = 'scripts/unapproved.py'
        blobs[unknown] = self.clone_file(unknown)
        self.stage_c_manifest([self.verifier_sources[0], unknown])
        result = self.audit_index(blobs)
        self.assertFalse(result['passed'])
        self.assertEqual([unknown], result['excluded_unmanaged_files'])
        self.assertEqual([self.verifier_sources[0]], result['stage_c_documentation_files'])
        self.assertEqual({unknown}, {item['path'] for item in result['issues']
                                    if item['kind'] == 'unauthorized_stage_c_manifest_file'})
        self.assertEqual({unknown, self.verifier_sources[1]},
                         {item['path'] for item in result['issues']
                          if item['kind'] == 'unauthorized_staged_file'})

    def test_owned_verifier_sources_do_not_expand_stage_b_subtitle_authorization(self):
        blobs = {path: self.clone_file(path) for path in self.verifier_sources}
        approved = 's01-e001.en.srt'
        excluded = 's01-e001.en.vtt'
        subtitle_data = b'Synthetic unchanged subtitle fixture\n'
        subtitle_paths = [f'subtitles/1/{name}' for name in (approved, excluded)]
        for path in subtitle_paths:
            self.clone_file(path, subtitle_data)
        blobs[subtitle_paths[1]] = subtitle_data
        self.config['phase'] = 'B'
        configuration = copy.deepcopy(self.config)
        self.private_fixture('inventory.json', {'episodes': [{
            'episode_id': 's01-e001', 'series_id': '1', 'subtitles': {
                '.en.srt': {'status': 'matched', 'asset_name': approved,
                            'sha256': hashlib.sha256(subtitle_data).hexdigest()},
                '.en.vtt': {'status': 'matched', 'asset_name': excluded,
                            'sha256': hashlib.sha256(subtitle_data).hexdigest()}}}]})
        rights = self.private_fixture('rights.json', {
            'default': 'unknown', 'episodes': {'s01-e001': {'en': 'confirmed'}}})
        authorization = self.private_fixture('authorization.json', {
            'authorization_id': 'retained-private-upload-scope', 'visibility': 'private',
            'approved_existing_asset_names': [approved]})
        self.private_fixture('stage_b_stage_manifest.json', {'files': list(blobs)})
        result = self.audit_index(blobs)
        self.assertFalse(result['passed'])
        self.assertEqual(sorted(self.verifier_sources), result['stage_b_authorized_files'])
        self.assertEqual([subtitle_paths[0]], result['confirmed_subtitle_material_files'])
        self.assertEqual([subtitle_paths[1]], result['unconfirmed_material_files'])
        self.assertIn({'kind': 'unauthorized_stage_manifest_file', 'path': subtitle_paths[1]}, result['issues'])
        self.assertIn({'kind': 'unauthorized_staged_file', 'path': subtitle_paths[1]}, result['issues'])
        self.assertEqual(configuration, self.config)
        self.assertEqual(authorization, self.work.local('authorization.json').read_bytes())
        self.assertEqual(rights, self.work.local('rights.json').read_bytes())
