# 本地准备与 Release 发布

全部命令在发布工作目录执行。仅依赖已有 Python 3 标准库与 GitHub CLI。视频从只读源读取，不进入 Git，不使用 LFS，不转码。

## Maintaining the existing library / 维护既有资料库

For RailDyn Atlas documentation maintenance, use the shared internationalization inputs and the existing local build/validation commands below. Follow the [maintainer architecture](architecture.md) for precise staged-file auditing, the frozen lesson-identity baseline, and GET-only Release/attachment verification with the preserved private baseline and new receipt filenames. Local rendering and metadata verification do not authorize media uploads or other remote changes.

维护 RailDyn Atlas 现有文档时，修改共用国际化输入并使用下列本地构建与验证入口。精确暂存审计、冻结课程身份基线及只读远端核验步骤见[维护架构](architecture.md)；核验使用保留的私有基线并另存新回执。原视频和字幕目录保持只读，原课程 ID、媒体映射及 tag 保留。

```powershell
python -B .\repo\scripts\publish.py build
python -B .\repo\scripts\publish.py i18n-validate
python -B .\repo\scripts\publish.py test
python -B .\repo\scripts\publish.py audit
```

The retained Stage A/B workflow below is for separately authorized media additions. Routine maintenance uses `library_verify.py` as documented above; the legacy `publish.py verify` belongs to the upload workflow. Do not rerun `scan` to reallocate existing IDs or use the old `report` command for internationalization progress: it writes Stage A/B summaries to the private progress record. Preserve that record and update the current maintenance evidence directly.

下文保留阶段 A/B 流程，供另行明确授权的新增媒体使用。日常维护采用维护架构中的 `library_verify.py`；旧 `publish.py verify` 属于上传流程。不要重新扫描并分配已有课程 ID；旧 `report` 会把私有进度记录写为 A/B 摘要，国际化续接应保留原记录并直接更新当前证据。上传权利、授权范围、同名冲突及工程识别检查继续生效。

## Retained Stage A/B workflow / 保留的阶段 A/B 流程

以下说明保留阶段 A/B 的准备与上传流程。实际执行权限以私有配置、逐项权利记录、本轮授权、真实登录身份和目标 commit 为准，本文不代替授权。仓库保持 private，不自动改为 public。

未加 `--apply` 的 upload/release 命令仍仅预演；预演不会调用 GitHub 接口，不会计算全部视频哈希，也不会产生下载链接。阶段 B 的 `verify` 会查询远端并更新核验状态，`--download` 可在需要时下载到私有临时目录比对字节。

```powershell
python .\repo\scripts\publish.py doctor
python .\repo\scripts\publish.py scan
python .\repo\scripts\publish.py build
python .\repo\scripts\publish.py plan --series all
python .\repo\scripts\publish.py upload --series 1 --limit 1
python .\repo\scripts\publish.py upload --series all
python .\repo\scripts\publish.py verify --series all
python .\repo\scripts\publish.py test
python .\repo\scripts\publish.py audit
python .\repo\scripts\publish.py report
```

`--limit 1` 表示一课的完整可用附件组。系列 5 缺字幕视频继续独立保留，缺失字幕不生成替代品。完整文件名与系列目录作匹配键，数字前缀不作主键。扫描后的新增文件只追加 ID，改名保留旧映射并报告。

单附件必须严格小于 2147483648 字节，每 Release 最多 1000 个附件；超限项阻止并单列，其余可继续。远端附件通过分页读取，SHA-256 与远端 digest 比较；同名内容不同不覆盖、不删除。无 digest 仅算元数据检查，可用 `verify --download` 下载后核对哈希。上传失败后先重查远端；有限指数退避遵循 Retry-After。仅提供文件级续跑，没有单个文件字节级断点续传。

## 阶段 B 前提

必须由用户本轮明确确认系列范围、视频/中文字幕/英文字幕分别的传播权利、仓库可见性。private 仓库也需要授权；本工具不创建仓库、不 push、不自动改 public。未确认的逐字稿和其他资料保持 unknown。

