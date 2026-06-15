/* PPT Master - Eight Confirmations UI
 * Finite/enumerable fields (canvas, mode, visual style, icons, image usage,
 * AI source, formula policy, generation mode) list ALL options from
 * /static/catalogs.json with the AI's recommendation marked. Open/generative
 * fields (color, typography, generated-image style) show a few AI candidates. Open fields also expose
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
            custom_typography: "Custom typography",
            custom_typography_placeholder: "Type your font plan, e.g. Heading: Georgia + KaiTi; Body: Microsoft YaHei + Arial…",
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
            custom_typography: "自定义字体方案",
            custom_typography_placeholder: "输入字体方案，如：标题用楷体；正文用微软雅黑…",
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

    function section(num, titleKey, noteText) {
        var sec = el("div", "section");
        var head = el("div", "section-head");
        head.appendChild(el("span", "section-num", String(num)));
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
            var chip = el("div", "chip");
            chip.appendChild(el("span", "chip-text", label));
            if (o.id === recommendedId) {
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

    function imageStrategySelectedIndex() {
        var spec = imageStrategySpec();
        var idx = spec.selected || 0;
        return Math.min(idx, Math.max(imageStrategyCandidates().length - 1, 0));
    }

    // ---- section renderers ----------------------------------------------
    function renderCanvas(host) {
        var sec = section(1, "sec_canvas");
        enumField(sec, CAT.canvas, recOrFirst("canvas", CAT.canvas),
            function () { return STATE.canvas; }, function (v) { STATE.canvas = v; }, { allowCustom: true });
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
            function () { return STATE.visual_style; }, function (v) { STATE.visual_style = v; }, { allowCustom: true });
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

    function renderColor(host) {
        var cands = (REC.color && REC.color.candidates) || [];
        var sec = section(5, "sec_color");
        var grid = el("div", "color-grid");
        var hexInputs = {};

        function applyHexInputs(pal) {
            PALETTE_ROLES.forEach(function (role) { if (hexInputs[role]) hexInputs[role].value = pal[role] || ""; });
        }
        function selectCard(idx) {
            var c = cands[idx] || {};
            STATE.color = { name: c.name || "", palette: Object.assign({}, normPalette(c)) };
            grid.querySelectorAll(".color-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
            applyHexInputs(STATE.color.palette);
        }

        cands.forEach(function (c, idx) {
            var pal = normPalette(c);
            var card = el("div", "color-card");
            var sw = el("div", "swatches");
            PALETTE_ROLES.forEach(function (role) {
                if (!pal[role]) return;
                var col = el("div", "swatch-col");
                var s = el("div", "swatch"); s.style.background = pal[role];
                col.appendChild(s); col.appendChild(el("div", "swatch-role", t("role_" + role)));
                sw.appendChild(col);
            });
            card.appendChild(sw);
            card.appendChild(el("div", "color-name", localized(c, "name") || (t("option_prefix") + " " + (idx + 1))));
            if (localized(c, "note")) card.appendChild(el("div", "color-note", localized(c, "note")));
            card.addEventListener("click", function () { selectCard(idx); });
            grid.appendChild(card);
        });
        sec.appendChild(grid);

        var override = el("div", "hex-override");
        override.appendChild(el("div", "subfield-label", t("hex_override")));
        var row = el("div", "hex-row");
        PALETTE_ROLES.forEach(function (role) {
            var wrap = el("div", "hex-cell");
            wrap.appendChild(el("div", "hex-cell-label", t("role_" + role)));
            var inp = document.createElement("input");
            inp.type = "text"; inp.placeholder = "#";
            inp.addEventListener("input", function () {
                if (!STATE.color) STATE.color = { name: "custom", palette: {} };
                if (!STATE.color.palette) STATE.color.palette = {};
                STATE.color.palette[role] = inp.value;
            });
            hexInputs[role] = inp; wrap.appendChild(inp); row.appendChild(wrap);
        });
        override.appendChild(row);
        sec.appendChild(override);
        host.appendChild(sec);

        var selIdx = -1;
        if (STATE.color && STATE.color.name) cands.forEach(function (c, i) { if (c.name === STATE.color.name) selIdx = i; });
        if (selIdx >= 0) selectCard(selIdx);
        else applyHexInputs((STATE.color && STATE.color.palette) || {});
    }

    function renderIcons(host) {
        var sec = section(6, "sec_icons");
        enumField(sec, CAT.icons, recOrFirst("icons", CAT.icons),
            function () { return STATE.icons; }, function (v) { STATE.icons = v; }, { allowCustom: true });
        host.appendChild(sec);
    }

    function fontSample(box, slot, css) {
        var line = el("div", "font-sample-line");
        var cjk = el("span", "fs-cjk", slot.sample_cjk || t("sample_cjk"));
        var lat = el("span", "fs-latin", slot.sample_latin || t("sample_latin"));
        if (css) { cjk.style.fontFamily = css; lat.style.fontFamily = css; }
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

        function selectFont(idx) {
            var c = normTypography(cands[idx] || {});
            STATE.typography = {
                name: c.name || "",
                heading: c.heading || {},
                body: c.body || {},
                body_size: c.body_size || (STATE.typography && STATE.typography.body_size) || ""
            };
            if (sizeInput) sizeInput.value = STATE.typography.body_size || "";
            customInput.style.display = "none";
            grid.querySelectorAll(".font-card").forEach(function (card, i) { card.classList.toggle("selected", i === idx); });
        }

        function selectCustomTypography() {
            STATE.typography = {
                name: "custom",
                custom: customInput.value || "",
                heading: {},
                body: {},
                body_size: (STATE.typography && STATE.typography.body_size) || ""
            };
            grid.querySelectorAll(".font-card").forEach(function (card) { card.classList.remove("selected"); });
            customCard.classList.add("selected");
            customInput.style.display = "block";
            customInput.focus();
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
        sizeInput.placeholder = "18 / 24";
        sizeInput.addEventListener("input", function () {
            if (!STATE.typography) STATE.typography = { name: "", heading: {}, body: {} };
            STATE.typography.body_size = sizeInput.value;
        });
        sizeRow.appendChild(sizeInput);
        sizeRow.appendChild(el("div", "toggle-desc", t("font_body_size_hint")));
        sizeField.appendChild(sizeRow);
        sec.appendChild(sizeField);

        var subfp = el("div", "subfield");
        subfp.appendChild(el("div", "subfield-label", t("formula_policy")));
        enumField(subfp, CAT.formula_policy, recOrFirst("formula_policy", CAT.formula_policy),
            function () { return STATE.formula_policy; }, function (v) { STATE.formula_policy = v; });
        sec.appendChild(subfp);
        host.appendChild(sec);

        var selIdx = -1;
        if (STATE.typography && STATE.typography.name) cands.forEach(function (c, i) { if (c.name === STATE.typography.name) selIdx = i; });
        if (selIdx >= 0) selectFont(selIdx);
        else if (STATE.typography && STATE.typography.name === "custom") {
            customInput.value = STATE.typography.custom || "";
            customCard.classList.add("selected");
            customInput.style.display = "block";
        }
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
            var ids = (CAT.image_usage || []).map(function (item) { return item.id; });
            return STATE.image_usage && ids.indexOf(STATE.image_usage) === -1;
        }
        function needsGeneratedImages() {
            return STATE.image_usage === "ai" || usesCustomImagePlan();
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

    function renderAll() {
        var host = document.getElementById("sections");
        host.innerHTML = "";
        renderCanvas(host);
        renderPages(host);
        renderAudience(host);
        renderStyle(host);
        renderColor(host);
        renderIcons(host);
        renderTypography(host);
        renderImages(host);
        renderMode(host);
        renderRefine(host);
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

    function initState() {
        STATE.canvas = pick("canvas", CAT.canvas);
        STATE.page_count = (REC.page_count && REC.page_count.value != null) ? String(REC.page_count.value) : "";
        STATE.audience = (REC.audience && REC.audience.value) || "";
        STATE.mode = pick("mode", CAT.modes);
        STATE.visual_style = pick("visual_style", CAT.visual_styles);

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
            body_size: t0.body_size || typographyBodySize(REC.typography)
        };
        STATE.formula_policy = pick("formula_policy", CAT.formula_policy);

        STATE.image_usage = pick("image_usage", CAT.image_usage);
        STATE.image_ai_path = pick("image_ai_path", CAT.image_ai_path);

        STATE.generation_mode = pick("generation_mode", CAT.generation_mode);
        STATE.refine_spec = !!((REC.refine_spec && REC.refine_spec.value) || (REC.recommend && REC.recommend.refine_spec));
    }

    // ---- confirm + close -------------------------------------------------
    function showConfirmedOverlay() {
        var ov = document.getElementById("confirmed-overlay");
        ov.querySelector(".cf-title").textContent = t("confirmed_title");
        ov.querySelector(".cf-hint").textContent = t("confirmed_hint");
        ov.style.display = "flex";
    }

    function confirm() {
        var btn = document.getElementById("btn-confirm");
        var payload = Object.assign({}, STATE);
        var imageUsageIds = (CAT.image_usage || []).map(function (item) { return item.id; });
        var customImagePlan = payload.image_usage && imageUsageIds.indexOf(payload.image_usage) === -1;
        if (payload.image_usage === "custom" || (customImagePlan && !String(payload.image_usage).trim())) {
            document.getElementById("confirm-status").textContent = t("image_usage_custom_required");
            var customImageInput = document.querySelector(".image-usage-custom-input");
            if (customImageInput) customImageInput.focus();
            return;
        }
        if (customImagePlan) payload.image_usage = String(payload.image_usage).trim();
        if (payload.image_usage !== "ai" && !customImagePlan) {
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
        document.getElementById("btn-confirm").addEventListener("click", confirm);

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
