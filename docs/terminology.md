# Terminology / 术语约定

[English](#english) · [简体中文](#简体中文) · [Project](../README.md) · [项目首页](../README.zh-CN.md)

## English

The [eight-language glossary](../i18n/glossary.json) contains editorial term suggestions for this documentation. It is not a vendor-certified terminology standard and has not been independently reviewed by native-speaking railway engineers. Context and the original title take precedence over mechanical replacement.

| Chinese source concept | English display term | Distinction |
|---|---|---|
| 轮对 | wheelset | Not just one wheel |
| 构架／转向架构架 | bogie frame | Not the whole bogie |
| 转向架 | bogie | Keep separate from its frame |
| 车体 | carbody | Not the complete train |
| 钢轨／轨道 | rail / track | Rail is a component; track refers to the track system |
| 柔性体／弹性体 | flexible body | Multibody-system usage; not an elastomer |
| 应力／应变 | stress / strain | Keep distinct from deformation animation |
| 模态缩减／子结构 | modal reduction / substructure | Do not infer the reduction method from a filename alone |
| 预载荷／静平衡 | preload / static equilibrium | Distinct modelling concepts |
| 轨道不平顺／功率谱密度 | track irregularities / power spectral density (PSD) | Preserve the stated excitation context |

New display text uses **Abaqus**, **Ansys**, **Simpack** and **fe-safe**. Workbench Mechanical, APDL, SpaceClaim, Simpack Pre and Simpack Post remain recognizable. The exact formal Chinese series names preserve the maintainer's supplied spelling and punctuation; original media filenames and paths are not “corrected” or renamed.

Keep source labels `FBI`, `FTR`, `TRE`, `PSD`, `APDL`, `RWP` and `MSC`, and extensions `.fbi`, `.ftr`, `.tre`. Do not expand ambiguous abbreviations into product names or module claims. The literal `stress` label remains identifiable where a source title refers to a file or interface. `RAIL-EULER`, `rail-timo` and `BEAM188` retain their source identity.

“Coupled” or “integrated” wording does not claim synchronized co-simulation without source evidence. **Beam–Solid** and **Beam–Beam** distinguish Series 7 and 8; they do not demonstrate that one model is faster, more accurate or compliant with a national standard. A deformation animation is not automatically a quantitative strain result. A fatigue workflow is not proof of validated fatigue life.

Translated titles stay bound to the original Chinese title and stable lesson ID. Labels such as `new`, backup and “correct for version 2022” are attributed to the source title. Truncated titles remain marked as truncated. Report an ambiguity through [contributing](../CONTRIBUTING.md), citing the source title and relevant timestamp where available.

## 简体中文

[八语术语表](../i18n/glossary.json)是本轮文档的编辑建议，不是厂商认证标准，也没有母语铁路工程师独立审校的证据。具体语境和中文原题优先，不能机械替换。

| 原概念 | 英文显示词 | 需要保留的区别 |
|---|---|---|
| 轮对 | wheelset | 不是单个车轮 |
| 构架／转向架构架 | bogie frame | 不是整台转向架 |
| 转向架 | bogie | 与构架区分 |
| 车体 | carbody | 不是整列车 |
| 钢轨／轨道 | rail / track | 钢轨是构件，轨道指轨道系统 |
| 柔性体／弹性体 | flexible body | 多体系统语境，不译作橡胶弹性材料 elastomer |
| 应力／应变 | stress / strain | 与变形动画区分 |
| 模态缩减／子结构 | modal reduction / substructure | 不凭文件名推断具体缩减方法 |
| 预载荷／静平衡 | preload / static equilibrium | 两种不同建模概念 |
| 轨道不平顺／功率谱密度 | track irregularities / power spectral density (PSD) | 保留原题激励语境 |

新增显示文字统一使用 **Abaqus**、**Ansys**、**Simpack**、**fe-safe**；Workbench Mechanical、APDL、SpaceClaim、Simpack Pre、Simpack Post 保持可识别。中文正式系列名逐字保留维护者给定拼写及标点；原媒体文件名、路径不做“纠错”改名。

保留 `FBI`、`FTR`、`TRE`、`PSD`、`APDL`、`RWP`、`MSC` 标签及 `.fbi`、`.ftr`、`.tre` 扩展名，不从含义不明确的缩写扩写产品或模块。原题作为文件、接口标签使用的 `stress` 保持可识别；`RAIL-EULER`、`rail-timo`、`BEAM188` 保留源标识。

没有来源证据时，耦合或集成表达不扩展为同步 co-simulation。**Beam–Solid**、**Beam–Beam** 用于区分系列 7、8，不能据此声明某模型更快、更准确或符合国家标准。变形动画不自动构成定量应变结果，疲劳流程也不代表寿命已验证。

译名绑定中文原题和稳定课程 ID；`new`、备份、“2022版本正确”明确归属于原题标签。截断标题继续标为截断。歧义可通过[贡献说明](../CONTRIBUTING.md)反馈，并尽可能给出原题和相关时间戳。
