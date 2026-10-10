#!/usr/bin/env python3
"""Simpack local preparation and guarded GitHub Releases CLI (stdlib only)."""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from core import Workspace, now
import catalog_engine


def doctor(work):
    tools = {}
    for name, flag in (('python','--version'), ('git','--version'), ('gh','--version'), ('ffprobe','-version')):
        executable = sys.executable if name == 'python' else shutil.which(name)
        info = {'available': executable is not None, 'path': executable, 'version': None}
        if executable:
            try:
                response = subprocess.run([executable, flag], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=False, timeout=15)
                info['version'] = (response.stdout or response.stderr).splitlines()[0]
            except (OSError, subprocess.TimeoutExpired):
                info['available'] = False
        tools[name] = info
    result = {'checked_at': now(), 'tools': tools, 'github_owner': None,
              'auth_checked': False, 'remote_calls': 0, 'note': '此本地诊断不调用远端；gh 缺失时本地工作继续，ffprobe 缺失时视频时长未知。'}
    if 'ffprobe' not in work.config:
        work.config['ffprobe'] = tools['ffprobe']['path']
    work.write_json('config.json', work.config)
    work.write_json('doctor.json', result)
    return result


def report(work):
    if work.config.get('phase') == 'B':
        return report_stage_b(work)
    inventory = work.read_json('inventory.json')
    audit = catalog_engine.audit(work)
    checks = work.read_json('subtitle_copy_checks.json', {})
    tests = work.read_json('test_results.json', {})
    doctor_result = work.read_json('doctor.json', {})
    summary = inventory['summary'] if inventory else {}
    status = '通过' if audit['passed'] and checks.get('all_copies_sha256_equal') and tests.get('passed') else '待完成或存在失败'
    acceptance = ['# 阶段 A 验收报告', '', f'报告时间：{now()}；本地验收：{status}。', '', '## 工具单元测试', '',
                  f'运行结果：{tests.get("summary", "未执行")}；通过：{tests.get("passed", False)}。测试仅使用本地临时目录和模拟 GitHub 响应。',
                  f'原生符号链接测试跳过 {tests.get("skipped_tests", 0)} 项（Windows 创建链接权限不足）；模拟 reparse 与路径逃逸测试仍实际运行。',
                  '详见 test_results.json 与 test_results.log；模拟响应不等同于真实上传验证。', '', '## 本机真实扫描与构建', '',
                  f'- 视频 {summary.get("videos", 0)} 个；字幕 {summary.get("subtitles", 0)} 个；四种齐全 {summary.get("complete_subtitle_groups", 0)} 课。',
                  f'- 视频总字节 {summary.get("video_bytes", 0)}；最大视频：{json.dumps(summary.get("largest_video"), ensure_ascii=False)}。',
                  f'- 字幕副本实际 SHA-256 相等：{len(checks.get("files", []))}；全部相等：{checks.get("all_copies_sha256_equal", False)}。',
                  f'- 视频完整哈希：扫描未执行（0 个）；预演不读取全部视频字节。',
                  f'- 扫描及构建前后源大小/mtime 未变化：{summary.get("source_metadata_unchanged", False) and not checks.get("source_metadata_changes", [])}。',
                  f'- 已获取视频时长：{summary.get("duration_known", 0)}；未取得时长的视频不做字幕越界验收。',
                  f'- 公开目录安全扫描与相对链接检查：{audit["passed"]}；问题 {len(audit["issues"])} 个；暂存文件 {len(audit["staged_files"])} 个。',
                  '- 字幕语义、翻译质量、作者身份、硬字幕情况、技术内容：未核验。', '', '## 真实远端上传验证', '',
                  '未执行。未创建远端仓库、未 push、未上传视频或字幕、未发布 Release、未公开资料。没有真实下载链接。',
                  '远端分页、同名冲突、digest、有限重试、失败后重查和文件级续跑均由模拟测试覆盖；真实服务兼容性留待阶段 B 试传。',
                  '', '## 当前限制与下一步', '',
                  f'GitHub CLI 可用：{doctor_result.get("tools", {}).get("gh", {}).get("available", False)}；ffprobe 可用：{doctor_result.get("tools", {}).get("ffprobe", {}).get("available", False)}。',
                  '权利保持 unknown，allow_remote_write=false。阶段 B 前需要用户明确系列、分别确认视频/中文/英文字幕权利与仓库可见性。',
                  '本地复核：python .\\repo\\scripts\\publish.py doctor；scan；build；plan --series all；upload --series 1 --limit 1；verify --series all；audit。',
                  '完整命令和阶段 B 前提见 repo/docs/publishing.md。', '']
    work.write_local('acceptance_report.md', '\n'.join(acceptance))
    progress = ['# Simpack 发布进度', '', f'更新时间：{now()}。', f'阶段 A 本地验收：{status}。',
                '', '## 已完成与状态', '',
                f'- 已完整读取任务与配置，真实扫描 {summary.get("videos",0)} 视频 / {summary.get("subtitles",0)} 字幕；保留七个系列，无系列 4。',
                f'- 稳定编号保存在 id_map.json；生成 {summary.get("videos",0)} 个逐课页面及七个系列页面。',
                f'- 已复制并验证 {len(checks.get("files",[]))} 个字幕副本；视频未复制、未转码、未逐个计算 SHA-256。',
                '- 系列 5 的 0-课程效果.mp4 保留独立课程；四类字幕缺失。数字前缀冲突保留完整路径独立编号。',
                f'- 测试：{tests.get("summary","未执行")}；安全审计：{audit["passed"]}。',
                '- 上传工具提供 doctor/scan/build/plan/upload/verify/report/audit/test/release 接口，默认预演；状态以原子写入方式保存。',
                '- 远端操作未执行，无真实下载链接。权利 unknown；GitHub OWNER 未取得；不把 Windows 用户名当成 OWNER。',
                '', '## 续接规则', '',
                '先读 AGENTS.md、simpack_codex_v1.md、本文件、acceptance_report.md、rights.json、config.json 和 upload_state.json；不要重建或重编号。',
                '再次 scan/build 会备份变更的已生成文件。确认源数据未变后使用已生成工具继续。',
                '阶段 B 必须先取得本轮明确系列/素材权利/可见性授权；准备私有 authorization.json 并单独开启远端开关。',
                '当前 gh 缺失；由用户安装或提供现有 CLI 后运行 doctor 与 gh auth login --hostname github.com --web。',
                '必须先经审查按白名单提交并 push 到明确 commit，再试传一课完整附件组；试传验证通过后允许同一授权范围的批量上传。',
                'docs/publishing.md 提供配置结构、真实阶段 B 命令和冲突/immutable 的处理方式。', '']
    work.write_local('PROGRESS.md', '\n'.join(progress))
    return {'local_acceptance': status, 'summary': summary, 'audit_passed': audit['passed'], 'remote_upload': 'not_executed'}


