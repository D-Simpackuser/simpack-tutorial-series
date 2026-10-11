"""Inventory, deterministic catalogue generation, offline plans and audits."""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import re
import shutil
import subprocess
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from core import (SERIES, SUFFIXES, MAX_BYTES, MAX_ASSETS, Workspace, asset_allowed,
                  natural_key, now, safe_source, select_series, sha256, validate_subtitle, walk_source)

VIDEO_EXT = {'.mp4', '.mkv', '.mov', '.avi'}
BASELINE = {'1': (18,72), '2': (13,52), '3': (16,64), '5': (42,164), '6': (8,32), '7': (46,184), '8': (51,204)}


def md(value):
    text = html.escape(str(value), quote=True).replace('|', '&#124;').replace('\n', ' ')
    return re.sub(r'([\\`*_[\]])', r'\\\1', text)


def _variant(value):
    normalized = unicodedata.normalize('NFKC', value).casefold()
    return ''.join(ch for ch in normalized if ch.isalnum())


def _remote_record(state, name):
    repository = state.get('repository')
    return state.get('assets', {}).get(repository + '/' + name, {}) if repository else {}


def _download_link(record):
    url = record.get('browser_download_url')
    # Only API-returned, independently verified, published URLs may become links.
    if (record.get('status') in ('verified','uploaded_verified','skipped_verified') and
            record.get('verification') in ('verified','download_verified') and record.get('draft') is False and
            isinstance(url, str) and url.startswith('https://github.com/') and
            not any(ch in url for ch in ('\n','\r',' '))):
        return url
    return None


def _release_record(state, series_id):
    repository = state.get('repository')
    record = state.get('releases', {}).get(f'{repository}/{series_id}', {}) if repository else {}
    url = record.get('html_url')
    if record.get('draft') is False and isinstance(url, str):
        parsed = urlsplit(url)
        if (parsed.scheme == 'https' and parsed.netloc == 'github.com' and
                parsed.path.startswith(f'/{repository}/releases/') and
                not parsed.query and not parsed.fragment and not any(ch.isspace() for ch in url)):
            return record, url
    return record, None


def _download_status(record, url):
    if url:
        return '已验证（需仓库访问权限）' if record.get('visibility') == 'private' else '已验证'
    return '草稿待发布' if record.get('draft') is True else '待上传'


def snapshot(work, label):
    data = {'created_at': now(), 'sources': {}}
    for kind in ('video', 'subtitle'):
        root = work.config[kind + '_root']
        files, issues = walk_source(root)
        data['sources'][kind] = {'root': root, 'files': files, 'issues': issues}
    work.write_json(f'source_snapshot_{label}.json', data)
    return data


def compare_snapshots(before, after):
    changes = []
    for kind in ('video', 'subtitle'):
        a = {x['relative_path']: x for x in before['sources'][kind]['files']}
        b = {x['relative_path']: x for x in after['sources'][kind]['files']}
        for rel in sorted(a.keys() | b.keys(), key=natural_key):
            if a.get(rel) != b.get(rel):
                changes.append({'kind': 'source_metadata_changed', 'source': kind, 'relative_path': rel,
                                'before': a.get(rel), 'after': b.get(rel)})
    return changes


