/* ============================================================
   PPT Master - SVG Editor  |  app.js
   Vanilla JS, IIFE pattern
   ============================================================ */
(function () {
    "use strict";

    // ---- DOM refs ---------------------------------------------------
    var slideListEl       = document.getElementById("slide-list");
    var svgPlaceholder    = document.getElementById("svg-placeholder");
    var svgContent        = document.getElementById("svg-content");
    var selectedElementEl = document.getElementById("selected-element");
    var annotationInput   = document.getElementById("annotation-input");
    var annotationText    = document.getElementById("annotation-text");
    var btnAddAnnotation  = document.getElementById("btn-add-annotation");
    var annotationsEl     = document.getElementById("annotations");
    var btnSave           = document.getElementById("btn-save");
    var modalOverlay      = document.getElementById("modal-overlay");
    var modalMessage      = document.getElementById("modal-message");
    var modalConfirm      = document.getElementById("modal-confirm");
    var modalCancel       = document.getElementById("modal-cancel");

    // ---- State ------------------------------------------------------
    var currentSlide      = null;   // filename, e.g. "slide_01.svg"
    var selectedElementId = null;   // id attr of the clicked SVG element
    var slideAnnotations  = {};     // {element_id: annotation_text} for current slide

    // ================================================================
    //  1.  loadSlides  -- GET /api/slides
    // ================================================================
    function loadSlides() {
        fetch("/api/slides")
            .then(function (res) { return res.json(); })
            .then(function (data) {
                slideListEl.innerHTML = "";
                (data.slides || []).forEach(function (s) {
                    var item = document.createElement("div");
                    item.className = "slide-item" + (s.name === currentSlide ? " active" : "");
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
            })
            .catch(function (err) {
                console.error("loadSlides:", err);
                showError("Failed to load slides: " + err.message);
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
        selectedElementId = null;
        slideAnnotations = {};

        // Reset right panel
        clearSelection();

        fetch("/api/slide/" + encodeURIComponent(name))
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    console.error("selectSlide:", data.error);
                    return;
                }
                // Render SVG
                svgPlaceholder.style.display = "none";
                svgContent.style.display = "block";
                svgContent.innerHTML = sanitizeSvg(data.content);

                // Build annotations map from response
                (data.annotations || []).forEach(function (a) {
                    slideAnnotations[a.element_id] = a.annotation;
                });

                setupSvgInteraction();
                refreshAnnotationVisuals();
                updateAnnotationList();
            })
            .catch(function (err) {
                console.error("selectSlide:", err);
                showError("Failed to load slide: " + err.message);
            });
    }

    // ================================================================
    //  3.  setupSvgInteraction
    // ================================================================
    var SKIP_TAGS = ["defs", "style", "title", "desc"];

    function setupSvgInteraction() {
        var svg = svgContent.querySelector("svg");
        if (!svg) return;

        var allEls = svg.querySelectorAll("*");
        allEls.forEach(function (el) {
            var tag = el.tagName.toLowerCase();
            if (SKIP_TAGS.indexOf(tag) !== -1) return;
            if (el === svg) return;

            el.classList.add("svg-selectable");

            el.addEventListener("click", function (e) {
                e.stopPropagation();
                selectElement(el);
            });
        });

        // Click on blank area clears selection
        svg.addEventListener("click", function (e) {
            if (e.target === svg) clearSelection();
        });
    }

    // ================================================================
    //  4.  selectElement
    // ================================================================
    function selectElement(elem) {
        // Remove old highlight
        if (selectedElementId) {
            var old = svgContent.querySelector("#" + CSS.escape(selectedElementId));
            if (old) old.classList.remove("svg-selected");
        }

        selectedElementId = elem.id || null;
        elem.classList.add("svg-selected");

        // Update right panel info
        selectedElementEl.classList.remove("empty");
        var tag = elem.tagName.toLowerCase();
        var id  = elem.id || "(no id)";
        selectedElementEl.innerHTML =
            '<span class="el-tag">&lt;' + escapeHtml(tag) + '&gt;</span>' +
            '<span class="el-id">' + escapeHtml(id) + '</span>';

        // Show annotation input, pre-fill if annotation already exists
        annotationInput.style.display = "block";
        annotationText.value = slideAnnotations[selectedElementId] || "";
        annotationText.focus();
    }

    // ================================================================
    //  5.  clearSelection
    // ================================================================
    function clearSelection() {
        if (selectedElementId) {
            var el = svgContent.querySelector("#" + CSS.escape(selectedElementId));
            if (el) el.classList.remove("svg-selected");
        }
        selectedElementId = null;
        selectedElementEl.classList.add("empty");
        selectedElementEl.innerHTML = "Click an element on the slide to select it";
        annotationInput.style.display = "none";
        annotationText.value = "";
    }

    // ================================================================
    //  6.  Add annotation  -- POST /api/slide/{name}/annotate
    // ================================================================
    btnAddAnnotation.addEventListener("click", function () {
        if (!currentSlide || !selectedElementId) return;

        var text = annotationText.value.trim();
        if (!text) return;

        fetch("/api/slide/" + encodeURIComponent(currentSlide) + "/annotate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                element_id: selectedElementId,
                annotation: text
            })
        })
            .then(function (res) { return res.json(); })
            .then(function () {
                slideAnnotations[selectedElementId] = text;
                refreshAnnotationVisuals();
                updateAnnotationList();
                annotationText.value = "";
                // Reload slide list to update badge counts
                loadSlides();
            })
            .catch(function (err) {
                console.error("addAnnotation:", err);
                showError("Failed to add annotation: " + err.message);
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
                refreshAnnotationVisuals();
                updateAnnotationList();
                loadSlides();
            })
            .catch(function (err) {
                console.error("removeAnnotation:", err);
                showError("Failed to remove annotation: " + err.message);
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
            annotationsEl.innerHTML = '<div class="annotations-empty">No annotations yet</div>';
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
            removeBtn.title = "Remove annotation";
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
    // 10.  Save all  -- two-step: confirm then save + shutdown
    // ================================================================
    var CONFIRM_MSG = "Submitting will close this page. Make sure you've added all the annotations you want.";
    var SUCCESS_MSG = "Annotations submitted.\n\nReturn to the chat and tell the AI you're ready — it will apply your edits.";

    btnSave.addEventListener("click", function () {
        // Step 1: show confirmation
        modalMessage.textContent = CONFIRM_MSG;
        modalConfirm.style.display = "";
        modalCancel.style.display = "";
        modalOverlay.style.display = "flex";
    });

    modalConfirm.addEventListener("click", function () {
        // Step 2: save + shutdown
        modalConfirm.style.display = "none";
        modalCancel.style.display = "none";

        fetch("/api/save-all", { method: "POST" })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    modalMessage.textContent = "Save failed: " + data.error;
                } else {
                    modalMessage.textContent = SUCCESS_MSG;
                    fetch("/api/shutdown", { method: "POST" }).catch(function () {});
                }
            })
            .catch(function (err) {
                modalMessage.textContent = "Save failed: " + err;
            });
    });

    modalCancel.addEventListener("click", function () {
        modalOverlay.style.display = "none";
    });

    // Close modal on overlay click
    modalOverlay.addEventListener("click", function (e) {
        if (e.target === modalOverlay) {
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

    function escapeHtml(str) {
        var d = document.createElement("div");
        d.appendChild(document.createTextNode(str));
        return d.innerHTML;
    }

    // ================================================================
    //  Boot
    // ================================================================
    loadSlides();
})();
