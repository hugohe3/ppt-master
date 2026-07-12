# Minimal Semantic SVG Markers

PPT Master uses a small set of rendering-neutral compiler hints only where
ordinary SVG cannot reliably express a required PowerPoint packaging decision.
These markers are not a second content model and do not abbreviate SVG.

## 1. Boundary

| Marker | Placement | Purpose |
|---|---|---|
| `data-pptx-page-role` | Root `<svg>` | Select the compatibility Layout family only for a legacy baseline page whose project has no `pptx_layouts` mapping. New baseline/free-design pages use `data-pptx-layout` instead. |
| `data-pptx-role` | A structural page-frame element | Identify the few objects whose package or animation behavior is not already expressed by specialized metadata. The element also needs a stable unique `id`. |

The complete geometry, text, styles, grouping, and asset references remain in
ordinary SVG. Removing these markers must not change browser rendering. Do not
copy visible values into metadata, and do not mark ordinary titles, body text,
cards, KPIs, diagrams, charts, icons, or images merely to describe their
content.

Use the existing specialized contracts for specialized facts:

- `data-pptx-layout`, `data-pptx-layout-name`, and `data-pptx-layer` own Master/Layout/Slide structure. A new baseline/free-design page with a locked `pptx_layouts` row uses these markers while remaining `pptx_structure.mode: baseline`;
- `data-pptx-placeholder` owns PowerPoint placeholder identity;
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

Layout structure is authored, never discovered. Reuse a Layout key only when its
static Layout layer and placeholder contract match exactly. Do not cluster
visually similar pages, move concrete content into a Layout, or mark a complex
page-specific group merely to manufacture reuse.

Ordinary placeholder carriers are direct atomic objects: one text frame, image,
crop SVG, or other supported atomic shape. This is a narrow exception to the
top-level content-group budget, and the carrier does not count toward that
budget. Do not use an arbitrary composite `<g>` as a placeholder; keep complex
groups Slide-local. Native chart/table marker groups remain governed by their
separate specialized contract.

## 2. Canonical Values

### Page roles

| Value | Meaning | Baseline Layout |
|---|---|---|
| `cover` | Opening cover | `Cover` |
| `toc` | Agenda or contents page | `Agenda` |
| `section` | Chapter divider or transition | `Section` |
| `content` | Ordinary information page | `Content` |
| `ending` | Closing, thanks, Q&A, or contact page | `Closing` |

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

### Legacy baseline fallback page

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

### Explicit authored Layout page

This form applies to a new free-design/brand-only baseline page as well as to a
template page. The structure metadata does not change baseline mode into
template mode and does not imply a `page_layouts` reference.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-layout="content-default"
     data-pptx-layout-name="Content Default">
  <rect id="master-bg"
        data-pptx-layer="master"
        data-pptx-editable="false"
        x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>

  <g id="layout-header"
     data-pptx-layer="layout"
     data-pptx-editable="false">
    <!-- Complete reusable header drawing remains here. -->
  </g>

  <!-- Placeholder identity is already sufficient; no generic title role. -->
  <text id="title-slot" data-pptx-placeholder="title"
        x="72" y="92" font-size="32" fill="#172033">{{PAGE_TITLE}}</text>

  <!-- Logo has no specialized marker, so the minimal structural hint is useful. -->
  <text id="brand-mark" data-pptx-role="logo"
        x="1180" y="46" text-anchor="end">ACME</text>

  <!-- The placeholder already owns slide-number behavior; do not add a role. -->
  <text id="page-number" data-pptx-placeholder="slide-number"
        x="1200" y="680" text-anchor="end">7</text>
</svg>
```

## 4. Validation and Compatibility

The quality checker validates marker placement, canonical values, and stable
unique IDs. Export consumes explicit authored Layout metadata before baseline
compatibility hints and heuristics:

- root `data-pptx-layout` is authoritative when the page has a locked mapping;
- on an unmapped legacy baseline page, root page role is preferred over filename-based Layout classification;
- `data-pptx-placeholder="slide-number"` is preferred over a generic role or id;
- explicit structural role is preferred over id-token chrome detection;
- animation target scanning uses the structural role before id-token fallback.

Filename and id heuristics remain compatibility fallbacks only for older SVGs
that lack the corresponding marker. On an unmapped legacy baseline page, a
canonical page role is authoritative over the filename. Any explicit structural
role prevents id-based reinterpretation; an unknown role remains renderable but
produces a quality-check warning.
