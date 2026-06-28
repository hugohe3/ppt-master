/* ============================================================
   PPT Master - SVG Editor  |  app.js
   Vanilla JS, IIFE pattern
   ============================================================ */
(function () {
    "use strict";

    // ---- i18n -------------------------------------------------------
    var MESSAGES = {
        en: {
            page_title: "PPT Master - Live Preview",
            panel_slides: "Slides",
            panel_annotations: "Annotations",
            panel_edit_annotate: "Edit / Annotate",
            placeholder_select_slide: "Select a slide on the left to begin",
            label_selected_element: "Selected element",
            empty_selected_element: "Click an element on the slide to select it",
            btn_select_group: "Select parent group",
            label_batch_edit: "Batch edit",
            label_group_edit: "Group edit",
            section_geometry: "Geometry",
            section_style: "Style",
            section_text_style: "Text",
            section_raw_attrs: "Raw attributes",
            label_edit_instruction: "Edit instruction",
            pending_none: "No pending changes",
            pending_summary: "{edits} direct edit(s), {annotations} annotation page(s) pending",
            pending_pages: "Pages: {pages}",
            quick_align: "Align / move",
            quick_resize: "Resize",
            quick_replace_image: "Replace image",
            quick_copy: "Revise copy",
            quick_relayout: "Relayout area",
            placeholder_annotation: "Describe how the AI should modify this element...",
            placeholder_annotation_multi: "Describe how to modify all {count} elements...",
            btn_add_annotation: "Add annotation",
            label_annotations_on_slide: "Annotations on this slide",
            btn_submit_annotations: "Apply changes",
            btn_exit_preview: "Exit preview",
            modal_submit: "Submit",
            modal_cancel: "Cancel",
            empty_waiting_slides: "Waiting for generated slides...",
            empty_no_slides: "No slides found",
            placeholder_live_ready: "Live preview is ready. Generated slides will appear here.",
            placeholder_slide_writing: "Slide is still being written. Waiting for the next refresh...",
            empty_annotations: "No annotations yet",
            tooltip_remove_annotation: "Remove annotation",
            multi_selected: "{count} elements selected",
            multi_mixed: "mixed",
            err_load_slides: "Failed to load slides: ",
            err_load_slide: "Failed to load slide: ",
            err_add_annotation: "Failed to add annotation: ",
            err_remove_annotation: "Failed to remove annotation: ",
            err_save: "Save failed: ",
            err_edit: "Edit failed: ",
            label_direct_edit: "Object attributes (pending until Apply changes)",
            prop_multiline_hint: "Multi-line — select a single line (tspan) to edit text",
            edit_saved_hint: "Change staged. Click Apply changes to write it to svg_output.",
            btn_undo: "Undo",
            undo_done: "Reverted last staged edit",
            undo_empty: "No staged edit to undo",
            overlap_caption: "Overlapping here — pick one",
            err_empty_svg: "Slide loaded but the canvas is empty. The SVG may be malformed or missing a root <svg> element.",
            warn_icon_inline: "{count} icon(s) failed to render: {names}",
            warn_svg_no_dims: "SVG is missing width/height attributes. Please ask the AI to strictly follow shared-standards.md §4 and include width & height in the SVG root element.",
            warn_matrix_transform: "This geometry edit is stored as a transform matrix. Preview is exact; PPTX export depends on matrix-aware conversion.",
            modal_matrix_transform_note: "\n\nNote: at least one staged geometry edit uses a transform matrix. Re-export with the current PPTX exporter so the matrix is applied.",
            slide_error_tooltip: "Failed to parse this slide: ",
            reload_banner: "This slide was updated on disk. Click to reload.",
            modal_confirm_submit: "Apply staged direct edits and AI annotations to disk?\n\nThe preview service will keep running. Click Exit preview when you want to stop it.",
            modal_success_submit: "Changes saved to svg_output.\n\nThe preview service is still running.",
            modal_success_direct_only: "Changes saved to svg_output.\n\nDirect edits are now in the SVG source. Return to the chat and ask to re-export when you want a refreshed PPTX. The preview service is still running.",
            modal_success_annotations_only: "Annotations saved to svg_output.\n\nReturn to the chat and ask to apply annotations when you want AI to interpret them. The preview service is still running.",
            modal_success_mixed: "Direct edits and annotations saved to svg_output.\n\nReturn to the chat to apply AI-needed annotations, then re-export the PPTX when ready. The preview service is still running.",
            modal_confirm_exit: "Exit preview and stop the local server?\n\nUnapplied edits and annotations will be discarded.",
            modal_success_exit: "Preview stopped.\n\nYou can close this tab and return to the chat.",
            modal_stopping: "Stopping preview server...",
            lang_toggle_title: "Switch language",
            nav_first: "First slide (Home)",
            nav_prev: "Previous slide (←)",
            nav_next: "Next slide (→)",
            nav_last: "Last slide (End)",
            nav_counter: "{current} / {total}",
            nav_empty: "— / —"
        },
        zh: {
            page_title: "PPT Master - 实时预览",
            panel_slides: "幻灯片",
            panel_annotations: "标注",
            panel_edit_annotate: "编辑 / 标注",
            placeholder_select_slide: "在左侧选择一张幻灯片开始",
            label_selected_element: "已选元素",
            empty_selected_element: "点击幻灯片中的元素进行选择",
            btn_select_group: "选择父级组",
            label_batch_edit: "批量编辑",
            label_group_edit: "组编辑",
            section_geometry: "几何",
            section_style: "样式",
            section_text_style: "文本",
            section_raw_attrs: "原始属性",
            label_edit_instruction: "修改说明",
            pending_none: "没有待应用修改",
            pending_summary: "{edits} 条直接修改、{annotations} 个页面有 AI 标注待应用",
            pending_pages: "页面：{pages}",
            quick_align: "对齐/移动",
            quick_resize: "调整大小",
            quick_replace_image: "换图",
            quick_copy: "改文案",
            quick_relayout: "重排此区域",
            placeholder_annotation: "描述希望 AI 如何修改该元素……",
            placeholder_annotation_multi: "描述希望如何修改所选 {count} 个元素……",
            btn_add_annotation: "添加标注",
            label_annotations_on_slide: "本页标注",
            btn_submit_annotations: "应用修改",
            btn_exit_preview: "退出预览",
            modal_submit: "提交",
            modal_cancel: "取消",
            empty_waiting_slides: "正在等待生成幻灯片……",
            empty_no_slides: "未找到幻灯片",
            placeholder_live_ready: "实时预览已就绪,生成的幻灯片会在这里出现。",
            placeholder_slide_writing: "幻灯片仍在写入,等待下次刷新……",
            empty_annotations: "暂无标注",
            tooltip_remove_annotation: "删除标注",
            multi_selected: "已选 {count} 个元素",
            multi_mixed: "混合",
            err_load_slides: "加载幻灯片失败:",
            err_load_slide: "加载幻灯片失败:",
            err_add_annotation: "添加标注失败:",
            err_remove_annotation: "删除标注失败:",
            err_save: "保存失败:",
            err_edit: "编辑失败:",
            label_direct_edit: "对象属性(点击应用修改后写入)",
            prop_multiline_hint: "多行文本——选中单行(tspan)编辑文字",
            edit_saved_hint: "修改已暂存。点击“应用修改”后写入 svg_output。",
            btn_undo: "撤销",
            undo_done: "已撤销上一条暂存修改",
            undo_empty: "没有可撤销的暂存修改",
            overlap_caption: "此处重叠元素——点击选择",
            err_empty_svg: "幻灯片已加载但画布为空。SVG 可能损坏或缺少根 <svg> 元素。",
            warn_icon_inline: "{count} 个图标渲染失败:{names}",
            warn_svg_no_dims: "SVG 缺少 width/height 属性，预览可能异常。请让 AI 严格遵守 shared-standards.md §4 规范，在 SVG 根元素中补全 width 和 height。",
            warn_matrix_transform: "本次几何修改会以 transform matrix 保存。预览是准确的；PPTX 导出需要使用支持 matrix 的当前导出器。",
            modal_matrix_transform_note: "\n\n提示：至少有一条暂存几何修改使用了 transform matrix。请用当前 PPTX 导出器重新导出，确保 matrix 被应用。",
            slide_error_tooltip: "该幻灯片解析失败:",
            reload_banner: "当前页已在磁盘上更新,点此重新加载。",
            modal_confirm_submit: "确认将暂存的直接修改和 AI 标注写入磁盘?\n\n预览服务会继续运行。需要关闭时请点击退出预览。",
            modal_success_submit: "修改已保存到 svg_output。\n\n预览服务仍在运行。",
            modal_success_direct_only: "修改已保存到 svg_output。\n\n直接修改已经写入 SVG 源文件；需要刷新 PPTX 时，请回到对话窗口要求重新导出。预览服务仍在运行。",
            modal_success_annotations_only: "标注已保存到 svg_output。\n\n需要 AI 理解并执行这些标注时，请回到对话窗口要求应用标注。预览服务仍在运行。",
            modal_success_mixed: "直接修改和标注已保存到 svg_output。\n\n请回到对话窗口先应用需要 AI 判断的标注，确认后再重新导出 PPTX。预览服务仍在运行。",
            modal_confirm_exit: "退出预览并停止本地服务?\n\n未应用的属性修改和标注将被丢弃。",
            modal_success_exit: "预览已停止。\n\n可以关闭本标签页并回到对话窗口。",
            modal_stopping: "正在停止预览服务……",
            lang_toggle_title: "切换语言",
            nav_first: "第一页 (Home)",
            nav_prev: "上一页 (←)",
            nav_next: "下一页 (→)",
            nav_last: "末页 (End)",
            nav_counter: "{current} / {total}",
            nav_empty: "— / —"
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

    function t(key, params) {
        var dict = MESSAGES[LANG] || MESSAGES.en;
        var msg = dict[key];
        if (msg === undefined) msg = MESSAGES.en[key];
        if (msg === undefined) return key;
        if (params) {
            Object.keys(params).forEach(function (p) {
                msg = msg.replace("{" + p + "}", params[p]);
            });
        }
        return msg;
    }

    function applyI18n() {
        document.documentElement.setAttribute("lang", LANG === "zh" ? "zh-CN" : "en");
        document.title = t("page_title");
        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            el.textContent = t(el.getAttribute("data-i18n"));
        });
        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
            el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
        });
        document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
            el.title = t(el.getAttribute("data-i18n-title"));
        });
        updateNavLabel();
    }

    function setLang(lang) {
        if (lang !== "zh" && lang !== "en") return;
        LANG = lang;
        try { window.localStorage.setItem("ppt_lang", lang); } catch (e) { /* ignore */ }
        applyI18n();
        var toggleBtn = document.getElementById("btn-lang-toggle");
        if (toggleBtn) {
            toggleBtn.textContent = lang === "zh" ? "EN" : "中";
            toggleBtn.title = t("lang_toggle_title");
        }
        // Re-render dynamic regions so they pick up the new language
        updateSelectionPanel();
        updateAnnotationList();
        updateUndoButton();
        updatePendingStatus();
        initAnnotationQuickActions();
        loadSlides();
    }

    // ---- DOM refs ---------------------------------------------------
    var slideListEl       = document.getElementById("slide-list");
    var svgPlaceholder    = document.getElementById("svg-placeholder");
    var svgContent        = document.getElementById("svg-content");
    var selectedElementEl = document.getElementById("selected-element");
    var annotationInput   = document.getElementById("annotation-input");
    var annotationQuickActions = document.getElementById("annotation-quick-actions");
    var annotationText    = document.getElementById("annotation-text");
    var btnAddAnnotation  = document.getElementById("btn-add-annotation");
    var annotationsEl     = document.getElementById("annotations");
    var btnUndo           = document.getElementById("btn-undo");
    var btnSave           = document.getElementById("btn-save");
    var btnExitPreview    = document.getElementById("btn-exit-preview");
    var modalOverlay      = document.getElementById("modal-overlay");
    var modalMessage      = document.getElementById("modal-message");
    var modalConfirm      = document.getElementById("modal-confirm");
    var modalCancel       = document.getElementById("modal-cancel");
    var elementPropsEl    = document.getElementById("element-props");
    var pendingStatusEl   = document.getElementById("pending-status");

    var navFirstBtn       = document.getElementById("nav-first");
    var navPrevBtn        = document.getElementById("nav-prev");
    var navNextBtn        = document.getElementById("nav-next");
    var navLastBtn        = document.getElementById("nav-last");
    var navCounterEl      = document.getElementById("nav-counter");
    var navNameEl         = document.getElementById("nav-name");

    // ---- State ------------------------------------------------------
    var currentSlide      = null;   // filename, e.g. "slide_01.svg"
    var slideNames        = [];     // ordered slide filenames for navigation
    var selectedElementIds = new Set(); // id attrs of selected SVG elements
    var slideAnnotations  = {};     // {element_id: annotation_text} for current slide
    var liveMode          = false;
    var slidePollTimer    = null;
    var pendingModalAction = "submit";
    var slideMtimes       = {};     // {name: mtime} — last-seen mtime for each slide
    var reloadBannerEl    = null;   // singleton banner element shown when currentSlide mtime drifts
    var editStackCount    = {};     // {name: staged edit count} — mirrors backend PENDING_EDITS
    var savedHintShown    = false;  // show the "staged edit" hint once per session
    var matrixHintShown   = false;  // show transform-matrix export hint once per session
    var matrixEditSlides  = {};     // {name: true} when a staged edit wrote transform=matrix(...)
    var annotationsDirty  = false;  // unsaved annotations added/removed this session
    var annotationEditSlides = {};  // {name: true} when annotations changed this session

    function pendingDirectEditCount() {
        return Object.keys(editStackCount).reduce(function (total, name) {
            return total + Math.max(0, editStackCount[name] || 0);
        }, 0);
    }

    function pendingDirectEditSlides() {
        return Object.keys(editStackCount).filter(function (name) {
            return (editStackCount[name] || 0) > 0;
        });
    }

    function pendingAnnotationSlides() {
        return Object.keys(annotationEditSlides).filter(function (name) {
            return !!annotationEditSlides[name];
        });
    }

    function pendingAnnotationChangeCount() {
        return pendingAnnotationSlides().length;
    }

    function pendingSlideNames() {
        var seen = {};
        pendingDirectEditSlides().concat(pendingAnnotationSlides()).forEach(function (name) {
            seen[name] = true;
        });
        return Object.keys(seen).sort();
    }

    function updatePendingStatus() {
        if (!pendingStatusEl) return;
        var edits = pendingDirectEditCount();
        var annotations = pendingAnnotationChangeCount();
        if (edits === 0 && annotations === 0) {
            pendingStatusEl.className = "pending-status empty";
            pendingStatusEl.textContent = t("pending_none");
            return;
        }
        var pages = pendingSlideNames();
        pendingStatusEl.className = "pending-status active";
        pendingStatusEl.innerHTML =
            '<div>' + escapeHtml(t("pending_summary", {
                edits: edits,
                annotations: annotations,
            })) + '</div>' +
            (pages.length ? '<div class="pending-pages">' + escapeHtml(t("pending_pages", {
                pages: pages.join(", "),
            })) + '</div>' : '');
    }

    function markAnnotationChanged(slide) {
        if (!slide) return;
        annotationEditSlides[slide] = true;
        annotationsDirty = true;
        updatePendingStatus();
    }

    function initAnnotationQuickActions() {
        if (!annotationQuickActions) return;
        var actions = [
            { key: "quick_align" },
            { key: "quick_resize" },
            { key: "quick_replace_image" },
            { key: "quick_copy" },
            { key: "quick_relayout" },
        ];
        annotationQuickActions.innerHTML = "";
        actions.forEach(function (action) {
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "annotation-quick-chip";
            btn.textContent = t(action.key);
            btn.addEventListener("click", function () {
                var label = t(action.key);
                var prefix = LANG === "zh" ? label + "：" : label + ": ";
                if (!annotationText.value.trim()) {
                    annotationText.value = prefix;
                } else if (annotationText.value.indexOf(prefix) === -1) {
                    annotationText.value = prefix + annotationText.value;
                }
                annotationText.focus();
                annotationText.selectionStart = annotationText.selectionEnd = annotationText.value.length;
            });
            annotationQuickActions.appendChild(btn);
        });
    }

    // Staged edits live in server memory until "Apply changes"; the server can
    // still idle-timeout or be killed and drop them. Warn before the tab leaves
    // so the user remembers to apply (browsers show their own generic prompt).
    function hasUnsavedWork() {
        if (annotationsDirty) return true;
        return Object.keys(editStackCount).some(function (k) {
            return editStackCount[k] > 0;
        });
    }
    window.addEventListener("beforeunload", function (e) {
        if (!hasUnsavedWork()) return undefined;
        e.preventDefault();
        e.returnValue = "";
        return "";
    });

    function currentSlideIndex() {
        if (!currentSlide) return -1;
        return slideNames.indexOf(currentSlide);
    }

    function gotoSlideIndex(idx) {
        if (idx < 0 || idx >= slideNames.length) return;
        var name = slideNames[idx];
        if (name === currentSlide) return;
        var item = slideListEl.querySelector('.slide-item[data-name="' + cssAttr(name) + '"]');
        selectSlide(name, item || undefined);
    }

    function cssAttr(value) {
        return String(value).replace(/"/g, '\\"');
    }

    function updateNavLabel() {
        if (!navCounterEl) return;
        var total = slideNames.length;
        if (total === 0 || !currentSlide) {
            navCounterEl.textContent = t("nav_empty");
            if (navNameEl) navNameEl.textContent = "";
        } else {
            var idx = currentSlideIndex();
            navCounterEl.textContent = t("nav_counter", { current: idx + 1, total: total });
            if (navNameEl) navNameEl.textContent = currentSlide;
        }
        var idx2 = currentSlideIndex();
        var hasCurrent = idx2 >= 0;
        if (navFirstBtn) navFirstBtn.disabled = !hasCurrent || idx2 === 0;
        if (navPrevBtn)  navPrevBtn.disabled  = !hasCurrent || idx2 <= 0;
        if (navNextBtn)  navNextBtn.disabled  = !hasCurrent || idx2 >= total - 1;
        if (navLastBtn)  navLastBtn.disabled  = !hasCurrent || idx2 >= total - 1;
    }

    // ================================================================
    //  1.  loadSlides  -- GET /api/slides
    // ================================================================
    function loadSlides() {
        return fetch("/api/slides")
            .then(function (res) { return res.json(); })
            .then(function (data) {
                slideListEl.innerHTML = "";
                var slides = data.slides || [];
                slideNames = slides.map(function (s) { return s.name; });

                if (slides.length === 0) {
                    var empty = document.createElement("div");
                    empty.className = "slide-list-empty";
                    empty.textContent = liveMode
                        ? t("empty_waiting_slides")
                        : t("empty_no_slides");
                    slideListEl.appendChild(empty);
                    if (!currentSlide) {
                        svgPlaceholder.style.display = "block";
                        svgPlaceholder.textContent = liveMode
                            ? t("placeholder_live_ready")
                            : t("empty_no_slides");
                        svgContent.style.display = "none";
                    }
                    updateNavLabel();
                    updatePendingStatus();
                    return;
                }

                var currentExists = false;
                var currentMtimeChanged = false;
                slides.forEach(function (s) {
                    if (s.name === currentSlide) {
                        currentExists = true;
                        // Compare against the mtime we recorded when we last rendered this slide.
                        var lastSeen = slideMtimes[s.name];
                        if (lastSeen !== undefined && s.mtime && s.mtime !== lastSeen) {
                            currentMtimeChanged = true;
                        }
                    }
                    // Track every slide's mtime for the next poll (only update non-current here;
                    // currentSlide's mtime is updated by selectSlide so we can detect drift).
                    if (s.name !== currentSlide && s.mtime !== undefined) {
                        slideMtimes[s.name] = s.mtime;
                    }

                    var item = document.createElement("div");
                    item.className = "slide-item" + (s.name === currentSlide ? " active" : "");
                    if (s.ok === false) {
                        item.className += " slide-error";
                        item.title = t("slide_error_tooltip") + (s.error || "");
                    }
                    item.setAttribute("data-name", s.name);

                    var nameSpan = document.createElement("span");
                    nameSpan.className = "slide-name";
                    nameSpan.textContent = s.name;
                    item.appendChild(nameSpan);

                    if (s.annotation_count > 0) {
                        var badge = document.createElement("span");
                        badge.className = "badge";
                        badge.textContent = s.annotation_count;
                        item.appendChild(badge);
                    }

                    item.addEventListener("click", function () {
                        selectSlide(s.name, item);
                    });
                    slideListEl.appendChild(item);
                });

                if (!currentSlide || !currentExists) {
                    selectSlide(slides[0].name);
                } else if (currentMtimeChanged) {
                    showReloadBanner(currentSlide);
                }
                updateNavLabel();
                updatePendingStatus();
            })
            .catch(function (err) {
                console.error("loadSlides:", err);
                showError(t("err_load_slides") + err.message);
            });
    }

    // ================================================================
    //  2.  selectSlide  -- GET /api/slide/{name}
    // ================================================================
    function selectSlide(name, el) {
        // Update active class in sidebar
        document.querySelectorAll(".slide-item").forEach(function (it) {
            it.classList.remove("active");
        });
        if (el) el.classList.add("active");

        currentSlide = name;
        selectedElementIds.clear();
        slideAnnotations = {};
        updateNavLabel();

        // Reset right panel and rubber band
        cancelRubberBand();
        clearSelection();

        // Selecting a slide implicitly dismisses any stale "page updated" banner.
        hideReloadBanner();

        // Remove any stale spec-violation banner from a previous load.
        var oldSpecBanner = document.getElementById("spec-banner");
        if (oldSpecBanner) oldSpecBanner.remove();

        fetch("/api/slide/" + encodeURIComponent(name))
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    console.error("selectSlide:", data.error);
                    showError(t("err_load_slide") + data.error);
                    if (liveMode) {
                        currentSlide = null;
                        svgPlaceholder.style.display = "block";
                        svgPlaceholder.textContent = t("placeholder_slide_writing");
                        svgContent.style.display = "none";
                    }
                    return;
                }
                // Render SVG
                svgPlaceholder.style.display = "none";
                svgContent.style.display = "block";
                svgContent.innerHTML = sanitizeSvg(data.content);

                // Empty-canvas guard: surface a clear error if the SVG parsed
                // to nothing renderable (issue #115's silent-blank scenario).
                var rootSvg = svgContent.querySelector("svg");
                // Spec observability: missing width/height → red banner only
                if (rootSvg && (!rootSvg.hasAttribute("width") || !rootSvg.hasAttribute("height"))) {
                    var specBanner = document.createElement("div");
                    specBanner.id = "spec-banner";
                    specBanner.style.cssText = "position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);"
                        + "background:#fee2e2;color:#b91c1c;border:2px solid #f87171;border-radius:8px;"
                        + "padding:24px 36px;font-size:16px;font-weight:bold;text-align:center;z-index:9999;"
                        + "width:420px;line-height:1.6;box-shadow:0 4px 12px rgba(0,0,0,0.15);";
                    specBanner.textContent = t("warn_svg_no_dims");
                    document.body.appendChild(specBanner);
                }
                var hasContent = false;
                if (rootSvg) {
                    var children = rootSvg.querySelectorAll("*");
                    for (var i = 0; i < children.length; i++) {
                        var ctag = children[i].tagName.toLowerCase();
                        if (ctag !== "defs" && ctag !== "style" && ctag !== "title" && ctag !== "desc") {
                            hasContent = true;
                            break;
                        }
                    }
                }
                if (!rootSvg || !hasContent) {
                    showError(t("err_empty_svg"));
                    svgPlaceholder.style.display = "block";
                    svgPlaceholder.textContent = t("err_empty_svg");
                    svgContent.style.display = "none";
                    return;
                }

                // Non-fatal warnings (e.g. icon inline failures): surface as a
                // single combined toast so users know why something looks off.
                if (data.warnings && data.warnings.length > 0) {
                    var names = data.warnings.map(function (w) {
                        return w.icon || "(unknown)";
                    }).join(", ");
                    showWarning(t("warn_icon_inline", {
                        count: data.warnings.length,
                        names: names,
                    }));
                }

                // Record the mtime so the next poll can detect on-disk drift.
                if (data.mtime !== undefined) {
                    slideMtimes[name] = data.mtime;
                }

                // Build annotations map from response
                (data.annotations || []).forEach(function (a) {
                    slideAnnotations[a.element_id] = a.annotation;
                });

                editStackCount[name] = data.undo_depth || 0;
                setupSvgInteraction();
                refreshAnnotationVisuals();
                updateAnnotationList();
                updateUndoButton();
                updatePendingStatus();
            })
            .catch(function (err) {
                console.error("selectSlide:", err);
                showError(t("err_load_slide") + err.message);
            });
    }

    // ================================================================
    //  3.  setupSvgInteraction
    // ================================================================
    var SKIP_TAGS = ["defs", "style", "title", "desc"];

    function setupSvgInteraction() {
        var svg = svgContent.querySelector("svg");
        if (!svg) return;

        // Visual class only — selectability is handled by the delegated handler below.
        // Skipping the per-element addEventListener brings listener-registration time
        // from O(n) to O(1), which matters on decks with hundreds of elements per slide.
        var allEls = svg.querySelectorAll("*");
        allEls.forEach(function (el) {
            var tag = el.tagName.toLowerCase();
            if (SKIP_TAGS.indexOf(tag) !== -1) return;
            if (el === svg) return;
            el.classList.add("svg-selectable");
        });

        svg.addEventListener("click", function (e) {
            // Skip the synthetic click that follows a rubber-band drag-release.
            if (suppressNextSvgClick) {
                suppressNextSvgClick = false;
                return;
            }
            var target = e.target;
            // Blank-area click on the svg root → clear selection.
            if (target === svg) {
                clearSelection();
                return;
            }
            // Ignore clicks bubbling out of non-interactive subtrees.
            if (target.closest && target.closest("defs, style, title, desc")) return;
            // Backend assign_temp_ids() guarantees every element has an id, so
            // closest("[id]") will always find a hit. The exclusion of `svg`
            // itself routes "click outside any real shape" to clearSelection.
            // Icon placeholders are expanded only for browser preview. If a
            // click lands on a generated child, edit the disk-backed data-icon
            // group instead of an inner preview-only node.
            var picked = e.altKey && target.closest
                ? target.closest("g[id]")
                : null;
            picked = picked || (target.closest && target.closest("[data-icon][id]")) ||
                target.closest("[id]");
            if (!picked || picked === svg) {
                clearSelection();
                return;
            }
            selectElement(picked, e.ctrlKey || e.metaKey);
        });
    }

    // ================================================================
    //  4.  selectElement
    // ================================================================
    function selectElement(elem, addToSelection) {
        var eid = elem.id;
        if (!eid) return;

        if (addToSelection) {
            // Ctrl+click: toggle this element
            if (selectedElementIds.has(eid)) {
                selectedElementIds.delete(eid);
                elem.classList.remove("svg-selected");
            } else {
                selectedElementIds.add(eid);
                elem.classList.add("svg-selected");
            }
        } else {
            // Normal click: clear others, select only this one
            selectedElementIds.forEach(function (id) {
                if (id !== eid) {
                    var old = svgContent.querySelector("#" + CSS.escape(id));
                    if (old) old.classList.remove("svg-selected");
                }
            });
            selectedElementIds.clear();
            selectedElementIds.add(eid);
            elem.classList.add("svg-selected");
        }

        updateSelectionPanel();
    }

    // ================================================================
    //  5.  clearSelection
    // ================================================================
    function clearSelection() {
        selectedElementIds.forEach(function (id) {
            var el = svgContent.querySelector("#" + CSS.escape(id));
            if (el) el.classList.remove("svg-selected");
        });
        selectedElementIds.clear();
        updateSelectionPanel();
    }

    function updateSelectionPanel() {
        var propsEl = elementPropsEl;
        var count = selectedElementIds.size;

        if (count === 0) {
            selectedElementEl.classList.add("empty");
            selectedElementEl.textContent = t("empty_selected_element");
            annotationInput.style.display = "none";
            annotationText.value = "";
            propsEl.style.display = "none";
            propsEl.innerHTML = "";
            return;
        }

        selectedElementEl.classList.remove("empty");
        propsEl.style.display = "block";

        if (count === 1) {
            var eid = selectedElementIds.values().next().value;
            var el = svgContent.querySelector("#" + CSS.escape(eid));
            if (el) {
                var tag = el.tagName.toLowerCase();
                selectedElementEl.innerHTML =
                    '<span class="el-tag">&lt;' + escapeHtml(tag) + '&gt;</span>' +
                    '<span class="el-id">' + escapeHtml(eid) + '</span>';
                propsEl.innerHTML = renderEditableProps(el);
                attachPropEditors(el);
            }
        } else {
            selectedElementEl.innerHTML =
                '<span class="multi-count">' + escapeHtml(t("multi_selected", { count: count })) + '</span>';
            propsEl.innerHTML = renderMultiSelectSummary(Array.from(selectedElementIds));
            attachMultiSelectionEditors(Array.from(selectedElementIds));
        }

        annotationInput.style.display = "block";
        annotationText.placeholder = count > 1
            ? t("placeholder_annotation_multi", { count: count })
            : t("placeholder_annotation");
        annotationText.value = count === 1
            ? (slideAnnotations[selectedElementIds.values().next().value] || "")
            : "";
    }

    // ---- Rubber band selection ----
    var rubberBandEl = null;
    var rubberBandStart = null;
    var rubberBandUsed = false;
    var suppressNextSvgClick = false;
    var RUBBER_BAND_THRESHOLD = 5;

    // ---- Drag-to-move (direct geometry edit on the canvas) ----
    // Pressing on an already-selected element drags the whole selection. Frames
    // only update the preview; one staged edit per element is written on release,
    // reusing attrsForMove + stageEditRequest (and backend coalescing).
    var dragStart = null;       // {x, y} screen coords at mousedown on a selection
    var dragMoved = false;      // crossed the move threshold this gesture
    var dragEls = [];           // top-level selected elements being moved
    var dragStartAttrs = {};    // {id: startGeometryAttrs} for drift-free preview

    function hitSelectedAncestor(target) {
        // Walk up from the pressed node to the first element already in the
        // selection, so a press on a selected shape (or its inner preview
        // children) starts a drag regardless of how it was selected.
        var svg = svgContent.querySelector("svg");
        var node = target;
        while (node && node !== svg && node.nodeType === 1) {
            if (node.id && selectedElementIds.has(node.id)) return node;
            node = node.parentNode;
        }
        return null;
    }

    function screenDeltaToLocal(el, dxScreen, dyScreen) {
        // Map a screen-pixel delta into the coordinate space computeRenderBox /
        // attrsForMove use for THIS element (its getCTM() output space). Using the
        // element's own getCTM ∘ getScreenCTM⁻¹ is robust to how a browser splits
        // the viewBox scale between getCTM and getScreenCTM, and naturally accounts
        // for each element's own group transform (correct under multi-select).
        var sctm = el.getScreenCTM ? el.getScreenCTM() : null;
        var ctm = el.getCTM ? el.getCTM() : null;
        if (!sctm || !ctm) return { x: dxScreen, y: dyScreen };
        try {
            var n = ctm.multiply(sctm.inverse());  // linear part: screen → local delta
            var lx = n.a * dxScreen + n.c * dyScreen;
            var ly = n.b * dxScreen + n.d * dyScreen;
            // Singular CTM → SVGMatrix.inverse() throws, DOMMatrix yields NaN.
            // Either way, fall back to the raw delta rather than wedge the drag.
            if (!isFinite(lx) || !isFinite(ly)) return { x: dxScreen, y: dyScreen };
            return { x: lx, y: ly };
        } catch (err) {
            return { x: dxScreen, y: dyScreen };
        }
    }

    function beginDrag() {
        dragEls = topLevelSelectedElements(Array.from(selectedElementIds));
        dragStartAttrs = {};
        dragEls.forEach(function (el) {
            // attrsForMove(el, 0, 0) returns the element's current geometry in the
            // exact attribute shape a move writes (x/y, cx/cy, … or transform);
            // restoring it before each frame keeps the preview drift-free.
            try { dragStartAttrs[el.id] = attrsForMove(el, 0, 0); }
            catch (err) { dragStartAttrs[el.id] = null; }
        });
        document.body.classList.add("svg-dragging");
    }

    function applyAttrSnapshot(el, sa) {
        if (!sa) return;
        applyElementAttrs(el, sa);
    }

    function applyElementAttrs(el, attrs) {
        if (localName(el) === "g" && el.hasAttribute("data-icon") &&
                attrs.x !== undefined && attrs.y !== undefined) {
            // The preview expands <use data-icon> into a <g>, but disk still owns
            // the source <use>. Keep the browser geometry in sync while the staged
            // edit writes x/y back to the real placeholder instead of persisting a
            // transform.
            var m = ownMatrix(el);
            el.setAttribute("transform", "matrix(" + [
                formatCoord(m.a), formatCoord(m.b), formatCoord(m.c),
                formatCoord(m.d), formatCoord(parseFloat(attrs.x)),
                formatCoord(parseFloat(attrs.y))
            ].join(",") + ")");
            el.setAttribute("data-use-x", attrs.x);
            el.setAttribute("data-use-y", attrs.y);
        }
        Object.keys(attrs).forEach(function (k) {
            if (localName(el) === "g" && el.hasAttribute("data-icon") &&
                    (k === "x" || k === "y" || k === "transform")) return;
            if (attrs[k] === null || attrs[k] === undefined) el.removeAttribute(k);
            else el.setAttribute(k, attrs[k]);
        });
    }

    function localName(el) {
        return el && el.tagName ? el.tagName.toLowerCase() : "";
    }

    function markCommittedAttrs(el, attrs) {
        if (attrs && attrs.transform === null &&
                localName(el) === "g" && el.hasAttribute("data-icon")) {
            el.removeAttribute("data-use-has-transform");
        }
    }

    function payloadForCurrentElementState(el, payload) {
        if (!payload || !payload.attrs || payload.attrs.transform !== null ||
                localName(el) !== "g" || !el.hasAttribute("data-icon") ||
                el.hasAttribute("data-use-has-transform")) {
            return payload;
        }
        var attrs = Object.assign({}, payload.attrs);
        delete attrs.transform;
        return Object.assign({}, payload, { attrs: attrs });
    }

    function restoreDragStart(el) {
        applyAttrSnapshot(el, dragStartAttrs[el.id]);
    }

    function applyMoveLocal(el, dxScreen, dyScreen) {
        // Each element converts the shared screen delta into its own local space,
        // so a selection spanning differently-transformed groups still tracks the
        // pointer. Restore-then-apply keeps every frame relative to the start.
        restoreDragStart(el);
        var d = screenDeltaToLocal(el, dxScreen, dyScreen);
        var attrs;
        try { attrs = attrsForMove(el, d.x, d.y); }
        catch (err) { attrs = null; }
        if (!attrs) return null;
        applyElementAttrs(el, attrs);
        return attrs;
    }

    function updateDragPreview(dxScreen, dyScreen) {
        dragEls.forEach(function (el) { applyMoveLocal(el, dxScreen, dyScreen); });
        if (dragEls.length === 1) refreshGeoInputs(dragEls[0], elementPropsEl);
    }

    function commitDrag(dxScreen, dyScreen) {
        var single = dragEls.length === 1;
        dragEls.forEach(function (el) {
            // Capture the pre-drag snapshot in the closure: endDrag() clears
            // dragStartAttrs synchronously after this call, before the staging
            // promise can reject, so the rollback can't rely on the global.
            var startAttrs = dragStartAttrs[el.id];
            var attrs = applyMoveLocal(el, dxScreen, dyScreen);
            if (!attrs) return;
            var payload = payloadForMovedElement(el, attrs);
            stageEditRequest(el.id, payload).then(function () {
                if (payload.attrs) markCommittedAttrs(el, payload.attrs);
                if (payload.promote_tspan) {
                    var promoted = promoteTspanDom(el, payload.promote_tspan);
                    if (promoted && single) refreshGeoInputs(promoted, elementPropsEl);
                }
            }).catch(function (err) {
                // Optimistic preview already moved the element; roll it back so the
                // canvas never shows a move the server never staged.
                applyAttrSnapshot(el, startAttrs);
                if (single) refreshGeoInputs(el, elementPropsEl);
                showError(t("err_edit") + err.message);
            });
        });
    }

    function endDrag() {
        dragStart = null;
        dragMoved = false;
        dragEls = [];
        dragStartAttrs = {};
        document.body.classList.remove("svg-dragging");
    }

    // Per-element nudge staging is serialized: a held arrow key fires many
    // keydowns, each sending an *absolute* position. Without ordering, the
    // unlocked backend could coalesce them out of order and leave the staged
    // value behind the on-screen one. So at most one nudge stage per element is
    // in flight; extra keypresses only update the preview and the queued target,
    // and the next send reads the current DOM position (= the latest).
    var nudgeFlight = {};   // key -> bool: a nudge stage is in flight
    var nudgeQueued = {};   // key -> {el, single, slide, attrs}: latest target awaiting send
    var nudgeLastOk = {};   // key -> attrs: last position the server confirmed

    function nudgeKey(slide, el) { return slide + "|" + el.id; }

    function sendNudge(key, el, single, slide, payload) {
        if (!payload) return;
        payload = payloadForCurrentElementState(el, payload);
        nudgeFlight[key] = true;
        stageEditRequest(el.id, payload, slide).then(function () {
            if (payload.attrs) nudgeLastOk[key] = payload.attrs;
            if (payload.attrs) markCommittedAttrs(el, payload.attrs);
            nudgeFlight[key] = false;
            var q = nudgeQueued[key];
            if (q) { delete nudgeQueued[key]; sendNudge(key, q.el, q.single, q.slide, q.payload); }
        }).catch(function (err) {
            nudgeFlight[key] = false;
            delete nudgeQueued[key];
            // Re-sync the preview to the last confirmed position so it can't show
            // a move the server never staged (only meaningful on the live slide).
            if (payload.promote_tspan && el.__promotionRollback) {
                var restored = el.__promotionRollback();
                if (single && restored) refreshGeoInputs(restored, elementPropsEl);
            } else if (nudgeLastOk[key] && slide === currentSlide && el.isConnected) {
                applyAttrSnapshot(el, nudgeLastOk[key]);
                if (single) refreshGeoInputs(el, elementPropsEl);
            }
            showError(t("err_edit") + err.message);
        });
    }

    function stageNudge(el, single, slide, payload) {
        var key = nudgeKey(slide, el);
        if (nudgeFlight[key]) {
            nudgeQueued[key] = { el: el, single: single, slide: slide, payload: payload };
            return;
        }
        sendNudge(key, el, single, slide, payload);
    }

    function nudgeSelection(dxScreen, dyScreen) {
        // Keyboard arrow micro-move: same geometry path as drag. The DOM updates
        // immediately; staging is serialized per element (see sendNudge), and
        // consecutive same-direction nudges coalesce into one undo step.
        var els = topLevelSelectedElements(Array.from(selectedElementIds));
        if (els.length === 0) return;
        var slide = currentSlide;
        var single = els.length === 1;
        var lastSingleEl = null;
        els.forEach(function (el) {
            var key = nudgeKey(slide, el);
            if (!nudgeFlight[key] && !nudgeQueued[key]) {
                // Fresh burst: re-capture the pre-move baseline from the current
                // DOM, so a failed nudge rolls back to *this* burst's start rather
                // than a stale position left by an earlier drag/edit/undo.
                try { nudgeLastOk[key] = attrsForMove(el, 0, 0); }
                catch (err) { delete nudgeLastOk[key]; }
            }
            var d = screenDeltaToLocal(el, dxScreen, dyScreen);
            var attrs;
            try { attrs = attrsForMove(el, d.x, d.y); } catch (err) { attrs = null; }
            if (!attrs) return;
            applyElementAttrs(el, attrs);
            var payload = payloadForMovedElement(el, attrs);
            if (payload.promote_tspan) {
                el = promoteTspanDom(el, payload.promote_tspan) || el;
            }
            lastSingleEl = el;
            stageNudge(el, single, slide, payload);
        });
        if (single && lastSingleEl) refreshGeoInputs(lastSingleEl, elementPropsEl);
    }

    // ---- Overlap picker (right-click → list every selectable element here) ----
    // Left-click stays a fast "select the topmost" gesture; right-click is the
    // opt-in disambiguator for stacked elements, so it never pops on normal use.
    var overlapPickerEl = null;

    function collectSelectableAt(clientX, clientY) {
        var svg = svgContent.querySelector("svg");
        if (!svg || !document.elementsFromPoint) return [];
        var out = [];
        var seen = {};
        document.elementsFromPoint(clientX, clientY).forEach(function (node) {
            if (!svg.contains(node) || node === svg) return;
            if (node.closest && node.closest("defs, style, title, desc")) return;
            // Resolve to the disk-backed selectable entity, mirroring the click
            // handler: prefer an enclosing data-icon group, else nearest id.
            var picked = (node.closest && node.closest("[data-icon][id]")) ||
                         (node.closest && node.closest("[id]"));
            if (!picked || picked === svg || !picked.id || seen[picked.id]) return;
            seen[picked.id] = true;
            out.push(picked);
        });
        return out;  // top → bottom in paint order
    }

    function closeOverlapPicker() {
        if (!overlapPickerEl) return;
        var svg = svgContent.querySelector("svg");
        if (svg) {
            svg.querySelectorAll(".overlap-hover").forEach(function (e) {
                e.classList.remove("overlap-hover");
            });
        }
        overlapPickerEl.remove();
        overlapPickerEl = null;
    }

    function showOverlapPicker(clientX, clientY, candidates) {
        closeOverlapPicker();
        var menu = document.createElement("div");
        menu.id = "overlap-picker";
        var cap = document.createElement("div");
        cap.className = "overlap-caption";
        cap.textContent = t("overlap_caption");
        menu.appendChild(cap);
        candidates.forEach(function (el) {
            var item = document.createElement("div");
            item.className = "overlap-item";
            var tag = el.tagName.toLowerCase();
            var txt = (tag === "text" || tag === "tspan")
                ? (el.textContent || "").trim().slice(0, 28) : "";
            item.innerHTML = '<span class="overlap-tag">&lt;' + escapeHtml(tag) +
                '&gt;</span><span class="overlap-id">' + escapeHtml(el.id) + '</span>' +
                (txt ? '<span class="overlap-txt">' + escapeHtml(txt) + '</span>' : '');
            item.addEventListener("mouseenter", function () { el.classList.add("overlap-hover"); });
            item.addEventListener("mouseleave", function () { el.classList.remove("overlap-hover"); });
            item.addEventListener("click", function (ev) {
                ev.stopPropagation();
                selectElement(el, ev.ctrlKey || ev.metaKey);
                closeOverlapPicker();
            });
            menu.appendChild(item);
        });
        document.body.appendChild(menu);
        // Keep the menu inside the viewport.
        var x = Math.min(clientX, window.innerWidth - menu.offsetWidth - 8);
        var y = Math.min(clientY, window.innerHeight - menu.offsetHeight - 8);
        menu.style.left = Math.max(8, x) + "px";
        menu.style.top = Math.max(8, y) + "px";
        overlapPickerEl = menu;
    }

    function initRubberBand() {
        var overlay = document.getElementById("rubber-band-overlay");
        var container = document.getElementById("svg-container");

        container.addEventListener("mousedown", function (e) {
            // Only left mouse button
            if (e.button !== 0) return;

            // Pressing on an already-selected element arms a drag of the whole
            // selection instead of a rubber band. Selecting stays a separate
            // click, so the background is never dragged by accident.
            if (hitSelectedAncestor(e.target)) {
                dragStart = { x: e.clientX, y: e.clientY };
                dragMoved = false;
                return;
            }

            // Always start tracking — rubber band only activates when
            // mousemove exceeds the threshold. This allows clicking on any
            // element (including SVG background rects) to still trigger
            // the element's click handler for selection.
            rubberBandStart = { x: e.clientX, y: e.clientY };
            rubberBandUsed = false;
        });

        document.addEventListener("mousemove", function (e) {
            if (dragStart) {
                var ddx = e.clientX - dragStart.x;
                var ddy = e.clientY - dragStart.y;
                if (!dragMoved && Math.sqrt(ddx * ddx + ddy * ddy) < RUBBER_BAND_THRESHOLD) {
                    return;  // below threshold — still a click, let selection stand
                }
                if (!dragMoved) {
                    dragMoved = true;
                    beginDrag();
                }
                updateDragPreview(ddx, ddy);
                return;
            }
            if (!rubberBandStart) return;

            var dx = e.clientX - rubberBandStart.x;
            var dy = e.clientY - rubberBandStart.y;
            var dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < RUBBER_BAND_THRESHOLD) {
                return;
            }

            // Threshold exceeded — this is a drag, not a click
            if (!rubberBandUsed) {
                rubberBandUsed = true;
                overlay.classList.add("active");
            }

            if (!rubberBandEl) {
                rubberBandEl = document.createElement("div");
                rubberBandEl.id = "rubber-band";
                document.body.appendChild(rubberBandEl);
            }

            var x = Math.min(rubberBandStart.x, e.clientX);
            var y = Math.min(rubberBandStart.y, e.clientY);
            var w = Math.abs(dx);
            var h = Math.abs(dy);

            rubberBandEl.style.left = x + "px";
            rubberBandEl.style.top = y + "px";
            rubberBandEl.style.width = w + "px";
            rubberBandEl.style.height = h + "px";
        });

        document.addEventListener("mouseup", function (e) {
            if (dragStart) {
                if (dragMoved) {
                    commitDrag(e.clientX - dragStart.x, e.clientY - dragStart.y);
                    // Swallow the click that follows the drag-release so it does
                    // not re-trigger selection on the dropped element.
                    suppressNextSvgClick = true;
                    window.setTimeout(function () { suppressNextSvgClick = false; }, 50);
                }
                endDrag();
                return;
            }
            if (!rubberBandStart) return;

            overlay.classList.remove("active");

            var dx = e.clientX - rubberBandStart.x;
            var dy = e.clientY - rubberBandStart.y;
            var dist = Math.sqrt(dx * dx + dy * dy);

            if (rubberBandEl) {
                rubberBandEl.remove();
                rubberBandEl = null;
            }

            // Only process if drag was beyond threshold
            if (dist >= RUBBER_BAND_THRESHOLD) {
                var rect = {
                    left: Math.min(rubberBandStart.x, e.clientX),
                    top: Math.min(rubberBandStart.y, e.clientY),
                    right: Math.max(rubberBandStart.x, e.clientX),
                    bottom: Math.max(rubberBandStart.y, e.clientY)
                };

                if (!e.ctrlKey && !e.metaKey) {
                    clearSelection();
                }

                selectByRubberBand(rect);
                suppressNextSvgClick = true;
                window.setTimeout(function () {
                    suppressNextSvgClick = false;
                }, 50);
            } else {
                // Below threshold: treat as click on empty space
                if (!e.ctrlKey && !e.metaKey) {
                    clearSelection();
                }
            }

            rubberBandStart = null;
        });

        // Right-click → list every selectable element under the pointer, so
        // stacked/overlapping shapes can be reached without blind cycling.
        container.addEventListener("contextmenu", function (e) {
            var svg = svgContent.querySelector("svg");
            if (!svg) return;
            var cands = collectSelectableAt(e.clientX, e.clientY);
            if (cands.length === 0) return;            // nothing here → native menu
            e.preventDefault();
            if (cands.length === 1) { selectElement(cands[0], false); return; }
            showOverlapPicker(e.clientX, e.clientY, cands);
        });

        // Dismiss the picker on any press outside it (item clicks stop their own
        // propagation, so this never fires before a selection is made).
        document.addEventListener("mousedown", function (e) {
            if (overlapPickerEl && !overlapPickerEl.contains(e.target)) {
                closeOverlapPicker();
            }
        });
    }

    function cancelRubberBand() {
        rubberBandStart = null;
        if (rubberBandEl) {
            rubberBandEl.remove();
            rubberBandEl = null;
        }
        var ov = document.getElementById("rubber-band-overlay");
        if (ov) ov.classList.remove("active");
        suppressNextSvgClick = false;
        endDrag();
        closeOverlapPicker();
    }

    function selectByRubberBand(screenRect) {
        var svg = svgContent.querySelector("svg");
        if (!svg) return;

        var selectableEls = svg.querySelectorAll(".svg-selectable");
        selectableEls.forEach(function (el) {
            try {
                var bbox = el.getBBox();
                var ctm = el.getScreenCTM();
                if (!ctm) return;

                // Transform bbox corners to screen coordinates
                var corners = [
                    { x: bbox.x, y: bbox.y },
                    { x: bbox.x + bbox.width, y: bbox.y },
                    { x: bbox.x, y: bbox.y + bbox.height },
                    { x: bbox.x + bbox.width, y: bbox.y + bbox.height }
                ];

                var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                corners.forEach(function (c) {
                    var sx = c.x * ctm.a + c.y * ctm.c + ctm.e;
                    var sy = c.x * ctm.b + c.y * ctm.d + ctm.f;
                    if (sx < minX) minX = sx;
                    if (sy < minY) minY = sy;
                    if (sx > maxX) maxX = sx;
                    if (sy > maxY) maxY = sy;
                });

                // AABB intersection
                if (minX < screenRect.right && maxX > screenRect.left &&
                    minY < screenRect.bottom && maxY > screenRect.top) {
                    var eid = el.id;
                    if (eid) {
                        selectedElementIds.add(eid);
                        el.classList.add("svg-selected");
                    }
                }
            } catch (err) {
                // getBBox can throw for elements with no geometry
            }
        });

        updateSelectionPanel();
    }

    // ================================================================
    //  Keyboard shortcuts
    // ================================================================
    function initKeyboardShortcuts() {
        document.addEventListener("keydown", function (e) {
            // Ctrl+Z / Cmd+Z: drop the last staged edit. Let inputs/selects handle
            // their own native undo when focused.
            if ((e.ctrlKey || e.metaKey) && (e.key === "z" || e.key === "Z")) {
                var ae = document.activeElement;
                if (ae && (ae === annotationText || ae.tagName === "INPUT" ||
                           ae.tagName === "TEXTAREA" || ae.tagName === "SELECT")) {
                    return;
                }
                e.preventDefault();
                runUndo();
                return;
            }

            // Ctrl+A / Cmd+A: select all elements
            if ((e.ctrlKey || e.metaKey) && e.key === "a") {
                // Don't intercept if focus is in textarea
                if (document.activeElement === annotationText) return;

                e.preventDefault();
                var svg = svgContent.querySelector("svg");
                if (!svg) return;

                svg.querySelectorAll(".svg-selectable").forEach(function (el) {
                    var eid = el.id;
                    if (eid) {
                        selectedElementIds.add(eid);
                        el.classList.add("svg-selected");
                    }
                });
                updateSelectionPanel();
            }

            // Escape: close the overlap picker first if open, else clear selection.
            if (e.key === "Escape") {
                if (document.activeElement === annotationText) return;
                if (overlapPickerEl) { closeOverlapPicker(); return; }
                clearSelection();
            }

            // Slide navigation: ArrowLeft/Right + Home/End (skip while typing)
            if (document.activeElement === annotationText) return;
            if (e.ctrlKey || e.metaKey || e.altKey) return;

            // Arrow keys nudge the selection (1px, Shift = 10px) instead of
            // navigating slides whenever something is selected.
            if (selectedElementIds.size > 0 &&
                (e.key === "ArrowLeft" || e.key === "ArrowRight" ||
                 e.key === "ArrowUp" || e.key === "ArrowDown")) {
                e.preventDefault();
                var step = e.shiftKey ? 10 : 1;
                var nx = e.key === "ArrowLeft" ? -step : e.key === "ArrowRight" ? step : 0;
                var ny = e.key === "ArrowUp" ? -step : e.key === "ArrowDown" ? step : 0;
                nudgeSelection(nx, ny);
                return;
            }

            if (slideNames.length === 0) return;

            if (e.key === "ArrowLeft") {
                e.preventDefault();
                gotoSlideIndex(currentSlideIndex() - 1);
            } else if (e.key === "ArrowRight") {
                e.preventDefault();
                gotoSlideIndex(currentSlideIndex() + 1);
            } else if (e.key === "Home") {
                e.preventDefault();
                gotoSlideIndex(0);
            } else if (e.key === "End") {
                e.preventDefault();
                gotoSlideIndex(slideNames.length - 1);
            }
        });
    }

    function initSlideNav() {
        if (navFirstBtn) navFirstBtn.addEventListener("click", function () { gotoSlideIndex(0); });
        if (navPrevBtn)  navPrevBtn.addEventListener("click", function ()  { gotoSlideIndex(currentSlideIndex() - 1); });
        if (navNextBtn)  navNextBtn.addEventListener("click", function ()  { gotoSlideIndex(currentSlideIndex() + 1); });
        if (navLastBtn)  navLastBtn.addEventListener("click", function ()  { gotoSlideIndex(slideNames.length - 1); });
    }

    // ================================================================
    //  6.  Add annotation  -- POST /api/slide/{name}/annotate
    // ================================================================
    btnAddAnnotation.addEventListener("click", function () {
        if (!currentSlide || selectedElementIds.size === 0) return;

        var text = annotationText.value.trim();
        if (!text) return;

        var ids = Array.from(selectedElementIds);
        var promises = ids.map(function (eid) {
            return fetch("/api/slide/" + encodeURIComponent(currentSlide) + "/annotate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ element_id: eid, annotation: text })
            }).then(jsonOrThrow);
        });

        Promise.all(promises)
            .then(function () {
                ids.forEach(function (eid) {
                    slideAnnotations[eid] = text;
                });
                markAnnotationChanged(currentSlide);
                refreshAnnotationVisuals();
                updateAnnotationList();
                annotationText.value = "";
                loadSlides();
            })
            .catch(function (err) {
                console.error("addAnnotation:", err);
                showError(t("err_add_annotation") + err.message);
            });
    });

    // ================================================================
    //  7.  removeAnnotation  -- DELETE /api/slide/{name}/annotate/{id}
    // ================================================================
    function removeAnnotation(elementId) {
        if (!currentSlide) return;

        fetch("/api/slide/" + encodeURIComponent(currentSlide) + "/annotate/" + encodeURIComponent(elementId), {
            method: "DELETE"
        })
            .then(function (res) { return res.json(); })
            .then(function () {
                delete slideAnnotations[elementId];
                markAnnotationChanged(currentSlide);
                refreshAnnotationVisuals();
                updateAnnotationList();
                loadSlides();
            })
            .catch(function (err) {
                console.error("removeAnnotation:", err);
                showError(t("err_remove_annotation") + err.message);
            });
    }

    // ================================================================
    //  8.  refreshAnnotationVisuals
    // ================================================================
    function refreshAnnotationVisuals() {
        // Clear all annotated marks
        svgContent.querySelectorAll(".svg-annotated").forEach(function (el) {
            el.classList.remove("svg-annotated");
        });
        // Apply marks
        Object.keys(slideAnnotations).forEach(function (eid) {
            var el = svgContent.querySelector("#" + CSS.escape(eid));
            if (el) el.classList.add("svg-annotated");
        });
    }

    // ================================================================
    //  9.  updateAnnotationList
    // ================================================================
    function updateAnnotationList() {
        annotationsEl.innerHTML = "";

        var ids = Object.keys(slideAnnotations);
        if (ids.length === 0) {
            annotationsEl.innerHTML = '<div class="annotations-empty">' + escapeHtml(t("empty_annotations")) + '</div>';
            return;
        }

        ids.forEach(function (eid) {
            var item = document.createElement("div");
            item.className = "annotation-item";

            // Try to resolve tag from live SVG
            var tag = "";
            var el = svgContent.querySelector("#" + CSS.escape(eid));
            if (el) tag = el.tagName.toLowerCase();

            var header = document.createElement("div");
            header.className = "ann-header";

            var leftSpan = document.createElement("span");
            if (tag) {
                var tagSpan = document.createElement("span");
                tagSpan.className = "ann-tag";
                tagSpan.textContent = "<" + tag + ">";
                leftSpan.appendChild(tagSpan);
            }
            var idSpan = document.createElement("span");
            idSpan.className = "ann-id";
            idSpan.textContent = eid;
            leftSpan.appendChild(idSpan);

            header.appendChild(leftSpan);

            var removeBtn = document.createElement("button");
            removeBtn.className = "ann-remove";
            removeBtn.innerHTML = "&times;";
            removeBtn.title = t("tooltip_remove_annotation");
            removeBtn.addEventListener("click", function () {
                removeAnnotation(eid);
            });
            header.appendChild(removeBtn);

            item.appendChild(header);

            var textDiv = document.createElement("div");
            textDiv.className = "ann-text";
            textDiv.textContent = slideAnnotations[eid];
            item.appendChild(textDiv);

            annotationsEl.appendChild(item);
        });
    }

    // ================================================================
    // 10.  Save all  -- two-step: confirm then save
    // ================================================================
    btnSave.addEventListener("click", function () {
        pendingModalAction = "submit";
        modalMessage.textContent = t("modal_confirm_submit") +
            (hasPendingMatrixEdits() ? t("modal_matrix_transform_note") : "");
        modalConfirm.textContent = t("modal_submit");
        modalConfirm.style.display = "";
        modalCancel.style.display = "";
        modalOverlay.style.display = "flex";
    });

    btnExitPreview.addEventListener("click", function () {
        pendingModalAction = "exit";
        modalMessage.textContent = t("modal_confirm_exit");
        modalConfirm.textContent = t("btn_exit_preview");
        modalConfirm.style.display = "";
        modalCancel.style.display = "";
        modalOverlay.style.display = "flex";
    });

    modalConfirm.addEventListener("click", function () {
        if (pendingModalAction === "exit") {
            modalConfirm.style.display = "none";
            modalCancel.style.display = "none";
            modalMessage.textContent = t("modal_stopping");
            fetch("/api/shutdown", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reason: "exit-preview" })
            })
                .then(function () {
                    modalMessage.textContent = t("modal_success_exit");
                })
                .catch(function () {
                    modalMessage.textContent = t("modal_success_exit");
                });
            return;
        }

        // Step 2: save annotations. Service lifetime is controlled only by Exit preview.
        var hadDirectEdits = pendingDirectEditCount() > 0;
        var hadAnnotationChanges = pendingAnnotationChangeCount() > 0;
        modalConfirm.style.display = "none";
        modalCancel.style.display = "none";

        // Wait for any just-fired direct edits (drag/nudge) to land first, or
        // save-all could race ahead and leave their edits as a fresh pending set.
        drainDirectEdits()
            .then(function () { return fetch("/api/save-all", { method: "POST" }); })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    modalMessage.textContent = t("err_save") + data.error;
                } else {
                    if (hadDirectEdits && hadAnnotationChanges) {
                        modalMessage.textContent = t("modal_success_mixed");
                    } else if (hadDirectEdits) {
                        modalMessage.textContent = t("modal_success_direct_only");
                    } else if (hadAnnotationChanges) {
                        modalMessage.textContent = t("modal_success_annotations_only");
                    } else {
                        modalMessage.textContent = t("modal_success_submit");
                    }
                    editStackCount = {};
                    matrixEditSlides = {};
                    matrixHintShown = false;
                    savedHintShown = false;
                    annotationsDirty = false;
                    annotationEditSlides = {};
                    updateUndoButton();
                    updatePendingStatus();
                    var activeSlide = currentSlide;
                    loadSlides().then(function () {
                        if (activeSlide) {
                            var item = slideListEl.querySelector('.slide-item[data-name="' + cssAttr(activeSlide) + '"]');
                            selectSlide(activeSlide, item || undefined);
                        }
                    });
                }
            })
            .catch(function (err) {
                modalMessage.textContent = t("err_save") + err;
                modalConfirm.style.display = "";
                modalCancel.style.display = "";
            });
    });

    modalCancel.addEventListener("click", function () {
        modalConfirm.textContent = t("modal_submit");
        modalOverlay.style.display = "none";
    });

    // Close modal on overlay click
    modalOverlay.addEventListener("click", function (e) {
            if (e.target === modalOverlay) {
                modalConfirm.textContent = t("modal_submit");
                modalOverlay.style.display = "none";
            }
        });

    // ================================================================
    //  Utility
    // ================================================================
    function sanitizeSvg(svgString) {
        var doc = new DOMParser().parseFromString(svgString, "image/svg+xml");
        doc.querySelectorAll("script,foreignObject").forEach(function (el) { el.remove(); });
        doc.querySelectorAll("*").forEach(function (el) {
            Array.from(el.attributes).forEach(function (attr) {
                if (attr.name.indexOf("on") === 0) el.removeAttribute(attr.name);
                // Strip dangerous URI protocols from href/xlink:href
                if ((attr.name === "href" || attr.name === "xlink:href") &&
                    (/^\s*javascript\s*:/i.test(attr.value) ||
                     /^\s*data\s*:/i.test(attr.value))) {
                    el.removeAttribute(attr.name);
                }
            });
        });
        return new XMLSerializer().serializeToString(doc.documentElement);
    }

    function showError(msg) {
        var banner = document.createElement("div");
        banner.style.cssText = "position:fixed;top:0;left:0;right:0;padding:10px 16px;background:#ef4444;color:#fff;font-size:13px;text-align:center;z-index:999;cursor:pointer;";
        banner.textContent = msg;
        banner.onclick = function () { banner.remove(); };
        document.body.appendChild(banner);
        setTimeout(function () { banner.remove(); }, 5000);
    }

    function showWarning(msg) {
        // Amber, non-fatal counterpart to showError. Stacks below an existing
        // error banner because z-index is identical and DOM order wins.
        var banner = document.createElement("div");
        banner.style.cssText = "position:fixed;top:38px;left:0;right:0;padding:8px 16px;background:#f59e0b;color:#1f1300;font-size:12px;text-align:center;z-index:998;cursor:pointer;";
        banner.textContent = msg;
        banner.onclick = function () { banner.remove(); };
        document.body.appendChild(banner);
        setTimeout(function () { banner.remove(); }, 6000);
    }

    function showReloadBanner(name) {
        // Singleton: replace any prior banner so we never stack reloads.
        hideReloadBanner();
        var banner = document.createElement("div");
        banner.id = "reload-banner";
        banner.style.cssText = "position:fixed;top:0;left:0;right:0;padding:10px 16px;background:#2563eb;color:#fff;font-size:13px;text-align:center;z-index:1000;cursor:pointer;";
        banner.textContent = t("reload_banner");
        banner.onclick = function () {
            hideReloadBanner();
            // Re-fetch via selectSlide so all post-load logic (annotation merge,
            // warnings, mtime update) runs the same way as a manual click.
            var item = slideListEl.querySelector('.slide-item[data-name="' + cssAttr(name) + '"]');
            selectSlide(name, item || undefined);
        };
        document.body.appendChild(banner);
        reloadBannerEl = banner;
    }

    function hideReloadBanner() {
        if (reloadBannerEl) {
            reloadBannerEl.remove();
            reloadBannerEl = null;
        }
    }

    function escapeHtml(str) {
        var d = document.createElement("div");
        d.appendChild(document.createTextNode(str));
        return d.innerHTML;
    }

    function jsonOrThrow(res) {
        return res.json().then(function (data) {
            if (!res.ok || data.error) {
                throw new Error(data.error || ("Request failed with status " + res.status));
            }
            return data;
        });
    }

    function loadConfig() {
        return fetch("/api/config")
            .then(function (res) { return res.json(); })
            .then(function (data) {
                liveMode = !!data.live;
            })
            .catch(function () {
                liveMode = false;
            });
    }

    function startSlidePolling() {
        if (!liveMode || slidePollTimer) return;
        slidePollTimer = window.setInterval(function () {
            loadSlides();
        }, 2000);
    }

    // ---- Direct-edit undo + save hint --------------------------------
    function updateUndoButton() {
        if (!btnUndo) return;
        var n = (currentSlide && editStackCount[currentSlide]) || 0;
        btnUndo.disabled = n === 0;
        btnUndo.textContent = n > 0 ? (t("btn_undo") + " (" + n + ")") : t("btn_undo");
    }

    function runUndo() {
        if (!currentSlide || !editStackCount[currentSlide]) return;
        fetch("/api/slide/" + encodeURIComponent(currentSlide) + "/undo", { method: "POST" })
            .then(jsonOrThrow)
            .then(function (data) {
                if (data.status === "empty") {
                    editStackCount[currentSlide] = 0;
                    matrixEditSlides[currentSlide] = false;
                    updateUndoButton();
                    updatePendingStatus();
                    showWarning(t("undo_empty"));
                    return;
                }
                if (data.mtime !== undefined && data.mtime !== null) {
                    slideMtimes[currentSlide] = data.mtime;
                }
                // Reload the page so the canvas reflects the reverted SVG;
                // selectSlide refreshes editStackCount + the undo button.
                var item = slideListEl.querySelector('.slide-item[data-name="' + cssAttr(currentSlide) + '"]');
                selectSlide(currentSlide, item || undefined);
                updatePendingStatus();
                showWarning(t("undo_done"));
            })
            .catch(function (err) {
                showError(t("err_edit") + err.message);
            });
    }

    function maybeShowSavedHint() {
        if (savedHintShown) return;
        savedHintShown = true;
        showWarning(t("edit_saved_hint"));
    }

    function payloadHasMatrixTransform(payload) {
        var transform = payload && payload.attrs && payload.attrs.transform;
        return typeof transform === "string" && /^\s*matrix\s*\(/i.test(transform);
    }

    function hasPendingMatrixEdits() {
        return Object.keys(matrixEditSlides).some(function (name) {
            return !!matrixEditSlides[name];
        });
    }

    function markMatrixTransformEdit(slide) {
        matrixEditSlides[slide] = true;
        if (matrixHintShown) return;
        matrixHintShown = true;
        showWarning(t("warn_matrix_transform"));
    }

    // ================================================================
    //  Property extraction & rendering
    // ================================================================
    // Editable property panel for a single selected element: computed geometry,
    // text content where safe, and the element's own SVG attributes.
    function renderEditableProps(el) {
        var tag = localName(el);
        var isGroup = tag === "g";
        var html = '<div class="prop-caption">' +
            escapeHtml(isGroup ? t("label_group_edit") : t("label_direct_edit")) + '</div>';

        var parentGroup = nearestParentGroup(el);
        if (parentGroup && !isGroup) {
            html += '<table class="prop-table"><tr><td class="prop-key">group</td><td class="prop-val">' +
                '<button type="button" class="btn-select-group" data-group-id="' +
                escapeHtml(parentGroup.id) + '">' + escapeHtml(t("btn_select_group")) +
                '</button></td></tr></table>';
        }

        html += '<div class="prop-section">' + escapeHtml(t("section_geometry")) + '</div>';
        html += '<table class="prop-table">';
        // Geometry: position + size in render coords — editable, folded into
        // the element's transform matrix on commit (works for any element type).
        try {
            var rb = computeRenderBox(el);
            html += '<tr><td class="prop-key">position</td><td class="prop-val geo-cell">' +
                '<input type="number" class="prop-edit prop-edit-geo" data-geo="x" value="' + Math.round(rb.x) + '">' +
                '<input type="number" class="prop-edit prop-edit-geo" data-geo="y" value="' + Math.round(rb.y) + '">' +
                '</td></tr>';
            html += '<tr><td class="prop-key">size</td><td class="prop-val geo-cell">' +
                '<input type="number" class="prop-edit prop-edit-geo" data-geo="w" min="1" value="' + Math.round(rb.w) + '">' +
                '<input type="number" class="prop-edit prop-edit-geo" data-geo="h" min="1" value="' + Math.round(rb.h) + '">' +
                '</td></tr>';
        } catch (e) { /* no geometry */ }
        html += '</table>';

        var textStyleTargets = textStyleTargetsForSelection(el);

        // L1: text content + computed text styles. When a textbox/group is
        // selected, style controls target its descendant text leaves.
        if (tag === "text" || tag === "tspan" || textStyleTargets.length > 0) {
            html += '<div class="prop-section">' + escapeHtml(t("section_text_style")) + '</div>';
            html += '<table class="prop-table">';
            if ((tag === "text" || tag === "tspan") && el.querySelector("tspan")) {
                html += '<tr><td class="prop-key">content</td><td class="prop-val prop-note">' +
                    escapeHtml(t("prop_multiline_hint")) + '</td></tr>';
            } else if (tag === "text" || tag === "tspan") {
                html += '<tr><td class="prop-key">content</td><td class="prop-val">' +
                    '<textarea class="prop-edit prop-edit-content" rows="2">' +
                    escapeHtml(el.textContent || "") + '</textarea></td></tr>';
            }
            if (textStyleTargets.length > 0) {
                textStyleSpecs(textStyleTargets).forEach(function (spec) {
                    html += '<tr><td class="prop-key">' + escapeHtml(spec.key) + '</td><td class="prop-val">';
                    html += renderTextStyleControl(spec, textStyleTargets);
                    html += '</td></tr>';
                });
            }
            html += '</table>';
        }

        html += '<div class="prop-section">' + escapeHtml(t("section_raw_attrs")) + '</div>';
        html += '<table class="prop-table">';
        ownAttributeSpecs(el).forEach(function (spec) {
            html += '<tr><td class="prop-key">' + escapeHtml(spec.key) + '</td><td class="prop-val">';
            if (!spec.editable) {
                html += '<span class="prop-ro">' + escapeHtml(spec.value) + '</span>';
            } else {
                html += renderAttributeControl(spec);
            }
            html += '</td></tr>';
        });

        html += '</table>';
        return html;
    }

    function nearestParentGroup(el) {
        var node = el ? el.parentElement : null;
        while (node && node !== svgContent) {
            if (node.tagName && localName(node) === "g" && node.id) return node;
            node = node.parentElement;
        }
        return null;
    }

    function ownAttributeSpecs(el) {
        var specs = [];
        Array.from(el.attributes).forEach(function (attr) {
            var key = attr.name;
            if (key === "class" || key === "data-edit-target" || key === "data-edit-annotation") return;
            specs.push({
                key: key,
                value: attr.value,
                editable: isEditableAttributeName(key)
            });
        });
        return specs;
    }

    function isEditableAttributeName(key) {
        var k = String(key).toLowerCase();
        if (k === "id" || k === "class" || k === "href" || k === "xlink:href") return false;
        if (k.indexOf("on") === 0) return false;
        return /^[A-Za-z_][A-Za-z0-9_.:-]*$/.test(key);
    }

    function textStyleTargetsForSelection(el) {
        if (!el) return [];
        var tag = localName(el);
        if (tag === "tspan") return el.id ? [el] : [];
        if (tag === "text") return textStyleLeavesForText(el);

        var targets = [];
        el.querySelectorAll("text").forEach(function (textEl) {
            targets = targets.concat(textStyleLeavesForText(textEl));
        });
        return uniqueElements(targets);
    }

    function textStyleLeavesForText(textEl) {
        var tspans = Array.from(textEl.querySelectorAll("tspan")).filter(function (tspan) {
            return !!tspan.id;
        });
        if (tspans.length > 0) return tspans;
        return textEl.id ? [textEl] : [];
    }

    function uniqueElements(elements) {
        var seen = new Set();
        return elements.filter(function (el) {
            if (!el || !el.id || seen.has(el.id)) return false;
            seen.add(el.id);
            return true;
        });
    }

    function textStyleSpecs(targets) {
        return [
            { key: "fill", type: "color" },
            { key: "font-size", type: "text" },
            { key: "font-family", type: "text" },
            { key: "font-weight", type: "select",
              options: ["", "normal", "bold", "300", "400", "500", "600", "700", "800"] },
            { key: "text-anchor", type: "select", options: ["", "start", "middle", "end"] }
        ].map(function (spec) {
            var value = commonAttrValue(targets, spec.key);
            var copy = Object.assign({}, spec);
            copy.value = value === null ? "" : value;
            copy.mixed = value === null;
            return copy;
        });
    }

    function renderTextStyleControl(spec, targets) {
        var targetIds = encodeURIComponent(JSON.stringify(targets.map(function (el) { return el.id; })));
        var placeholder = spec.mixed ? t("multi_mixed") : "";
        if (spec.type === "color") {
            return '<input type="color" class="prop-edit prop-edit-text-style-color" data-key="' +
                escapeHtml(spec.key) + '" data-target-ids="' + targetIds +
                '" value="' + normalizeHexForPicker(spec.value) + '">' +
                '<input type="text" class="prop-edit prop-edit-text-style" data-key="' +
                escapeHtml(spec.key) + '" data-target-ids="' + targetIds +
                '" placeholder="' + escapeHtml(placeholder) +
                '" value="' + escapeHtml(spec.mixed ? "" : spec.value) + '">';
        }
        if (spec.type === "select") {
            var html = '<select class="prop-edit prop-edit-text-style" data-key="' +
                escapeHtml(spec.key) + '" data-target-ids="' + targetIds + '">';
            var hasValue = spec.options.indexOf(spec.value) !== -1;
            if (!spec.mixed && spec.value && !hasValue) {
                html += '<option value="' + escapeHtml(spec.value) + '" selected>' +
                    escapeHtml(spec.value) + '</option>';
            }
            spec.options.forEach(function (opt) {
                var label = opt || placeholder || "";
                var selected = !spec.mixed && spec.value === opt ? " selected" : "";
                html += '<option value="' + escapeHtml(opt) + '"' + selected + '>' +
                    escapeHtml(label) + '</option>';
            });
            html += '</select>';
            return html;
        }
        return '<input type="text" class="prop-edit prop-edit-text-style" data-key="' +
            escapeHtml(spec.key) + '" data-target-ids="' + targetIds +
            '" placeholder="' + escapeHtml(placeholder) +
            '" value="' + escapeHtml(spec.mixed ? "" : spec.value) + '">';
    }

    function isColorAttribute(key, value) {
        var k = String(key).toLowerCase();
        if (["fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"].indexOf(k) !== -1) {
            return isSafeColor(value);
        }
        return false;
    }

    function renderAttributeControl(spec) {
        if (isColorAttribute(spec.key, spec.value)) {
            return '<input type="color" class="prop-edit prop-edit-color" data-key="' +
                escapeHtml(spec.key) + '" value="' + normalizeHexForPicker(spec.value) + '">' +
                '<input type="text" class="prop-edit prop-edit-color-text" data-key="' +
                escapeHtml(spec.key) + '" value="' + escapeHtml(spec.value) + '">';
        }
        if (spec.value.length > 60 || spec.key === "d" || spec.key === "points" || spec.key === "style") {
            return '<textarea class="prop-edit prop-edit-attr-area" rows="2" data-key="' +
                escapeHtml(spec.key) + '">' + escapeHtml(spec.value) + '</textarea>';
        }
        return '<input type="text" class="prop-edit prop-edit-attr" data-key="' +
            escapeHtml(spec.key) + '" value="' + escapeHtml(spec.value) + '">';
    }

    // ---- Geometry (position/size) helpers ----------------------------
    // Edits fold into the element's own transform matrix so they apply
    // uniformly regardless of how the element is positioned (x/y, cx/cy, d…).

    function computeRenderBox(el) {
        // Local geometry bbox (excludes the element's OWN transform) ...
        var bbox = el.getBBox();
        // ... times the element CTM (includes own + ancestor transforms) =
        // the on-screen box in the svg root user space (= svg_output coords).
        var ctm = el.getCTM();
        if (!ctm) return { x: bbox.x, y: bbox.y, w: bbox.width, h: bbox.height };
        var corners = [
            { x: bbox.x, y: bbox.y },
            { x: bbox.x + bbox.width, y: bbox.y },
            { x: bbox.x, y: bbox.y + bbox.height },
            { x: bbox.x + bbox.width, y: bbox.y + bbox.height }
        ];
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        corners.forEach(function (p) {
            var sx = p.x * ctm.a + p.y * ctm.c + ctm.e;
            var sy = p.x * ctm.b + p.y * ctm.d + ctm.f;
            minX = Math.min(minX, sx); minY = Math.min(minY, sy);
            maxX = Math.max(maxX, sx); maxY = Math.max(maxY, sy);
        });
        return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }

    function ownMatrix(el) {
        var t = el.transform && el.transform.baseVal;
        if (t && t.numberOfItems) {
            var c = t.consolidate();
            if (c) {
                var m = c.matrix;
                return new DOMMatrix([m.a, m.b, m.c, m.d, m.e, m.f]);
            }
        }
        return new DOMMatrix();
    }

    function parentCTM(el) {
        // parent → svg-root user space; identity when parent is the outer <svg>.
        var p = el.parentNode;
        var pm = (p && p.getCTM) ? p.getCTM() : null;
        return pm ? new DOMMatrix([pm.a, pm.b, pm.c, pm.d, pm.e, pm.f]) : new DOMMatrix();
    }

    function matrixAfterMove(el, rb, nx, ny) {
        // Desired shift in root coords, mapped into parent space (linear part only).
        var pm = parentCTM(el);
        var rx = nx - rb.x, ry = ny - rb.y;
        var det = pm.a * pm.d - pm.b * pm.c || 1;
        var dpx = (pm.d * rx - pm.c * ry) / det;
        var dpy = (-pm.b * rx + pm.a * ry) / det;
        return new DOMMatrix().translate(dpx, dpy).multiply(ownMatrix(el));
    }

    function matrixAfterResize(el, rb, nw, nh) {
        var pm = parentCTM(el);
        var sx = nw / rb.w, sy = nh / rb.h;
        // Anchor = render top-left, mapped to parent coords (full inverse).
        var im = pm.inverse();
        var ax = im.a * rb.x + im.c * rb.y + im.e;
        var ay = im.b * rb.x + im.d * rb.y + im.f;
        return new DOMMatrix()
            .translate(ax, ay).scale(sx, sy).translate(-ax, -ay)
            .multiply(ownMatrix(el));
    }

    function matrixToString(m) {
        var r = function (v) { return Math.round(v * 1e6) / 1e6; };
        var values = [m.a, m.b, m.c, m.d, m.e, m.f].map(r);
        if (!values.every(function (v) { return Number.isFinite(v); })) return null;
        return "matrix(" + values.join(",") + ")";
    }

    function refreshGeoInputs(el, panel) {
        var rb = computeRenderBox(el);
        var vals = { x: Math.round(rb.x), y: Math.round(rb.y), w: Math.round(rb.w), h: Math.round(rb.h) };
        Object.keys(vals).forEach(function (k) {
            var inp = panel.querySelector('.prop-edit-geo[data-geo="' + k + '"]');
            if (inp && document.activeElement !== inp) inp.value = vals[k];
        });
    }

    function normalizeHexForPicker(val) {
        var s = String(val).trim();
        if (/^#[0-9a-fA-F]{6}$/.test(s)) return s;
        if (/^#[0-9a-fA-F]{3}$/.test(s)) {
            return "#" + s[1] + s[1] + s[2] + s[2] + s[3] + s[3];
        }
        return "#000000";
    }

    var SVG_UNIT_OPTIONAL_LENGTH_ATTRS = new Set([
        "x", "y", "x1", "x2", "y1", "y2",
        "cx", "cy", "r", "rx", "ry",
        "dx", "dy", "width", "height",
        "font-size", "stroke-width", "stroke-dashoffset",
        "letter-spacing", "word-spacing"
    ]);

    function normalizeSvgLengthValue(key, value) {
        var s = String(value || "");
        if (!SVG_UNIT_OPTIONAL_LENGTH_ATTRS.has(String(key).toLowerCase())) return s;
        s = s.trim();
        var m = s.match(/^(-?\d+(?:\.\d+)?)px$/i);
        return m ? m[1] : s;
    }

    function normalizeEditableAttrValue(key, value) {
        var s = String(value || "").trim();
        return normalizeSvgLengthValue(key, s);
    }

    function isSafeColor(val) {
        // Only allow values that look like CSS colors (hex, rgb, rgba, hsl, named).
        // Reject anything with ; : url @ \ to prevent CSS injection.
        return val.length < 100 && !/[;:@\\]|url\s*\(/i.test(val);
    }

    function splitNumberUnit(value) {
        var m = String(value || "").trim().match(/^(-?\d+(?:\.\d+)?)([A-Za-z%]*)$/);
        if (!m) return null;
        return { num: parseFloat(m[1]), unit: m[2] || "" };
    }

    function shiftedAttrValue(el, key, delta) {
        var parsed = splitNumberUnit(el.getAttribute(key));
        if (!parsed || !Number.isFinite(parsed.num)) return null;
        var next = Math.round((parsed.num + delta) * 1000) / 1000;
        return String(next) + parsed.unit;
    }

    function parentDelta(dx, dy, el) {
        var pm = parentCTM(el);
        var det = pm.a * pm.d - pm.b * pm.c;
        if (Math.abs(det) < 1e-9) return null;
        return {
            x: (pm.d * dx - pm.c * dy) / det,
            y: (-pm.b * dx + pm.a * dy) / det
        };
    }

    function firstNumber(value) {
        var m = String(value || "").match(/-?\d+(?:\.\d+)?/);
        return m ? parseFloat(m[0]) : null;
    }

    function formatCoord(value) {
        return String(Math.round(value * 1000) / 1000);
    }

    function tspanBaseline(tspan) {
        var text = tspan && tspan.parentElement;
        if (!text || localName(text) !== "text") return null;
        var curX = firstNumber(text.getAttribute("x"));
        var curY = firstNumber(text.getAttribute("y"));
        var children = Array.from(text.children);
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (localName(child) !== "tspan") continue;
            var x = firstNumber(child.getAttribute("x"));
            var y = firstNumber(child.getAttribute("y"));
            var dx = firstNumber(child.getAttribute("dx"));
            var dy = firstNumber(child.getAttribute("dy"));
            if (x !== null) curX = x;
            else if (dx !== null) curX = (curX || 0) + dx;
            if (y !== null) curY = y;
            else if (dy !== null) curY = (curY || 0) + dy;
            if (child === tspan) break;
        }
        if (curX === null || curY === null) return null;
        return { x: curX, y: curY };
    }

    function tspanPromotionPayload(tspan) {
        if (localName(tspan) !== "tspan") return null;
        var base = tspanBaseline(tspan);
        if (!base) return null;
        var own = ownMatrix(tspan);
        var close = function (a, b) { return Math.abs(a - b) < 1e-6; };
        if (!close(own.a, 1) || !close(own.b, 0) ||
                !close(own.c, 0) || !close(own.d, 1)) return null;
        return {
            x: formatCoord(base.x + own.e),
            y: formatCoord(base.y + own.f)
        };
    }

    function copyTextAttrs(src, dst, skip) {
        Array.from(src.attributes || []).forEach(function (attr) {
            if (skip[attr.name]) return;
            dst.setAttribute(attr.name, attr.value);
        });
    }

    function adjustedDyValue(oldValue, nextY, prevY) {
        var parsed = splitNumberUnit(oldValue);
        if (!parsed) return formatCoord(nextY - prevY);
        return formatCoord(nextY - prevY) + parsed.unit;
    }

    function promoteTspanDom(tspan, promoted) {
        var text = tspan && tspan.parentElement;
        if (!text || localName(tspan) !== "tspan" || localName(text) !== "text") return null;
        var next = tspan.nextElementSibling;
        var nextBase = next && localName(next) === "tspan" ? tspanBaseline(next) : null;
        var prev = tspan.previousElementSibling;
        var prevBase = prev && localName(prev) === "tspan" ? tspanBaseline(prev) : null;
        var parentBaseY = firstNumber(text.getAttribute("y")) || 0;

        var newText = document.createElementNS(tspan.namespaceURI, "text");
        copyTextAttrs(text, newText, { id: true, x: true, y: true, dx: true, dy: true });
        copyTextAttrs(tspan, newText, {
            id: true, x: true, y: true, dx: true, dy: true, transform: true
        });
        newText.setAttribute("id", tspan.id);
        newText.setAttribute("x", promoted.x);
        newText.setAttribute("y", promoted.y);

        Array.from(tspan.childNodes || []).forEach(function (node) {
            newText.appendChild(node.cloneNode(true));
        });
        if (newText.childNodes.length === 0) {
            newText.textContent = tspan.textContent || "";
        }

        var textParent = text.parentNode;
        var textNext = text.nextSibling;
        var textClone = text.cloneNode(true);
        newText.__promotionRollback = function () {
            if (newText.parentNode) newText.parentNode.removeChild(newText);
            if (text.parentNode) text.parentNode.removeChild(text);
            if (textParent) {
                if (textNext && textNext.parentNode === textParent) {
                    textParent.insertBefore(textClone, textNext);
                } else {
                    textParent.appendChild(textClone);
                }
            }
            selectedElementIds.delete(newText.id);
            selectedElementIds.add(tspan.id);
            markSelection();
            return textClone.querySelector("#" + CSS.escape(tspan.id)) || textClone;
        };

        text.parentNode.insertBefore(newText, text.nextSibling);
        text.removeChild(tspan);
        if (next && nextBase && !next.hasAttribute("y") && next.hasAttribute("dy")) {
            next.setAttribute("dy", adjustedDyValue(
                next.getAttribute("dy"),
                nextBase.y,
                prevBase ? prevBase.y : parentBaseY
            ));
        }
        if (!(text.textContent || "").trim() && text.children.length === 0) {
            text.parentNode.removeChild(text);
        }
        selectedElementIds.delete(tspan.id);
        selectedElementIds.add(newText.id);
        markSelection();
        return newText;
    }

    function payloadForMovedElement(el, attrs) {
        var promoted = tspanPromotionPayload(el);
        if (promoted) return { promote_tspan: promoted };
        return { attrs: attrs };
    }

    function canUseRawGeometry(el) {
        var own = ownMatrix(el);
        var close = function (a, b) { return Math.abs(a - b) < 1e-6; };
        if (close(own.b, 0) && close(own.c, 0)) {
            if (close(own.a, 1) && close(own.d, 1)) return "translate";
            if (localName(el) === "use") return "use-transform";
            if (["rect", "image"].indexOf(localName(el)) !== -1) return "box-transform";
        }
        return "";
    }

    function rawMoveAttrs(el, dx, dy) {
        if (localName(el) === "g" && el.hasAttribute("data-icon") &&
                el.hasAttribute("data-use-x") && el.hasAttribute("data-use-y")) {
            var iconOwn = ownMatrix(el);
            var close = function (a, b) { return Math.abs(a - b) < 1e-6; };
            if (close(iconOwn.b, 0) && close(iconOwn.c, 0)) {
                var iconDelta = parentDelta(dx, dy, el);
                if (iconDelta) {
                    var iconAttrs = {
                        x: formatCoord(iconOwn.e + iconDelta.x),
                        y: formatCoord(iconOwn.f + iconDelta.y)
                    };
                    if (el.hasAttribute("data-use-has-transform")) {
                        iconAttrs.transform = null;
                    }
                    return iconAttrs;
                }
            }
        }

        var rawMode = canUseRawGeometry(el);
        if (!rawMode) return null;
        var d = parentDelta(dx, dy, el);
        if (!d) return null;
        var tag = localName(el);
        var attrs = {};
        var own = ownMatrix(el);
        var add = function (key, delta) {
            if (!el.hasAttribute(key)) return false;
            var next = shiftedAttrValue(el, key, delta);
            if (next === null) return false;
            attrs[key] = next;
            return true;
        };
        var fmt = function (value) {
            return String(Math.round(value * 1000) / 1000);
        };
        var bakeTranslate = function (xKey, yKey) {
            if (!el.hasAttribute(xKey) || !el.hasAttribute(yKey)) return false;
            if (rawMode === "use-transform") {
                attrs[xKey] = fmt(own.e + d.x);
                attrs[yKey] = fmt(own.f + d.y);
                attrs.transform = null;
                return true;
            }
            var nx = shiftedAttrValue(el, xKey, own.e + d.x);
            var ny = shiftedAttrValue(el, yKey, own.f + d.y);
            if (nx === null || ny === null) return false;
            attrs[xKey] = nx;
            attrs[yKey] = ny;
            if (el.hasAttribute("transform")) attrs.transform = null;
            return true;
        };
        var bakeBox = function () {
            if (!el.hasAttribute("x") || !el.hasAttribute("y") ||
                    !el.hasAttribute("width") || !el.hasAttribute("height")) return false;
            var x = splitNumberUnit(el.getAttribute("x"));
            var y = splitNumberUnit(el.getAttribute("y"));
            var w = splitNumberUnit(el.getAttribute("width"));
            var h = splitNumberUnit(el.getAttribute("height"));
            if (!x || !y || !w || !h || x.unit !== y.unit ||
                    x.unit !== w.unit || x.unit !== h.unit) return false;
            attrs.x = fmt(own.a * x.num + own.e + d.x) + x.unit;
            attrs.y = fmt(own.d * y.num + own.f + d.y) + y.unit;
            attrs.width = fmt(Math.abs(own.a) * w.num) + w.unit;
            attrs.height = fmt(Math.abs(own.d) * h.num) + h.unit;
            attrs.transform = null;
            return true;
        };

        if (rawMode === "box-transform") {
            return bakeBox() ? attrs : null;
        }
        if (["rect", "image", "use", "text"].indexOf(tag) !== -1) {
            return bakeTranslate("x", "y") ? attrs : null;
        }
        if (tag === "circle" || tag === "ellipse") {
            return bakeTranslate("cx", "cy") ? attrs : null;
        }
        if (tag === "line") {
            if (add("x1", own.e + d.x) && add("x2", own.e + d.x) &&
                    add("y1", own.f + d.y) && add("y2", own.f + d.y)) {
                if (el.hasAttribute("transform")) attrs.transform = null;
                return attrs;
            }
            return null;
        }
        return null;
    }

    function attrsForMove(el, dx, dy) {
        var attrs = rawMoveAttrs(el, dx, dy);
        if (attrs) return attrs;
        var rb = computeRenderBox(el);
        var moved = matrixAfterMove(el, rb, rb.x + dx, rb.y + dy);
        var tstr = matrixToString(moved);
        return tstr ? { transform: tstr } : null;
    }

    function computeElementsBox(elements) {
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        elements.forEach(function (el) {
            var rb = computeRenderBox(el);
            minX = Math.min(minX, rb.x);
            minY = Math.min(minY, rb.y);
            maxX = Math.max(maxX, rb.x + rb.w);
            maxY = Math.max(maxY, rb.y + rb.h);
        });
        return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }

    function topLevelSelectedElements(ids) {
        var els = ids.map(function (eid) {
            return svgContent.querySelector("#" + CSS.escape(eid));
        }).filter(Boolean);
        return els.filter(function (el) {
            return !els.some(function (other) {
                return other !== el && other.contains(el);
            });
        });
    }

    function attachPropEditors(el) {
        var eid = el.id;
        var panel = elementPropsEl;

        var groupBtn = panel.querySelector(".btn-select-group");
        if (groupBtn) {
            groupBtn.addEventListener("click", function () {
                var gid = groupBtn.getAttribute("data-group-id");
                var groupEl = gid ? svgContent.querySelector("#" + CSS.escape(gid)) : null;
                if (groupEl) selectElement(groupEl, false);
            });
        }

        // L1: text content (fires on blur/change).
        var contentBox = panel.querySelector(".prop-edit-content");
        if (contentBox) {
            contentBox.addEventListener("change", function () {
                var newText = contentBox.value;
                stageEditRequest(eid, { text: newText })
                    .then(function () { el.textContent = newText; })
                    .catch(function (err) { showError(t("err_edit") + err.message); });
            });
        }

        // Raw own attributes: color picker + text input stay in sync.
        panel.querySelectorAll(".prop-edit-color").forEach(function (picker) {
            var key = picker.getAttribute("data-key");
            var textInput = panel.querySelector('.prop-edit-color-text[data-key="' + key + '"]');
            picker.addEventListener("input", function () {
                if (textInput) textInput.value = picker.value;
            });
            picker.addEventListener("change", function () {
                stageAttr(el, eid, key, picker.value);
            });
        });
        panel.querySelectorAll(".prop-edit-color-text").forEach(function (textInput) {
            var key = textInput.getAttribute("data-key");
            var picker = panel.querySelector('input.prop-edit-color[data-key="' + key + '"]');
            textInput.addEventListener("change", function () {
                var v = textInput.value.trim();
                if (picker) picker.value = normalizeHexForPicker(v);
                stageAttr(el, eid, key, v);
            });
        });

        panel.querySelectorAll(".prop-edit-text-style-color").forEach(function (picker) {
            var key = picker.getAttribute("data-key");
            var textInput = panel.querySelector('.prop-edit-text-style[data-key="' + key + '"]');
            picker.addEventListener("input", function () {
                if (textInput) textInput.value = picker.value;
            });
            picker.addEventListener("change", function () {
                if (textInput) textInput.value = picker.value;
                stageTextStyleAttr(key, picker.value, picker.getAttribute("data-target-ids"));
            });
        });
        panel.querySelectorAll(".prop-edit-text-style").forEach(function (input) {
            input.addEventListener("change", function () {
                var key = input.getAttribute("data-key");
                var value = normalizeEditableAttrValue(key, input.value);
                if (!value) return;
                stageTextStyleAttr(key, value, input.getAttribute("data-target-ids"));
            });
        });

        panel.querySelectorAll(".prop-edit-attr, .prop-edit-attr-area").forEach(function (input) {
            var key = input.getAttribute("data-key");
            input.addEventListener("change", function () {
                stageAttr(el, eid, key, normalizeEditableAttrValue(key, input.value));
            });
        });

        // Geometry: position (move) + size (resize), folded into the transform.
        if (panel.querySelector(".prop-edit-geo")) {
            var readGeo = function (k) {
                var inp = panel.querySelector('.prop-edit-geo[data-geo="' + k + '"]');
                return inp ? parseFloat(inp.value) : NaN;
            };
            var commitGeo = function (mode) {
                var rb;
                try { rb = computeRenderBox(el); } catch (e) { return; }
                var newM;
                var attrs = null;
                if (mode === "move") {
                    var nx = readGeo("x"), ny = readGeo("y");
                    if (isNaN(nx) || isNaN(ny)) return;
                    if (Math.abs(nx - rb.x) < 1e-6 && Math.abs(ny - rb.y) < 1e-6) return;
                    attrs = attrsForMove(el, nx - rb.x, ny - rb.y);
                    if (!attrs) newM = matrixAfterMove(el, rb, nx, ny);
                } else {
                    var nw = readGeo("w"), nh = readGeo("h");
                    if (isNaN(nw) || isNaN(nh) || nw <= 0 || nh <= 0 || rb.w <= 0 || rb.h <= 0) {
                        showError(t("err_edit") + "size");
                        return;
                    }
                    if (Math.abs(nw - rb.w) < 1e-6 && Math.abs(nh - rb.h) < 1e-6) return;
                    newM = matrixAfterResize(el, rb, nw, nh);
                }
                if (!attrs) {
                    var tstr = matrixToString(newM);
                    if (!tstr) {
                        showError(t("err_edit") + "transform");
                        return;
                    }
                    attrs = { transform: tstr };
                }
                var payload = mode === "move" ? payloadForMovedElement(el, attrs) : { attrs: attrs };
                stageEditRequest(eid, payload)
                    .then(function () {
                    if (payload.promote_tspan) {
                        el = promoteTspanDom(el, payload.promote_tspan) || el;
                    } else {
                        applyElementAttrs(el, attrs);
                        markCommittedAttrs(el, attrs);
                    }
                    refreshGeoInputs(el, panel);
                    })
                    .catch(function (err) { showError(t("err_edit") + err.message); });
            };
            panel.querySelectorAll('.prop-edit-geo[data-geo="x"], .prop-edit-geo[data-geo="y"]').forEach(function (inp) {
                inp.addEventListener("change", function () { commitGeo("move"); });
            });
            panel.querySelectorAll('.prop-edit-geo[data-geo="w"], .prop-edit-geo[data-geo="h"]').forEach(function (inp) {
                inp.addEventListener("change", function () { commitGeo("resize"); });
            });
        }
    }

    function stageTextStyleAttr(key, value, encodedTargetIds) {
        value = normalizeEditableAttrValue(key, value);
        if ((key === "fill" || key === "stroke") && !isSafeColor(value)) {
            showError(t("err_edit") + key);
            return;
        }
        var ids;
        try {
            ids = JSON.parse(decodeURIComponent(encodedTargetIds || "%5B%5D"));
        } catch (e) {
            ids = [];
        }
        var targets = ids.map(function (id) {
            return svgContent.querySelector("#" + CSS.escape(id));
        }).filter(function (target) {
            return target && attrOrComputedValue(target, key) !== value;
        });
        if (targets.length === 0) return;

        var attrs = {};
        attrs[key] = value;
        var jobs = targets.map(function (target) {
            return stageEditRequest(target.id, { attrs: attrs }).then(function () {
                target.setAttribute(key, value);
            });
        });
        Promise.all(jobs)
            .then(function () { updateSelectionPanel(); })
            .catch(function (err) { showError(t("err_edit") + err.message); });
    }

    function stageAttr(el, eid, key, value) {
        value = normalizeEditableAttrValue(key, value);
        if ((key === "fill" || key === "stroke") && !isSafeColor(value)) {
            showError(t("err_edit") + key);
            return;
        }
        var attrs = {};
        attrs[key] = value;
        stageEditRequest(eid, { attrs: attrs })
            .then(function () { el.setAttribute(key, value); })
            .catch(function (err) { showError(t("err_edit") + err.message); });
    }

    // Tracks every in-flight direct-edit POST so Apply changes can wait for them
    // to land before /save-all (otherwise a just-sent edit could arrive after the
    // save and resurrect a pending edit).
    var inFlightEdits = new Set();

    function drainDirectEdits() {
        if (inFlightEdits.size === 0) return Promise.resolve();
        return Promise.allSettled(Array.from(inFlightEdits)).then(function (results) {
            var failed = results.find(function (r) { return r.status === "rejected"; });
            if (failed) throw (failed.reason || new Error("direct edit failed"));
            return drainDirectEdits();
        });
    }

    function stageEditRequest(eid, payload, slideName) {
        // Pin the slide at call time: a queued nudge may fire after the user has
        // navigated, and must still POST to the slide it was made on, not the
        // global currentSlide.
        var slide = slideName || currentSlide;
        var body = { element_id: eid };
        if (payload.text !== undefined) body.text = payload.text;
        if (payload.attrs !== undefined) body.attrs = payload.attrs;
        if (payload.promote_tspan !== undefined) body.promote_tspan = payload.promote_tspan;
        var p = fetch("/api/slide/" + encodeURIComponent(slide) + "/edit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        }).then(jsonOrThrow).then(function (data) {
            if (data && data.undo_depth !== undefined) {
                editStackCount[slide] = data.undo_depth;
                if (slide === currentSlide) updateUndoButton();
                updatePendingStatus();
            }
            if (payloadHasMatrixTransform(payload)) {
                markMatrixTransformEdit(slide);
            }
            maybeShowSavedHint();
            return data;
        });
        inFlightEdits.add(p);
        var done = function () { inFlightEdits.delete(p); };
        p.then(done, done);
        return p;
    }

    function renderMultiSelectSummary(ids) {
        var moveEls = topLevelSelectedElements(ids);
        var summary = '<div class="prop-caption">' + escapeHtml(t("label_batch_edit")) + '</div>';

        if (moveEls.length > 0) {
            try {
                var rb = computeElementsBox(moveEls);
                summary += '<div class="prop-section">' + escapeHtml(t("section_geometry")) + '</div>';
                summary += '<table class="prop-table"><tr><td class="prop-key">x / y</td>' +
                    '<td class="prop-val geo-cell">' +
                    '<input type="number" class="prop-edit prop-edit-multi-geo" data-geo="x" value="' +
                    Math.round(rb.x) + '">' +
                    '<input type="number" class="prop-edit prop-edit-multi-geo" data-geo="y" value="' +
                    Math.round(rb.y) + '">' +
                    '</td></tr></table>';
            } catch (e) { /* no multi geometry */ }
        }
        summary += '<div class="prop-section">' + escapeHtml(t("section_style")) + '</div>';
        summary += '<table class="prop-table">';
        batchEditSpecs(moveEls).forEach(function (spec) {
            summary += '<tr><td class="prop-key">' + escapeHtml(spec.key) + '</td><td class="prop-val">';
            summary += renderBatchControl(spec);
            summary += '</td></tr>';
        });
        summary += '</table>';
        return summary;
    }

    function batchEditSpecs(elements) {
        var keys = [
            { key: "fill", type: "color" },
            { key: "stroke", type: "color" },
            { key: "opacity", type: "number", min: "0", max: "1", step: "0.05" }
        ];
        if (elements.length > 0 && elements.every(isTextElement)) {
            keys = keys.concat([
                { key: "font-size", type: "text" },
                { key: "font-family", type: "text" },
                { key: "font-weight", type: "select",
                  options: ["", "normal", "bold", "300", "400", "500", "600", "700", "800"] },
                { key: "text-anchor", type: "select", options: ["", "start", "middle", "end"] }
            ]);
        }
        return keys.map(function (spec) {
            var value = commonAttrValue(elements, spec.key);
            var copy = Object.assign({}, spec);
            copy.value = value === null ? "" : value;
            copy.mixed = value === null;
            return copy;
        });
    }

    function isTextElement(el) {
        var tag = el.tagName.toLowerCase();
        return tag === "text" || tag === "tspan";
    }

    function commonAttrValue(elements, key) {
        if (elements.length === 0) return "";
        var first = attrOrComputedValue(elements[0], key);
        for (var i = 1; i < elements.length; i++) {
            if (attrOrComputedValue(elements[i], key) !== first) return null;
        }
        return first;
    }

    function attrOrComputedValue(el, key) {
        var value = el.getAttribute(key);
        if (value !== null && value !== "") return normalizeSvgLengthValue(key, value);
        var style = window.getComputedStyle(el);
        var map = {
            "fill": "fill",
            "stroke": "stroke",
            "opacity": "opacity",
            "font-size": "fontSize",
            "font-family": "fontFamily",
            "font-weight": "fontWeight",
            "text-anchor": "textAnchor"
        };
        return normalizeSvgLengthValue(key, (map[key] && style[map[key]]) || "");
    }

    function renderBatchControl(spec) {
        var placeholder = spec.mixed ? t("multi_mixed") : "";
        if (spec.type === "color") {
            return '<input type="color" class="prop-edit prop-edit-batch-color" data-key="' +
                escapeHtml(spec.key) + '" value="' + normalizeHexForPicker(spec.value) + '">' +
                '<input type="text" class="prop-edit prop-edit-batch" data-key="' +
                escapeHtml(spec.key) + '" placeholder="' + escapeHtml(placeholder) +
                '" value="' + escapeHtml(spec.mixed ? "" : spec.value) + '">';
        }
        if (spec.type === "number") {
            return '<input type="number" class="prop-edit prop-edit-batch" data-key="' +
                escapeHtml(spec.key) + '" min="' + escapeHtml(spec.min || "") +
                '" max="' + escapeHtml(spec.max || "") + '" step="' +
                escapeHtml(spec.step || "1") + '" placeholder="' + escapeHtml(placeholder) +
                '" value="' + escapeHtml(spec.mixed ? "" : spec.value) + '">';
        }
        if (spec.type === "select") {
            var html = '<select class="prop-edit prop-edit-batch" data-key="' + escapeHtml(spec.key) + '">';
            spec.options.forEach(function (opt) {
                var label = opt || placeholder || "";
                var selected = !spec.mixed && spec.value === opt ? " selected" : "";
                html += '<option value="' + escapeHtml(opt) + '"' + selected + '>' +
                    escapeHtml(label) + '</option>';
            });
            html += '</select>';
            return html;
        }
        return '<input type="text" class="prop-edit prop-edit-batch" data-key="' +
            escapeHtml(spec.key) + '" placeholder="' + escapeHtml(placeholder) +
            '" value="' + escapeHtml(spec.mixed ? "" : spec.value) + '">';
    }

    function attachMultiSelectionEditors(ids) {
        var panel = elementPropsEl;
        var moveEls = topLevelSelectedElements(ids);
        if (moveEls.length === 0) return;

        var readGeo = function (k) {
            var inp = panel.querySelector('.prop-edit-multi-geo[data-geo="' + k + '"]');
            return inp ? parseFloat(inp.value) : NaN;
        };
        var commitMove = function () {
            var rb;
            try { rb = computeElementsBox(moveEls); } catch (e) { return; }
            var nx = readGeo("x"), ny = readGeo("y");
            if (isNaN(nx) || isNaN(ny)) return;
            var dx = nx - rb.x, dy = ny - rb.y;
            if (Math.abs(dx) < 1e-6 && Math.abs(dy) < 1e-6) return;

            var jobs = [];
            moveEls.forEach(function (el) {
                var attrs;
                try { attrs = attrsForMove(el, dx, dy); } catch (e) { attrs = null; }
                if (!attrs) return;
                var payload = payloadForMovedElement(el, attrs);
                jobs.push(stageEditRequest(el.id, payload).then(function () {
                    if (payload.promote_tspan) promoteTspanDom(el, payload.promote_tspan);
                    else {
                        applyElementAttrs(el, attrs);
                        markCommittedAttrs(el, attrs);
                    }
                }));
            });

            Promise.all(jobs)
                .then(function () { updateSelectionPanel(); })
                .catch(function (err) { showError(t("err_edit") + err.message); });
        };

        panel.querySelectorAll(".prop-edit-multi-geo").forEach(function (inp) {
            inp.addEventListener("change", commitMove);
        });

        panel.querySelectorAll(".prop-edit-batch-color").forEach(function (picker) {
            var key = picker.getAttribute("data-key");
            var text = panel.querySelector('.prop-edit-batch[data-key="' + key + '"]');
            picker.addEventListener("input", function () {
                if (text) text.value = picker.value;
            });
            picker.addEventListener("change", function () {
                if (text) text.value = picker.value;
                commitBatchAttr(key, picker.value, moveEls);
            });
        });

        panel.querySelectorAll(".prop-edit-batch").forEach(function (input) {
            input.addEventListener("change", function () {
                var key = input.getAttribute("data-key");
                var value = normalizeEditableAttrValue(key, input.value);
                if (!value) return;
                commitBatchAttr(key, value, moveEls);
            });
        });
    }

    function commitBatchAttr(key, value, elements) {
        value = normalizeEditableAttrValue(key, value);
        if ((key === "fill" || key === "stroke") && !isSafeColor(value)) {
            showError(t("err_edit") + key);
            return;
        }
        var jobs = elements.map(function (el) {
            var attrs = {};
            attrs[key] = value;
            return stageEditRequest(el.id, { attrs: attrs }).then(function () {
                el.setAttribute(key, value);
            });
        });
        Promise.all(jobs)
            .then(function () { updateSelectionPanel(); })
            .catch(function (err) { showError(t("err_edit") + err.message); });
    }

    // ================================================================
    //  Boot
    // ================================================================
    applyI18n();
    initAnnotationQuickActions();
    updatePendingStatus();
    var langToggleBtn = document.getElementById("btn-lang-toggle");
    if (langToggleBtn) {
        langToggleBtn.textContent = LANG === "zh" ? "EN" : "中";
        langToggleBtn.title = t("lang_toggle_title");
        langToggleBtn.addEventListener("click", function () {
            setLang(LANG === "zh" ? "en" : "zh");
        });
    }

    loadConfig().then(function () {
        loadSlides();
        startSlidePolling();
    });
    initRubberBand();
    initKeyboardShortcuts();
    initSlideNav();
    if (btnUndo) btnUndo.addEventListener("click", runUndo);
})();