def report_stage_b(work):
    """Summarize saved actual evidence without inventing remote completion."""
    inventory = work.read_json('inventory.json', {})
    summary = inventory.get('summary', {})
    audit = catalog_engine.audit(work)
    copies = work.read_json('subtitle_copy_checks.json', {})
    tests = work.read_json('test_results.json', {})
    rights = work.read_json('rights.json', {})
    authorization = work.read_json('authorization.json', {})
    state = work.read_json('upload_state.json', {})
    status_record = work.read_json('stage_b_status.json', {})
    selected = authorization.get('series') or list(catalog_engine.SERIES)
    materials = authorization.get('materials') or ['video', 'zh-CN', 'en']
    exclusions = authorization.get('excluded_assets', {})
    repository = state.get('repository')
    expected, blocked, missing, unconfirmed = {}, [], [], []
    for ep in inventory.get('episodes', []):
        if ep['series_id'] not in selected:
            continue
        for suffix, item in [('', ep.get('video', {})), *ep.get('subtitles', {}).items()]:
            material = 'video' if not suffix else 'zh-CN' if suffix.startswith('.zh-CN') else 'en'
            if material not in materials:
                continue
            name = item.get('asset_name')
            if item.get('status') == 'missing':
                missing.append(name)
                continue
            if name in exclusions:
                continue
            confirmed = rights.get('episodes', {}).get(ep['episode_id'], {}).get(material, rights.get('default', 'unknown')) == 'confirmed'
            if not confirmed:
                unconfirmed.append(name)
                continue
            size = item.get('size_bytes') or 0
            if not 0 < size < catalog_engine.MAX_BYTES or item.get('status') in ('invalid','unreadable','zero_byte','blocked_reparse'):
                blocked.append({'asset_name': name, 'reason': 'blocked_oversize' if size >= catalog_engine.MAX_BYTES else item.get('status')})
                continue
            expected[name] = {'series_id': ep['series_id'], 'material': material}
    records = {name: state.get('assets', {}).get(f'{repository}/{name}', {}) if repository else {} for name in expected}
    verified_names = {name for name, record in records.items() if
                      record.get('status') in ('verified','uploaded_verified','skipped_verified') and
                      record.get('verification') in ('verified','download_verified')}
    failed_names = {name for name, record in records.items() if record.get('status') in
                    ('failed','conflict','deferred_retry_after','source_changed_after_upload','source_changed_during_verification')}
    # Verification rewrites current statuses to "verified". Upload/skip history
    # therefore comes from saved actual operation receipts, not current state.
    uploaded_names, skipped_names = set(), set()
    operation_receipts = []
    receipt_repository = repository or authorization.get('repository')
    failure_statuses = {'failed', 'conflict', 'deferred_retry_after', 'source_changed_after_upload', 'source_changed_during_verification'}
    for receipt_file, operation in (('upload_trial_result.json', 'trial'), ('upload_batch_result.json', 'batch')):
        receipt = work.read_json(receipt_file, {})
        valid = (isinstance(receipt, dict) and receipt.get('mode') == 'apply' and
                 receipt.get('remote_called') is True and isinstance(receipt.get('assets'), list))
        if valid and 'repository' in receipt and receipt['repository'] != receipt_repository:
            valid = False
        uploaded, skipped, failed, unbound_failed = set(), set(), set(), set()
        if valid:
            for item in receipt['assets']:
                if not isinstance(item, dict) or item.get('asset_name') not in expected:
                    continue
                # Older receipt schemas have no top-level repository field;
                # their actual API-returned URL still binds each successful row.
                url = item.get('browser_download_url')
                name, status = item['asset_name'], item.get('status')
                scoped_url = (bool(receipt_repository) and isinstance(url, str) and
                              url.startswith(f'https://github.com/{receipt_repository}/releases/'))
                if status in failure_statuses:
                    failure_bound = (scoped_url or receipt.get('repository') == receipt_repository and bool(receipt_repository) or
                                     bool(authorization.get('authorization_id')) and
                                     receipt.get('authorization_id') == authorization['authorization_id'] or
                                     bool(repository) and records[name].get('status') in failure_statuses)
                    (failed if failure_bound else unbound_failed).add(name)
                if scoped_url and item.get('verification') in ('verified', 'download_verified'):
                    if status == 'uploaded_verified':
                        uploaded.add(name)
                    elif status == 'skipped_verified':
                        skipped.add(name)
        uploaded_names.update(uploaded)
        skipped_names.update(skipped)
        operation_receipts.append({'operation': operation, 'source_file': receipt_file, 'available': valid,
                                   'completed_at': receipt.get('completed_at') if valid else None,
                                   'uploaded_verified': len(uploaded), 'skipped_verified': len(skipped),
                                   'failed': len(failed), 'unbound_failed': len(unbound_failed),
                                   'unique_processed': len(uploaded | skipped | failed)})
    counts = {'authorized_available': len(expected), 'verified': len(verified_names),
              'uploaded_verified': len(uploaded_names), 'skipped_verified': len(skipped_names),
              'upload_receipt_unique': len(uploaded_names | skipped_names),
              'failed': len(failed_names), 'pending': len(expected.keys() - verified_names - failed_names),
              'blocked_oversize': sum(item['reason'] == 'blocked_oversize' for item in blocked),
              'blocked_other': sum(item['reason'] != 'blocked_oversize' for item in blocked),
              'missing_subtitle_files': len(missing), 'explicitly_excluded': len(exclusions),
              'unconfirmed_excluded': len(unconfirmed)}
    release_rows = []
    for sid in selected:
        record, url = catalog_engine._release_record(state, sid)
        release_rows.append({'series_id': sid, 'url': url, 'draft': record.get('draft'),
                             'recorded_url': record.get('html_url'),
                             'verified': sum(name in verified_names for name, data in expected.items() if data['series_id'] == sid),
                             'expected': sum(data['series_id'] == sid for data in expected.values())})
    published = sum(bool(row['url']) for row in release_rows)
    complete = (bool(expected) and counts['verified'] == len(expected) and not failed_names and not blocked and
                published == len(selected) and status_record.get('catalog_push_verified') is True and audit['passed'] and
                copies.get('all_copies_sha256_equal') is True and tests.get('passed') is True)
    pending_reason = status_record.get('pending_reason') or (
        '尚未保存全部附件、Release 与最终目录推送的完整核验记录。' if not complete else '所选附件、Release 与目录推送均有完成记录。')
    repo_url = status_record.get('repository_url')
    heading = '完成' if complete else '部分完成或待执行'
    lines = ['# 阶段 B 验收与续接记录', '', f'更新时间：{now()}；阶段 B：{heading}。',
             f'所选系列：{", ".join(selected)}；授权素材：{", ".join(materials)}；要求可见性：{authorization.get("visibility", "private")}。',
             '视频、字幕以逐项私有权利记录为准；未确认素材、逐字稿与其他资料不自动放行。', '',
             f'实际仓库地址：{repo_url or "尚未获得核验记录"}。',
             '远端一致性验证总量取最新 upload_state；实际上传与续跑跳过取试传及批量的真实操作回执。本报告本身不执行新的远端查询。',
             '同一附件可能试传上传后在批量中跳过，上传与跳过计数不可相加作为总附件数；回执去重总量按精确附件名取并集。',
             '', '| 指标 | 数量 |', '|---|---:|']
    labels = {'authorized_available':'已确认且可上传附件', 'verified':'最新远端记录已校验一致附件',
              'uploaded_verified':'操作回执记录上传且一致（独立附件）', 'skipped_verified':'操作回执记录跳过且一致（独立附件）',
              'upload_receipt_unique':'上传/跳过操作回执去重附件总量',
              'failed':'失败/冲突/延期附件', 'pending':'尚未保存一致性验证附件', 'blocked_oversize':'超限附件',
              'blocked_other':'其他阻止附件', 'missing_subtitle_files':'缺失字幕文件', 'explicitly_excluded':'明确排除附件',
              'unconfirmed_excluded':'权利未确认而排除附件'}
    lines.extend(f'| {labels[key]} | {value} |' for key, value in counts.items())
    lines += ['', '| 操作回执 | 上传且一致 | 跳过且一致 | 失败记录 | 操作内去重附件 |', '|---|---:|---:|---:|---:|']
    for item in operation_receipts:
        label = ('试传' if item['operation'] == 'trial' else '批量') + ('（未保存有效实际回执）' if not item['available'] else '')
        failed_label = str(item['failed']) + (f'（另 {item["unbound_failed"]} 项归属无法确认）' if item['unbound_failed'] else '')
        lines.append(f'| {label} | {item["uploaded_verified"]} | {item["skipped_verified"]} | {failed_label} | {item["unique_processed"]} |')
    lines += ['', '未保存有效操作回执时，对应历史次数未知；表中的 0 仅表示没有已保存回执记录，不代表从未执行上传或跳过。']
    lines += ['失败回执行没有下载链接时，使用匹配仓库字段、授权 ID 或当前仓库同名失败状态确认归属；无法确认的失败行单列，不冒充没有失败。']
    lines += ['', '| 系列 | 一致性验证附件 | Release 状态与实际地址 |', '|---|---:|---|']
    for row in release_rows:
        release_status = (f'已发布：{row["url"]}' if row['url'] else
                          f'草稿：{row["recorded_url"] or "地址尚未记录"}' if row['draft'] is True else '尚未获得发布核验记录')
        lines.append(f'| {row["series_id"]} | {row["verified"]}/{row["expected"]} | {release_status} |')
    if failed_names or blocked:
        lines += ['', '失败、冲突或阻止附件：', '']
        for name in sorted(failed_names):
            record = records[name]
            lines.append(f'- {name}：{record.get("status")}；{record.get("error") or "等待再次逐文件核验"}。')
        lines.extend(f'- {item["asset_name"]}：{item["reason"]}。' for item in blocked)
    lines += ['', f'当前状态/待完成原因：{pending_reason}',
              f'最终目录 push 已核验：{status_record.get("catalog_push_verified") is True}。',
              '', f'本地安全审计：{audit["passed"]}；字幕副本 SHA-256 全部相等：{copies.get("all_copies_sha256_equal", False)}。',
              f'工具测试：{tests.get("summary", "未执行")}；通过：{tests.get("passed", False)}。模拟测试不代表真实远端完成。',
              '扫描/构建中的视频哈希计数与上传前哈希记录分别保存；本报告不会把元数据未变写成视频全量哈希已完成。',
              '缺字幕文件不造假；系列 5 的 0-课程效果.mp4 保留独立课程。仓库保持 private，不自动公开。',
              '', '续接先读本文件、任务文件、rights.json、config.json、authorization.json、upload_state.json 与 stage_b_status.json；复用现有编号和脚本。',
              '先确认源数据未变和 gh 真实身份、目标仓库；试传一课完整附件组校验通过后再批量上传。已有一致附件跳过，同名冲突停止。',
              '使用本轮 authorization_id 与已 push 的明确 commit；完整命令见 repo/docs/publishing.md。', '']
    work.write_local('acceptance_report.md', '\n'.join(lines))
    work.write_local('PROGRESS.md', '\n'.join(lines))
    result = {'phase': 'B', 'complete': complete, 'repository_url': repo_url, 'counts': counts,
              'operation_receipts': operation_receipts,
              'releases': release_rows, 'audit_passed': audit['passed'], 'pending_reason': pending_reason}
    work.write_json('stage_b_report.json', result)
    return result


