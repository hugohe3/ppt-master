(function () {
  "use strict";

  var STATE = null;
  var OUTLINE = { schema_version: 2, pages: [] };
  var SELECTED_TEMPLATE = "";
  var SELECTED_VISUAL_STYLE = "";
  var VISUAL_STYLE_SOURCE = "";
  var RECOMMENDED_VISUAL_STYLE = "";
  var VISUAL_STYLE_CATALOG = [];
  var ANALYSIS_REQUIRED = null;
  var ANALYSIS_STYLE_ID = "";
  var ANALYSIS_DOMAIN_ID = "";

  function byId(id) { return document.getElementById(id); }
  function toast(message) {
    var node = byId("toast");
    node.textContent = message;
    node.classList.add("show");
    setTimeout(function () { node.classList.remove("show"); }, 3200);
  }
  function request(url, options) {
    return fetch(url, options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) throw new Error(data.error || ("HTTP " + response.status));
        return data;
      });
    });
  }
  function setBusy(button, busy, busyText) {
    if (!button.dataset.label) button.dataset.label = button.textContent;
    button.disabled = busy;
    button.textContent = busy ? busyText : button.dataset.label;
  }

  function loadState() {
    return request("/api/workflow/state").then(function (data) {
      STATE = data;
      byId("project-name").textContent = data.project;
      var selection = data.selection || {};
      var library = data.analysis_library || {};
      SELECTED_TEMPLATE = selection.template_id || "";
      SELECTED_VISUAL_STYLE = selection.visual_style || "";
      VISUAL_STYLE_SOURCE = selection.visual_style_source || "";
      RECOMMENDED_VISUAL_STYLE = data.visual_style_recommendation || "swiss-minimal";
      ANALYSIS_REQUIRED = typeof selection.analysis_required === "boolean" ? selection.analysis_required : null;
      ANALYSIS_STYLE_ID = selection.analysis_style_id || "";
      ANALYSIS_DOMAIN_ID = selection.analysis_domain_id || "";
      renderIntakeSummary();
      renderTemplates();
      renderVisualStyles();
      renderAnalysisDecision();
      renderAnalysisLibrary();
      renderImages();
      OUTLINE = data.outline_draft || { schema_version: 2, pages: [] };
      renderOutline();
      byId("custom-style").value = selection.custom_style_description || "";
      byId("provider-profile").value = selection.provider_profile || "gptimage2.0-1K-mid";
      renderTemplates();
      renderInventorySummary();
      var gates = data.gates || {};
      byId("outline-status").textContent = gates.content_inventory_ready
        ? (data.outline_draft ? "大纲可编辑；保存后需要重新确认。" : "内容盘点已完成，等待 AI 写入逐页大纲，也可手动增加页面。")
        : "大纲尚未开放：" + (data.content_inventory_message || data.outline_message || "请先完成分析图决策与内容盘点");
      byId("confirm-status").textContent = gates.generation_unlocked
        ? "当前大纲已确认，正式生成已解锁。"
        : "尚未解锁：" + (data.outline_message || "请按顺序完成前置步骤");
    }).catch(function (error) { toast(error.message); });
  }

  function renderInventorySummary() {
    var host = byId("inventory-summary");
    var inventory = STATE.content_inventory;
    if (!inventory) {
      host.textContent = "尚无内容盘点。分析图决策完成且所需图片全部生成后，由 Strategist 汇总全部素材并推导页数。";
      return;
    }
    if (!STATE.content_inventory_ready) {
      host.textContent = "现有内容盘点已因素材、风格或分析图变化而失效，需要重新整理。";
      return;
    }
    var rationale = inventory.page_count_rationale;
    if (Array.isArray(rationale)) rationale = rationale.join("；");
    host.innerHTML = "";
    host.appendChild(document.createTextNode("建议页数 "));
    var count = document.createElement("strong"); count.textContent = inventory.recommended_page_count + " 页"; host.appendChild(count);
    host.appendChild(document.createTextNode("\n" + (rationale || "") + "\n最终页数以确认时的页面卡片数量为准。"));
  }

  function renderVisualStyles() {
    var host = byId("visual-style-grid");
    if (!host || !VISUAL_STYLE_CATALOG.length) return;
    host.innerHTML = "";
    VISUAL_STYLE_CATALOG.forEach(function (group) {
      var section = document.createElement("section"); section.className = "visual-style-group";
      var heading = document.createElement("h4"); heading.textContent = group.group_zh || group.group || "视觉风格";
      var items = document.createElement("div"); items.className = "visual-style-items";
      (group.items || []).forEach(function (item) {
        var card = document.createElement("button"); card.type = "button";
        card.className = "visual-style-card" + (SELECTED_VISUAL_STYLE === item.id ? " selected" : "");
        var preview = document.createElement("img"); preview.src = "/static/style_previews/" + item.id + ".svg"; preview.alt = item.label_zh || item.id;
        var title = document.createElement("b"); title.textContent = item.label_zh || item.label || item.id;
        var desc = document.createElement("small"); desc.textContent = item.desc_zh || item.desc || "";
        card.appendChild(preview); card.appendChild(title); card.appendChild(desc);
        if (item.id === RECOMMENDED_VISUAL_STYLE) {
          var badge = document.createElement("span"); badge.className = "recommend-badge"; badge.textContent = "推荐"; card.appendChild(badge);
        }
        card.onclick = function () { SELECTED_VISUAL_STYLE = item.id; VISUAL_STYLE_SOURCE = "user"; renderVisualStyles(); };
        items.appendChild(card);
      });
      section.appendChild(heading); section.appendChild(items); host.appendChild(section);
    });
    var customSection = document.createElement("section"); customSection.className = "visual-style-group";
    var customHeading = document.createElement("h4"); customHeading.textContent = "自定义";
    var customItems = document.createElement("div"); customItems.className = "visual-style-items";
    var customCard = document.createElement("button"); customCard.type = "button";
    customCard.className = "visual-style-card" + (SELECTED_VISUAL_STYLE === "custom" ? " selected" : "");
    var customPreview = document.createElement("div"); customPreview.className = "custom-style-preview"; customPreview.textContent = "Aa / 自定义";
    var customTitle = document.createElement("b"); customTitle.textContent = "自定义视觉风格";
    var customDesc = document.createElement("small"); customDesc.textContent = "在下方描述配色、材料感、排版和氛围。";
    customCard.appendChild(customPreview); customCard.appendChild(customTitle); customCard.appendChild(customDesc);
    customCard.onclick = function () { SELECTED_VISUAL_STYLE = "custom"; VISUAL_STYLE_SOURCE = "user"; renderVisualStyles(); };
    customItems.appendChild(customCard); customSection.appendChild(customHeading); customSection.appendChild(customItems); host.appendChild(customSection);
  }

  function renderAnalysisDecision() {
    byId("analysis-yes").classList.toggle("selected", ANALYSIS_REQUIRED === true);
    byId("analysis-no").classList.toggle("selected", ANALYSIS_REQUIRED === false);
    byId("analysis-config").classList.toggle("locked-section", ANALYSIS_REQUIRED !== true);
    byId("generation-log").textContent = ANALYSIS_REQUIRED === false
      ? "已选择不补充专业分析图；保存后将跳过生图，直接进入内容盘点。"
      : (ANALYSIS_REQUIRED === null ? "请先明确是否需要专业分析图。" : "");
  }

  function renderIntakeSummary() {
    var manifest = STATE.source_manifest;
    var synthesis = STATE.source_synthesis;
    if (!manifest) {
      byId("intake-summary").textContent = "尚未导入资料。";
      return;
    }
    var lines = ["已归档 " + manifest.source_count + " 个文件/资产。"];
    if (manifest.duplicate_groups && manifest.duplicate_groups.length) lines.push("检测到重复组：" + manifest.duplicate_groups.length);
    lines.push("AI 梳理状态：" + ((synthesis && synthesis.status) || "未生成"));
    byId("intake-summary").textContent = lines.join("\n");
  }

  function renderTemplates() {
    var grid = byId("template-grid");
    grid.innerHTML = "";
    var free = document.createElement("div");
    free.className = "template-card" + (!SELECTED_TEMPLATE ? " selected" : "");
    free.innerHTML = "<b>0 · 自由设计</b><p>不锁定现有模板。</p>";
    free.onclick = function () { SELECTED_TEMPLATE = ""; renderTemplates(); };
    grid.appendChild(free);
    (STATE.templates || []).forEach(function (template) {
      var card = document.createElement("div");
      card.className = "template-card" + (SELECTED_TEMPLATE === template.id ? " selected" : "");
      var title = document.createElement("b");
      title.textContent = template.number + " · " + template.id;
      var desc = document.createElement("p");
      desc.textContent = template.summary || template.path;
      card.appendChild(title);
      card.appendChild(desc);
      card.onclick = function () { SELECTED_TEMPLATE = template.id; renderTemplates(); };
      grid.appendChild(card);
    });
  }

  function renderAnalysisLibrary() {
    var library = STATE.analysis_library || {};
    var styleGrid = byId("analysis-style-grid");
    var domainTabs = byId("analysis-domain-tabs");
    styleGrid.innerHTML = "";
    domainTabs.innerHTML = "";
    if (!(library.styles || []).length) {
      styleGrid.textContent = "分析图库尚未编译。";
      return;
    }
    (library.styles || []).forEach(function (style, index) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "analysis-style-card" + (ANALYSIS_STYLE_ID === style.id ? " selected" : "");
      var preview = document.createElement("img");
      preview.src = style.preview_url || "";
      preview.alt = style.name_zh || style.id;
      var title = document.createElement("b");
      title.textContent = (index + 1) + " · " + (style.name_zh || style.id);
      var detail = document.createElement("span");
      detail.textContent = style.item_count + " 种分析图";
      card.appendChild(preview); card.appendChild(title); card.appendChild(detail);
      if (style.id === library.default_style_id) {
        var badge = document.createElement("span"); badge.className = "recommend-badge"; badge.textContent = "推荐"; card.appendChild(badge);
      }
      card.onclick = function () { ANALYSIS_STYLE_ID = style.id; renderAnalysisLibrary(); };
      styleGrid.appendChild(card);
    });

    var domains = library.domains || [];
    if (!domains.some(function (domain) { return domain.id === ANALYSIS_DOMAIN_ID; })) {
      ANALYSIS_DOMAIN_ID = "";
    }
    domains.forEach(function (domain) {
      var tab = document.createElement("button");
      tab.type = "button";
      tab.className = "analysis-domain-tab" + (ANALYSIS_DOMAIN_ID === domain.id ? " active" : "");
      tab.textContent = domain.name_zh;
      tab.onclick = function () { ANALYSIS_DOMAIN_ID = domain.id; renderAnalysisLibrary(); };
      domainTabs.appendChild(tab);
    });
  }

  function renderImages() {
    var picker = byId("reference-images");
    picker.innerHTML = "";
    var selected = ((STATE.selection || {}).reference_images || []);
    (STATE.images || []).forEach(function (image) {
      var label = document.createElement("label");
      label.className = "image-choice";
      var input = document.createElement("input");
      input.type = "checkbox";
      input.value = image.path.replace(/^images\//, "");
      input.checked = selected.indexOf(input.value) >= 0;
      var preview = document.createElement("img");
      preview.src = image.url;
      preview.alt = image.name;
      var name = document.createElement("span");
      name.textContent = image.name;
      label.appendChild(input); label.appendChild(preview); label.appendChild(name);
      picker.appendChild(label);
    });
    if (!(STATE.images || []).length) picker.textContent = "尚无可用图片，请先导入效果图。";
  }

  function selectedReferences() {
    return Array.prototype.slice.call(byId("reference-images").querySelectorAll("input:checked"))
      .map(function (input) { return input.value; });
  }

  function collectSelection() {
    var visualStyle = SELECTED_VISUAL_STYLE || RECOMMENDED_VISUAL_STYLE;
    var visualSource = SELECTED_VISUAL_STYLE ? (VISUAL_STYLE_SOURCE || "user") : "auto";
    return {
      visual_style: visualStyle,
      visual_style_source: visualSource,
      template_id: SELECTED_TEMPLATE,
      custom_style_description: byId("custom-style").value,
      analysis_required: ANALYSIS_REQUIRED,
      analysis_selection_confirmed: ANALYSIS_REQUIRED === false || (
        ANALYSIS_REQUIRED === true && Boolean(ANALYSIS_STYLE_ID) && Boolean(ANALYSIS_DOMAIN_ID)
      ),
      analysis_pack_id: "",
      analysis_library_id: ((STATE.analysis_library || {}).library_id || ""),
      analysis_style_id: ANALYSIS_REQUIRED ? ANALYSIS_STYLE_ID : "",
      analysis_domain_id: ANALYSIS_REQUIRED ? ANALYSIS_DOMAIN_ID : "",
      analysis_item_ids: [],
      reference_images: ANALYSIS_REQUIRED ? selectedReferences() : [],
      provider_profile: byId("provider-profile").value
    };
  }

  function saveSelection() {
    return request("/api/workflow/selection", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectSelection())
    }).then(function () { toast("选择已保存"); return loadState(); });
  }

  function runAnalysis(dryRun) {
    if (ANALYSIS_REQUIRED !== true) {
      toast("只有选择“需要专业分析图”后才能运行生图");
      return Promise.resolve();
    }
    var button = dryRun ? byId("dry-run-analysis") : byId("generate-analysis");
    setBusy(button, true, dryRun ? "验证中…" : "所选图片生成中…");
    return saveSelection().then(function () {
      return request("/api/workflow/generate-analysis", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign(collectSelection(), { dry_run: dryRun }))
      });
    }).then(function (data) {
      byId("generation-log").textContent = data.stdout || "完成";
      toast(dryRun ? "离线请求验证通过" : "所选分析图生成完成");
      return loadState();
    }).catch(function (error) {
      byId("generation-log").textContent = error.message;
      toast(error.message);
    }).finally(function () { setBusy(button, false); });
  }

  function pageTemplate(index) {
    return {
      page_id: "P" + String(index + 1).padStart(2, "0"),
      title: "新页面",
      core_message: "填写本页核心信息",
      body: "",
      source_refs: ["source_manifest.json"],
      images: []
    };
  }

  function imageUrl(filename) {
    var found = (STATE.images || []).find(function (image) { return image.name === filename; });
    return found ? found.url : "";
  }

  function field(labelText, value, onInput, multiline) {
    var label = document.createElement("label");
    label.appendChild(document.createTextNode(labelText));
    var input = multiline ? document.createElement("textarea") : document.createElement("input");
    if (multiline) input.rows = 3;
    input.value = value == null ? "" : String(value);
    input.oninput = function () { onInput(input.value); };
    label.appendChild(input);
    return label;
  }

  function renderImageSlot(page, image, imageIndex, host) {
    var slot = document.createElement("div");
    slot.className = "image-slot";
    var preview = document.createElement("img");
    preview.src = imageUrl(image.filename || "") || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='200'%3E%3Crect width='100%25' height='100%25' fill='%23e9eeec'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' fill='%2364726e' font-family='Arial'%3E%E5%BE%85%E7%94%9F%E6%88%90/%E5%BE%85%E4%B8%8A%E4%BC%A0%3C/text%3E%3C/svg%3E";
    var fields = document.createElement("div");
    fields.className = "slot-fields";
    fields.appendChild(field("图片文件", image.filename || "", function (value) { image.filename = value; preview.src = imageUrl(value) || preview.src; }));
    fields.appendChild(field("图片来源", image.source || "ai", function (value) { image.source = value; }));
    fields.appendChild(field("分析图风格", image.analysis_style_id || "", function (value) { image.analysis_style_id = value; }));
    fields.appendChild(field("分析图大类", image.analysis_domain_id || ANALYSIS_DOMAIN_ID, function (value) { image.analysis_domain_id = value; }));
    fields.appendChild(field("提示词", image.prompt || "", function (value) { image.prompt = value; }, true));
    var actions = document.createElement("div");
    actions.className = "slot-actions";
    var upload = document.createElement("button");
    upload.className = "secondary"; upload.type = "button"; upload.textContent = "替换上传";
    upload.onclick = function () {
      var input = document.createElement("input"); input.type = "file"; input.accept = "image/*";
      input.onchange = function () {
        if (!input.files[0]) return;
        var form = new FormData(); form.append("image", input.files[0]);
        request("/api/workflow/upload-image", { method: "POST", body: form }).then(function (data) {
          image.filename = data.name; image.source = "provided"; preview.src = data.url; toast("图片已上传");
        }).catch(function (error) { toast(error.message); });
      };
      input.click();
    };
    var regen = document.createElement("button");
    regen.className = "secondary"; regen.type = "button"; regen.textContent = "重新生图";
    regen.onclick = function () {
      setBusy(regen, true, "生成中…");
      request("/api/workflow/regenerate-image", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: image.filename, prompt: image.prompt, reference_images: selectedReferences() })
      }).then(function () { toast("图片已重新生成"); return loadState(); })
        .catch(function (error) { toast(error.message); })
        .finally(function () { setBusy(regen, false); });
    };
    var remove = document.createElement("button");
    remove.className = "danger"; remove.type = "button"; remove.textContent = "删除图片槽";
    remove.onclick = function () { page.images.splice(imageIndex, 1); renderOutline(); };
    actions.appendChild(upload); actions.appendChild(regen); actions.appendChild(remove);
    fields.appendChild(actions);
    slot.appendChild(preview); slot.appendChild(fields); host.appendChild(slot);
  }

  function renderOutline() {
    var host = byId("outline-cards");
    host.innerHTML = "";
    (OUTLINE.pages || []).forEach(function (page, index) {
      var card = document.createElement("article");
      card.className = "page-card"; card.draggable = true; card.dataset.index = index;
      card.ondragstart = function () { card.classList.add("dragging"); };
      card.ondragend = function () { card.classList.remove("dragging"); };
      card.ondragover = function (event) { event.preventDefault(); };
      card.ondrop = function (event) {
        event.preventDefault();
        var dragging = host.querySelector(".dragging");
        if (!dragging) return;
        var from = Number(dragging.dataset.index); var to = index;
        var moved = OUTLINE.pages.splice(from, 1)[0]; OUTLINE.pages.splice(to, 0, moved); renderOutline();
      };
      var toolbar = document.createElement("div"); toolbar.className = "page-toolbar";
      var handle = document.createElement("span"); handle.className = "drag-handle"; handle.textContent = "☰ " + (page.page_id || ("P" + (index + 1)));
      var remove = document.createElement("button"); remove.className = "danger"; remove.type = "button"; remove.textContent = "删除页面";
      remove.onclick = function () { OUTLINE.pages.splice(index, 1); renderOutline(); };
      toolbar.appendChild(handle); toolbar.appendChild(remove); card.appendChild(toolbar);
      var grid = document.createElement("div"); grid.className = "grid two";
      grid.appendChild(field("页码", page.page_id || "", function (value) { page.page_id = value; }));
      grid.appendChild(field("标题", page.title || "", function (value) { page.title = value; }));
      grid.appendChild(field("核心信息", page.core_message || "", function (value) { page.core_message = value; }, true));
      grid.appendChild(field("正文", page.body || "", function (value) { page.body = value; }, true));
      grid.appendChild(field("来源依据（每行一个）", (page.source_refs || []).join("\n"), function (value) {
        page.source_refs = value.split(/\r?\n/).map(function (item) { return item.trim(); }).filter(Boolean);
      }, true));
      card.appendChild(grid);
      (page.images || []).forEach(function (image, imageIndex) { renderImageSlot(page, image, imageIndex, card); });
      var addImage = document.createElement("button"); addImage.className = "secondary"; addImage.type = "button"; addImage.textContent = "增加图片槽";
      addImage.onclick = function () { page.images = page.images || []; page.images.push({ source: "ai", filename: "", prompt: "", reference_images: [] }); renderOutline(); };
      card.appendChild(addImage); host.appendChild(card);
    });
    if (!(OUTLINE.pages || []).length) host.textContent = "尚无逐页大纲。等待 AI 生成，或点击“增加页面”手动开始。";
  }

  function initStyles() {
    request("/api/catalogs").then(function (catalogs) {
      VISUAL_STYLE_CATALOG = catalogs.visual_styles || [];
      renderVisualStyles();
    }).catch(function (error) { toast(error.message); });
  }

  byId("intake-form").onsubmit = function (event) {
    event.preventDefault(); var button = event.submitter || event.target.querySelector("button[type=submit]");
    setBusy(button, true, "导入处理中…");
    request("/api/workflow/intake", { method: "POST", body: new FormData(event.target) })
      .then(function () { toast("资料已导入，等待 AI 完成 source_synthesis.json"); event.target.reset(); return loadState(); })
      .catch(function (error) { toast(error.message); })
      .finally(function () { setBusy(button, false); });
  };
  byId("save-selection").onclick = saveSelection;
  byId("analysis-yes").onclick = function () { ANALYSIS_REQUIRED = true; renderAnalysisDecision(); };
  byId("analysis-no").onclick = function () {
    ANALYSIS_REQUIRED = false;
    ANALYSIS_STYLE_ID = "";
    ANALYSIS_DOMAIN_ID = "";
    renderAnalysisDecision();
    renderAnalysisLibrary();
  };
  byId("dry-run-analysis").onclick = function () { runAnalysis(true); };
  byId("generate-analysis").onclick = function () { runAnalysis(false); };
  byId("reload-outline").onclick = loadState;
  byId("add-page").onclick = function () { OUTLINE.pages.push(pageTemplate(OUTLINE.pages.length)); renderOutline(); };
  byId("save-outline").onclick = function () {
    request("/api/workflow/outline", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(OUTLINE)
    }).then(function () { toast("大纲已保存，旧确认已失效"); return loadState(); }).catch(function (error) { toast(error.message); });
  };
  byId("confirm-outline").onclick = function () {
    var button = byId("confirm-outline"); setBusy(button, true, "确认中…");
    request("/api/workflow/outline/confirm", { method: "POST" })
      .then(function () { toast("大纲已确认，正式生成已解锁"); return loadState(); })
      .catch(function (error) { toast(error.message); })
      .finally(function () { setBusy(button, false); });
  };

  initStyles();
  loadState();
}());
