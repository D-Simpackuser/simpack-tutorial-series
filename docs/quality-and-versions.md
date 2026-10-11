# Quality and versions / 质量与版本说明

[English](#english) · [简体中文](#简体中文) · [Project](../README.md) · [项目首页](../README.zh-CN.md)

## English

The catalogue preserves separate kinds of evidence. A file can be available and byte-identical to its source without its teaching content, subtitle meaning or simulation results being independently validated.

| Evidence | What it supports | What it does not establish |
|---|---|---|
| Inventory and exact-path matching | Existing lesson IDs, file mapping and subtitle availability | Authorship, technical correctness or complete video privacy review |
| Subtitle copy SHA-256 equality | Copies have the same bytes as the source subtitles | Translation quality or timestamp accuracy |
| Release attachment size and SHA-256 digest comparison | Recorded remote media match the verified attachment evidence | Independent simulation validation or engineering applicability |
| Editorial title and terminology review | More consistent navigation in eight documentation languages | Review by native-speaking railway engineers |

The available subtitles are Chinese and English SRT/VTT files for 193 of 194 lessons. Their semantic and timing review status has not been established by format or hash checks. The missing group is [Series 5, `s05-e001`](../lessons/s05-e001.md). Eight documentation languages do not imply eight subtitle languages or multilingual narration.

Software versions are not assigned from product names or guessed interface appearance. A source title labelled `new`, backup or “correct for version 2022” remains a source label, rather than a current-version recommendation verified by this library. Truncated source titles are identified without guessing the omitted text. Unknown `duration_seconds` values remain `null`; no total runtime or learning-hours claim is derived from them.

Course titles that discuss older and newer locomotive dynamics standards do not establish which standards apply today, in your jurisdiction or to a particular vehicle. Verify the actual standard, date and application requirements separately when using the material. The library does not claim official vendor certification, supplied model files or an experimentally validated benchmark. Coupled or integrated workflows are not automatically described as synchronized co-simulation, and “full-platform” wording does not demonstrate compatibility with every operating system.

Video, subtitle and documentation permissions are distinct from these technical checks. Existing private-upload permission is not a public-distribution grant. A full content privacy review of all recordings has not been established. See [sources and distribution rights](../PROVENANCE.md). For a correction, cite the lesson ID and the specific source or timestamp in [a contribution](../CONTRIBUTING.md).

## 简体中文

目录区分不同层次的证据。文件可用且与源文件字节一致，不等于教学内容、字幕语义或仿真结果已获独立验证。

| 证据 | 可支持的结论 | 不能由此确认的结论 |
|---|---|---|
| 真实清单与完整路径匹配 | 既有课程 ID、原始文件映射和字幕可用性 | 作者身份、技术正确性、完整视频隐私审阅 |
| 字幕副本 SHA-256 一致 | 副本字节与源字幕相同 | 翻译质量或时间轴准确性 |
| Release 附件大小与 SHA-256 digest 比对 | 已记录远端媒体与核验依据一致 | 独立仿真验证或工程适用性 |
| 题名与术语编辑复核 | 八语文档导航用词较一致 | 母语铁路工程师审校 |

194 课中有 193 课具备中文、英文 SRT/VTT 文件。格式或哈希检查没有证明语义和时间轴审校完成。缺失组为[系列 5 的 `s05-e001`](../lessons/s05-e001.md)。八种文档语言不代表八语字幕或多语配音。

不从产品名或猜测的界面外观指定软件版本。原题中的 `new`、备份和“2022版本正确”保留为源标签，不能视为本资料库核实的当前版本推荐。截断原题明确标记，不猜测补全。未知 `duration_seconds` 保持 `null`，不据此编造总时长或学习小时数。

讲解机车动力学新、旧标准的课目，不能证明当前适用标准、地区要求或特定车辆要求。实际应用时需另行核实标准、日期及适用条件。本资料库不声称官方厂商认证、提供模型文件或经过试验验证的 benchmark。耦合或集成流程不能自动称为同步联合求解；“全平台”字样也不证明全部操作系统兼容。

视频、字幕及文档的传播权利与这些技术检查分别处理。现有 private 上传授权不等于向公众分发的授权；尚未建立全部录像内容的完整隐私审阅记录。详见[来源与传播权利](../PROVENANCE.md)。纠错请在[贡献](../CONTRIBUTING.md)中给出课程 ID 和明确出处或时间戳。