续接先读取私有进度、清单、配对与验收报告，比较源文件列表、大小和修改时间，复用稳定编号。只有源数据确实变化时才重新 scan；build 用于刷新已生成目录，不重新搭建工程。使用既有 GitHub CLI 和登录身份，先检查：

```powershell
gh --version
gh auth status --hostname github.com
gh api --help
gh api user --jq .login
```

从实际登录身份取得 OWNER，写入私有配置 `github.owner`。查询目标仓库前不要创建；鉴权或网络错误不能解释成仓库不存在：

```powershell
gh repo view OWNER/simpack-tutorial-series --json nameWithOwner,isPrivate,url
```

既有身份有效时直接复用；仅确实未登录时，由用户执行 `gh auth login --hostname github.com --web`，不要索取或打印 token。CLI 不在当前 PATH 时可使用既有可执行文件，不改全局 PATH 或全局 Git 设置。

只有从成功鉴权的实际查询明确取得不存在结果，并符合本轮授权后，才可执行 `gh repo create OWNER/simpack-tutorial-series --private`。已有同名仓库要核实属于本任务，禁止接管已有非本任务内容。使用现有 Git 身份；缺失时由用户提供项目级身份，不改全局设置。

历史阶段 A 的 `catalog_only_file_manifest.json` 仅列目录框架，不授权字幕正文。阶段 B 使用 `_local/stage_b_stage_manifest.json` 的 `files` 数组保存逐个 repo 相对路径的精确暂存白名单；先对未暂存工作树审计，再从任务拥有的目录、文档、脚本和已确认字幕建立该数组。初始化审计时可先保存 `{"files": []}`，不能因为清单尚未存在而绕过审计。

私有配置 `phase="B"` 允许检查授权暂存，其他阶段仍拒绝意外暂存。审计仅接受白名单中属于本任务的文件，以及同时满足真实字幕映射、对应语言权利 confirmed 和原件 SHA-256 的字幕副本。`approved_existing_asset_names` 再限定本轮已经确认的精确附件名；新增或未列出的素材不自动放行。手工在白名单中加入陌生文件不构成授权。

字幕默认被 Git 忽略，只按经过审查的精确路径批次执行 `git add -f -- <path>`，禁止 `git add .`。审计不仅检查工作树，还读取每个暂存 blob 和文件模式，拒绝个人绝对路径、凭据、链接模式以及字节与原件不一致的字幕。暂存前后审计通过才提交并 push。不要把备份、任务文件、配置、日志、token 或源视频带入 Git。

Release 工具还要求远端该 commit 的 `PROVENANCE.md` 含工程标识 `simpack-local-publish-v1`，防止误写其他工程。远端必须已有明确的 40 位 commit SHA；所有新 Release 指向该 SHA 并保持 draft。

## 本轮私有授权记录

由阶段 B 执行者依据用户明确指令填写 `_local/rights.json` 的所选 episode：`video`、`zh-CN`、`en` 分别改为 `confirmed`。不要批量确认未授权项。

私有 `_local/authorization.json` 示例（仅占位）：

```json
{
  "authorization_id": "USER_CONFIRMED_SESSION_ID",
  "confirmed": true,
  "rights_confirmed": true,
  "issued_at": "ISO_UTC_TIME",
  "expires_at": "ISO_UTC_EXPIRY",
  "series": ["1"],
  "materials": ["video", "zh-CN", "en"],
  "repository": "OWNER/simpack-tutorial-series",
  "visibility": "private",
  "commit_sha": "PUSHED_40_CHARACTER_COMMIT_SHA",
  "approved_existing_asset_names": [
    "s01-e001.mp4",
    "s01-e001.zh-CN.srt",
    "s01-e001.zh-CN.vtt",
    "s01-e001.en.srt",
    "s01-e001.en.vtt"
  ],
  "excluded_assets": {}
}
```

上述附件数组只演示一课，实际记录应逐一列出本轮获准的全部既有附件；缺失字幕没有附件名可上传，未确认项不能加入。新素材需要新的明确确认及清单复核，不能沿用既有课程的语言权限自动上传。

