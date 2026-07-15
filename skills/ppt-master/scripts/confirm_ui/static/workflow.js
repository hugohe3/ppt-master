(function () {
  "use strict";

  var STATE = null;
  var OUTLINE = { schema_version: 2, pages: [] };
  var SELECTED_TEMPLATE = "";

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
      renderIntakeSummary();
      renderTemplates();
      renderPacks();
      renderImages();
      OUTLINE = data.outline_draft || { schema_version: 2, pages: [] };
      renderOutline();
      var selection = data.selection || {};
      SELECTED_TEMPLATE = selection.template_id || "";
      byId("custom-style").value = selection.custom_style_description || "";
      byId("provider-profile").value = selection.provider_profile || "gptimage2.0-1K-low";
      if (selection.analysis_pack_id) byId("analysis-pack").value = selection.analysis_pack_id;
      renderTemplates();
      byId("outline-status").textContent = data.analysis_ready
        ? (data.outline_draft ? "大纲可编辑；保存后需要重新确认。" : "等待 AI 写入 outline_draft.json，也可手动增加页面。")
        : "所选分析图包尚未全部生成，暂不能最终确认大纲。";
      byId("confirm-status").textContent = data.outline_ready && data.outline_confirmed
        ? "当前大纲已确认，正式生成已解锁。"
        : "尚未确认：" + (data.outline_message || "请先完成逐页大纲");
    }).catch(function (error) { toast(error.message); });
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

  function renderPacks() {
    var select = byId("analysis-pack");
    var current = select.value;
    select.innerHTML = '<option value="">不使用分析图包</option>';
    (STATE.analysis_packs || []).forEach(function (pack) {
      var option = document.createElement("option");
      option.value = pack.id;
      option.textContent = pack.name_zh || pack.id;
      option.title = pack.description_zh || "";
      select.appendChild(option);
    });
    select.value = current || ((STATE.selection || {}).analysis_pack_id || "");
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
    return {
      visual_style: byId("visual-style").value,
      template_id: SELECTED_TEMPLATE,
      custom_style_description: byId("custom-style").value,
      analysis_pack_id: byId("analysis-pack").value,
      reference_images: selectedReferences(),
      provider_profile: byId("provider-profile").value
    };
  }

  function saveSelection() {
    return request("/api/workflow/selection", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectSelection())
    }).then(function () { toast("选择已保存"); return loadState(); });
  }

  function runPack(dryRun) {
    var button = dryRun ? byId("dry-run-pack") : byId("generate-pack");
    setBusy(button, true, dryRun ? "验证中…" : "整套生成中…");
    return saveSelection().then(function () {
      return request("/api/workflow/generate-pack", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign(collectSelection(), { dry_run: dryRun }))
      });
    }).then(function (data) {
      byId("generation-log").textContent = data.stdout || "完成";
      toast(dryRun ? "离线请求验证通过" : "分析图包生成完成");
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
    fields.appendChild(field("分析包条目", image.analysis_item_id || "", function (value) { image.analysis_item_id = value; }));
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
      var select = byId("visual-style"); select.innerHTML = "";
      (catalogs.visual_styles || []).forEach(function (group) {
        (group.items || []).forEach(function (item) {
          var option = document.createElement("option"); option.value = item.id; option.textContent = item.label_zh || item.label || item.id; select.appendChild(option);
        });
      });
      var custom = document.createElement("option"); custom.value = "custom"; custom.textContent = "客制化"; select.appendChild(custom);
      if (STATE && STATE.selection && STATE.selection.visual_style) select.value = STATE.selection.visual_style;
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
  byId("dry-run-pack").onclick = function () { runPack(true); };
  byId("generate-pack").onclick = function () { runPack(false); };
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

  loadState().then(initStyles);
}());
