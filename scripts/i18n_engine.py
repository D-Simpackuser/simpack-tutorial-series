"""Deterministic multilingual documentation for the existing media catalogue.

Rendering and validation are offline. They never authenticate, upload media,
edit Releases, move tags, change visibility, or amend upload authorization.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

from core import SERIES, SUFFIXES, sha256, walk_source

LOCALES = ('en', 'zh-CN', 'ja', 'fr', 'de', 'it', 'es', 'ko')
LANGUAGE_NAMES = {'en': 'English', 'zh-CN': '简体中文', 'ja': '日本語',
                  'fr': 'Français', 'de': 'Deutsch', 'it': 'Italiano',
                  'es': 'Español', 'ko': '한국어'}
REPOSITORY = 'D-Simpackuser/simpack-tutorial-series'
REPOSITORY_ID = 1412669436
FORMAL_NAMES = {
    '1': '基于ABAQUS-Simpack联合的轨道车辆-柔性轨-浮置板耦合动力学',
    '2': '基于ANSYS/ABAQUS-Simpack-Fesafe的弹性体动态应力应变/疲劳仿真解决方案',
    '3': '基于ANSYS Workbench Mechanical & APDL的轨道车辆-弹性轨道动力学全平台实现',
    '5': 'ABAQUS-Simpack联合仿真实现车线桥耦合动力学系统',
    '6': 'Simpack轨道车辆动力学快速入门案例',
    '7': 'ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Solid）',
    '8': 'ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Beam）',
}

# Short interface phrases only. Complete introductions are maintained as the
# supplied, editable i18n/readme source documents, not reconstructed here.
UI = {
    'en': {
        'series': 'Series', 'id': 'Lesson ID', 'title': 'Title', 'video': 'Video',
        'subtitles': 'Subtitles', 'details': 'Details (EN / 中文)', 'download': 'MP4',
        'missing': 'Missing', 'unavailable': 'Unavailable', 'home': 'Home', 'topics': 'Topic guide',
        'stats': '{videos} video lessons · {subtitles} subtitle files · {complete} lessons with all four subtitle files.',
        'private': 'Private repository: a GitHub account with repository access is required for video and subtitle downloads.',
        'unverified_visibility': 'Access settings have not been freshly observed. Repository access may be required.',
        'notice': 'Titles and topic groups are editorial descriptions, not independently validated simulation results. Lesson details are bilingual English / Chinese; original Chinese filenames remain there for exact identification.',
        'subtitle_note': 'Subtitle languages: Chinese and English, in SRT / VTT. File availability does not establish semantic or timeline review. Eight documentation languages do not add subtitle tracks.',
        'missing_note': 'No accompanying subtitle files: ',
        'using': 'Download guide', 'learning': 'Learning paths', 'quality': 'Quality and versions',
        'terms': 'Terminology', 'contributing': 'Contributing', 'source': 'Sources and rights',
    },
    'zh-CN': {
        'series': '系列', 'id': '课程 ID', 'title': '课程标题', 'video': '视频',
        'subtitles': '字幕', 'details': '详情（EN / 中文）', 'download': 'MP4',
        'missing': '缺失', 'unavailable': '暂无', 'home': '首页', 'topics': '主题导览',
        'stats': '{videos} 个视频课程 · {subtitles} 个字幕文件 · {complete} 课具备四种配套字幕文件。',
        'private': '仓库当前为 private：下载视频及字幕需要具有仓库访问权限的 GitHub 账号。',
        'unverified_visibility': '尚未重新读取仓库可见性，访问可能需要仓库权限。',
        'notice': '显示题名和主题分组是编辑整理，不代表仿真结果经过独立验证。课程详情为中英双语，保留原始中文文件名用于精确识别。',
        'subtitle_note': '字幕语言为中文和英文，提供 SRT / VTT。文件可用不代表语义及时间轴已审校；八语文档不会增加字幕语言。',
        'missing_note': '没有配套字幕的课程：',
        'using': '下载说明', 'learning': '学习建议', 'quality': '质量与版本',
        'terms': '术语约定', 'contributing': '参与纠错', 'source': '来源与权利',
    },
    'ja': {
        'series': 'シリーズ', 'id': '講義 ID', 'title': '題名', 'video': '動画',
        'subtitles': '字幕', 'details': '詳細（EN / 中文）', 'download': 'MP4',
        'missing': 'なし', 'unavailable': '未提供', 'home': 'ホーム', 'topics': 'テーマ別ガイド',
        'stats': '動画 {videos} 本 · 字幕ファイル {subtitles} 個 · 4種類の字幕が揃う動画 {complete} 本。',
        'private': '現在は非公開リポジトリです。動画・字幕のダウンロードにはアクセス権のある GitHub アカウントが必要です。',
        'unverified_visibility': '公開設定は新たに確認されていません。アクセス権が必要な場合があります。',
        'notice': '題名とテーマは編集上の整理であり、解析結果の独立した検証を示しません。詳細ページは英語・中国語で、照合用の中国語原ファイル名を保持しています。',
        'subtitle_note': '字幕は中国語・英語の SRT / VTT です。ファイルの存在は意味や同期の審査を示しません。8言語の文書化は字幕の追加ではありません。',
        'missing_note': '字幕ファイルのない講義：',
        'using': 'ダウンロード案内', 'learning': '学習案', 'quality': '品質とバージョン',
        'terms': '用語', 'contributing': '訂正への協力', 'source': '出典と権利',
    },
    'fr': {
        'series': 'Série', 'id': 'ID du cours', 'title': 'Titre', 'video': 'Vidéo',
        'subtitles': 'Sous-titres', 'details': 'Détails (EN / 中文)', 'download': 'MP4',
        'missing': 'Absent', 'unavailable': 'Indisponible', 'home': 'Accueil', 'topics': 'Repères thématiques',
        'stats': '{videos} vidéos · {subtitles} fichiers de sous-titres · {complete} vidéos avec les quatre fichiers.',
        'private': 'Dépôt actuellement privé : un compte GitHub disposant des droits d’accès est nécessaire pour télécharger les vidéos et les sous-titres.',
        'unverified_visibility': 'La visibilité n’a pas été relue récemment. Des droits d’accès peuvent être nécessaires.',
        'notice': 'Les titres et thèmes sont un classement éditorial, pas une validation indépendante des résultats. Les détails sont en anglais / chinois et conservent les noms chinois d’origine.',
        'subtitle_note': 'Sous-titres chinois et anglais en SRT / VTT. Leur présence ne prouve pas une révision du sens ou de la synchronisation. Les huit langues documentaires n’ajoutent pas de sous-titres.',
        'missing_note': 'Cours sans fichiers de sous-titres : ',
        'using': 'Téléchargement', 'learning': 'Parcours suggérés', 'quality': 'Qualité et versions',
        'terms': 'Terminologie', 'contributing': 'Contributions', 'source': 'Sources et droits',
    },
    'de': {
        'series': 'Reihe', 'id': 'Lektions-ID', 'title': 'Titel', 'video': 'Video',
        'subtitles': 'Untertitel', 'details': 'Details (EN / 中文)', 'download': 'MP4',
        'missing': 'Fehlt', 'unavailable': 'Nicht verfügbar', 'home': 'Startseite', 'topics': 'Themenüberblick',
        'stats': '{videos} Videos · {subtitles} Untertiteldateien · {complete} Videos mit allen vier Untertiteldateien.',
        'private': 'Das Repository ist derzeit privat. Für Video- und Untertiteldownloads ist ein GitHub-Konto mit Zugriffsberechtigung erforderlich.',
        'unverified_visibility': 'Die Sichtbarkeit wurde nicht erneut abgefragt. Eine Zugriffsberechtigung kann erforderlich sein.',
        'notice': 'Titel und Themengruppen sind redaktionell geordnet und belegen keine unabhängige Validierung. Die Detailseiten sind Englisch / Chinesisch; chinesische Originaldateinamen bleiben erhalten.',
        'subtitle_note': 'Untertitel: Chinesisch und Englisch, SRT / VTT. Vorhandene Dateien belegen keine Prüfung von Inhalt oder Synchronität. Acht Dokumentationssprachen sind keine acht Untertitelsprachen.',
        'missing_note': 'Lektionen ohne Untertiteldateien: ',
        'using': 'Downloadhinweise', 'learning': 'Lernempfehlungen', 'quality': 'Qualität und Versionen',
        'terms': 'Terminologie', 'contributing': 'Mitarbeit', 'source': 'Quellen und Rechte',
    },
    'it': {
        'series': 'Serie', 'id': 'ID lezione', 'title': 'Titolo', 'video': 'Video',
        'subtitles': 'Sottotitoli', 'details': 'Dettagli (EN / 中文)', 'download': 'MP4',
        'missing': 'Assente', 'unavailable': 'Non disponibile', 'home': 'Home', 'topics': 'Guida agli argomenti',
        'stats': '{videos} video · {subtitles} file di sottotitoli · {complete} video con tutti e quattro i file.',
        'private': 'Il repository è attualmente privato. Per scaricare video e sottotitoli serve un account GitHub autorizzato ad accedervi.',
        'unverified_visibility': 'La visibilità non è stata riletta. Potrebbero essere necessari i diritti di accesso.',
        'notice': 'Titoli e temi sono un’organizzazione editoriale, non una validazione indipendente. I dettagli sono in inglese / cinese e conservano i nomi cinesi dei file originali.',
        'subtitle_note': 'Sottotitoli in cinese e inglese, SRT / VTT. La presenza dei file non dimostra una revisione del significato o della sincronizzazione. Otto lingue dei documenti non aggiungono sottotitoli.',
        'missing_note': 'Lezioni senza file di sottotitoli: ',
        'using': 'Download', 'learning': 'Percorsi suggeriti', 'quality': 'Qualità e versioni',
        'terms': 'Terminologia', 'contributing': 'Contributi', 'source': 'Fonti e diritti',
    },
    'es': {
        'series': 'Serie', 'id': 'ID de lección', 'title': 'Título', 'video': 'Vídeo',
        'subtitles': 'Subtítulos', 'details': 'Detalles (EN / 中文)', 'download': 'MP4',
        'missing': 'Ausente', 'unavailable': 'No disponible', 'home': 'Inicio', 'topics': 'Guía temática',
        'stats': '{videos} vídeos · {subtitles} archivos de subtítulos · {complete} vídeos con los cuatro archivos.',
        'private': 'El repositorio es privado actualmente. Para descargar vídeos y subtítulos se necesita una cuenta de GitHub con acceso.',
        'unverified_visibility': 'La visibilidad no se ha consultado de nuevo. Puede ser necesario tener acceso al repositorio.',
        'notice': 'Los títulos y temas son una organización editorial, no una validación independiente. Los detalles están en inglés / chino y conservan los nombres chinos originales.',
        'subtitle_note': 'Subtítulos chinos e ingleses en SRT / VTT. Su disponibilidad no acredita revisión semántica ni sincronización. Las ocho lenguas documentales no añaden pistas de subtítulos.',
        'missing_note': 'Lecciones sin archivos de subtítulos: ',
        'using': 'Descargas', 'learning': 'Itinerarios sugeridos', 'quality': 'Calidad y versiones',
        'terms': 'Terminología', 'contributing': 'Contribuciones', 'source': 'Fuentes y derechos',
    },
    'ko': {
        'series': '시리즈', 'id': '강의 ID', 'title': '제목', 'video': '영상',
        'subtitles': '자막', 'details': '상세 (EN / 中文)', 'download': 'MP4',
        'missing': '없음', 'unavailable': '미제공', 'home': '홈', 'topics': '주제 안내',
        'stats': '영상 {videos}개 · 자막 파일 {subtitles}개 · 네 종류의 자막이 있는 강의 {complete}개.',
        'private': '현재 비공개 저장소입니다. 영상과 자막을 다운로드하려면 저장소 접근 권한이 있는 GitHub 계정이 필요합니다.',
        'unverified_visibility': '공개 설정을 새로 확인하지 않았습니다. 접근 권한이 필요할 수 있습니다.',
        'notice': '제목과 주제 분류는 편집상 정리이며 독립 검증을 뜻하지 않습니다. 상세 페이지는 영어 / 중국어이며 원래 중국어 파일명을 유지합니다.',
        'subtitle_note': '자막은 중국어와 영어의 SRT / VTT입니다. 파일 존재가 의미나 동기화 검토를 입증하지 않습니다. 8개 문서 언어는 자막 추가를 뜻하지 않습니다.',
        'missing_note': '자막 파일이 없는 강의: ',
        'using': '다운로드 안내', 'learning': '학습 제안', 'quality': '품질과 버전',
        'terms': '용어', 'contributing': '기여', 'source': '출처와 권리',
    },
}


def readme_name(locale):
    return 'README.md' if locale == 'en' else f'README.{locale}.md'


def source_title_hash(title):
    return hashlib.sha256(title.encode('utf-8')).hexdigest()


def enabled(work):
    # Partial internationalization inputs must fail closed, not restore the
    # legacy generator over already-localized reader pages.
    return work.repo('i18n').exists()


def _md(value):
    value = html.escape(str(value), quote=True).replace('|', '&#124;').replace('\n', ' ')
    return re.sub(r'([\\`*_[\]])', r'\\\1', value)


def _read(work, relative):
    path = work.repo(relative)
    if not path.is_file():
        raise ValueError(f'Missing internationalization input: {relative}')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def _url(value):
    if value is None:
        return None
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or
            not parsed.path.startswith('/' + REPOSITORY + '/releases/') or
            parsed.query or parsed.fragment or any(ch.isspace() for ch in value)):
        raise ValueError('Catalogue contains an unexpected download or Release URL')
    return value


def _visibility(work, catalog, series):
    observation = work.read_json('stage_c/repository_observation.json', {})
    if observation:
        try:
            stamp = datetime.fromisoformat(observation['observed_at'].replace('Z', '+00:00'))
        except (KeyError, TypeError, ValueError):
            raise ValueError('Invalid read-only repository observation') from None
        if (observation.get('repository') != REPOSITORY or
                observation.get('repository_id') != REPOSITORY_ID or
                observation.get('remote_read_only') is not True or stamp.tzinfo is None or
                observation.get('visibility') not in ('private', 'public')):
            raise ValueError('Invalid read-only repository observation')
        return observation['visibility']
    observed = {item.get('release_visibility') for item in series['series']}
    observed.update(ep.get('download_visibility') for ep in catalog['episodes'])
    # Only a real, separate read-only observation can lift the private banner.
    return 'private' if 'private' in observed else 'unverified'


def _stats(episodes):
    return {'videos': len(episodes),
            'subtitles': sum(bool(sub.get('path')) for ep in episodes for sub in ep['subtitles'].values()),
            'complete': sum(all(ep['subtitles'][suffix].get('path') for suffix in SUFFIXES) for ep in episodes)}


def load(work, check_copies=True):
    """Strictly join translations to IDs and exact source strings before writes."""
    catalog, series = _read(work, 'catalog.json'), _read(work, 'series.json')
    if catalog.get('schema_version') != 1 or not isinstance(catalog.get('episodes'), list):
        raise ValueError('Internationalization requires the existing schema 1 episodes catalogue')
    rows = series.get('series')
    if not isinstance(rows, list) or tuple(x.get('id') for x in rows) != SERIES:
        raise ValueError('Existing series IDs or ordering differ from the retained seven series')
    definitions = _read(work, 'i18n/series.json')
    if (definitions.get('schema_version') != 1 or tuple(definitions.get('locales', [])) != LOCALES or
            definitions.get('target_repository') != REPOSITORY or
            definitions.get('target_repository_id') != REPOSITORY_ID):
        raise ValueError('Internationalization project identity or locale set differs')
    named = definitions.get('series', [])
    if tuple(item.get('id') for item in named) != SERIES:
        raise ValueError('Internationalization series IDs differ')
    by_series = {item['id']: item for item in named}
    for current in rows:
        item, sid = by_series[current['id']], current['id']
        if item.get('release_tag') != current.get('release_tag') or current.get('release_tag') != f'series-{sid}-v1':
            raise ValueError('Internationalization must not alter retained Release tags')
        if set(item.get('titles', {})) != set(LOCALES) or set(item.get('modules', {})) != set(LOCALES):
            raise ValueError('Every series requires titles and topic groups in all eight languages')
        if item['titles']['zh-CN'] != FORMAL_NAMES[sid]:
            raise ValueError(f'Formal Chinese series name differs: {sid}')
        for locale in LOCALES:
            if not isinstance(item['titles'][locale], str) or not item['titles'][locale].strip():
                raise ValueError('Series display title is empty')
            if not isinstance(item['modules'][locale], list) or any(not isinstance(x, str) or not x.strip() for x in item['modules'][locale]):
                raise ValueError('Series topic groups are invalid')
        _url(current.get('release_url'))
    episodes, paths, ids, copies = catalog['episodes'], set(), set(), 0
    for ep in episodes:
        episode_id, relative, sid = ep['episode_id'], ep['original_relative_path'], ep['series_id']
        path = PurePosixPath(relative)
        if (episode_id in ids or relative in paths or sid not in SERIES or
                not re.fullmatch(r's\d{2}-e\d{3,}', episode_id) or
                not episode_id.startswith(f's{int(sid):02d}-') or path.is_absolute() or
                '..' in path.parts or not path.parts or path.parts[0] != sid or
                path.name != ep['original_filename']):
            raise ValueError('Catalogue IDs or exact original relative paths are invalid or duplicated')
        ids.add(episode_id)
        paths.add(relative)
        _url(ep.get('download_url'))
        if set(ep.get('subtitles', {})) != set(SUFFIXES):
            raise ValueError('Existing subtitle suffix set differs')
        for suffix, sub in ep['subtitles'].items():
            _url(sub.get('download_url'))
            if not sub.get('path'):
                if sub.get('status') != 'missing':
                    raise ValueError('Subtitle without a retained copy is not marked missing')
                continue
            copy = work.repo(sub['path'])
            if copy.name != sub.get('asset_name') or copy.suffix not in ('.srt', '.vtt') or not copy.is_file():
                raise ValueError('Retained subtitle path or filename differs')
            if check_copies and sha256(copy) != sub.get('sha256'):
                raise ValueError('Retained subtitle copy SHA-256 differs')
            copies += 1
    localized, introductions = {}, {}
    for locale in LOCALES:
        content = _read(work, f'i18n/lessons/{locale}.json')
        entries = content.get('lessons')
        if content.get('schema_version') != 1 or content.get('locale') != locale or not isinstance(entries, dict) or set(entries) != ids:
            raise ValueError(f'Localized lesson IDs differ: {locale}')
        for ep in episodes:
            entry = entries[ep['episode_id']]
            if (entry.get('original_relative_path') != ep['original_relative_path'] or
                    entry.get('original_title') != ep['title'] or
                    entry.get('source_title_hash') != source_title_hash(ep['title'])):
                raise ValueError(f'Exact title/path translation binding differs: {locale}/{ep["episode_id"]}')
            if not isinstance(entry.get('title'), str) or not entry['title'].strip() or not entry.get('review_status'):
                raise ValueError(f'Localized lesson title or review status missing: {locale}')
            if locale == 'zh-CN' and entry['title'] != ep['title']:
                raise ValueError('Chinese lesson display title must preserve the original title')
        localized[locale] = entries
        intro = work.repo('i18n/readme/' + readme_name(locale))
        if not intro.is_file():
            raise ValueError(f'Missing complete README source: {locale}')
        text = intro.read_text(encoding='utf-8-sig').replace('\r\n', '\n').strip()
        if len(text) < 500 or len(re.findall(r'^## ', text, flags=re.M)) < 5:
            raise ValueError(f'Introduction source is incomplete: {locale}')
        introductions[locale] = text
    for item in rows:
        stats = _stats([ep for ep in episodes if ep['series_id'] == item['id']])
        if item.get('videos') != stats['videos'] or item.get('subtitles') != stats['subtitles']:
            raise ValueError('Existing series statistics differ from the retained catalogue')
    return {'catalog': catalog, 'series': series, 'definitions': definitions,
            'named': by_series, 'lessons': localized, 'introductions': introductions,
            'visibility': _visibility(work, catalog, series), 'subtitle_copies_checked': copies,
            'stats': _stats(episodes)}


def _navigation(locale, prefix=''):
    return ' · '.join(f'[{LANGUAGE_NAMES[x]}]({prefix}{readme_name(x)})' for x in LOCALES)


def _banner(locale, visibility):
    if visibility == 'public':
        return ''
    return '> ' + UI[locale]['private' if visibility == 'private' else 'unverified_visibility']


def _footer(locale, prefix=''):
    ui = UI[locale]
    pages = [('using', 'docs/using-the-library.md'), ('learning', 'docs/learning-paths.md'),
             ('quality', 'docs/quality-and-versions.md'), ('terms', 'docs/terminology.md'),
             ('contributing', 'CONTRIBUTING.md'), ('source', 'PROVENANCE.md')]
    return ' · '.join(f'[{ui[label]}]({prefix}{page})' for label, page in pages)


def _missing(episodes):
    return [ep for ep in episodes if not any(sub.get('path') for sub in ep['subtitles'].values())]


def _stat_paragraph(locale, episodes):
    result = UI[locale]['stats'].format(**_stats(episodes))
    missing = _missing(episodes)
    if missing:
        result += ' ' + UI[locale]['missing_note'] + '; '.join(
            f'`{ep["episode_id"]}` — {_md(ep["title"])}' for ep in missing) + '.'
    return result


def _root_readme(locale, data):
    text = data['introductions'][locale]
    paragraphs = text.split('\n\n')
    counts = [i for i, paragraph in enumerate(paragraphs) if
              re.search(r'\*\*\d+', paragraph) and 'SRT' in paragraph and 'VTT' in paragraph]
    if len(counts) != 1:
        raise ValueError(f'Cannot identify introduction statistics paragraph: {locale}')
    paragraphs[counts[0]] = _stat_paragraph(locale, data['catalog']['episodes'])
    text = '\n\n'.join(paragraphs)
    lines = text.splitlines()
    row_indices = [i for i, line in enumerate(lines) if re.match(r'^\|\s*(?:1|2|3|5|6|7|8)\s*\|', line)]
    if len(row_indices) != len(SERIES) or row_indices != list(range(row_indices[0], row_indices[0] + len(SERIES))):
        raise ValueError(f'Cannot identify the seven-series introduction table: {locale}')
    replacements = []
    for current, old_index in zip(data['series']['series'], row_indices):
        sid = current['id']
        existing_links = re.findall(r'\[([^\]]+)\]\([^)]*\)', lines[old_index])
        release_label = existing_links[-1] if len(existing_links) > 1 else 'Release'
        release = f'[{_md(release_label)}]({current["release_url"]})' if current.get('release_url') else UI[locale]['unavailable']
        title = data['named'][sid]['titles'][locale]
        replacements.append(f'| {sid} | [{_md(title)}](series/{sid}/{readme_name(locale)}) | {current["videos"]} | {release} |')
    lines[row_indices[0]:row_indices[-1] + 1] = replacements
    # Regenerate only the supplied topic section from the shared series input.
    topics = [i for i, line in enumerate(lines) if re.match(r'^### .*?\b[1235678]\s+[—–-]\s+', line)]
    if len(topics) != len(SERIES):
        raise ValueError(f'Cannot identify introduction topic groups: {locale}')
    end = next((i for i in range(topics[-1] + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
    topic_lines = []
    for sid in SERIES:
        item = data['named'][sid]
        topic_lines += [f'### {UI[locale]["series"]} {sid} — {_md(item["titles"][locale])}', '']
        topic_lines += ['- ' + _md(module) for module in item['modules'][locale]] + ['']
    lines[topics[0]:end] = topic_lines
    text = '\n'.join(lines)
    # Drafts use main URLs. Use branch-relative document links so PR navigation
    # follows the prepared branch, while media links remain the recorded URLs.
    text = re.sub(r'https://github\.com/' + re.escape(REPOSITORY) + r'/blob/[^/]+/PROVENANCE\.md', 'PROVENANCE.md', text)
    nav_index = next((i for i, line in enumerate(text.splitlines()) if line.startswith('[English](')), None)
    if nav_index is None:
        raise ValueError(f'Missing introduction language navigation: {locale}')
    lines = text.splitlines()
    lines[nav_index] = _navigation(locale)
    banner = _banner(locale, data['visibility'])
    if banner:
        lines[nav_index + 1:nav_index + 1] = ['', banner]
    return '\n'.join(lines).rstrip() + '\n\n' + _footer(locale) + '\n'


def _subtitle_cell(ep, locale, prefix):
    if not any(sub.get('path') for sub in ep['subtitles'].values()):
        return UI[locale]['missing']
    groups = []
    for language in ('zh-CN', 'en'):
        label = '中文' if language == 'zh-CN' else 'EN'
        formats = []
        for fmt in ('srt', 'vtt'):
            sub = ep['subtitles'][f'.{language}.{fmt}']
            target = sub.get('download_url') or (prefix + quote(sub['path'], safe='/') if sub.get('path') else None)
            formats.append(f'[{fmt.upper()}]({target})' if target else f'{fmt.upper()} —')
        groups.append(label + ' ' + ' / '.join(formats))
    return '<br>'.join(groups)


def _series_page(sid, locale, data):
    item = data['named'][sid]
    episodes = [ep for ep in data['catalog']['episodes'] if ep['series_id'] == sid]
    ui = UI[locale]
    rows = [f'# {ui["series"]} {sid} | {_md(item["titles"][locale])}', '', _navigation(locale), '']
    banner = _banner(locale, data['visibility'])
    if banner:
        rows += [banner, '']
    rows += [_stat_paragraph(locale, episodes), '', ui['notice'], '', ui['subtitle_note'], '',
             f'## {ui["topics"]}', '']
    rows += ['- ' + _md(module) for module in item['modules'][locale]] + ['']
    rows += ['| ' + ' | '.join(ui[key] for key in ('id', 'title', 'video', 'subtitles', 'details')) + ' |',
             '|---|---|---|---|---|']
    for ep in episodes:
        video = f'[{ui["download"]}]({ep["download_url"]})' if ep.get('download_url') else ui['unavailable']
        title = data['lessons'][locale][ep['episode_id']]['title']
        rows.append('| ' + ' | '.join([ep['episode_id'], _md(title), video, _subtitle_cell(ep, locale, '../../'),
                    f'[{ui["details"]}](../../lessons/{ep["episode_id"]}.md)']) + ' |')
    current = next(x for x in data['series']['series'] if x['id'] == sid)
    ending = f'[{ui["home"]}](../../{readme_name(locale)})'
    if current.get('release_url'):
        ending += f' · [Release]({current["release_url"]})'
    rows += ['', ending, '', _footer(locale, '../../'), '']
    return '\n'.join(rows)


def _detail(ep, data):
    sid, episode_id = ep['series_id'], ep['episode_id']
    english = data['lessons']['en'][episode_id]['title']
    names = data['named'][sid]['titles']
    video_en = f'[Download MP4]({ep["download_url"]})' if ep.get('download_url') else 'Unavailable'
    video_zh = f'[下载 MP4]({ep["download_url"]})' if ep.get('download_url') else '暂无已记录下载链接'
    rows = [f'# {_md(english)}', '', '[English](#english) · [简体中文](#zh-cn)', '']
    if data['visibility'] != 'public':
        rows += [_banner('en', data['visibility']), '', _banner('zh-CN', data['visibility']), '']
    rows += ['<a id="english"></a>', '', '## English', '',
             f'- Lesson ID: `{episode_id}`',
             f'- Series {sid}: [{_md(names["en"])}](../series/{sid}/README.md)',
             f'- Original Chinese title: {_md(ep["title"])}',
             f'- Original filename: {_md(ep["original_filename"])}',
             f'- Original relative path: {_md(ep["original_relative_path"])}',
             f'- Video size: {ep["size_bytes"]} bytes', f'- Video: {video_en}']
    if ep.get('duration_seconds') is not None:
        rows.append(f'- Recorded duration: {ep["duration_seconds"]} seconds')
    rows += ['', 'The English title is an editorial translation of the original filename. Source version labels and truncated names are identifiers, not evidence of current software compatibility or validated results.',
             'Chinese / English subtitle file availability is recorded below. Semantic accuracy and audio alignment have not been independently reviewed.', '',
             '<a id="zh-cn"></a>', '', '## 简体中文', '', f'### {_md(ep["title"])}', '',
             f'- 稳定课程 ID：`{episode_id}`', f'- 系列 {sid}：[{_md(names["zh-CN"])}](../series/{sid}/README.zh-CN.md)',
             f'- 原始文件名：{_md(ep["original_filename"])}', f'- 原始相对路径：{_md(ep["original_relative_path"])}',
             f'- 视频大小：{ep["size_bytes"]} 字节', f'- 视频下载：{video_zh}']
    if ep.get('duration_seconds') is not None:
        rows.append(f'- 已记录时长：{ep["duration_seconds"]} 秒')
    rows += ['', '英文题名依据原始文件名编辑翻译；原题的版本、备份及截断标记继续保留，不代表当前软件兼容性或仿真验证结论。',
             '下表记录字幕文件可用性；语义、翻译质量和音画时间轴未经过独立审校。', '',
             '## Subtitles / 字幕', '', '| Language / 语言 | Format / 格式 | File / 文件 |', '|---|---|---|']
    for suffix in SUFFIXES:
        sub = ep['subtitles'][suffix]
        language = '中文 (zh-CN)' if suffix.startswith('.zh-CN') else 'English (en)'
        target = sub.get('download_url')
        if sub.get('path'):
            cell = '[Repository copy / 仓库副本](../' + quote(sub['path'], safe='/') + ')'
            if target:
                cell += f' · [Download / 下载]({target})'
        else:
            cell = 'Missing / 缺失'
        rows.append(f'| {language} | {suffix.rsplit(".", 1)[-1].upper()} | {cell} |')
    rows += ['', '[Home](../README.md) · [中文首页](../README.zh-CN.md) · [Sources and rights / 来源与权利](../PROVENANCE.md)', '']
    return '\n'.join(rows)


def outputs(data):
    """Construct only the public documentation and Chinese display-name update."""
    result = {}
    series = deepcopy(data['series'])
    for item in series['series']:
        item['display_name'] = data['named'][item['id']]['titles']['zh-CN']
    result['series.json'] = json.dumps(series, ensure_ascii=False, indent=2) + '\n'
    for locale in LOCALES:
        result[readme_name(locale)] = _root_readme(locale, data)
        for sid in SERIES:
            result[f'series/{sid}/{readme_name(locale)}'] = _series_page(sid, locale, data)
    for ep in data['catalog']['episodes']:
        result[f'lessons/{ep["episode_id"]}.md'] = _detail(ep, data)
    return result


def render(work):
    """Render the complete existing project without rewriting media metadata."""
    data = load(work)
    rendered = outputs(data)  # Complete strict validation precedes the first write.
    for relative, text in rendered.items():
        work.write_repo(relative, text)
    return {'locales': list(LOCALES), 'project_readmes': len(LOCALES),
            'series_pages': len(SERIES) * len(LOCALES), 'lessons': len(data['catalog']['episodes']),
            'subtitle_copies': data['subtitle_copies_checked'], 'visibility': data['visibility'],
            'remote_calls': 0, 'media_writes': 0,
            'output_hashes': {relative: hashlib.sha256(text.encode('utf-8')).hexdigest() for relative, text in rendered.items()}}


def _case_sensitive_file(root, path):
    """Check exact path spelling even when the local filesystem folds case."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        names = {child.name for child in current.iterdir()} if current.is_dir() else set()
        if part not in names:
            return False
        current /= part
    return current.is_file()


