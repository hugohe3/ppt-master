> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core and [`pptx-structure-interface.md`](./pptx-structure-interface.md) for the SVG metadata contract.

# Executor Structured Template Branch

Conditional Executor authority for `template_reuse_scope: mirror|layout` with `pptx_structure.mode: structured`.

**Trigger**: the lock selects structured template reuse.

**Hard rule — package structure, not information structure**: this branch owns reusable Master/Layout atoms, placeholders, slots, and prototype topology; [`executor-structure.md`](./executor-structure.md) independently owns Slide-local qualitative composition, and neither implies the other.

## 1. Template Reuse Rules

### 1.0 Template Context Load

| Context | Load policy |
|---|---|
| `templates/design_spec.md` | Reuse in a valid context; after invalidation read it once with the planning artifacts |
| Current page mapping | The retained `spec_lock.md page_layouts` row; a page change needs no file load |
| Selected prototype SVG | Read the complete `templates/<basename>.svg` once per valid context and reuse it until a known change |

**Hard rule**: the complete Slide prototype SVG is authoritative and already resolves its Master + Layout; standalone Master/Layout definition SVGs are invalid; never author from a roster, manifest, sidecar, filename, or summary (manifest/text-slot files are tool metadata whose absence neither invalidates a legacy workspace nor permits text-topology changes). Resolve each page's prototype directly from its `page_layouts` row — `mirror` → §1.1 (the workspace must support `replication_mode: mirror`); `layout` → resolve `P<NN>: <basename>`, retain the structure system, apply the re-skin/reflow rules below; a missing row stops (adaptive mode still needs one selected input prototype, and there is no filename/page-type fallback). A mapping change stops and returns to Strategist to update the plan, read back and validate, then load the new prototype.

**Default — re-skin `layout` (may override when the application plan keeps template visuals and the lock reflects them)**: inherit geometry, label/legend placement, and series encoding; repaint gradients, shadows, fills, and strokes from the current style/lock. `mirror` preserves visuals under §1.1.

**Hard rule — font size is skin, not geometry (non-mirror)**: a template's hardcoded `font-size` values are never inherited. Build a per-page text inventory from §IX and the current notes; map every structural role and reusable slot (`title`, `subtitle` / `lead`, `body`, `annotation`, `footnote` / `page_number`, reusable hero or emphasis slots) to a declared `spec_lock.typography` role — a missing role returns upstream, never a numerically close one; choose the anchor or one value within `±2` px before placing text (only a Slide-local, non-slot Hero/Display element may use `executor-base.md`'s sparse exception; reusable slots never do); lay out from those sizes — line height, wrapped lines, child `y` / `dy`, card padding and height, column gaps, image/chart area — and reflow containers and local geometry with the bounded type rather than starting from a template size. Do not repaginate, split, or drop content; a value still outside the band returns upstream under `executor-base.md` §2.1.

### 1.1 Mirror reuse — literal page replacement

