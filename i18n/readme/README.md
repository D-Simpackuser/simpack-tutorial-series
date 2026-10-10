# Simpack Railway Dynamics Tutorials

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

**Vehicle–track–bridge interaction · Flexible bodies · Stress recovery and fatigue**

This repository brings together seven tutorial series on railway dynamics workflows using Simpack, Abaqus, Ansys and fe-safe. It provides a structured route through vehicle modelling, flexible rails and track foundations, vehicle–track–bridge coupling, and flexible-body stress and fatigue analysis.

The current catalogue contains **194 video lessons**. **193 lessons** have Chinese and English subtitle files in both SRT and VTT formats, for a total of **772 subtitle files**. The introductory video `0-课程效果` in Series 5 has no accompanying subtitle files.

## Series catalogue

| Series | Subject | Lessons | Files |
|---|---|---:|---|
| 1 | [Coupled Railway Vehicle–Flexible Rail–Floating Slab Dynamics with Abaqus and Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/1/README.md) | 18 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Dynamic Stress, Strain and Fatigue Analysis of Flexible Bodies with Ansys/Abaqus, Simpack and fe-safe](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/2/README.md) | 13 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Railway Vehicle–Flexible Track Dynamics with Ansys Workbench Mechanical, APDL and Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/3/README.md) | 16 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Coupled Vehicle–Track–Bridge Dynamics with Abaqus and Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/5/README.md) | 42 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Getting Started with Railway Vehicle Dynamics in Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/6/README.md) | 8 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Vehicle–Track–Bridge Dynamics with Ansys and Simpack: Beam–Solid Modelling](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/7/README.md) | 46 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Vehicle–Track–Bridge Dynamics with Ansys and Simpack: Beam–Beam Modelling](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/8/README.md) | 51 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

Open a series title for the existing lesson-by-lesson index. Release pages contain the downloadable video and subtitle assets. The original series identifiers are retained; there is no Series 4.

## Where to start

For a first vehicle model, start with **Series 6**. For flexible-track workflows, choose **Series 1** for the Abaqus route or **Series 3** for the Ansys route. Continue with **Series 5, 7 or 8** for vehicle–track–bridge models. Use **Series 2** when the focus is stress/strain recovery and fatigue. This is an editorial learning suggestion, not a verified prerequisite chain.

## Topic guide

The topic groups below organise the supplied lesson titles. They are not evidence that a model, numerical result or software-version combination has been independently validated.

### Series 1 — Coupled Railway Vehicle–Flexible Rail–Floating Slab Dynamics with Abaqus and Simpack

- Flexible rail and spring-supported floating slab modelling in Abaqus; FBI generation
- FTR authoring and flexible-track setup in Simpack
- Wheelset, bogie-frame and complete-vehicle modelling; vehicle–floating-slab coupling
- TRE / PSD excitation, flexible-body animation and response post-processing

### Series 2 — Dynamic Stress, Strain and Fatigue Analysis of Flexible Bodies with Ansys/Abaqus, Simpack and fe-safe

- Abaqus / Ansys interface preparation and FBI flexible-body generation
- Flexible-body setup and stress/strain recovery in Simpack
- Deformation, stress and strain visualisation in Simpack Post
- Export to fe-safe; fatigue analysis and an integrated workflow example

### Series 3 — Railway Vehicle–Flexible Track Dynamics with Ansys Workbench Mechanical, APDL and Simpack

- Rail beam modelling in SpaceClaim; substructuring in Workbench Mechanical
- APDL graphical and command-based workflows; FBI interface handling
- FTR foundation connections and batch configuration of force elements
- Simple vehicle models, TRE / PSD excitation, animation and post-processing parameters

### Series 5 — Coupled Vehicle–Track–Bridge Dynamics with Abaqus and Simpack

- Rails, CRTS III track slabs, concrete layers, base slabs and a simply supported bridge girder
- Materials, mesh, fasteners, internal contacts and substructure generation
- FBI / FTR, parameterised vehicles, static equilibrium and vehicle–track–bridge coupling
- Preload, solver setup, track irregularities and the dynamics assessment quantities addressed in the recordings

### Series 6 — Getting Started with Railway Vehicle Dynamics in Simpack

- Wheelset and bogie-frame modelling
- Complete-vehicle model assembly
- TRE files and PSD excitation
- Response post-processing and analysis

### Series 7 — Vehicle–Track–Bridge Dynamics with Ansys and Simpack: Beam–Solid Modelling

- RAIL-EULER, rail-timo, solid bridge models and modal topics
- Rail and bridge FBI files; FTR authoring and troubleshooting
- Parameterised vehicles, coupling order and transition-zone stiffness/damping
- Preload, solver setup, excitation, bridge/rail responses and model organisation

### Series 8 — Vehicle–Track–Bridge Dynamics with Ansys and Simpack: Beam–Beam Modelling

- RAIL-EULER, rail-timo, BEAM188 bridge models and modal topics
- FBI / FTR setup, parameterised vehicles and vehicle–track–bridge coupling
- Batch creation of rail/bridge connection points, connections, supports and sensors
- Preload, solver setup, excitation, post-processing and model organisation

## Download and use

Open the relevant series, choose a lesson and download its MP4 together with the matching `.zh-CN.srt` or `.en.srt` file. Keep the stable filename stem unchanged and select the subtitle file in your local video player. VTT files are available as an alternative format. A repository clone or the Code → Download ZIP archive does not include the video assets stored in Releases.

Download links follow the repository’s access settings. While the repository is private, an authorised GitHub account is required. Video links are download links, not a promise of an embedded streaming player.

## Languages

The introduction and topic guide are provided in English, Simplified Chinese, Japanese, French, German, Italian, Spanish and Korean. This is documentation localisation: it does not create additional subtitle tracks or dubbed audio. The current subtitle languages are Chinese and English. Original Chinese lesson titles remain available for exact identification.

## Scope and technical limitations

This is a tutorial library, not a validated benchmark or a software distribution. A topic appearing in a recording does not imply that its model files, solver licences or input data are included. Verify the software version, units, boundary conditions, damping, model reduction settings and evaluation criteria before adapting a workflow. Historical discussions of railway standards must not be treated as statements of current requirements. Beam–Solid and Beam–Beam name two course tracks; they do not establish which modelling level is more accurate.

Subtitle file presence and checksum agreement do not establish translation accuracy or audio–subtitle alignment. Technical translations should be checked against the original recording and the relevant software documentation.

## Corrections and contributions

Report corrections with the series identifier, stable lesson identifier, subtitle language and timestamp where relevant. Keep original file identifiers unchanged when proposing a better title or translation. Do not upload commercial software, licence files, third-party course material or models without the necessary permission.

## Sources and permissions

Repository maintenance, course authorship and software ownership are different roles. See the existing provenance statement for the recorded source and rights status. No official vendor affiliation or endorsement is claimed. Public availability alone is not a blanket licence to reuse or redistribute the course media.

[Source and rights statement](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/PROVENANCE.md)
