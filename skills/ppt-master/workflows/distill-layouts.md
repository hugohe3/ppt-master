---
description: Distill completed free-design or template-based SVG pages into reusable PowerPoint Layouts
---

# Distill Layouts Workflow

Finalize reusable Master/Layout structure only after the complete visible SVG pages exist.

**Trigger**: Run on explicit free-design reuse requests, and automatically after template-based visual generation only when `layout_strategy: distill` is locked and `pptx_layouts` is still absent.

---

## 1. Scope and State

| Project state | Action |
|---|---|
| `mode: baseline` with no `layout_strategy` | Continue only when the user selected finished pages for reuse |
| `mode: template` + `layout_strategy: distill` + no `pptx_layouts` | Continue; every page already has one input prototype in `page_layouts` |
| `layout_strategy: distill` + complete `pptx_layouts` | Validate/no-op and continue to export; re-enter only when the user explicitly asks to re-distill after later SVG changes |
| `mode: template` without `layout_strategy` | Stop; keep the legacy immediate/pre-authored template contract |
| `mode: preserve` | Stop; preserve owns the imported native package contract |
| Raw PPTX request | Route to [`create-template`](./create-template.md) |
| Cross-project package from an already distilled source | Route to [`create-template`](./create-template.md) with only user-selected/`distilled` pages, never `utility` pages |
| Cross-project package from an undistilled free-design source | First complete this workflow for the explicitly selected source pages, then pass only those `distilled` pages to [`create-template`](./create-template.md) |
| Missing completed `svg_output/` | Stop; finish Executor visual construction first |

`page_layouts` is the input prototype mapping. `pptx_layouts` is the output native Layout contract. Do not write the latter before the complete SVG design exists on a deferred template route.

🚧 **GATE**: Read `spec_lock.md`, every SVG in `svg_output/`, every template SVG named by `page_layouts`, the complete page roster, and `animations.json` when present. Distillation writes one all-page output contract; a selected-page-only read is insufficient.

**Hard rule**: Keep this work in the main agent. Do not infer, cluster, or match by visual similarity.

---

## 2. Resolve Prototypes

### 2.1 Baseline selection

**User selection wins**: Use the requested page numbers or filenames. One selected page creates one Layout unless the user explicitly asks to share a family.

⛔ **BLOCKING**: When a baseline reuse request names no pages, present a short candidate list with page number, composition, and reuse rationale, then wait for the user to choose. Do not promote every page automatically.

**Shared baseline family**: Share one key only when the user explicitly requests it. The named prototype supplies the default bounds; otherwise use the first page in the selection order and state that choice. Every member repeats the same placeholder ids/types/indices/default bounds and static Layout elements. Slide-local geometry may differ.

### 2.2 Template prototypes

**Per-page source**: Resolve each `P<NN>` through `page_layouts` to one complete SVG in `templates/`. The template page is both the visual prototype and the structural authority for its Master/Layout/placeholder metadata.

| Adherence | Final contract |
|---|---|
| `strict` | Keep the prototype Layout key/name, Master/Layout ids/topology/geometry, and placeholder id/type/index/default-bounds contract |
| `adaptive` | Keep the prototype Master ids/topology/geometry; derive a new explicit Layout key/name, static framing, placeholder topology, and design-zone bounds only when the completed page evolved |

**Hard rule — stable provenance**: Match inherited structure by `page_layouts` plus stable direct-child `id`. Do not recover a missing object by geometry, text role, filename, or visual similarity.

**Template skin boundary**: For non-mirror templates, colors, strokes, effects, and font sizes follow the project `spec_lock` re-skin rules. Strict locks reusable structure and bounds, not the template package's sample paint. Mirror remains visually literal.

**Strict legacy boundary**: A strict prototype without explicit bounds on every placeholder cannot enter deferred distillation. Return to the Strategist bounds preflight and use legacy immediate-template compatibility, or upgrade the template package. Do not switch the user's strict choice to adaptive automatically.

---

## 3. Build the Final Contract

| Scope | Baseline source | Template source |
|---|---|---|
| Master | Preserve an already exact all-page Master; do not invent one | Preserve the selected template Master ids/topology/geometry in both strict and adaptive; apply the locked project skin |
| Layout | User-selected reusable static framing behind content | Strict copies the prototype; adaptive keeps only stable evolved framing from the completed design |
| Placeholder | Safe direct atomic carrier, or the final composite-object region exception below | Strict keeps the prototype identity/bounds; adaptive keeps template semantics where applicable and derives evolved design-zone bounds |
| Slide | Actual text, imagery, data, icons, complex groups, foreground overlays, local geometry | Same |

