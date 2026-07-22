> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core and [`pptx-structure-interface.md`](./pptx-structure-interface.md) for the SVG metadata contract.

# Executor Structured Template Branch

Conditional Executor authority for `template_reuse_scope: mirror|layout` with `pptx_structure.mode: structured`.

**Trigger**: load only when the lock selects structured template reuse.

## 1. Template Reuse Rules

### 1.0 Template Context Load

| Context | Load policy |
|---|---|
| `templates/design_spec.md` | Strategist reads once; continuous Executor reuses it, fresh Executor reads it once |
| Current page delta | Run [`executor-base.md`](./executor-base.md) §2.1 immediately before that page |
| Selected prototype SVG | Read once on an absent/changed `reference_set` path + SHA; otherwise reuse it |

**Hard rule**: Page-context carries no prototype payload. `reference_set` identifies the authoritative complete SVG; never author from a roster, manifest, sidecar, filename, or summary alone.

Manifest/text-slot files are derived tool metadata, not model inputs. Missing metadata neither invalidates a legacy workspace nor permits text-topology changes.

**Mapping change**: stop and return to Strategist to update the owning plan; regenerate that page's delta before resuming, then load only a new/changed prototype fingerprint.

Resolve the per-page template SVG from `page_context.template.prototype`; the owning `spec_lock.md page_layouts` row remains authoritative. There is no filename/page-type fallback.

**Resolution order (per page):**

1. `template_reuse_scope: mirror` → see §1.1. The installed workspace must support `replication_mode: mirror`.
2. `template_reuse_scope: layout` → resolve `P<NN>: <basename>` from `page_layouts`, retain the structure system, and apply the non-mirror skin/reflow rules below.
3. `mirror` / `layout` with no current-page `page_layouts` row → stop; adaptive mode still requires one selected input prototype.

> Note: `page_layouts` disambiguates the multiple content variants a template may ship; missing mappings are contract errors.

**Default — re-skin `layout` (may override when the application plan keeps template visuals and the lock reflects them)**: inherit geometry, label/legend placement, and series encoding; otherwise repaint template gradients, shadows, fills, and strokes from the current style/lock. Template font sizes remain placeholders. `mirror` preserves visuals under §1.1.

**Font size is skin, not geometry (non-mirror).** A chart / layout template's hardcoded `font-size` values (often 11–16px, sized for the template's own dense placeholder text) are NOT inherited. Structural text and reusable slots start from their `spec_lock.md` role and stay within anchor `±2`px; only a qualifying Slide-local Hero/Display element follows the sparse exception in `executor-base.md`. Template placeholder px supplies neither a role anchor nor a sparse display value.

**Typography execution order (mandatory):**

1. Build a per-page text inventory from `design_spec.md §IX` + the current `notes/<NN>_*.md`.
2. Classify each text item before drawing. **Structural roles and reusable feature slots** (`title`, `subtitle` / `lead`, `body`, `annotation`, `footnote` / `page_number`, reusable hero or emphasis slots) map to a declared `spec_lock.typography` size role. A missing semantic role returns upstream; do not borrow an unrelated size because it is numerically close. Only a Slide-local, non-slot Hero/Display element may use the sparse-size exception in [`executor-base.md`](./executor-base.md); reusable Layout slots never do.
3. For every mapped role or reusable slot, choose the role anchor or one contextual value within anchor `±2`px before placing the text. A qualifying Slide-local sparse display follows `executor-base.md` directly. Never start from a template `font-size` and then adjust it.
4. Layout from those chosen sizes: compute line-height, wrapped line count, child `y` / `dy`, card padding, card height, column gaps, and available image/chart area.
5. Reflow containers and local geometry together with the bounded role treatment; an inherited template slot never justifies leaving the declared band.

**Geometry and bounded type co-adapt**: widen or heighten the card, open spacing, recompute child `y` / `dy`, and choose within the mapped role's anchor `±2`px instead of inheriting the template's compact size. Page count and density remain the confirmed Strategist decision: do not repaginate, split, or drop content. If structural text or a reusable slot still needs a value outside the band, return upstream under [`executor-base.md`](./executor-base.md) §2.1; only qualifying Slide-local display text uses its sparse exception. Mirror instead preserves source typography under §1.1.

### 1.1 Mirror reuse — literal page replacement

When `spec_lock.md` records the AI-derived `template_reuse_scope: mirror`, Executor switches to a literal replacement path. The workspace capability `replication_mode: mirror` is a prerequisite, not the trigger by itself:

