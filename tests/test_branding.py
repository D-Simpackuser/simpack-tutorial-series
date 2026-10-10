"""Offline reader-branding checks; all generated output uses private fixtures."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
from unittest.mock import patch

from test_local import LocalFixture
import test_i18n as fixtures
import catalog_engine
import i18n_engine as engine


class BrandingTests(LocalFixture):
    def prepare(self):
        fixtures.InternationalizationTests.prepare(self)

    def project(self):
        # Explicit expectations rather than copying the production metadata.
        return {
            'schema_version': 1,
            'target_repository': engine.REPOSITORY,
            'target_repository_id': engine.REPOSITORY_ID,
            'brand_name': 'RailDyn Atlas',
            'titles': {locale: ('RailDyn Atlas｜轨道车辆系统动力学教程图谱'
                               if locale == 'zh-CN' else 'RailDyn Atlas')
                       for locale in engine.LOCALES},
            'subtitles': {locale: ('Simpack Railway Dynamics & Flexible-Body Simulation Library'
                                  if locale == 'en' else '轨道车辆系统动力学教程图谱'
                                  if locale == 'zh-CN' else f'{locale} synthetic technical subtitle')
                          for locale in engine.LOCALES},
        }

    def write_project(self, value):
        self.work.write_repo('i18n/project.json',
                             json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    def test_production_input_has_all_locale_branding_and_full_reader_introductions(self):
        repo = Path(__file__).resolve().parents[1]
        project = json.loads((repo / 'i18n/project.json').read_text(encoding='utf-8'))
        self.assertEqual('RailDyn Atlas', project['brand_name'])
        self.assertEqual(engine.REPOSITORY, project['target_repository'])
        self.assertEqual(engine.REPOSITORY_ID, project['target_repository_id'])
        self.assertEqual(set(engine.LOCALES), set(project['titles']))
        self.assertEqual(set(engine.LOCALES), set(project['subtitles']))
        self.assertEqual('RailDyn Atlas｜轨道车辆系统动力学教程图谱', project['titles']['zh-CN'])
        self.assertEqual('Simpack Railway Dynamics & Flexible-Body Simulation Library',
                         project['subtitles']['en'])
        for locale in engine.LOCALES:
            with self.subTest(locale=locale):
                text = (repo / 'i18n/readme' / engine.readme_name(locale)).read_text(encoding='utf-8')
                self.assertTrue(text.startswith('# ' + project['titles'][locale] + '\n'))
                self.assertGreater(len(text), 3000)
                self.assertGreaterEqual(len(re.findall(r'^## ', text, re.M)), 8)
                self.assertEqual(7, len(re.findall(r'^### ', text, re.M)))
                self.assertIn('194', text)
                self.assertIn('193', text)
                self.assertIn('772', text)
                self.assertIn('0-课程效果', text)
                self.assertIn('SRT', text)
                self.assertIn('VTT', text)
                self.assertIn('.zh-CN.srt', text)
                self.assertIn('.en.srt', text)
                self.assertIn('PROVENANCE.md', text)
                self.assertIn(engine._navigation(locale), text)
                if locale != 'zh-CN':
                    self.assertEqual('RailDyn Atlas', project['titles'][locale])
                    self.assertIn('**' + project['subtitles'][locale] + '**', text)

    def test_brand_header_is_localized_without_losing_complete_content_or_statistics(self):
        self.prepare()
        project = self.project()
        self.write_project(project)
        result = engine.render(self.work)
        self.assertEqual((8, 56, 4, 12), tuple(result[key] for key in
                         ('project_readmes', 'series_pages', 'lessons', 'subtitle_copies')))
        for locale in engine.LOCALES:
            with self.subTest(locale=locale):
                text = self.work.repo(engine.readme_name(locale)).read_text(encoding='utf-8')
                self.assertTrue(text.startswith('# ' + project['titles'][locale] + '\n'))
                self.assertIn(engine._navigation(locale), text)
                self.assertIn(engine.UI[locale]['private'], text)
                self.assertIn('Fixture description. ' * 25, text)
                self.assertIn('Editorial learning suggestions.', text)
                self.assertIn('Releases contain video files.', text)
                self.assertIn('Documentation languages do not imply subtitle languages.', text)
                self.assertIn('[Sources](PROVENANCE.md)', text)
                self.assertIn(engine.UI[locale]['stats'].format(videos=4, subtitles=12, complete=3), text)
                self.assertNotIn('**194**', text)
                self.assertEqual(7, len(re.findall(r'^### ', text, re.M)))
                self.assertEqual(1, len(re.findall(r'^# ', text, re.M)))
                if locale == 'zh-CN':
                    self.assertNotIn('**' + project['subtitles'][locale] + '**', text)
                else:
                    self.assertIn('**' + project['subtitles'][locale] + '**', text)

    def test_legacy_i18n_without_branding_retains_its_original_heading(self):
        self.prepare()
        self.assertIsNone(engine.load(self.work)['project'])
        catalog_engine.build(self.work)
        for locale in engine.LOCALES:
            text = self.work.repo(engine.readme_name(locale)).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('# Complete fixture introduction\n'))
            self.assertNotIn('RailDyn Atlas', text)

    def test_canonical_metadata_overrides_stale_source_heading_and_keeps_raw_ampersand(self):
        self.prepare()
        project = self.project()
        project['subtitles']['en'] = 'Reviewed fixture dynamics & flexible bodies'
        self.write_project(project)
        source = self.work.repo('i18n/readme/README.md').read_text(encoding='utf-8')
        self.work.write_repo('i18n/readme/README.md', source.replace(
            '# Complete fixture introduction', '# A stale source title\n\n**Obsolete subtitle**'))
        engine.render(self.work)
        text = self.work.repo('README.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('# RailDyn Atlas\n\n**Reviewed fixture dynamics & flexible bodies**\n'))
        self.assertNotIn('A stale source title', text)
        self.assertNotIn('Obsolete subtitle', text)
        self.assertNotIn('dynamics &amp; flexible', text)
        self.assertIn('Fixture description. ' * 25, text)

    def test_incomplete_foreign_or_markup_branding_fails_before_any_page_write(self):
        self.prepare()
        cases = []
        for field, value in [('target_repository', 'other/project'),
                             ('target_repository_id', engine.REPOSITORY_ID + 1),
                             ('brand_name', ' '), ('brand_name', '<script>'),
                             ('schema_version', 2)]:
            project = self.project()
            project[field] = value
            cases.append(project)
        for field, locale, value in [('titles', 'ja', 'Unrelated project'),
                                     ('subtitles', 'fr', ''),
                                     ('subtitles', 'de', 'Line one\nLine two'),
                                     ('subtitles', 'it', '[link](https://example.invalid)'),
                                     ('subtitles', 'es', '**bold**')]:
            project = self.project()
            project[field][locale] = value
            cases.append(project)
        project = self.project()
        project['titles'].pop('ko')
        cases += [project, [], None]
        for number, project in enumerate(cases):
            with self.subTest(case=number):
                self.write_project(project)
                with patch.object(self.work, 'write_repo', side_effect=AssertionError('Unexpected page write')):
                    with self.assertRaises(ValueError):
                        engine.render(self.work)

    def test_malformed_json_fails_before_any_page_write(self):
        self.prepare()
        self.work.write_repo('i18n/project.json', '{"schema_version":')
        with patch.object(self.work, 'write_repo', side_effect=AssertionError('Unexpected page write')):
            with self.assertRaises(json.JSONDecodeError):
                catalog_engine.build(self.work)

    def test_branded_legacy_build_is_idempotent_offline_and_preserves_all_media(self):
        self.prepare()
        self.write_project(self.project())
        original_series = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        original_config = copy.deepcopy(self.work.config)
        with patch.object(catalog_engine.subprocess, 'run', side_effect=AssertionError('Network/process forbidden')):
            first = catalog_engine.build(self.work)
            before = {name: self.work.repo(name).read_bytes() for name in first['output_hashes']}
            second = catalog_engine.build(self.work)
        self.assertEqual(first, second)
        self.assertEqual(before, {name: self.work.repo(name).read_bytes() for name in second['output_hashes']})
        self.assertEqual(self.catalog_bytes, self.work.repo('catalog.json').read_bytes())
        self.assertEqual(self.original_media, self.snapshot(self.subtitle_root))
        self.assertEqual(self.original_videos, self.snapshot(self.video_root))
        self.assertEqual(original_config, self.work.config)
        for path, raw in self.original_copies.items():
            self.assertEqual(raw, self.work.repo(path).read_bytes())
        series = json.loads(self.work.repo('series.json').read_text(encoding='utf-8'))
        self.assertEqual(engine.FORMAL_NAMES, {row['id']: row['display_name'] for row in series['series']})
        self.assertEqual([row['release_tag'] for row in original_series['series']],
                         [row['release_tag'] for row in series['series']])
        self.assertFalse(self.work.repo('series/4').exists())
        for ep in self.catalog['episodes']:
            text = self.work.repo(f'lessons/{ep["episode_id"]}.md').read_text(encoding='utf-8')
            self.assertIn(ep['original_relative_path'], text)
            self.assertIn('](' + ep['download_url'] + ')', text)
        self.assertTrue(engine.validate(self.work)['passed'])

    def test_brand_does_not_lift_private_access_or_change_upload_authorization(self):
        self.prepare()
        self.write_project(self.project())
        configuration = copy.deepcopy(self.work.config)
        engine.render(self.work)
        for locale in engine.LOCALES:
            text = self.work.repo(engine.readme_name(locale)).read_text(encoding='utf-8')
            self.assertIn(engine.UI[locale]['private'], text)
        self.work.write_json('stage_c/repository_observation.json', {
            'repository': engine.REPOSITORY, 'repository_id': engine.REPOSITORY_ID,
            'visibility': 'public', 'observed_at': '2026-10-10T01:00:00Z', 'remote_read_only': True})
        engine.render(self.work)
        for locale in engine.LOCALES:
            text = self.work.repo(engine.readme_name(locale)).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('# ' + self.project()['titles'][locale] + '\n'))
            self.assertNotIn(engine.UI[locale]['private'], text)
        self.assertEqual(configuration, self.work.config)
        self.assertEqual(self.catalog_bytes, self.work.repo('catalog.json').read_bytes())
        self.assertFalse(self.work.config['github']['allow_remote_write'])