def _anchors(text):
    result = set(re.findall(r'<a\s+id="([^\"]+)"', text))
    counts = {}
    for title in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
        plain = html.unescape(re.sub(r'\\(.)', r'\1', title))
        slug = re.sub(r'[^\w\- ]', '', plain.lower()).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug + (f'-{count}' if count else ''))
    return result


def markdown_links(work):
    issues, checked = [], 0
    root = work.repo('').resolve()
    anchor_cache = {}
    # Reuse the source walker: never descend into links or Windows junctions,
    # including those whose targets are inside the repository.
    files, walk_issues = walk_source(root)
    issues.extend(dict(item, kind='repository_' + item['kind']) for item in walk_issues
                  if not item['relative_path'].startswith('.git/'))
    for entry in files:
        relative = entry['relative_path']
        if relative.startswith('.git/') or not relative.endswith('.md'):
            continue
        path = work.repo(relative)
        text = path.read_text(encoding='utf-8-sig')
        text = re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*(?:\n|$)', '', text)
        for target in re.findall(r'\]\(([^\s)]+)\)', text):
            checked += 1
            parsed = urlsplit(target)
            if parsed.scheme:
                if parsed.scheme not in ('https', 'mailto') or any(ch.isspace() for ch in target):
                    issues.append({'kind': 'invalid_external_link', 'path': path.relative_to(root).as_posix()})
                continue
            # abspath normalizes ../ without resolving wrong-case spellings on
            # Windows, so those errors remain observable for Linux readers.
            linked = Path(os.path.abspath(path.parent / unquote(parsed.path))) if parsed.path else path
            if not linked.resolve().is_relative_to(root) or not _case_sensitive_file(root, linked):
                issues.append({'kind': 'broken_or_wrong_case_link', 'path': path.relative_to(root).as_posix(), 'target': target})
                continue
            try:
                # Resolve lexical relative spelling against the same guarded
                # Workspace method before reading a destination for anchors.
                destination = work.repo(linked.relative_to(root))
            except ValueError:
                issues.append({'kind': 'linked_reparse_point', 'path': relative, 'target': target})
                continue
            if parsed.fragment:
                if linked not in anchor_cache:
                    anchor_cache[linked] = _anchors(destination.read_text(encoding='utf-8-sig'))
                if unquote(parsed.fragment) not in anchor_cache[linked]:
                    issues.append({'kind': 'missing_anchor', 'path': path.relative_to(root).as_posix(), 'target': target})
    return {'checked_links': checked, 'issues': issues, 'passed': not issues}


def validate(work):
    """Read-only local coverage, byte, spelling and anchor validation."""
    data = load(work)
    expected = outputs(data)
    differences = [relative for relative, text in expected.items() if
                   not work.repo(relative).is_file() or work.repo(relative).read_bytes() != text.encode('utf-8')]
    links = markdown_links(work)
    return {'passed': not differences and links['passed'], 'locales': list(LOCALES),
            'project_readmes': len(LOCALES), 'series_pages': len(SERIES) * len(LOCALES),
            'lesson_detail_pages': len(data['catalog']['episodes']),
            'lesson_titles_per_locale': {locale: len(data['lessons'][locale]) for locale in LOCALES},
            'stats': data['stats'], 'subtitle_copies_sha256_checked': data['subtitle_copies_checked'],
            'visibility': data['visibility'], 'output_differences': differences,
            'links': links, 'remote_calls': 0, 'media_writes': 0}
