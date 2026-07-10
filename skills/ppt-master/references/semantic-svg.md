# Minimal Semantic SVG Markers

PPT Master uses a small set of rendering-neutral compiler hints only where
ordinary SVG cannot reliably express a required PowerPoint packaging decision.
These markers are not a second content model and do not abbreviate SVG.

## 1. Boundary

| Marker | Placement | Purpose |
|---|---|---|
| `data-pptx-page-role` | Root `<svg>` | Select the baseline PowerPoint Layout family. Required on newly generated baseline/free-design pages; template/preserve pages already use `data-pptx-layout`. |
| `data-pptx-role` | A structural page-frame element | Identify the few objects whose package or animation behavior is not already expressed by specialized metadata. The element also needs a stable unique `id`. |

The complete geometry, text, styles, grouping, and asset references remain in
ordinary SVG. Removing these markers must not change browser rendering. Do not
copy visible values into metadata, and do not mark ordinary titles, body text,
cards, KPIs, diagrams, charts, icons, or images merely to describe their
content.

Use the existing specialized contracts for specialized facts:

- `data-pptx-layout` and `data-pptx-layer` own Master/Layout/Slide structure;
- `data-pptx-placeholder` owns PowerPoint placeholder identity;
- `data-pptx-native` owns native chart/table reconstruction.

Do not duplicate those facts with `data-pptx-role`. Consumers resolve semantics
in this order: specialized metadata, minimal compiler hints, then legacy
filename/id conventions.

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

### Free-design page

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

### Reusable template page

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
unique IDs. Baseline export consumes explicit markers before compatibility
heuristics:

- root page role is preferred over filename-based Layout classification;
- `data-pptx-placeholder="slide-number"` is preferred over a generic role or id;
- explicit structural role is preferred over id-token chrome detection;
- animation target scanning uses the structural role before id-token fallback.

Filename and id heuristics remain compatibility fallbacks only for older SVGs
that lack the corresponding marker. A canonical page role is authoritative over
the filename. Any explicit structural role prevents id-based reinterpretation;
an unknown role remains renderable but produces a quality-check warning.
