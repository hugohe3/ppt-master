/* PPT Master - Strategist confirmation UI
 * Stage 1 confirms the communication contract and the free-design/template
 * choice together. Stage 2 combines the coherent deck solution and production
 * mechanics, then writes the final result.
 * Finite fields use /static/catalogs.json; coordinated design directions seed
 * mode, visual style, color, typography, icons, and generated-image rendering,
 * while template-application prose stays conditional. Final confirm saves the
 * flattened current values to result.json.
 */
(function () {
    "use strict";

    // ---- i18n ------------------------------------------------------------
    var MESSAGES = {
        en: {
            page_title: "PPT Master - Confirm Design",
            topbar_hint: "Answer the open questions, or pick and customize recommendations, then continue.",
            stage_anchors: "Stage 1 · Communication contract",
            stage_final_plan: "Stage 2 · Final plan & production",
            loading: "Loading…",
            load_error: "Could not load the current recommendation stage. The AI must write it before launch.",
            btn_confirm: "Confirm",
            btn_confirm_contract: "Confirm contract & continue →",
            btn_confirm_final_plan: "Confirm final plan →",
            deriving: "Generating the downstream options from your choices…",
            template_selection_required: "Choose free design or use templates. When using templates, select at least one workspace.",
            connection_lost: "Connection to the confirm server was interrupted; retrying. If this keeps failing, return to the chat for confirmation.",
            confirmed_title: "✓ Confirmed",
            confirmed_hint: "Your choices are saved. You can close this page and return to the chat.",
            lang_toggle_title: "Switch language",
            sec_template_choice: "Design basis",
            template_choice_hint: "Choose how this deck should establish its design system.",
            template_free_title: "Design from the current content",
            template_free_desc: "Use no reusable template workspace. The Strategist will derive the visual system from this project.",
            template_use_title: "Use templates",
            template_use_desc: "Select one or more reusable Brand, Style, Layout, Deck, or specified workspaces.",
            sec_template_library: "Template combination",
            template_library_hint: "Choose at most one registered template for each type. Brand, Style, Layout, and Deck can be combined.",
            sec_template_explicit: "Specified templates",
            template_explicit_hint: "Choose at most one exact workspace supplied for this run. Its source path is shown for verification.",
            template_kind_brand: "Brand",
            template_kind_style: "Style",
            template_kind_layout: "Layout",
            template_kind_deck: "Deck",
            template_source_library: "Library",
            template_source_explicit: "Specified path",
            template_source_path: "Source path",
            template_select_none: "None",
            template_none_registered: "No registered templates",
            template_none_explicit: "No specified templates for this run",
            sec_canvas: "Canvas format",
            sec_pages: "Page count",
            sec_audience: "Target audience",
            sec_communication: "What this presentation must accomplish",
            sec_delivery: "How it will be used and what must remain",
            sec_narrative: "Narrative direction",
            sec_visual: "Visual direction",
            sec_color: "Color scheme",
            sec_icons: "Icon usage",
            sec_type: "Typography",
            sec_images: "Image usage",
            sec_image_production: "Image production",
            sec_proactive_execution: "Proactive execution",
            sec_mode: "Generation mode",
            sec_refine: "Review the Design Spec first",
            sec_design_directions: "Coherent design directions",
            design_directions_hint: "Choose a complete direction first, then fine-tune the projected fields below. Clicking a direction again restores its authored bundle.",
            direction_active: "Applied",
            direction_adjusted: "Adjusted",
            direction_reset_hint: "Click to apply or restore this complete direction.",
            scheme_component_options: "Project-specific custom choices · select a card to edit",
            sec_template_application: "Template application",
            template_application_hint: "The AI recommends how to apply the installed template to this deck. Revise the plan directly in natural language.",
            placeholder_template_application: "Describe which template pages or prototypes to use, skip, repeat, or reorder; what must stay; and what may be replaced or reorganized.",
            sub_mode: "Narrative mode",
            sub_visual: "Visual style",
            sub_divergence: "Material divergence (how freely to reshape vs. stay close to the source)",
            placeholder_divergence: "In your words — e.g. \"stick closely to the document\" / \"freely restructure and expand within the source\". Leave blank for a balanced default.",
            communication_intent: "What should this presentation accomplish?",
            communication_intent_hint: "Open answer — combine any that apply: inform, explain, persuade, decide, align, teach, report/account, mobilize, or leave a record/hand-off. Describe priority or sequence when useful; do not choose labels.",
            placeholder_communication_intent: "e.g. Report progress and surface risk first, then secure a decision on the next investment.",
            audience_outcome: "Desired audience outcome / success condition",
            placeholder_audience_outcome: "What should the audience know, understand, believe, decide, or do afterward?",
            core_message: "Core message / decision ask / action",
            placeholder_core_message: "Which claims, requests, or actions must land even if little else is remembered?",
            delivery_context: "Delivery context (name the primary)",
            delivery_context_hint: "Distinguish presenter-led, reader-led, hybrid, or recorded/self-running. For hybrid use, state which mode leads and what secondary use must still work.",
            placeholder_delivery_context: "e.g. Primary: presenter-led 20-minute leadership review. Secondary: reader-led approval copy shared afterward.",
            artifact_afterlife: "Artifact afterlife",
            placeholder_artifact_afterlife: "e.g. approval, review, audit, archive, hand-off, or reuse; leave blank when no later use is expected.",
            stage1_current_value_hint: "Editable fields contain recommendations. Keep, revise, or clear them; confirmation saves the current text exactly, including blank values.",
            content_divergence_locked_hint: "This profile preserves the source wording and page structure, so this field is fixed.",
            custom: "Custom",
            custom_placeholder: "Type your own…",
            ai_custom_candidate: "AI custom proposal",
            ai_custom_candidate_hint: "Always visible for comparison. It is not selected by default; select it to edit.",
            custom_behavior_required: "The selected AI custom proposal cannot be blank.",
            custom_color_required: "Describe the custom color scheme before continuing.",
            design_system_required: "Choose a complete palette and typography system before continuing.",
            mode_behavior_placeholder: "Describe the act sequence, title voice, page rhythm, and presentation posture.",
            visual_style_behavior_placeholder: "Describe shape language, composition, decoration density, whitespace, typography character, and texture.",
            recommended: "Recommended",
            placeholder_audience: "Who is this deck for?",
            placeholder_pages: "e.g. 12-15",
            hex_override: "Custom HEX override:",
            formula_policy: "Formula rendering policy",
            image_ai_path: "AI image source",
            image_strategy: "Generated image style",
            image_strategy_empty: "No preset style references are available. You can still use a custom style.",
            image_strategy_required: "Choose a generated-image preset or describe a custom style.",
            image_strategy_invalid: "The selected generated-image preset is not available.",
            image_strategy_select_placeholder: "Choose a generated-image preset…",
            image_strategy_recommended_group: "Recommended for this deck",
            image_strategy_all_group: "All preset styles",
            image_strategy_rendering: "Rendering",
            image_strategy_visual: "Visual",
            image_strategy_mood: "Mood",
            image_strategy_ai_custom: "AI custom proposal",
            image_strategy_ai_custom_desc: "A novel or multi-reference rendering proposal. Select it to edit.",
            image_strategy_custom_placeholder: "Describe the exact generated-image direction, subjects, composition, style cues, or things to avoid.",
            image_strategy_reference_hint: "Reference images show rendering only. Final AI images inherit the deck color scheme selected above.",
            image_strategy_no_reference: "No reference image for this custom choice.",
            image_source_summary: "Selected image sources",
            image_production_hint: "Image sources and rendering are selected above. Resolve only the production path here.",
            image_usage_notes: "Additional image requirements",
            image_usage_notes_placeholder: "e.g. realistic handwashing scenes; avoid cartoon germs; keep product photos untouched.",
            image_usage_required: "Select at least one image usage option.",
            image_usage_none_exclusive: "No images cannot be combined with other image options.",
            proactive_execution_hint: "These defaults apply only when you have not explicitly instructed otherwise. Your latest explicit instruction always takes priority.",
            proactive_speaker_notes: "Proactively generate speaker notes",
            proactive_speaker_notes_desc: "On by default. The agent generates speaker notes without a separate request.",
            proactive_custom_animations: "Proactively create custom animations",
            proactive_custom_animations_desc: "Off by default. Strategist motion suggestions remain available; turn this on to have the agent create custom animations without a separate request.",
            proactive_narration_audio: "Proactively generate narration audio",
            proactive_narration_audio_desc: "Off by default. This raw choice does not rewrite the speaker-notes toggle; the Strategist resolves narration's effective notes dependency in the Design Spec.",
            font_heading: "Heading",
            font_body: "Body",
            font_selection: "Font selection",
            primary_language_font: "Primary-language font",
            english_font: "English font",
            font_picker_hint: "Choosing a recommendation fills these selectors. Changing any font marks the typography as customized.",
            other_installed_font: "Other installed font…",
            other_font_placeholder: "Exact installed font name",
            customized: "Customized",
            font_body_size: "Body baseline size",
            font_body_size_hint: "All type sizes derive from this body baseline.",
            body_size_unit_relation: "SVG px to PPT pt: 1px = 0.75pt.",
            body_size_pt_hint: "Approximately {pt} pt (1px = 0.75pt; saved as px).",
            role_size_pt_hint: "≈ {pt} pt",
            body_size_hint_canvas: "This canvas suggests ~{lo}–{hi}px (scales with canvas height).",
            body_size_hint_purpose: "This reading mode recommends {def}px — one fixed size, not a range.",
            body_size_hint_oor: "(Current value is outside the usual range for this canvas — check the unit is right and that it fits.)",
            delivery_purpose: "Reading mode",
            delivery_purpose_hint: "Choose where the meaning lives: read-close decks explain themselves with complete sentences and detail; presenter-led decks use one idea, concise claims, and visual evidence.",
            size_override: "Per-role size override:",
            size_role_title: "title",
            size_role_subtitle: "subtitle",
            size_role_annotation: "annotation",
            custom_typography: "Custom typography",
            custom_color: "Custom color",
            custom_color_placeholder: "Describe your colors in words, e.g. deep navy primary, warm orange accent, white background — or paste HEX values…",
            role_background: "bg",
            role_secondary_bg: "2nd bg",
            role_primary: "primary",
            role_accent: "accent",
            role_secondary_accent: "2nd accent",
            role_body_text: "body text",
            cjk: "CJK",
            latin: "Latin",
            sample_heading_cjk: "主题方案标题",
            sample_heading_latin: "Presentation Title",
            sample_body_cjk: "关键信息摘要",
            sample_body_latin: "Key message summary",
            style_preview_label: "Overall impression (color + typography + icons)",
            style_preview_body: "· rough feel only, not the actual slide layout",
            no_icons: "No icons",
            preview_big_title: "Big Title",
            preview_section_title: "Section Title",
            preview_latin_title: "Section Title",
            preview_body_intro: "Body copy shows the baseline text rhythm and contrast.",
            preview_latin_body: "Body text sample for checking Latin typography.",
            preview_point_1_title: "Body content",
            preview_point_1_text: "Use this area to judge paragraph density and line spacing.",
            preview_point_2_title: "Key point",
            preview_point_2_text: "Icons are placed next to real text instead of floating alone.",
            preview_point_3_title: "Conclusion",
            preview_point_3_text: "The combination should stay readable at presentation scale.",
            mode_continuous_desc: "Generate the whole deck in one pass.",
            mode_split_desc: "Stop after the spec; resume SVG generation in a fresh window.",
            refine_off_desc: "Write the Design Spec and execution lock in sequence, then auto-proceed.",
            refine_on_desc: "Stop after the Design Spec. Revise any part in chat; approval then creates the execution lock and continues generation.",
            off_default: "Off",
            on: "On",
            option_prefix: "Option",
            error_retry: "Error - retry"
        },
        ja: {
            page_title: "PPT Master - デザイン確認",
            topbar_hint: "自由記述の質問に答えるか、提案を選択・調整して次へ進んでください。",
            stage_anchors: "ステージ 1 · コミュニケーション契約",
            stage_final_plan: "ステージ 2 · 最終プランと制作",
            loading: "読み込み中…",
            load_error: "現在の推奨ステージを読み込めませんでした。起動前にAIが書き込む必要があります。",
            btn_confirm: "確定",
            btn_confirm_contract: "契約内容を確定して次へ →",
            btn_confirm_final_plan: "最終プランを確定 →",
            deriving: "選択内容をもとに後続の選択肢を生成しています…",
            template_selection_required: "自由デザインまたはテンプレート利用を選んでください。テンプレート利用時は、1つ以上のワークスペースを選択してください。",
            connection_lost: "確認ページのサーバー接続が中断されました。再試行しています。失敗が続く場合はチャットで確認してください。",
            confirmed_title: "✓ 確定しました",
            confirmed_hint: "選択内容を保存しました。このページを閉じてチャットに戻ってください。",
            lang_toggle_title: "言語を切り替え",
            sec_template_choice: "デザインの基準",
            template_choice_hint: "この資料のデザインシステムをどう決めるか選択します。",
            template_free_title: "現在の内容からデザインする",
            template_free_desc: "再利用テンプレートを使わず、Strategist がこのプロジェクトからビジュアルシステムを組み立てます。",
            template_use_title: "テンプレートを使用",
            template_use_desc: "Brand、Style、Layout、Deck、または指定ワークスペースから1つ以上選択します。",
            sec_template_library: "テンプレートの組み合わせ",
            template_library_hint: "登録済みテンプレートは種類ごとに1件まで選択でき、Brand、Style、Layout、Deck を組み合わせられます。",
            sec_template_explicit: "指定テンプレート",
            template_explicit_hint: "この実行で指定された正確なワークスペースを1件まで選択できます。確認用に参照元パスを表示します。",
            template_kind_brand: "Brand",
            template_kind_style: "Style",
            template_kind_layout: "Layout",
            template_kind_deck: "Deck",
            template_source_library: "ライブラリ",
            template_source_explicit: "指定パス",
            template_source_path: "参照元パス",
            template_select_none: "なし",
            template_none_registered: "登録済みテンプレートはありません",
            template_none_explicit: "この実行で指定されたテンプレートはありません",
            sec_canvas: "キャンバス形式",
            sec_pages: "ページ数",
            sec_audience: "想定読者",
            sec_communication: "このプレゼンで何を実現するか",
            sec_delivery: "どう使い、何を残すか",
            sec_narrative: "ナラティブ方針",
            sec_visual: "ビジュアル方針",
            sec_color: "配色",
            sec_icons: "アイコンの使用",
            sec_type: "タイポグラフィ",
            sec_images: "画像の使用",
            sec_image_production: "画像制作",
            sec_proactive_execution: "能動的な実行",
            sec_mode: "生成モード",
            sec_refine: "先に設計仕様を確認",
            sec_design_directions: "統合デザイン方針",
            design_directions_hint: "まず全体案を選び、その下に反映された各項目を微調整します。同じ全体案をもう一度押すと、元の組み合わせに戻ります。",
            direction_active: "適用中",
            direction_adjusted: "調整済み",
            direction_reset_hint: "クリックすると、この全体案を適用または元の状態に戻します。",
            scheme_component_options: "プロジェクト専用カスタム案 · カードを選んで編集",
            sec_template_application: "テンプレートの適用方法",
            template_application_hint: "AIが現在の内容に合わせたテンプレートの使い方を提案します。自然言語で直接修正できます。",
            placeholder_template_application: "使用・省略・反復・並べ替えするページやプロトタイプ、保持する要素、差し替え・再構成できる内容を記述します。",
            sub_mode: "ナラティブモード",
            sub_visual: "ビジュアルスタイル",
            sub_divergence: "素材からの発散度（どこまで自由に再構成するか、原文に忠実か）",
            placeholder_divergence: "自分の言葉でどうぞ — 例：「文書に忠実に」「元素材の範囲内で自由に再構成・展開」。空欄ならバランス型になります。",
            communication_intent: "このプレゼンで何を実現したいですか？",
            communication_intent_hint: "自由記述です。情報共有・説明・説得・意思決定・合意形成・教育・報告と説明責任・行動喚起・記録と引き継ぎを必要に応じて組み合わせ、必要なら優先順位や順序も書いてください。ラベルを選ぶ必要はありません。",
            placeholder_communication_intent: "例：まず進捗とリスクを報告し、そのうえで次の投資判断を得る。",
            audience_outcome: "聴衆に期待する変化・成功条件",
            placeholder_audience_outcome: "終了後、聴衆は何を知り、理解し、信じ、決め、行動できる状態になるべきですか？",
            core_message: "中核メッセージ／意思決定の依頼／行動",
            placeholder_core_message: "ほかの内容が忘れられても、必ず残すべき主張・依頼・行動は何ですか？",
            delivery_context: "利用状況（主モードを明記）",
            delivery_context_hint: "発表者主導、読者主導、ハイブリッド、録画／自動再生を区別してください。ハイブリッドでは主モードと、維持すべき副用途を明記します。",
            placeholder_delivery_context: "例：主は発表者付き20分の経営レビュー。副は会議後に単独で読む承認資料。",
            artifact_afterlife: "資料の利用後",
            placeholder_artifact_afterlife: "例：承認、レビュー、監査、保管、引き継ぎ、再利用。後続利用がなければ空欄で構いません。",
            stage1_current_value_hint: "編集可能な欄には提案が入っています。そのまま使う・修正する・空にすることができ、確定時の現在値を空欄も含めてそのまま保存します。",
            content_divergence_locked_hint: "このプロファイルは原文とページ構成を保持するため、この項目は固定されています。",
            custom: "カスタム",
            custom_placeholder: "自由に入力…",
            ai_custom_candidate: "AIカスタム案",
            ai_custom_candidate_hint: "比較できるよう常に全文を表示します。初期選択はされず、選択後に編集できます。",
            custom_behavior_required: "選択したAIカスタム案を空欄にはできません。",
            custom_color_required: "続行する前に、カスタム配色の説明を入力してください。",
            design_system_required: "続行する前に、完全な配色と書体システムを選択してください。",
            mode_behavior_placeholder: "構成の流れ、タイトルの語り口、ページのリズム、表現姿勢を記述します。",
            visual_style_behavior_placeholder: "形状言語、構図、装飾密度、余白、書体の性格、質感を記述します。",
            recommended: "おすすめ",
            placeholder_audience: "この資料は誰に向けたもの？",
            placeholder_pages: "例：12-15",
            hex_override: "カスタムHEXで上書き：",
            formula_policy: "数式レンダリング方針",
            image_ai_path: "AI画像の生成元",
            image_strategy: "生成画像のスタイル",
            image_strategy_empty: "プリセットのスタイル見本を利用できません。カスタムスタイルは引き続き使用できます。",
            image_strategy_required: "生成画像のプリセットを選ぶか、カスタムスタイルを記述してください。",
            image_strategy_invalid: "選択した生成画像プリセットは利用できません。",
            image_strategy_select_placeholder: "生成画像のプリセットを選択…",
            image_strategy_recommended_group: "この資料へのおすすめ",
            image_strategy_all_group: "すべてのプリセットスタイル",
            image_strategy_rendering: "レンダリング",
            image_strategy_visual: "ビジュアル",
            image_strategy_mood: "ムード",
            image_strategy_ai_custom: "AIカスタム案",
            image_strategy_ai_custom_desc: "新規または複数の既存表現を統合したレンダリング案です。選択後に編集できます。",
            image_strategy_custom_placeholder: "生成画像の方向性、被写体、構図、スタイル要素、避けたい要素を具体的に入力してください。",
            image_strategy_reference_hint: "参照画像はレンダリングのみを示します。最終AI画像の色は上で選んだデッキ配色を継承します。",
            image_strategy_no_reference: "このカスタム選択には参照画像がありません。",
            image_source_summary: "選択中の画像ソース",
            image_production_hint: "画像ソースとレンダリングは上で選択済みです。ここでは制作経路だけを決めます。",
            image_usage_notes: "画像に関する補足要件",
            image_usage_notes_placeholder: "例：リアルな手洗いシーンを優先、漫画調の菌のイラストは避ける、製品写真はそのまま使う。",
            image_usage_required: "画像の使用方法を少なくとも1つ選択してください。",
            image_usage_none_exclusive: "「画像なし」は他の画像オプションと同時に選択できません。",
            proactive_execution_hint: "これらの初期設定は、明示的な指示がない場合にのみ適用されます。最新の明示的な指示が常に優先されます。",
            proactive_speaker_notes: "発表者ノートを能動的に生成",
            proactive_speaker_notes_desc: "初期設定はオンです。個別の依頼がなくても発表者ノートを生成します。",
            proactive_custom_animations: "カスタムアニメーションを能動的に作成",
            proactive_custom_animations_desc: "初期設定はオフです。ストラテジストの動きの提案は維持され、オンにすると個別の依頼がなくてもカスタムアニメーションを作成します。",
            proactive_narration_audio: "ナレーション音声を能動的に生成",
            proactive_narration_audio_desc: "初期設定はオフです。この選択は発表者ノートの設定を書き換えません。ナレーションに必要なノートの有効状態は、ストラテジストが設計仕様で解決します。",
            font_heading: "見出し",
            font_body: "本文",
            font_selection: "フォント選択",
            primary_language_font: "主要言語のフォント",
            english_font: "英語フォント",
            font_picker_hint: "提案を選ぶと下の選択欄に反映されます。いずれかのフォントを変更するとカスタマイズ済みになります。",
            other_installed_font: "その他のインストール済みフォント…",
            other_font_placeholder: "インストール済みフォントの正確な名前",
            customized: "カスタマイズ済み",
            font_body_size: "本文の基準サイズ",
            font_body_size_hint: "すべての文字サイズはこの本文基準から導出されます。",
            body_size_unit_relation: "SVG px と PPT pt の換算：1px = 0.75pt。",
            body_size_pt_hint: "約 {pt} pt（1px = 0.75pt 換算、保存は px）。",
            role_size_pt_hint: "約 {pt} pt",
            body_size_hint_canvas: "このキャンバスの目安は約{lo}–{hi}px（キャンバスの高さに応じて変化）。",
            body_size_hint_purpose: "この閲覧モードの推奨は{def}px — 範囲ではなく固定値です。",
            body_size_hint_oor: "（現在の値はこのキャンバスの通常範囲外です — 単位とサイズ感を確認してください。）",
            delivery_purpose: "閲覧モード",
            delivery_purpose_hint: "情報を主にページと話者のどちらに担わせるかを決めます。近距離閲覧は完全な文と細部で自立させ、プレゼン型は1枚1メッセージで短い主張と視覚的根拠を中心にします。",
            size_override: "役割ごとのサイズ上書き：",
            size_role_title: "タイトル",
            size_role_subtitle: "サブタイトル",
            size_role_annotation: "注釈",
            custom_typography: "カスタムタイポグラフィ",
            custom_color: "カスタム配色",
            custom_color_placeholder: "配色を言葉で説明 — 例：濃紺をメインに暖色オレンジのアクセント、背景は白 — またはHEX値を貼り付け…",
            role_background: "背景",
            role_secondary_bg: "第2背景",
            role_primary: "メイン",
            role_accent: "アクセント",
            role_secondary_accent: "第2アクセント",
            role_body_text: "本文文字",
            cjk: "和文",
            latin: "欧文",
            sample_heading_cjk: "プレゼンテーションの表題",
            sample_heading_latin: "Presentation Title",
            sample_body_cjk: "キーメッセージの要約",
            sample_body_latin: "Key message summary",
            style_preview_label: "全体の印象（配色 + タイポグラフィ + アイコン）",
            style_preview_body: "· 雰囲気の確認用で、実際のレイアウトではありません",
            no_icons: "アイコンなし",
            preview_big_title: "大見出し",
            preview_section_title: "章タイトル",
            preview_latin_title: "Section Title",
            preview_body_intro: "本文の基準サイズとコントラストを確認するための文です。",
            preview_latin_body: "Body text sample for checking Latin typography.",
            preview_point_1_title: "本文内容",
            preview_point_1_text: "段落密度と行間の見え方をここで確認します。",
            preview_point_2_title: "要点説明",
            preview_point_2_text: "アイコンは単独ではなく、実際の文章の横に配置します。",
            preview_point_3_title: "結論・提案",
            preview_point_3_text: "投影時にも読みやすい組み合わせかを判断します。",
            mode_continuous_desc: "デッキ全体を一気に生成します。",
            mode_split_desc: "設計仕様の作成後に停止し、別ウィンドウでSVG生成を再開します。",
            refine_off_desc: "設計仕様と実行ロックを順番に作成し、そのまま自動で進みます。",
            refine_on_desc: "設計仕様の作成後に停止します。チャットで任意の箇所を修正し、承認後に実行ロックを作成して生成を続けます。",
            off_default: "オフ",
            on: "オン",
            option_prefix: "案",
            error_retry: "エラー - 再試行"
        },
        zh: {
            page_title: "确认设计方案",
            topbar_hint: "回答开放问题，或选择并调整推荐项，然后继续。",
            stage_anchors: "第一阶段 · 沟通契约",
            stage_final_plan: "第二阶段 · 最终方案与制作",
            loading: "加载中…",
            load_error: "无法加载推荐文件，需在启动前写入。",
            btn_confirm: "确认",
            btn_confirm_contract: "确认沟通契约并继续 →",
            btn_confirm_final_plan: "确认最终方案 →",
            deriving: "正在根据你的选择生成下游选项…",
            template_selection_required: "请选择自由设计或使用模板；选择使用模板时，至少选择一个工作区。",
            connection_lost: "确认页服务连接中断，正在重试；如果持续失败，请回到聊天窗口走聊天确认。",
            confirmed_title: "✓ 已确认",
            confirmed_hint: "选择已保存，可关闭此页并回到聊天窗口。",
            lang_toggle_title: "切换语言",
            sec_template_choice: "设计基础",
            template_choice_hint: "选择这份演示文稿如何建立设计系统。",
            template_free_title: "根据当前内容从零设计",
            template_free_desc: "不使用可复用模板工作区，由 Strategist 根据当前项目推导视觉系统。",
            template_use_title: "使用模板",
            template_use_desc: "选择一个或多个 Brand、Style、Layout、Deck 或指定工作区。",
            sec_template_library: "模板组合",
            template_library_hint: "每种已注册模板最多选择一个；Brand、Style、Layout、Deck 可以组合使用。",
            sec_template_explicit: "指定模板",
            template_explicit_hint: "本次运行明确提供的精确工作区最多选择一个；显示来源路径供你核对。",
            template_kind_brand: "Brand",
            template_kind_style: "Style",
            template_kind_layout: "Layout",
            template_kind_deck: "Deck",
            template_source_library: "模板库",
            template_source_explicit: "指定地址",
            template_source_path: "来源路径",
            template_select_none: "无",
            template_none_registered: "暂无已注册模板",
            template_none_explicit: "本次运行没有指定模板",
            sec_canvas: "画布格式",
            sec_pages: "页数",
            sec_audience: "目标受众",
            sec_communication: "这份演示要完成什么",
            sec_delivery: "如何使用、之后留下什么",
            sec_narrative: "叙事方向",
            sec_visual: "视觉方向",
            sec_color: "色彩方案",
            sec_icons: "图标使用",
            sec_type: "字体方案",
            sec_images: "图片使用",
            sec_image_production: "图片生产",
            sec_proactive_execution: "主动执行",
            sec_mode: "生成模式",
            sec_refine: "先审核设计规范",
            sec_design_directions: "成套设计方向",
            design_directions_hint: "先选择一套完整方案，再在下方微调各项；再次点击同一方案会恢复它原本的整套预设。",
            direction_active: "已应用",
            direction_adjusted: "已调整",
            direction_reset_hint: "点击可应用或恢复这套完整方案。",
            scheme_component_options: "项目专属自定义方案 · 选中卡片后可编辑",
            sec_template_application: "模板应用方式",
            template_application_hint: "AI 会根据当前内容推荐如何使用已安装模板；你可以直接用自然语言修改。",
            placeholder_template_application: "说明使用、跳过、重复或重排哪些模板页面/原型，哪些内容必须保留，哪些可以替换或重组。",
            sub_mode: "叙事模式",
            sub_visual: "视觉风格",
            sub_divergence: "材料发散度（多大程度重塑，还是贴近源材料）",
            placeholder_divergence: "用你自己的话写，例如「严格贴着文档来」/「在源材料范围内自由重组并展开」。留空则按平衡处理。",
            communication_intent: "这份演示文稿需要完成什么？",
            communication_intent_hint: "开放回答，可按需组合：告知、解释、说服、决策、对齐、教学、汇报与问责、动员、留档与交接。必要时说明主次或先后，不需要选择标签。",
            placeholder_communication_intent: "例如：先汇报进展并暴露风险，再推动管理层决定下一阶段投入。",
            audience_outcome: "期望的受众变化 / 成功条件",
            placeholder_audience_outcome: "结束后，受众应该知道、理解、相信、决定或采取什么行动？",
            core_message: "核心信息 / 决策请求 / 行动",
            placeholder_core_message: "即使其他内容没有被记住，受众至少需要接住哪些主张、请求或行动？",
            delivery_context: "传递场景（明确主要模式）",
            delivery_context_hint: "区分演讲者主导、读者主导、混合、录制/自动播放；混合场景要说明哪一种主导，以及还要兼顾什么次要用途。",
            placeholder_delivery_context: "例如：主要为有主讲的 20 分钟管理层现场评审；次要为会后独立阅读的审批材料。",
            artifact_afterlife: "演示后的成果用途",
            placeholder_artifact_afterlife: "例如：审批、评审、审计、留档、交接或复用；没有后续用途时可留空。",
            stage1_current_value_hint: "可编辑字段中是推荐内容。你可以保留、修改或清空；确认时会按当前内容原样保存，空白也会保持为空。",
            content_divergence_locked_hint: "当前流程要求原文和页面结构保持不变，因此该字段已锁定。",
            custom: "自定义",
            custom_placeholder: "输入自定义内容…",
            ai_custom_candidate: "AI 自定义方案",
            ai_custom_candidate_hint: "始终展示完整内容用于比较；默认不选中，选择后可编辑。",
            custom_behavior_required: "已选择的 AI 自定义方案不能为空。",
            custom_color_required: "请先填写自定义配色说明，再继续确认。",
            design_system_required: "请先选择完整的配色与字体方案，再继续确认。",
            mode_behavior_placeholder: "描述叙事阶段、标题语气、页面节奏和表达姿态。",
            visual_style_behavior_placeholder: "描述形状语言、构图、装饰密度、留白、字体气质和纹理。",
            recommended: "推荐",
            placeholder_audience: "这份演示文稿面向谁？",
            placeholder_pages: "如：12-15",
            hex_override: "自定义色值覆盖：",
            formula_policy: "公式渲染策略",
            image_ai_path: "生成配图来源",
            image_strategy: "生成图风格",
            image_strategy_empty: "当前没有可用的预设风格参考，仍可使用自定义风格。",
            image_strategy_required: "请选择一种生成图预设，或填写自定义风格。",
            image_strategy_invalid: "所选生成图预设当前不可用。",
            image_strategy_select_placeholder: "选择生成图预设…",
            image_strategy_recommended_group: "本项目推荐",
            image_strategy_all_group: "全部预设风格",
            image_strategy_rendering: "渲染风格",
            image_strategy_visual: "视觉",
            image_strategy_mood: "情绪",
            image_strategy_ai_custom: "AI 自定义方案",
            image_strategy_ai_custom_desc: "一套全新或综合多个已有风格的渲染方案；选择后可以编辑。",
            image_strategy_custom_placeholder: "描述生成图的具体方向、主体、构图、风格关键词或需要避免的内容。",
            image_strategy_reference_hint: "参考图只展示渲染风格；最终 AI 图片直接继承上方已选的整套 PPT 配色。",
            image_strategy_no_reference: "自定义选择没有参考图。",
            image_source_summary: "已选图片来源",
            image_production_hint: "图片来源和渲染方向已在上方选择；这里仅决定实际生产路径。",
            image_usage_notes: "图片补充要求",
            image_usage_notes_placeholder: "例如：优先真实洗手场景；不要卡通病菌；产品照片保持原样。",
            image_usage_required: "请至少选择一种图片使用方式。",
            image_usage_none_exclusive: "「不使用图片」不能和其它图片选项同时选择。",
            proactive_execution_hint: "这些默认开关只在你没有明确要求时生效；你最新的明确指令始终优先。",
            proactive_speaker_notes: "主动生成演讲者备注",
            proactive_speaker_notes_desc: "默认开启。无需另行要求，Agent 也会生成演讲者备注。",
            proactive_custom_animations: "主动生成自定义动画",
            proactive_custom_animations_desc: "默认关闭。策略师的动画建议仍会保留；开启后，Agent 可在没有另行要求时实际制作自定义动画。",
            proactive_narration_audio: "主动生成旁白音频",
            proactive_narration_audio_desc: "默认关闭。这里保留原始选择，不改写演讲者备注开关；策略师会在设计规范中解析旁白所需的最终备注状态。",
            font_heading: "标题",
            font_body: "正文",
            font_selection: "字体选择",
            primary_language_font: "主要语言字体",
            english_font: "英文字体",
            font_picker_hint: "选择推荐方案会同步下方字体；修改任一下拉或手动字体后会标记为已自定义。",
            other_installed_font: "其他已安装字体…",
            other_font_placeholder: "输入精确的已安装字体名称",
            customized: "已自定义",
            font_body_size: "正文基准字号",
            font_body_size_hint: "所有字号按这个正文基准推导。",
            body_size_unit_relation: "SVG px 与 PPT pt 的换算：1px = 0.75pt。",
            body_size_pt_hint: "约 {pt} pt（按 1px = 0.75pt 换算；提交仍保存 px）。",
            role_size_pt_hint: "约 {pt} pt",
            body_size_hint_canvas: "当前画布建议 ~{lo}–{hi}px（随画布高度缩放）。",
            body_size_hint_purpose: "该阅读模式推荐 {def}px（单一固定值，非区间）。",
            body_size_hint_oor: "（当前数值超出该画布的常用范围——请确认单位无误、是否合适。）",
            delivery_purpose: "阅读模式",
            delivery_purpose_hint: "决定信息主要由页面还是讲者承担：近读型用完整句、短段落和细节自洽；演讲型一页一意，以简短主张和视觉证据为主。",
            size_override: "逐角色字号覆盖：",
            size_role_title: "标题",
            size_role_subtitle: "副标题",
            size_role_annotation: "注释",
            custom_typography: "自定义字体方案",
            custom_color: "自定义配色",
            custom_color_placeholder: "用文字描述配色，如：深蓝主色、暖橙强调、白色背景——或直接粘贴 HEX 值…",
            role_background: "背景",
            role_secondary_bg: "次级背景",
            role_primary: "主色",
            role_accent: "强调",
            role_secondary_accent: "次强调",
            role_body_text: "正文文字",
            cjk: "中文",
            latin: "西文",
            sample_heading_cjk: "主题方案标题",
            sample_heading_latin: "Presentation Title",
            sample_body_cjk: "关键信息摘要",
            sample_body_latin: "Key message summary",
            style_preview_label: "整体形象（配色 + 字体 + 图标）",
            style_preview_body: "· 仅大致形象，非实际版式",
            no_icons: "无图标",
            preview_big_title: "大标题",
            preview_section_title: "章节标题",
            preview_latin_title: "Section Title",
            preview_body_intro: "正文内容用于判断基础字号、行距和颜色对比。",
            preview_latin_body: "Body text sample for checking Latin typography.",
            preview_point_1_title: "正文内容",
            preview_point_1_text: "这里展示普通段落的密度和阅读节奏。",
            preview_point_2_title: "要点说明",
            preview_point_2_text: "图标和文字放在一起，判断真实使用效果。",
            preview_point_3_title: "结论建议",
            preview_point_3_text: "组合效果需要在演示场景下保持清晰可读。",
            mode_continuous_desc: "一次性连续生成整份演示文稿。",
            mode_split_desc: "写完设计规范后停止，另开窗口继续生成页面。",
            refine_off_desc: "依次生成设计规范和执行锁，然后自动继续。",
            refine_on_desc: "生成设计规范后暂停；你可在聊天中修改任何部分，明确确认后再生成执行锁并继续制作。",
            off_default: "关",
            on: "开",
            option_prefix: "方案",
            error_retry: "出错，请重试"
        }
    };

    var LANG = (function () {
        try {
            var stored = window.localStorage.getItem("ppt_lang");
            if (stored === "zh" || stored === "en" || stored === "ja") return stored;
        } catch (e) { /* ignore */ }
        var nav = (navigator.language || navigator.userLanguage || "en").toLowerCase();
        if (nav.indexOf("zh") === 0) return "zh";
        if (nav.indexOf("ja") === 0) return "ja";
        return "en";
    })();

    function t(key) {
        var dict = MESSAGES[LANG] || MESSAGES.en;
        return dict[key] != null ? dict[key] : key;
    }

    // Fallback stays LANG-relative: zh/en users never see Japanese labels,
    // ja pages fall back ja → en → zh.
    var LANG_FALLBACK = { zh: ["zh", "en", "ja"], en: ["en", "zh", "ja"], ja: ["ja", "en", "zh"] };
    var IMAGE_COMPARISON_LABELS = {
        rendering: {
            "vector-illustration": { zh: "矢量插画", en: "Vector illustration", ja: "ベクターイラスト" },
            flat: { zh: "扁平插画", en: "Flat illustration", ja: "フラットイラスト" },
            "3d-isometric": { zh: "3D 等距", en: "3D isometric", ja: "3Dアイソメトリック" },
            "digital-dashboard": { zh: "数字仪表盘", en: "Digital dashboard", ja: "デジタルダッシュボード" },
            "corporate-photo": { zh: "企业摄影", en: "Corporate photo", ja: "企業写真" },
            blueprint: { zh: "蓝图线稿", en: "Blueprint", ja: "ブループリント" },
            editorial: { zh: "编辑杂志", en: "Editorial", ja: "エディトリアル" },
            "sketch-notes": { zh: "手绘笔记", en: "Sketch notes", ja: "スケッチノート" },
            "ink-notes": { zh: "墨线笔记", en: "Ink notes", ja: "インクノート" },
            chalkboard: { zh: "粉笔黑板", en: "Chalkboard", ja: "チョークボード" },
            watercolor: { zh: "水彩", en: "Watercolor", ja: "水彩" },
            "warm-scene": { zh: "暖调场景", en: "Warm scene", ja: "暖色シーン" },
            "screen-print": { zh: "丝网印刷", en: "Screen print", ja: "スクリーンプリント" },
            "fantasy-animation": { zh: "幻想动画", en: "Fantasy animation", ja: "ファンタジーアニメ" },
            "pixel-art": { zh: "像素艺术", en: "Pixel art", ja: "ピクセルアート" },
            nature: { zh: "自然有机", en: "Nature", ja: "自然・オーガニック" },
            "minimalist-swiss": { zh: "瑞士极简", en: "Minimalist Swiss", ja: "スイスミニマル" },
            glassmorphism: { zh: "玻璃拟态", en: "Glassmorphism", ja: "グラスモーフィズム" },
            "vintage-poster": { zh: "复古海报", en: "Vintage poster", ja: "ヴィンテージポスター" },
            "paper-cut": { zh: "剪纸拼贴", en: "Paper cut", ja: "ペーパーカット" }
        }
    };

    function localized(obj, base) {
        if (!obj) return "";
        var langKey = base + "_" + LANG;
        if (obj[langKey] != null) return obj[langKey];
        var order = LANG_FALLBACK[LANG] || LANG_FALLBACK.en;
        var i;
        if (obj[base] != null) {
            if (typeof obj[base] === "object") {
                for (i = 0; i < order.length; i++) {
                    if (obj[base][order[i]]) return obj[base][order[i]];
                }
                return "";
            }
            return obj[base];
        }
        for (i = 0; i < order.length; i++) {
            if (obj[base + "_" + order[i]]) return obj[base + "_" + order[i]];
        }
        return "";
    }

    function optionLabel(option) {
        return localized(option, "label") || String(option && option.id);
    }

    function optionDesc(option) {
        return localized(option, "desc");
    }

    function groupLabel(group) {
        return localized(group, "group");
    }

    function humanizeId(value) {
        return String(value || "")
            .replace(/[_-]+/g, " ")
            .replace(/\b[a-z]/g, function (match) { return match.toUpperCase(); });
    }

    function langMappedLabel(kind, id) {
        if (!id) return "";
        if (id === "custom") return t("custom");
        var entry = IMAGE_COMPARISON_LABELS[kind] && IMAGE_COMPARISON_LABELS[kind][id];
        if (!entry) return "";
        var order = LANG_FALLBACK[LANG] || LANG_FALLBACK.en;
        for (var i = 0; i < order.length; i += 1) {
            if (entry[order[i]]) return entry[order[i]];
        }
        return entry.en || "";
    }

    function comparisonValueLabel(kind, id) {
        return langMappedLabel(kind, id) || humanizeId(id);
    }

    function applyStaticTranslations() {
        document.documentElement.setAttribute("lang", LANG === "zh" ? "zh-CN" : (LANG === "ja" ? "ja" : "en"));
        document.querySelectorAll("[data-i18n]").forEach(function (node) {
            node.textContent = t(node.getAttribute("data-i18n"));
        });
    }

    var LANG_NAMES = { zh: "中文", en: "English", ja: "日本語" };

    function refreshLangToggle(toggleBtn) {
        // Custom dropdown (OS-independent): button shows the CURRENT language.
        var cur = document.getElementById("lang-current");
        if (cur) cur.textContent = LANG_NAMES[LANG] || LANG;
        toggleBtn.title = t("lang_toggle_title");
        document.querySelectorAll("#lang-menu li").forEach(function (li) {
            var selected = li.getAttribute("data-lang") === LANG;
            li.classList.toggle("selected", selected);
            li.setAttribute("aria-selected", selected ? "true" : "false");
        });
    }

    // ---- state -----------------------------------------------------------
    var CAT = null;     // catalogs.json — finite option universe
    var REC = null;     // current recommendation stage — AI picks + candidates
    var ICON_PREVIEWS = {};  // /api/icon-previews — real SVG samples from templates/icons
    var AI_IMAGE_COMPARISON = {};  // /api/ai-image-comparison — preset rendering catalog
    var STATE = {};
    var ACTIVE_DIRECTION_ID = "";
    var ACTIVE_DIRECTION_BASELINE = "";
    var ACTIVE_COMPONENT_DIRECTION_IDS = {};
    var refreshDesignDirectionState = function () {};
    var DIRECTION_COMPONENT_PAINTERS = [];

    function refreshDirectionComponentStates() {
        DIRECTION_COMPONENT_PAINTERS.forEach(function (paint) { paint(); });
    }
    var TEMPLATE_KINDS = ["brand", "style", "layout", "deck"];
    var TEMPLATE_OPTIONS = null;
    var TEMPLATE_CANDIDATES = [];
    var TEMPLATE_SELECTED_KEYS = [];
    var TEMPLATE_SELECTIONS = { brand: "", style: "", layout: "", deck: "", explicit: "" };
    var TEMPLATE_MODE = "";
    var REC_ALIASES = {
        icons: {
            line: "tabler-outline",
            filled: "tabler-filled",
            monochrome: "chunk-filled"
        },
        image_usage: {
            search: "web"
        },
        image_ai_path: {
            default: "auto",
            builtin: "host-native"
        }
    };

    // ---- DOM helpers -----------------------------------------------------
    function el(tag, cls, text) {
        var node = document.createElement(tag);
        if (cls) node.className = cls;
        if (text != null) node.textContent = text;
        return node;
    }

    function previewNode(kind, id) {
        var node = el("div", "option-preview option-preview-" + kind);
        node.setAttribute("aria-hidden", "true");
        if (kind === "visual_style") {
            appendVisualStyleImage(node, id);
            return node;
        }
        var markup = kind === "icons" ? iconStylePreview(id) : "";
        if (!markup) return null;
        node.innerHTML = markup;
        return node;
    }

    function visualStylePreviewSrc(id) {
        return "/static/style_previews/" + encodeURIComponent(id || "") + ".svg";
    }

    function appendVisualStyleImage(parent, id) {
        var img = document.createElement("img");
        img.alt = "";
        img.loading = "lazy";
        img.src = visualStylePreviewSrc(id);
        img.onerror = function () {
            parent.innerHTML = visualStylePreview(id);
        };
        parent.appendChild(img);
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function visualStylePreview(id) {
        var label = escapeHtml(humanizeId(id) || t("sub_visual"));
        var fallback = escapeHtml(t("error_retry"));
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">' +
            '<rect width="1280" height="720" fill="#F8FAFC"/>' +
            '<path d="M0 160H1280M0 360H1280M0 560H1280M220 0V720M640 0V720M1060 0V720" stroke="#E2E8F0" stroke-width="2"/>' +
            '<rect x="116" y="96" width="1048" height="528" rx="28" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="3"/>' +
            '<rect x="164" y="148" width="360" height="34" rx="17" fill="#111827"/>' +
            '<rect x="164" y="228" width="520" height="20" rx="10" fill="#CBD5E1"/>' +
            '<rect x="164" y="274" width="440" height="20" rx="10" fill="#E2E8F0"/>' +
            '<rect x="760" y="188" width="292" height="236" rx="22" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="3"/>' +
            '<path d="M808 378L874 308L942 348L1012 258" fill="none" stroke="#2563EB" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>' +
            '<circle cx="1012" cy="258" r="22" fill="#0F172A"/>' +
            '<rect x="164" y="464" width="220" height="24" rx="12" fill="#94A3B8"/>' +
            '<text x="164" y="548" fill="#475569" font-family="Arial, sans-serif" font-size="34">' + label + '</text>' +
            '<text x="164" y="594" fill="#94A3B8" font-family="Arial, sans-serif" font-size="24">' + fallback + '</text>' +
            '</svg>';
    }

    function iconStylePreview(id) {
        var common = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100"';
        var samples = ICON_PREVIEWS[id] || [];
        if (samples.length) {
            var sample = samples[0] || {};
            return '<div class="real-icon-preview real-icon-preview-' + escapeHtml(id) + '">' +
                '<div class="real-icon-sample"><div class="real-icon-mark">' +
                (sample.svg || "") +
                '</div><span class="real-icon-label">' + escapeHtml(sample.name || "") + '</span></div>' +
                '</div>';
        }
        if (id === "emoji") return '<svg ' + common + '><rect width="160" height="100" rx="10" fill="#FFF7ED"/><text x="80" y="60" text-anchor="middle" font-size="34">📊</text></svg>';
        if (id === "none") return '<svg ' + common + '><rect width="160" height="100" rx="10" fill="#FFFFFF"/><rect x="22" y="20" width="116" height="9" rx="4.5" fill="#111827"/><rect x="22" y="42" width="90" height="6" rx="3" fill="#CBD5E1"/><rect x="22" y="56" width="104" height="6" rx="3" fill="#CBD5E1"/><rect x="22" y="70" width="70" height="6" rx="3" fill="#CBD5E1"/><path d="M118 42l24 24M142 42l-24 24" stroke="#94A3B8" stroke-width="3" stroke-linecap="round"/></svg>';
        return "";
    }

    function comparisonImageUrl(kind, id) {
        var value = String(id || "").trim();
        if (!value || value === "custom") return "";
        if (!/^[A-Za-z0-9_.-]+$/.test(value)) return "";
        return "/ai-image-comparison/" + kind + "/" + encodeURIComponent(value) + ".png";
    }

    function appendImageStrategyPreviews(card, candidate) {
        if (candidate.rendering === "custom") return;
        var previews = [
            [t("image_strategy_rendering"), comparisonImageUrl("rendering", candidate.rendering)]
        ].filter(function (item) { return item[1]; });
        if (!previews.length) return;
        var row = el("div", "image-strategy-previews");
        previews.forEach(function (item) {
            var frame = el("div", "image-strategy-preview");
            var img = document.createElement("img");
            img.alt = item[0];
            img.loading = "lazy";
            img.src = item[1];
            img.onerror = function () {
                frame.remove();
                if (!row.childElementCount) row.remove();
            };
            frame.appendChild(img);
            frame.appendChild(el("span", "image-strategy-preview-label", item[0]));
            row.appendChild(frame);
        });
        card.appendChild(row);
        return row;
    }

    // Section numbers run 1..N within the stage currently rendered; the counter is
    // reset at the top of renderForStage. The legacy `num` arg is ignored so each
    // stage numbers its own sections cleanly (stage 2 is not a continuation of 1).
    var _secCounter = 0;
    function section(num, titleKey, noteText) {
        _secCounter += 1;
        var sec = el("div", "section");
        var head = el("div", "section-head");
        head.appendChild(el("span", "section-num", String(_secCounter)));
        head.appendChild(el("span", "section-title", t(titleKey)));
        if (noteText) head.appendChild(el("span", "section-note", noteText));
        sec.appendChild(head);
        return sec;
    }

    function setSectionNote(sec, text) {
        var head = sec.querySelector(".section-head");
        var note = head.querySelector(".section-note");
        if (!note) {
            note = el("span", "section-note");
            head.appendChild(note);
        }
        note.textContent = text;
    }

    // ---- Stage 1 template selection --------------------------------------
    function normalizeTemplateCandidates(raw, source, kind) {
        if (!Array.isArray(raw)) return [];
        return raw.filter(function (candidate) {
            return candidate && candidate.key != null && String(candidate.key).trim();
        }).map(function (candidate) {
            var normalized = Object.assign({}, candidate);
            normalized.key = String(candidate.key);
            normalized.source = source;
            if (kind) normalized.kind = kind;
            return normalized;
        });
    }

    function initTemplateOptions(data) {
        var library = data && data.library && typeof data.library === "object"
            ? data.library : {};
        var defaultMode = data && data.default_mode;
        if (defaultMode !== "free_design" && defaultMode !== "templates") {
            throw new Error("template_options.default_mode must be free_design or templates");
        }
        var normalized = {
            lang: data && data.lang,
            default_mode: defaultMode,
            library: {},
            explicit: [],
            preselected_keys: Array.isArray(data && data.preselected_keys)
                ? data.preselected_keys.map(String) : []
        };
        TEMPLATE_CANDIDATES = [];
        TEMPLATE_KINDS.forEach(function (kind) {
            var candidates = normalizeTemplateCandidates(library[kind], "library", kind);
            normalized.library[kind] = candidates;
            TEMPLATE_CANDIDATES = TEMPLATE_CANDIDATES.concat(candidates);
        });
        normalized.explicit = normalizeTemplateCandidates(data && data.explicit, "explicit", "");
        TEMPLATE_CANDIDATES = TEMPLATE_CANDIDATES.concat(normalized.explicit);
        var candidatesByKey = Object.create(null);
        TEMPLATE_CANDIDATES.forEach(function (candidate) {
            if (candidatesByKey[candidate.key]) {
                throw new Error("Duplicate template option key: " + candidate.key);
            }
            candidatesByKey[candidate.key] = candidate;
        });
        TEMPLATE_SELECTIONS = emptyTemplateSelections();
        normalized.preselected_keys.filter(function (key, index, all) {
            return all.indexOf(key) === index;
        }).forEach(function (key) {
            var candidate = candidatesByKey[key];
            var slot = templateSelectionSlot(candidate);
            if (!candidate || !slot) {
                throw new Error("Invalid preselected template key: " + key);
            }
            if (TEMPLATE_SELECTIONS[slot]) {
                throw new Error("Multiple preselected templates for slot: " + slot);
            }
            TEMPLATE_SELECTIONS[slot] = key;
        });
        syncTemplateSelectionState();
        TEMPLATE_MODE = normalized.default_mode;
        TEMPLATE_OPTIONS = normalized;
    }

    function emptyTemplateSelections() {
        return { brand: "", style: "", layout: "", deck: "", explicit: "" };
    }

    function templateSelectionSlot(candidate) {
        if (!candidate) return "";
        if (candidate.source === "explicit") return "explicit";
        if (candidate.source === "library" && TEMPLATE_KINDS.indexOf(candidate.kind) >= 0) {
            return candidate.kind;
        }
        return "";
    }

    function templateCandidateByKey(key) {
        key = String(key || "");
        for (var i = 0; i < TEMPLATE_CANDIDATES.length; i += 1) {
            if (TEMPLATE_CANDIDATES[i].key === key) return TEMPLATE_CANDIDATES[i];
        }
        return null;
    }

    function syncTemplateSelectionState() {
        TEMPLATE_SELECTED_KEYS = TEMPLATE_KINDS.map(function (kind) {
            return TEMPLATE_SELECTIONS[kind];
        });
        TEMPLATE_SELECTED_KEYS.push(TEMPLATE_SELECTIONS.explicit);
        TEMPLATE_SELECTED_KEYS = TEMPLATE_SELECTED_KEYS.filter(Boolean);
    }

    function templateCandidateTitle(candidate) {
        return localized(candidate, "label") || candidate.label || candidate.id || candidate.key;
    }

    function templateCandidateSummary(candidate) {
        return localized(candidate, "summary") || candidate.summary || "";
    }

    function templateKindLabel(kind) {
        return t("template_kind_" + kind);
    }

    function chooseFreeDesign() {
        TEMPLATE_SELECTIONS = emptyTemplateSelections();
        syncTemplateSelectionState();
        TEMPLATE_MODE = "free_design";
        updateTemplateSelectionControls();
    }

    function chooseTemplateMode() {
        TEMPLATE_MODE = "templates";
        updateTemplateSelectionControls();
    }

    function chooseTemplateForSlot(slot, key) {
        TEMPLATE_SELECTIONS[slot] = String(key || "");
        syncTemplateSelectionState();
        TEMPLATE_MODE = "templates";
        updateTemplateSelectionControls();
    }

    function templateOptionTitle(candidate) {
        var details = [];
        var summary = templateCandidateSummary(candidate);
        if (summary) details.push(summary);
        if (candidate.workspace_root) details.push(candidate.workspace_root);
        return details.join(" · ");
    }

    function renderTemplateSelectField(slot, label, candidates) {
        var field = el("div", "template-select-field template-select-field-" + slot);
        var selectId = "template-select-" + slot;
        var fieldLabel = el("label", "template-select-label", label);
        fieldLabel.setAttribute("for", selectId);
        field.appendChild(fieldLabel);

        var select = el("select", "template-select");
        select.id = selectId;
        select.setAttribute("data-template-slot", slot);
        var none = el("option", "", t("template_select_none"));
        none.value = "";
        select.appendChild(none);
        candidates.forEach(function (candidate) {
            var option = el("option", "", templateCandidateTitle(candidate));
            option.value = candidate.key;
            var title = templateOptionTitle(candidate);
            if (title) option.title = title;
            select.appendChild(option);
        });
        select.value = TEMPLATE_SELECTIONS[slot] || "";
        select.disabled = !candidates.length;
        select.addEventListener("change", function () {
            chooseTemplateForSlot(slot, select.value);
        });
        field.appendChild(select);

        if (slot === "explicit") {
            field.appendChild(el(
                "div",
                "template-select-help",
                candidates.length ? t("template_explicit_hint") : t("template_none_explicit")
            ));
            var path = el("div", "template-selected-path");
            path.id = "template-explicit-path";
            path.appendChild(el("span", "template-selected-path-label", t("template_source_path") + ":"));
            var code = el("code", "template-selected-path-value");
            code.id = "template-explicit-path-value";
            path.appendChild(code);
            field.appendChild(path);
        }
        return field;
    }

    function renderTemplateModeChoice(id, mode, titleKey, descKey, onSelect) {
        var selected = TEMPLATE_MODE === mode;
        var choice = el("button", "template-mode-choice" + (selected ? " selected" : ""));
        choice.id = id;
        choice.type = "button";
        choice.setAttribute("aria-pressed", selected ? "true" : "false");
        choice.appendChild(el("span", "template-choice-radio"));
        var copy = el("span", "template-choice-copy");
        copy.appendChild(el("span", "template-choice-title", t(titleKey)));
        copy.appendChild(el("span", "template-choice-desc", t(descKey)));
        choice.appendChild(copy);
        choice.addEventListener("click", onSelect);
        return choice;
    }

    function renderTemplateSelection(host) {
        if (!TEMPLATE_OPTIONS) return;
        var sec = section("T", "sec_template_choice", t("template_choice_hint"));
        var choices = el("div", "template-mode-choices");
        choices.appendChild(renderTemplateModeChoice(
            "template-free-choice", "free_design", "template_free_title",
            "template_free_desc", chooseFreeDesign
        ));
        var useChoice = renderTemplateModeChoice(
            "template-use-choice", "templates", "template_use_title",
            "template_use_desc", chooseTemplateMode
        );
        useChoice.setAttribute("aria-controls", "template-selector-panel");
        choices.appendChild(useChoice);
        sec.appendChild(choices);

        var panel = el("div", "template-selector-panel");
        panel.id = "template-selector-panel";
        panel.appendChild(el("div", "template-selector-hint", t("template_library_hint")));
        var grid = el("div", "template-select-grid");
        TEMPLATE_KINDS.forEach(function (kind) {
            var candidates = TEMPLATE_OPTIONS.library[kind] || [];
            grid.appendChild(renderTemplateSelectField(kind, templateKindLabel(kind), candidates));
        });
        grid.appendChild(renderTemplateSelectField(
            "explicit",
            t("template_source_explicit"),
            TEMPLATE_OPTIONS.explicit || []
        ));
        panel.appendChild(grid);
        sec.appendChild(panel);
        host.appendChild(sec);
        updateTemplateSelectionControls();
    }

    function updateTemplateExplicitPath() {
        var path = document.getElementById("template-explicit-path");
        var value = document.getElementById("template-explicit-path-value");
        if (!path || !value) return;
        var candidate = templateCandidateByKey(TEMPLATE_SELECTIONS.explicit);
        var workspaceRoot = candidate && candidate.workspace_root ? candidate.workspace_root : "";
        path.hidden = !workspaceRoot;
        value.textContent = workspaceRoot;
        value.title = workspaceRoot;
    }

    function updateTemplateSelectionControls() {
        var freeChoice = document.getElementById("template-free-choice");
        var useChoice = document.getElementById("template-use-choice");
        var selectorPanel = document.getElementById("template-selector-panel");
        var freeSelected = TEMPLATE_MODE === "free_design";
        var templatesSelected = TEMPLATE_MODE === "templates";
        if (freeChoice) {
            freeChoice.classList.toggle("selected", freeSelected);
            freeChoice.setAttribute("aria-pressed", freeSelected ? "true" : "false");
        }
        if (useChoice) {
            useChoice.classList.toggle("selected", templatesSelected);
            useChoice.setAttribute("aria-pressed", templatesSelected ? "true" : "false");
            useChoice.setAttribute("aria-expanded", templatesSelected ? "true" : "false");
        }
        if (selectorPanel) selectorPanel.hidden = !templatesSelected;
        TEMPLATE_KINDS.concat(["explicit"]).forEach(function (slot) {
            var select = document.getElementById("template-select-" + slot);
            if (select) select.value = TEMPLATE_SELECTIONS[slot] || "";
        });
        updateTemplateExplicitPath();
        var status = document.getElementById("confirm-status");
        if (status) status.textContent = "";
    }

    function normalizeRecId(field, value) {
        if (Array.isArray(value)) return normalizeRecId(field, value[0]);
        if (value == null || value === "") return value;
        var aliases = REC_ALIASES[field] || {};
        return aliases[value] || value;
    }

    function normalizeRecIds(field, value) {
        if (Array.isArray(value)) {
            return value.map(function (item) { return normalizeRecId(field, item); })
                .filter(function (item, idx, arr) { return item && arr.indexOf(item) === idx; });
        }
        var normalized = normalizeRecId(field, value);
        return normalized ? [normalized] : [];
    }

    function legacyRecId(field) {
        if (!REC) return null;
        if (field === "canvas") return REC.canvas && REC.canvas.value;
        if (field === "visual_style") return REC.visual_style || (REC.style && REC.style.value);
        if (field === "icons") return REC.icons && REC.icons.value;
        if (field === "image_usage") return REC.images && REC.images.value;
        if (field === "image_ai_path") return REC.image_ai_path || (REC.images && REC.images.ai_path);
        if (field === "formula_policy") return REC.typography && REC.typography.formula_policy && REC.typography.formula_policy.value;
        if (field === "generation_mode") return REC.generation_mode && REC.generation_mode.value;
        return REC[field] && REC[field].value;
    }

    function recId(field) {
        var value = (REC && REC.recommend && REC.recommend[field]) || legacyRecId(field);
        return normalizeRecId(field, value || null);
    }

    function recValue(field) {
        return (REC && REC.recommend && REC.recommend[field]) || legacyRecId(field);
    }

    function booleanRecommendation(field, fallback) {
        if (!REC || !Object.prototype.hasOwnProperty.call(REC, field)) return fallback;
        var spec = REC[field];
        var value = spec && typeof spec === "object" ? spec.value : spec;
        return typeof value === "boolean" ? value : fallback;
    }

    function recommendationFieldLocked(field) {
        return !!(REC && REC[field] && typeof REC[field] === "object" && REC[field].locked === true);
    }

    // Guaranteed recommendation: the AI's pick, or the first catalog option as a
    // fallback so an enumerable field ALWAYS shows a badged recommendation.
    function recOrFirst(field, list) {
        var r = recId(field);
        if (r == null || r === "") r = normalizeRecId(field, directionField(field));
        if (r != null && r !== "") return r;
        return firstId(list);
    }
    // Render an enumerable field: ALL options from the catalog, recommended one
    // badged, current selection from STATE, plus an optional Custom box. An
    // AI-authored custom candidate stays fully visible while unselected and
    // becomes editable only after selection; legacy custom inputs keep their
    // compact free-text behavior.
    // `list` is either a flat array of {id,label,desc,dim,viewbox} or a grouped array
    // of {group, items:[...]}.
    function enumField(parent, list, recommendedId, getVal, setVal, opts2) {
        list = list || [];
        opts2 = opts2 || {};
        var grouped = list.length && list[0] && list[0].items;
        var flat = grouped ? list.reduce(function (a, g) { return a.concat(g.items || []); }, []) : list;
        var ids = flat.map(function (o) { return o.id; });
        // Optional legacy spectrum: marks several catalog ids with localized
        // tags and notes instead of one recommendation badge.
        var spectrum = (opts2.spectrum && opts2.spectrum.length) ? opts2.spectrum : null;
        var specById = {};
        if (spectrum) spectrum.forEach(function (s) {
            if (s && s.id) specById[s.id] = { tag: localized(s, "tag"), note: localized(s, "note") };
        });
        var allowCustom = opts2.allowCustom === true;  // only for fields not fully enumerable
        var aiCustom = opts2.aiCustom || null;
        var customSentinel = opts2.customSentinel || (aiCustom ? "custom" : "");
        var customInvalidValues = opts2.customInvalidValues || [];
        var cur = getVal();
        var isCustom = cur != null && cur !== "" &&
            (cur === customSentinel || ids.indexOf(cur) === -1);
        if (!allowCustom && isCustom && opts2.preserveCustom !== true) {
            // closed field with an out-of-catalog value → snap to recommended/first
            cur = ids.indexOf(recommendedId) >= 0 ? recommendedId : ids[0];
            setVal(cur);
            isCustom = false;
        }

        var allChips = [];
        var customInput = el(aiCustom ? "textarea" : "input", "text-input custom-input");
        setNaturalInputDirection(customInput);
        if (opts2.inputClass) customInput.classList.add(opts2.inputClass);
        if (aiCustom) customInput.rows = aiCustom.rows || 4;
        else customInput.type = "text";
        customInput.placeholder = opts2.placeholder || t("custom_placeholder");
        customInput.style.display = "none";
        var customPreview = null;

        function customText() {
            if (!aiCustom) return customInput.value || "";
            return String(aiCustom.getText ? aiCustom.getText() : (aiCustom.text || ""));
        }

        function syncAiCustom(selected) {
            if (!aiCustom || !customPreview) return;
            var value = customText();
            customPreview.textContent = value;
            customPreview.style.display = selected ? "none" : "block";
            customInput.style.display = selected ? "block" : "none";
            if (selected && customInput.value !== value) customInput.value = value;
        }

        function deselect() {
            allChips.forEach(function (c) { c.classList.remove("selected"); });
            if (aiCustom) syncAiCustom(false);
        }
        function makeChip(o) {
            var label = optionLabel(o);
            var desc = optionDesc(o);
            var spec = specById[o.id];
            var chip = el("div", "chip");
            var preview = previewNode(opts2.preview, o.id);
            if (preview) {
                chip.classList.add("chip-with-preview");
                chip.classList.add("chip-preview-" + opts2.preview);
                chip.appendChild(preview);
            }
            var copy = el("div", "chip-copy");
            if (o.viewbox) {
                label = label + (o.dim ? " · " + o.dim : "");
            } else {
                if (o.dim) label += " · " + o.dim;
                if (desc) label += (LANG === "zh" || LANG === "ja" ? "：" : " — ") + desc;
                if (spec && spec.note) label += " · " + spec.note;
            }
            copy.appendChild(el("span", "chip-text", label));
            if (spec) {
                // spectrum pick: badge shows its temperament tag, not the generic ★
                chip.classList.add("recommended");
                copy.appendChild(el("span", "rec-badge", "★ " + (spec.tag || t("recommended"))));
            } else if (!spectrum && o.id === recommendedId) {
                chip.classList.add("recommended");
                copy.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
            chip.appendChild(copy);
            if (!isCustom && o.id === cur) chip.classList.add("selected");
            chip.addEventListener("click", function () {
                deselect();
                chip.classList.add("selected");
                if (!aiCustom) customInput.style.display = "none";
                setVal(o.id);
            });
            allChips.push(chip);
            return chip;
        }

        var chipsClass = "chips" + (opts2.chipsClass ? " " + opts2.chipsClass : "");
        if (grouped) {
            list.forEach(function (g) {
                if (groupLabel(g)) parent.appendChild(el("div", "group-label", groupLabel(g)));
                var row = el("div", chipsClass);
                (g.items || []).forEach(function (o) { row.appendChild(makeChip(o)); });
                parent.appendChild(row);
            });
            if (allowCustom) {
                var lastRow = el("div", aiCustom ? "chips custom-chip-row" : "chips");
                lastRow.appendChild(buildCustomChip());
                parent.appendChild(lastRow);
            }
        } else {
            var wrap = el("div", chipsClass);
            var ownRowIds = opts2.ownRowIds || [];
            flat.filter(function (o) { return ownRowIds.indexOf(o.id) === -1; })
                .forEach(function (o) { wrap.appendChild(makeChip(o)); });
            if (allowCustom && !opts2.customOnOwnRow) wrap.appendChild(buildCustomChip());
            parent.appendChild(wrap);
            flat.filter(function (o) { return ownRowIds.indexOf(o.id) >= 0; })
                .forEach(function (o) {
                    var ownRow = el("div", "chips standalone-chip-row");
                    ownRow.appendChild(makeChip(o));
                    parent.appendChild(ownRow);
                });
            if (allowCustom && opts2.customOnOwnRow) {
                var customRow = el("div", "chips custom-chip-row");
                customRow.appendChild(buildCustomChip());
                parent.appendChild(customRow);
            }
        }
        if (allowCustom && !aiCustom) parent.appendChild(customInput);

        function buildCustomChip() {
            var customChip = el("div", aiCustom ? "chip ai-custom-candidate" : "chip");
            if (aiCustom) {
                var customHead = el("div", "ai-custom-candidate-head");
                customHead.appendChild(el("span", "chip-text",
                    aiCustom.label || t("ai_custom_candidate")));
                customHead.appendChild(el("span", "ai-custom-candidate-hint",
                    aiCustom.hint || t("ai_custom_candidate_hint")));
                customChip.appendChild(customHead);
                customPreview = el("div", "ai-custom-candidate-copy", customText());
                customChip.appendChild(customPreview);
                customChip.appendChild(customInput);
            } else {
                customChip.appendChild(el("span", "chip-text", t("custom")));
            }
            if (recommendedId === customSentinel ||
                    (recommendedId && ids.indexOf(recommendedId) === -1 && isCustom)) {
                customChip.classList.add("recommended");
                customChip.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
            if (isCustom) {
                customChip.classList.add("selected");
                if (aiCustom) syncAiCustom(true);
                else {
                    customInput.style.display = "block";
                    customInput.value = customInvalidValues.indexOf(cur) >= 0 ? "" : cur;
                }
            } else if (aiCustom) {
                syncAiCustom(false);
            }
            customChip.addEventListener("click", function () {
                deselect();
                customChip.classList.add("selected");
                if (aiCustom) syncAiCustom(true);
                else customInput.style.display = "block";
                customInput.focus();
                setVal(aiCustom ? customSentinel : (customInput.value || customSentinel));
            });
            allChips.push(customChip);
            return customChip;
        }
        customInput.addEventListener("click", function (event) { event.stopPropagation(); });
        customInput.addEventListener("input", function () {
            if (aiCustom) {
                if (aiCustom.setText) aiCustom.setText(customInput.value);
                setVal(customSentinel);
            } else {
                setVal(customInput.value || customSentinel);
            }
        });
    }

    function textField(parent, getVal, setVal, placeholderKey, numeric) {
        var input = el("input", numeric ? "num-input" : "text-input");
        input.type = "text";
        if (!numeric) setNaturalInputDirection(input);
        input.value = getVal() || "";
        input.placeholder = t(placeholderKey);
        input.addEventListener("input", function () { setVal(input.value); });
        parent.appendChild(input);
    }

    function textareaField(parent, getVal, setVal, placeholderKey, rows) {
        var input = el("textarea", "text-input");
        setNaturalInputDirection(input);
        input.rows = rows || 2;
        input.value = getVal() || "";
        input.placeholder = t(placeholderKey);
        input.addEventListener("input", function () { setVal(input.value); });
        parent.appendChild(input);
        return input;
    }

    function labeledTextarea(parent, labelKey, getVal, setVal, placeholderKey, hintKey, rows) {
        var field = el("div", "subfield");
        field.appendChild(el("div", "subfield-label", t(labelKey)));
        if (hintKey) field.appendChild(el("div", "toggle-desc", t(hintKey)));
        textareaField(field, getVal, setVal, placeholderKey, rows);
        parent.appendChild(field);
        return field;
    }

    function normPalette(c) {
        function read(src, keys) {
            if (!src) return undefined;
            for (var i = 0; i < keys.length; i += 1) {
                if (src[keys[i]] != null) return src[keys[i]];
            }
            return undefined;
        }
        function collect(src) {
            return {
                background: read(src, ["background", "bg"]),
                secondary_bg: read(src, ["secondary_bg", "secondary_background", "card_bg", "card_background"]),
                primary: read(src, ["primary"]),
                accent: read(src, ["accent"]),
                secondary_accent: read(src, ["secondary_accent", "secondary"]),
                body_text: read(src, ["body_text", "text"])
            };
        }
        if (c && c.palette) {
            return collect(c.palette);
        }
        if (!c) return {};
        return collect(c);
    }

    function recommendationLanguage() {
        // `lang` controls the Confirm UI language; it is not evidence of the
        // deck's content language. New staged files carry `primary_language`.
        var raw = REC && (REC.primary_language || REC.content_language || REC.language);
        if (raw && typeof raw === "object") {
            raw = raw.value || raw.id || raw.code || "";
        }
        // The API is the single normalizer; the browser consumes its canonical
        // value instead of maintaining a second alias table.
        return String(raw || "und").trim().replace(/_/g, "-");
    }

    function isEnglishProject() {
        return /^en(?:-|$)/i.test(recommendationLanguage());
    }

    function setEnglishLanguageAttributes(node) {
        node.lang = "en";
        node.dir = "ltr";
    }

    function setUiLanguageAttributes(node) {
        node.lang = LANG === "zh" ? "zh-CN" : (LANG === "ja" ? "ja-JP" : "en-US");
        node.dir = "ltr";
    }

    function setNaturalInputDirection(node) {
        node.dir = "auto";
    }

    function stringList(value) {
        if (Array.isArray(value)) return value.map(String);
        if (value == null || value === "") return [];
        return [String(value)];
    }

    function normalizedFontToken(value) {
        return String(value || "").trim().toLowerCase().replace(/[_\s]+/g, "-");
    }

    function fontScriptTokens(language) {
        var parts = normalizedFontToken(language).split("-");
        var base = parts[0];
        if (!base || base === "und") return [];
        var explicitScript = parts.filter(function (part) {
            return /^[a-z]{4}$/.test(part);
        })[0];
        if (explicitScript) return [explicitScript];
        if (base === "en") return ["latin", "latn", "english"];
        if (base === "zh") {
            if (parts.indexOf("cn") >= 0 || parts.indexOf("sg") >= 0) {
                return ["han", "hans", "cjk", "chinese", "zh"];
            }
            if (parts.indexOf("tw") >= 0 || parts.indexOf("hk") >= 0 ||
                    parts.indexOf("mo") >= 0) {
                return ["han", "hant", "cjk", "chinese", "zh"];
            }
            return ["han", "hans", "cjk", "chinese", "zh"];
        }
        if (base === "ja") return ["han", "jpan", "kana", "hiragana", "katakana", "cjk", "japanese", "ja"];
        if (base === "ko") return ["hangul", "kore", "han", "cjk", "korean", "ko"];
        if (["ru", "uk", "bg", "sr", "mk"].indexOf(base) >= 0) return ["cyrl", "cyrillic"];
        if (["ar", "fa", "ur"].indexOf(base) >= 0) return ["arab", "arabic"];
        if (base === "he" || base === "iw") return ["hebr", "hebrew"];
        if (base === "el") return ["grek", "greek"];
        if (base === "th") return ["thai"];
        if (base === "hi" || base === "mr" || base === "ne") return ["deva", "devanagari"];
        // Most remaining presentation locales use Latin script. Locale metadata
        // still wins before this fallback.
        return ["latin", "latn"];
    }

    function fontSupportsLanguage(font, language) {
        var target = normalizedFontToken(language);
        var targetBase = target.split("-")[0];
        var locales = stringList(font && font.locales).map(normalizedFontToken);
        if (locales.some(function (locale) {
            return locale === "*" || locale === target ||
                (target !== targetBase && locale === targetBase);
        })) return true;

        var supportedScripts = stringList(font && font.scripts).map(normalizedFontToken);
        var wantedScripts = fontScriptTokens(language);
        if (supportedScripts.some(function (script) {
            return wantedScripts.indexOf(script) >= 0;
        })) return true;

        // A catalog entry without language metadata remains usable. Once either
        // metadata field is present, filtering follows it.
        return !locales.length && !supportedScripts.length;
    }

    function fontCatalogEntries(field) {
        var fonts = (CAT && Array.isArray(CAT.fonts)) ? CAT.fonts : [];
        var language = field === "english" ? "en" : recommendationLanguage();
        if (field === "primary" && language === "und") {
            return fonts.filter(function (font) { return font && font.id; });
        }
        var matching = fonts.filter(function (font) {
            return font && font.id && fontSupportsLanguage(font, language);
        });
        return matching;
    }

    function findFontCatalogEntry(id) {
        var fonts = (CAT && Array.isArray(CAT.fonts)) ? CAT.fonts : [];
        var target = String(id || "").trim().toLowerCase();
        for (var i = 0; i < fonts.length; i += 1) {
            if (String(fonts[i].id || "").trim().toLowerCase() === target) return fonts[i];
        }
        return null;
    }

    function derivedFontCss(font) {
        var primary = findFontCatalogEntry(font && font.primary);
        return String((primary && primary.css) || "sans-serif").trim() ||
            "sans-serif";
    }

    function normalizedFontRole(font, samples) {
        font = (font && typeof font === "object") ? Object.assign({}, font) : {};
        samples = samples || {};
        var primary = font.primary;
        var english = font.english;
        if (isEnglishProject()) {
            primary = primary || font.latin || font.cjk || "";
            english = "";
        } else {
            primary = primary || font.cjk || "";
            english = english || font.latin || "";
        }
        font.primary = primary;
        if (isEnglishProject()) delete font.english;
        else font.english = english;
        font.sample_primary = font.sample_primary ||
            (isEnglishProject() ? font.sample_latin : font.sample_cjk) ||
            samples.primary || "";
        if (isEnglishProject()) {
            delete font.sample_english;
        } else {
            font.sample_english = font.sample_english || font.sample_latin ||
                samples.english || "";
        }
        delete font.cjk;
        delete font.latin;
        delete font.sample_cjk;
        delete font.sample_latin;
        if (!String(font.css || "").trim()) font.css = derivedFontCss(font);
        return font;
    }

    function normTypography(c) {
        c = c || {};
        var normalized = Object.assign({}, c);
        var objectShape = c.heading && typeof c.heading === "object" &&
            c.body && typeof c.body === "object";
        var heading = objectShape ? c.heading : {
            primary: isEnglishProject() ? (c.heading_latin || c.heading || "") : (c.heading || ""),
            english: isEnglishProject() ? "" : (c.heading_latin || ""),
            css: c.heading_css || ""
        };
        var body = objectShape ? c.body : {
            primary: isEnglishProject() ? (c.body_latin || c.body || "") : (c.body || ""),
            english: isEnglishProject() ? "" : (c.body_latin || ""),
            css: c.body_css || ""
        };
        normalized.name = c.name || "";
        normalized.note = c.note || "";
        normalized.custom = c.custom || "";
        normalized.body_size = typographyBodySize(c);
        normalized.heading = normalizedFontRole(heading, {
            primary: isEnglishProject()
                ? (c.sample_heading_latin || c.sample_heading || "")
                : (c.sample_heading || ""),
            english: c.sample_heading_latin || ""
        });
        normalized.body = normalizedFontRole(body, {
            primary: isEnglishProject()
                ? (c.sample_body_latin || c.sample_body || "")
                : (c.sample_body || ""),
            english: c.sample_body_latin || ""
        });
        delete normalized.heading_latin;
        delete normalized.body_latin;
        delete normalized.heading_css;
        delete normalized.body_css;
        delete normalized.sample_heading;
        delete normalized.sample_heading_latin;
        delete normalized.sample_body;
        delete normalized.sample_body_latin;
        return normalized;
    }

    function typographyBodySize(c) {
        c = c || {};
        var value = c.body_size || c.body_baseline || c.body_px ||
            (c.sizes && c.sizes.body) ||
            (c.size && c.size.body) ||
            (c.body && typeof c.body === "object" && (c.body.size || c.body.font_size));
        return value == null ? "" : String(value).replace(/px$/i, "");
    }

    function designDirectionSpec() {
        return (REC && REC.design_directions) ||
            (REC && REC.design && REC.design.directions) ||
            {};
    }

    function designDirectionCandidates() {
        var spec = designDirectionSpec();
        return spec.candidates || spec.options || [];
    }

    function designDirectionId(candidate, index) {
        var value = candidate && candidate.id;
        return String(value || ("direction-" + (Number(index) + 1)));
    }

    function selectedDesignDirection() {
        var candidates = designDirectionCandidates();
        var selected = Number(designDirectionSpec().selected || 0);
        if (!isFinite(selected) || selected < 0) selected = 0;
        return candidates[Math.min(selected, Math.max(candidates.length - 1, 0))] || {};
    }

    function directionField(field) {
        var candidate = selectedDesignDirection();
        return candidate[field] != null ? candidate[field] : null;
    }

    function directionBehavior(candidate, field) {
        return String(localized(candidate, field + "_behavior") ||
            (candidate && candidate[field + "_behavior"]) || "");
    }

    function directionStateSignature(candidate) {
        candidate = candidate || {};
        var out = {};
        if (candidate.mode) {
            out.mode = STATE.mode || "";
            out.mode_behavior = STATE.mode === "custom" ? (STATE.mode_behavior || "") : "";
        }
        if (candidate.visual_style) {
            out.visual_style = STATE.visual_style || "";
            out.visual_style_behavior = STATE.visual_style === "custom" ?
                (STATE.visual_style_behavior || "") : "";
        }
        if (candidate.color) {
            var palette = normPalette(STATE.color || {});
            out.color = {
                custom: (STATE.color && STATE.color.custom) || "",
                palette: {}
            };
            PALETTE_ROLES.forEach(function (role) {
                out.color.palette[role] = normHex(palette[role]) || "";
            });
        }
        if (candidate.typography) {
            var typography = normTypography(STATE.typography || {});
            out.typography = {
                heading: typography.heading || {},
                body: typography.body || {},
                body_size: String(typography.body_size || ""),
                sizes: {}
            };
            ["title", "subtitle", "annotation"].forEach(function (role) {
                out.typography.sizes[role] = String(
                    (STATE.typography && STATE.typography.sizes && STATE.typography.sizes[role]) || ""
                );
            });
        }
        if (candidate.icons) out.icons = STATE.icons || "";
        if (candidate.image_strategy) {
            out.image_strategy = comparableImageStrategy(STATE.image_strategy || {});
        }
        return JSON.stringify(out);
    }

    function activeDirectionAdjusted(candidate, index) {
        return designDirectionId(candidate, index) === ACTIVE_DIRECTION_ID &&
            directionStateSignature(candidate) !== ACTIVE_DIRECTION_BASELINE;
    }

    function customCandidateSpec(field) {
        var candidates = REC && REC.custom_candidates;
        var candidate = candidates && candidates[field];
        if (typeof candidate === "string") return { behavior: candidate };
        if (candidate && typeof candidate === "object") return candidate;
        var legacy = REC && REC[field + "_behavior"];
        if (legacy && typeof legacy === "object") legacy = legacy.value;
        return legacy ? { behavior: legacy } : {};
    }

    function customCandidateBehavior(field) {
        var candidate = customCandidateSpec(field);
        return String(localized(candidate, "behavior") || candidate.value || candidate.custom || "");
    }

    function creativeCustomOptions(field, stateKey, placeholderKey) {
        var candidate = customCandidateSpec(field);
        var current = String(STATE[stateKey] || customCandidateBehavior(field) || "");
        if (!current.trim()) return null;
        STATE[stateKey] = current;
        return {
            label: localized(candidate, "name") || t("ai_custom_candidate"),
            hint: t("ai_custom_candidate_hint"),
            getText: function () { return STATE[stateKey] || ""; },
            setText: function (value) { STATE[stateKey] = value; },
            rows: 4,
            placeholder: t(placeholderKey)
        };
    }

    function colorRecommendationCandidates() {
        var direct = (REC.color && REC.color.candidates) || [];
        if (direct.length) return direct;
        return designDirectionCandidates().map(function (candidate) {
            return candidate && candidate.color;
        }).filter(Boolean);
    }

    function typographyRecommendationCandidates() {
        var direct = (REC.typography && REC.typography.candidates) || [];
        if (direct.length) return direct;
        return designDirectionCandidates().map(function (candidate) {
            return candidate && candidate.typography;
        }).filter(Boolean);
    }

    function imageStrategySpec() {
        return (REC && REC.image_strategy) ||
            (REC && REC.images && REC.images.strategy) ||
            (REC && REC.images && REC.images.ai_strategy) ||
            {};
    }

    function imageStrategyCandidates() {
        var spec = imageStrategySpec();
        var direct = spec.candidates || spec.options || [];
        if (direct.length) return direct;
        return designDirectionCandidates().map(function (candidate) {
            return candidate && candidate.image_strategy;
        }).filter(Boolean);
    }

    function imageStrategyRecommendationCandidates() {
        return imageStrategyCandidates().filter(function (candidate) {
            return candidate && candidate.rendering !== "custom";
        }).slice(0, 3);
    }

    function imageStrategyCatalogCandidates() {
        var items = AI_IMAGE_COMPARISON && AI_IMAGE_COMPARISON.rendering;
        if (!Array.isArray(items)) return [];
        return items.map(function (item) {
            return item && item.id ? { rendering: item.id } : null;
        }).filter(Boolean);
    }

    function imageStrategySelectableCandidates() {
        var recommended = imageStrategyRecommendationCandidates();
        var seen = {};
        recommended.forEach(function (candidate) { seen[candidate.rendering] = true; });
        return recommended.concat(imageStrategyCatalogCandidates().filter(function (candidate) {
            return !seen[candidate.rendering];
        }));
    }

    function imageStrategyCustomCandidate() {
        var candidate = customCandidateSpec("image_strategy");
        if (!customCandidateBehavior("image_strategy")) return null;
        if (!candidate || typeof candidate !== "object") candidate = {};
        candidate = Object.assign({}, candidate, { rendering: "custom" });
        return normalizedImageStrategy(candidate);
    }

    function normalizedImageStrategy(candidate) {
        candidate = candidate || {};
        var out = {
            name: localized(candidate, "name") || candidate.name || "",
            rendering: candidate.rendering || "",
            visual: localized(candidate, "visual") || "",
            mood: localized(candidate, "mood") || ""
        };
        var behavior = localized(candidate, "behavior") || candidate.behavior || candidate.custom || "";
        if (behavior) out.behavior = behavior;
        return out;
    }

    function comparableImageStrategy(candidate) {
        var strategy = normalizedImageStrategy(candidate);
        return {
            rendering: strategy.rendering || "",
            visual: strategy.visual || "",
            mood: strategy.mood || "",
            behavior: strategy.behavior || ""
        };
    }

    function usesCustomImagePlanValue(value) {
        var ids = (CAT.image_usage || []).map(function (item) { return item.id; });
        if (Array.isArray(value)) return false;
        return value && ids.indexOf(value) === -1;
    }

    function customImagePlanHasAiSignal() {
        return imageStrategyRecommendationCandidates().length > 0 || !!recId("image_ai_path");
    }

    function needsGeneratedImagesForUsage(value) {
        if (Array.isArray(value)) return value.indexOf("ai") >= 0;
        return value === "ai" || (usesCustomImagePlanValue(value) && customImagePlanHasAiSignal());
    }

    function selectedImageUsageIds(value) {
        var validIds = (CAT.image_usage || []).map(function (item) { return item.id; });
        return normalizeRecIds("image_usage", value).filter(function (id) {
            return validIds.indexOf(id) >= 0;
        });
    }

    function imageUsageNotesRecommendation(rawUsage) {
        var notes = (REC && REC.image_notes && REC.image_notes.value) ||
            (REC && REC.image_notes) ||
            (REC && REC.images && REC.images.notes) ||
            "";
        if (!notes && usesCustomImagePlanValue(rawUsage)) notes = rawUsage;
        return typeof notes === "string" ? notes : "";
    }

    function defaultImageUsageId() {
        return firstId(CAT.image_usage);
    }

    function imageStrategySelectedIndex() {
        var spec = imageStrategySpec();
        var direct = spec.candidates || spec.options || [];
        var idx = direct.length ? (spec.selected || 0) : (designDirectionSpec().selected || 0);
        return Math.min(idx, Math.max(imageStrategyRecommendationCandidates().length - 1, 0));
    }

    // ---- section renderers ----------------------------------------------
    function renderCanvas(host) {
        var sec = section(1, "sec_canvas");
        enumField(sec, CAT.canvas, recOrFirst("canvas", CAT.canvas),
            function () { return STATE.canvas; },
            function (v) {
                STATE.canvas = v;
                if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
                // Canvas changes dimensions only — never silently rewrite font sizes
                // the user can see / edit. The size hint re-renders with the new
                // canvas; a default body is filled only when none is set yet.
                if (!STATE.typography.body_size) {
                    STATE.typography.body_size = defaultBodySizeForCanvas(v, STATE.delivery_purpose);
                }
                renderAll();
            }, { allowCustom: true });
        host.appendChild(sec);
    }

    function renderPages(host) {
        var sec = section(2, "sec_pages");
        textField(sec, function () { return STATE.page_count; },
            function (v) { STATE.page_count = v; }, "placeholder_pages", true);
        host.appendChild(sec);
    }

    function templateApplicationRecommendation() {
        if (!REC || REC.template_application == null) return null;
        var field = REC.template_application;
        if (typeof field === "object") {
            return field.value == null ? "" : String(field.value);
        }
        return String(field);
    }

    function renderTemplateApplication(host) {
        if (templateApplicationRecommendation() == null) return;
        var sec = section("T", "sec_template_application");
        setSectionNote(sec, t("template_application_hint"));
        textareaField(sec,
            function () { return STATE.template_application; },
            function (v) { STATE.template_application = v; },
            "placeholder_template_application", 4);
        host.appendChild(sec);
    }

    function renderCommunication(host) {
        var sec = section(1, "sec_communication");
        var audienceField = el("div", "subfield");
        audienceField.appendChild(el("div", "subfield-label", t("sec_audience")));
        textField(audienceField, function () { return STATE.audience; },
            function (v) { STATE.audience = v; }, "placeholder_audience", false);
        sec.appendChild(audienceField);
        labeledTextarea(sec, "communication_intent",
            function () { return STATE.communication_intent; },
            function (v) { STATE.communication_intent = v; },
            "placeholder_communication_intent", "communication_intent_hint", 3);
        labeledTextarea(sec, "audience_outcome",
            function () { return STATE.audience_outcome; },
            function (v) { STATE.audience_outcome = v; },
            "placeholder_audience_outcome", null, 2);
        labeledTextarea(sec, "core_message",
            function () { return STATE.core_message; },
            function (v) { STATE.core_message = v; },
            "placeholder_core_message", null, 2);
        host.appendChild(sec);
    }

    function renderDelivery(host) {
        var sec = section(2, "sec_delivery");
        labeledTextarea(sec, "delivery_context",
            function () { return STATE.delivery_context; },
            function (v) { STATE.delivery_context = v; },
            "placeholder_delivery_context", "delivery_context_hint", 2);
        labeledTextarea(sec, "artifact_afterlife",
            function () { return STATE.artifact_afterlife; },
            function (v) { STATE.artifact_afterlife = v; },
            "placeholder_artifact_afterlife", null, 2);
        // Material divergence remains open prose: it controls how source material
        // may be reshaped, independently of communication intent and template reuse.
        var divergenceField = labeledTextarea(sec, "sub_divergence",
            function () { return STATE.content_divergence; },
            function (v) { STATE.content_divergence = v; },
            "placeholder_divergence", null, 2);
        if (recommendationFieldLocked("content_divergence")) {
            var divergenceInput = divergenceField.querySelector("textarea");
            if (divergenceInput) {
                divergenceInput.readOnly = true;
                divergenceInput.classList.add("locked-field");
            }
            divergenceField.appendChild(el("div", "toggle-desc locked-field-hint", t("content_divergence_locked_hint")));
        }
        host.appendChild(sec);
    }

    function renderReadingMode(host) {
        if (!isPptCanvas(STATE.canvas)) return;
        var sec = section("D", "delivery_purpose");
        setSectionNote(sec, t("delivery_purpose_hint"));
        enumField(sec, CAT.delivery_purpose,
            recOrFirst("delivery_purpose", CAT.delivery_purpose),
            function () { return STATE.delivery_purpose; },
            function (v) {
                STATE.delivery_purpose = v;
                // Same-stage dependency, resolved entirely in the browser: do
                // not ask the backend to author Stage 2 again. Manual size
                // overrides remain authoritative.
                syncUnpinnedTypographySizes(true);
            });
        host.appendChild(sec);
    }

    function applyDesignDirection(candidate, index, shouldRender) {
        candidate = candidate || {};
        var directionId = designDirectionId(candidate, index);
        if (candidate.mode) {
            STATE.mode = candidate.mode;
            STATE.mode_behavior = candidate.mode === "custom" ?
                directionBehavior(candidate, "mode") : "";
            ACTIVE_COMPONENT_DIRECTION_IDS.mode = directionId;
        }
        if (candidate.visual_style) {
            STATE.visual_style = candidate.visual_style;
            STATE.visual_style_behavior = candidate.visual_style === "custom" ?
                directionBehavior(candidate, "visual_style") : "";
            ACTIVE_COMPONENT_DIRECTION_IDS.visual_style = directionId;
        }
        if (candidate.color) {
            STATE.color = {
                name: localized(candidate.color, "name") || candidate.color.name || "",
                palette: Object.assign({}, normPalette(candidate.color))
            };
        }
        if (candidate.typography) {
            var typography = normTypography(candidate.typography);
            resetTypographySizeOverrides();
            STATE.typography = typography;
            STATE.typography.name = localized(candidate.typography, "name") || typography.name || "";
            STATE.typography.body_size = typography.body_size ||
                defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose);
            STATE.typography.sizes = Object.assign({}, typography.sizes || {});
            syncUnpinnedTypographySizes(true);
        }
        if (candidate.icons) STATE.icons = normalizeRecId("icons", candidate.icons);
        if (candidate.image_strategy) {
            STATE.image_strategy = normalizedImageStrategy(candidate.image_strategy);
            ACTIVE_COMPONENT_DIRECTION_IDS.image_strategy = directionId;
        }
        ACTIVE_DIRECTION_ID = directionId;
        ACTIVE_DIRECTION_BASELINE = directionStateSignature(candidate);
        if (shouldRender !== false) renderAll();
    }

    function renderDesignDirections(host) {
        var candidates = designDirectionCandidates();
        if (!candidates.length) return;
        var sec = section("B", "sec_design_directions", t("design_directions_hint"));
        var grid = el("div", "font-grid design-direction-grid");
        var cardStates = [];
        candidates.forEach(function (candidate, idx) {
            var card = el("div", "font-card design-direction-card");
            card.title = t("direction_reset_hint");
            var head = el("div", "font-card-head");
            head.appendChild(el("span", "font-card-name",
                localized(candidate, "name") || (t("option_prefix") + " " + (idx + 1))));
            var status = el("span", "rec-badge direction-status");
            status.style.display = "none";
            head.appendChild(status);
            card.appendChild(head);
            if (candidate.visual_style) {
                var preview = el("div", "design-direction-preview");
                appendVisualStyleImage(preview, candidate.visual_style);
                card.appendChild(preview);
            }
            var meta = [];
            if (candidate.mode) meta.push(directionComponentValueLabel(candidate, "mode"));
            if (candidate.visual_style) {
                meta.push(directionComponentValueLabel(candidate, "visual_style"));
            }
            if (candidate.icons) meta.push(humanizeId(candidate.icons));
            if (candidate.image_strategy && candidate.image_strategy.rendering) {
                meta.push(comparisonValueLabel("rendering", candidate.image_strategy.rendering));
            }
            if (meta.length) card.appendChild(el("div", "font-card-meta", meta.join(" · ")));
            var palette = normPalette(candidate.color || {});
            var swatches = el("div", "palette-swatches design-direction-swatches");
            PALETTE_ROLES.forEach(function (role) {
                var value = normHex(palette[role]);
                if (!value) return;
                var swatch = el("span", "swatch");
                swatch.style.background = value;
                swatch.title = role + ": " + value;
                swatches.appendChild(swatch);
            });
            if (swatches.childElementCount) card.appendChild(swatches);
            var note = localized(candidate, "note");
            if (note) card.appendChild(el("div", "color-note", note));
            card.addEventListener("click", function () { applyDesignDirection(candidate, idx); });
            cardStates.push({ candidate: candidate, index: idx, card: card, status: status });
            grid.appendChild(card);
        });
        refreshDesignDirectionState = function () {
            cardStates.forEach(function (entry) {
                var active = designDirectionId(entry.candidate, entry.index) === ACTIVE_DIRECTION_ID;
                var adjusted = active && activeDirectionAdjusted(entry.candidate, entry.index);
                entry.card.classList.toggle("selected", active && !adjusted);
                entry.card.classList.toggle("adjusted", adjusted);
                entry.status.style.display = active ? "inline-block" : "none";
                entry.status.textContent = adjusted ? t("direction_adjusted") : t("direction_active");
            });
        };
        refreshDesignDirectionState();
        sec.appendChild(grid);
        host.appendChild(sec);
    }

    function directionComponentMatchesAuthored(candidate, field) {
        if (field === "mode") {
            return STATE.mode === candidate.mode &&
                (candidate.mode !== "custom" ||
                    String(STATE.mode_behavior || "") === directionBehavior(candidate, "mode"));
        }
        if (field === "visual_style") {
            return STATE.visual_style === candidate.visual_style &&
                (candidate.visual_style !== "custom" ||
                    String(STATE.visual_style_behavior || "") ===
                        directionBehavior(candidate, "visual_style"));
        }
        if (field === "image_strategy") {
            return JSON.stringify(comparableImageStrategy(STATE.image_strategy || {})) ===
                JSON.stringify(comparableImageStrategy(candidate.image_strategy || {}));
        }
        return false;
    }

    function directionComponentSelected(candidate, field, index) {
        var activeId = ACTIVE_COMPONENT_DIRECTION_IDS[field];
        if (activeId) return activeId === designDirectionId(candidate, index);
        return directionComponentMatchesAuthored(candidate, field);
    }

    function applyDirectionComponent(candidate, field, index) {
        if (field === "mode") {
            STATE.mode = candidate.mode;
            STATE.mode_behavior = candidate.mode === "custom" ?
                directionBehavior(candidate, "mode") : "";
        } else if (field === "visual_style") {
            STATE.visual_style = candidate.visual_style;
            STATE.visual_style_behavior = candidate.visual_style === "custom" ?
                directionBehavior(candidate, "visual_style") : "";
        } else if (field === "image_strategy") {
            STATE.image_strategy = normalizedImageStrategy(candidate.image_strategy || {});
        }
        ACTIVE_COMPONENT_DIRECTION_IDS[field] = designDirectionId(candidate, index);
        renderAll();
    }

    function directionComponentIsCustom(candidate, field) {
        if (field === "image_strategy") {
            return candidate && candidate.image_strategy &&
                candidate.image_strategy.rendering === "custom";
        }
        return candidate && candidate[field] === "custom";
    }

    function setDirectionComponentBehavior(field, value) {
        if (field === "mode") {
            STATE.mode = "custom";
            STATE.mode_behavior = value;
        } else if (field === "visual_style") {
            STATE.visual_style = "custom";
            STATE.visual_style_behavior = value;
        } else if (field === "image_strategy") {
            STATE.image_strategy = normalizedImageStrategy(STATE.image_strategy || {});
            STATE.image_strategy.rendering = "custom";
            STATE.image_strategy.behavior = value;
        }
    }

    function directionComponentValueLabel(candidate, field) {
        var value = candidate && candidate[field];
        if (field === "image_strategy") {
            value = value && value.rendering;
            return comparisonValueLabel("rendering", value);
        }
        var catalog = field === "mode" ? CAT.modes : CAT.visual_styles;
        var option = findCatalogOption(catalog, value);
        return option ? optionLabel(option) : (value === "custom" ? t("custom") : humanizeId(value));
    }

    function directionComponentNote(candidate, field) {
        if (field === "image_strategy") {
            var strategy = normalizedImageStrategy(candidate.image_strategy || {});
            return [strategy.visual, strategy.mood, strategy.behavior].filter(Boolean).join(" · ");
        }
        if (candidate[field] === "custom") return directionBehavior(candidate, field);
        return localized(candidate, "note") || "";
    }

    function directionComponentEditableBehavior(candidate, field) {
        if (field === "image_strategy") {
            return normalizedImageStrategy(candidate.image_strategy || {}).behavior || "";
        }
        return directionBehavior(candidate, field);
    }

    function renderDirectionComponentCandidates(parent, field) {
        var candidates = designDirectionCandidates().filter(function (candidate) {
            return candidate && candidate[field];
        });
        if (!candidates.length) return;
        var block = el("div", "subfield scheme-component-options");
        block.appendChild(el("div", "subfield-label", t("scheme_component_options")));
        var grid = el("div", "font-grid scheme-component-grid");
        var entries = [];
        candidates.forEach(function (candidate, index) {
            var card = el("div", "font-card scheme-component-card");
            card.dataset.candidateId = designDirectionId(candidate, index) + ":" + field;
            var head = el("div", "font-card-head");
            head.appendChild(el("span", "font-card-name",
                localized(candidate, "name") || (t("option_prefix") + " " + (index + 1))));
            head.appendChild(el("span", "font-card-meta",
                directionComponentValueLabel(candidate, field)));
            card.appendChild(head);
            if (field === "visual_style" && candidate.visual_style !== "custom") {
                var preview = el("div", "design-direction-preview");
                appendVisualStyleImage(preview, candidate.visual_style);
                card.appendChild(preview);
            }
            var note = directionComponentNote(candidate, field);
            var noteNode = note ? el("div", "color-note", note) : null;
            if (noteNode) card.appendChild(noteNode);
            var editor = null;
            if (directionComponentIsCustom(candidate, field)) {
                editor = el("textarea", "text-input scheme-component-editor");
                setNaturalInputDirection(editor);
                editor.rows = 4;
                editor.value = directionComponentEditableBehavior(candidate, field);
                editor.placeholder = t(field === "mode" ? "mode_behavior_placeholder" :
                    (field === "visual_style" ? "visual_style_behavior_placeholder" :
                        "image_strategy_custom_placeholder"));
                editor.style.display = "none";
                editor.addEventListener("click", function (event) {
                    event.stopPropagation();
                });
                editor.addEventListener("input", function () {
                    setDirectionComponentBehavior(field, editor.value);
                    if (field === "image_strategy") refreshImageStrategyPreview();
                    refreshDesignDirectionState();
                    refreshDirectionComponentStates();
                });
                card.appendChild(editor);
            }
            card.addEventListener("click", function () {
                applyDirectionComponent(candidate, field, index);
            });
            entries.push({
                candidate: candidate,
                index: index,
                card: card,
                note: noteNode,
                editor: editor
            });
            grid.appendChild(card);
        });
        var paint = function () {
            entries.forEach(function (entry) {
                var selected = directionComponentSelected(
                    entry.candidate, field, entry.index
                );
                var adjusted = selected &&
                    !directionComponentMatchesAuthored(entry.candidate, field);
                entry.card.classList.toggle("selected", selected);
                entry.card.classList.toggle("adjusted", adjusted);
                if (entry.editor) {
                    entry.editor.style.display = selected ? "block" : "none";
                    if (selected && document.activeElement !== entry.editor) {
                        var current = field === "mode" ? STATE.mode_behavior :
                            (field === "visual_style" ? STATE.visual_style_behavior :
                                ((STATE.image_strategy || {}).behavior || ""));
                        entry.editor.value = current;
                    }
                }
                if (entry.note) entry.note.style.display = selected ? "none" : "block";
            });
        };
        DIRECTION_COMPONENT_PAINTERS.push(paint);
        paint();
        block.appendChild(grid);
        parent.appendChild(block);
    }

    function currentDirectionCustomCandidate(field, stateKey) {
        if (STATE[field] !== "custom") return null;
        return designDirectionCandidates().filter(function (candidate) {
            return candidate && candidate[field] === "custom" &&
                directionBehavior(candidate, field) === String(STATE[stateKey] || "");
        })[0];
    }

    function renderCurrentDirectionCustomEditor(parent, field, stateKey, placeholderKey) {
        if (STATE[field] !== "custom") return null;
        if (ACTIVE_COMPONENT_DIRECTION_IDS[field]) return null;
        var source = currentDirectionCustomCandidate(field, stateKey);
        if (!source && customCandidateBehavior(field)) return null;
        var block = el("div", "subfield direction-custom-editor");
        var label = t("custom");
        if (source && localized(source, "name")) {
            label = localized(source, "name") + " · " + label;
        }
        block.appendChild(el("div", "subfield-label", label));
        var input = el("textarea", "text-input custom-input");
        setNaturalInputDirection(input);
        input.rows = 4;
        input.placeholder = t(placeholderKey);
        input.value = STATE[stateKey] || "";
        input.style.display = "block";
        input.addEventListener("input", function () {
            STATE[stateKey] = input.value;
            refreshDesignDirectionState();
            refreshDirectionComponentStates();
        });
        block.appendChild(input);
        parent.appendChild(block);
        return block;
    }

    function renderNarrativeDirection(host) {
        var sec = section(4, "sec_narrative");
        renderDirectionComponentCandidates(sec, "mode");
        var directionCustomEditor = null;
        var custom = currentDirectionCustomCandidate("mode", "mode_behavior") ? null :
            creativeCustomOptions("mode", "mode_behavior", "mode_behavior_placeholder");
        enumField(sec, CAT.modes, recOrFirst("mode", CAT.modes),
            function () { return STATE.mode; }, function (v) {
                STATE.mode = v;
                ACTIVE_COMPONENT_DIRECTION_IDS.mode = "";
                if (v !== "custom") STATE.mode_behavior = "";
                refreshDesignDirectionState();
                refreshDirectionComponentStates();
                if (directionCustomEditor) {
                    directionCustomEditor.style.display = v === "custom" ? "block" : "none";
                }
            },
            {
                allowCustom: !!custom,
                customOnOwnRow: true,
                customSentinel: "custom",
                preserveCustom: true,
                placeholder: t("mode_behavior_placeholder"),
                aiCustom: custom
            });
        directionCustomEditor = renderCurrentDirectionCustomEditor(
            sec, "mode", "mode_behavior", "mode_behavior_placeholder"
        );
        host.appendChild(sec);
    }

    function renderVisualDirection(host) {
        var sec = section(5, "sec_visual");
        renderDirectionComponentCandidates(sec, "visual_style");
        var directionCustomEditor = null;
        var custom = currentDirectionCustomCandidate(
            "visual_style", "visual_style_behavior"
        ) ? null : creativeCustomOptions(
                "visual_style", "visual_style_behavior", "visual_style_behavior_placeholder"
        );
        enumField(sec, CAT.visual_styles, recOrFirst("visual_style", CAT.visual_styles),
            function () { return STATE.visual_style; }, function (v) {
                STATE.visual_style = v;
                ACTIVE_COMPONENT_DIRECTION_IDS.visual_style = "";
                if (v !== "custom") STATE.visual_style_behavior = "";
                refreshDesignDirectionState();
                refreshDirectionComponentStates();
                if (directionCustomEditor) {
                    directionCustomEditor.style.display = v === "custom" ? "block" : "none";
                }
            },
            {
                allowCustom: !!custom,
                customOnOwnRow: true,
                customSentinel: "custom",
                preserveCustom: true,
                placeholder: t("visual_style_behavior_placeholder"),
                aiCustom: custom,
                preview: "visual_style",
                chipsClass: "visual-style-grid"
            });
        directionCustomEditor = renderCurrentDirectionCustomEditor(
            sec, "visual_style", "visual_style_behavior",
            "visual_style_behavior_placeholder"
        );
        host.appendChild(sec);
    }

    var PALETTE_ROLES = [
        "background",
        "secondary_bg",
        "primary",
        "accent",
        "secondary_accent",
        "body_text"
    ];

    function normHex(val) {
        var v = (val || "").trim();
        if (!/^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/.test(v)) return null;
        return v.charAt(0) === "#" ? v : "#" + v;
    }
    function hexOr(val, fallback) {
        return normHex(val) || fallback;
    }
    // Replaced when the combined color+typography preview mounts; the color and
    // typography sections call it after every change so the preview stays live.
    var refreshStylePreview = function () {};
    // Replaced when the selected generated-image preview mounts.
    var refreshImageStrategyPreview = function () {};
    // Replaced when the final plan's image-production section mounts; image-use
    // edits call it so the conditional AI path stays synchronized on the page.
    var refreshImageProduction = function () {};
    // Replaced when the typography section mounts; the canvas section calls it so
    // the body-size hint tracks the chosen canvas height.
    var refreshBodySizeHint = function () {};
    // Replaced when the typography section mounts; body-size / reading-mode
    // changes call it so unpinned per-role values update locally.
    var refreshSizeInputs = function () {};

    // Per-role size slots the user can edit directly (parallel to color roles).
    // Defaults derive from `body` via mid-band ramp ratios (strategist.md §g);
    // values are px (the system's only unit).
    var SIZE_ROLES = ["title", "subtitle", "annotation"];
    var SIZE_RATIO = { title: 1.75, subtitle: 1.35, annotation: 0.78 };
    var TYPOGRAPHY_SIZE_OVERRIDES = {
        body: false,
        title: false,
        subtitle: false,
        annotation: false
    };

    function resetTypographySizeOverrides() {
        Object.keys(TYPOGRAPHY_SIZE_OVERRIDES).forEach(function (role) {
            TYPOGRAPHY_SIZE_OVERRIDES[role] = false;
        });
    }

    function deriveSize(role, bodyVal) {
        var raw = (bodyVal || 0) * (SIZE_RATIO[role] || 1);
        // All px. On PPT, snap the recommended role size to a clean even number so
        // the user sees conventional sizes (body 24 → title 42, subtitle 32), not
        // ratio leftovers. Non-PPT keeps a plain integer — large px, snapping moot.
        if (isPptCanvas(STATE.canvas)) return Math.round(raw / 2) * 2;
        return Math.round(raw);
    }

    // Canvas height (viewBox user units) parsed from a catalog `dim` like
    // "1242×1660" or from a custom canvas string containing WxH; null if unknown.
    function canvasHeight(canvasVal) {
        var dim = null;
        (CAT.canvas || []).forEach(function (o) { if (o.id === canvasVal) dim = o.dim; });
        var m = String(dim || canvasVal || "").match(/(\d{2,5})\s*[×xX*]\s*(\d{2,5})/);
        return m ? parseInt(m[2], 10) : null;
    }

    function bodySizeRatioBand(canvasVal) {
        var dim = null;
        (CAT.canvas || []).forEach(function (o) { if (o.id === canvasVal) dim = o.dim; });
        var raw = String(dim || canvasVal || "");
        var id = String(canvasVal || "").toLowerCase();
        var isPpt = id === "ppt169" || id === "ppt43" ||
            /1280\s*[×xX*]\s*720/.test(raw) ||
            /1024\s*[×xX*]\s*768/.test(raw);
        return isPpt ? { lo: 0.031, hi: 0.047 } : { lo: 0.025, hi: 0.033 };
    }

    // PPT canvases (16:9 / 4:3) take the fixed per-reading-mode body px;
    // social / print canvases scale the body px by canvas height instead.
    function isPptCanvas(canvasVal) {
        var dim = null;
        (CAT.canvas || []).forEach(function (o) { if (o.id === canvasVal) dim = o.dim; });
        var raw = String(dim || canvasVal || "");
        var id = String(canvasVal || "").toLowerCase();
        return id === "ppt169" || id === "ppt43" ||
            /1280\s*[×xX*]\s*720/.test(raw) ||
            /1024\s*[×xX*]\s*768/.test(raw);
    }

    // Body baseline in **px** per reading mode (legacy key:
    // delivery_purpose; see strategist.md §g). The
    // system is px-only — these are the SVG/execution px values, recalibrated for
    // the 1280×720 PPT canvas. No pt layer, no conversion. `def` is the fixed
    // recommendation; lo/hi are a sanity envelope for the out-of-range flag only.
    function deliveryBodyPx(purposeId) {
        if (purposeId === "text") return { lo: 18, hi: 21, def: 20 };
        if (purposeId === "presentation") return { lo: 28, hi: 32, def: 32 };
        return { lo: 22, hi: 25, def: 24 }; // balanced — the default
    }

    function defaultBodySizeForCanvas(canvasVal, purposeId) {
        if (isPptCanvas(canvasVal)) return deliveryBodyPx(purposeId).def;
        var h = canvasHeight(canvasVal);
        if (!h) return 40;
        var band = bodySizeRatioBand(canvasVal);
        return Math.round(h * (band.lo + band.hi) / 2);
    }

    // Resolve the only deterministic same-stage size dependency locally. The
    // backend authors Stage 2 once; changing reading mode or body size updates
    // only unpinned values already visible in this page.
    function syncUnpinnedTypographySizes(resetBodyFromReadingMode) {
        if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
        if (!STATE.typography.sizes) STATE.typography.sizes = {};
        if (resetBodyFromReadingMode && !TYPOGRAPHY_SIZE_OVERRIDES.body) {
            STATE.typography.body_size = defaultBodySizeForCanvas(
                STATE.canvas, STATE.delivery_purpose
            );
        }
        var body = parseFloat(STATE.typography.body_size);
        if (!isFinite(body)) {
            body = defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose);
        }
        SIZE_ROLES.forEach(function (role) {
            if (!TYPOGRAPHY_SIZE_OVERRIDES[role]) {
                STATE.typography.sizes[role] = deriveSize(role, body);
            }
        });
        refreshSizeInputs();
        refreshBodySizeHint();
        refreshStylePreview();
    }

    function roundSize(value) {
        return Math.round(value * 100) / 100;
    }

    function formatPtFromPx(value) {
        var px = parseFloat(value);
        if (!isFinite(px)) return "";
        var pt = Math.round(px * 0.75 * 10) / 10;
        return pt % 1 === 0 ? String(Math.round(pt)) : String(pt);
    }

    function normalizeTypographyForSubmit(payload) {
        if (!payload.typography || typeof payload.typography !== "object") return;
        var typ = normTypography(payload.typography);
        payload.typography = typ;
        if (isEnglishProject()) {
            ["heading", "body"].forEach(function (role) {
                delete typ[role].english;
                delete typ[role].sample_english;
            });
        }
        var body = parseFloat(typ.body_size);
        if (!isFinite(body)) {
            // Cleared / invalid body field — fall back so role sizes never submit
            // against an empty anchor.
            body = defaultBodySizeForCanvas(payload.canvas, payload.delivery_purpose);
        }
        // px is the only unit — round and submit as-is. No pt conversion, no
        // body_size_pt / sizes_pt provenance (the system never carries pt).
        typ.body_size = roundSize(body);
        typ.body_size_unit = "px";
        if (typ.sizes && typeof typ.sizes === "object") {
            Object.keys(typ.sizes).forEach(function (role) {
                var raw = parseFloat(typ.sizes[role]);
                if (isFinite(raw)) typ.sizes[role] = roundSize(raw);
            });
        }
        if (typographyFamiliesComplete(typ)) delete typ.custom;
        // delivery_purpose is PPT-only; drop it on non-PPT canvases where it has
        // no meaning and was never shown.
        if (!isPptCanvas(payload.canvas)) delete payload.delivery_purpose;
    }

    function renderColor(host) {
        var cands = colorRecommendationCandidates();
        var sec = section(5, "sec_color");
        var grid = el("div", "color-grid");
        var hexInputs = {};
        var hexSwatches = {};
        var cardSwatchRefs = [];   // idx -> {role: swatchEl}, for live override feedback
        var selectedIdx = -1;

        function paintSwatch(elem, val) {
            var n = normHex(val);
            elem.style.background = n || "transparent";
            elem.classList.toggle("hex-swatch-empty", !n);
        }
        function applyHexInputs(pal) {
            PALETTE_ROLES.forEach(function (role) {
                if (hexInputs[role]) hexInputs[role].value = pal[role] || "";
                if (hexSwatches[role]) paintSwatch(hexSwatches[role], pal[role]);
            });
        }
        var customInput = el("textarea", "text-input custom-color-input");
        setNaturalInputDirection(customInput);
        customInput.rows = 2;
        customInput.placeholder = t("custom_color_placeholder");
        customInput.style.display = "none";

        function selectCard(idx) {
            var c = cands[idx] || {};
            selectedIdx = idx;
            STATE.color = {
                name: localized(c, "name") || c.name || "",
                palette: Object.assign({}, normPalette(c))
            };
            grid.querySelectorAll(".color-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
            customInput.style.display = "none";
            applyHexInputs(STATE.color.palette);
            refreshStylePreview();
        }

        function selectCustomColor() {
            selectedIdx = -1;
            STATE.color = { name: "custom", custom: customInput.value || "", palette: {} };
            grid.querySelectorAll(".color-card").forEach(function (card) { card.classList.remove("selected"); });
            customCard.classList.add("selected");
            customInput.style.display = "block";
            customInput.focus();
            refreshStylePreview();
        }

        cands.forEach(function (c, idx) {
            var pal = normPalette(c);
            var refs = {};
            var card = el("div", "color-card");
            var sw = el("div", "swatches");
            PALETTE_ROLES.forEach(function (role) {
                if (!pal[role]) return;
                var col = el("div", "swatch-col");
                var s = el("div", "swatch"); s.style.background = pal[role];
                refs[role] = s;
                col.appendChild(s);
                col.appendChild(el("div", "swatch-role", t("role_" + role)));
                col.appendChild(el("div", "color-hex", normHex(pal[role]) || pal[role]));
                sw.appendChild(col);
            });
            cardSwatchRefs[idx] = refs;
            card.appendChild(sw);
            card.appendChild(el("div", "color-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            if (localized(c, "note")) card.appendChild(el("div", "color-note", localized(c, "note")));
            card.addEventListener("click", function () { selectCard(idx); });
            grid.appendChild(card);
        });
        var customCard = el("div", "color-card color-card-custom");
        customCard.appendChild(el("div", "color-name", t("custom_color")));
        customCard.addEventListener("click", selectCustomColor);
        grid.appendChild(customCard);
        sec.appendChild(grid);
        customInput.addEventListener("input", function () {
            if (!STATE.color || STATE.color.name !== "custom") selectCustomColor();
            STATE.color.custom = customInput.value;
            refreshStylePreview();
        });
        sec.appendChild(customInput);

        var override = el("div", "hex-override");
        override.appendChild(el("div", "subfield-label", t("hex_override")));
        var row = el("div", "hex-row");
        PALETTE_ROLES.forEach(function (role) {
            var wrap = el("div", "hex-cell");
            wrap.appendChild(el("div", "hex-cell-label", t("role_" + role)));
            var line = el("div", "hex-input-line");
            var sw = el("div", "hex-swatch hex-swatch-empty");
            var inp = document.createElement("input");
            inp.type = "text"; inp.placeholder = "#";
            inp.addEventListener("input", function () {
                if (!STATE.color) STATE.color = { name: "custom", palette: {} };
                if (!STATE.color.palette) STATE.color.palette = {};
                STATE.color.palette[role] = inp.value;
                paintSwatch(sw, inp.value);
                // Reflect a valid override straight onto the selected card so the
                // user sees the change in context, not just in the input row.
                var n = normHex(inp.value);
                if (n && selectedIdx >= 0 && cardSwatchRefs[selectedIdx] && cardSwatchRefs[selectedIdx][role]) {
                    cardSwatchRefs[selectedIdx][role].style.background = n;
                }
                refreshStylePreview();
            });
            hexInputs[role] = inp; hexSwatches[role] = sw;
            line.appendChild(sw); line.appendChild(inp);
            wrap.appendChild(line); row.appendChild(wrap);
        });
        override.appendChild(row);
        sec.appendChild(override);
        host.appendChild(sec);

        var selIdx = -1;
        if (STATE.color && STATE.color.name && STATE.color.name !== "custom") {
            cands.forEach(function (c, i) {
                if ((localized(c, "name") || c.name) === STATE.color.name) selIdx = i;
            });
        }
        if (STATE.color && STATE.color.name === "custom") {
            customInput.value = STATE.color.custom || "";
            selectCustomColor();
        } else if (selIdx >= 0) {
            selectCard(selIdx);
        } else {
            applyHexInputs((STATE.color && STATE.color.palette) || {});
        }
    }

    function renderIcons(host) {
        var sec = section(6, "sec_icons");
        enumField(sec, CAT.icons, recOrFirst("icons", CAT.icons),
            function () { return STATE.icons; }, function (v) { STATE.icons = v; refreshStylePreview(); },
            { allowCustom: true, customOnOwnRow: true, ownRowIds: ["none"] });
        host.appendChild(sec);
    }

    function previewFontStack(primary, fallback) {
        if (!primary) return fallback || "";
        if (!fallback) return primary;
        return primary + ", " + fallback;
    }

    function typographyFamiliesComplete(typography) {
        typography = normTypography(typography || {});
        return ["heading", "body"].every(function (role) {
            var font = typography[role] || {};
            var fields = isEnglishProject() ? ["primary", "css"] :
                ["primary", "english", "css"];
            return fields.every(function (field) {
                return !!String(font[field] || "").trim();
            });
        });
    }

    function sampleText(role, field) {
        // Keep comparison copy stable: choices change visual treatment, not content.
        var useEnglish = field === "english" || isEnglishProject();
        if (role === "heading") {
            return t(useEnglish ? "preview_latin_title" : "preview_big_title");
        }
        return t(useEnglish ? "preview_latin_body" : "preview_body_intro");
    }

    function fontSample(box, slot, css, role) {
        var line = el("div", "font-sample-line");
        var primary = el("span", "fs-primary", sampleText(role, "primary"));
        setUiLanguageAttributes(primary);
        var primaryStack = previewFontStack(slot.primary, css);
        if (primaryStack) primary.style.fontFamily = primaryStack;
        if (primaryStack) primary.title = primaryStack;
        line.appendChild(primary);
        if (!isEnglishProject()) {
            var english = el("span", "fs-english", sampleText(role, "english"));
            setEnglishLanguageAttributes(english);
            var englishStack = previewFontStack(slot.english, css);
            if (englishStack) english.style.fontFamily = englishStack;
            if (englishStack) english.title = englishStack;
            line.appendChild(english);
        }
        box.appendChild(line);
    }

    function fontChoiceLabel(font) {
        var label = localized(font, "label") || font.id;
        if (String(label).toLowerCase() === String(font.id).toLowerCase()) {
            return String(font.id);
        }
        return label + " · " + font.id;
    }

    function typographyFieldLabel(field) {
        if (field === "english") return t("english_font");
        return t("primary_language_font");
    }

    function typographyChoiceConfigs() {
        var configs = [];
        ["heading", "body"].forEach(function (role) {
            configs.push([role, "primary"]);
            if (!isEnglishProject()) configs.push([role, "english"]);
        });
        return configs;
    }

    function typographySignature(typography) {
        typography = normTypography(typography || {});
        var fields = isEnglishProject() ? ["primary"] : ["primary", "english"];
        var values = [];
        ["heading", "body"].forEach(function (role) {
            fields.forEach(function (field) {
                values.push(String((typography[role] || {})[field] || "")
                    .trim().toLowerCase());
            });
        });
        return values.join("\u0000");
    }

    function renderTypography(host) {
        var cands = typographyRecommendationCandidates().filter(typographyFamiliesComplete);
        var sec = section(7, "sec_type");
        var grid = el("div", "font-grid");
        var customFields = el("div", "custom-typography-fields font-picker-fields");
        var customInputs = {};
        var customLegacyNote = el("div", "toggle-desc custom-typography-legacy");
        var pickerHead = el("div", "font-picker-head");
        pickerHead.appendChild(el("span", "subfield-label", t("font_selection")));
        var customStatus = el("span", "font-custom-status", t("customized"));
        pickerHead.appendChild(customStatus);
        customFields.appendChild(pickerHead);
        customFields.appendChild(el("div", "toggle-desc font-picker-hint", t("font_picker_hint")));
        customFields.appendChild(customLegacyNote);

        function syncCustomInputs() {
            var typography = STATE.typography || {};
            customLegacyNote.textContent = String(typography.custom || "").trim();
            customLegacyNote.style.display = customLegacyNote.textContent ? "block" : "none";
            customStatus.style.display = typography.name === "custom" ? "inline-flex" : "none";
            typographyChoiceConfigs().forEach(function (config) {
                var role = config[0], field = config[1];
                var control = customInputs[role + "_" + field];
                if (!control) return;
                var value = String((typography[role] || {})[field] || "");
                var matchingFont = control.options.filter(function (font) {
                    return String(font.id).toLowerCase() === value.toLowerCase();
                })[0];
                control.select.value = matchingFont ? matchingFont.id : "__other__";
                control.other.value = matchingFont ? "" : value;
                control.other.style.display = matchingFont ? "none" : "block";
            });
        }

        function markCustomTypography() {
            if (!STATE.typography) {
                STATE.typography = { name: "custom", heading: {}, body: {} };
            }
            STATE.typography.name = "custom";
            grid.querySelectorAll(".font-card").forEach(function (card) {
                card.classList.remove("selected");
            });
            customCard.classList.add("selected");
            customStatus.style.display = "inline-flex";
        }

        function updateRoleCss(role) {
            if (!STATE.typography[role]) STATE.typography[role] = {};
            STATE.typography[role].css = derivedFontCss(STATE.typography[role]);
        }

        function selectFont(idx) {
            var c = normTypography(cands[idx] || {});
            var prev = STATE.typography || {};
            STATE.typography = {
                name: localized(c, "name") || c.name || "",
                heading: c.heading || {},
                body: c.body || {},
                // Font cards choose family and character. Reading mode and
                // explicit size inputs own the sizing state.
                body_size: prev.body_size ||
                    defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose),
                sizes: Object.assign({}, prev.sizes || {})
            };
            if (sizeInput) sizeInput.value = STATE.typography.body_size || "";
            grid.querySelectorAll(".font-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
            syncCustomInputs();
            refreshSizeInputs();   // fill any role with no value yet; never overwrites existing values
            refreshStylePreview();
        }

        function selectCustomTypography() {
            var prev = STATE.typography || {};
            STATE.typography = normTypography(prev);
            STATE.typography.name = "custom";
            STATE.typography.body_size = prev.body_size || "";
            // Switching font family must not drop any explicit size.
            STATE.typography.sizes = Object.assign({}, prev.sizes || {});
            markCustomTypography();
            syncCustomInputs();
            var firstControl = customInputs.heading_primary;
            if (firstControl) firstControl.select.focus();
            refreshSizeInputs();
            refreshStylePreview();
        }

        cands.forEach(function (c, idx) {
            c = normTypography(c);
            var head = c.heading || {}, body = c.body || {};
            var card = el("div", "font-card");
            var top = el("div", "font-card-head");
            top.appendChild(el("span", "font-card-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            var metaFields = isEnglishProject() ? ["primary"] : ["primary", "english"];
            var meta = ["heading", "body"].map(function (role) {
                var slot = role === "heading" ? head : body;
                return t("font_" + role) + " " + metaFields.map(function (field) {
                    return typographyFieldLabel(field) + ": " + (slot[field] || "—");
                }).join(" / ");
            }).join("  ·  ");
            top.appendChild(el("span", "font-card-meta", meta));
            card.appendChild(top);
            var hbox = el("div", "font-sample-heading-box"); fontSample(hbox, head, head.css, "heading"); card.appendChild(hbox);
            var bbox = el("div", "font-sample-body-box"); fontSample(bbox, body, body.css, "body"); card.appendChild(bbox);
            if (localized(c, "note")) card.appendChild(el("div", "color-note", localized(c, "note")));
            card.addEventListener("click", function () { selectFont(idx); });
            grid.appendChild(card);
        });
        var customCard = el("div", "font-card font-card-custom");
        customCard.appendChild(el("div", "font-card-name", t("custom_typography")));
        customCard.addEventListener("click", selectCustomTypography);
        grid.appendChild(customCard);
        sec.appendChild(grid);
        typographyChoiceConfigs().forEach(function (config) {
            var role = config[0], fieldName = config[1];
            var field = el("label", "custom-typography-field");
            field.appendChild(el("span", "hex-cell-label",
                t("font_" + role) + " · " + typographyFieldLabel(fieldName)));
            var options = fontCatalogEntries(fieldName);
            var select = el("select", "font-select");
            options.forEach(function (font) {
                var option = document.createElement("option");
                option.value = font.id;
                option.textContent = fontChoiceLabel(font);
                select.appendChild(option);
            });
            var otherOption = document.createElement("option");
            otherOption.value = "__other__";
            otherOption.textContent = t("other_installed_font");
            select.appendChild(otherOption);
            var input = el("input", "text-input other-font-input");
            input.type = "text";
            input.placeholder = t("other_font_placeholder");
            select.addEventListener("change", function () {
                markCustomTypography();
                if (!STATE.typography[role]) {
                    STATE.typography[role] = { css: "sans-serif" };
                }
                if (select.value === "__other__") {
                    input.value = "";
                    input.style.display = "block";
                    STATE.typography[role][fieldName] = "";
                    input.focus();
                } else {
                    input.value = "";
                    input.style.display = "none";
                    STATE.typography[role][fieldName] = select.value;
                }
                updateRoleCss(role);
                refreshStylePreview();
            });
            input.addEventListener("input", function () {
                markCustomTypography();
                if (!STATE.typography[role]) {
                    STATE.typography[role] = { css: "sans-serif" };
                }
                STATE.typography[role][fieldName] = input.value;
                updateRoleCss(role);
                refreshStylePreview();
            });
            customInputs[role + "_" + fieldName] = {
                select: select,
                other: input,
                options: options
            };
            field.appendChild(select);
            field.appendChild(input);
            customFields.appendChild(field);
        });
        sec.appendChild(customFields);

        var sizeField = el("div", "subfield");
        sizeField.appendChild(el("div", "subfield-label", t("font_body_size")));
        sizeField.appendChild(el("div", "toggle-desc body-size-relation", t("body_size_unit_relation")));
        var sizeRow = el("div", "font-size-row");
        var sizeInput = el("input", "num-input font-size-input");
        sizeInput.type = "number";
        sizeInput.min = "8";
        sizeInput.max = "96";
        sizeInput.step = "1";
        sizeInput.value = (STATE.typography && STATE.typography.body_size) || "";
        sizeInput.placeholder = isPptCanvas(STATE.canvas) ? "20 / 24 / 32" : "40 / 48";
        sizeInput.addEventListener("input", function () {
            if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
            STATE.typography.body_size = sizeInput.value;
            TYPOGRAPHY_SIZE_OVERRIDES.body = sizeInput.value !== "";
            // Body is an explicit local anchor. Recompute only role values the
            // user has not edited; no request leaves the browser.
            syncUnpinnedTypographySizes(false);
        });
        sizeRow.appendChild(sizeInput);
        sizeRow.appendChild(el("span", "font-size-unit", "px"));
        var sizePtHint = el("div", "toggle-desc body-size-pt");
        var sizeHint = el("div", "toggle-desc body-size-hint");
        // PPT body is one fixed px value per reading mode (not a range); non-PPT
        // canvases scale px to canvas height. A manually pinned value is never
        // overwritten by later reading-mode changes.
        // Everything is px — lo/hi are only a sanity envelope for the OOR flag.
        refreshBodySizeHint = function () {
            var txt = t("font_body_size_hint");
            var lo, hi;
            if (isPptCanvas(STATE.canvas)) {
                var pb = deliveryBodyPx(STATE.delivery_purpose);
                lo = pb.lo; hi = pb.hi;
                txt += " " + t("body_size_hint_purpose").replace("{def}", pb.def);
            } else {
                var h = canvasHeight(STATE.canvas);
                var band = bodySizeRatioBand(STATE.canvas);
                if (h) {
                    lo = Math.round(h * band.lo); hi = Math.round(h * band.hi);
                    txt += " " + t("body_size_hint_canvas")
                        .replace("{lo}", lo).replace("{hi}", hi);
                }
            }
            // Flag (hint only) a value far outside the
            // canvas's usual px range, so an accidental extreme value is visible
            // instead of silently submitting it.
            var cur = parseFloat(STATE.typography && STATE.typography.body_size);
            sizePtHint.textContent = isFinite(cur)
                ? t("body_size_pt_hint").replace("{pt}", formatPtFromPx(cur))
                : "";
            if (isFinite(cur) && isFinite(lo) && isFinite(hi) && (cur < lo || cur > hi)) {
                txt += " " + t("body_size_hint_oor");
            }
            sizeHint.textContent = txt;
        };
        refreshBodySizeHint();
        sizeField.appendChild(sizeRow);
        sizeField.appendChild(sizePtHint);
        sizeField.appendChild(sizeHint);

        // Reading mode and typography are both confirmed in Stage 2. Its
        // compatibility key remains delivery_purpose; the dependency is a local
        // deterministic update, not a second Stage-2 recommendation.
        sec.appendChild(sizeField);

        // Per-role size override (parallel to color's per-role HEX override): the
        // ramp derives title / subtitle / annotation from body, but the user may
        // set each explicitly. Values are px (the system's only unit).
        var sizeOverride = el("div", "hex-override");
        sizeOverride.appendChild(el("div", "subfield-label", t("size_override")));
        var srow = el("div", "hex-row");
        var sizeInputs = {};
        var sizePtHints = {};
        function refreshRolePtHint(role) {
            var input = sizeInputs[role];
            var hint = sizePtHints[role];
            if (!input || !hint) return;
            var pt = formatPtFromPx(input.value);
            hint.textContent = pt ? t("role_size_pt_hint").replace("{pt}", pt) : "";
        }
        SIZE_ROLES.forEach(function (role) {
            var wrap = el("div", "hex-cell");
            wrap.appendChild(el("div", "hex-cell-label", t("size_role_" + role)));
            var inputLine = el("div", "role-size-line");
            var inp = document.createElement("input");
            inp.type = "number"; inp.min = "6"; inp.max = "200"; inp.step = "1";
            inp.addEventListener("input", function () {
                if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
                if (!STATE.typography.sizes) STATE.typography.sizes = {};
                STATE.typography.sizes[role] = inp.value;
                TYPOGRAPHY_SIZE_OVERRIDES[role] = true;
                refreshRolePtHint(role);
                refreshStylePreview();
            });
            sizeInputs[role] = inp;
            inputLine.appendChild(inp);
            inputLine.appendChild(el("span", "font-size-unit", "px"));
            wrap.appendChild(inputLine);
            sizePtHints[role] = el("div", "role-size-pt");
            wrap.appendChild(sizePtHints[role]);
            srow.appendChild(wrap);
        });
        sizeOverride.appendChild(srow);
        sec.appendChild(sizeOverride);

        // Reflect state into the controls. Derivation itself happens only through
        // syncUnpinnedTypographySizes(); a re-render preserves the visible state.
        refreshSizeInputs = function () {
            if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
            if (!STATE.typography.sizes) STATE.typography.sizes = {};
            sizeInput.value = STATE.typography.body_size || "";
            var bodyVal = parseFloat(STATE.typography.body_size) ||
                (isPptCanvas(STATE.canvas) ? deliveryBodyPx(STATE.delivery_purpose).def : 40);
            SIZE_ROLES.forEach(function (role) {
                var cur = STATE.typography.sizes[role];
                var hasVal = cur !== undefined && cur !== null && cur !== "";
                if (!hasVal) STATE.typography.sizes[role] = deriveSize(role, bodyVal);
                if (sizeInputs[role]) sizeInputs[role].value = STATE.typography.sizes[role];
                refreshRolePtHint(role);
            });
        };
        refreshSizeInputs();

        host.appendChild(sec);

        var nameMatch = -1;
        var signatureMatch = -1;
        var stateSignature = typographySignature(STATE.typography || {});
        if (STATE.typography && STATE.typography.name !== "custom") cands.forEach(function (c, i) {
            var sameName = [localized(c, "name"), c.name_zh, c.name_en, c.name_ja]
                .some(function (name) { return name === STATE.typography.name; });
            if (!sameName && c.name && typeof c.name === "object") {
                sameName = Object.keys(c.name).some(function (key) {
                    return c.name[key] === STATE.typography.name;
                });
            }
            if (sameName && nameMatch < 0) nameMatch = i;
            if (typographySignature(c) === stateSignature && signatureMatch < 0) signatureMatch = i;
        });
        // Names preserve the selected candidate when several recommendations share
        // one font stack. Signature matching is only a first-match legacy fallback.
        var selIdx = nameMatch >= 0 ? nameMatch : signatureMatch;
        if (selIdx >= 0) selectFont(selIdx);
        else if (STATE.typography && STATE.typography.name === "custom") {
            ["heading", "body"].forEach(function (role) {
                if (!STATE.typography[role]) STATE.typography[role] = {};
                if (!STATE.typography[role].css) updateRoleCss(role);
            });
            customCard.classList.add("selected");
            syncCustomInputs();
        } else {
            syncCustomInputs();
        }
    }

    function renderFormulaPolicy(host) {
        var sec = section("F", "formula_policy");
        enumField(sec, CAT.formula_policy, recOrFirst("formula_policy", CAT.formula_policy),
            function () { return STATE.formula_policy; }, function (v) { STATE.formula_policy = v; });
        host.appendChild(sec);
    }

    // Combined color + typography + icon preview — not a separate confirmation, just a
    // live "overall impression" of the style choices made above. Kept
    // deliberately abstract (a style chip, not a slide layout); page layout
    // preview is the live-preview server's job (Step 6).
    function renderStylePreview(host) {
        var wrap = el("div", "style-preview");
        var label = el("div", "style-preview-label");
        label.appendChild(el("span", "spl-title", t("style_preview_label")));
        // The "rough feel, not a slide layout" caveat sits in the label in the
        // UI font — never rendered in the candidate's body font, so it cannot
        // pose as sample content.
        label.appendChild(el("span", "spl-note", t("style_preview_body")));
        wrap.appendChild(label);
        var card = el("div", "style-preview-card");
        var textcol = el("div", "sp-textcol");
        var title = el("div", "sp-title");
        var titlePrimary = el("span", "sp-title-primary");
        var titleEnglish = el("span", "sp-title-english");
        title.appendChild(titlePrimary); title.appendChild(titleEnglish);
        var bodyRow = el("div", "sp-body");
        var accentBar = el("span", "sp-accent-bar");
        var bodyWrap = el("div", "sp-body-wrap");
        var bodyPrimary = el("span", "sp-body-primary");
        var bodyEnglish = el("span", "sp-body-english");
        setEnglishLanguageAttributes(titleEnglish);
        setEnglishLanguageAttributes(bodyEnglish);
        bodyWrap.appendChild(bodyPrimary); bodyWrap.appendChild(bodyEnglish);
        bodyRow.appendChild(accentBar); bodyRow.appendChild(bodyWrap);
        textcol.appendChild(title); textcol.appendChild(bodyRow);
        var content = el("div", "sp-content");
        var chip = el("div", "sp-chip");
        var chipDot = el("span", "sp-chip-dot");
        var chipLabel = el("span", "sp-chip-label");
        chip.appendChild(chipDot); chip.appendChild(chipLabel);
        card.appendChild(textcol); card.appendChild(content); card.appendChild(chip);
        wrap.appendChild(card);
        host.appendChild(wrap);
        // The strip is mounted inside the top bar on Stage 2, so it stays visible
        // while the center form scrolls.
        wrap.style.top = "0px";

        function paint() {
            var pal = (STATE.color && STATE.color.palette) || {};
            var typ = STATE.typography || {};
            var head = typ.heading || {}, body = typ.body || {};
            var bg = hexOr(pal.background, "#ffffff");
            var sbg = hexOr(pal.secondary_bg, bg);
            var pri = hexOr(pal.primary, "#1a3a6b");
            var acc = hexOr(pal.accent, pri);
            var sacc = hexOr(pal.secondary_accent, acc);
            var txt = hexOr(pal.body_text, "#1d2430");
            // body_size is px everywhere — preview it directly, no conversion.
            var rawSize = parseFloat(typ.body_size) || (isPptCanvas(STATE.canvas) ? 24 : 18);
            var bodyPx = Math.max(12, Math.min(34, rawSize));
            var headPrimaryStack = previewFontStack(head.primary, head.css);
            var headEnglishStack = previewFontStack(head.english, head.css);
            var bodyPrimaryStack = previewFontStack(body.primary, body.css);
            var bodyEnglishStack = previewFontStack(body.english, body.css);

            card.style.background = bg;
            titlePrimary.textContent = sampleText("heading", "primary");
            setUiLanguageAttributes(titlePrimary);
            titleEnglish.textContent = sampleText("heading", "english");
            title.style.color = pri;
            title.style.fontSize = Math.round(bodyPx * 1.7) + "px";
            titlePrimary.style.fontFamily = headPrimaryStack || "";
            titleEnglish.style.fontFamily = headEnglishStack || "";
            bodyPrimary.textContent = sampleText("body", "primary");
            setUiLanguageAttributes(bodyPrimary);
            bodyEnglish.textContent = sampleText("body", "english");
            bodyWrap.style.color = txt;
            bodyWrap.style.fontSize = bodyPx + "px";
            bodyPrimary.style.fontFamily = bodyPrimaryStack || "";
            bodyEnglish.style.fontFamily = bodyEnglishStack || "";
            titleEnglish.style.display = isEnglishProject() ? "none" : "";
            bodyEnglish.style.display = isEnglishProject() ? "none" : "";
            accentBar.style.background = acc;
            content.style.color = txt;
            content.style.fontFamily = bodyPrimaryStack || "";
            content.innerHTML = stylePreviewContentMarkup(STATE.icons);
            setUiLanguageAttributes(content);
            chip.style.background = sbg;
            chipDot.style.background = sacc;
            chipLabel.textContent = t("role_secondary_bg");
            chipLabel.style.color = txt;
            chipLabel.style.fontFamily = bodyPrimaryStack || "";
        }
        refreshStylePreview = paint;
        paint();
    }

    function renderImageStrategyPreview(host) {
        var wrap = el("div", "style-preview image-strategy-left-preview");
        var label = el("div", "style-preview-label");
        label.appendChild(el("span", "spl-title", t("image_strategy")));
        label.appendChild(el("span", "spl-note", t("image_strategy_reference_hint")));
        wrap.appendChild(label);
        var card = el("div", "style-preview-card image-strategy-preview-card");
        var visual = el("div", "image-strategy-preview-visual");
        var copy = el("div", "direction-preview-copy");
        var title = el("div", "direction-preview-title");
        var desc = el("div", "direction-preview-desc");
        copy.appendChild(title);
        copy.appendChild(desc);
        card.appendChild(visual);
        card.appendChild(copy);
        wrap.appendChild(card);
        host.appendChild(wrap);
        function paint() {
            var show = needsGeneratedImagesForUsage(STATE.image_usage);
            wrap.hidden = !show;
            if (!show) return;
            var strategy = STATE.image_strategy || {};
            visual.innerHTML = "";
            var row = appendImageStrategyPreviews(visual, strategy);
            visual.classList.toggle("image-strategy-preview-empty", !row);
            if (!row) visual.appendChild(el("div", "toggle-desc",
                strategy.rendering === "custom" ? t("image_strategy_no_reference") :
                    t("image_strategy_select_placeholder")));
            title.textContent = strategy.name ||
                (strategy.rendering === "custom" ? t("image_strategy_ai_custom") :
                    (strategy.rendering ? comparisonValueLabel("rendering", strategy.rendering) :
                        t("image_strategy_select_placeholder")));
            var parts = [];
            if (strategy.rendering) {
                parts.push(t("image_strategy_rendering") + ": " +
                    comparisonValueLabel("rendering", strategy.rendering));
            }
            if (strategy.visual) parts.push(t("image_strategy_visual") + ": " + strategy.visual);
            if (strategy.mood) parts.push(t("image_strategy_mood") + ": " + strategy.mood);
            if (strategy.behavior) parts.push(strategy.behavior);
            desc.textContent = parts.join(" · ") || t("image_strategy_reference_hint");
        }
        refreshImageStrategyPreview = paint;
        paint();
    }

    function findCatalogOption(list, id) {
        var flat = [];
        (list || []).forEach(function (item) {
            if (item && item.items) flat = flat.concat(item.items);
            else flat.push(item);
        });
        for (var i = 0; i < flat.length; i += 1) {
            if (flat[i] && flat[i].id === id) return flat[i];
        }
        return null;
    }

    function stylePreviewRows() {
        return [
            [t("preview_point_1_title"), t("preview_point_1_text")],
            [t("preview_point_2_title"), t("preview_point_2_text")],
            [t("preview_point_3_title"), t("preview_point_3_text")]
        ];
    }

    function stylePreviewContentMarkup(iconId) {
        var rows = stylePreviewRows();
        var icons = stylePreviewIconSamples(iconId, rows.length);
        return rows.map(function (row, idx) {
            return '<div class="sp-content-row">' +
                '<span class="sp-content-icon">' + icons[idx] + '</span>' +
                '<span class="sp-content-copy"><b>' + escapeHtml(row[0]) + '</b><small>' + escapeHtml(row[1]) + '</small></span>' +
                '</div>';
        }).join("");
    }

    function stylePreviewIconSamples(iconId, count) {
        if (iconId === "emoji") return ["📊", "💡", "✅"].slice(0, count).map(function (x) {
            return '<span class="sp-icon-emoji">' + x + '</span>';
        });
        if (iconId === "none") return new Array(count).fill('<span class="sp-icon-none-dot"></span>');
        var samples = ICON_PREVIEWS[iconId] || [];
        var out = [];
        for (var i = 0; i < count; i += 1) {
            var sample = samples[i % Math.max(samples.length, 1)];
            out.push(sample ? '<span class="sp-icon-mark" title="' + escapeHtml(sample.name || "") + '">' + (sample.svg || "") + '</span>' : '<span class="sp-icon-none-dot"></span>');
        }
        return out;
    }

    function renderImageDirection(host) {
        var sec = section(8, "sec_images");
        var usageChips = el("div", "chips");
        var usageNote = el("div", "subfield");
        usageNote.appendChild(el("div", "subfield-label", t("image_usage_notes")));
        var usageNoteInput = el("textarea", "text-input image-usage-notes-input");
        setNaturalInputDirection(usageNoteInput);
        usageNoteInput.placeholder = t("image_usage_notes_placeholder");
        usageNoteInput.value = STATE.image_notes || "";
        usageNoteInput.addEventListener("input", function () { STATE.image_notes = usageNoteInput.value; });
        usageNote.appendChild(usageNoteInput);

        var strategySub = el("div", "subfield image-strategy-subfield");
        strategySub.appendChild(el("div", "subfield-label", t("image_strategy")));
        strategySub.appendChild(el("div", "toggle-desc", t("image_strategy_reference_hint")));
        renderDirectionComponentCandidates(strategySub, "image_strategy");
        var recommendedStrategies = imageStrategyRecommendationCandidates();
        var strategyCands = imageStrategySelectableCandidates();
        var hasRecommendedStrategies = recommendedStrategies.length > 0;
        var customStrategy = STATE.image_strategy_custom || imageStrategyCustomCandidate();
        var presetPicker = el("div", "image-strategy-picker");
        var presetSelect = el("select", "font-select image-strategy-select");
        var customCard = null;
        var currentCustomEditor = null;
        var syncCustomStrategy = function () {};
        var selectCustomImageStrategy = function () {};

        function selectImageStrategy(idx) {
            if (!strategyCands[idx]) return;
            STATE.image_strategy = normalizedImageStrategy(strategyCands[idx]);
            ACTIVE_COMPONENT_DIRECTION_IDS.image_strategy = "";
            presetSelect.value = String(idx);
            if (customCard) customCard.classList.remove("selected");
            if (currentCustomEditor) currentCustomEditor.style.display = "none";
            syncCustomStrategy(false);
            refreshImageStrategyPreview();
            refreshDesignDirectionState();
            refreshDirectionComponentStates();
        }

        function imageStrategyCandidateIndex(strategy) {
            if (!strategy) return -1;
            var normalized = JSON.stringify(comparableImageStrategy(strategy));
            for (var i = 0; i < strategyCands.length; i += 1) {
                if (JSON.stringify(comparableImageStrategy(strategyCands[i])) === normalized) return i;
            }
            for (var fallback = 0; fallback < strategyCands.length; fallback += 1) {
                if (strategyCands[fallback] &&
                        strategyCands[fallback].rendering === strategy.rendering) return fallback;
            }
            return -1;
        }

        function strategyOptionLabel(candidate, idx) {
            var renderingLabel = comparisonValueLabel("rendering", candidate.rendering);
            var candidateName = localized(candidate, "name") || renderingLabel ||
                (t("option_prefix") + " " + (idx + 1));
            return candidateName !== renderingLabel ?
                candidateName + " · " + renderingLabel : candidateName;
        }

        function appendStrategyOptions(label, start, end) {
            if (start >= end) return;
            var group = document.createElement("optgroup");
            group.label = label;
            for (var idx = start; idx < end; idx += 1) {
                var option = document.createElement("option");
                option.value = String(idx);
                option.textContent = strategyOptionLabel(strategyCands[idx], idx);
                group.appendChild(option);
            }
            presetSelect.appendChild(group);
        }

        var placeholderOption = document.createElement("option");
        placeholderOption.value = "";
        placeholderOption.textContent = t("image_strategy_select_placeholder");
        placeholderOption.disabled = true;
        placeholderOption.selected = true;
        presetSelect.appendChild(placeholderOption);
        appendStrategyOptions(t("image_strategy_recommended_group"), 0, recommendedStrategies.length);
        appendStrategyOptions(t("image_strategy_all_group"), recommendedStrategies.length, strategyCands.length);
        presetSelect.disabled = !strategyCands.length;
        presetSelect.addEventListener("change", function () {
            selectImageStrategy(parseInt(presetSelect.value, 10));
        });
        presetPicker.appendChild(presetSelect);
        if (!strategyCands.length) {
            presetPicker.appendChild(el("div", "toggle-desc", t("image_strategy_empty")));
        }
        strategySub.appendChild(presetPicker);

        if (customStrategy) {
            customStrategy = normalizedImageStrategy(customStrategy);
            STATE.image_strategy_custom = customStrategy;
            customCard = el("div", "font-card image-strategy-custom-card ai-custom-candidate");
            var customTop = el("div", "font-card-head");
            customTop.appendChild(el("span", "font-card-name",
                customStrategy.name || t("image_strategy_ai_custom")));
            customTop.appendChild(el("span", "font-card-meta", t("image_strategy_ai_custom_desc")));
            customCard.appendChild(customTop);
            [
                ["image_strategy_visual", customStrategy.visual],
                ["image_strategy_mood", customStrategy.mood]
            ].forEach(function (row) {
                if (row[1]) customCard.appendChild(el("div", "color-note", t(row[0]) + "：" + row[1]));
            });
            var customCopy = el("div", "ai-custom-candidate-copy",
                customStrategy.behavior || t("image_strategy_custom_placeholder"));
            customCard.appendChild(customCopy);
            var customInput = el("textarea", "text-input image-strategy-custom-input");
            setNaturalInputDirection(customInput);
            customInput.rows = 4;
            customInput.placeholder = t("image_strategy_custom_placeholder");
            customInput.value = customStrategy.behavior;
            customInput.style.display = "none";
            customCard.appendChild(customInput);

            syncCustomStrategy = function (selected) {
                customCopy.textContent = customStrategy.behavior || t("image_strategy_custom_placeholder");
                customCopy.style.display = selected ? "none" : "block";
                customInput.style.display = selected ? "block" : "none";
                if (selected && customInput.value !== customStrategy.behavior) {
                    customInput.value = customStrategy.behavior || "";
                }
            };

            selectCustomImageStrategy = function () {
                STATE.image_strategy = normalizedImageStrategy(customStrategy);
                ACTIVE_COMPONENT_DIRECTION_IDS.image_strategy = "";
                presetSelect.value = "";
                customCard.classList.add("selected");
                syncCustomStrategy(true);
                refreshImageStrategyPreview();
                refreshDesignDirectionState();
                refreshDirectionComponentStates();
            };

            customInput.addEventListener("click", function (event) { event.stopPropagation(); });
            customInput.addEventListener("input", function () {
                customStrategy.behavior = customInput.value;
                STATE.image_strategy_custom = normalizedImageStrategy(customStrategy);
                selectCustomImageStrategy();
            });
            customCard.addEventListener("click", function () {
                selectCustomImageStrategy();
                customInput.focus();
            });
            syncCustomStrategy(false);
            strategySub.appendChild(customCard);
        }

        if (!customCard && !ACTIVE_COMPONENT_DIRECTION_IDS.image_strategy &&
                STATE.image_strategy &&
                STATE.image_strategy.rendering === "custom") {
            var customEditorField = el("div", "subfield image-strategy-current-custom");
            customEditorField.appendChild(el("div", "subfield-label", t("custom")));
            currentCustomEditor = el("textarea", "text-input image-strategy-custom-input");
            setNaturalInputDirection(currentCustomEditor);
            currentCustomEditor.rows = 4;
            currentCustomEditor.placeholder = t("image_strategy_custom_placeholder");
            currentCustomEditor.value = STATE.image_strategy.behavior || "";
            currentCustomEditor.addEventListener("input", function () {
                STATE.image_strategy.behavior = currentCustomEditor.value;
                refreshImageStrategyPreview();
                refreshDesignDirectionState();
                refreshDirectionComponentStates();
            });
            customEditorField.appendChild(currentCustomEditor);
            strategySub.appendChild(customEditorField);
        }

        var recommendedIds = selectedImageUsageIds(recValue("image_usage"));
        if (!recommendedIds.length) recommendedIds = [defaultImageUsageId()];
        var usageChipById = {};
        function refreshUsageChips() {
            Object.keys(usageChipById).forEach(function (id) {
                usageChipById[id].classList.toggle("selected", STATE.image_usage.indexOf(id) >= 0);
            });
            var noImages = STATE.image_usage.indexOf("none") >= 0;
            usageNote.style.display = noImages ? "none" : "block";
            strategySub.style.display = needsGeneratedImagesForUsage(STATE.image_usage) ? "block" : "none";
            refreshImageStrategyPreview();
        }
        function toggleImageUsage(id) {
            var current = STATE.image_usage.slice();
            if (id === "none") {
                current = current.indexOf("none") >= 0 ? [] : ["none"];
            } else {
                current = current.filter(function (item) { return item !== "none"; });
                if (current.indexOf(id) >= 0) {
                    current = current.filter(function (item) { return item !== id; });
                } else {
                    current.push(id);
                }
            }
            STATE.image_usage = current;
            refreshUsageChips();
            refreshImageProduction();
        }
        (CAT.image_usage || []).forEach(function (option) {
            var label = optionLabel(option);
            var desc = optionDesc(option);
            if (desc) label += (LANG === "zh" || LANG === "ja" ? "：" : " — ") + desc;
            var chip = el("div", "chip");
            chip.appendChild(el("span", "chip-text", label));
            if (recommendedIds.indexOf(option.id) >= 0) {
                chip.classList.add("recommended");
                chip.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
            chip.addEventListener("click", function () { toggleImageUsage(option.id); });
            usageChipById[option.id] = chip;
            usageChips.appendChild(chip);
        });
        sec.appendChild(usageChips);
        sec.appendChild(usageNote);
        sec.appendChild(strategySub);

        var currentStrategyIndex = imageStrategyCandidateIndex(STATE.image_strategy);
        if (STATE.image_strategy && STATE.image_strategy.rendering === "custom" && customCard) {
            selectCustomImageStrategy();
        } else if (STATE.image_strategy && STATE.image_strategy.rendering === "custom") {
            presetSelect.value = "";
        } else if (currentStrategyIndex >= 0) {
            presetSelect.value = String(currentStrategyIndex);
            if (customCard) customCard.classList.remove("selected");
            syncCustomStrategy(false);
        } else if ((!STATE.image_strategy || !STATE.image_strategy.rendering) &&
                needsGeneratedImagesForUsage(STATE.image_usage) &&
                hasRecommendedStrategies && strategyCands.length) {
            selectImageStrategy(imageStrategySelectedIndex());
        }
        refreshUsageChips();
        host.appendChild(sec);
    }

    function renderImageProduction(host) {
        var sec = section("P", "sec_image_production", t("image_production_hint"));
        var body = el("div", "image-production-body");
        sec.appendChild(body);
        refreshImageProduction = function () {
            body.innerHTML = "";
            var summary = el("div", "subfield");
            summary.appendChild(el("div", "subfield-label", t("image_source_summary")));
            var chips = el("div", "chips locked-summary-chips");
            (STATE.image_usage || []).forEach(function (id) {
                var option = findCatalogOption(CAT.image_usage, id);
                chips.appendChild(el("div", "chip selected locked-summary-chip",
                    option ? optionLabel(option) : humanizeId(id)));
            });
            summary.appendChild(chips);
            body.appendChild(summary);
            if (needsGeneratedImagesForUsage(STATE.image_usage)) {
                var pathField = el("div", "subfield");
                pathField.appendChild(el("div", "subfield-label", t("image_ai_path")));
                enumField(pathField, CAT.image_ai_path, recOrFirst("image_ai_path", CAT.image_ai_path),
                    function () { return STATE.image_ai_path; }, function (value) { STATE.image_ai_path = value; });
                body.appendChild(pathField);
            }
        };
        refreshImageProduction();
        host.appendChild(sec);
    }

    function renderMode(host) {
        var sec = section("M", "sec_mode");
        function refresh() {
            setSectionNote(sec, STATE.generation_mode === "split" ? t("mode_split_desc") : t("mode_continuous_desc"));
        }
        enumField(sec, CAT.generation_mode, recOrFirst("generation_mode", CAT.generation_mode),
            function () { return STATE.generation_mode; }, function (v) { STATE.generation_mode = v; refresh(); });
        refresh();
        host.appendChild(sec);
    }

    function renderProactiveExecution(host) {
        var sec = section("A", "sec_proactive_execution", t("proactive_execution_hint"));
        var opts = [{ id: "off", label: t("off_default") }, { id: "on", label: t("on") }];

        function addToggle(labelKey, descKey, stateKey, fallback) {
            var field = el("div", "subfield");
            field.appendChild(el("div", "subfield-label", t(labelKey)));
            field.appendChild(el("div", "toggle-desc", t(descKey)));
            var recommended = booleanRecommendation(stateKey, fallback);
            enumField(field, opts, recommended ? "on" : "off",
                function () { return STATE[stateKey] ? "on" : "off"; },
                function (value) {
                    STATE[stateKey] = value === "on";
                });
            sec.appendChild(field);
        }

        addToggle(
            "proactive_speaker_notes",
            "proactive_speaker_notes_desc",
            "proactive_speaker_notes",
            true
        );
        addToggle(
            "proactive_custom_animations",
            "proactive_custom_animations_desc",
            "proactive_custom_animations",
            false
        );
        addToggle(
            "proactive_narration_audio",
            "proactive_narration_audio_desc",
            "proactive_narration_audio",
            false
        );
        host.appendChild(sec);
    }

    function renderRefine(host) {
        var sec = section("R", "sec_refine");
        var opts = [{ id: "off", label: t("off_default") }, { id: "on", label: t("on") }];
        function refresh() {
            setSectionNote(sec, STATE.refine_spec ? t("refine_on_desc") : t("refine_off_desc"));
        }
        enumField(sec, opts, STATE.refine_spec ? "on" : "off",
            function () { return STATE.refine_spec ? "on" : "off"; },
            function (v) { STATE.refine_spec = (v === "on"); refresh(); });
        refresh();
        host.appendChild(sec);
    }

    // Two-stage confirmation: communication contract, then complete final plan.
    var STAGE = 1;

    function stageNumber(data) {
        var raw = data && data.stage;
        raw = String(raw == null ? "" : raw).toLowerCase();
        if (raw === "stage1") return 1;
        if (raw === "stage2") return 2;
        return 0;
    }

    function stageTitle(stage) {
        if (stage === 1) return t("stage_anchors");
        if (stage === 2) return t("stage_final_plan");
        return t("page_title");
    }

    function renderForStage(stage) {
        var host = document.getElementById("sections");
        host.innerHTML = "";
        _secCounter = 0;
        var heading = document.querySelector("#topbar .topbar-titles h1");
        if (heading) heading.textContent = stageTitle(stage);
        var hint = document.getElementById("topbar-hint");
        if (hint) hint.textContent = stage === 1 ? t("stage1_current_value_hint") : t("topbar_hint");
        // Detach the previous preview's repaint closures before the sections
        // re-render: color/typography auto-select would otherwise call them and
        // write to now-detached nodes until renderStylePreview remounts them.
        refreshStylePreview = function () {};
        refreshImageStrategyPreview = function () {};
        refreshImageProduction = function () {};
        refreshBodySizeHint = function () {};
        refreshSizeInputs = function () {};
        DIRECTION_COMPONENT_PAINTERS = [];
        var previewHost = document.getElementById("topbar-preview");
        if (previewHost) previewHost.innerHTML = "";
        if (stage === 1) {
            // Stage 1 closes the communication contract and its design basis in
            // one submission. Detailed template controls stay hidden until the
            // user explicitly chooses template-backed design.
            renderCommunication(host);
            renderDelivery(host);
            renderCanvas(host);
            renderTemplateSelection(host);
        } else if (stage === 2) {
            if (previewHost) renderStylePreview(previewHost);
            if (previewHost) renderImageStrategyPreview(previewHost);
            // Stage 2 confirms one coherent deck solution. Bundles provide a
            // coordinated starting point; individual controls remain editable.
            renderTemplateApplication(host);
            renderDesignDirections(host);
            renderNarrativeDirection(host);
            renderVisualDirection(host);
            renderReadingMode(host);
            renderPages(host);
            var styleGroup = el("div", "style-group");
            renderColor(styleGroup);
            renderIcons(styleGroup);
            renderTypography(styleGroup);
            host.appendChild(styleGroup);
            renderImageDirection(host);
            renderImageProduction(host);
            renderFormulaPolicy(host);
            renderProactiveExecution(host);
            renderMode(host);
            renderRefine(host);
            var refreshDirectionIndicators = function () {
                window.setTimeout(function () {
                    refreshDesignDirectionState();
                    refreshDirectionComponentStates();
                }, 0);
            };
            host.oninput = refreshDirectionIndicators;
            host.onchange = refreshDirectionIndicators;
            host.onclick = refreshDirectionIndicators;
        }
        updateActionBar(stage);
    }

    function renderAll() { renderForStage(STAGE); }

    function updateActionBar(stage) {
        var btn = document.getElementById("btn-confirm");
        btn.disabled = false;
        if (stage === 1) btn.textContent = t("btn_confirm_contract");
        else if (stage === 2) btn.textContent = t("btn_confirm_final_plan");
        else btn.textContent = t("btn_confirm");
    }

    // ---- state init (once) ----------------------------------------------
    function firstId(list) {
        if (!list || !list.length) return undefined;
        if (list[0].items) return (list[0].items[0] || {}).id;
        return list[0].id;
    }
    function pick(field, catList) {
        var recommended = recId(field);
        if (recommended == null || recommended === "") {
            recommended = normalizeRecId(field, directionField(field));
        }
        return recommended != null && recommended !== "" ? recommended : firstId(catList);
    }

    function initCreativeSelection(field, catalog, behaviorKey) {
        var value = pick(field, catalog);
        var behavior = customCandidateBehavior(field);
        if (value && value !== "custom" && !findCatalogOption(catalog, value)) {
            behavior = String(value);
            value = "custom";
        }
        STATE[field] = value;
        STATE[behaviorKey] = behavior;
    }

    function initStage1State() {
        STATE.primary_language = recommendationLanguage();
        STATE.canvas = pick("canvas", CAT.canvas);
        STATE.audience = (REC.audience && REC.audience.value) || "";
        STATE.communication_intent = (REC.communication_intent && REC.communication_intent.value) || "";
        STATE.audience_outcome = (REC.audience_outcome && REC.audience_outcome.value) || "";
        STATE.core_message = (REC.core_message && REC.core_message.value) || "";
        STATE.delivery_context = (REC.delivery_context && REC.delivery_context.value) || "";
        STATE.artifact_afterlife = (REC.artifact_afterlife && REC.artifact_afterlife.value) || "";
        STATE.content_divergence = (REC.content_divergence && REC.content_divergence.value) || "";  // free text; blank = balanced default
    }

    // Stage-2 fields are (re-)read from the recommendations. At boot they come from
    // the active stage file; after a stage-1 confirm enterStage() calls this again
    // with the newly authored candidates. Stage-1 STATE is preserved
    // across the single-session transition — this never resets the contract.
    function initStage2State() {
        [
            "audience",
            "communication_intent",
            "audience_outcome",
            "core_message",
            "delivery_context",
            "artifact_afterlife",
            "content_divergence"
        ].forEach(function (field) {
            var value = recValue(field);
            if (value && typeof value === "object") value = value.value;
            if (value != null) STATE[field] = String(value);
        });
        STATE.primary_language = recommendationLanguage();
        resetTypographySizeOverrides();
        var templateApplication = templateApplicationRecommendation();
        if (templateApplication != null) {
            STATE.template_application = templateApplication;
        } else if (stageNumber(REC) === 2) {
            delete STATE.template_application;
        }
        // Reading mode is a design-density tool, not part of the communication
        // purpose. Keep the legacy delivery_purpose key for JSON compatibility.
        STATE.delivery_purpose = recId("delivery_purpose") ||
            directionField("delivery_purpose") || STATE.delivery_purpose || "balanced";
        STATE.page_count = (REC.page_count && REC.page_count.value != null) ? String(REC.page_count.value) : (STATE.page_count || "");
        initCreativeSelection("mode", CAT.modes, "mode_behavior");
        initCreativeSelection("visual_style", CAT.visual_styles, "visual_style_behavior");
        var cc = colorRecommendationCandidates();
        var csel = (REC.color && REC.color.selected != null) ? REC.color.selected :
            (designDirectionSpec().selected || 0);
        var c0 = cc[Math.min(csel, Math.max(cc.length - 1, 0))] || {};
        STATE.color = {
            name: localized(c0, "name") || c0.name || "",
            palette: Object.assign({}, normPalette(c0))
        };

        STATE.icons = pick("icons", CAT.icons);

        var tc = typographyRecommendationCandidates();
        var tsel = (REC.typography && REC.typography.selected != null) ? REC.typography.selected :
            (designDirectionSpec().selected || 0);
        var t0 = normTypography(tc[Math.min(tsel, Math.max(tc.length - 1, 0))] || {});
        STATE.typography = {
            name: localized(t0, "name") || t0.name || "",
            heading: t0.heading || {},
            body: t0.body || {},
            body_size: t0.body_size || typographyBodySize(REC.typography),
            sizes: Object.assign({}, t0.sizes || {})
        };
        if (t0.custom) STATE.typography.custom = t0.custom;

        // Guarantee a body baseline even when a candidate omitted body_size, on
        // any canvas (PPT → px default by purpose, non-PPT → px from canvas height),
        // so role sizes never derive from an empty anchor.
        if (STATE.typography && !STATE.typography.body_size) {
            STATE.typography.body_size = defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose);
        }
        // A freshly authored Stage 2 starts from one deterministic reading-mode
        // baseline.
        if (stageNumber(REC) === 2) syncUnpinnedTypographySizes(true);
        var rawImageUsage = recValue("image_usage");
        STATE.image_usage = selectedImageUsageIds(rawImageUsage);
        if (!STATE.image_usage.length) {
            STATE.image_usage = [defaultImageUsageId()];
        }
        STATE.image_notes = imageUsageNotesRecommendation(rawImageUsage);
        STATE.image_strategy_custom = imageStrategyCustomCandidate();
        var strategyCandidates = imageStrategyRecommendationCandidates();
        var directionStrategy = directionField("image_strategy");
        var customStrategyRecommended = recId("image_strategy") === "custom";
        if (customStrategyRecommended && STATE.image_strategy_custom) {
            STATE.image_strategy = normalizedImageStrategy(STATE.image_strategy_custom);
        } else if (directionStrategy) {
            STATE.image_strategy = normalizedImageStrategy(directionStrategy);
        } else if (strategyCandidates.length) {
            STATE.image_strategy = normalizedImageStrategy(
                strategyCandidates[imageStrategySelectedIndex()] || strategyCandidates[0]
            );
        }
        var directions = designDirectionCandidates();
        if (directions.length) {
            var selected = Number(designDirectionSpec().selected || 0);
            if (!isFinite(selected) || selected < 0) selected = 0;
            selected = Math.min(selected, directions.length - 1);
            applyDesignDirection(directions[selected], selected, false);
        }
    }

    function initProductionState() {
        STATE.formula_policy = pick("formula_policy", CAT.formula_policy);
        STATE.image_ai_path = pick("image_ai_path", CAT.image_ai_path);
        STATE.proactive_speaker_notes = booleanRecommendation("proactive_speaker_notes", true);
        STATE.proactive_custom_animations = booleanRecommendation("proactive_custom_animations", false);
        STATE.proactive_narration_audio = booleanRecommendation("proactive_narration_audio", false);

        STATE.generation_mode = pick("generation_mode", CAT.generation_mode);
        STATE.refine_spec = !!((REC.refine_spec && REC.refine_spec.value) || (REC.recommend && REC.recommend.refine_spec));
    }

    function initState() {
        initStage1State();
    }

    // ---- confirm + close -------------------------------------------------
    function showConfirmedOverlay() {
        var ov = document.getElementById("confirmed-overlay");
        ov.querySelector(".cf-title").textContent = t("confirmed_title");
        ov.querySelector(".cf-hint").textContent = t("confirmed_hint");
        ov.style.display = "flex";
    }

    // ---- staged submit + next-stage transitions -------------------------
    function communicationPayload() {
        var payload = {
            canvas: STATE.canvas,
            audience: STATE.audience,
            communication_intent: STATE.communication_intent,
            audience_outcome: STATE.audience_outcome,
            core_message: STATE.core_message,
            delivery_context: STATE.delivery_context,
            artifact_afterlife: STATE.artifact_afterlife,
            content_divergence: STATE.content_divergence
        };
        if (STATE.primary_language && STATE.primary_language !== "und") {
            payload.primary_language = STATE.primary_language;
        }
        return payload;
    }

    function stage1Payload() {
        var payload = communicationPayload();
        payload.stage = "stage1";
        payload.template_selection = {
            mode: TEMPLATE_MODE,
            selection_keys: TEMPLATE_MODE === "templates"
                ? TEMPLATE_SELECTED_KEYS.slice() : []
        };
        return payload;
    }

    function normalizeCreativePayload(payload) {
        if (payload.mode !== "custom") delete payload.mode_behavior;
        if (payload.visual_style !== "custom") delete payload.visual_style_behavior;
        var imageStrategy = payload.image_strategy;
        if (imageStrategy && imageStrategy.rendering === "custom") {
            if (!imageStrategy.behavior && imageStrategy.custom) {
                imageStrategy.behavior = imageStrategy.custom;
            }
            delete imageStrategy.custom;
        } else if (imageStrategy) {
            delete imageStrategy.behavior;
            delete imageStrategy.custom;
        }
        delete payload.image_strategy_custom;
        return payload;
    }

    function customSelectionsValid(payload) {
        var imageStrategy = payload.image_strategy || {};
        var valid = payload.mode !== "custom" || String(payload.mode_behavior || "").trim();
        valid = valid && (payload.visual_style !== "custom" ||
            String(payload.visual_style_behavior || "").trim());
        valid = valid && (imageStrategy.rendering !== "custom" ||
            String(imageStrategy.behavior || "").trim());
        if (!valid) {
            document.getElementById("confirm-status").textContent = t("custom_behavior_required");
        }
        return !!valid;
    }

    function imageStrategyValid(payload) {
        if (!needsGeneratedImagesForUsage(payload.image_usage)) return true;
        var imageStrategy = payload.image_strategy || {};
        var rendering = String(imageStrategy.rendering || "").trim();
        if (!rendering) {
            document.getElementById("confirm-status").textContent = t("image_strategy_required");
            return false;
        }
        var presetIds = imageStrategyCatalogCandidates().map(function (candidate) {
            return candidate.rendering;
        });
        if (rendering !== "custom" && presetIds.length && presetIds.indexOf(rendering) < 0) {
            document.getElementById("confirm-status").textContent = t("image_strategy_invalid");
            return false;
        }
        return true;
    }

    function positiveNumber(value) {
        var number = parseFloat(value);
        return isFinite(number) && number > 0;
    }

    function designSystemValid(payload) {
        var color = payload.color || {};
        var palette = color.palette || {};
        var completePalette = PALETTE_ROLES.every(function (role) {
            return !!normHex(palette[role]);
        });
        var customPalette = color.name === "custom" && String(color.custom || "").trim();

        var typography = payload.typography || {};
        var completeFamilies = typographyFamiliesComplete(typography);
        var sizes = typography.sizes || {};
        var completeSizes = positiveNumber(typography.body_size) &&
            ["title", "subtitle", "annotation"].every(function (role) {
                return positiveNumber(sizes[role]);
            });
        var valid = (completePalette || customPalette) &&
            completeFamilies && completeSizes;
        if (!valid) {
            var message = color.name === "custom" && !customPalette
                ? t("custom_color_required")
                : t("design_system_required");
            document.getElementById("confirm-status").textContent = message;
        }
        return !!valid;
    }

    function submitStage(payload, nextStage) {
        var btn = document.getElementById("btn-confirm");
        btn.disabled = true;
        fetch("/api/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(function (r) {
            if (!r.ok) throw new Error("stage submit failed");
            showDeriving();
            pollForStage(nextStage);
        }).catch(function () {
            btn.disabled = false;
            document.getElementById("confirm-status").textContent = t("error_retry");
        });
    }

    function imageUsageValid(value) {
        var ids = selectedImageUsageIds(value);
        if (!ids.length) {
            document.getElementById("confirm-status").textContent = t("image_usage_required");
            return false;
        }
        if (ids.indexOf("none") >= 0 && ids.length > 1) {
            document.getElementById("confirm-status").textContent = t("image_usage_none_exclusive");
            return false;
        }
        return true;
    }

    function templateSelectionValid() {
        var valid = TEMPLATE_MODE === "free_design" ||
            (TEMPLATE_MODE === "templates" && TEMPLATE_SELECTED_KEYS.length > 0);
        if (!valid) {
            document.getElementById("confirm-status").textContent =
                t("template_selection_required");
        }
        return valid;
    }

    function submitStage1() {
        if (!templateSelectionValid()) return;
        submitStage(stage1Payload(), 2);
    }

    function submitStage2() {
        confirm();
    }

    function showDeriving() {
        document.getElementById("sections").style.display = "none";
        document.getElementById("actionbar").style.display = "none";
        var l = document.getElementById("loading");
        l.textContent = t("deriving");
        l.style.display = "block";
    }

    // Poll session state first. It is derived from recommendation stage files
    // and result.json, so a recovered server can tell the existing page exactly when
    // the next stage is ready.
    function pollForStage(nextStage) {
        fetchJson("/api/session", "session")
            .then(function (session) {
                var readyStage = Number(session && session.recommendation_stage_number || 0);
                if (readyStage < nextStage) {
                    setTimeout(function () { pollForStage(nextStage); }, 1200);
                    return null;
                }
                return fetchJson("/api/recommendations", "recommendations").then(function (data) {
                    var serverStage = stageNumber(data);
                    if (data && typeof serverStage === "number" && serverStage >= nextStage) {
                        enterStage(data, serverStage);
                    }
                    else { setTimeout(function () { pollForStage(nextStage); }, 1200); }
                    return null;
                });
            }).catch(function (err) {
                var l = document.getElementById("loading");
                if (l) l.textContent = t("connection_lost") + " " + (err && err.message ? err.message : "");
                setTimeout(function () { pollForStage(nextStage); }, 1500);
            });
    }

    function enterStage(data, stage) {
        REC = data;
        if (stage === 2) {
            initStage2State();
            initProductionState();
        }
        STAGE = stage;
        document.getElementById("loading").style.display = "none";
        document.getElementById("sections").style.display = "block";
        document.getElementById("actionbar").style.display = "flex";
        document.getElementById("confirm-status").textContent = "";
        renderForStage(stage);
    }

    function confirm() {
        var btn = document.getElementById("btn-confirm");
        var payload = JSON.parse(JSON.stringify(STATE));
        normalizeTypographyForSubmit(payload);
        payload.stage = "final";
        payload.image_usage = selectedImageUsageIds(payload.image_usage);
        if (!imageUsageValid(payload.image_usage)) return;
        if (!String(payload.image_notes || "").trim()) delete payload.image_notes;
        if (!needsGeneratedImagesForUsage(payload.image_usage)) {
            delete payload.image_ai_path;
            delete payload.image_strategy;
        } else {
            payload.image_strategy = normalizedImageStrategy(payload.image_strategy);
        }
        normalizeCreativePayload(payload);
        if (!imageStrategyValid(payload)) return;
        if (!designSystemValid(payload)) return;
        if (!customSelectionsValid(payload)) return;
        btn.disabled = true;
        fetch("/api/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(function (r) {
            if (!r.ok) throw new Error("confirm failed");
            showConfirmedOverlay();
            fetch("/api/shutdown", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reason: "confirmed" })
            }).catch(function () { /* server already gone — fine */ });
            setTimeout(function () { try { window.close(); } catch (e) { /* ignore */ } }, 400);
        }).catch(function () {
            btn.disabled = false;
            document.getElementById("confirm-status").textContent = t("error_retry");
        });
    }

    // ---- boot ------------------------------------------------------------
    function showError(msg) {
        document.getElementById("loading").style.display = "none";
        var e = document.getElementById("error");
        e.style.display = "block";
        e.textContent = msg;
    }

    function fetchJson(url, label) {
        return fetch(url, { cache: "no-store" }).then(function (r) {
            return r.text().then(function (text) {
                var data = null;
                if (text) {
                    try { data = JSON.parse(text); }
                    catch (e) {
                        if (r.ok) throw new Error((label || url) + ": invalid JSON");
                    }
                }
                if (!r.ok) {
                    var serverMsg = data && data.error ? data.error : (text || r.statusText || r.status);
                    throw new Error((label || url) + ": " + serverMsg);
                }
                return data || {};
            });
        });
    }

    function loadCatalogs() {
        return fetchJson("/api/catalogs", "catalogs")
            .catch(function () { return fetchJson("/static/catalogs.json", "static catalogs"); });
    }

    function loadIconPreviews() {
        return fetchJson("/api/icon-previews", "icon previews")
            .catch(function () { return {}; });
    }

    function loadAiImageComparison() {
        return fetchJson("/api/ai-image-comparison", "AI image comparison")
            .catch(function () { return {}; });
    }

    function applyServerLanguage(data) {
        var requested = data && data.lang;
        if (requested !== "zh" && requested !== "en" && requested !== "ja") return;
        var hasStored = false;
        try { hasStored = !!window.localStorage.getItem("ppt_lang"); } catch (e) { /* ignore */ }
        if (hasStored) return;
        LANG = requested;
        applyStaticTranslations();
        var toggleBtn = document.getElementById("btn-lang-toggle");
        if (toggleBtn) refreshLangToggle(toggleBtn);
    }

    function loadStrategistUi(forceStage) {
        return Promise.all([
            loadCatalogs(),
            fetchJson("/api/recommendations", "recommendations"),
            loadIconPreviews(),
            loadAiImageComparison()
        ]).then(function (res) {
            CAT = res[0];
            REC = res[1];
            ICON_PREVIEWS = res[2] || {};
            AI_IMAGE_COMPARISON = res[3] || {};
            applyServerLanguage(REC);
            var activeStage = forceStage || stageNumber(REC);
            if (activeStage === 1) {
                if (!REC.template_options || typeof REC.template_options !== "object" ||
                        Array.isArray(REC.template_options)) {
                    throw new Error("Stage 1 recommendations must include template_options");
                }
                initTemplateOptions(REC.template_options);
            }
            initState();
            enterStage(REC, activeStage);
            return REC;
        });
    }

    function boot() {
        applyStaticTranslations();
        var toggleBtn = document.getElementById("btn-lang-toggle");
        var langMenu = document.getElementById("lang-menu");
        refreshLangToggle(toggleBtn);
        var setMenuOpen = function (open) {
            langMenu.hidden = !open;
            toggleBtn.setAttribute("aria-expanded", open ? "true" : "false");
            if (open) {
                var sel = langMenu.querySelector("li.selected") || langMenu.querySelector("li[data-lang]");
                if (sel) sel.focus();
            }
        };
        var chooseLang = function (v) {
            setMenuOpen(false);
            toggleBtn.focus();
            if (v !== "ja" && v !== "en" && v !== "zh") return;
            if (v === LANG) return;
            LANG = v;
            try { window.localStorage.setItem("ppt_lang", LANG); } catch (e2) { /* ignore */ }
            applyStaticTranslations();
            refreshLangToggle(toggleBtn);
            if (REC && CAT) {
                renderAll();   // STATE persists → selections preserved
            }
        };
        toggleBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            setMenuOpen(langMenu.hidden);
        });
        toggleBtn.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !langMenu.hidden) {
                e.stopPropagation();
                setMenuOpen(false);
            } else if ((e.key === "ArrowDown" || e.key === "ArrowUp") && langMenu.hidden) {
                e.preventDefault();
                e.stopPropagation();
                setMenuOpen(true);
            }
        });
        langMenu.addEventListener("click", function (e) {
            e.stopPropagation();
            var li = e.target && e.target.closest ? e.target.closest("li[data-lang]") : null;
            if (li) chooseLang(li.getAttribute("data-lang"));
            else setMenuOpen(false);
        });
        langMenu.addEventListener("keydown", function (e) {
            e.stopPropagation();   // page-level shortcuts must not fire while the menu is open
            var items = Array.prototype.slice.call(langMenu.querySelectorAll("li[data-lang]"));
            var idx = items.indexOf(document.activeElement);
            if (e.key === "Escape") {
                setMenuOpen(false);
                toggleBtn.focus();
            } else if (e.key === "ArrowDown") {
                e.preventDefault();
                (items[idx + 1] || items[0]).focus();
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                (items[idx - 1] || items[items.length - 1]).focus();
            } else if (e.key === "Home") {
                e.preventDefault();
                items[0].focus();
            } else if (e.key === "End") {
                e.preventDefault();
                items[items.length - 1].focus();
            } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
                e.preventDefault();
            } else if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                if (idx >= 0) chooseLang(items[idx].getAttribute("data-lang"));
            }
        });
        toggleBtn.parentElement.addEventListener("focusout", function (e) {
            if (!langMenu.hidden && !toggleBtn.parentElement.contains(e.relatedTarget)) setMenuOpen(false);
        });
        document.addEventListener("click", function () {
            if (!langMenu.hidden) setMenuOpen(false);
        });
        document.getElementById("btn-confirm").addEventListener("click", function () {
            if (STAGE === 1) submitStage1();
            else if (STAGE === 2) submitStage2();
            else confirm();
        });

        // Session remains the first network read so completed runs can close
        // cleanly. Active runs always load the current Strategist stage; Stage 1
        // carries its template catalog inside the recommendation payload.
        fetchJson("/api/session", "session").catch(function () {
            return { phase: "strategist" };
        }).then(function (session) {
            if (session && session.status === "done") {
                document.getElementById("loading").style.display = "none";
                showConfirmedOverlay();
                return null;
            }
            return loadStrategistUi().catch(function (err) {
                showError(t("load_error") + " " + (err && err.message ? err.message : ""));
                return null;
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