def run_tests(work):
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'repo/tests', '-v'],
                            cwd=work.root, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, shell=False)
    output = result.stdout + result.stderr
    work.write_local('test_results.log', output)
    summary_lines = [line for line in output.splitlines() if line.startswith(('Ran ', 'OK', 'FAILED'))]
    ran = re.search(r'Ran (\d+) tests?', output)
    skipped = re.search(r'skipped=(\d+)', output)
    result_data = {'run_at': now(), 'passed': result.returncode == 0, 'exit_code': result.returncode,
                   'summary': ' / '.join(summary_lines), 'total_tests': int(ran.group(1)) if ran else 0,
                   'skipped_tests': int(skipped.group(1)) if skipped else 0, 'real_remote_upload': False}
    work.write_json('test_results.json', result_data)
    return result_data


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description='本地目录生成与受授权保护的 GitHub Release 发布')
    parser.add_argument('--work-root', type=Path, default=Path(__file__).resolve().parents[2])
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('doctor','scan','build','report','audit','test','i18n-build','i18n-validate'):
        sub.add_parser(command)
    for command in ('plan','upload','verify','release'):
        part = sub.add_parser(command)
        part.add_argument('--series', default='all')
        if command in ('upload','release'):
            part.add_argument('--apply', action='store_true')
            part.add_argument('--authorization', help='本轮 authorization.json 的明确授权 ID')
        if command == 'upload':
            part.add_argument('--limit', type=int, help='完整课程附件组数量')
        if command == 'verify':
            part.add_argument('--download', action='store_true', help='远端已配置时下载所选附件并核对 SHA-256')
    args = parser.parse_args()
    try:
        work = Workspace(args.work_root)
        logging.basicConfig(filename=work.local('publish.log'), level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
        logging.info('command=%s', args.command)
        if args.command == 'doctor':
            result = doctor(work)
        elif args.command == 'scan':
            result = catalog_engine.scan(work)['summary']
        elif args.command == 'build':
            result = catalog_engine.build(work)
        elif args.command in ('i18n-build', 'i18n-validate'):
            import i18n_engine
            result = i18n_engine.render(work) if args.command == 'i18n-build' else i18n_engine.validate(work)
        elif args.command == 'plan':
            full = catalog_engine.plan(work, args.series)
            result = {'mode': full['mode'], 'remote_calls': 0,
                      'releases': [{k:v for k,v in item.items() if k != 'lessons'} for item in full['releases']]}
        elif args.command in ('upload','verify','release'):
            import github_release
            if args.command == 'upload':
                result = github_release.upload(work, args.series, args.limit, args.apply, args.authorization)
                if not args.apply:
                    work.write_json('upload_trial_preview.json' if args.limit == 1 else 'upload_batch_preview.json', result)
                if not args.apply and len(result.get('assets', [])) > 10:
                    result = {key:value for key,value in result.items() if key != 'assets'} | {'preview_file': '_local/upload_preview.json'}
            elif args.command == 'verify':
                result = github_release.verify(work, args.series, args.download)
            else:
                result = github_release.release(work, args.series, args.apply, args.authorization)
        elif args.command == 'audit':
            result = catalog_engine.audit(work)
            result = {'passed':result['passed'], 'issues':result['issues'], 'candidate_files':len(result['candidate_files']),
                      'unconfirmed_material_files':len(result['unconfirmed_material_files']), 'staged_files':result['staged_files']}
        elif args.command == 'test':
            result = run_tests(work)
        else:
            result = report(work)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command in ('test', 'audit', 'i18n-validate') and not result['passed']:
            return 1
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
        # No CLI subprocess stderr is printed here: API failures can contain credentials.
        message = str(exc) if not isinstance(exc, OSError) else type(exc).__name__
        print(f'操作停止：{message}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