1. **Per-page reference selection** — Strategist selects one mirror page per project page via `spec_lock.md page_layouts` (e.g., `P04: 015_content`). The basename is the mirror filename without extension; Strategist made this choice by reading `design_spec.md §V Page Roster` descriptions, not by guessing.
2. **Copy, don't fill** — use the retained full mirror SVG as the starting point, then edit slide-specific text in place. Preserve every non-text element and every `data-pptx-*` structure attribute verbatim. Do not reopen the same path + SHA merely because another page selects it.
3. **What you may edit** — decide the semantic slot mapping and replacement text only. Change only visible string values already carried by `<text>` and `<tspan>` nodes that express slide-specific content (title, body, captions, KPI labels, dates, page numbers). Keep the number, order, nesting relationship, and **all attributes** of every `<text>` / `<tspan>` node unchanged. Never merge or split nodes, move a string between nodes, add a new tspan, or delete an empty carrier. `svg_quality_checker.py` and export validate attributes, topology, and prototype hashes against the complete prototype internally.
4. **What you must not touch** — element positions, sizes, fonts, colors, fills, strokes, gradients, **which image each `<image>` points at**, `<g>` grouping, sprite-sheet `<svg viewBox>` wrappers, decorative `<rect>` / `<path>` / `<circle>` / `<polygon>` shapes, `<use data-icon="...">` markers, embedded chart data structures. Mirror's value is preserving the source deck's visual identity — any geometric / decorative drift defeats the purpose. **The `href` path is not the image**: normalizing a bare `href="cover_bg.png"` to `href="../images/<name>"` (when Step 3 relocated the asset to `images/`) points at the *same* image and changes nothing visual — that is an allowed path fix, not a fidelity edit. Leaving the bare href as-is is also fine; the exporter and live preview resolve bare hrefs against `images/` either way.
5. **Content fit** — if the replacement needs a different number of text segments/items, do not merge/split nodes, drop sourced content, or restructure the grid. Report `warning: P<NN> content does not fit mirror reference <basename>; choose another prototype or change template_reuse_scope to layout/style`, then return to Strategist to select the prototype or scope and update the planning mappings.
6. **Visible text editing** — mirror SVGs may keep literal source text rather than `{{...}}` authoring markers. Edit values in place while retaining imported semantic `data-pptx-placeholder` identity and exact text topology.
7. **Output filename** — follow the standard project SVG naming convention (`<NN>_<page_name>.svg` where `<NN>` matches the project page index, not the mirror source index). The mirror filename is the *reference*, not the *output*.

**Detecting mirror mode**: read `page_context.template.reuse_scope` from the current page delta. `replication_mode: mirror` in the installed template only determines whether that derived scope is legal; it must never force mirror behavior when the lock records `layout` or `style`.

**Mirror + chart pages**: chart structures inside a mirror SVG are already drawn (axis, series, labels). Treat them as visual references — replace the data labels and series text content to match the project's chart spec, but do not redraw the chart from a `templates/charts/<name>.svg` baseline. A mirror template's `page_charts` entries are normally absent for this reason.

**Legacy template boundary**: A template with missing root Master identity, direct atomic placeholders, `data-pptx-layout-kind`, unmapped `baseline`, `preserve`, or `layout_strategy: distill` is not a fallback input. Stop and create a new current workspace through [`create-template`](../workflows/create-template.md) before generation.

### Page-Template Mapping Declaration (Required Output)

Before generating each page, output which template is used:

```
📝 **Template mapping**: `templates/03a_content_image_text.svg` (free-design routes may use "None")
🎯 **Adherence rules / layout strategy**: [specific description]
```

- **Content pages**: template defines only header/footer; content area is free
- **No template**: allowed only on free-design or brand-only routes

### 1.2 PowerPoint Master / Layout Mapping

This section applies only when a deck/layout template's AI-derived lock records `template_reuse_scope: mirror|layout`. `page_layouts` selects the input SVG prototype, `pptx_masters` / `pptx_layouts` declare unique reusable output definitions, and `page_pptx_layouts` assigns every generated page before the first page is drawn. `template_reuse_scope: style`, free-design, and brand-only routes use `pptx_structure.mode: flat`, omit all four sections, skip the rest of §1.2, and keep every SVG object Slide-local.

**Hard rule — reuse-scope route**: `template_reuse_scope: mirror|layout` requires `pptx_structure.mode: structured`. `template_reuse_scope: style` requires `mode: flat` even though a template supplied its visual vocabulary. Missing mode or legacy values (`baseline`, `template`, `preserve`), `layout_strategy`, Layout-kind fields, partial mappings, and old direct placeholders stop generation. Create a new template workspace through [`create-template`](../workflows/create-template.md); do not upgrade the active SVG project in place.

**Hard rule — root identity**: A `page_pptx_layouts` row binds the page to one key in `pptx_layouts`; that unique definition supplies its Master key, Layout picker name, and prototype source. Put the declared Master key/name and Layout key/name on the root SVG. A Layout key belongs to exactly one Master and remains globally unique.

