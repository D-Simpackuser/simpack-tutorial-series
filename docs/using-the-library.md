# Using the library / 下载与使用

[English](#english) · [简体中文](#简体中文) · [Project](../README.md) · [项目首页](../README.zh-CN.md)

## English

### What you can access

The repository is public, confirmed on 12 October 2026. Its README, lesson catalogue, subtitles and existing published Release pages can be read without repository membership. Use the original lesson links for downloads. Public access does not itself grant a media reuse licence.

The existing features are Markdown course catalogues, bilingual lesson details, Release download links and Chinese/English subtitle files. There is no embedded video player, dedicated search interface or automatic learning-progress tracker. The learning routes help you choose a starting point; watching still uses your local player.

### Shortest viewing workflow

1. Choose [Simpack basics](learning-paths.md#simpack-basics), [Abaqus flexible track](learning-paths.md#abaqus-flexible-track) or [stress recovery and fatigue](learning-paths.md#stress-recovery-fatigue), then find a lesson in the series catalogue. The eight catalogue languages are documentation languages; lesson details are bilingual English/Chinese.
2. Reuse the existing local MP4 if you already have it. Otherwise, use the lesson's download link or its series Release to obtain the MP4. GitHub's **Code → Download ZIP** and a normal clone contain repository files, not the Release videos; an MP4 absent from a clone is not a missing attachment.
3. Select the matching Chinese (`zh-CN`) or English (`en`) SRT/VTT in a player that supports external subtitles. Use the stable lesson ID to match downloaded files; the original filename in the lesson details identifies an existing local video. Keeping the subtitle beside the video can help, but explicitly select the desired file if the player does not load it or selects another language. Switch languages by selecting the other subtitle file or an already loaded subtitle track. Do not rename or modify the original media to make a player load subtitles. No subtitle is burned into the video by this library update.

For a first example, open [wheelset modelling, `s06-e001`](../lessons/s06-e001.md), original filename `1 轮对建模.mp4`. Its lesson details link the MP4 and all four subtitle formats. The original local video and the downloaded `s06-e001.mp4` have different names; match them through the lesson ID and recorded original filename, then load the subtitle explicitly. This does not establish that a particular player is installed or that playback and subtitle alignment have been tested on your device.

### Finding passages and reporting a problem

Search a catalogue for a topic, then read the matching subtitle file to locate candidate timestamps. A timestamp from a subtitle is a navigation aid; rewatch the recording before relying on a menu name, parameter value or simulation conclusion. If using Codex, ask it to retain the lesson ID, distinguish quoted subtitle evidence from its summary and mark uncertain recognition errors.

Use the [contribution guide](../CONTRIBUTING.md) and the appropriate issue form to report a stable lesson ID, language, timestamp and observed problem. Creating an issue requires GitHub sign-in; reading public issues does not require repository membership. The catalogue displays translated titles while retaining the original filename in the lesson detail page; a translated title does not rename the media attachment.

The current inventory contains 194 videos and 772 subtitle files. Four subtitle files—Chinese SRT/VTT and English SRT/VTT—are available for 193 lessons. [Series 5, `s05-e001`](../lessons/s05-e001.md), original file `0-课程效果.mp4`, has no matching files in these four formats. Its video remains a separate lesson; no substitute subtitle is provided.

When the repository is private, repository membership or other granted GitHub access is required for its pages and Release downloads; a normal download URL alone does not grant access. Sign in with an account that already has permission, or contact the maintainer through an existing authorized channel. Do not send passwords or access tokens in an issue. When the repository is public, anonymous access does not grant a media reuse licence. Check the project homepage and the actual GitHub repository for the current state. Changing visibility requires separate distribution permission and review; documentation translations do not enable public access.

The root navigation includes [English](../README.md), [简体中文](../README.zh-CN.md), [日本語](../README.ja.md), [Français](../README.fr.md), [Deutsch](../README.de.md), [Italiano](../README.it.md), [Español](../README.es.md) and [한국어](../README.ko.md). Only Chinese/English subtitle files are listed. Available files have not thereby been declared semantically or linguistically reviewed. See [quality and versions](quality-and-versions.md), [terminology](terminology.md) and [sources](../PROVENANCE.md).

## 简体中文

### 可以访问什么

2026 年 10 月 12 日已核实仓库为 public，README、逐课目录、字幕及既有已发布 Release 页面可匿名访问，无需仓库成员权限。按原课程链接下载；公开可访问本身不会授予媒体再利用许可。

当前已有 Markdown 课程目录、中英双语详情、Release 下载链接与中英文字幕；没有内嵌播放器、专用搜索界面或自动学习进度功能。学习路线用于选择起点，观看仍使用本地播放器。

### 最短看课步骤

1. 选择[Simpack 入门](learning-paths.md#simpack-basics)、[Abaqus 柔性轨道](learning-paths.md#abaqus-flexible-track)或[应力恢复与疲劳](learning-paths.md#stress-recovery-fatigue)，再在系列目录找课。八语目录属于文档语言；课程详情为中英双语。
2. 已有本地 MP4 时直接复用；否则使用课程下载链接或该系列 Release 获取视频。GitHub 的 **Code → Download ZIP** 与普通 clone 包含仓库文件，不包含 Release 视频；clone 中没有 MP4 不代表附件丢失。
3. 用支持外挂字幕的播放器选择同课中文（`zh-CN`）或英文（`en`）SRT/VTT。下载文件用稳定课程 ID 配对；已有本地视频用详情记录的原始文件名核对。字幕放在视频旁可便于管理，但未自动加载或选错语言时应手动指定文件。切换语言时选择另一字幕文件或已加载的字幕轨。不要为了自动加载而改名或修改原始素材。本轮整理不向视频烧录字幕。

首次可打开[轮对建模 `s06-e001`](../lessons/s06-e001.md)，原始文件名为 `1 轮对建模.mp4`。详情页提供 MP4 与四种字幕格式链接。原本机视频和下载的 `s06-e001.mp4` 名称不同，应按课程 ID 与记录的原文件名核对，再手动加载字幕。这些说明不代表已确认你的播放器安装、实际播放或音画同步。

### 定位片段与反馈问题

先按课目检索目录，再阅读对应字幕定位候选时间戳。字幕时间戳用于导航；菜单名、参数值和仿真结论须回看视频确认。用 Codex 整理时，要求保留课程 ID，区分字幕依据与归纳，并标记疑似识别错误。

请按[贡献说明](../CONTRIBUTING.md)使用对应问题表单，给出稳定课程 ID、语言、时间戳和实际问题。提交问题需要登录 GitHub；阅读公开问题单不需要仓库成员权限。目录使用显示译名，详情页保留中文原文件名；显示题名变化不会改名媒体附件。

真实清单包含 194 个视频、772 个字幕文件。193 课拥有中文 SRT/VTT、英文 SRT/VTT 四种文件。[系列 5 的 `s05-e001`](../lessons/s05-e001.md)，原文件 `0-课程效果.mp4`，四种配套字幕均缺失；视频继续独立保留，不提供伪造的替代字幕。

仓库为 private 时，查看仓库页面和下载 Release 需要已授予的 GitHub 访问权限；普通下载地址本身不会授予权限。请使用已有权限的账号登录，或通过既有授权渠道联系维护者；不要在问题单中发送密码或访问 token。仓库为 public 时可匿名访问，但不因此获得媒体再利用许可。当前状态以首页和实际 GitHub 仓库为准；公开操作需要独立的传播权限与审查，不会因题名翻译而自动开启。

文档导航提供[英文](../README.md)、[简体中文](../README.zh-CN.md)、[日文](../README.ja.md)、[法文](../README.fr.md)、[德文](../README.de.md)、[意大利文](../README.it.md)、[西班牙文](../README.es.md)及[韩文](../README.ko.md)，字幕仅列中文与英文。文件可用不代表语义和语言已审校。参见[质量与版本说明](quality-and-versions.md)、[术语约定](terminology.md)和[来源说明](../PROVENANCE.md)。
