# Simpack 철도차량 동역학 튜토리얼

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

> 현재 비공개 저장소입니다. 영상과 자막을 다운로드하려면 저장소 접근 권한이 있는 GitHub 계정이 필요합니다.

**차량–궤도–교량 상호작용 · 유연체 · 응력 복원 및 피로 해석**

이 저장소는 Simpack, Abaqus, Ansys, fe-safe를 이용한 철도 동역학 작업 흐름을 일곱 시리즈로 정리합니다. 차량 모델링, 유연 레일과 궤도 기초, 차량–궤도–교량 연성, 유연체의 응력·변형률 복원 및 피로 해석을 주제별로 찾아볼 수 있습니다.

영상 194개 · 자막 파일 772개 · 네 종류의 자막이 있는 강의 193개. 자막 파일이 없는 강의: `s05-e001` — 0-课程效果.

## 시리즈 목록

| 시리즈 | 주제 | 영상 수 | 파일 |
|---|---|---:|---|
| 1 | [Abaqus–Simpack 기반 철도차량·유연 레일·플로팅 슬래브 연성동역학](series/1/README.ko.md) | 18 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Ansys/Abaqus–Simpack–fe-safe 기반 유연체의 동적 응력·변형률 및 피로 해석](series/2/README.ko.md) | 13 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Ansys Workbench Mechanical·APDL·Simpack을 이용한 철도차량–유연 궤도 동역학 해석](series/3/README.ko.md) | 16 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Abaqus–Simpack을 이용한 차량–궤도–교량 연성동역학](series/5/README.ko.md) | 42 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Simpack 철도차량 동역학 입문 사례](series/6/README.ko.md) | 8 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Ansys–Simpack 차량–궤도–교량 연성동역학: Beam–Solid 모델링](series/7/README.ko.md) | 46 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Ansys–Simpack 차량–궤도–교량 연성동역학: Beam–Beam 모델링](series/8/README.ko.md) | 51 | [릴리스](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

시리즈 제목을 누르면 기존 개별 강의 목록으로, 릴리스를 누르면 영상과 자막 다운로드로 이동합니다. 원래 번호를 유지하므로 시리즈 4는 없습니다.

## 학습 시작점

처음 차량 모델을 만든다면 **시리즈 6**부터 시작하는 것을 권합니다. 유연 궤도는 Abaqus 경로의 **시리즈 1** 또는 Ansys 경로의 **시리즈 3**을 선택한 뒤 **시리즈 5·7·8**의 차량–궤도–교량 모델로 진행할 수 있습니다. 응력·변형률 복원과 피로 해석이 목적이라면 **시리즈 2**를 참고하세요. 이는 편집상 학습 제안이며, 검증된 선수 과목 체계는 아닙니다.

## 주제 안내

아래 분류는 제공된 강의 제목을 정리한 것입니다. 모델, 수치 결과 또는 소프트웨어 버전 조합이 독립적으로 검증되었다는 뜻은 아닙니다.

### 시리즈 1 — Abaqus–Simpack 기반 철도차량·유연 레일·플로팅 슬래브 연성동역학

- Abaqus에서 유연 레일과 스프링 지지 플로팅 슬래브 모델링 및 FBI 생성
- FTR 파일 작성과 Simpack 유연 궤도 설정
- 윤축·대차 프레임·전체 차량 모델링 및 차량–플로팅 슬래브 연성
- TRE / PSD 가진, 유연체 변형 애니메이션, 응답 후처리

### 시리즈 2 — Ansys/Abaqus–Simpack–fe-safe 기반 유연체의 동적 응력·변형률 및 피로 해석

- Abaqus / Ansys 인터페이스 데이터 준비와 FBI 유연체 생성
- Simpack 유연체 설정 및 응력·변형률 복원
- Simpack Post의 변형·응력·변형률 시각화
- fe-safe용 데이터 내보내기, 피로 해석, 통합 작업 흐름 사례

### 시리즈 3 — Ansys Workbench Mechanical·APDL·Simpack을 이용한 철도차량–유연 궤도 동역학 해석

- SpaceClaim 레일 보 모델과 Workbench Mechanical 부분구조 축약
- APDL 그래픽 인터페이스·명령 작업 흐름과 FBI 인터페이스 처리
- FTR 궤도 기초 연결 및 힘 요소 일괄 설정
- 단순 차량 모델, TRE / PSD 가진, 애니메이션, 후처리 매개변수

### 시리즈 5 — Abaqus–Simpack을 이용한 차량–궤도–교량 연성동역학

- 레일, CRTS III 궤도 슬래브, 콘크리트 층, 기초 슬래브 및 단순지지 교량 거더
- 재료, 메시, 체결장치, 내부 접촉 및 부분구조 생성
- FBI / FTR, 매개변수화 차량, 정적 평형 및 차량–궤도–교량 연성
- 초기 하중, 솔버, 궤도 불규칙 및 영상에서 다루는 동역학 평가량

### 시리즈 6 — Simpack 철도차량 동역학 입문 사례

- 윤축과 대차 프레임 모델링
- 전체 차량 모델 조립
- TRE 파일과 PSD 가진
- 응답 후처리 및 분석

### 시리즈 7 — Ansys–Simpack 차량–궤도–교량 연성동역학: Beam–Solid 모델링

- RAIL-EULER, rail-timo, 솔리드 교량 모델 및 모드 관련 내용
- 레일·교량 FBI 파일, FTR 작성 및 오류 분석
- 매개변수화 차량, 연성 설정 순서, 전이 구간 강성과 감쇠
- 초기 하중, 솔버, 가진, 교량·레일 응답 및 모델 정리

### 시리즈 8 — Ansys–Simpack 차량–궤도–교량 연성동역학: Beam–Beam 모델링

- RAIL-EULER, rail-timo, BEAM188 교량 모델 및 모드 관련 내용
- FBI / FTR 설정, 매개변수화 차량 및 차량–궤도–교량 연성
- 레일·교량 연결점, 연결 요소, 받침 및 센서 일괄 생성
- 초기 하중, 솔버, 가진, 후처리 및 모델 정리

## 다운로드 및 사용

해당 시리즈에서 MP4와 같은 강의의 `.zh-CN.srt` 또는 `.en.srt` 파일을 다운로드하세요. 파일명의 공통 식별자를 유지하고 로컬 영상 플레이어에서 자막 파일을 선택하면 됩니다. VTT 형식도 제공됩니다. 저장소 clone이나 Code → Download ZIP에는 Releases에 저장된 영상이 포함되지 않습니다.

다운로드 권한은 저장소 공개 설정을 따릅니다. private 상태에서는 접근 권한이 있는 GitHub 계정이 필요합니다. 영상 링크는 다운로드용이며 내장 스트리밍 플레이어 제공을 보장하지 않습니다.

## 언어 안내

소개와 주제 안내는 영어, 중국어 간체, 일본어, 프랑스어, 독일어, 이탈리아어, 스페인어, 한국어로 제공됩니다. 문서 현지화가 해당 언어의 자막이나 더빙 추가를 뜻하지는 않습니다. 현재 자막 언어는 중국어와 영어입니다. 정확한 식별을 위해 원래 중국어 강의 제목을 유지합니다.

## 범위와 기술적 주의사항

이 프로젝트는 튜토리얼 자료실이며 검증된 벤치마크나 소프트웨어 배포본이 아닙니다. 영상에 모델이 등장한다고 해서 모델 파일, 솔버 라이선스 또는 입력 데이터가 포함된 것은 아닙니다. 절차를 적용하기 전에 버전, 단위, 경계조건, 감쇠, 모델 축약 설정 및 평가 기준을 확인해야 합니다. 과거 영상의 표준 설명을 현행 요구사항으로 간주하지 마세요. Beam–Solid와 Beam–Beam은 두 학습 경로를 구분하는 이름이지 정확도 우위를 입증한 결과가 아닙니다.

자막 파일의 존재와 체크섬 일치만으로 번역의 정확성이나 음성 동기화를 확인할 수는 없습니다. 전문 용어는 원본 영상과 해당 소프트웨어 문서를 대조해 검토해야 합니다.

## 수정 및 기여

수정 사항을 알릴 때 시리즈 번호, 고정 강의 식별자, 자막 언어 및 필요한 타임스탬프를 포함해 주세요. 표시 제목이나 번역을 개선할 때도 원래 식별자는 변경하지 않습니다. 필요한 허가 없이 상용 소프트웨어, 라이선스 파일, 제삼자 강의 또는 모델을 올리지 마세요.

## 출처와 이용 권한

저장소 관리, 강의 저작, 소프트웨어 소유는 서로 다른 역할입니다. 기록된 출처와 권리 상태는 출처 설명을 확인하세요. 공급업체의 공식 제휴나 보증을 주장하지 않습니다. 공개 접근이 가능하다는 사실만으로 강의 자료의 무제한 재사용·재배포가 허용되는 것은 아닙니다.

[출처 및 권리 설명](PROVENANCE.md)

[다운로드 안내](docs/using-the-library.md) · [학습 제안](docs/learning-paths.md) · [품질과 버전](docs/quality-and-versions.md) · [용어](docs/terminology.md) · [기여](CONTRIBUTING.md) · [출처와 권리](PROVENANCE.md)