**Hard rule — complete-SVG authority**: The finished SVG remains the sole visible page authority. Do not add a visible object from the template during distillation. Missing inherited visuals are an Executor error; return to page generation instead of repairing them invisibly at export time.

**Hard rule — no visible redesign**: Do not change text, geometry, paint, image hrefs, or z-order. Structure-only reparenting is allowed only for the safe single-carrier case below.

**Hard rule — safe placeholder carrier**: Prefer one direct atomic object. When the reusable unit is an already completed multi-object region, the final `distilled` SVG may mark exactly one direct top-level `<g>` as `data-pptx-placeholder="object"` with explicit design-zone bounds. This is a Layout-only region proxy: its visible Slide group remains ordinary and export adds a hidden transparent binding proxy. Do not use this exception in reusable template SVGs, pending template pages, utility pages, or legacy immediate contracts. Nested metadata, unsafe text extraction, and non-top-level groups remain forbidden.

**Single-carrier extraction**: Replace a top-level one-carrier wrapper by its child only when the wrapper has no clip, mask, filter, `animations.json` reference, animation target, or multi-object semantics. Materialize inherited presentation attributes and transforms, preserve the effective paint position and stable referenced id, then run the render-equivalence gate in §7. If the gate cannot run, keep the object Slide-local.

**Native chart/table boundary**: Keep chart/table groups Slide-local by default. Mark one as a placeholder only when it already carries a valid matching `data-pptx-native` contract and export will use the same `--native-objects` choice.

**Final kind**: Add `data-pptx-layout-kind="distilled"` to every selected baseline page and every deferred template page. Template distillation has no utility pages because every page owns a `page_layouts` prototype.

**Finished-Slide preservation**: A distilled marker supplies a Layout prototype without moving visible content. Atomic carriers retain matching Slide bindings for render fidelity. Composite object-region carriers remain ordinary and receive hidden transparent binding proxies, preventing empty inherited slots from painting over an approved page.

```xml
<svg viewBox="0 0 1280 720"
     data-pptx-layout="editorial-visual"
     data-pptx-layout-name="Editorial Visual"
     data-pptx-layout-kind="distilled">
  <g id="visual-frame" data-pptx-layer="layout">...</g>
  <text id="page-title"
        data-pptx-placeholder="title"
        data-pptx-placeholder-bounds="60 36 1160 64">Actual title</text>
  <image id="hero-image"
         data-pptx-placeholder="picture"
         data-pptx-placeholder-idx="1"
         data-pptx-placeholder-bounds="570 120 650 500"
         x="620" y="120" width="600" height="500"
         href="../images/hero.jpg"/>
  ...
</svg>
```

---

## 4. Derive Default Placeholder Bounds

| Placeholder | Bounds source |
|---|---|
| `title` / `subtitle` | Title safe area or header zone |
| `body` | Column, panel inner box, or intended copy region |
| `picture` / `media` | Image frame or intended visual region |
| `chart` / `table` / `object` | Reusable plot, grid, or object zone; chart/table remains conditional under §3 |
| `footer` / `slide-number` | Stable footer or page-number zone |

**Hard rule**: Every placeholder on a `distilled` Layout carries `data-pptx-placeholder-bounds="x y width height"` with four finite values and positive width/height.

**Forbidden — text-tight bounds**: Do not derive bounds from character count, glyph width, line wrapping, text ink, or `data-pptx-text-bounds`. Use the intended design zone. `data-pptx-text-bounds` continues to own only the current Slide text frame.

**Local geometry remains free**: Placeholder bounds define the Layout default. The current object geometry remains the Slide override and may differ across pages using one key.

---

## 5. Complete the All-Page Mapping

### 5.1 Baseline utility mapping

Map every unselected baseline page to one empty utility Layout:

```xml
<svg ...
     data-pptx-layout="freeform-unselected"
     data-pptx-layout-name="Freeform"
     data-pptx-layout-kind="utility">
  ...all visible objects remain Slide-local...
</svg>
```

**Hard rule**: A `utility` Layout has zero Layout elements and zero placeholders. It exists only to keep the baseline mapping complete.

