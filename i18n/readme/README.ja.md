# RailDyn Atlas

**Simpack 鉄道車両動力学・柔軟体シミュレーション資料ライブラリー**

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

**車両・軌道・橋梁の連成 · 弾性体 · 応力復元と疲労解析**

RailDyn Atlasは、Simpack、Abaqus、Ansys、fe-safeを用いた鉄道動力学の動画教材を七つのシリーズに整理しています。車両モデル、弾性レールと軌道基礎、車両・軌道・橋梁の連成、弾性体の応力・ひずみ復元と疲労解析を、テーマ別に探せます。

現在の目録には**194本の動画**があります。**193本**には中国語と英語の字幕がSRT・VTTの両形式で付属し、字幕ファイルは計**772個**です。シリーズ5の導入動画 `0-课程效果` には字幕ファイルがありません。

## シリーズ一覧

| シリーズ | テーマ | 動画数 | ファイル |
|---|---|---:|---|
| 1 | [Abaqus・Simpackによる鉄道車両・弾性レール・フローティングスラブの連成動力学](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/1/README.md) | 18 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Ansys／Abaqus・Simpack・fe-safeによる弾性体の動的応力・ひずみと疲労解析](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/2/README.md) | 13 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Ansys Workbench Mechanical・APDL・Simpackによる鉄道車両・弾性軌道の動力学解析](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/3/README.md) | 16 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Abaqus・Simpackによる車両・軌道・橋梁の連成動力学](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/5/README.md) | 42 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Simpackによる鉄道車両動力学の入門事例](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/6/README.md) | 8 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Ansys・Simpackによる車両・軌道・橋梁の連成動力学：Beam–Solidモデル](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/7/README.md) | 46 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Ansys・Simpackによる車両・軌道・橋梁の連成動力学：Beam–Beamモデル](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/8/README.md) | 51 | [リリース](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

シリーズ名から既存の各回一覧へ、リリースから動画・字幕のダウンロードへ進めます。元の番号を維持しているため、シリーズ4はありません。

## 学習の始め方

車両モデルを初めて作る場合は**シリーズ6**から始めるのがおすすめです。弾性軌道はAbaqusを使う**シリーズ1**、またはAnsysを使う**シリーズ3**を選び、その後に**シリーズ5・7・8**の車両・軌道・橋梁モデルへ進めます。応力・ひずみ復元と疲労が目的なら**シリーズ2**を参照してください。これは編集上の学習案であり、先修条件を検証したものではありません。

## テーマ別ガイド

以下は提供された各回の題名を整理したものです。モデル、数値結果、ソフトウェアのバージョン構成が独立に検証済みであることを意味しません。

### シリーズ 1 — Abaqus・Simpackによる鉄道車両・弾性レール・フローティングスラブの連成動力学

- Abaqusによる弾性レールとばね支持フローティングスラブのモデル化、FBI生成
- FTRファイルの作成とSimpackの弾性軌道設定
- 輪軸・台車枠・車両全体のモデル化と車両–フローティングスラブの連成
- TRE／PSD加振、弾性体の変形アニメーション、応答の後処理

### シリーズ 2 — Ansys／Abaqus・Simpack・fe-safeによる弾性体の動的応力・ひずみと疲労解析

- Abaqus／Ansysのインターフェース用データ準備とFBI生成
- Simpackの弾性体設定と応力・ひずみの復元
- Simpack Postによる変形・応力・ひずみの可視化
- fe-safeへのデータ出力、疲労解析、一連の解析手順の事例

### シリーズ 3 — Ansys Workbench Mechanical・APDL・Simpackによる鉄道車両・弾性軌道の動力学解析

- SpaceClaimのレール梁モデルとWorkbench Mechanicalの部分構造縮約
- APDLのGUI・コマンド処理とFBIインターフェース
- FTRの軌道基礎接続と力要素の一括設定
- 簡易車両、TRE／PSD加振、アニメーション、後処理パラメータ

### シリーズ 5 — Abaqus・Simpackによる車両・軌道・橋梁の連成動力学

- レール、CRTS III軌道スラブ、コンクリート層、路盤スラブ、単純支持橋桁
- 材料、メッシュ、締結装置、内部接触、部分構造生成
- FBI／FTR、車両のパラメータ化、静的釣り合い、車両–軌道–橋梁の連成
- 初期荷重、ソルバー設定、軌道不整、動画で扱う動力学評価量

### シリーズ 6 — Simpackによる鉄道車両動力学の入門事例

- 輪軸と台車枠のモデル化
- 車両全体モデルの組立
- TREファイルとPSD加振
- 応答の後処理と解析

### シリーズ 7 — Ansys・Simpackによる車両・軌道・橋梁の連成動力学：Beam–Solidモデル

- RAIL-EULER、rail-timo、ソリッド橋梁モデル、モード関連の内容
- レール・橋梁のFBIファイル、FTR作成と問題の切り分け
- 車両のパラメータ化、連成設定の順序、遷移区間の剛性・減衰
- 初期荷重、求解、加振、橋梁・レールの応答、モデル整理

### シリーズ 8 — Ansys・Simpackによる車両・軌道・橋梁の連成動力学：Beam–Beamモデル

- RAIL-EULER、rail-timo、BEAM188橋梁モデル、モード関連の内容
- FBI／FTR設定、車両のパラメータ化、車両–軌道–橋梁の連成
- レール・橋梁の接続点、接続要素、支承、センサーの一括作成
- 初期荷重、求解、加振、後処理、モデル整理

## ダウンロードと利用

対象シリーズから必要な動画MP4と、同じ回の `.zh-CN.srt` または `.en.srt` をダウンロードします。ファイル名の共通識別子を変えずに保存し、ローカルの動画プレーヤーで字幕ファイルを選択してください。VTT形式も利用できます。リポジトリのcloneやCode → Download ZIPには、Releasesに置かれた動画は含まれません。

ダウンロードの可否はリポジトリの公開設定に従います。privateの間はアクセス権のあるGitHubアカウントが必要です。動画リンクはダウンロード用であり、埋め込み配信プレーヤーを保証するものではありません。

## 言語について

紹介文とテーマ別ガイドは、英語、簡体字中国語、日本語、フランス語、ドイツ語、イタリア語、スペイン語、韓国語で用意しています。文書の多言語化は、字幕や吹き替えの追加を意味しません。現在の字幕言語は中国語と英語です。照合のため元の中国語の題名を保持します。

## 対象範囲と技術上の注意

本プロジェクトは教材ライブラリであり、検証済みベンチマークやソフトウェア配布物ではありません。動画にモデルが登場しても、モデルファイル、ソルバーのライセンス、入力データの配布を意味しません。応用する際は、バージョン、単位、境界条件、減衰、モデル縮約設定、評価基準を確認してください。動画内の過去の規格説明を現行要件として扱わないでください。Beam–SolidとBeam–Beamは教材の分類であり、精度の優劣を証明するものではありません。

字幕の存在やチェックサムの一致だけでは、訳の正確さや音声との同期は確認できません。専門用語は原動画と該当ソフトウェアの文書で確認してください。

## 訂正と協力

訂正は、シリーズ番号、各回の固定識別子、字幕言語、必要に応じてタイムスタンプを添えて報告してください。表示名や訳を修正する際も元の識別子は変更しません。必要な許可のない商用ソフトウェア、ライセンスファイル、第三者教材、モデルは投稿しないでください。

## 出典と利用許諾

リポジトリ管理者、教材の著者、ソフトウェアの権利者は別の立場です。記録された出典と権利状況は出典説明を参照してください。ベンダーの公式認定や推奨は主張しません。公開されていること自体は、教材の無制限な再利用・再配布を許諾するものではありません。

[出典・権利の説明](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/PROVENANCE.md)
