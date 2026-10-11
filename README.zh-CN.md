# RailDyn Atlas｜轨道车辆系统动力学教程图谱

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

> 仓库当前为 private：下载视频及字幕需要具有仓库访问权限的 GitHub 账号。

**车辆–轨道–桥梁耦合 · 柔性体 · 应力应变恢复与疲劳分析**

RailDyn Atlas 按七个系列整理 Simpack、Abaqus、Ansys 与 fe-safe 相关的轨道车辆动力学视频教程，覆盖车辆建模、柔性钢轨与轨道基础、车–线–桥耦合，以及柔性体应力应变恢复和疲劳分析。目录用于按主题定位课程、下载视频并选择对应字幕。

194 个视频课程 · 772 个字幕文件 · 193 课具备四种配套字幕文件。 没有配套字幕的课程：`s05-e001` — 0-课程效果.

[下载说明](docs/using-the-library.md) · [学习建议](docs/learning-paths.md) · [质量与版本](docs/quality-and-versions.md)

本项目提供教程录像；未确认配套模型文件和软件版本，也未建立独立数值验证依据。文档提供八种语言，字幕仍为中文和英文。

## 系列目录

| 系列 | 课程主题 | 视频数 | 文件 |
|---|---|---:|---|
| 1 | [基于ABAQUS-Simpack联合的轨道车辆-柔性轨-浮置板耦合动力学](series/1/README.zh-CN.md) | 18 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [基于ANSYS/ABAQUS-Simpack-Fesafe的弹性体动态应力应变/疲劳仿真解决方案](series/2/README.zh-CN.md) | 13 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [基于ANSYS Workbench Mechanical &amp; APDL的轨道车辆-弹性轨道动力学全平台实现](series/3/README.zh-CN.md) | 16 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [ABAQUS-Simpack联合仿真实现车线桥耦合动力学系统](series/5/README.zh-CN.md) | 42 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Simpack轨道车辆动力学快速入门案例](series/6/README.zh-CN.md) | 8 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Solid）](series/7/README.zh-CN.md) | 46 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Beam）](series/8/README.zh-CN.md) | 51 | [下载合集](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

点击系列名称进入现有逐课目录，点击下载合集进入该系列的 Release。保留原始系列编号，不补建系列 4，也不因学习顺序调整而重编号。

## 从哪里开始

初次建立车辆模型，建议先学习**系列 6**。柔性轨道方向可按工具背景选择 Abaqus 路线的**系列 1**或 Ansys 路线的**系列 3**，随后进入**系列 5、7、8**中的车–线–桥耦合内容。以应力、应变恢复和疲劳分析为目标时，重点查看**系列 2**。这是目录维护者提出的学习建议，不是已经核验的课程先修关系。

## 主题导览

以下分组依据已有课程标题整理，便于浏览；不表示模型、数值结果或软件版本组合已经通过独立验证。

### 系列 1 — 基于ABAQUS-Simpack联合的轨道车辆-柔性轨-浮置板耦合动力学

- Abaqus 柔性钢轨与钢弹簧浮置板建模；FBI 文件生成
- FTR 文件编写与 Simpack 柔性轨道设置
- 轮对、构架和整车建模；车辆与浮置板轨道耦合
- TRE / PSD 激励、柔性体动画及响应后处理

### 系列 2 — 基于ANSYS/ABAQUS-Simpack-Fesafe的弹性体动态应力应变/疲劳仿真解决方案

- Abaqus / Ansys 接口准备与 FBI 柔性体文件生成
- Simpack 柔性体设置及应力、应变恢复
- Simpack Post 变形与应力应变结果查看
- 向 fe-safe 导出计算文件；疲劳分析与完整流程案例

### 系列 3 — 基于ANSYS Workbench Mechanical &amp; APDL的轨道车辆-弹性轨道动力学全平台实现

- SpaceClaim 钢轨梁模型；Workbench Mechanical 子结构缩减
- APDL 图形界面与命令流；FBI 接口处理
- FTR 弹性轨道基础连接与力元批量设置
- 简易车辆、TRE / PSD 激励、动画与后处理参数读取

### 系列 5 — ABAQUS-Simpack联合仿真实现车线桥耦合动力学系统

- 钢轨、CRTS III 型轨道板、混凝土层、底座板与简支梁
- 材料、网格、扣件、内部接触和子结构生成
- FBI / FTR、参数化车辆、静平衡及车–线–桥耦合
- 预载荷、求解、轨道不平顺及课程涉及的动力学评价指标

### 系列 6 — Simpack轨道车辆动力学快速入门案例

- 轮对与构架建模
- 整车模型装配
- TRE 文件与 PSD 激励设置
- 仿真响应的后处理及分析

### 系列 7 — ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Solid）

- RAIL-EULER、rail-timo、实体桥梁与模态相关课程
- 钢轨和桥梁 FBI 文件；FTR 编写与错误排查
- 参数化车辆、耦合顺序及过渡段刚度阻尼
- 预载荷、求解、激励、桥梁与钢轨响应、模型整理

### 系列 8 — ANSYS-SIMPACK 车-线-桥大系统联合仿真动力学（Beam-Beam）

- RAIL-EULER、rail-timo、BEAM188 桥梁与模态相关课程
- FBI / FTR 设置、参数化车辆与车–线–桥耦合
- 钢轨和桥梁连接点、连接作用、支座及传感器批量创建
- 预载荷、求解、激励、后处理和模型整理

## 下载与使用

进入对应系列后，下载所需课程的 MP4 和同课的 `.zh-CN.srt` 或 `.en.srt`。保留文件名中的稳定课程编号，在本地播放器中选择对应字幕；需要时也可使用 VTT 格式。克隆仓库或点击 Code → Download ZIP，不会下载存放在 Releases 中的视频附件。

下载权限随仓库可见性变化。仓库仍为 private 时，需要具有访问权限的 GitHub 账号。视频入口用于下载，不代表仓库已经提供内嵌流媒体播放器。

## 语言说明

项目介绍与主题导览提供英语、简体中文、日语、法语、德语、意大利语、西班牙语和韩语版本。文档多语言化不等于新增了对应语言的字幕或配音；现有字幕语言仍为中文和英文。原始中文课程标题保留，用于准确识别与核对。

## 内容边界与技术注意事项

本项目是教程资料库，不是已完成验证的基准模型库，也不分发商业仿真软件。视频涉及某个模型，不代表其工程文件、求解器许可或输入数据已经随仓库提供。复用流程前，应核对软件版本、单位制、边界条件、阻尼、模型缩减设置及评价指标。课程涉及的历史标准不能直接视为现行要求。Beam-Solid 与 Beam-Beam 是两个课程方向，不构成模型精度优劣的验证结论。

字幕文件存在、格式通过检查或校验和一致，不等于翻译语义与音画同步已经校对。专业术语应结合原视频与相应软件文档核查。

## 纠错与协作

反馈问题时，请给出系列编号、稳定课程编号、相关字幕语言及时间戳。修改显示标题或译名时保留原始文件标识。不要提交未经许可的商业软件、许可文件、第三方课程或模型资料。

## 来源与使用权限

仓库维护者、课程作者与软件权利人是不同角色。已记录的来源及权利状态见来源说明，不声称本项目获得软件厂商官方认证或背书。公开可访问不等于对课程媒体授予不受限制的再利用或再分发许可。

[来源与权利说明](PROVENANCE.md)

[下载说明](docs/using-the-library.md) · [学习建议](docs/learning-paths.md) · [质量与版本](docs/quality-and-versions.md) · [术语约定](docs/terminology.md) · [参与纠错](CONTRIBUTING.md) · [来源与权利](PROVENANCE.md)