### 5.2 Template mapping

Map every template page to `distilled`. Strict reuses the selected prototype key/name. Adaptive keeps that key/name only when the static Layout, placeholder identities, and default bounds still match; any evolved reusable contract receives both a new key and a new picker name. Pages sharing one key repeat an identical static/placeholder/default-bounds contract.

For a `replication_mode: mirror` package, the Master and every Slide-local non-text element preserve literal paint, fonts, effects, grouping, geometry, and referenced asset identity. A reused Layout/placeholder identity does the same. Only visible text content may change. Adaptive may intentionally evolve a Layout, but it must use the new key/name rule above; the mirror Master and ordinary Slide-local visuals remain literal. Referenced `<defs>` and applicable embedded-style rules are compared by each layer's actual dependency closure, so resources private to a genuinely new adaptive Layout do not masquerade as Slide-local drift.

**Forbidden — template utility**: Do not map any deferred template page to `utility`, omit its prototype, or fall back to free design.

---

## 6. Finalize `spec_lock.md`

Write `layout_strategy: distill` and the complete output mapping atomically. Keep `page_layouts` unchanged on template routes.

```markdown
## pptx_structure
- mode: template
- template_adherence: adaptive
- layout_strategy: distill

## pptx_layouts
- P01: cover-hero | Cover Hero | distilled
- P02: editorial-visual | Editorial Visual | distilled

## page_layouts
- P01: 01_cover
- P02: 03_content
```

**Hard rule**: Write one row for every generated page. Do not leave a partial mapping or mix final and pending SVG roots. Remove `data-pptx-page-role` from every mapped root and remove generic `data-pptx-role` from a carrier that now has specialized placeholder metadata.

**Baseline migration**: Do not silently replace an existing kindless structured-baseline mapping. Proceed only when the request explicitly asks to migrate or re-distill it.

**Completed-state re-entry**: A complete distilled mapping is idempotent. If no SVG structure changed, validate it and continue without rewriting. After later edits, re-distill only on an explicit request and replace the complete mapping/root metadata atomically; never expose a partial pending state.

---

## 7. Validate and Resume Export

Before any extraction or metadata reparenting, render each affected page with the existing fixed-output renderer, then copy the baseline outside `.preview/` before the next render overwrites it:

```bash
python3 skills/ppt-master/scripts/visual_review.py "<project_path>" --pages "<page_stem>"
mkdir -p "<project_path>/analysis/layout_distill_compare"
cp "<project_path>/.preview/<page_stem>.png" "<project_path>/analysis/layout_distill_compare/<page_stem>.before.png"
```

After the structure edit, render the same page again and compare the retained baseline with the new `.preview` PNG:

```bash
python3 skills/ppt-master/scripts/visual_review.py "<project_path>" --pages "<page_stem>"
python3 -c 'from PIL import Image, ImageChops; import sys; a=Image.open(sys.argv[1]).convert("RGBA"); b=Image.open(sys.argv[2]).convert("RGBA"); raise SystemExit(0 if a.size == b.size and ImageChops.difference(a, b).getbbox() is None else 1)' "<project_path>/analysis/layout_distill_compare/<page_stem>.before.png" "<project_path>/.preview/<page_stem>.png"
```

Require exit code 0. If a page differs, undo the extraction and keep that object Slide-local. Pure root metadata additions that do not reparent or change any visible child do not need this comparison.

Run the project quality gate:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
```

The checker validates complete mappings, explicit bounds, utility emptiness, selected template prototypes, strict structural equality, and adaptive Master-structure equality. Fix every error before export.

| Entry point | Next action |
|---|---|
| Before the first export | Resume `SKILL.md` Step 7 |
| After an existing export | Re-run Step 7.2 `finalize_svg.py`, then repeat the exact prior Step 7.3 invocation with the same native-object, animation, narration, notes, and transition flags |

```markdown
## ✅ Layout Distillation Complete

- [x] Baseline user selections or all template prototypes resolved explicitly
- [x] Every distilled placeholder has explicit design-zone bounds
- [x] Template Master structure matches the selected prototypes
- [x] `spec_lock.md` and every SVG root carry one complete final mapping
- [x] Structure-only edits are pixel-identical to their pre-edit render
- [x] Project quality checker reports zero errors
- [ ] **Next**: Resume or repeat the canonical export steps
```
