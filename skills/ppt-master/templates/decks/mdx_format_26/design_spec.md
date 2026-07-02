---
deck_id: mdx_format_26
template_id: mdx_format_26
kind: deck
category: brand
summary: Givery Marketing DX '26 brand deck — white canvas with gradient orbs, navy #1D2088 identity, Poppins/Noto Sans JP + Montserrat Givery legacy red, dark thank-you ending.
keywords: [givery, marketing-dx, deca, brand, japanese, navy]
primary_color: "#1D2088"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
source_canvas_width: 960
source_canvas_height: 540
source_viewbox: "0 0 960 540"
page_count: 15
replication_mode: fidelity
placeholders:
  01a_cover_centered: ["{{TITLE}}", "{{UPDATE_DATE}}"]
  01b_cover_client: ["{{CLIENT_NAME}}", "{{TITLE}}", "{{DATE}}"]
  02a_toc_index: ["{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_2_TITLE}}", "{{TOC_ITEM_3_TITLE}}", "{{TOC_ITEM_4_TITLE}}"]
  03a_chapter_light: ["{{SECTION_TITLE}}", "{{SECTION_INDEX}}", "{{PAGE_NUM}}"]
  03b_chapter_section: ["{{CHAPTER_LABEL}}", "{{SECTION_TITLE}}", "{{SECTION_INDEX}}", "{{PAGE_NUM}}"]
  04a_content_text: ["{{TITLE}}", "{{LEAD}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04b_content_emphasis: ["{{EMPHASIS}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04c_content_figure: ["{{TITLE}}", "{{LEAD}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04d_content_right_title: ["{{TITLE}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04e_content_givery: ["{{EN_SUBTITLE}}", "{{TITLE}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04f_content_givery_small: ["{{EN_SUBTITLE}}", "{{TITLE}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04g_content_grid: ["{{TITLE}}", "{{LEAD}}", "{{NOTE}}", "{{CELL_1_TITLE}}", "{{CELL_1_SUB}}", "{{CELL_2_TITLE}}", "{{CELL_2_SUB}}", "{{CELL_3_TITLE}}", "{{CELL_3_SUB}}", "{{PAGE_NUM}}"]
  04h_content_case: ["{{EN_SUBTITLE}}", "{{TITLE}}", "{{LEAD}}", "{{ISSUE_BODY}}", "{{ACTION_BODY}}", "{{PANEL_CAPTION}}", "{{FIGURE}}", "{{NEWS_LINK}}", "{{PAGE_NUM}}"]
  05a_message_hero: ["{{TITLE}}", "{{MESSAGE}}", "{{NOTE}}", "{{PAGE_NUM}}"]
  06a_ending_thanks: ["{{THANKS}}", "{{SUBTEXT}}", "{{CONTACT}}"]
---

# MDX Format '26 (Givery Marketing DX) — Design Specification

Source of truth: `projects/【編集中｜マスタ】MDX_資料フォーマット'26.pptx` **v1.1**（マスターフッター表記、59 slides / 37 layouts）。960×540 実測ジオメトリを ×1.3333 で 1280×720 へ正規化。

## I. Template Overview

- **Use cases**: Givery / DECA Marketing DX の提案書、会社・部門紹介、プロジェクト事例、クライアント向け資料。日本語ファーストのビジネス資料。
- **Design tone**: クリーンで明るいコーポレートモダン。余白広め、構造色はネイビー1色、装飾はコーナーのグラデーションオーブのみ。
- **Theme mode**: mixed — 本文・表紙・目次・中表紙はライト（白キャンバス）、エンディングのみダーク（黒系オーブ背景）。**黒背景の中表紙は v1.1 に存在しない**（旧テンプレの 03b_chapter_dark は誤抽出のため廃止）。
- **At a glance**: 白地に淡いピンク/ブルー/パープルのオーブ、薄い巨大「X」ウォーターマーク、コーナーの X DECA / Givery マーク。タイトル・タブ・フッター・ページバッジは深いインディゴ `#1D2088`。ギブリーフォーマット系ページのみ Montserrat＋レガシー赤 `#C60000` の別人格を持つ。

## II. Color Scheme

11色ブランドパレット厳守 — **新しい色を作らない**（資料作成の掟 5）。

| Role | HEX | Application |
|------|-----|-------------|
| Primary (dk1) | `#1D2088` | タイトル、タブ、フッター、Page ピル、Index ピル、グリッドカード（25%不透明） |
| Secondary (dk2) | `#00A0E9` | コンテンツページ左端タブ、アイコンパーツの枠線 |
| Light bg (lt1) | `#FFFFFF` | ページキャンバス、ダーク上のテキスト |
| Panel (lt2) | `#EDEDF3` | 補足カード・スコープ説明カードの塗り |
| accent1 | `#E4007F` | 図式エリアの破線枠、グリッドの ✕ コネクタ |
| accent2 | `#F94549` | 作業用ラベル（テンプレでは未使用・予約） |
| accent3 | `#A81B8D` | 予約 |
| accent4 | `#FFD100` | 予約 |
| accent5 | `#6ABF4B` | 予約 |
| accent6 | `#06C755` | 予約 |
| hlink | `#0097A7` | 目次の未到達章（下線）、ニュースリンク、外部リンク |
| legacy red | `#C60000` | ギブリーフォーマット系: EN サブタイトル・赤ページ番号・事例リード強調・課題/施策ラベル |
| case band | `#EFEFEF` | 事例フォーマットのグレー帯 |

**Typography**: 表示タイトル `"Poppins ExtraBold", "Noto Sans JP", sans-serif`／ブランドロックアップ・フッター `Poppins, "Noto Sans JP", sans-serif`／本文 `"Noto Sans JP", sans-serif`／ギブリーフォーマット系のみ `Montserrat, "Noto Sans JP", Arial, sans-serif`。Poppins / Montserrat / Noto Sans JP は非プリインストールのため sans-serif フォールバック前提。

## III. Signature Design Elements

- **オーブ背景**: 白地＋コーナーのぼかしオーブ＋X ウォーターマークは背景 PNG に焼き込み済み — ベクターで描き直さない。ページ型ごとに専用 PNG（`assets/*_bg.png`）を全面配置する。
- **ネイビーエッジタブ（表紙①）**: 縦中央で左右からブリードする 2 本の `#1D2088` 矩形がタイトルを挟む。
- **中央ロックアップ**: 「Marketing DX / powered by Givery」＋短いネイビー下線。表紙 2 種に登場。
- **フッターロックアップ**: 左下「© 2026 Givery, Inc」＋2px 下線。ページ型により Poppins ネイビー（標準）、白（図主体）、黒 Noto（ギブリー系）の 3 態。
- **Page バッジ**: 右下。標準＝ネイビー角丸ピル＋白字、右寄せ/メッセージ型＝白ピル＋ネイビー字、図主体＝小型ネイビーピル、ギブリー系＝裸の赤数字 32px。
- **Index ピル（中表紙）**: 中央のネイビー角丸ピル「Index｜NN」を 2 本の水平ルールが挟む。セクション細分は「Index｜NN - n」。
- **図式エリア**: 白 25% 矩形＋ **4px ピンク `#E4007F` 破線**（`stroke-dasharray 5.33`）＋中央の額縁アイコン（`assets/figure_placeholder.png`）。全コンテンツ型で共通。
- **グリッドカード**: `#1D2088` 25%不透明・角丸 12px の等幅 3 カード（01/02/03 ナンバリング）、カード間はピンクの ✕ コネクタ。（旧テンプレの `#EDEDF3` カードは v1.0 時代の誤り）
- **事例フォーマット**: タイトル下に全幅 `#EFEFEF` 帯、赤強調 2 行リード、`#C60000` 五角形ラベル（課題･要件／施策）、右側の白パネル＋イタリック説明、右下シアンのニュースリンク。
- **Margins**: コンテンツ左右 ≈96–100px、ヘッダー基線 ≈55–185px（型により 3 段階）、フッター帯 ≈657–707px。

## IV. Page Roster

視覚忠実度: 表紙/中表紙/エンディング＝**literal**、コンテンツ＝fidelity。クラスタは v1.1 の実スライド。

| File | Cluster source | Description |
|------|----------------|-------------|
| `01a_cover_centered.svg` | slide1/4 + layout1 | 表紙①: オーブ背景全面、ネイビーエッジタブ、中央タイトル＋ロックアップ、日付フッター。 |
| `01b_cover_client.svg` | slide5 + layout37 | 表紙②: クライアント宛 — 「○○御中」＋左寄せ大タイトル、日付フッター。 |
| `02a_toc_index.svg` | slide2/30 + layout2 | 目次: 大「Index」＋目次、章リスト（現在章＝黒 / 未到達章＝シアン下線）。 |
| `03a_chapter_light.svg` | slide6/43 + layout3 | 中表紙: 中央タイトル＋ネイビー「Index｜NN」ピル。 |
| `03b_chapter_section.svg` | slide7 + layout33 | 中表紙＋セクション: 章ラベル小＋セクションタイトル大＋「Index｜NN - n」ピル。 |
| `04a_content_text.svg` | slide8–10 + layout4–6 | テキスト主体: タイトル＋強調 2 行リード＋補足 3 行＋下部図式エリア。 |
| `04b_content_emphasis.svg` | slide3/11/52 + layout7 | １行の強調タイトル: 53px 強調 1 行＋大型図式エリア。 |
| `04c_content_figure.svg` | slide12–17 + layout8–13 | 図･イラスト主体: 小タイトル＋リード＋小補足＋最大級の図式エリア。 |
| `04d_content_right_title.svg` | slide19–23 + layout15–19 | 右寄せページタイトル: 右上ネイビーブロック＋右寄せタイトル＋図式エリア。 |
| `04e_content_givery.svg` | slide24–26 + layout20–22 | ギブリーフォーマット: 赤 EN サブタイトル＋Montserrat 44px タイトル＋右上 Givery ロゴ＋赤ページ番号。 |
| `04f_content_givery_small.svg` | slide27–29 + layout23–25 | ギブリーフォーマット（タイトル小）: 29px タイトル版。 |
| `04g_content_grid.svg` | slide50/51 (+layout4 chrome) | 3 カードグリッド: navy25% 角丸カード ×3（01/02/03）＋ピンク ✕ コネクタ。 |
| `04h_content_case.svg` | slide38–40/53–55 (+layout25 chrome) | プロジェクト事例: グレー帯＋赤強調リード＋課題/施策＋右白パネル＋ニュースリンク。 |
| `05a_message_hero.svg` | slide18/31 + layout14 | 大メッセージ: 右寄せタイトル＋中央 42px メッセージ 2 行＋補足。 |
| `06a_ending_thanks.svg` | layout34 (unused by sample slides) | エンディング: **ダーク**オーブ背景＋Givery 白ロゴ＋サンクス＋白い DECA 検索ピル＋連絡先。v1.1 ではレイアウトのみに存在（スライド未使用）だが公式チュートリアルの締めページとして収録。 |

## V. Assets

`assets/` 直下＝背景・ブランドチェーム（意味名）、`assets/icons/` ＝公式アイコンパーツ、`assets/logos/services/` ＝サービスロゴ。クライアントロゴ（KIRIN・名鉄等）と slide58 のフリー素材アイコンは**非公式のため非収録**（掟 3「アイコンはフリー素材を使わず」）。

| File | Source (v1.1) | Usage |
|------|--------------|-------|
| `cover_bg.png` | image1 (layout1) | 表紙①背景 |
| `cover_client_bg.png` | image14 (layout37) | 表紙②背景 |
| `toc_bg.png` | image3 (layout2) | 目次背景（左ビジュアル焼き込み） |
| `chapter_bg.png` | image4 (layout3/33) | 中表紙背景 |
| `content_bg.png` | image5 (layout4–6/8/9) | コンテンツ背景（透過オーブオーバーレイ） |
| `emphasis_bg.png` | image6 (layout7) | 1行強調背景 |
| `figure_bg.png` | image7 (layout10–13) | 図主体背景 |
| `message_bg.png` | image8 (layout14) | 大メッセージ背景 |
| `right_title_bg.png` | image9 (layout15–19) | 右寄せタイトル背景 |
| `photo_bg.png` | image11 (layout32) | 予備（薄紫オーブ・全面写真ページ用） |
| `ending_bg.png` | image12 (layout34) | エンディング背景（**ダーク**） |
| `marketing_dx_logo.png` | image2 | 表紙中央ロックアップ上のロゴ |
| `givery_logo.png` | image10 | ギブリーフォーマット右上ロゴ |
| `givery_logo_white.png` | image13 | エンディング用白ロゴ |
| `figure_placeholder.png` | image15 | 図式エリア中央の額縁アイコン |
| `deca_x_mark.png` | image36 | DECA X マーク |
| `icons/official/<group>_NN.png` | slide56 (image53–120, 68点) | 公式アイコンパーツ。group = db / file / chatbot / human / sns / instagram / web / line / mail / data / phone（slide56 のラベル枠に基づく） |
| `icons/misc/misc_NNN.png` | slide57 (image121–201, 81点) | 公式アイコンパーツ（未整理）。番号は source image 番号 |
| `logos/services/service_NNN.png` | slide59 (image259–325, 67点) | 各種サービスロゴ。番号は source image 番号 |

## VI. Placeholder Overrides

`placeholders:` frontmatter が本テンプレの正式ボキャブラリ。日本語ビジネス提案の頁義（クライアント宛表紙、「Index｜NN」中表紙、EN サブタイトル＋JP タイトルのギブリー系ヘッダ、大メッセージ、課題/施策の事例型）が汎用語彙に写像できないための上書き。`{{FIGURE}}` はコメントで位置を示す図式エリア（白 25%＋ピンク破線＋額縁アイコン）を置換する運用。`{{PAGE_NUM}}` は正規どおり。
