"""Read-only source access, confined writes and small standard-library helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SERIES = ('1', '2', '3', '5', '6', '7', '8')
SUFFIXES = ('.zh-CN.srt', '.zh-CN.vtt', '.en.srt', '.en.vtt')
MAX_BYTES = 2147483648
MAX_ASSETS = 1000


def now():
    return datetime.now(timezone.utc).isoformat()


def is_link(path):
    info = Path(path).lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def confined(root, relative):
    root = Path(root).absolute()
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('Unsafe relative path')
    candidate = root / rel
    for item in (root, *candidate.parents):
        if item == root or root in item.parents:
            if item.exists() and is_link(item):
                raise ValueError('Link/reparse point in path')
    if candidate.exists() and is_link(candidate):
        raise ValueError('Link/reparse point target')
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escaped root')
    return candidate


def safe_source(root, relative):
    path = confined(root, relative)
    if not path.is_file():
        raise ValueError('Source is not a regular file')
    return path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def natural_key(value):
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r'(\d+)', str(value)))


def asset_allowed(size):
    return 0 < size < MAX_BYTES


def select_series(value):
    selected = list(SERIES) if value == 'all' else value.split(',')
    if not selected or any(x not in SERIES for x in selected) or len(set(selected)) != len(selected):
        raise ValueError('Series must be all or a subset of 1,2,3,5,6,7,8')
    return selected


class Workspace:
    def __init__(self, root, config=None):
        self.root = Path(root).absolute()
        if not self.root.is_dir() or is_link(self.root):
            raise ValueError('Work root must be an existing real directory')
        if config is None:
            current = self.root / '_local/config.json'
            draft = self.root / 'simpack_config_v1.json'
            selected = current if current.exists() else draft
            config = json.loads(selected.read_text(encoding='utf-8-sig'))
        self.config = config
        if Path(config['work_root']).resolve() != self.root.resolve():
            raise ValueError('Configuration work_root differs from active work directory')
        for key in ('video_root', 'subtitle_root'):
            source = Path(config[key]).absolute()
            if not source.is_dir() or is_link(source):
                raise ValueError(f'{key} must be an existing real directory')
            if self.root.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(self.root.resolve()):
                raise ValueError('Source and writable work trees must not overlap')
        video = Path(config['video_root']).resolve()
        sub = Path(config['subtitle_root']).resolve()
        if video.is_relative_to(sub) or sub.is_relative_to(video):
            raise ValueError('Source roots must not overlap')
        for name in ('repo', '_local', 'staging'):
            path = confined(self.root, name)
            path.mkdir(exist_ok=True)
        manifest = self.local('managed_files.json')
        self.managed = set(json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else [])

    def local(self, relative):
        return confined(self.root, Path('_local') / relative)

    def repo(self, relative):
        return confined(self.root, Path('repo') / relative)

    def read_json(self, relative, default=None):
        path = self.local(relative)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

    def _atomic(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.simpack-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def write(self, relative, data):
        path = confined(self.root, relative)
        key = path.relative_to(self.root).as_posix()
        payload = data.encode('utf-8') if isinstance(data, str) else data
        if path.exists():
            previous = path.read_bytes()
            if previous == payload:
                return path
            if key not in self.managed:
                raise ValueError(f'Refusing to overwrite unmanaged file: {key}')
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = self.local(Path('backups') / stamp / key)
            self._atomic(backup, previous)
        self._atomic(path, payload)
        self.managed.add(key)
        self._atomic(self.local('managed_files.json'), json.dumps(sorted(self.managed), ensure_ascii=False, indent=2).encode('utf-8'))
        return path

    def write_json(self, relative, obj):
        return self.write(Path('_local') / relative, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

    def write_local(self, relative, text):
        return self.write(Path('_local') / relative, text)

    def write_repo(self, relative, text):
        return self.write(Path('repo') / relative, text)


def walk_source(root):
    """Do not traverse links, even when their target is inside the source."""
    root = Path(root).absolute()
    files, issues = [], []

    def visit(directory):
        try:
            entries = sorted(os.scandir(directory), key=lambda item: natural_key(item.name))
        except OSError as exc:
            issues.append({'kind': 'unreadable_directory', 'relative_path': directory.relative_to(root).as_posix(), 'error': type(exc).__name__})
            return
        for entry in entries:
            path = Path(entry.path)
            rel = path.relative_to(root).as_posix()
            try:
                if is_link(path):
                    issues.append({'kind': 'skipped_reparse_point', 'relative_path': rel})
                elif entry.is_dir(follow_symlinks=False):
                    visit(path)
                elif entry.is_file(follow_symlinks=False):
                    info = entry.stat(follow_symlinks=False)
                    files.append({'relative_path': rel, 'size_bytes': info.st_size, 'mtime_ns': info.st_mtime_ns})
                else:
                    issues.append({'kind': 'non_regular_file', 'relative_path': rel})
            except OSError as exc:
                issues.append({'kind': 'unreadable_file', 'relative_path': rel, 'error': type(exc).__name__})
    visit(root)
    return files, issues


TIMESTAMP = re.compile(r'(?:(\d{2,}):)?(\d{2}):(\d{2})[,.](\d{3})')


def timestamp(value):
    match = TIMESTAMP.fullmatch(value)
    if not match:
        raise ValueError('Invalid timestamp')
    hour, minute, second, milli = match.groups()
    if int(minute) >= 60 or int(second) >= 60:
        raise ValueError('Timestamp component out of range')
    return int(hour or 0) * 3600 + int(minute) * 60 + int(second) + int(milli) / 1000


def validate_subtitle(path, duration=None):
    result = {'valid': False, 'encoding': None, 'cue_count': 0, 'issues': [], 'overlap_count': 0,
              'bounds_checked': duration is not None, 'semantic_checked': False}
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        result['issues'].append(type(exc).__name__)
        return result
    if not raw:
        result['issues'].append('zero_byte')
        return result
    encodings = ['utf-16'] if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else ['utf-8-sig', 'gb18030']
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            result['encoding'] = encoding
            break
        except UnicodeDecodeError:
            pass
    else:
        result['issues'].append('decode_error')
        return result
    lines = text.replace('\r\n', '\n').replace('\r', '\n')
    vtt = Path(path).suffix.lower() == '.vtt'
    if vtt and not re.match(r'^WEBVTT(?:[ \t].*)?(?:\n|$)', lines):
        result['issues'].append('missing_WEBVTT_header')
    previous_start, previous_end = -1, -1
    for block in re.split(r'\n[ \t]*\n', lines.strip()):
        rows = block.splitlines()
        if vtt and rows and (rows[0].startswith('WEBVTT') or rows[0].startswith(('NOTE', 'STYLE', 'REGION'))):
            continue
        positions = [i for i, line in enumerate(rows) if '-->' in line]
        if len(positions) != 1:
            result['issues'].append('missing_or_multiple_cue_timing')
            continue
        index = positions[0]
        if (not vtt and (index != 1 or not rows[0].isdigit())) or index > 1 or index + 1 >= len(rows):
            result['issues'].append('invalid_cue_structure')
        try:
            left, right = rows[index].split('-->')
            start, end = timestamp(left.strip()), timestamp(right.strip().split()[0])
            if end <= start:
                result['issues'].append('non_positive_cue_duration')
            if start < previous_start:
                result['issues'].append('out_of_order_cue')
            if start < previous_end:
                result['overlap_count'] += 1
            if duration is not None and end > duration + 0.05:
                result['issues'].append('cue_beyond_video_duration')
            previous_start, previous_end = start, max(previous_end, end)
            result['cue_count'] += 1
        except (ValueError, IndexError):
            result['issues'].append('invalid_timestamp')
    if not result['cue_count']:
        result['issues'].append('no_cues')
    result['issues'] = sorted(set(result['issues']))
    result['valid'] = not result['issues']
    return result
