# Learning paths / 学习路径

[English](#english) · [简体中文](#简体中文) · [Project](../README.md) · [项目首页](../README.zh-CN.md)

## English

These are editorial suggestions based on the course titles, rather than instructor-confirmed prerequisites or evidence that every recording has been reviewed. Follow the existing order within each series; these suggestions do not change lesson IDs or reorder the catalogue.

| Interest | Suggested entry points |
|---|---|
| Getting started with railway vehicles in Simpack | [Series 6](../series/6/README.md), then the vehicle-related lessons in a relevant coupled workflow |
| Flexible rail and flexible-track workflows | [Series 1](../series/1/README.md) and [Series 3](../series/3/README.md) |
| Vehicle–track–bridge coupling | [Series 5](../series/5/README.md), [Series 7: Beam–Solid](../series/7/README.md) and [Series 8: Beam–Beam](../series/8/README.md) |
| Flexible-body stress, strain and fatigue workflows | [Series 2](../series/2/README.md) |

Start with the modelling and file-generation titles relevant to your chosen workflow, then consult its coupling, excitation and post-processing titles. This is a way to navigate the library, not a promise that workflows interchange across software versions or that a model has been validated for a particular engineering application. The Beam–Solid and Beam–Beam labels distinguish courses; they do not establish an accuracy or speed comparison. No estimated study hours are provided where durations are unknown. Consult [quality and versions](quality-and-versions.md) before applying a workflow.

The repository is public. The routes below link to the existing lesson catalogue and published Release media; repository membership is not required to browse them. Accompanying model files remain unconfirmed. See [what is available and how to watch](using-the-library.md).

## Three starting routes / 三个学习入口

<a id="simpack-basics"></a>

### Simpack basics / Simpack 入门

Start with [wheelset modelling, `s06-e001`](../lessons/s06-e001.md) in [Series 6](../series/6/README.md). Continue through that series' frame and complete-vehicle modelling titles, then its TRE/PSD and response-processing titles in the existing order. Keep a note of the lesson ID and the timestamp of any menu or model setting you need to revisit. This route identifies course topics; it does not supply the accompanying model or validate the resulting vehicle model.

从[系列 6](../series/6/README.zh-CN.md)的[轮对建模 `s06-e001`](../lessons/s06-e001.md)开始，按原目录继续查看构架、整车建模，再查看 TRE/PSD 与响应后处理课目。记录需要回看的菜单或模型设置对应的课程 ID 和时间戳。这条路线用于定位课目，不提供配套模型，也不验证学习者建立的车辆模型。

<a id="abaqus-flexible-track"></a>

### Abaqus flexible track / Abaqus 柔性轨道

Use [Series 1](../series/1/README.md). Its first two lessons, [`s01-e001`](../lessons/s01-e001.md) and [`s01-e002`](../lessons/s01-e002.md), are titled Abaqus flexible-rail modelling; [`s01-e003`](../lessons/s01-e003.md) is the Simpack flexible-rail FBI generation lesson. Continue with the FTR and floating-slab modelling titles, then the vehicle–floating-slab coupling and excitation/post-processing titles in the catalogue. For an Ansys-oriented route, compare the topics in [Series 3](../series/3/README.md), without assuming interchangeable settings or files.

选择[系列 1](../series/1/README.zh-CN.md)。前两课[`s01-e001`](../lessons/s01-e001.md)、[`s01-e002`](../lessons/s01-e002.md)的原题为 ABAQUS 柔性钢轨建模上、下；[`s01-e003`](../lessons/s01-e003.md)为 Simpack 柔性钢轨 FBI 生成课目。沿目录继续查看 FTR、浮置板建模，再进入车辆–浮置板耦合、激励和后处理课目。Ansys 背景可对照[系列 3](../series/3/README.zh-CN.md)的课目，但不能据此假定设置或文件可互换。

<a id="stress-recovery-fatigue"></a>

### Stress recovery and fatigue / 应力恢复与疲劳

Use [Series 2](../series/2/README.md) and its complete original order. Useful lookup points are [FBI generation, `s02-e010`](../lessons/s02-e010.md), [Simpack flexible-body setup, `s02-e009`](../lessons/s02-e009.md) and [stress/strain recovery matrices, `s02-e013`](../lessons/s02-e013.md). These are topic lookup points, not a new prerequisite sequence. Read the surrounding file-preparation and fe-safe export/fatigue lesson titles to find the steps relevant to your own input files. Subtitle reading can help locate passages, but does not establish the correct recovery options, required file extensions, matrix dimensions or numerical results.

选择[系列 2](../series/2/README.zh-CN.md)，仍按完整原目录学习。按研究主题查课时可定位[FBI 生成 `s02-e010`](../lessons/s02-e010.md)、[Simpack 柔性体设置 `s02-e009`](../lessons/s02-e009.md)和[应力应变恢复矩阵 `s02-e013`](../lessons/s02-e013.md)。这些是查找入口，不是重排后的先修顺序；结合目录中的文件准备、fe-safe 导出与疲劳课目，定位与你已有输入文件相关的环节。字幕可帮助定位片段，不能据此确定恢复选项、所需扩展名、矩阵维度或数值结果。

For all three routes, confirm software versions, licences, units and input-file availability before reproducing a workflow. Do not infer an exact parameter from uncertain subtitle wording. Report a correction using the [contribution guide](../CONTRIBUTING.md), with the lesson ID and timestamp; creating an issue requires GitHub sign-in.

三条路线均应先确认软件版本、许可、单位制和输入文件是否具备。不要从模糊字幕推定精确参数。按[贡献说明](../CONTRIBUTING.md)反馈课程 ID 与时间戳；提交问题需要登录 GitHub。

## 简体中文

以下路线是依据课目名称的编辑建议，不是讲师确认的先修关系，也不代表已完整审阅全部视频。各系列仍按原有顺序学习；建议路线不改变课程 ID 和目录排序。

可直接打开上方三个中英双语入口：[Simpack 入门](#simpack-basics)、[Abaqus 柔性轨道](#abaqus-flexible-track)、[应力恢复与疲劳](#stress-recovery-fatigue)。本仓库已为 public，课目目录及既有已发布 Release 可匿名访问；配套模型仍未确认。看课步骤见[使用说明](using-the-library.md)。

| 关注方向 | 建议入口 |
|---|---|
| Simpack 轨道车辆入门 | [系列 6](../series/6/README.zh-CN.md)，再选择相关耦合流程中的车辆课目 |
| 柔性钢轨与柔性轨道流程 | [系列 1](../series/1/README.zh-CN.md)、[系列 3](../series/3/README.zh-CN.md) |
| 车—线—桥耦合 | [系列 5](../series/5/README.zh-CN.md)、[系列 7：Beam–Solid](../series/7/README.zh-CN.md)、[系列 8：Beam–Beam](../series/8/README.zh-CN.md) |
| 柔性体应力、应变与疲劳流程 | [系列 2](../series/2/README.zh-CN.md) |

可先查看所选流程相关的建模、文件生成课目，再查看耦合、激励与后处理课目。这只是目录导航建议，不保证跨软件版本的流程可互换，也不声明模型已通过特定工程应用验证。Beam–Solid、Beam–Beam 用于区分课程，不能据此推断精度或效率对照结果。时长未知时不估算学习小时数。应用流程前请阅读[质量与版本说明](quality-and-versions.md)。