**Hard rule — atomic fixed layers**: Every `data-pptx-layer="master|layout"` visual is one direct root semantic atom that compiles to one DrawingML object. An ordinary marked `<g>` is forbidden; one validated compact authored-preset `<g>` emitted by `preset_shape_svg.py` is the sole group exception because it compiles to one native shape. When reconstructing source PPTX groups, recursively push supported transforms, paint, opacity, and z-order into atomic children. Repeat the identical ordered Master atom contract on every page using that Master and the identical ordered Layout atom contract on every page sharing that `(master, layout)` pair.

**Hard rule — PowerPoint paint order**: Direct children appear in this order: Master background atoms, Layout background atoms, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local content groups. Backgrounds are the inheritance plane beneath all shapes.

**Mandatory — slot authoring**: A reusable content slot is one direct root `<g id>` carrying `data-pptx-placeholder` and one positive `data-pptx-bounds`; the same design zone is both the reusable Layout default and the slot module boundary. A normal slot contains exactly one compatible direct drawable child marked `data-pptx-carrier="true"`. Export unwraps that child into the real Slide placeholder binding. Decorations do not belong in the slot; move reusable decoration to a root Layout atom and keep page-specific labels/captions in another bounded slot or Slide-local group.

**Mandatory — slot identity**: Preserve imported `data-pptx-idx` values where available; otherwise omit the title index and assign unique indices only where repeated roles need disambiguation. Pages sharing one Layout key repeat the same slot ids/types/effective indices/default bounds/binding modes. Current text, crop, and Slide-local carrier geometry may differ.

**Composite proxy fallback**: A genuinely composite region may use a direct `<g data-pptx-placeholder="object" data-pptx-binding="proxy">` with positive bounds. Its visible group remains Slide-local and export creates one hidden transparent matching placeholder proxy. This downgrade is valid only for `object`; do not use it for an ordinary title, body, picture, chart, table, or media slot.

**Forbidden — dummy carriers**: Never satisfy a carrier slot with tiny text, near-transparent glyphs, background-colored punctuation, or other fake content. Leave an intentionally blank text carrier empty/whitespace-only—the exporter emits a legal invisible U+200B run—or use the composite `object` proxy contract. If `strict` prototype binding cannot represent the completed composition, surface the mismatch; select a compatible prototype or create an explicit adaptive Layout instead of hiding the conflict.

**Zero-slot Layout**: A Layout may have no slot groups. Covers, posters, and fixed visual pages still declare their named Master/Layout and fixed atoms. Do not manufacture a full-page `object` slot or empty `utility` identity.

**Mandatory — per-page slot coverage**: On every mapped page, declare a slot for each standard role the page actually has: the page heading as `title`, a cover tagline as `subtitle`, the page number as `slide-number`, running footer text as `footer`, a hero / content image as `picture`, and a body block already authored as one merged text frame as `body`. A page shipping zero slots exports a Layout with no insertable placeholders — valid only for a genuinely fixed composition (see Zero-slot Layout above), never as the deck-wide default. Pages sharing one layout key ship the same slot set.

**Hard rule — variable slot content**: “Per-page headings never stay Slide-local by default” means authoring them as `title` / `subtitle` slots; it never permits page-varying text or images to become fixed Layout atoms. Any such value that varies across pages sharing one Layout key MUST be carried by a slot or remain Slide-local.

**Mandatory — master/layout layer coverage**: On every mapped page, mark the deck-wide background and every-page chrome (footer bar, running logo) `data-pptx-layer="master"`, and mark the static framing that defines this layout key's composition (header rule, divider band, zone panels — including chrome repeated on every content page but absent from the cover) `data-pptx-layer="layout"`. A mapped page with zero `data-pptx-layer` marks exports a bare Master and an empty Layout — the layer marks, not the slide content, give each Layout its visible design.

**Layout identity**: Different keys differ in fixed Layout atoms or slot topology/default bounds/binding modes. Identical contracts should share one key. Current wording, imagery, crop, and Slide-local geometry never define identity.

**Template adherence**: Strict preserves reusable Master/Layout atoms and slot ids/types/indices/default bounds/bindings. Under `layout`, the application plan may still change current text/tspans, line height, crop, and carrier-local geometry inside those bounds; `mirror` remains topology-frozen. Adaptive keeps the prototype Master and changes reusable atoms or slots only under a new explicit Layout key/name, written to `spec_lock.md pptx_layouts` while authoring the first affected page. Changing only content is not a new Layout.

**Layout-content boundary**: Mark only genuinely reusable fixed framing as a Master/Layout atom. Concrete titles, body copy, metrics, chart marks, images, and page-specific groups remain inside slot groups or ordinary Slide-local content groups. The exporter never infers or clusters structure.

**Background ownership**:

