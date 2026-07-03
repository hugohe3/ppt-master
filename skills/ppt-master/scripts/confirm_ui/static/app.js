/* PPT Master - Strategist confirmation stage UI
 * Finite/enumerable fields (canvas, mode, visual style, icons, image usage,
 * AI source, formula policy, generation mode) list ALL options from
 * /static/catalogs.json with the AI's recommendation marked. Open/generative
 * fields (color, typography, generated-image style) show >=3 AI candidates. Open fields also expose
 * Custom controls. On confirm the page saves result.json and closes.
 */
(function () {
    "use strict";

    // ---- i18n ------------------------------------------------------------
    var MESSAGES = {
        en: {
            page_title: "PPT Master - Confirm Design",
            topbar_hint: "Pick or type your choices, then click Confirm — the page closes and you return to the chat.",
            stage_anchors: "Stage 1 · Direction",
            stage_design: "Stage 2 · Design system",
            stage_images: "Stage 3 · Images & execution",
            loading: "Loading…",
            load_error: "Could not load recommendations.json. The AI must write it before launch.",
            btn_confirm: "Confirm",
            btn_next: "Next →",
            deriving: "Generating the downstream options from your choices…",
            already_confirmed: "Already confirmed once. Re-submitting overwrites the previous choices.",
            confirmed_title: "✓ Confirmed",
            confirmed_hint: "Your choices are saved. You can close this page and return to the chat.",
            lang_toggle_title: "Switch language",
            sec_canvas: "Canvas format",
            sec_pages: "Page count",
            sec_audience: "Target audience",
            sec_style: "Style objective",
            sec_color: "Color scheme",
            sec_icons: "Icon usage",
            sec_type: "Typography",
            sec_images: "Image usage",
            sec_mode: "Generation mode",
            sec_refine: "Refine spec first",
            sub_mode: "Narrative mode",
            sub_visual: "Visual style",
            sub_divergence: "Material divergence (how freely to reshape vs. stay close to the source)",
            placeholder_divergence: "In your words — e.g. \"stick closely to the document\" / \"freely restructure and expand within the source\". Leave blank for a balanced default.",
            custom: "Custom",
            custom_placeholder: "Type your own…",
            recommended: "Recommended",
            placeholder_audience: "Who is this deck for?",
            placeholder_pages: "e.g. 12-15",
            hex_override: "Custom HEX override:",
            formula_policy: "Formula rendering policy",
            image_ai_path: "AI image source",
            image_strategy: "Generated image style",
            image_strategy_empty: "No generated-image style candidates were provided.",
            image_strategy_rendering: "Rendering",
            image_strategy_palette: "Palette",
            image_strategy_visual: "Visual",
            image_strategy_color: "Color",
            image_strategy_mood: "Mood",
            image_strategy_manual: "Custom",
            image_strategy_manual_desc: "Choose a rendering and palette manually, or use custom prose.",
            image_strategy_reference_hint: "Reference images show rendering / color-behavior only. Final AI images use the color scheme selected above.",
            image_strategy_color_follow: "Uses the color scheme selected above; the palette only controls color behavior.",
            image_strategy_no_reference: "No reference image for this custom choice.",
            image_usage_notes: "Additional image requirements",
            image_usage_notes_placeholder: "e.g. realistic handwashing scenes; avoid cartoon germs; keep product photos untouched.",
            image_usage_required: "Select at least one image usage option.",
            image_usage_none_exclusive: "No images cannot be combined with other image options.",
            font_heading: "Heading",
            font_body: "Body",
            font_body_size: "Body baseline size",
            font_body_size_hint: "All type sizes derive from this body baseline.",
            body_size_hint_canvas: "This canvas suggests ~{lo}–{hi}px (scales with canvas height).",
            body_size_hint_purpose: "This delivery purpose recommends {def}px — one fixed size, not a range.",
            body_size_hint_oor: "(Current value is outside the usual range for this canvas — check the unit is right and that it fits.)",
            delivery_purpose: "Delivery purpose",
            delivery_purpose_hint: "Read-close decks can run smaller; projected decks need larger type.",
            size_override: "Per-role size override:",
            size_role_title: "title",
            size_role_subtitle: "subtitle",
            size_role_annotation: "annotation",
            custom_typography: "Custom typography",
            custom_typography_placeholder: "Type your font plan, e.g. Heading: Georgia + KaiTi; Body: Microsoft YaHei + Arial…",
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
            refine_off_desc: "Spec is written in one go; the pipeline auto-proceeds.",
            refine_on_desc: "Stop after the spec for review/revision before any generation.",
            off_default: "Off",
            on: "On",
            option_prefix: "Option",
            error_retry: "Error - retry"
        },
        ja: {
            page_title: "PPT Master - デザイン確認",
            topbar_hint: "各項目を選択または入力して「確定」を押してください。ページが閉じたらチャットに戻ります。",
            stage_anchors: "ステージ 1 · 方向性",
            stage_design: "ステージ 2 · デザインシステム",
            stage_images: "ステージ 3 · 画像と実行方法",
            loading: "読み込み中…",
            load_error: "recommendations.json を読み込めませんでした。起動前にAIが書き込む必要があります。",
            btn_confirm: "確定",
            btn_next: "次へ →",
            deriving: "選択内容をもとに後続の選択肢を生成しています…",
            already_confirmed: "すでに一度確定済みです。再送信すると前回の選択を上書きします。",
            confirmed_title: "✓ 確定しました",
            confirmed_hint: "選択内容を保存しました。このページを閉じてチャットに戻ってください。",
            lang_toggle_title: "言語を切り替え",
            sec_canvas: "キャンバス形式",
            sec_pages: "ページ数",
            sec_audience: "想定読者",
            sec_style: "スタイルの狙い",
            sec_color: "配色",
            sec_icons: "アイコンの使用",
            sec_type: "タイポグラフィ",
            sec_images: "画像の使用",
            sec_mode: "生成モード",
            sec_refine: "先に設計仕様を精査",
            sub_mode: "ナラティブモード",
            sub_visual: "ビジュアルスタイル",
            sub_divergence: "素材からの発散度（どこまで自由に再構成するか、原文に忠実か）",
            placeholder_divergence: "自分の言葉でどうぞ — 例：「文書に忠実に」「元素材の範囲内で自由に再構成・展開」。空欄ならバランス型になります。",
            custom: "カスタム",
            custom_placeholder: "自由に入力…",
            recommended: "おすすめ",
            placeholder_audience: "この資料は誰に向けたもの？",
            placeholder_pages: "例：12-15",
            hex_override: "カスタムHEXで上書き：",
            formula_policy: "数式レンダリング方針",
            image_ai_path: "AI画像の生成元",
            image_strategy: "生成画像のスタイル",
            image_strategy_empty: "生成画像スタイルの候補がまだありません。",
            image_strategy_rendering: "レンダリング",
            image_strategy_palette: "パレット",
            image_strategy_visual: "ビジュアル",
            image_strategy_color: "カラー",
            image_strategy_mood: "ムード",
            image_strategy_manual: "カスタム",
            image_strategy_manual_desc: "レンダリングとパレットを手動で選ぶか、カスタム記述を使います。",
            image_strategy_reference_hint: "参照画像はレンダリング／色の使い方だけを示します。最終AI画像の色は上で選んだ配色に従います。",
            image_strategy_color_follow: "上で選んだ配色を使用します。パレットは色の使い方だけを制御します。",
            image_strategy_no_reference: "このカスタム選択には参照画像がありません。",
            image_usage_notes: "画像に関する補足要件",
            image_usage_notes_placeholder: "例：リアルな手洗いシーンを優先、漫画調の菌のイラストは避ける、製品写真はそのまま使う。",
            image_usage_required: "画像の使用方法を少なくとも1つ選択してください。",
            image_usage_none_exclusive: "「画像なし」は他の画像オプションと同時に選択できません。",
            font_heading: "見出し",
            font_body: "本文",
            font_body_size: "本文の基準サイズ",
            font_body_size_hint: "すべての文字サイズはこの本文基準から導出されます。",
            body_size_hint_canvas: "このキャンバスの目安は約{lo}–{hi}px（キャンバスの高さに応じて変化）。",
            body_size_hint_purpose: "この利用シーンの推奨は{def}px — 範囲ではなく固定値です。",
            body_size_hint_oor: "（現在の値はこのキャンバスの通常範囲外です — 単位とサイズ感を確認してください。）",
            delivery_purpose: "利用シーン",
            delivery_purpose_hint: "手元で読む資料は小さめでOK、投影する資料は大きめの文字が必要です。",
            size_override: "役割ごとのサイズ上書き：",
            size_role_title: "タイトル",
            size_role_subtitle: "サブタイトル",
            size_role_annotation: "注釈",
            custom_typography: "カスタムタイポグラフィ",
            custom_typography_placeholder: "フォント案を入力 — 例：見出し：Georgia + 游明朝 / 本文：游ゴシック + Arial…",
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
            refine_off_desc: "設計仕様を一度で書き上げ、パイプラインは自動で進みます。",
            refine_on_desc: "設計仕様の作成後に停止し、生成前にレビュー・修正できます。",
            off_default: "オフ",
            on: "オン",
            option_prefix: "案",
            error_retry: "エラー - 再試行"
        },
        zh: {
            page_title: "确认设计方案",
            topbar_hint: "选择或自定义各项后点「确认」；页面会关闭，请回到聊天窗口。",
            stage_anchors: "第一阶段 · 方向确认",
            stage_design: "第二阶段 · 设计系统",
            stage_images: "第三阶段 · 图片与执行方式",
            loading: "加载中…",
            load_error: "无法加载推荐文件，需在启动前写入。",
            btn_confirm: "确认",
            btn_next: "下一步 →",
            deriving: "正在根据你的选择生成下游选项…",
            already_confirmed: "已确认过一次，重新提交会覆盖之前的选择。",
            confirmed_title: "✓ 已确认",
            confirmed_hint: "选择已保存，可关闭此页并回到聊天窗口。",
            lang_toggle_title: "切换语言",
            sec_canvas: "画布格式",
            sec_pages: "页数",
            sec_audience: "目标受众",
            sec_style: "风格目标",
            sec_color: "色彩方案",
            sec_icons: "图标使用",
            sec_type: "字体方案",
            sec_images: "图片使用",
            sec_mode: "生成模式",
            sec_refine: "先精修设计规范",
            sub_mode: "叙事模式",
            sub_visual: "视觉风格",
            sub_divergence: "材料发散度（多大程度重塑，还是贴近源材料）",
            placeholder_divergence: "用你自己的话写，例如「严格贴着文档来」/「在源材料范围内自由重组并展开」。留空则按平衡处理。",
            custom: "自定义",
            custom_placeholder: "输入自定义内容…",
            recommended: "推荐",
            placeholder_audience: "这份演示文稿面向谁？",
            placeholder_pages: "如：12-15",
            hex_override: "自定义色值覆盖：",
            formula_policy: "公式渲染策略",
            image_ai_path: "生成配图来源",
            image_strategy: "生成图风格",
            image_strategy_empty: "还没有提供生成图风格候选。",
            image_strategy_rendering: "渲染风格",
            image_strategy_palette: "图像调色",
            image_strategy_visual: "视觉",
            image_strategy_color: "色彩",
            image_strategy_mood: "情绪",
            image_strategy_manual: "自定义",
            image_strategy_manual_desc: "手动选择渲染风格和图像调色，也可以使用自定义描述。",
            image_strategy_reference_hint: "参考图只展示渲染风格 / 用色行为；最终 AI 图片颜色跟随上方色彩方案。",
            image_strategy_color_follow: "使用上方已选色彩方案；图像调色只控制用色比例和行为。",
            image_strategy_no_reference: "自定义选择没有参考图。",
            image_usage_notes: "图片补充要求",
            image_usage_notes_placeholder: "例如：优先真实洗手场景；不要卡通病菌；产品照片保持原样。",
            image_usage_required: "请至少选择一种图片使用方式。",
            image_usage_none_exclusive: "「不使用图片」不能和其它图片选项同时选择。",
            font_heading: "标题",
            font_body: "正文",
            font_body_size: "正文基准字号",
            font_body_size_hint: "所有字号按这个正文基准推导。",
            body_size_hint_canvas: "当前画布建议 ~{lo}–{hi}px（随画布高度缩放）。",
            body_size_hint_purpose: "该交付目的推荐 {def}px（单一固定值，非区间）。",
            body_size_hint_oor: "（当前数值超出该画布的常用范围——请确认单位无误、是否合适。）",
            delivery_purpose: "交付目的",
            delivery_purpose_hint: "近读型可以小一点；投影型需要更大的字。",
            size_override: "逐角色字号覆盖：",
            size_role_title: "标题",
            size_role_subtitle: "副标题",
            size_role_annotation: "注释",
            custom_typography: "自定义字体方案",
            custom_typography_placeholder: "输入字体方案，如：标题用楷体；正文用微软雅黑…",
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
            refine_off_desc: "设计规范一次写完，流程自动继续。",
            refine_on_desc: "写完设计规范后停下供你审阅或修改，再开始生成。",
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
        },
        palette: {
            "cool-corporate": { zh: "冷静企业色", en: "Cool corporate", ja: "クール企業色" },
            "warm-earth": { zh: "暖土色", en: "Warm earth", ja: "ウォームアース" },
            "tech-neon": { zh: "科技霓虹", en: "Tech neon", ja: "テックネオン" },
            "editorial-classic": { zh: "经典编辑色", en: "Editorial classic", ja: "エディトリアルクラシック" },
            macaron: { zh: "马卡龙", en: "Macaron", ja: "マカロン" },
            "mono-ink": { zh: "单色墨线", en: "Mono ink", ja: "モノインク" },
            "vivid-launch": { zh: "高饱和发布", en: "Vivid launch", ja: "ビビッドローンチ" },
            "dark-cinematic": { zh: "暗色电影感", en: "Dark cinematic", ja: "ダークシネマティック" },
            duotone: { zh: "双色调", en: "Duotone", ja: "デュオトーン" },
            "nature-organic": { zh: "自然有机色", en: "Nature organic", ja: "自然オーガニック色" },
            "jewel-tone": { zh: "宝石色", en: "Jewel tone", ja: "ジュエルトーン" },
            "frost-ice": { zh: "霜冰浅色", en: "Frost ice", ja: "フロストアイス" },
            "sunset-gradient": { zh: "日落渐变", en: "Sunset gradient", ja: "サンセットグラデーション" },
            "earthy-dusty": { zh: "尘土大地色", en: "Earthy dusty", ja: "ダスティアース" }
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
    var REC = null;     // recommendations.json — AI picks + candidates
    var ICON_PREVIEWS = {};  // /api/icon-previews — real SVG samples from templates/icons
    var AI_IMAGE_COMPARISON = {};  // /api/ai-image-comparison — reference PNG options
    var STATE = {};
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
        if (candidate.rendering === "custom" || candidate.palette === "custom") return;
        var previews = [
            [t("image_strategy_rendering"), comparisonImageUrl("rendering", candidate.rendering)],
            [t("image_strategy_palette"), comparisonImageUrl("palette", candidate.palette)]
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

    function comparisonItems(kind) {
        return (AI_IMAGE_COMPARISON && AI_IMAGE_COMPARISON[kind]) || [];
    }

    function comparisonItem(kind, id) {
        var items = comparisonItems(kind);
        for (var i = 0; i < items.length; i += 1) {
            if (items[i] && items[i].id === id) return items[i];
        }
        return null;
    }

    function comparisonLabel(item, kind) {
        return item ? (comparisonValueLabel(kind, item.id) || item.label || item.id || "") : "";
    }

    function firstComparisonId(kind, fallback) {
        var items = comparisonItems(kind);
        if (fallback === "custom") return fallback;
        if (fallback && comparisonItem(kind, fallback)) return fallback;
        return items.length ? items[0].id : (fallback || "");
    }

    function comparisonSelect(kind, value) {
        var select = el("select", "text-input image-strategy-select");
        comparisonItems(kind).forEach(function (item) {
            var option = document.createElement("option");
            option.value = item.id;
            option.textContent = comparisonLabel(item, kind);
            select.appendChild(option);
        });
        var customOption = document.createElement("option");
        customOption.value = "custom";
        customOption.textContent = t("custom");
        select.appendChild(customOption);
        select.value = firstComparisonId(kind, value);
        return select;
    }

    function imageStrategyColorSummary(candidate) {
        var behavior = localized(candidate || {}, "color");
        return t("image_strategy_color_follow") + (behavior ? " " + behavior : "");
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
    // Guaranteed recommendation: the AI's pick, or the first catalog option as a
    // fallback so an enumerable field ALWAYS shows a badged recommendation.
    function recOrFirst(field, list) {
        var r = recId(field);
        if (r != null && r !== "") return r;
        return firstId(list);
    }
    // Render an enumerable field: ALL options from the catalog, recommended one
    // badged, current selection from STATE, plus a trailing Custom box.
    // `list` is either a flat array of {id,label,desc,dim,viewbox} or a grouped array
    // of {group, items:[...]}.
    function enumField(parent, list, recommendedId, getVal, setVal, opts2) {
        list = list || [];
        opts2 = opts2 || {};
        var grouped = list.length && list[0] && list[0].items;
        var flat = grouped ? list.reduce(function (a, g) { return a.concat(g.items || []); }, []) : list;
        var ids = flat.map(function (o) { return o.id; });
        // Optional personality spectrum: instead of a single ★ recommendation,
        // the AI marks a few catalog ids (safe / shifted / bold) each with a
        // temperament tag + a real-world analogy note. Replaces the single badge.
        var spectrum = (opts2.spectrum && opts2.spectrum.length) ? opts2.spectrum : null;
        var specById = {};
        if (spectrum) spectrum.forEach(function (s) {
            if (s && s.id) specById[s.id] = { tag: localized(s, "tag"), note: localized(s, "note") };
        });
        var allowCustom = opts2.allowCustom === true;  // only for fields not fully enumerable
        var customSentinel = opts2.customSentinel || "";
        var customInvalidValues = opts2.customInvalidValues || [];
        var cur = getVal();
        var isCustom = cur != null && cur !== "" && ids.indexOf(cur) === -1;
        if (!allowCustom && isCustom) {
            // closed field with an out-of-catalog value → snap to recommended/first
            cur = ids.indexOf(recommendedId) >= 0 ? recommendedId : ids[0];
            setVal(cur);
            isCustom = false;
        }

        var allChips = [];
        var customInput = el("input", "text-input custom-input");
        if (opts2.inputClass) customInput.classList.add(opts2.inputClass);
        customInput.type = "text";
        customInput.placeholder = opts2.placeholder || t("custom_placeholder");
        customInput.style.display = "none";

        function deselect() { allChips.forEach(function (c) { c.classList.remove("selected"); }); }
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
                customInput.style.display = "none";
                setVal(o.id);
            });
            allChips.push(chip);
            return chip;
        }

        if (grouped) {
            list.forEach(function (g) {
                if (groupLabel(g)) parent.appendChild(el("div", "group-label", groupLabel(g)));
                var row = el("div", "chips");
                (g.items || []).forEach(function (o) { row.appendChild(makeChip(o)); });
                parent.appendChild(row);
            });
            if (allowCustom) {
                var lastRow = el("div", "chips");
                lastRow.appendChild(buildCustomChip());
                parent.appendChild(lastRow);
            }
        } else {
            var wrap = el("div", "chips");
            flat.forEach(function (o) { wrap.appendChild(makeChip(o)); });
            if (allowCustom) wrap.appendChild(buildCustomChip());
            parent.appendChild(wrap);
        }
        if (allowCustom) parent.appendChild(customInput);

        function buildCustomChip() {
            var customChip = el("div", "chip", t("custom"));
            if (recommendedId && ids.indexOf(recommendedId) === -1) {
                customChip.classList.add("recommended");
                customChip.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
            if (isCustom) {
                customChip.classList.add("selected");
                customInput.style.display = "block";
                customInput.value = customInvalidValues.indexOf(cur) >= 0 ? "" : cur;
            }
            customChip.addEventListener("click", function () {
                deselect();
                customChip.classList.add("selected");
                customInput.style.display = "block";
                customInput.focus();
                setVal(customInput.value || customSentinel);
            });
            allChips.push(customChip);
            return customChip;
        }
        customInput.addEventListener("input", function () { setVal(customInput.value || customSentinel); });
    }

    function textField(parent, getVal, setVal, placeholderKey, numeric) {
        var input = el("input", numeric ? "num-input" : "text-input");
        input.type = "text";
        input.value = getVal() || "";
        input.placeholder = t(placeholderKey);
        input.addEventListener("input", function () { setVal(input.value); });
        parent.appendChild(input);
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

    function normTypography(c) {
        c = c || {};
        if (c.heading && typeof c.heading === "object" && c.body && typeof c.body === "object") {
            return Object.assign({}, c, {
                body_size: typographyBodySize(c),
                heading: Object.assign({}, c.heading, {
                    sample_cjk: c.heading.sample_cjk || c.sample_heading || "",
                    sample_latin: c.heading.sample_latin || c.sample_heading_latin || ""
                }),
                body: Object.assign({}, c.body, {
                    sample_cjk: c.body.sample_cjk || c.sample_body || "",
                    sample_latin: c.body.sample_latin || c.sample_body_latin || ""
                })
            });
        }
        return {
            name: c.name || "",
            note: c.note || "",
            custom: c.custom || "",
            body_size: typographyBodySize(c),
            heading: {
                cjk: c.heading || "",
                latin: c.heading_latin || "",
                css: c.heading_css || "",
                sample_cjk: c.sample_heading || "",
                sample_latin: c.sample_heading_latin || ""
            },
            body: {
                cjk: c.body || "",
                latin: c.body_latin || "",
                css: c.body_css || "",
                sample_cjk: c.sample_body || "",
                sample_latin: c.sample_body_latin || ""
            }
        };
    }

    function typographyBodySize(c) {
        c = c || {};
        var value = c.body_size || c.body_baseline || c.body_px ||
            (c.sizes && c.sizes.body) ||
            (c.size && c.size.body) ||
            (c.body && typeof c.body === "object" && (c.body.size || c.body.font_size));
        return value == null ? "" : String(value).replace(/px$/i, "");
    }

    function imageStrategySpec() {
        return (REC && REC.image_strategy) ||
            (REC && REC.images && REC.images.strategy) ||
            (REC && REC.images && REC.images.ai_strategy) ||
            {};
    }

    function imageStrategyCandidates() {
        var spec = imageStrategySpec();
        return spec.candidates || spec.options || [];
    }

    function imageStrategyRecommendationCandidates() {
        return imageStrategyCandidates().filter(function (candidate) {
            return candidate && candidate.rendering !== "custom" && candidate.palette !== "custom";
        }).slice(0, 3);
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
        var idx = spec.selected || 0;
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

    function renderAudience(host) {
        var sec = section(3, "sec_audience");
        textField(sec, function () { return STATE.audience; },
            function (v) { STATE.audience = v; }, "placeholder_audience", false);
        // Material divergence — a distinct, free-text sub-question inside §c, shown
        // right under the audience box: the user states in their own words how
        // closely to follow the source vs. how freely to reshape it. Free prose, not
        // fixed options; no page-count coupling, no source-signal recommendation.
        var subDiv = el("div", "subfield");
        subDiv.appendChild(el("div", "subfield-label", t("sub_divergence")));
        textField(subDiv, function () { return STATE.content_divergence; },
            function (v) { STATE.content_divergence = v; }, "placeholder_divergence", false);
        sec.appendChild(subDiv);
        // Delivery purpose (PPT only) lives in the §c key-information confirmation,
        // beside audience — it is part of "who / how this deck is consumed". It is a
        // Stage-1 anchor: its value sets the body size (one fixed value per purpose), page
        // density, and the re-derived Stage-2 page-count recommendation. Non-PPT
        // canvases scale the body by canvas height instead, so the axis does not apply.
        if (isPptCanvas(STATE.canvas)) {
            var purposeField = el("div", "subfield");
            purposeField.appendChild(el("div", "subfield-label", t("delivery_purpose")));
            enumField(purposeField, CAT.delivery_purpose,
                recOrFirst("delivery_purpose", CAT.delivery_purpose),
                function () { return STATE.delivery_purpose; },
                function (v) { STATE.delivery_purpose = v; });
            sec.appendChild(purposeField);
        }
        host.appendChild(sec);
    }

    function renderStyle(host) {
        var sec = section(4, "sec_style");
        sec.appendChild(el("div", "subfield-label", t("sub_mode")));
        enumField(sec, CAT.modes, recOrFirst("mode", CAT.modes),
            function () { return STATE.mode; }, function (v) { STATE.mode = v; }, { allowCustom: true });
        var sub2 = el("div", "subfield");
        sub2.appendChild(el("div", "subfield-label", t("sub_visual")));
        enumField(sub2, CAT.visual_styles, recOrFirst("visual_style", CAT.visual_styles),
            function () { return STATE.visual_style; }, function (v) { STATE.visual_style = v; refreshDirectionPreview(); },
            { allowCustom: true, spectrum: REC && REC.visual_style_spectrum });
        sec.appendChild(sub2);
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
    // Replaced when the Stage-1 visual-style preview mounts.
    var refreshDirectionPreview = function () {};
    // Replaced when the Stage-3 generated-image preview mounts.
    var refreshImageStrategyPreview = function () {};
    // Replaced when the typography section mounts; the canvas section calls it so
    // the body-size hint tracks the chosen canvas height.
    var refreshBodySizeHint = function () {};
    // Replaced when the typography section mounts; body-size / delivery changes
    // call it so the per-role size overrides the user hasn't pinned re-derive.
    var refreshSizeInputs = function () {};

    // Per-role size slots the user can edit directly (parallel to color roles).
    // Defaults derive from `body` via mid-band ramp ratios (strategist.md §g);
    // values are px (the system's only unit).
    var SIZE_ROLES = ["title", "subtitle", "annotation"];
    var SIZE_RATIO = { title: 1.75, subtitle: 1.35, annotation: 0.78 };
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

    // PPT canvases (16:9 / 4:3) take the fixed per-delivery-purpose body px;
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

    // Body baseline in **px** per delivery purpose (see strategist.md §g). The
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

    function roundSize(value) {
        return Math.round(value * 100) / 100;
    }

    function normalizeTypographyForSubmit(payload) {
        if (!payload.typography || typeof payload.typography !== "object") return;
        var typ = payload.typography;
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
        // delivery_purpose is PPT-only; drop it on non-PPT canvases where it has
        // no meaning and was never shown.
        if (!isPptCanvas(payload.canvas)) delete payload.delivery_purpose;
    }

    function renderColor(host) {
        var cands = (REC.color && REC.color.candidates) || [];
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
        customInput.rows = 2;
        customInput.placeholder = t("custom_color_placeholder");
        customInput.style.display = "none";

        function selectCard(idx) {
            var c = cands[idx] || {};
            selectedIdx = idx;
            STATE.color = { name: c.name || "", palette: Object.assign({}, normPalette(c)) };
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
                col.appendChild(s); col.appendChild(el("div", "swatch-role", t("role_" + role)));
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
            cands.forEach(function (c, i) { if (c.name === STATE.color.name) selIdx = i; });
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
            { allowCustom: true });
        host.appendChild(sec);
    }

    function previewFontStack(primary, fallback) {
        if (!primary) return fallback || "";
        if (!fallback) return primary;
        return primary + ", " + fallback;
    }

    function sampleText(role, script) {
        if (role === "heading") return t(script === "latin" ? "preview_latin_title" : "preview_big_title");
        return t(script === "latin" ? "preview_latin_body" : "preview_body_intro");
    }

    function fontSample(box, slot, css, role) {
        var line = el("div", "font-sample-line");
        var cjk = el("span", "fs-cjk", sampleText(role, "cjk"));
        var lat = el("span", "fs-latin", sampleText(role, "latin"));
        var cjkStack = previewFontStack(slot.cjk, css);
        var latinStack = previewFontStack(slot.latin, css);
        if (cjkStack) cjk.style.fontFamily = cjkStack;
        if (latinStack) lat.style.fontFamily = latinStack;
        if (cjkStack) cjk.title = cjkStack;
        if (latinStack) lat.title = latinStack;
        line.appendChild(cjk); line.appendChild(lat); box.appendChild(line);
    }

    function renderTypography(host) {
        var f = REC.typography || {};
        var cands = f.candidates || [];
        var sec = section(7, "sec_type");
        var grid = el("div", "font-grid");
        var customInput = el("textarea", "text-input custom-typography-input");
        customInput.rows = 2;
        customInput.placeholder = t("custom_typography_placeholder");
        customInput.style.display = "none";

        function selectFont(idx, preserveSizing) {
            var c = normTypography(cands[idx] || {});
            var prev = STATE.typography || {};
            STATE.typography = {
                name: c.name || "",
                heading: c.heading || {},
                body: c.body || {},
                body_size: (preserveSizing && prev.body_size) ? prev.body_size : (c.body_size || prev.body_size || ""),
                sizes: (preserveSizing && prev.sizes) ? Object.assign({}, prev.sizes) : Object.assign({}, c.sizes || {})
            };
            if (sizeInput) sizeInput.value = STATE.typography.body_size || "";
            customInput.style.display = "none";
            grid.querySelectorAll(".font-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
            refreshSizeInputs();   // fill any role with no value yet; never overwrites existing values
            refreshStylePreview();
        }

        function selectCustomTypography() {
            var prev = STATE.typography || {};
            STATE.typography = {
                name: "custom",
                custom: customInput.value || "",
                heading: {},
                body: {},
                body_size: prev.body_size || "",
                sizes: Object.assign({}, prev.sizes || {})   // switching font family must not drop sizes
            };
            grid.querySelectorAll(".font-card").forEach(function (card) { card.classList.remove("selected"); });
            customCard.classList.add("selected");
            customInput.style.display = "block";
            customInput.focus();
            refreshSizeInputs();
            refreshStylePreview();
        }

        cands.forEach(function (c, idx) {
            c = normTypography(c);
            var head = c.heading || {}, body = c.body || {};
            var card = el("div", "font-card");
            var top = el("div", "font-card-head");
            top.appendChild(el("span", "font-card-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            var meta = t("font_heading") + " " + t("cjk") + ":" + (head.cjk || "—") + " / " + t("latin") + ":" + (head.latin || "—")
                + "  ·  " + t("font_body") + " " + t("cjk") + ":" + (body.cjk || "—") + " / " + t("latin") + ":" + (body.latin || "—");
            if (c.body_size) meta += "  ·  " + t("font_body_size") + ":" + c.body_size + "px";
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
        customInput.addEventListener("input", function () {
            if (!STATE.typography || STATE.typography.name !== "custom") selectCustomTypography();
            STATE.typography.custom = customInput.value;
            refreshStylePreview();
        });
        sec.appendChild(customInput);

        var sizeField = el("div", "subfield");
        sizeField.appendChild(el("div", "subfield-label", t("font_body_size")));
        var sizeRow = el("div", "font-size-row");
        var sizeInput = el("input", "num-input font-size-input");
        sizeInput.type = "number";
        sizeInput.min = "8";
        sizeInput.max = "96";
        sizeInput.step = "1";
        sizeInput.value = (STATE.typography && STATE.typography.body_size) || "";
        sizeInput.placeholder = isPptCanvas(STATE.canvas) ? "16 / 20 / 24" : "40 / 48";
        sizeInput.addEventListener("input", function () {
            if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
            // Independent input — body never auto-changes the role sizes (no
            // interlinking); the role inputs carry their own values.
            STATE.typography.body_size = sizeInput.value;
            refreshBodySizeHint();   // hint text only (e.g. out-of-range flag) — no value cascade
            refreshStylePreview();
        });
        sizeRow.appendChild(sizeInput);
        var sizeHint = el("div", "toggle-desc");
        sizeRow.appendChild(sizeHint);
        // Hint only — the user's value is never overwritten; downstream §g
        // re-derives if ignored. PPT body is one fixed px value per delivery
        // purpose (not a range); non-PPT canvases scale px to canvas height.
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
            // Flag (hint only — never auto-corrected) a value far outside the
            // canvas's usual px range, so an accidental extreme value is visible
            // instead of silently submitting it.
            var cur = parseFloat(STATE.typography && STATE.typography.body_size);
            if (isFinite(cur) && isFinite(lo) && isFinite(hi) && (cur < lo || cur > hi)) {
                txt += " " + t("body_size_hint_oor");
            }
            sizeHint.textContent = txt;
        };
        refreshBodySizeHint();
        sizeField.appendChild(sizeRow);

        // Delivery purpose is a Stage-1 anchor confirmed inside renderAudience (§c) —
        // it is set before this Stage-2 section exists, so its value drives the
        // body-size hint here via STATE.delivery_purpose (preserved across the
        // single-session transition). The control itself no longer lives here.
        sec.appendChild(sizeField);

        // Per-role size override (parallel to color's per-role HEX override): the
        // ramp derives title / subtitle / annotation from body, but the user may
        // set each explicitly. Values are px (the system's only unit).
        var sizeOverride = el("div", "hex-override");
        sizeOverride.appendChild(el("div", "subfield-label", t("size_override")));
        var srow = el("div", "hex-row");
        var sizeInputs = {};
        SIZE_ROLES.forEach(function (role) {
            var wrap = el("div", "hex-cell");
            wrap.appendChild(el("div", "hex-cell-label", t("size_role_" + role)));
            var inp = document.createElement("input");
            inp.type = "number"; inp.min = "6"; inp.max = "200"; inp.step = "1";
            inp.addEventListener("input", function () {
                if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
                if (!STATE.typography.sizes) STATE.typography.sizes = {};
                // Independent input — each role holds its own value; no cascade.
                STATE.typography.sizes[role] = inp.value;
                refreshStylePreview();
            });
            sizeInputs[role] = inp;
            wrap.appendChild(inp); srow.appendChild(wrap);
        });
        sizeOverride.appendChild(srow);
        sec.appendChild(sizeOverride);

        // Inputs are independent — this only **fills a role that has no value yet**
        // (a one-time starting suggestion from the ramp) and reflects the current
        // value into the input. It never overwrites an existing value, so editing
        // body / purpose / canvas does not cascade into the role sizes, and a
        // re-render (canvas / language switch) preserves exactly what the user sees.
        refreshSizeInputs = function () {
            if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
            if (!STATE.typography.sizes) STATE.typography.sizes = {};
            var bodyVal = parseFloat(STATE.typography.body_size) ||
                (isPptCanvas(STATE.canvas) ? deliveryBodyPx(STATE.delivery_purpose).def : 40);
            SIZE_ROLES.forEach(function (role) {
                var cur = STATE.typography.sizes[role];
                var hasVal = cur !== undefined && cur !== null && cur !== "";
                if (!hasVal) STATE.typography.sizes[role] = deriveSize(role, bodyVal);
                if (sizeInputs[role]) sizeInputs[role].value = STATE.typography.sizes[role];
            });
        };
        refreshSizeInputs();

        var subfp = el("div", "subfield");
        subfp.appendChild(el("div", "subfield-label", t("formula_policy")));
        enumField(subfp, CAT.formula_policy, recOrFirst("formula_policy", CAT.formula_policy),
            function () { return STATE.formula_policy; }, function (v) { STATE.formula_policy = v; });
        sec.appendChild(subfp);
        host.appendChild(sec);

        var selIdx = -1;
        if (STATE.typography && STATE.typography.name) cands.forEach(function (c, i) { if (c.name === STATE.typography.name) selIdx = i; });
        if (selIdx >= 0) selectFont(selIdx, true);
        else if (STATE.typography && STATE.typography.name === "custom") {
            customInput.value = STATE.typography.custom || "";
            customCard.classList.add("selected");
            customInput.style.display = "block";
        }
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
        var titleCjk = el("span", "sp-title-cjk");
        var titleLat = el("span", "sp-title-lat");
        title.appendChild(titleCjk); title.appendChild(titleLat);
        var bodyRow = el("div", "sp-body");
        var accentBar = el("span", "sp-accent-bar");
        var bodyWrap = el("div", "sp-body-wrap");
        var bodyCjk = el("span", "sp-body-cjk");
        var bodyLat = el("span", "sp-body-lat");
        bodyWrap.appendChild(bodyCjk); bodyWrap.appendChild(bodyLat);
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
            var headStack = previewFontStack(head.cjk, head.css);
            var headLatStack = previewFontStack(head.latin, head.css);
            var bodyStack = previewFontStack(body.cjk, body.css);
            var bodyLatStack = previewFontStack(body.latin, body.css);

            card.style.background = bg;
            titleCjk.textContent = t("preview_big_title");
            titleLat.textContent = t("preview_section_title");
            title.style.color = pri;
            title.style.fontSize = Math.round(bodyPx * 1.7) + "px";
            titleCjk.style.fontFamily = headStack || "";
            titleLat.style.fontFamily = headLatStack || "";
            // CJK and Latin previewed with their own stacks (mirrors the title
            // and the per-card font samples) so each script's font is visible.
            bodyCjk.textContent = t("preview_body_intro");
            bodyLat.textContent = "";
            bodyWrap.style.color = txt;
            bodyWrap.style.fontSize = bodyPx + "px";
            bodyCjk.style.fontFamily = bodyStack || "";
            bodyLat.style.fontFamily = bodyLatStack || "";
            accentBar.style.background = acc;
            content.style.color = txt;
            content.innerHTML = stylePreviewContentMarkup(STATE.icons);
            chip.style.background = sbg;
            chipDot.style.background = sacc;
            chipLabel.textContent = t("role_secondary_bg");
            chipLabel.style.color = txt;
        }
        refreshStylePreview = paint;
        paint();
    }

    function renderDirectionPreview(host) {
        var wrap = el("div", "style-preview direction-preview");
        var label = el("div", "style-preview-label");
        label.appendChild(el("span", "spl-title", t("sub_visual")));
        label.appendChild(el("span", "spl-note", t("style_preview_body")));
        wrap.appendChild(label);
        var card = el("div", "style-preview-card direction-preview-card");
        var visual = el("div", "direction-preview-visual");
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
            var option = findCatalogOption(CAT.visual_styles, STATE.visual_style);
            visual.innerHTML = "";
            appendVisualStyleImage(visual, STATE.visual_style);
            title.textContent = option ? optionLabel(option) : (STATE.visual_style || "");
            desc.textContent = option ? optionDesc(option) : "";
        }
        refreshDirectionPreview = paint;
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
            if (!row) visual.appendChild(el("div", "toggle-desc", t("image_strategy_no_reference")));
            title.textContent = strategy.name || t("image_strategy_manual");
            var parts = [];
            if (strategy.rendering) parts.push(t("image_strategy_rendering") + ": " + comparisonValueLabel("rendering", strategy.rendering));
            if (strategy.palette) parts.push(t("image_strategy_palette") + ": " + comparisonValueLabel("palette", strategy.palette));
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

    function renderImages(host) {
        var sec = section(8, "sec_images");
        var usageChips = el("div", "chips");
        var usageNote = el("div", "subfield");
        usageNote.appendChild(el("div", "subfield-label", t("image_usage_notes")));
        var usageNoteInput = el("textarea", "text-input image-usage-notes-input");
        usageNoteInput.placeholder = t("image_usage_notes_placeholder");
        usageNoteInput.value = STATE.image_notes || "";
        usageNoteInput.addEventListener("input", function () { STATE.image_notes = usageNoteInput.value; });
        usageNote.appendChild(usageNoteInput);
        var sub = el("div", "subfield");
        sub.appendChild(el("div", "subfield-label", t("image_ai_path")));
        var strategySub = el("div", "subfield image-strategy-subfield");
        strategySub.appendChild(el("div", "subfield-label", t("image_strategy")));
        strategySub.appendChild(el("div", "toggle-desc", t("image_strategy_reference_hint")));
        var strategyGrid = el("div", "font-grid");
        var strategyCands = imageStrategyRecommendationCandidates();
        function needsGeneratedImages() {
            return needsGeneratedImagesForUsage(STATE.image_usage);
        }
        function refreshAiControls() {
            var needsAiPath = needsGeneratedImages();
            sub.style.display = needsAiPath ? "block" : "none";
            strategySub.style.display = needsAiPath ? "block" : "none";
            refreshImageStrategyPreview();
        }
        function markStrategyCard(selectedCard) {
            strategyGrid.querySelectorAll(".font-card").forEach(function (card) {
                card.classList.toggle("selected", card === selectedCard);
            });
        }
        function selectImageStrategy(idx, selectedCard) {
            var c = strategyCands[idx] || {};
            STATE.image_strategy = {
                name: localized(c, "name") || c.name || "",
                rendering: c.rendering || "",
                palette: c.palette || "",
                visual: localized(c, "visual") || "",
                color: imageStrategyColorSummary(c),
                mood: localized(c, "mood") || ""
            };
            markStrategyCard(selectedCard || strategyGrid.querySelector('[data-strategy-index="' + idx + '"]'));
            refreshImageStrategyPreview();
        }
        strategyCands.forEach(function (c, idx) {
            var card = el("div", "font-card");
            card.setAttribute("data-strategy-index", String(idx));
            var top = el("div", "font-card-head");
            top.appendChild(el("span", "font-card-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            var meta = [];
            if (c.rendering) meta.push(t("image_strategy_rendering") + ":" + comparisonValueLabel("rendering", c.rendering));
            if (c.palette) meta.push(t("image_strategy_palette") + ":" + comparisonValueLabel("palette", c.palette));
            if (meta.length) top.appendChild(el("span", "font-card-meta", meta.join("  ·  ")));
            card.appendChild(top);
            [
                ["image_strategy_visual", localized(c, "visual")],
                ["image_strategy_color", imageStrategyColorSummary(c)],
                ["image_strategy_mood", localized(c, "mood")]
            ].forEach(function (row) {
                if (row[1]) card.appendChild(el("div", "color-note", t(row[0]) + "：" + row[1]));
            });
            card.addEventListener("click", function () { selectImageStrategy(idx, card); });
            strategyGrid.appendChild(card);
        });
        if (!strategyCands.length) strategyGrid.appendChild(el("div", "toggle-desc", t("image_strategy_empty")));
        var manualCard = el("div", "font-card image-strategy-manual-card");
        var manualTop = el("div", "font-card-head");
        manualTop.appendChild(el("span", "font-card-name", t("image_strategy_manual")));
        manualTop.appendChild(el("span", "font-card-meta", t("image_strategy_manual_desc")));
        manualCard.appendChild(manualTop);
        var manualControls = el("div", "image-strategy-manual-controls");
        var manualRendering = firstComparisonId("rendering", (STATE.image_strategy && STATE.image_strategy.rendering) || (strategyCands[0] && strategyCands[0].rendering));
        var manualPalette = firstComparisonId("palette", (STATE.image_strategy && STATE.image_strategy.palette) || (strategyCands[0] && strategyCands[0].palette));
        var renderingWrap = el("label", "image-strategy-select-wrap");
        renderingWrap.appendChild(el("span", "image-strategy-select-label", t("image_strategy_rendering")));
        var renderingSelect = comparisonSelect("rendering", manualRendering);
        renderingWrap.appendChild(renderingSelect);
        var paletteWrap = el("label", "image-strategy-select-wrap");
        paletteWrap.appendChild(el("span", "image-strategy-select-label", t("image_strategy_palette")));
        var paletteSelect = comparisonSelect("palette", manualPalette);
        paletteWrap.appendChild(paletteSelect);
        manualControls.appendChild(renderingWrap);
        manualControls.appendChild(paletteWrap);
        manualCard.appendChild(manualControls);
        function selectManualImageStrategy() {
            var rendering = renderingSelect.value;
            var palette = paletteSelect.value;
            STATE.image_strategy = {
                name: t("image_strategy_manual"),
                rendering: rendering,
                palette: palette,
                visual: comparisonLabel(comparisonItem("rendering", rendering), "rendering") || comparisonValueLabel("rendering", rendering),
                color: t("image_strategy_color_follow"),
                mood: t("image_strategy_manual_desc")
            };
            markStrategyCard(manualCard);
            refreshImageStrategyPreview();
        }
        [renderingSelect, paletteSelect].forEach(function (select) {
            select.addEventListener("click", function (e) { e.stopPropagation(); });
            select.addEventListener("change", function () {
                selectManualImageStrategy();
            });
        });
        manualCard.addEventListener("click", selectManualImageStrategy);
        strategyGrid.appendChild(manualCard);
        strategySub.appendChild(strategyGrid);
        var recommendedIds = selectedImageUsageIds(recValue("image_usage"));
        if (!recommendedIds.length) recommendedIds = [defaultImageUsageId()];
        var usageChipById = {};
        function refreshUsageChips() {
            Object.keys(usageChipById).forEach(function (id) {
                usageChipById[id].classList.toggle("selected", STATE.image_usage.indexOf(id) >= 0);
            });
            var noImages = STATE.image_usage.indexOf("none") >= 0;
            usageNote.style.display = noImages ? "none" : "block";
            refreshAiControls();
        }
        function toggleImageUsage(id) {
            var cur = STATE.image_usage.slice();
            if (id === "none") {
                cur = cur.indexOf("none") >= 0 ? [] : ["none"];
            } else {
                cur = cur.filter(function (item) { return item !== "none"; });
                if (cur.indexOf(id) >= 0) cur = cur.filter(function (item) { return item !== id; });
                else cur.push(id);
            }
            STATE.image_usage = cur;
            refreshUsageChips();
        }
        (CAT.image_usage || []).forEach(function (o) {
            var label = optionLabel(o);
            var desc = optionDesc(o);
            if (desc) label += (LANG === "zh" || LANG === "ja" ? "：" : " — ") + desc;
            var chip = el("div", "chip");
            chip.appendChild(el("span", "chip-text", label));
            if (recommendedIds.indexOf(o.id) >= 0) {
                chip.classList.add("recommended");
                chip.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
            chip.addEventListener("click", function () { toggleImageUsage(o.id); });
            usageChipById[o.id] = chip;
            usageChips.appendChild(chip);
        });
        sec.appendChild(usageChips);
        sec.appendChild(usageNote);
        enumField(sub, CAT.image_ai_path, recOrFirst("image_ai_path", CAT.image_ai_path),
            function () { return STATE.image_ai_path; }, function (v) { STATE.image_ai_path = v; });
        sec.appendChild(sub);
        sec.appendChild(strategySub);
        if (strategyCands.length) selectImageStrategy(imageStrategySelectedIndex());
        else selectManualImageStrategy();
        refreshUsageChips();
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

    // Stage of the staged confirm flow:
    // 1 = direction anchors, 2 = design system, 3 = images/execution,
    // "all" = legacy single-pass (recommendations.json carried no stage).
    var STAGE = 1;

    function stageNumber(data) {
        var raw = data && data.stage != null ? data.stage : (data && data.tier);
        raw = String(raw == null ? "" : raw).toLowerCase();
        if (raw === "1" || raw === "stage1" || raw === "tier1") return 1;
        if (raw === "2" || raw === "stage2" || raw === "tier2") return 2;
        if (raw === "3" || raw === "stage3" || raw === "tier3") return 3;
        return "all";
    }

    function stageTitle(stage) {
        if (stage === 1) return t("stage_anchors");
        if (stage === 2) return t("stage_design");
        if (stage === 3) return t("stage_images");
        return t("page_title");
    }

    function renderForStage(stage) {
        var host = document.getElementById("sections");
        host.innerHTML = "";
        _secCounter = 0;
        var heading = document.querySelector("#topbar .topbar-titles h1");
        if (heading) heading.textContent = stageTitle(stage);
        // Detach the previous preview's repaint closures before the sections
        // re-render: color/typography auto-select would otherwise call them and
        // write to now-detached nodes until renderStylePreview remounts them.
        refreshStylePreview = function () {};
        refreshDirectionPreview = function () {};
        refreshImageStrategyPreview = function () {};
        refreshBodySizeHint = function () {};
        refreshSizeInputs = function () {};
        var previewHost = document.getElementById("topbar-preview");
        if (previewHost) previewHost.innerHTML = "";
        if (stage === 1) {
            if (previewHost) renderDirectionPreview(previewHost);
            // Direction anchors — Stage 2 is re-derived from these.
            // Delivery purpose rides inside renderAudience (§c key info).
            renderCanvas(host);
            renderAudience(host);
            renderStyle(host);
        } else if (stage === 2) {
            if (previewHost) renderStylePreview(previewHost);
            renderPages(host);
            // Group the three sections reflected by the fixed preview strip.
            var styleGroup = el("div", "style-group");
            renderColor(styleGroup);
            renderIcons(styleGroup);
            renderTypography(styleGroup);
            host.appendChild(styleGroup);
        } else if (stage === 3) {
            if (previewHost) renderImageStrategyPreview(previewHost);
            renderImages(host);
            renderMode(host);
            renderRefine(host);
        } else {
            // Legacy single-pass: show every section on one page.
            if (previewHost) renderStylePreview(previewHost);
            renderCanvas(host);
            renderAudience(host);
            renderStyle(host);
            renderPages(host);
            var legacyStyleGroup = el("div", "style-group");
            renderColor(legacyStyleGroup);
            renderIcons(legacyStyleGroup);
            renderTypography(legacyStyleGroup);
            host.appendChild(legacyStyleGroup);
            renderImages(host);
            renderMode(host);
            renderRefine(host);
        }
        updateActionBar(stage);
    }

    function renderAll() { renderForStage(STAGE); }

    function updateActionBar(stage) {
        var btn = document.getElementById("btn-confirm");
        btn.disabled = false;
        // Stage 1/2 advance; Stage 3 / single-pass confirm.
        btn.textContent = (stage === 1 || stage === 2) ? t("btn_next") : t("btn_confirm");
    }

    // ---- state init (once) ----------------------------------------------
    function firstId(list) {
        if (!list || !list.length) return undefined;
        if (list[0].items) return (list[0].items[0] || {}).id;
        return list[0].id;
    }
    function pick(field, catList) {
        return recOrFirst(field, catList);
    }

    function initStage1State() {
        STATE.canvas = pick("canvas", CAT.canvas);
        STATE.audience = (REC.audience && REC.audience.value) || "";
        STATE.content_divergence = (REC.content_divergence && REC.content_divergence.value) || "";  // free text; blank = balanced default
        STATE.mode = pick("mode", CAT.modes);
        STATE.visual_style = pick("visual_style", CAT.visual_styles);
        // Delivery purpose drives the PPT body px baseline; default balanced
        // (not the catalog-first id) when the Strategist did not recommend one.
        STATE.delivery_purpose = recId("delivery_purpose") || "balanced";
    }

    // Stage-2 fields are (re-)read from the recommendations. At boot they come from
    // whatever recommendations.json carried; after a stage-1 confirm enterStage()
    // calls this again with the re-derived candidates. Stage-1 STATE is preserved
    // across the single-session transition — this never resets the anchors.
    function initStage2State() {
        STATE.page_count = (REC.page_count && REC.page_count.value != null) ? String(REC.page_count.value) : (STATE.page_count || "");

        var cc = (REC.color && REC.color.candidates) || [];
        var csel = (REC.color && REC.color.selected) || 0;
        var c0 = cc[Math.min(csel, Math.max(cc.length - 1, 0))] || {};
        STATE.color = { name: c0.name || "", palette: Object.assign({}, normPalette(c0)) };

        STATE.icons = pick("icons", CAT.icons);

        var tc = (REC.typography && REC.typography.candidates) || [];
        var tsel = (REC.typography && REC.typography.selected) || 0;
        var t0 = normTypography(tc[Math.min(tsel, Math.max(tc.length - 1, 0))] || {});
        STATE.typography = {
            name: t0.name || "",
            heading: t0.heading || {},
            body: t0.body || {},
            body_size: t0.body_size || typographyBodySize(REC.typography),
            sizes: Object.assign({}, t0.sizes || {})
        };
        STATE.formula_policy = pick("formula_policy", CAT.formula_policy);

        // Guarantee a body baseline even when a candidate omitted body_size, on
        // any canvas (PPT → px default by purpose, non-PPT → px from canvas height),
        // so role sizes never derive from an empty anchor.
        if (STATE.typography && !STATE.typography.body_size) {
            STATE.typography.body_size = defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose);
        }
    }

    function initStage3State() {
        var rawImageUsage = recValue("image_usage");
        STATE.image_usage = selectedImageUsageIds(rawImageUsage);
        if (!STATE.image_usage.length) {
            STATE.image_usage = [defaultImageUsageId()];
        }
        STATE.image_notes = imageUsageNotesRecommendation(rawImageUsage);
        STATE.image_ai_path = pick("image_ai_path", CAT.image_ai_path);

        STATE.generation_mode = pick("generation_mode", CAT.generation_mode);
        STATE.refine_spec = !!((REC.refine_spec && REC.refine_spec.value) || (REC.recommend && REC.recommend.refine_spec));
    }

    function initState() {
        initStage1State();
        initStage2State();
        initStage3State();
    }

    // ---- confirm + close -------------------------------------------------
    function showConfirmedOverlay() {
        var ov = document.getElementById("confirmed-overlay");
        ov.querySelector(".cf-title").textContent = t("confirmed_title");
        ov.querySelector(".cf-hint").textContent = t("confirmed_hint");
        ov.style.display = "flex";
    }

    // ---- staged submit + re-derive transitions --------------------------
    function stage1Payload() {
        var payload = {
            stage: "stage1",
            canvas: STATE.canvas,
            audience: STATE.audience,
            content_divergence: STATE.content_divergence,
            mode: STATE.mode,
            visual_style: STATE.visual_style
        };
        // Delivery purpose is PPT-only and rendered only on PPT canvases (§c).
        if (isPptCanvas(STATE.canvas)) payload.delivery_purpose = STATE.delivery_purpose;
        return payload;
    }

    function stage2Payload() {
        var payload = {
            stage: "stage2",
            canvas: STATE.canvas,
            audience: STATE.audience,
            content_divergence: STATE.content_divergence,
            mode: STATE.mode,
            visual_style: STATE.visual_style,
            page_count: STATE.page_count,
            color: STATE.color,
            icons: STATE.icons,
            typography: STATE.typography,
            formula_policy: STATE.formula_policy
        };
        if (isPptCanvas(STATE.canvas)) payload.delivery_purpose = STATE.delivery_purpose;
        normalizeTypographyForSubmit(payload);
        return payload;
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

    function submitStage1() { submitStage(stage1Payload(), 2); }

    function submitStage2() { submitStage(stage2Payload(), 3); }

    function showDeriving() {
        document.getElementById("sections").style.display = "none";
        document.getElementById("actionbar").style.display = "none";
        var l = document.getElementById("loading");
        l.textContent = t("deriving");
        l.style.display = "block";
    }

    // Poll the recommendations endpoint (no-store) until the AI overwrites it with
    // the next re-derived stage, then render it in the same session.
    function pollForStage(nextStage) {
        fetch("/api/recommendations", { cache: "no-store" })
            .then(function (r) { if (!r.ok) throw new Error("poll failed"); return r.json(); })
            .then(function (data) {
                if (data && stageNumber(data) === nextStage) { enterStage(data, nextStage); }
                else { setTimeout(function () { pollForStage(nextStage); }, 1200); }
            }).catch(function (err) {
                var l = document.getElementById("loading");
                if (l) l.textContent = t("load_error") + " " + (err && err.message ? err.message : "");
                setTimeout(function () { pollForStage(nextStage); }, 1500);
            });
    }

    function enterStage(data, stage) {
        REC = data;
        if (stage === 2) initStage2State();
        if (stage === 3) initStage3State();
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
        if (!payload.image_usage.length) {
            document.getElementById("confirm-status").textContent = t("image_usage_required");
            return;
        }
        if (payload.image_usage.indexOf("none") >= 0 && payload.image_usage.length > 1) {
            document.getElementById("confirm-status").textContent = t("image_usage_none_exclusive");
            return;
        }
        if (!String(payload.image_notes || "").trim()) delete payload.image_notes;
        if (!needsGeneratedImagesForUsage(payload.image_usage)) {
            delete payload.image_ai_path;
            delete payload.image_strategy;
        }
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

    function loadCatalogs() {
        return fetch("/api/catalogs")
            .then(function (r) { if (r.ok) return r.json(); throw new Error("no api"); })
            .catch(function () { return fetch("/static/catalogs.json").then(function (r) { return r.json(); }); });
    }

    function loadIconPreviews() {
        return fetch("/api/icon-previews")
            .then(function (r) { if (r.ok) return r.json(); throw new Error("no icon preview api"); })
            .catch(function () { return {}; });
    }

    function loadAiImageComparison() {
        return fetch("/api/ai-image-comparison")
            .then(function (r) { if (r.ok) return r.json(); throw new Error("no ai image comparison api"); })
            .catch(function () { return {}; });
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
            if (REC && CAT) renderAll();   // STATE persists → selections preserved
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

        Promise.all([
            loadCatalogs(),
            fetch("/api/recommendations").then(function (r) { if (!r.ok) throw new Error("load failed"); return r.json(); }),
            loadIconPreviews(),
            loadAiImageComparison()
        ]).then(function (res) {
            CAT = res[0];
            REC = res[1];
            ICON_PREVIEWS = res[2] || {};
            AI_IMAGE_COMPARISON = res[3] || {};
            if (REC.lang === "zh" || REC.lang === "en" || REC.lang === "ja") {
                var hasStored = false;
                try { hasStored = !!window.localStorage.getItem("ppt_lang"); } catch (e) { /* ignore */ }
                if (!hasStored) { LANG = REC.lang; applyStaticTranslations(); refreshLangToggle(toggleBtn); }
            }
            initState();
            // stage 1 / 2 / 3 from the recommendations; absent → legacy single-pass.
            STAGE = stageNumber(REC);
            document.getElementById("loading").style.display = "none";
            document.getElementById("sections").style.display = "block";
            document.getElementById("actionbar").style.display = "flex";
            renderAll();
            if (REC._already_confirmed) {
                document.getElementById("confirm-status").textContent = t("already_confirmed");
            }
        }).catch(function () {
            showError(t("load_error"));
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
