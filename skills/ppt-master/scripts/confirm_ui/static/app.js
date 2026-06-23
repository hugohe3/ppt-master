/* PPT Master - Eight Confirmations UI
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
            image_usage_custom_required: "Describe the custom image plan before confirming.",
            font_heading: "Heading",
            font_body: "Body",
            font_body_size: "Body baseline size",
            font_body_size_hint: "All type sizes derive from this body baseline.",
            body_size_hint_canvas: "This canvas suggests ~{lo}–{hi}px (scales with canvas height).",
            body_size_hint_pt: "PPT body is confirmed in pt — this purpose suggests ~{lo}–{hi}pt (default {def}pt). Saved as px after confirmation.",
            body_size_hint_oor: "(Current value is outside this range — it is not auto-converted across canvases; check it fits.)",
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
            sample_cjk: "数字化转型战略",
            sample_latin: "Digital Transformation",
            style_preview_label: "Overall impression (color + typography)",
            style_preview_body: "· rough feel only, not the actual slide layout",
            mode_continuous_desc: "Generate the whole deck in one pass.",
            mode_split_desc: "Stop after the spec; resume SVG generation in a fresh window.",
            refine_off_desc: "Spec is written in one go; the pipeline auto-proceeds.",
            refine_on_desc: "Stop after the spec for review/revision before any generation.",
            off_default: "Off",
            on: "On",
            option_prefix: "Option",
            error_retry: "Error - retry"
        },
        zh: {
            page_title: "确认设计方案",
            topbar_hint: "选择或自定义各项后点「确认」；页面会关闭，请回到聊天窗口。",
            loading: "加载中…",
            load_error: "无法加载推荐文件，需在启动前写入。",
            btn_confirm: "确认",
            btn_next: "下一步 →",
            deriving: "正在据你的选择生成下游选项…",
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
            image_usage_custom_required: "请先写清楚自定义图片方案。",
            font_heading: "标题",
            font_body: "正文",
            font_body_size: "正文基准字号",
            font_body_size_hint: "所有字号按这个正文基准推导。",
            body_size_hint_canvas: "当前画布建议 ~{lo}–{hi}px（随画布高度缩放）。",
            body_size_hint_pt: "PPT 正文确认时用 pt — 该交付目的建议 ~{lo}–{hi}pt（默认 {def}pt），确认后保存为 px。",
            body_size_hint_oor: "（当前数值不在此区间——换画布不会自动换算，请确认是否合适。）",
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
            sample_cjk: "数字化转型战略",
            sample_latin: "Digital Transformation",
            style_preview_label: "整体形象（配色 + 字体）",
            style_preview_body: "· 仅大致形象，非实际版式",
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
            if (stored === "zh" || stored === "en") return stored;
        } catch (e) { /* ignore */ }
        var nav = (navigator.language || navigator.userLanguage || "en").toLowerCase();
        return nav.indexOf("zh") === 0 ? "zh" : "en";
    })();

    function t(key) {
        var dict = MESSAGES[LANG] || MESSAGES.en;
        return dict[key] != null ? dict[key] : key;
    }

    function localized(obj, base) {
        if (!obj) return "";
        var langKey = base + "_" + LANG;
        var fallbackKey = base + "_" + (LANG === "zh" ? "en" : "zh");
        if (obj[langKey] != null) return obj[langKey];
        if (obj[base] != null) {
            if (typeof obj[base] === "object") {
                return obj[base][LANG] || obj[base].en || obj[base].zh || "";
            }
            return obj[base];
        }
        return obj[fallbackKey] || "";
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

    function applyStaticTranslations() {
        document.documentElement.setAttribute("lang", LANG === "zh" ? "zh-CN" : "en");
        document.querySelectorAll("[data-i18n]").forEach(function (node) {
            node.textContent = t(node.getAttribute("data-i18n"));
        });
    }

    function refreshLangToggle(toggleBtn) {
        toggleBtn.textContent = LANG === "zh" ? "EN" : "中";
        toggleBtn.title = t("lang_toggle_title");
    }

    // ---- state -----------------------------------------------------------
    var CAT = null;     // catalogs.json — finite option universe
    var REC = null;     // recommendations.json — AI picks + candidates
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

    // Section numbers run 1..N within the tier currently rendered; the counter is
    // reset at the top of renderForTier. The legacy `num` arg is ignored so each
    // tier numbers its own sections cleanly (tier 2 is not a continuation of 1).
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
        if (value == null || value === "") return value;
        var aliases = REC_ALIASES[field] || {};
        return aliases[value] || value;
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
    // Guaranteed recommendation: the AI's pick, or the first catalog option as a
    // fallback so an enumerable field ALWAYS shows a badged recommendation.
    function recOrFirst(field, list) {
        var r = recId(field);
        if (r != null && r !== "") return r;
        return firstId(list);
    }

    // Render an enumerable field: ALL options from the catalog, recommended one
    // badged, current selection from STATE, plus a trailing Custom box.
    // `list` is either a flat array of {id,label,desc,dim} or a grouped array
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
            if (o.dim) label += " · " + o.dim;
            var desc = optionDesc(o);
            if (desc) label += (LANG === "zh" ? "：" : " — ") + desc;
            var spec = specById[o.id];
            if (spec && spec.note) label += " · " + spec.note;
            var chip = el("div", "chip");
            chip.appendChild(el("span", "chip-text", label));
            if (spec) {
                // spectrum pick: badge shows its temperament tag, not the generic ★
                chip.classList.add("recommended");
                chip.appendChild(el("span", "rec-badge", "★ " + (spec.tag || t("recommended"))));
            } else if (!spectrum && o.id === recommendedId) {
                chip.classList.add("recommended");
                chip.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
            }
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
            return Object.assign({}, c, { body_size: typographyBodySize(c) });
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

    function usesCustomImagePlanValue(value) {
        var ids = (CAT.image_usage || []).map(function (item) { return item.id; });
        return value && ids.indexOf(value) === -1;
    }

    function customImagePlanHasAiSignal() {
        return imageStrategyCandidates().length > 0 || !!recId("image_ai_path");
    }

    function needsGeneratedImagesForUsage(value) {
        return value === "ai" || (usesCustomImagePlanValue(value) && customImagePlanHasAiSignal());
    }

    function imageStrategySelectedIndex() {
        var spec = imageStrategySpec();
        var idx = spec.selected || 0;
        return Math.min(idx, Math.max(imageStrategyCandidates().length - 1, 0));
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
        // Tier-1 anchor: its value seeds the body-size band, type character, page
        // density, and the re-derived Tier-2 page-count recommendation. Non-PPT
        // canvases carry no PowerPoint pt semantics, so the axis does not apply.
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
            function () { return STATE.visual_style; }, function (v) { STATE.visual_style = v; },
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
    // Replaced when the typography section mounts; the canvas section calls it so
    // the body-size hint tracks the chosen canvas height.
    var refreshBodySizeHint = function () {};
    // Replaced when the typography section mounts; body-size / delivery changes
    // call it so the per-role size overrides the user hasn't pinned re-derive.
    var refreshSizeInputs = function () {};

    // Per-role size slots the user can edit directly (parallel to color roles).
    // Defaults derive from `body` via mid-band ramp ratios (strategist.md §g);
    // values follow body's unit (pt on PPT canvases, px otherwise).
    var SIZE_ROLES = ["title", "subtitle", "annotation"];
    var SIZE_RATIO = { title: 1.75, subtitle: 1.35, annotation: 0.78 };
    function deriveSize(role, bodyVal) {
        return Math.round((bodyVal || 0) * (SIZE_RATIO[role] || 1));
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

    // PPT canvases (16:9 / 4:3) carry the pt design language + pt→px conversion;
    // social / print canvases have no PowerPoint pt semantics and stay in px.
    function isPptCanvas(canvasVal) {
        var dim = null;
        (CAT.canvas || []).forEach(function (o) { if (o.id === canvasVal) dim = o.dim; });
        var raw = String(dim || canvasVal || "");
        var id = String(canvasVal || "").toLowerCase();
        return id === "ppt169" || id === "ppt43" ||
            /1280\s*[×xX*]\s*720/.test(raw) ||
            /1024\s*[×xX*]\s*768/.test(raw);
    }

    // PPT confirmation pt band + default per delivery purpose (see strategist.md §g).
    // The confirmed pt is converted to px (×4/3) before any spec is written.
    function deliveryPtBand(purposeId) {
        if (purposeId === "text") return { lo: 14, hi: 18, def: 16 };
        if (purposeId === "presentation") return { lo: 22, hi: 28, def: 24 };
        return { lo: 18, hi: 22, def: 20 }; // balanced — the default
    }

    function defaultBodySizeForCanvas(canvasVal, purposeId) {
        if (isPptCanvas(canvasVal)) return deliveryPtBand(purposeId).def;
        var h = canvasHeight(canvasVal);
        if (!h) return 40;
        var band = bodySizeRatioBand(canvasVal);
        return Math.round(h * (band.lo + band.hi) / 2);
    }

    function roundSize(value) {
        return Math.round(value * 100) / 100;
    }

    function ptToPx(value) {
        return roundSize(value * 4 / 3);
    }

    function normalizeTypographyForSubmit(payload) {
        if (!payload.typography || typeof payload.typography !== "object") return;
        var typ = payload.typography;
        var ppt = isPptCanvas(payload.canvas);
        var body = parseFloat(typ.body_size);
        if (!isFinite(body)) {
            // Cleared / invalid body field — fall back so role sizes never submit
            // against an empty anchor, and (on PPT) so the pt→px branch still runs
            // instead of leaking pt-valued role sizes through as px.
            body = defaultBodySizeForCanvas(payload.canvas, payload.delivery_purpose);
            typ.body_size = body;
        }
        if (ppt && isFinite(body)) {
            typ.body_size_pt = roundSize(body);
            typ.body_size = ptToPx(body);
            typ.body_size_unit = "px";
            typ.body_size_source_unit = "pt";
            if (typ.sizes && typeof typ.sizes === "object") {
                var sizesPt = {};
                var sizesPx = {};
                Object.keys(typ.sizes).forEach(function (role) {
                    var raw = parseFloat(typ.sizes[role]);
                    if (!isFinite(raw)) return;
                    sizesPt[role] = roundSize(raw);
                    sizesPx[role] = ptToPx(raw);
                });
                typ.sizes_pt = sizesPt;
                typ.sizes = sizesPx;
            }
            return;
        }
        if (isFinite(body)) {
            typ.body_size = roundSize(body);
            typ.body_size_unit = "px";
        }
        if (typ.sizes && typeof typ.sizes === "object") {
            Object.keys(typ.sizes).forEach(function (role) {
                var raw = parseFloat(typ.sizes[role]);
                if (isFinite(raw)) typ.sizes[role] = roundSize(raw);
            });
        }
        delete typ.body_size_pt;
        delete typ.sizes_pt;
        delete payload.delivery_purpose;
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
            function () { return STATE.icons; }, function (v) { STATE.icons = v; }, { allowCustom: true });
        host.appendChild(sec);
    }

    function previewFontStack(primary, fallback) {
        if (!primary) return fallback || "";
        if (!fallback) return primary;
        return primary + ", " + fallback;
    }

    function fontSample(box, slot, css) {
        var line = el("div", "font-sample-line");
        var cjk = el("span", "fs-cjk", slot.sample_cjk || t("sample_cjk"));
        var lat = el("span", "fs-latin", slot.sample_latin || t("sample_latin"));
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
            if (c.body_size) meta += "  ·  " + t("font_body_size") + ":" + c.body_size + (isPptCanvas(STATE.canvas) ? "pt" : "px");
            top.appendChild(el("span", "font-card-meta", meta));
            card.appendChild(top);
            var hbox = el("div", "font-sample-heading-box"); fontSample(hbox, head, head.css); card.appendChild(hbox);
            var bbox = el("div", "font-sample-body-box"); fontSample(bbox, body, body.css); card.appendChild(bbox);
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
        // re-derives if ignored. PPT canvases speak pt (range by delivery
        // purpose); non-PPT canvases speak px (≈% of canvas height).
        refreshBodySizeHint = function () {
            var txt = t("font_body_size_hint");
            var lo, hi;
            if (isPptCanvas(STATE.canvas)) {
                var pb = deliveryPtBand(STATE.delivery_purpose);
                lo = pb.lo; hi = pb.hi;
                txt += " " + t("body_size_hint_pt")
                    .replace("{lo}", pb.lo).replace("{hi}", pb.hi).replace("{def}", pb.def);
            } else {
                var h = canvasHeight(STATE.canvas);
                var band = bodySizeRatioBand(STATE.canvas);
                if (h) {
                    lo = Math.round(h * band.lo); hi = Math.round(h * band.hi);
                    txt += " " + t("body_size_hint_canvas")
                        .replace("{lo}", lo).replace("{hi}", hi);
                }
            }
            // Flag (hint only — never auto-corrected) a value outside the range,
            // e.g. a pt number kept after switching to a px canvas, so a cross-unit
            // switch is visible instead of silently submitting a mis-unit size.
            var cur = parseFloat(STATE.typography && STATE.typography.body_size);
            if (isFinite(cur) && isFinite(lo) && isFinite(hi) && (cur < lo || cur > hi)) {
                txt += " " + t("body_size_hint_oor");
            }
            sizeHint.textContent = txt;
        };
        refreshBodySizeHint();
        sizeField.appendChild(sizeRow);

        // Delivery purpose is a Tier-1 anchor confirmed inside renderAudience (§c) —
        // it is set before this Tier-2 section exists, so its value drives the
        // body-size hint here via STATE.delivery_purpose (preserved across the
        // single-session transition). The control itself no longer lives here.
        sec.appendChild(sizeField);

        // Per-role size override (parallel to color's per-role HEX override): the
        // ramp derives title / subtitle / annotation from body, but the user may
        // set each explicitly. Values follow body's unit (pt on PPT, px else).
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
                (isPptCanvas(STATE.canvas) ? deliveryPtBand(STATE.delivery_purpose).def : 40);
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

    // Combined color + typography preview — not a ninth confirmation, just a
    // live "overall impression" of the two style choices made above. Kept
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
        var chip = el("div", "sp-chip");
        var chipDot = el("span", "sp-chip-dot");
        var chipLabel = el("span", "sp-chip-label");
        chip.appendChild(chipDot); chip.appendChild(chipLabel);
        card.appendChild(textcol); card.appendChild(chip);
        wrap.appendChild(card);
        host.appendChild(wrap);
        // Pin the strip just under the sticky topbar so it stays visible while
        // the user scrolls through the color / icon / typography sections.
        var topbar = document.getElementById("topbar");
        if (topbar) wrap.style.top = topbar.offsetHeight + "px";

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
            // body_size is pt on PPT canvases (×4/3 → px) and px elsewhere.
            var rawSize = parseFloat(typ.body_size) || (isPptCanvas(STATE.canvas) ? 20 : 18);
            var bodyPx = Math.max(12, Math.min(34,
                isPptCanvas(STATE.canvas) ? rawSize * 4 / 3 : rawSize));
            var headStack = previewFontStack(head.cjk, head.css);
            var headLatStack = previewFontStack(head.latin, head.css);
            var bodyStack = previewFontStack(body.cjk, body.css);
            var bodyLatStack = previewFontStack(body.latin, body.css);

            card.style.background = bg;
            titleCjk.textContent = head.sample_cjk || t("sample_cjk");
            titleLat.textContent = head.sample_latin || t("sample_latin");
            title.style.color = pri;
            title.style.fontSize = Math.round(bodyPx * 1.7) + "px";
            titleCjk.style.fontFamily = headStack || "";
            titleLat.style.fontFamily = headLatStack || "";
            // CJK and Latin previewed with their own stacks (mirrors the title
            // and the per-card font samples) so each script's font is visible.
            bodyCjk.textContent = body.sample_cjk || t("sample_cjk");
            bodyLat.textContent = body.sample_latin || t("sample_latin");
            bodyWrap.style.color = txt;
            bodyWrap.style.fontSize = bodyPx + "px";
            bodyCjk.style.fontFamily = bodyStack || "";
            bodyLat.style.fontFamily = bodyLatStack || "";
            accentBar.style.background = acc;
            chip.style.background = sbg;
            chipDot.style.background = sacc;
            chipLabel.textContent = t("role_secondary_bg");
            chipLabel.style.color = txt;
        }
        refreshStylePreview = paint;
        paint();
    }

    function renderImages(host) {
        var sec = section(8, "sec_images");
        var sub = el("div", "subfield");
        sub.appendChild(el("div", "subfield-label", t("image_ai_path")));
        var strategySub = el("div", "subfield image-strategy-subfield");
        strategySub.appendChild(el("div", "subfield-label", t("image_strategy")));
        var strategyGrid = el("div", "font-grid");
        var strategyCands = imageStrategyCandidates();
        function usesCustomImagePlan() {
            return usesCustomImagePlanValue(STATE.image_usage);
        }
        function needsGeneratedImages() {
            return needsGeneratedImagesForUsage(STATE.image_usage);
        }
        function refreshAiControls() {
            var needsAiPath = needsGeneratedImages();
            sub.style.display = needsAiPath ? "block" : "none";
            strategySub.style.display = needsAiPath ? "block" : "none";
        }
        function selectImageStrategy(idx) {
            var c = strategyCands[idx] || {};
            STATE.image_strategy = {
                name: localized(c, "name") || c.name || "",
                rendering: c.rendering || "",
                palette: c.palette || "",
                visual: localized(c, "visual") || "",
                color: localized(c, "color") || "",
                mood: localized(c, "mood") || ""
            };
            strategyGrid.querySelectorAll(".font-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
        }
        strategyCands.forEach(function (c, idx) {
            var card = el("div", "font-card");
            var top = el("div", "font-card-head");
            top.appendChild(el("span", "font-card-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            var meta = [];
            if (c.rendering) meta.push(t("image_strategy_rendering") + ":" + c.rendering);
            if (c.palette) meta.push(t("image_strategy_palette") + ":" + c.palette);
            if (meta.length) top.appendChild(el("span", "font-card-meta", meta.join("  ·  ")));
            card.appendChild(top);
            [
                ["image_strategy_visual", localized(c, "visual")],
                ["image_strategy_color", localized(c, "color")],
                ["image_strategy_mood", localized(c, "mood")]
            ].forEach(function (row) {
                if (row[1]) card.appendChild(el("div", "color-note", t(row[0]) + "：" + row[1]));
            });
            card.addEventListener("click", function () { selectImageStrategy(idx); });
            strategyGrid.appendChild(card);
        });
        if (!strategyCands.length) strategyGrid.appendChild(el("div", "toggle-desc", t("image_strategy_empty")));
        strategySub.appendChild(strategyGrid);
        enumField(sec, CAT.image_usage, recOrFirst("image_usage", CAT.image_usage),
            function () { return STATE.image_usage; },
            function (v) {
                STATE.image_usage = v;
                refreshAiControls();
            },
            {
                allowCustom: true,
                customSentinel: "custom",
                customInvalidValues: ["custom"],
                inputClass: "image-usage-custom-input",
                placeholder: LANG === "zh"
                    ? "例如：封面用 AI 生成，产品页用用户素材，行业页用网络来源"
                    : "e.g. AI cover + user product assets + web industry images"
            });
        enumField(sub, CAT.image_ai_path, recOrFirst("image_ai_path", CAT.image_ai_path),
            function () { return STATE.image_ai_path; }, function (v) { STATE.image_ai_path = v; });
        sec.appendChild(sub);
        sec.appendChild(strategySub);
        if (strategyCands.length) selectImageStrategy(imageStrategySelectedIndex());
        refreshAiControls();
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

    // Stage of the two-tier confirm flow: 1 = anchors, 2 = re-derived realization,
    // "all" = legacy single-pass (recommendations.json carried no `tier`).
    var STAGE = 1;

    function renderForTier(tier) {
        var host = document.getElementById("sections");
        host.innerHTML = "";
        _secCounter = 0;
        // Detach the previous preview's repaint closures before the sections
        // re-render: color/typography auto-select would otherwise call them and
        // write to now-detached nodes until renderStylePreview remounts them.
        refreshStylePreview = function () {};
        refreshBodySizeHint = function () {};
        refreshSizeInputs = function () {};
        if (tier === 1) {
            // Anchors — decided first; Tier 2 is re-derived from these.
            // Delivery purpose rides inside renderAudience (§c key info).
            renderCanvas(host);
            renderAudience(host);
            renderStyle(host);
        } else {
            // Tier 2 (realization) or single-pass: page count + visual treatment.
            // Single-pass also shows the anchors up front on the same page.
            if (tier === "all") {
                renderCanvas(host);
                renderAudience(host);
                renderStyle(host);
            }
            renderPages(host);
            // Group the preview with the three sections it reflects so its sticky
            // scope ends when typography scrolls past — it does not linger over the
            // image / mode / refine sections below.
            var styleGroup = el("div", "style-group");
            renderStylePreview(styleGroup);
            renderColor(styleGroup);
            renderIcons(styleGroup);
            renderTypography(styleGroup);
            host.appendChild(styleGroup);
            renderImages(host);
            renderMode(host);
            renderRefine(host);
        }
        updateActionBar(tier);
    }

    function renderAll() { renderForTier(STAGE); }

    function updateActionBar(tier) {
        var btn = document.getElementById("btn-confirm");
        btn.disabled = false;
        // Tier 1 advances to the re-derived Tier 2; Tier 2 / single-pass confirm.
        btn.textContent = (tier === 1) ? t("btn_next") : t("btn_confirm");
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

    function initTier1State() {
        STATE.canvas = pick("canvas", CAT.canvas);
        STATE.audience = (REC.audience && REC.audience.value) || "";
        STATE.content_divergence = (REC.content_divergence && REC.content_divergence.value) || "";  // free text; blank = balanced default
        STATE.mode = pick("mode", CAT.modes);
        STATE.visual_style = pick("visual_style", CAT.visual_styles);
        // Delivery purpose drives the PPT confirmation pt baseline; default balanced
        // (not the catalog-first id) when the Strategist did not recommend one.
        STATE.delivery_purpose = recId("delivery_purpose") || "balanced";
    }

    // Tier-2 fields are (re-)read from the recommendations. At boot they come from
    // whatever recommendations.json carried; after a tier-1 confirm enterTier2()
    // calls this again with the re-derived candidates. Tier-1 STATE is preserved
    // across the single-session transition — this never resets the anchors.
    function initTier2State() {
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

        STATE.image_usage = pick("image_usage", CAT.image_usage);
        STATE.image_ai_path = pick("image_ai_path", CAT.image_ai_path);

        STATE.generation_mode = pick("generation_mode", CAT.generation_mode);
        STATE.refine_spec = !!((REC.refine_spec && REC.refine_spec.value) || (REC.recommend && REC.recommend.refine_spec));
        // Guarantee a body baseline even when a candidate omitted body_size, on
        // any canvas (PPT → pt default by purpose, non-PPT → px from canvas height),
        // so role sizes never derive from an empty anchor.
        if (STATE.typography && !STATE.typography.body_size) {
            STATE.typography.body_size = defaultBodySizeForCanvas(STATE.canvas, STATE.delivery_purpose);
        }
    }

    function initState() {
        initTier1State();
        initTier2State();
    }

    // ---- confirm + close -------------------------------------------------
    function showConfirmedOverlay() {
        var ov = document.getElementById("confirmed-overlay");
        ov.querySelector(".cf-title").textContent = t("confirmed_title");
        ov.querySelector(".cf-hint").textContent = t("confirmed_hint");
        ov.style.display = "flex";
    }

    // ---- tier-1 submit + re-derive transition ---------------------------
    function submitTier1() {
        var btn = document.getElementById("btn-confirm");
        // Anchors only — the page stays open; the AI re-derives Tier 2 and the
        // same browser session renders it (STATE is preserved across the poll).
        var payload = {
            stage: "tier1",
            canvas: STATE.canvas,
            audience: STATE.audience,
            content_divergence: STATE.content_divergence,
            mode: STATE.mode,
            visual_style: STATE.visual_style
        };
        // Delivery purpose is PPT-only and rendered only on PPT canvases (§c).
        // On a non-PPT canvas the control is never shown, so STATE holds an unseen
        // default — do NOT write it as a confirmed anchor, or it would steer the
        // Tier-2 page-count / density re-derivation behind the user's back. (The
        // final submit drops it for non-PPT the same way, via normalizeTypographyForSubmit.)
        if (isPptCanvas(STATE.canvas)) {
            payload.delivery_purpose = STATE.delivery_purpose;
        }
        btn.disabled = true;
        fetch("/api/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(function (r) {
            if (!r.ok) throw new Error("tier1 failed");
            showDeriving();
            pollForTier2();
        }).catch(function () {
            btn.disabled = false;
            document.getElementById("confirm-status").textContent = t("error_retry");
        });
    }

    function showDeriving() {
        document.getElementById("sections").style.display = "none";
        document.getElementById("actionbar").style.display = "none";
        var l = document.getElementById("loading");
        l.textContent = t("deriving");
        l.style.display = "block";
    }

    // Poll the recommendations endpoint (no-store) until the AI overwrites it with
    // the re-derived Tier 2, then render Tier 2 in the same session.
    function pollForTier2() {
        fetch("/api/recommendations", { cache: "no-store" })
            .then(function (r) { if (!r.ok) throw new Error("poll failed"); return r.json(); })
            .then(function (data) {
                if (data && data.tier === 2) { enterTier2(data); }
                else { setTimeout(pollForTier2, 1200); }
            })
            .catch(function () { setTimeout(pollForTier2, 1500); });
    }

    function enterTier2(data) {
        REC = data;
        initTier2State();   // re-read realization fields; tier-1 STATE preserved
        STAGE = 2;
        document.getElementById("loading").style.display = "none";
        document.getElementById("sections").style.display = "block";
        document.getElementById("actionbar").style.display = "flex";
        document.getElementById("confirm-status").textContent = "";
        renderForTier(2);
    }

    function confirm() {
        var btn = document.getElementById("btn-confirm");
        var payload = JSON.parse(JSON.stringify(STATE));
        normalizeTypographyForSubmit(payload);
        payload.stage = "final";
        var customImagePlan = usesCustomImagePlanValue(payload.image_usage);
        if (payload.image_usage === "custom" || (customImagePlan && !String(payload.image_usage).trim())) {
            document.getElementById("confirm-status").textContent = t("image_usage_custom_required");
            var customImageInput = document.querySelector(".image-usage-custom-input");
            if (customImageInput) customImageInput.focus();
            return;
        }
        if (customImagePlan) payload.image_usage = String(payload.image_usage).trim();
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

    function boot() {
        applyStaticTranslations();
        var toggleBtn = document.getElementById("btn-lang-toggle");
        refreshLangToggle(toggleBtn);
        toggleBtn.addEventListener("click", function () {
            LANG = (LANG === "zh") ? "en" : "zh";
            try { window.localStorage.setItem("ppt_lang", LANG); } catch (e) { /* ignore */ }
            applyStaticTranslations();
            refreshLangToggle(toggleBtn);
            if (REC && CAT) renderAll();   // STATE persists → selections preserved
        });
        document.getElementById("btn-confirm").addEventListener("click", function () {
            if (STAGE === 1) { submitTier1(); } else { confirm(); }
        });

        Promise.all([
            loadCatalogs(),
            fetch("/api/recommendations").then(function (r) { if (!r.ok) throw new Error("load failed"); return r.json(); })
        ]).then(function (res) {
            CAT = res[0];
            REC = res[1];
            if (REC.lang === "zh" || REC.lang === "en") {
                var hasStored = false;
                try { hasStored = !!window.localStorage.getItem("ppt_lang"); } catch (e) { /* ignore */ }
                if (!hasStored) { LANG = REC.lang; applyStaticTranslations(); refreshLangToggle(toggleBtn); }
            }
            initState();
            // tier 1 / 2 from the recommendations; absent → legacy single-pass.
            STAGE = (REC.tier === 1) ? 1 : (REC.tier === 2 ? 2 : "all");
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