| Scope | SVG authoring |
|---|---|
| Deck-wide default | Direct full-canvas solid `<rect data-pptx-layer="master">` repeated identically on every page |
| Page-type default | Direct full-canvas solid `<rect data-pptx-layer="layout">` repeated on every page sharing that layout key |
| One-page exception | Direct full-canvas solid `<rect data-pptx-layer="slide">` |

The exporter writes these solid fills as real Master/Layout/Slide `p:bg`, not selectable full-canvas shapes. In structured mode, gradients, preset patterns, images, textures, and overlay panels remain explicit shapes or pictures; the generic background-promotion rule outside structured mode does not expand this ownership contract.

---

## 2. Per-page Structured Lookup

**Per-page template lookup — `page_layouts` section (`mirror` / `layout` only)**:

Before drawing each page, use `page_context.template.prototype` to identify the inherited basename. Its matching `reference_set` entry supplies the complete SVG's path and SHA; §1.0 owns whether that file must be read or can be reused from the active context:

- Entry present (e.g., `P04: 03a_content_image_text`) → inherit the corresponding full SVG. The basename **must match** an actual file in the chosen template directory. If it does not, stop before drawing and report the invalid mapping; neither `strict` nor `adaptive` may fall back to free design inside a structured template deck.
- No entry for this page with `template_reuse_scope: mirror|layout` → stop before drawing and report the missing Strategist mapping. Adaptive mode still requires one selected complete template SVG; flexibility applies to the post-design output Layout, not to whether an input prototype exists.
- Whole section absent while `template_reuse_scope: mirror|layout` is present → stop before drawing; the current template contract is incomplete.
- `template_reuse_scope: style` → the whole section must be absent; do not perform per-page prototype lookup.

Do **not** invent a prototype entry, and do **not** assume a structured template just because `templates/` exists. For `mirror` / `layout`, a missing or invalid `page_layouts` row is an upstream contract error. `style` is a separate flat deck route, never a per-page fallback.

**Per-page PowerPoint layout lookup — `template_reuse_scope: mirror|layout` only**:

- When `pptx_structure.mode` is `flat` (including `template_reuse_scope: style`), skip this lookup and the structured scaffold below. `pptx_masters`, `pptx_layouts`, `page_layouts`, and the corresponding SVG metadata must all be absent; each root still declares its canonical `data-pptx-page-role`.
- With `template_reuse_scope: mirror|layout`, `pptx_structure.mode` must equal `structured`; any other or missing value is rejected. Do not migrate an invalid structured contract in place: create a new current-contract workspace through Create Template before generation resumes.
- Read the current page assignment as `P<NN>: <layout_key>`. Resolve the assigned Layout key in `pptx_layouts`, then resolve its Master key in `pptx_masters`. Missing, malformed, or partial mappings stop before drawing.
- Write matching root Master/Layout key and picker names. Do not write `data-pptx-layout-kind` or `data-pptx-page-role`.
- On strict template use, the row and SVG contract match the selected prototype exactly.
- On adaptive template use, retain the prototype Master and realize the Layout key/name already declared for this page. If construction proves that fixed Layout atoms or slot topology/bounds must change, stop before completing the page and return to Strategist to declare the revised definition and assignment; regenerate the current page context before resuming.
- A Layout key may repeat across non-adjacent pages only when its fixed atoms and slot contracts are identical.

**Structured template-page scaffold**:

```xml
<svg viewBox="…"
     data-pptx-master="<master-key>" data-pptx-master-name="<master-name>"
     data-pptx-layout="<layout-key>" data-pptx-layout-name="<layout-name>">
  <rect id="master-bg" data-pptx-layer="master" …/>              <!-- one atomic Master object -->
  <text id="master-footer" data-pptx-layer="master" …>…</text>   <!-- no Master/Layout g -->
  <path id="layout-rule" data-pptx-layer="layout" …/>            <!-- one atomic Layout object -->
  <g id="title-slot" data-pptx-placeholder="title"
     data-pptx-bounds="60 36 1160 64">
    <text id="title-carrier" data-pptx-carrier="true" …>…</text>
  </g>
  <g id="body-slot" data-pptx-placeholder="body"
     data-pptx-idx="1"
     data-pptx-bounds="60 120 470 500">
    <text id="body-carrier" data-pptx-carrier="true" …>…</text>
  </g>
  <g id="picture-slot" data-pptx-placeholder="picture"
     data-pptx-idx="2"
     data-pptx-bounds="570 120 650 500">
    <image id="picture-carrier" data-pptx-carrier="true" …/>
  </g>
  <g id="content-block-1" data-pptx-bounds="60 120 470 500">…</g>   <!-- one group per logical content unit -->
  <g id="content-block-2" data-pptx-bounds="570 120 650 500">…</g>
</svg>
```

On structured template pages, Master/Layout atoms and slot groups are direct root children and precede ordinary content groups. Structural metadata nested inside an ordinary content group fails export. Flat pages use ordinary top-level semantic groups only.
