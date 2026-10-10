# Maintainer architecture / 维护架构

[English](#english) · [简体中文](#简体中文) · [Project](../../README.md) · [项目首页](../../README.zh-CN.md)

## English

### Target and data

The sole target is `D-Simpackuser/simpack-tutorial-series`, numeric repository ID `1412669436`. A matching name alone is insufficient target evidence. The stable marker `simpack-local-publish-v1` remains in [PROVENANCE](../../PROVENANCE.md) for existing upload checks and old commit/tag compatibility. Do not remove or bypass those checks when rearranging reader documentation.

- [catalog.json](../../catalog.json) retains its `schema_version` and `episodes` interface. `episode_id` is the stable lesson identity; `series_id` plus the exact `original_relative_path` binds a reference title to the existing lesson. Original filenames, attachment names, subtitle paths, SHA-256 values and media URLs retain their meaning. Numeric filename prefixes and translated-title sorting cannot allocate or merge IDs.
- [series.json](../../series.json) retains IDs `1`, `2`, `3`, `5`, `6`, `7`, `8` and their existing tags. Formal Chinese display names use the exact supplied text. There is no Series 4.
- [i18n/series.json](../../i18n/series.json) and `i18n/lessons/<locale>.json` hold editorial display text for `en`, `zh-CN`, `ja`, `fr`, `de`, `it`, `es`, `ko`. Each localized lesson uses the existing ID, source-title hash and review status. The [glossary](../../i18n/glossary.json) is editorial guidance.
- [i18n/project.json](../../i18n/project.json) is the RailDyn Atlas brand source for all eight project introductions. Change this input and the introduction text before rebuilding; editing generated README headings alone will not persist.
- Root and series pages render from these inputs: English uses `README.md`, others `README.<locale>.md`. Existing `lessons/<episode_id>.md` paths remain bilingual EN / 中文. Counts come from the real lesson/subtitle collections; unknown durations stay `null`.

### Local build and audit

Run from the release workspace, whose `repo/` subdirectory is the Git worktree:

```powershell
python -B .\repo\scripts\publish.py build
python -B .\repo\scripts\publish.py test
python -B .\repo\scripts\publish.py audit
```

Build renders local files without uploading, editing Releases or changing visibility. Two builds with unchanged inputs must produce identical bytes. The legacy build entry must use the internationalization inputs when present rather than restore default names or overwrite multilingual pages. The former one-time catalogue finalizer must not act as a competing source of display names.

Private source roots, ID mappings, rights, upload authorization, receipts, backups and audit evidence stay outside the Git worktree. Public JSON and documents use output field whitelists; never copy a private inventory or task package wholesale. Source directories remain read-only. MP4 files never enter Git or LFS. Preserve `.gitattributes` rules for subtitle bytes.

Audit a precise file whitelist before staging, then inspect staged blobs and file modes. Stage only reviewed paths; do not use `git add .`. A documentation PR does not authorize new media or history rewrites. Keep the existing Git identity and normal commits/pushes, without moving media tags or force-pushing.

### Read-only remote verification

`scripts/library_verify.py` compares the fixed repository identity, observed visibility, existing Releases/tags and paginated attachment metadata with an explicit local baseline. It also checks the local catalogue's stable mappings and links. It supports private or public observed repositories without requiring phase-B upload authorization or relaxing upload write gates. Metadata GET requests do not upload, edit, delete, change visibility or download video bytes.

Lesson identity is independently anchored to the verified phase-B `catalog.json` blob in frozen main commit `15726d0bbcdc3978ae064ee66e917cfe68390cdb`. The verifier checks that blob against its fixed SHA-256 before comparing all 194 lessons' series ID, episode ID, original relative path, original filename and original title. The current catalogue and a replacement attachment baseline cannot redefine this identity. Display translations and project branding are separate inputs.

The frozen Git object must be available locally. A missing object or digest mismatch stops verification before remote requests; verification never fetches it automatically. Use the existing project checkout with its retained history. A future course addition requires a separately reviewed identity-baseline update, alongside the usual rights and upload controls.

```powershell
python -B .\repo\scripts\library_verify.py --help
$verificationStamp = Get-Date -Format "yyyyMMdd_HHmmss_fffffff"
python -B .\repo\scripts\library_verify.py --baseline .\_local\stage_c\baseline.json --catalog .\repo\catalog.json --gh gh --output ".\_local\stage_c\remote_verification_$verificationStamp.json" --observation ".\_local\stage_c\visibility_observation_$verificationStamp.json"
```

The explicitly selected output/observation files are private records and must not be staged. Their paths must be under `_local/` and use new filenames: the verifier refuses to overwrite an existing receipt. The timestamped example preserves previous runs. If `gh` is absent from the process PATH, pass the existing executable through `--gh` without global configuration changes. Distinguish authentication, permission and network errors; none authorizes creating another repository. Metadata agreement is not a new complete video download/hash check, full video privacy review or anonymous public-access check. Refresh page access notices only from actual visibility evidence; a future public change requires separately confirmed distribution scope and review.

### Applying an observed access state

The timestamped `--observation` file is a receipt. The renderer reads only the private canonical file `_local/stage_c/repository_observation.json`; running the verifier alone does not refresh a page banner.

1. Review a successful verification receipt and its corresponding observation. Confirm `remote_read_only: true`, the exact repository and numeric ID, the real `visibility`, and a timezone-aware UTC `observed_at`. Do not replace these fields with an intended future state.
2. Promote that reviewed observation with the existing `Workspace.write_json` method. It backs up the previous canonical file before replacing it; preserve the timestamped receipt.
3. Run local build and audit. Historical phase-B rights and authorization remain unchanged.

From the same release-workspace PowerShell session used above, after that review:

```powershell
python -B -c "import json,sys; from pathlib import Path; sys.path.insert(0,str(Path('repo/scripts').resolve())); from core import Workspace; w=Workspace(Path('.')); observation=json.loads(w.local(sys.argv[1]).read_text(encoding='utf-8')); w.write_json('stage_c/repository_observation.json',observation)" "stage_c/visibility_observation_$verificationStamp.json"
python -B .\repo\scripts\publish.py build
python -B .\repo\scripts\publish.py audit
```

These local record and rendering steps do not modify GitHub visibility or grant public distribution rights.

### Additions and remote changes

This documentation update adds no courses or media. A future addition needs explicit scope, rights for video and each subtitle language, exact source matching, metadata-change checks and reviewed incremental ID allocation. Existing IDs remain stable. The [retained publishing workflow](publishing.md) covers trial upload, per-file retries, same-name conflict protection, limits and verification. An expired or private-only authorization cannot become public permission; do not invent a new private configuration phase to bypass write gates.

Prepared Release text is separate from rendering and the upload engine. A future explicitly authorized text plan changes only name/body, without moving tags, changing targets or rebuilding attachments; document links use the actual default branch. Creating a documentation PR does not authorize merging it, editing live Releases, making the repository public or deploying Pages.

## 简体中文

### 目标与数据

唯一目标为 `D-Simpackuser/simpack-tutorial-series`，数值仓库 ID `1412669436`；仅同名不能证明属于本工程。[PROVENANCE](../../PROVENANCE.md) 中的 `simpack-local-publish-v1` 保留用于已有上传检查及旧 commit、tag 兼容，整理文档不能删除或绕过。

- [catalog.json](../../catalog.json) 保留原 `schema_version`、`episodes` 接口。`episode_id` 是稳定身份；`series_id` 与完整 `original_relative_path` 严格连接参考题名和原课目。原文件名、附件名、字幕路径、SHA-256 和媒体 URL 保持原义，不能按数字前缀合并或按译名排序重新编号。
- [series.json](../../series.json) 保留七个 ID `1`、`2`、`3`、`5`、`6`、`7`、`8` 和原 tag，正式中文显示名逐字采用给定文本，不补系列 4。
- [i18n/series.json](../../i18n/series.json)、`i18n/lessons/<locale>.json` 保存八语编辑显示文字；译名按原 ID 保存原题哈希和审校状态。[术语表](../../i18n/glossary.json)只是编辑参考。
- [i18n/project.json](../../i18n/project.json) 是八语项目介绍共用的 RailDyn Atlas 品牌源。先修改该输入及介绍正文，再构建；仅改生成的 README 标题不会保留。
- 根 README、系列页由这些输入生成。英文为 `README.md`，其他语言为 `README.<locale>.md`；原详情路径 `lessons/<episode_id>.md` 为 EN / 中文。统计取真实课程、字幕集合，未知时长保留 `null`。

### 本地构建与审计

在发布工作目录执行上文 `publish.py build`、`test`、`audit`，`repo/` 为 Git 工作树。build 仅渲染本地文件，不上传、不改 Release 或可见性。相同输入连续构建应字节一致；存在国际化输入时，旧入口必须采用它们，不能恢复默认系列名或覆盖多语页面。旧一次性目录 finalizer 不作为第二套显示名来源。

源根、ID 映射、权利、授权、回执、备份和审计证据保存在 Git 工作树外。公共文件使用字段白名单，不整体复制私有清单或任务包。源目录只读，MP4 不进入 Git、LFS，保留 `.gitattributes` 字幕字节规则。暂存前审计精确文件白名单，暂存后核对 blob 和模式，仅加入已审查路径，不使用 `git add .`。保留原 Git 身份、正常提交和推送，不移动媒体 tag、不强推；文档 PR 不授权新媒体和改写历史。

### 只读远端核验

`scripts/library_verify.py` 按显式本地基线核对固定仓库身份、实际可见性、Release、tag、分页附件元数据，以及本地目录稳定映射和链接。它支持当前观察到的 private/public 仓库，不要求阶段 B 上传授权、不放宽写入门槛；仅 GET 元数据，不上传、编辑、删除、改可见性或下载视频字节。

课程身份独立绑定到已验证的阶段 B 原始 `catalog.json`，取自冻结的 main 提交 `15726d0bbcdc3978ae064ee66e917cfe68390cdb`。核验器先用固定 SHA-256 校验该 Git blob，再逐课比较 194 节课的系列 ID、课程 ID、原始相对路径、原文件名和原始标题。当前目录及可替换的附件基线不能重定义这些身份；显示译名和项目品牌由独立输入维护。

本地必须保留该冻结 Git 对象。对象缺失或摘要不符时，在远端请求前停止，不自动 fetch。使用保留历史的现有工程 checkout；未来增加课程需要单独审查身份基线更新，并继续执行权利和上传控制。

上文命令将 `--output`、`--observation` 写到私有区域，不提交这些文件。输出路径必须在 `_local/` 内且使用新文件名，核验器拒绝覆盖已有回执；示例时间戳保留每次记录。`gh` 不在进程 PATH 时，通过 `--gh` 指定已有 CLI，不改全局配置。鉴权、权限、网络错误应区分，不能触发另建仓库。元数据一致不等于视频重新完整下载验哈希、完整内容隐私审查或匿名公开访问通过。页面权限提示仅依据实际可见性刷新；未来公开需单独确认公共传播范围和审查。

### 将实际观察接入页面

带时间戳的 `--observation` 文件只是回执；渲染器仅读取私有规范入口 `_local/stage_c/repository_observation.json`。单独执行核验器不会自动刷新页面提示。

1. 审阅通过的核验回执及对应观察，确认 `remote_read_only: true`、精确仓库名与数值 ID、真实 `visibility` 以及带 UTC 时区的 `observed_at`。不得将字段改成希望将来达到的状态。
2. 通过已有 `Workspace.write_json` 更新规范入口，改写前自动备份原文件，保留带时间戳回执。上文命令从相同发布工作目录及 PowerShell 会话读取该次观察。
3. 执行本地 build、audit；不修改阶段 B 历史权利及授权。

这些步骤只更新本地观察和渲染，不改变 GitHub 可见性，也不授予公开传播权利。

### 新增与远端修改

本轮不新增课程或媒体。后续新增需明确范围，分别确认视频和各字幕语言权利，严格匹配源文件、比较元数据变化及审查增量 ID 分配；原 ID 保持。[原发布流程](publishing.md)保留试传、逐文件有限重试、同名冲突保护、限制和验证。过期、private-only 授权不能改为 public 权限，不能在原私有配置中虚构新阶段绕过门槛。

待应用 Release 文字与页面生成、上传引擎分离。未来明确授权后只改 name/body，不移动 tag、改目标 commit 或重建附件，文档链接采用真实默认分支。创建文档 PR 不授权自动合并、编辑线上 Release、公开仓库或部署 Pages。
