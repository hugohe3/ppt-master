# Minimal Semantic SVG Markers

PPT Master uses a small set of rendering-neutral compiler hints only where
ordinary SVG cannot reliably express a required PowerPoint packaging decision.
These markers are not a second content model and do not abbreviate SVG.

## 1. Boundary

| Marker | Placement | Purpose |
|---|---|---|
| `data-pptx-page-role` | Root `<svg>` | Select the compatibility Layout family for an unmapped baseline page, including free design before Layout distillation and legacy projects without `pptx_layouts`. |
| `data-pptx-role` | A structural page-frame element | Identify the few objects whose package or animation behavior is not already expressed by specialized metadata. The element also needs a stable unique `id`. |

The complete geometry, text, styles, grouping, and asset references remain in
ordinary SVG. Removing these markers must not change browser rendering. Do not
copy visible values into metadata, and do not mark ordinary titles, body text,
cards, KPIs, diagrams, charts, icons, or images merely to describe their
content.

Use the existing specialized contracts for specialized facts:

- `data-pptx-layout`, `data-pptx-layout-name`, `data-pptx-layout-kind`, and
  `data-pptx-layer` own Master/Layout/Slide structure. A free-design page uses
  them only after explicit post-design distillation. A deferred template page
  carries the selected prototype key/name and layer provenance during design,
  then adds the final kind only after distillation;
- `data-pptx-placeholder` owns the Layout placeholder prototype. A distilled
  carrier remains an ordinary object on the completed Slide. Legacy immediate
  template and pre-authored structured routes may also bind the Slide shape;
- `data-pptx-native` owns native chart/table reconstruction.
- `data-pptx-object`, `data-pptx-prst`, `data-pptx-frame`, `data-pptx-av-*`,
  `data-pptx-geometry-*`, `data-pptx-authoring`, and `data-pptx-part` own
  imported round-trip and authored preset-shape semantics under
  [`shared-standards.md`](./shared-standards.md) §§1.4–1.5.

Authored preset metadata comes only from `preset_shape_svg.py`; ordinary SVG
paths are never scanned, classified, or automatically upgraded to a preset.

Do not duplicate those facts with `data-pptx-role`. Consumers resolve semantics
in this order: specialized metadata, minimal compiler hints, then legacy
filename/id conventions.

The exporter consumes Layout structure; it never discovers or clusters it.
[`distill-layouts`](../workflows/distill-layouts.md) is the explicit authoring
workflow that converts user-selected baseline pages or every deferred template
page into final metadata before export. On template routes, `page_layouts`
selects the input prototype and `pptx_layouts` records the post-design output.
Reuse a key only when its placeholder default frames and static Layout layer
match. Do not move concrete content into a Layout or mark a complex
page-specific group merely to manufacture reuse.

Ordinary placeholder carriers are direct atomic objects: one text frame, image,
crop SVG, or other supported atomic shape. This is a narrow exception to the
top-level content-group budget, and the carrier does not count toward that
budget. A final post-design `distilled` page may additionally mark one direct
completed `<g>` as an `object` region proxy with explicit design-zone bounds;
the visible group remains ordinary and export adds a hidden transparent binding
proxy. Reusable template SVGs, pending template pages, utility pages, and legacy
immediate contracts may not use this exception. Native chart/table marker
groups remain governed by their separate specialized contract.

## 2. Canonical Values

### Page roles

| Value | Meaning | Baseline Layout |
|---|---|---|
| `cover` | Opening cover | `Cover` |
| `toc` | Agenda or contents page | `Agenda` |
| `section` | Chapter divider or transition | `Section` |
| `content` | Ordinary information page | `Content` |
| `ending` | Closing, thanks, Q&A, or contact page | `Closing` |

### Layout kinds

| Value | Meaning |
|---|---|
| `distilled` | A completed baseline selection or deferred template page distilled into reusable placeholder defaults and optional static framing. Every placeholder has explicit `data-pptx-placeholder-bounds`. |
| `utility` | The empty Freeform Layout shared by baseline pages not selected for distillation. It is forbidden on deferred template routes. |

### Structural roles

| Value | Compiler behavior |
|---|---|
| `background` | Treat an otherwise unmarked background as static page framing for animation purposes. |
| `decoration` | Treat decorative page framing as static for animation purposes. |
| `header` | Eligible for conservative repeated-chrome promotion; skip automatic entrance animation. |
| `footer` | Eligible for conservative repeated-chrome promotion; skip automatic entrance animation. |
| `logo` | Eligible for conservative repeated-chrome promotion; skip automatic entrance animation. |
| `watermark` | Eligible for conservative repeated-chrome promotion; skip automatic entrance animation. |
| `chrome` | Generic repeated page-frame object eligible for conservative promotion. |
| `page-number` | Identify a free-design page-number object; template `data-pptx-placeholder="slide-number"` already owns this behavior. |