同时将 `_local/config.json` 的 `phase` 设为 `"B"`、`github.allow_remote_write` 设为 true、`github.owner` 设为实际身份、`github.commit_sha` 设为已 push 的上述 SHA。开启开关仍需匹配授权 ID、有效期、精确素材范围、权利、commit 和真实 private 可见性。保留 private，公开需要新的明确授权与完整 Git 历史/字幕/Release 审查。`--apply` 本身不是权利授权。

## 先试传，再批量与发布

下面命令只有上述本轮授权记录、权利、远端仓库和 commit 均核实后才可执行：

```powershell
python .\repo\scripts\publish.py upload --series 1 --limit 1 --apply --authorization USER_CONFIRMED_SESSION_ID
python .\repo\scripts\publish.py verify --series 1
python .\repo\scripts\publish.py upload --series all --apply --authorization USER_CONFIRMED_SESSION_ID
python .\repo\scripts\publish.py verify --series all
python .\repo\scripts\publish.py release --series all --apply --authorization USER_CONFIRMED_SESSION_ID
python .\repo\scripts\publish.py verify --series all
python .\repo\scripts\publish.py build
python .\repo\scripts\publish.py audit
python .\repo\scripts\publish.py report
```

`all` 必须完全在本轮授权范围内；若只授权部分系列，改用如 `--series 1,2`。若范围不含 1，试传本轮第一个系列。试传失败或只有元数据检查时不进入批量。

若用户明确只发布部分附件，在本轮授权记录的 `excluded_assets` 中逐项填写精确附件名与非空原因，例如 `"s01-e002.mp4": "用户确认本轮排除此视频"`。工具校验名称属于授权系列的实际清单；排除范围会改变试传门槛，并写入 Release 说明。不允许以空泛理由静默忽略失败附件。

所有获准且实际可用附件完整验证后才发布。缺字幕视频在视频本体获准时可独立上传，目录保留“字幕缺失”；不存在的字幕不能算失败上传，也不能宣称双语齐全。存在但超限、不可读、无效或失败的附件会阻止系列发布；明确只发布部分时需逐项授权排除范围和原因。发布前重新核对每个所选系列的精确附件集合和哈希，远端多出未授权附件也停止，不删除它们。

已发布或 immutable Release 不追加/替换附件，不改 tag、不删旧附件。续跑仅在远端已存在同名且哈希一致时跳过；已发布系列可重复核验和跳过发布请求，其他仍为 draft 的系列继续处理。需新版本时另行准备经确认的 v2 方案。

真实 `browser_download_url`、asset_id、release_id、名称、digest、权限可见性写入私有 upload_state。仅已验证且已发布的 API 返回链接可用于 README、系列目录和课程详情；未知和 draft 链接不生成下载按钮，private 链接明确标注仓库访问权限。发布后再次 verify/build，再按精确白名单提交和 push 目录链接更新；Release 仍指向初始授权的已 push commit，不因目录更新重写 tag。

阶段 B 的 report 从仓库范围内保存的真实附件和 Release 状态生成私有验收及续接进度；部分完成、失败与未核验项分别记数。最后一次 verify 会更新附件状态，历史上传成功/跳过数量应同时保留各次上传结果，不能只从当前状态推断整轮上传次数。最终目录 push 的核验结果另存，缺少证据不报告全部完成。

源 SHA-256 缓存明确区分实际计算与“历史哈希＋元数据未变”；发送新的附件前强制读取源字节重新计算，重跑已验证附件可复用缓存。超过一分钟的 Retry-After 会保存下次允许重试的时间并停止，不提前重试。下载验证仅将二进制写入私有文件；工具根据实际 CLI help 检查新版原始字节输出选项，不关闭 TLS 校验。

官方实现依据：[Release 附件 API](https://docs.github.com/en/rest/releases/assets)、[GitHub CLI API](https://cli.github.com/manual/gh_api)、[Release 限制](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。不将容量说明解释成永久无限网盘承诺；保留本机原件和独立备份。