def _duration(work, path):
    executable = work.config.get('ffprobe', shutil.which('ffprobe'))
    if not executable:
        return None, 'ffprobe_unavailable'
    try:
        result = subprocess.run([executable, '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'json', str(path)], capture_output=True, text=True, timeout=30, shell=False)
        duration = float(json.loads(result.stdout)['format']['duration']) if result.returncode == 0 else None
        if duration is None or not math.isfinite(duration) or duration < 0:
            return None, 'probe_failed'
        return duration, 'ffprobe'
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return None, 'probe_failed'


def scan(work):
    before = snapshot(work, 'before')
    anomalies = []
    for source, details in before['sources'].items():
        anomalies.extend(dict(x, source=source) for x in details['issues'])
    video_files = []
    for item in before['sources']['video']['files']:
        rel = Path(item['relative_path'])
        if rel.parts[0] not in SERIES or len(rel.parts) < 2:
            anomalies.append({'kind': 'unexpected_series_or_root_file', 'source': 'video', **item})
        elif rel.suffix.lower() in VIDEO_EXT:
            video_files.append(item)
        else:
            anomalies.append({'kind': 'unrecognized_video_file', **item})
    subtitles = {}
    for item in before['sources']['subtitle']['files']:
        rel = item['relative_path']
        suffix = next((suffix for suffix in SUFFIXES if rel.endswith(suffix)), None)
        if not suffix or Path(rel).parts[0] not in SERIES:
            anomalies.append({'kind': 'unrecognized_subtitle_file', **item})
            continue
        subtitles[rel] = dict(item, suffix=suffix)
    ids = work.read_json('id_map.json', {'schema_version': 1, 'entries': {}, 'next': {sid: 1 for sid in SERIES}})
    rights = work.read_json('rights.json', {'default': 'unknown', 'episodes': {}})
    state = work.read_json('upload_state.json', {'schema_version': 1, 'assets': {}, 'releases': {}, 'trial_gates': {}})
    episodes, used = [], set()
    new_names = []
    for item in sorted(video_files, key=lambda x: natural_key(x['relative_path'])):
        rel = item['relative_path']
        relative = Path(rel)
        sid = relative.parts[0]
        if rel not in ids['entries']:
            index = ids['next'].get(sid, 1)
            ids['entries'][rel] = {'series_id': sid, 'episode_id': f's{int(sid):02d}-e{index:03d}', 'original_filename': relative.name}
            ids['next'][sid] = index + 1
            new_names.append(rel)
        episode_id = ids['entries'][rel]['episode_id']
        ep_rights = rights['episodes'].setdefault(episode_id, {key: 'unknown' for key in ('video','zh-CN','en','transcript','other')})
        path = safe_source(work.config['video_root'], rel)
        status = 'ready'
        try:
            with path.open('rb') as stream:
                stream.read(1)
            if item['size_bytes'] == 0:
                status = 'zero_byte'
            elif item['size_bytes'] >= MAX_BYTES:
                status = 'blocked_oversize'
        except OSError:
            status = 'unreadable'
        duration, duration_status = _duration(work, path)
        video = dict(item, path=str(path), asset_name=episode_id + relative.suffix.lower(), status=status,
                     rights=ep_rights['video'], upload_status=_remote_record(state, episode_id + relative.suffix.lower()).get('status', 'pending'))
        if status != 'ready':
            anomalies.append({'kind': status, 'relative_path': rel, 'size_bytes': item['size_bytes']})
        subs = {}
        for suffix in SUFFIXES:
            expected = (relative.parent / (relative.stem + suffix)).as_posix()
            entry = {'relative_path': expected, 'path': None, 'status': 'missing', 'asset_name': episode_id + suffix,
                     'size_bytes': None, 'mtime_ns': None, 'sha256': None,
                     'rights': ep_rights['zh-CN' if 'zh-CN' in suffix else 'en'], 'upload_status': 'pending'}
            if expected in subtitles:
                used.add(expected)
                sub_path = safe_source(work.config['subtitle_root'], expected)
                info = subtitles[expected]
                entry.update(info, path=str(sub_path))
                validation = validate_subtitle(sub_path, duration)
                entry['validation'] = validation
                try:
                    entry['sha256'] = sha256(sub_path)
                    entry['status'] = 'zero_byte' if info['size_bytes'] == 0 else 'matched' if validation['valid'] else 'invalid'
                except OSError:
                    entry['status'] = 'unreadable'
                if entry['status'] != 'matched':
                    anomalies.append({'kind': 'subtitle_' + entry['status'], 'relative_path': expected, 'issues': validation['issues']})
                if validation['overlap_count']:
                    anomalies.append({'kind': 'subtitle_overlap', 'relative_path': expected, 'count': validation['overlap_count']})
            else:
                candidates = [key for key in subtitles if _variant(Path(key).name) == _variant(Path(expected).name)]
                anomalies.append({'kind': 'missing_subtitle', 'relative_path': rel, 'expected': expected, 'candidates_only': candidates})
                if candidates:
                    anomalies.append({'kind': 'uncertain_match_candidates', 'expected': expected, 'candidates': candidates,
                                      'note': '未自动匹配；名称差异或跨系列'})
            subs[suffix] = entry
        episodes.append({'series_id': sid, 'episode_id': episode_id, 'relative_path': rel,
                         'original_filename': relative.name, 'title': relative.stem, 'video': video,
                         'subtitles': subs, 'duration_seconds': duration, 'duration_status': duration_status,
                         'rights': ep_rights, 'anomalies': [x['kind'] for x in anomalies if x.get('relative_path') == rel]})
    current = {ep['relative_path'] for ep in episodes}
    for previous in ids['entries']:
        if previous not in current:
            anomalies.append({'kind': 'removed_or_renamed_source', 'previous_relative_path': previous,
                              'new_source_candidates_only': new_names, 'episode_id': ids['entries'][previous]['episode_id']})
    for rel in sorted(subtitles.keys() - used, key=natural_key):
        path = safe_source(work.config['subtitle_root'], rel)
        validation = validate_subtitle(path)
        anomalies.append({'kind': 'orphan_subtitle', 'relative_path': rel, 'validation': validation})
    groups, duplicate_names = defaultdict(list), defaultdict(list)
    for ep in episodes:
        prefix = re.match(r'^\d+(?:[-－]\d+)*', ep['title'])
        if prefix:
            groups[(ep['series_id'], prefix.group())].append(ep['relative_path'])
        duplicate_names[ep['original_filename']].append(ep['relative_path'])
    for (sid, prefix), paths in groups.items():
        if len(paths) > 1:
            anomalies.append({'kind': 'duplicate_numeric_prefix', 'series_id': sid, 'prefix': prefix, 'paths': paths,
                              'note': '完整路径独立编号，无合并'})
    for name, paths in duplicate_names.items():
        if len(paths) > 1:
            anomalies.append({'kind': 'duplicate_filename', 'name': name, 'paths': paths, 'note': '不同目录保留独立课目'})
    after = snapshot(work, 'after')
    changes = compare_snapshots(before, after)
    anomalies.extend(changes)
    summary_series = {}
    for sid in SERIES:
        eps = [ep for ep in episodes if ep['series_id'] == sid]
        subtitle_count = sum(Path(rel).parts[0] == sid for rel in subtitles)
        summary_series[sid] = {'videos': len(eps), 'subtitles': subtitle_count,
            'complete_subtitle_groups': sum(all(x['path'] is not None for x in ep['subtitles'].values()) for ep in eps),
            'video_bytes': sum(ep['video']['size_bytes'] for ep in eps), 'release_tag': f'series-{sid}-v1',
            'baseline_video_delta': len(eps) - BASELINE[sid][0], 'baseline_subtitle_delta': subtitle_count - BASELINE[sid][1]}
    summary = {'videos': len(episodes), 'subtitles': len(subtitles), 'video_bytes': sum(ep['video']['size_bytes'] for ep in episodes),
               'subtitle_bytes': sum(item['size_bytes'] for item in subtitles.values()), 'series': summary_series,
               'complete_subtitle_groups': sum(x['complete_subtitle_groups'] for x in summary_series.values()),
               'missing_subtitle_files': sum(x['kind'] == 'missing_subtitle' for x in anomalies),
               'oversize_videos': sum(ep['video']['status'] == 'blocked_oversize' for ep in episodes),
               'source_metadata_unchanged': not changes, 'video_hashes_computed': 0,
               'subtitle_hashes_computed': sum(x['sha256'] is not None for ep in episodes for x in ep['subtitles'].values()),
               'duration_known': sum(ep['duration_seconds'] is not None for ep in episodes),
               'largest_video': max(({'relative_path': ep['relative_path'], 'size_bytes': ep['video']['size_bytes']} for ep in episodes),
                                    key=lambda x: x['size_bytes'], default=None)}
    inventory = {'schema_version': 1, 'scanned_at': now(), 'summary': summary, 'episodes': episodes, 'anomalies': anomalies}
    work.write_json('config.json', work.config)
    work.write_json('id_map.json', ids)
    work.write_json('rights.json', rights)
    work.write_json('inventory.json', inventory)
    work.write_json('upload_state.json', state)
    stream = io.StringIO(newline='')
    fields = ['series_id','episode_id','relative_path','title','size_bytes','modified_at','duration_seconds','asset_name','rights','upload_status','anomalies']
    fields += [suffix + field for suffix in SUFFIXES for field in (':path', ':status')]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for ep in episodes:
        video = ep['video']
        row = {key: ep.get(key, '') for key in ('series_id','episode_id','relative_path','title','duration_seconds')}
        row.update(size_bytes=video['size_bytes'], modified_at=datetime.fromtimestamp(video['mtime_ns']/1e9, timezone.utc).isoformat(),
                   asset_name=video['asset_name'], rights=json.dumps(ep['rights'], ensure_ascii=False), upload_status=video['upload_status'],
                   anomalies='; '.join(ep['anomalies']))
        for suffix in SUFFIXES:
            row[suffix + ':path'] = ep['subtitles'][suffix]['path'] or ''
            row[suffix + ':status'] = ep['subtitles'][suffix]['status']
        # Excel formula interpretation is blocked without changing the private JSON originals.
        writer.writerow({k: "'" + v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in row.items()})
    work.write(Path('_local/inventory.csv'), stream.getvalue().encode('utf-8-sig'))
    lines = ['# 真实扫描报告', '', f'扫描时间：{inventory["scanned_at"]}', '', '| 系列 | 视频 | 字幕 | 四种齐全课程 | 视频字节数 | 基线差异（视频/字幕） |', '|---|---:|---:|---:|---:|---|']
    for sid, item in summary_series.items():
        lines.append(f'| {sid} | {item["videos"]} | {item["subtitles"]} | {item["complete_subtitle_groups"]} | {item["video_bytes"]} | {item["baseline_video_delta"]}/{item["baseline_subtitle_delta"]} |')
    largest = summary['largest_video']
    lines += ['', f'视频总字节数：{summary["video_bytes"]}（{summary["video_bytes"] / 1024**3:.3f} GiB）；字幕总字节数：{summary["subtitle_bytes"]}。',
              f'最大视频：{md(largest["relative_path"])}，{largest["size_bytes"]} 字节。' if largest else '没有视频。',
              f'扫描前后源元数据未变化：{summary["source_metadata_unchanged"]}。字幕已计算 SHA-256：{summary["subtitle_hashes_computed"]}；视频：0。',
              f'已取得时长的视频：{summary["duration_known"]}；未知时不执行字幕时长越界检查。未校对语义、翻译或硬字幕。',
              '', '## 缺字幕清单', '']
    missing_lessons = [ep for ep in episodes if any(sub['status'] == 'missing' for sub in ep['subtitles'].values())]
    lines.extend('- ' + md(ep['relative_path']) + '：' + '、'.join(suffix for suffix, sub in ep['subtitles'].items() if sub['status'] == 'missing') for ep in missing_lessons)
    if not missing_lessons:
        lines.append('无缺字幕视频。')
    prefixes = [x for x in anomalies if x['kind'] == 'duplicate_numeric_prefix']
    lines += ['', f'## 重复数字前缀（{len(prefixes)} 组，独立保留）', '']
    for item in prefixes:
        lines.append(f'- 系列 {item["series_id"]}，前缀 {item["prefix"]}：' + '；'.join(md(path) for path in item['paths']))
    oversized = [ep for ep in episodes if ep['video']['status'] == 'blocked_oversize']
    lines += ['', '## 超限清单', '']
    lines.extend('- ' + md(ep['relative_path']) + f'：{ep["video"]["size_bytes"]} 字节，blocked_oversize。' for ep in oversized)
    if not oversized:
        lines.append('无超限视频；所有视频严格小于 2147483648 字节。')
    lines += ['', '## 完整异常记录（含跨系列重名）', '']
    lines.extend('- ' + md(json.dumps(x, ensure_ascii=False)) for x in anomalies)
    if not anomalies:
        lines.append('无异常。')
    work.write_local('scan_report.md', '\n'.join(lines) + '\n')
    return inventory


def plan(work, series='all'):
    inventory = work.read_json('inventory.json')
    if inventory is None:
        raise ValueError('Run scan first')
    selected = select_series(series)
    releases = []
    for sid in selected:
        lessons, count = [], 0
        for ep in inventory['episodes']:
            if ep['series_id'] != sid:
                continue
            assets = []
            for kind, entry in [('video', ep['video']), *ep['subtitles'].items()]:
                blocked = []
                if not entry.get('path'):
                    blocked.append('missing')
                if entry.get('size_bytes') is not None and not asset_allowed(entry['size_bytes']):
                    blocked.append('blocked_oversize' if entry['size_bytes'] >= MAX_BYTES else 'zero_byte')
                if entry['status'] in ('invalid','unreadable','zero_byte'):
                    blocked.append(entry['status'])
                if entry.get('rights') != 'confirmed':
                    blocked.append('rights_unknown')
                assets.append({'kind': kind, 'name': entry['asset_name'], 'source_path': entry.get('path'),
                               'size_bytes': entry.get('size_bytes'), 'blocked_reasons': sorted(set(blocked)),
                               'locally_available': entry.get('path') is not None})
                count += bool(entry.get('path') and entry.get('size_bytes') is not None and asset_allowed(entry['size_bytes']))
            lessons.append({'episode_id': ep['episode_id'], 'title': ep['title'], 'assets': assets})
        releases.append({'series_id': sid, 'release_tag': f'series-{sid}-v1', 'draft': True,
                         'available_asset_count': count, 'asset_count_allowed': count <= MAX_ASSETS, 'lessons': lessons})
    result = {'created_at': now(), 'mode': 'offline_dry_run', 'remote_calls': 0,
              'authorization_required': True, 'release_max_asset_bytes_exclusive': MAX_BYTES,
              'release_max_assets': MAX_ASSETS, 'releases': releases}
    work.write_json('upload_plan.json', result)
    return result


def build(work):
    # Internationalized projects render from the already verified schema 1
    # catalogue. Do not reconstruct links, reset names, rewrite subtitles or
    # overwrite reader-maintained provenance with the legacy initial template.
    import i18n_engine
    if i18n_engine.enabled(work):
        return i18n_engine.render(work)
    inventory = work.read_json('inventory.json')
    if inventory is None:
        raise ValueError('Run scan first')
    scanned = work.read_json('source_snapshot_after.json')
    current = snapshot(work, 'build_before')
    if scanned is None or compare_snapshots(scanned, current):
        raise ValueError('Sources changed since scan; run scan before build')
    documentation_root = Path(__file__).resolve().parents[1] / 'docs'
    # A fresh legacy project has no multilingual/maintainer documentation yet.
    # Reuse the retained complete upload guide, not a Stage C navigation stub
    # whose targets would be absent from such a project.
    retained_guide = documentation_root / 'maintainer/publishing.md'
    documentation = retained_guide if retained_guide.is_file() else documentation_root / 'publishing.md'
    if not work.repo('docs/publishing.md').exists():
        guide = documentation.read_text(encoding='utf-8')
        # The current maintainer guide begins with links/commands for an
        # internationalized project. A fresh legacy workspace has none of
        # those inputs or architecture pages; retain only its A/B section.
        retained_section = '\n## Retained Stage A/B workflow / 保留的阶段 A/B 流程\n'
        if documentation == retained_guide and retained_section in guide:
            guide = guide.split('\n', 1)[0] + '\n\n' + guide.split(retained_section, 1)[1].lstrip('\n')
        work.write_repo('docs/publishing.md', guide)
    before = current
    episodes = inventory['episodes']
    checks = []
    public_eps = []
    state = work.read_json('upload_state.json', {'assets': {}})
    rights = work.read_json('rights.json', {'default': 'unknown', 'episodes': {}})
    def right(episode_id, material):
        return rights.get('episodes', {}).get(episode_id, {}).get(material, rights.get('default', 'unknown'))
    for ep in episodes:
        subs = {}
        for suffix, item in ep['subtitles'].items():
            record = _remote_record(state, item['asset_name'])
            sub_url = _download_link(record)
            public = {'status': item['status'], 'asset_name': item['asset_name'], 'path': None, 'sha256': None,
                      'download_url': sub_url, 'download_status': _download_status(record, sub_url),
                      'download_visibility': record.get('visibility') if sub_url else None,
                      'rights': right(ep['episode_id'], 'zh-CN' if 'zh-CN' in suffix else 'en')}
            if item['path'] and item['status'] != 'unreadable':
                src = safe_source(work.config['subtitle_root'], item['relative_path'])
                source_hash = sha256(src)
                if source_hash != item['sha256']:
                    raise ValueError('Subtitle source changed since scan; run scan before build')
                rel = f'subtitles/{ep["series_id"]}/{item["asset_name"]}'
                dest = work.write_repo(rel, src.read_bytes())
                copy_hash, after_hash = sha256(dest), sha256(src)
                if source_hash != copy_hash or source_hash != after_hash:
                    raise ValueError('Subtitle copy SHA-256 mismatch')
                public.update(path=rel, sha256=copy_hash)
                checks.append({'source_relative_path': item['relative_path'], 'copy_relative_path': rel,
                               'source_sha256': source_hash, 'copy_sha256': copy_hash, 'equal': True})
            subs[suffix] = public
        remote = _remote_record(state, ep['video']['asset_name'])
        url = _download_link(remote)
        public_eps.append({'series_id': ep['series_id'], 'episode_id': ep['episode_id'], 'original_relative_path': ep['relative_path'],
                           'original_filename': ep['original_filename'], 'title': ep['title'], 'size_bytes': ep['video']['size_bytes'],
                           'duration_seconds': ep['duration_seconds'], 'video_status': ep['video']['status'],
                           'asset_name': ep['video']['asset_name'], 'download_url': url,
                           'download_status': _download_status(remote, url),
                           'download_visibility': remote.get('visibility') if url else None,
                           'rights': {material: right(ep['episode_id'], material) for material in ('video', 'zh-CN', 'en')},
                           'subtitles': subs})
    summary = inventory['summary']
    series_items = [{'id': sid, 'display_name': f'系列 {sid}', 'release_tag': f'series-{sid}-v1',
                     'page': f'series/{sid}/README.md', 'videos': summary['series'][sid]['videos'],
                     'subtitles': summary['series'][sid]['subtitles'],
                     'release_url': _release_record(state, sid)[1],
                     'release_status': '已发布' if _release_record(state, sid)[1] else
                         '草稿待发布' if _release_record(state, sid)[0].get('draft') is True else '待创建',
                     'release_visibility': state.get('visibility') if _release_record(state, sid)[1] else None} for sid in SERIES]
    work.write_repo('series.json', json.dumps({'series': series_items}, ensure_ascii=False, indent=2) + '\n')
    work.write_repo('catalog.json', json.dumps({'schema_version': 1, 'episodes': public_eps}, ensure_ascii=False, indent=2) + '\n')
    confirmed_counts = {material: sum(ep['rights'][material] == 'confirmed' for ep in public_eps)
                        for material in ('video', 'zh-CN', 'en')}
    rights_description = (f'本轮已确认 {confirmed_counts["video"]} 课的视频上传许可、{confirmed_counts["zh-CN"]} 课的中文字幕上传许可和 {confirmed_counts["en"]} 课的英文字幕上传许可；未确认资料仍排除，逐字稿及其他资料不自动放行。'
                          if any(confirmed_counts.values()) else '视频与字幕传播权利待核实。')
    readme = ['# Simpack 系列教程目录', '', f'本地实际清单：{summary["videos"]} 个视频、{summary["subtitles"]} 个字幕文件，{summary["complete_subtitle_groups"]} 课具备四种字幕文件。',
              '', '仅整理原始文件名、大小和字幕对应关系。系列名称为默认名称，未核实课程作者或资料来源。' + rights_description,
              '排序是文件名自然排序，不表示已核验教学先后顺序。字幕基础格式检查不代表语义、翻译质量或音画时间轴已校对。',
              '', '| 系列入口 | 视频 | 字幕 |', '|---|---:|---:|']
    readme.extend(f'| [系列 {x["id"]}]({x["page"]}) | {x["videos"]} | {x["subtitles"]} |' for x in series_items)
    readme += ['', '## Release 状态', '', '| 系列 | Release | 可见性 |', '|---|---|---|']
    for item in series_items:
        release_link = f'[已发布 Release]({item["release_url"]})' if item['release_url'] else item['release_status']
        visibility = 'private（需仓库访问权限）' if item['release_visibility'] == 'private' else item['release_visibility'] or '未验证'
        readme.append(f'| 系列 {item["id"]} | {release_link} | {visibility} |')
    download_count = sum(bool(ep['download_url']) for ep in public_eps)
    download_description = f'视频下载链接已验证：{download_count}/{len(public_eps)}。'
    if download_count < len(public_eps):
        download_description += '尚未提供已验证下载链接的视频，具体状态见各课详情。'
    readme += ['', '## 下载与使用', '', download_description + '视频作为每系列的 GitHub Release 附件；使用时下载视频及同课字幕，在本地播放器中选择字幕。',
               '本地字幕副本见[字幕目录](subtitles/README.md)，短英文附件名与稳定课程 ID 对应。缺字幕视频仍保留独立课程，详情页逐项标明缺失。',
               '', '视频不进入 Git，不使用 Git LFS；第一版未提供在线播放器。',
               '', '[来源与权利说明](PROVENANCE.md) · [发布工具与阶段 B 操作](docs/publishing.md)', '']
    work.write_repo('README.md', '\n'.join(readme))
    for sid in SERIES:
        rows = [f'# 系列 {sid}', '', f'原始系列编号：{sid}；默认名称：系列 {sid}。',
                '显示顺序为文件名自然排序；课程 ID 在后续新增文件时保持稳定。下载可见性以每课状态为准。',
                '', '| 稳定 ID | 原始中文标题 | 时长（秒） | 视频 | 中文 SRT | 中文 VTT | 英文 SRT | 英文 VTT | 详情 |', '|---|---|---|---|---|---|---|---|---|']
        for ep in public_eps:
            if ep['series_id'] != sid:
                continue
            sub_links = []
            for suffix in SUFFIXES:
                sub = ep['subtitles'][suffix]
                link = '[本地副本](../../' + quote(sub['path'], safe='/') + ')' if sub['path'] else '缺失'
                if sub['download_url']:
                    link += f' / [下载字幕]({sub["download_url"]})（{sub["download_status"]}）'
                if sub['path'] and sub['status'] != 'matched':
                    link += '（格式异常）'
                sub_links.append(link)
            rows.append('| ' + ' | '.join([ep['episode_id'], md(ep['title']), str(ep['duration_seconds']) if ep['duration_seconds'] is not None else '未知',
                '超限，阻止上传' if ep['video_status'] == 'blocked_oversize' else f'[下载视频]({ep["download_url"]})（{ep["download_status"]}）' if ep['download_url'] else ep['download_status'], *sub_links,
                f'[课程详情](../../lessons/{ep["episode_id"]}.md)']) + ' |')
        release_url = _release_record(state, sid)[1]
        if release_url:
            rows += ['', f'[系列 Release]({release_url})' + ('（private，需仓库访问权限）' if state.get('visibility') == 'private' else '')]
        rows += ['', '[返回总目录](../../README.md)', '']
        work.write_repo(f'series/{sid}/README.md', '\n'.join(rows))
    for ep in public_eps:
        detail = [f'# {md(ep["title"])}', '', f'- 稳定 ID：{ep["episode_id"]}', f'- 系列：[系列 {ep["series_id"]}](../series/{ep["series_id"]}/README.md)',
                  f'- 原始文件名：{md(ep["original_filename"])}', f'- 原始相对路径：{md(ep["original_relative_path"])}',
                  f'- 视频字节数：{ep["size_bytes"]}', f'- 时长（秒）：{ep["duration_seconds"] if ep["duration_seconds"] is not None else "未知"}',
                  f'- 视频下载：' + (f'[下载视频]({ep["download_url"]})（{ep["download_status"]}）' if ep['download_url'] else ep['download_status']), '', '| 字幕语言/格式 | 对应状态 | 副本 |', '|---|---|---|']
        for suffix in SUFFIXES:
            sub = ep['subtitles'][suffix]
            link = f'[本地副本](../{quote(sub["path"], safe="/")})' if sub['path'] else '缺失'
            if sub['download_url']:
                link += f' / [下载字幕]({sub["download_url"]})（{sub["download_status"]}）'
            detail.append(f'| {suffix} | {md(sub["status"])} | {link} |')
        ep_rights = '本轮已确认视频与中英字幕上传许可；未确认的其他资料仍排除。' if all(ep['rights'][m] == 'confirmed' for m in ('video','zh-CN','en')) else '资料传播权利以逐项记录为准；未确认素材仍排除。'
        detail += ['', '此页仅记录清单事实；课程内容、作者、技术结论、字幕翻译质量与语义时间轴均未核验。' + ep_rights, '', '[返回总目录](../README.md)', '']
        work.write_repo(f'lessons/{ep["episode_id"]}.md', '\n'.join(detail))
    subtitle_readme = ['# 字幕目录', '', f'本地逐文件复制并实际比对 SHA-256：{len(checks)} 个文件。保留原始字节，不改换行或字幕正文。',
        '中文与英文各有 SRT/VTT。缺失文件没有生成替代内容；只有本轮逐项确认上传许可的副本可提交或上传，未确认素材仍排除。', '', '| 系列 | 字幕副本数 | 对应课程 |', '|---|---:|---|']
    for sid in SERIES:
        subtitle_readme.append(f'| {sid} | {sum(Path(x["copy_relative_path"]).parts[1] == sid for x in checks)} | [系列 {sid}](../series/{sid}/README.md) |')
    subtitle_readme += ['', '[返回总目录](../README.md)', '']
    work.write_repo('subtitles/README.md', '\n'.join(subtitle_readme))
    work.write_repo('PROVENANCE.md', '# 来源与传播权利\n\nsimpack-local-publish-v1\n\n目录记录来自本地实际文件清单；课程作者与来源尚未核实。视频、中文字幕、英文字幕、逐字稿及其他资料的传播权利以私有权利记录逐项确认，未确认项为 unknown。\n\n不默认授予课程 MIT/CC 许可证，不声称官方课程或用户原创。private 仓库也需要资料传播授权。只有本轮明确授权的文件可进入远端。\n\n字幕副本保持原件字节；匹配、格式与哈希检查不代表语义校对。原件与独立备份仍需保留。\n')
    ignore = ['# Media and task-private data', '*.mp4','*.MP4','*.mkv','*.MKV','*.mov','*.MOV','*.avi','*.AVI',
              '*.zip','*.7z','*.rar','*.tar','*.gz','*.bin','*.fbi','*.simpack','*.spck','*.dll','*.exe',
              '*.log','*.tmp','*.local.json','.env','.env.*','*token*','*credential*','*.pem','*.key',
              '_local/','staging/','backups/','__pycache__/','*.py[cod]','.pytest_cache/',
              '# Unconfirmed subtitle materials remain unstaged; audited authorized staging can use explicit -f paths.',
              '/subtitles/**/*.srt','/subtitles/**/*.vtt','']
    work.write_repo('.gitignore', '\n'.join(ignore))
    work.write_repo('.gitattributes', '*.srt -text\n*.vtt -text\n*.md text eol=lf\n*.json text eol=lf\n*.py text eol=lf\n')
    work.write_repo('docs/config.example.json', json.dumps({'video_root': '<VIDEO_SOURCE>', 'subtitle_root': '<SUBTITLE_SOURCE>',
        'work_root': '<WORKSPACE>', 'github': {'owner': None, 'repository': 'simpack-tutorial-series', 'allow_remote_write': False,
        'initial_visibility': 'private'}, 'ffprobe': None}, ensure_ascii=False, indent=2) + '\n')
    after = snapshot(work, 'build_after')
    changes = compare_snapshots(before, after)
    work.write_json('subtitle_copy_checks.json', {'created_at': now(), 'files': checks, 'source_metadata_changes': changes,
        'all_copies_sha256_equal': all(x['equal'] for x in checks), 'video_hashes_computed': 0})
    if changes:
        raise ValueError('Source metadata changed during build')
    return {'lessons': len(public_eps), 'series_pages': len(SERIES), 'subtitle_copies': len(checks), 'source_metadata_unchanged': True}


def audit(work):
    """Inspect complete candidate repository and local Markdown links; stage nothing."""
    files, walk_issues = walk_source(work.root / 'repo')
    issues = [x for x in walk_issues if not x['relative_path'].startswith('.git/')]
    candidate, subtitle_materials, unmanaged = [], [], []
    owned_code = {'scripts/core.py','scripts/catalog_engine.py','scripts/publish.py','scripts/github_release.py',
                  'scripts/i18n_engine.py','tests/test_i18n.py',
                  'scripts/library_verify.py','tests/test_library_verify.py','tests/test_branding.py',
                  'tests/test_local.py','tests/test_github_release.py','tests/test_stage_b_catalog.py',
                  'tests/test_stage_b_release.py','docs/publishing.md'}
    forbidden_extensions = VIDEO_EXT | {'.zip','.rar','.7z','.bin','.log','.tmp','.pem','.key','.exe','.dll'}
    secret_pattern = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})')
    path_pattern = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]|/(?:Users|home)/[^/\s]+/')
    for info in files:
        rel = info['relative_path']
        if rel.startswith('.git/'):
            continue
        path = work.repo(rel)
        if '__pycache__' in Path(rel).parts or path.suffix in ('.pyc','.pyo'):
            issues.append({'kind': 'cache_in_repo', 'path': rel})
            continue
        if path.suffix.lower() in forbidden_extensions or any(p in Path(rel).parts for p in ('_local','staging','backups')) or rel.endswith('.local.json') or path.name.startswith('.env'):
            issues.append({'kind': 'forbidden_public_file', 'path': rel})
        raw = path.read_bytes()
        text = raw.decode('utf-8-sig', errors='replace')
        if secret_pattern.search(text) or path_pattern.search(text) or any(str(work.config[k]) in text for k in ('video_root','subtitle_root','work_root')):
            issues.append({'kind': 'private_path_or_credential', 'path': rel})
        if path.suffix.lower() == '.md':
            for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)', text):
                url = urlsplit(target)
                if not url.scheme and url.path:
                    linked = (path.parent / unquote(url.path)).resolve()
                    if not linked.is_relative_to((work.root / 'repo').resolve()) or not linked.is_file():
                        issues.append({'kind': 'broken_or_escaped_markdown_link', 'path': rel, 'target': target})
        if path.suffix.lower() in ('.srt','.vtt'):
            subtitle_materials.append(rel)
        elif 'repo/' + rel in work.managed or rel in owned_code:
            candidate.append(rel)
        else:
            unmanaged.append(rel)
    result = {'created_at': now(), 'passed': not issues, 'issues': issues, 'candidate_files': sorted(candidate),
              'unconfirmed_material_files': sorted(subtitle_materials), 'excluded_unmanaged_files': sorted(unmanaged), 'git_index_checked': False,
              'staged_files': [], 'remote_calls': 0}
    stage_c_manifest = work.read_json('stage_c/stage_manifest.json')
    stage_c = stage_c_manifest is not None
    stage_b = work.config.get('phase') == 'B' and not stage_c
    stage_allowed = set()
    subtitle_hashes = {}
    if stage_c:
        # Documentation preparation has its own exact manifest. It neither
        # changes Phase B's private authorization nor authorizes media edits.
        manifest = stage_c_manifest
        listed = manifest.get('files') if isinstance(manifest, dict) else None
        if (not isinstance(manifest, dict) or manifest.get('phase') != 'C' or
                manifest.get('repository') != 'D-Simpackuser/simpack-tutorial-series' or
                manifest.get('repository_id') != 1412669436 or
                manifest.get('authorization_scope') != 'documentation_only' or
                not isinstance(listed, list) or any(not isinstance(rel, str) for rel in listed) or
                len(listed) != len(set(listed))):
            result['issues'].append({'kind': 'invalid_stage_c_stage_manifest'})
        else:
            for rel in listed:
                parts = Path(rel).parts
                doc_location = bool(parts) and (len(parts) == 1 or parts[0] in
                                ('docs', 'series', 'lessons', 'i18n', 'scripts', 'tests', '.github'))
                if (rel not in candidate or not doc_location or
                        Path(rel).suffix.lower() not in ('.md', '.json', '.py', '.yml', '.yaml')):
                    result['issues'].append({'kind': 'unauthorized_stage_c_manifest_file', 'path': rel})
                else:
                    stage_allowed.add(rel)
        result['stage_c_documentation_files'] = sorted(stage_allowed)
        # Existing subtitle bytes can be reviewed, but no new or changed
        # subtitle blob is approved by this documentation-only manifest.
        result['unconfirmed_material_files'] = []
        inventory = work.read_json('inventory.json', {})
        expected_subs = {f'subtitles/{ep["series_id"]}/{data.get("asset_name", "")}': data.get('sha256')
                         for ep in inventory.get('episodes', []) for data in ep.get('subtitles', {}).values()
                         if data.get('status') == 'matched' and data.get('sha256')}
        for rel in subtitle_materials:
            if rel not in expected_subs or sha256(work.repo(rel)) != expected_subs[rel]:
                result['issues'].append({'kind': 'retained_subtitle_sha256_mismatch', 'path': rel})
    elif stage_b:
        rights = work.read_json('rights.json', {})
        inventory = work.read_json('inventory.json', {})
        authorization = work.read_json('authorization.json', {})
        approved_names = None
        if 'approved_existing_asset_names' in authorization:
            approved = authorization['approved_existing_asset_names']
            if (not isinstance(approved, list) or not approved or
                    any(not isinstance(name, str) or not name.strip() for name in approved) or
                    len(approved) != len(set(approved))):
                result['issues'].append({'kind': 'invalid_stage_b_approved_asset_names'})
                approved_names = set()
            else:
                approved_names = set(approved)
        for ep in inventory.get('episodes', []):
            for suffix, data in ep.get('subtitles', {}).items():
                material = 'zh-CN' if suffix.startswith('.zh-CN') else 'en'
                confirmed = rights.get('episodes', {}).get(ep['episode_id'], {}).get(material, rights.get('default', 'unknown')) == 'confirmed'
                rel = f'subtitles/{ep["series_id"]}/{data.get("asset_name", "")}'
                specifically_approved = approved_names is None or data.get('asset_name') in approved_names
                if confirmed and specifically_approved and data.get('status') == 'matched' and data.get('sha256') and rel in subtitle_materials:
                    subtitle_hashes[rel] = data['sha256']
        manifest = work.read_json('stage_b_stage_manifest.json', {})
        listed = manifest.get('files') if isinstance(manifest, dict) else None
        if (not isinstance(listed, list) or any(not isinstance(rel, str) for rel in listed) or
                len(listed) != len(set(listed))):
            result['issues'].append({'kind': 'invalid_stage_b_stage_manifest'})
        else:
            eligible = set(candidate) | subtitle_hashes.keys()
            for rel in listed:
                if rel not in eligible:
                    result['issues'].append({'kind': 'unauthorized_stage_manifest_file', 'path': rel})
                else:
                    stage_allowed.add(rel)
        result['stage_b_authorized_files'] = sorted(stage_allowed)
        result['confirmed_subtitle_material_files'] = sorted(subtitle_hashes)
        result['unconfirmed_material_files'] = sorted(set(subtitle_materials) - subtitle_hashes.keys())
    git_dir = work.root / 'repo/.git'
    if git_dir.exists() and shutil.which('git'):
        result['git_index_checked'] = True
        # Sandbox and interactive Windows accounts can differ. Trust only this
        # already-confined repository for these commands; never change Git config.
        git_prefix = ['git', '-c', 'safe.directory=' + (work.root / 'repo').resolve().as_posix(),
                      '-C', str(work.root / 'repo')]
        proc = subprocess.run([*git_prefix,'diff','--cached','--name-only','-z'], capture_output=True, shell=False)
        if proc.returncode:
            result['issues'].append({'kind': 'git_index_query_failed'})
            result['passed'] = False
        staged = [s.decode('utf-8') for s in proc.stdout.split(b'\0') if s]
        result['staged_files'] = staged
        if staged and not (stage_b or stage_c):
            result['issues'].append({'kind': 'unexpected_staged_files_in_stage_A', 'paths': staged})
            result['passed'] = False
        elif staged:
            mode_proc = subprocess.run([*git_prefix, 'ls-files', '--stage', '-z'],
                                       capture_output=True, shell=False)
            modes = {}
            if mode_proc.returncode:
                result['issues'].append({'kind': 'git_index_mode_query_failed'})
            else:
                for entry in mode_proc.stdout.split(b'\0'):
                    if not entry:
                        continue
                    metadata, separator, raw_path = entry.partition(b'\t')
                    fields = metadata.split()
                    if separator and len(fields) == 3 and fields[2] == b'0':
                        modes[raw_path.decode('utf-8')] = fields[0]
            for rel in staged:
                if rel not in stage_allowed:
                    result['issues'].append({'kind': 'unauthorized_staged_file', 'path': rel})
                    continue
                if modes.get(rel) not in (b'100644', b'100755'):
                    result['issues'].append({'kind': 'unsafe_staged_file_mode', 'path': rel})
                    continue
                blob = subprocess.run([*git_prefix, 'show', ':' + rel],
                                      capture_output=True, shell=False)
                if blob.returncode:
                    result['issues'].append({'kind': 'git_staged_blob_query_failed', 'path': rel})
                    continue
                staged_text = blob.stdout.decode('utf-8-sig', errors='replace')
                if (secret_pattern.search(staged_text) or path_pattern.search(staged_text) or
                        any(str(work.config[k]) in staged_text for k in ('video_root','subtitle_root','work_root'))):
                    result['issues'].append({'kind': 'private_path_or_credential_in_staged_blob', 'path': rel})
                if rel in subtitle_hashes and hashlib.sha256(blob.stdout).hexdigest() != subtitle_hashes[rel]:
                    result['issues'].append({'kind': 'staged_subtitle_sha256_mismatch', 'path': rel})
    result['passed'] = not result['issues']
    work.write_json('safety_audit.json', result)
    bad_paths = {issue.get('path') for issue in result['issues']}
    candidate = [path for path in candidate if path not in bad_paths]
    work.write_json('catalog_only_file_manifest.json', {'authorization_required': True, 'files': sorted(candidate),
        'excluded_subtitle_material_files': sorted(subtitle_materials), 'excluded_unmanaged_files': sorted(unmanaged),
        'audit_passed': result['passed'], 'note': '待用户确认目录框架传播范围后按此明确白名单暂存，禁止 git add .'})
    return result