`background` and `decoration` do not by themselves authorize Master/Layout
promotion. The existing background and exact-shared-structure safety checks
continue to own that decision.

## 3. Examples

### Unmapped baseline fallback page

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-page-role="content">
  <rect id="page-bg" data-pptx-role="background"
        x="0" y="0" width="1280" height="720" fill="#F7F9FC"/>

  <!-- Ordinary content keeps normal SVG structure; no duplicate role needed. -->
  <g id="growth-story">
    <text x="72" y="82" font-size="32" fill="#172033">Quarterly growth</text>
  </g>

  <text id="slide-number" data-pptx-role="page-number"
        x="1200" y="680" font-size="14" fill="#667085">7</text>
</svg>
```

### Post-design distilled Layout page

This form applies after the user selects a completed free-design/brand-only
baseline page, or after a deferred template page is reconciled with its
`page_layouts` prototype. Baseline does not imply an input prototype; template
does. Bounds are Layout defaults while current Slide geometry may differ. The
atomic carriers keep their matching Slide bindings, while a composite object
region remains an ordinary visible group with a hidden transparent binding
proxy. The generated Layout receives the reusable PowerPoint placeholders.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-layout="editorial-visual"
     data-pptx-layout-name="Editorial Visual"
     data-pptx-layout-kind="distilled">
  <path id="layout-rule" data-pptx-layer="layout"
        data-pptx-editable="false"
        d="M72 132H1208" stroke="#D0D5DD"/>

  <!-- Current x/y may differ from the reusable design-zone bounds. -->
  <text id="title-slot" data-pptx-placeholder="title"
        data-pptx-placeholder-bounds="72 48 1136 64"
        x="88" y="104" font-size="32" fill="#172033">Quarterly growth</text>

  <text id="body-slot" data-pptx-placeholder="body"
        data-pptx-placeholder-idx="1"
        data-pptx-placeholder-bounds="72 160 432 472"
        x="80" y="190" font-size="20" fill="#344054">Main narrative</text>

  <image id="picture-slot" data-pptx-placeholder="picture"
         data-pptx-placeholder-idx="2"
         data-pptx-placeholder-bounds="544 160 664 472"
         href="../images/quarterly-growth.png"
         x="576" y="176" width="616" height="440"
         preserveAspectRatio="xMidYMid slice"/>

  <!-- Logo has no specialized marker, so the minimal structural hint is useful. -->
  <text id="brand-mark" data-pptx-role="logo"
        x="1180" y="46" text-anchor="end">ACME</text>

  <!-- The placeholder already owns slide-number behavior; do not add a role. -->
  <text id="page-number" data-pptx-placeholder="slide-number"
        data-pptx-placeholder-idx="3"
        data-pptx-placeholder-bounds="1152 664 56 24"
        x="1200" y="680" text-anchor="end">7</text>
</svg>
```

### Unselected page after distillation

The page declares the complete project mapping but keeps every page-specific
visible object Slide-local. No child may carry Layout or placeholder metadata;
an exact shared Master contract is allowed when every page repeats it.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-layout="freeform-unselected"
     data-pptx-layout-name="Freeform"
     data-pptx-layout-kind="utility">
  <g id="page-content">
    <!-- The complete free-form design remains ordinary SVG. -->
  </g>
</svg>
```

## 4. Validation and Compatibility

The quality checker validates marker placement, canonical values, and stable
unique IDs. Export consumes explicit authored Layout metadata before baseline
compatibility hints and heuristics:

- root `data-pptx-layout` is authoritative when the page has a locked mapping;
- post-design distillation also requires root `data-pptx-layout-kind` to match the lock;
- a deferred template project with no `pptx_layouts` is pending and cannot enter release export;
- on an unmapped baseline page, root page role is preferred over filename-based Layout classification;
- `data-pptx-placeholder="slide-number"` is preferred over a generic role or id;
- explicit structural role is preferred over id-token chrome detection;
- animation target scanning uses the structural role before id-token fallback.

Filename and id heuristics remain compatibility fallbacks only for older SVGs
that lack the corresponding marker. On an unmapped baseline page, a
canonical page role is authoritative over the filename. Any explicit structural
role prevents id-based reinterpretation; an unknown role remains renderable but
produces a quality-check warning.