When the lock records `template_reuse_scope: mirror` (the workspace's `replication_mode: mirror` is a prerequisite, never the trigger, and never forces mirror when the lock says `layout` or `style`):

1. **Per-page reference**: Strategist selected one mirror page per project page in `page_layouts` (`P04: 015_content`) from `design_spec.md §V` descriptions.
2. **Copy, don't fill**: start from the retained full mirror SVG and edit slide-specific text in place, preserving every ordinary non-text element and every `data-pptx-*` structure attribute verbatim; the sole exception is a JSON-first Chart/Table whose marker id/kind/authority and metadata stay while its derived preview may regenerate from that JSON. Do not reopen the same path + SHA because another page selects it.
3. **Editable**: the semantic slot mapping and visible string values already carried by `<text>` / `<tspan>` nodes (title, body, captions, KPI labels, dates, page numbers). Keep the number, order, nesting, and all attributes of every text node; never merge, split, move a string between nodes, add a tspan, or delete an empty carrier — checker and export validate topology and prototype hashes.
4. **Untouchable**: positions, sizes, fonts, colors, fills, strokes, gradients, which image each ordinary `<image>` points at, grouping, sprite-sheet `<svg viewBox>` wrappers, decoration, `<use data-icon>` markers, authoritative Chart/Table JSON. The `href` path is not the image: normalize a bare `href="cover_bg.png"` to the exact `href="../images/<name>"` after Step 3 relocates the bytes — a transport rewrite, not a visual edit.
5. **Content fit**: when the replacement needs a different number of segments or items, do not merge, split, drop, or restructure — report `warning: P<NN> content does not fit mirror reference <basename>; choose another prototype or change template_reuse_scope to layout/style` and return to Strategist.
6. **Visible text**: mirror SVGs may carry literal source text rather than `{{...}}` markers; edit in place, retaining imported `data-pptx-placeholder` identity and exact topology.
7. **Output filename**: standard `<index>_<page_name>.svg` with the project page index; the mirror filename is the reference, not the output.

Chart, Table, and qualitative topology inside a mirror SVG are already authored: replace only permitted text and never redraw from a catalog or grammar; a JSON-first object may refresh its approximate preview from unchanged JSON without metadata, bounds, marker, slot, or visual drift; a mirror template normally omits `page_visualizations`, and legacy `page_charts` never overrides fidelity. **Legacy template boundary**: a template with missing root Master identity, direct atomic placeholders, `data-pptx-layout-kind`, unmapped `baseline`, `preserve`, or `layout_strategy: distill` is never a fallback input — stop and create a new workspace through [`create-template`](../workflows/create-template.md).

**Required output before each page**:

```
📝 **Template mapping**: `templates/03a_content_image_text.svg` (free-design routes may use "None")
🎯 **Adherence rules / application plan**: [specific description]
```

Content pages: the template defines only header/footer and the content area is free. No template is allowed only on free-design or brand-only routes.

### 1.2 PowerPoint Master / Layout Mapping

Applies only when the lock records `template_reuse_scope: mirror|layout`: `page_layouts` selects the input prototype, `pptx_masters` / `pptx_layouts` declare unique reusable output definitions, and `page_pptx_layouts` assigns every page before the first is drawn. `style`, free-design, and brand-only routes use `mode: flat`, omit all four sections, and keep every object Slide-local.

- **Hard rule — reuse-scope route**: `mirror|layout` requires `mode: structured`; `style` requires `flat` even with a template vocabulary. A missing mode, legacy values (`baseline`, `template`, `preserve`), `layout_strategy`, Layout-kind fields, partial mappings, or old direct placeholders stop generation — create a new workspace, never upgrade in place.
- **Hard rule — root identity**: a `page_pptx_layouts` row binds the page to one `pptx_layouts` key, which supplies its Master key, Layout picker name, and prototype source; write the Master key/name and Layout key/name on the root `<svg>`. A Layout key belongs to one Master and is globally unique.
- **Hard rule — atomic fixed layers**: every `data-pptx-layer="master|layout"` visual is one direct root atom compiling to one DrawingML object; an ordinary marked `<g>` is forbidden, and one validated compact `preset_shape_svg.py` `<g>` is the sole exception. Push supported transforms, paint, opacity, and z-order of source groups into atomic children. Repeat the identical ordered Master atom contract on every page of that Master and the identical Layout atom contract on every page sharing `(master, layout)`.
- **Hard rule — paint order**: Master background atoms, Layout background atoms, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local groups.
- **Mandatory — slots**: a reusable slot is one direct root `<g id>` with `data-pptx-placeholder` and one positive `data-pptx-bounds` (the reusable Layout default and the module boundary at once) containing exactly one compatible direct drawable child marked `data-pptx-carrier="true"`, which export unwraps into the real placeholder; decoration goes to a root Layout atom, page-specific labels to another slot or Slide-local group. Preserve imported `data-pptx-idx`; otherwise omit the title index and assign unique indices only where repeated roles need them; pages sharing a Layout key repeat the same slot ids, types, indices, default bounds, and binding modes while current text, crop, and carrier geometry may differ. A genuinely composite region may use `<g data-pptx-placeholder="object" data-pptx-binding="proxy">` with positive bounds (Slide-local visuals plus one hidden transparent proxy) — `object` only. **Forbidden — dummy carriers**: never tiny text, near-transparent glyphs, or background-colored punctuation; leave a blank text carrier empty (export emits an invisible U+200B run) or use the proxy; surface a `strict` mismatch instead of hiding it.
- **Zero-slot Layout**: covers, posters, and fixed visual pages still declare Master/Layout and fixed atoms without manufacturing a full-page `object` slot or `utility` identity.
- **Mandatory — per-page slot coverage**: declare a slot for each standard role the page actually has — heading `title`, cover tagline `subtitle`, page number `slide-number`, running footer `footer`, hero/content image `picture`, one merged body frame `body`; zero slots is valid only for a genuinely fixed composition, never as the default; pages sharing a key ship the same slot set. **Hard rule — variable content**: page-varying text or images are carried by a slot or stay Slide-local, never become fixed Layout atoms.
- **Mandatory — layer coverage**: mark the deck-wide background and every-page chrome (footer bar, running logo) `master`, and the static framing that defines this key's composition (header rule, divider band, zone panels, chrome repeated on content pages but absent from the cover) `layout`; a page with zero marks exports a bare Master and empty Layout.
- **Layout identity and adherence**: keys differ in fixed atoms or slot topology/default bounds/binding modes, never in wording, imagery, crop, or Slide-local geometry; identical contracts share one key. Strict preserves atoms and slot ids/types/indices/bounds/bindings (`layout` may still change current text/tspans, line height, crop, and carrier-local geometry inside those bounds; `mirror` is topology-frozen); adaptive keeps the prototype Master and realizes only the Layout definition and assignment already declared in the lock. A needed change to atoms or slot topology stops the page and returns to Strategist to declare a new key, update definition and assignments, and validate; content alone is never a new Layout. Mark only genuinely reusable fixed framing as an atom — titles, body, metrics, chart marks, images, and page-specific groups stay in slots or Slide-local groups; the exporter never infers structure.
- **Background ownership**: deck-wide default = a direct full-canvas solid `<rect data-pptx-layer="master">` identical on every page; page-type default = `data-pptx-layer="layout"` on every page sharing the key; one-page exception = `data-pptx-layer="slide"`. These export as real `p:bg`; gradients, patterns, images, textures, and overlay panels stay explicit shapes or pictures, and the flat-mode background promotion rule does not apply.

---

## 2. Per-page Structured Lookup

**`page_layouts` (`mirror` / `layout` only)**: before drawing, take the page's row (`P04: 03a_content_image_text`) and resolve the complete SVG in the selected template directory (§1.0 decides whether to read or reuse it; a `reference_set` fingerprint may diagnose an uncertain path but is not required). The basename must match a real file — otherwise stop and report the invalid mapping; neither strict nor adaptive falls back to free design. A missing row, or a missing section under `mirror|layout`, stops with an upstream contract error; under `style` the section must be absent. Never invent an entry or assume structure because `templates/` exists.

**`page_pptx_layouts` (`mirror|layout` only)**: under `flat` (including `style`) skip this and the scaffold, with `pptx_masters`, `pptx_layouts`, `page_layouts`, and the metadata all absent and each root declaring `data-pptx-page-role`. Otherwise `mode` must be `structured` (any other value is rejected — create a new workspace, never migrate); read `P<NN>: <layout_key>`, resolve the key in `pptx_layouts` and its Master in `pptx_masters` (missing or partial mappings stop), write the matching root keys and picker names, and write no `data-pptx-layout-kind` or `data-pptx-page-role`. Strict matches the prototype exactly; adaptive keeps the Master and realizes the declared Layout, stopping and returning upstream when atoms or slots must change. A key may repeat across non-adjacent pages only with identical atoms and slots.

```xml
<svg viewBox="…"
     data-pptx-master="<master-key>" data-pptx-master-name="<master-name>"
     data-pptx-layout="<layout-key>" data-pptx-layout-name="<layout-name>">
  <rect id="master-bg" data-pptx-layer="master" …/>              <!-- one atomic Master object -->
  <text id="master-footer" data-pptx-layer="master" …>…</text>   <!-- no Master/Layout g -->
  <path id="layout-rule" data-pptx-layer="layout" …/>            <!-- one atomic Layout object -->
  <g id="title-slot" data-pptx-placeholder="title" data-pptx-bounds="60 36 1160 64">
    <text id="title-carrier" data-pptx-carrier="true" …>…</text>
  </g>
  <g id="body-slot" data-pptx-placeholder="body" data-pptx-idx="1" data-pptx-bounds="60 120 470 500">
    <text id="body-carrier" data-pptx-carrier="true" …>…</text>
  </g>
  <g id="picture-slot" data-pptx-placeholder="picture" data-pptx-idx="2" data-pptx-bounds="570 120 650 500">
    <image id="picture-carrier" data-pptx-carrier="true" …/>
  </g>
  <g id="content-block-1" data-pptx-bounds="60 120 470 500">…</g>   <!-- one group per logical content unit -->
  <g id="content-block-2" data-pptx-bounds="570 120 650 500">…</g>
</svg>
```

Master/Layout atoms and slot groups are direct root children preceding ordinary content groups; structural metadata nested inside a content group fails export. Flat pages use ordinary top-level semantic groups only.
