---
description: Restore legacy SVG projects to the explicit structured Master/Layout contract
---

# Restore PPTX Structure Workflow

Restore an existing SVG-authored project or template before quality checking or release export when its Master/Layout contract is absent or legacy.

**Trigger**: Run when a structured/template project reports a missing or legacy `pptx_structure.mode`, or when the user explicitly asks to migrate an older structured SVG project. Do not run for a current free-design/brand-only project that explicitly declares `pptx_structure.mode: flat`; missing Master/Layout identity is intentional on that route.

**Hard rule — structure, not packaging**: Directory shape is not PowerPoint structure evidence. A current template workspace uses `templates/design_spec.md`; a compatible legacy-flat package uses `design_spec.md` at its root. Do not run this workflow merely to move a flat package into the current workspace shape.

**Boundary against template creation**: This workflow normalizes one existing project's/package's structure without visual redesign. It does not choose a reusable-template replication mode. When its result becomes type-B input to [`create-template`](./create-template.md), `standard` / `fidelity` treat it as visual reference and author new structure; `mirror` restores its explicit source ownership one-to-one.

---

## 1. Route Boundary

| Input state | Action |
|---|---|
| Missing `pptx_structure` or legacy `baseline` / `generated` | Restore structure from the complete SVG deck; use source facts when available |
| Legacy `template`, `layout_strategy: distill`, `data-pptx-layout-kind`, or `utility` | Replace the distillation contract with one explicit structured contract |
| Legacy `preserve` plus `native_structure.json` / `source_template.pptx` | Use the native facts as restoration evidence; rebuild the SVG contract instead of preserving package parts |
| Existing `mode: structured` project | Validate and repair only the reported mismatch; do not re-infer the deck |
| Legacy-flat template package whose SVG roots and slots already satisfy the current structured contract | Consume it through the compatibility reader; do not restore or relocate it solely because `design_spec.md` and SVGs are flat |
| Current template workspace with `templates/` and optional `images/`, `icons/`, or `exports/` | Inspect SVG metadata to decide whether restoration is needed; the workspace folders themselves do not prove or disprove structure |
| Raw PPTX intended as a reusable template | Run [`create-template`](./create-template.md), not this workflow |
| Existing PPTX receiving notes/audio/timing/transitions | Keep the direct [`native-enhance-pptx`](./native-enhance-pptx.md) route; do not create SVGs |
| Raw PPTX template receiving new content | Keep the direct [`template-fill-pptx`](./template-fill-pptx.md) route |

**Hard rule**: Keep restoration in the main agent and inspect the complete page roster. Do not delegate page classification, cluster by visual similarity, or write a batch SVG generator.

🚧 **GATE**: Take the explicit project/template workspace root as input. For a project, read `spec_lock.md`, every file in `svg_output/`, and every template SVG named by `page_layouts`. For a template, resolve `templates/design_spec.md` first and fall back to legacy root `design_spec.md`, then read every sibling template SVG. In either case, read any original PPTX/native structure facts that belong to the workspace.

---

## 2. Preserve the Pre-Migration State

Before editing, copy the current `svg_output/` and `spec_lock.md` into one new timestamped directory under:

```text
<project>/backup/<timestamp>/restore-pptx-structure/
```

Record the source evidence used for restoration in a short `README.md` inside that backup directory: original PPTX/native facts, legacy template SVGs, or completed SVG pages only.

**Hard rule**: Never delete the legacy sources during restoration. If the requested migration would rewrite several existing files and the user has not already authorized that operation, obtain the repository-required bulk-modification confirmation first.

**Hard rule — no packaging migration**: Keep the input workspace/package placement unchanged. This workflow edits the semantic SVG/lock contract only; it does not normalize a legacy-flat package into the current `templates/` plus optional `images/`, `icons/`, and `exports/` routing.

---

## 3. Determine the Structure

Use this evidence priority:

| Priority | Evidence | Contract |
|---:|---|---|
| 1 | Original PPTX plus verified native structure facts | Use the source contract as compatibility evidence for this no-redesign restoration; record any required normalization |
| 2 | Legacy template SVGs or explicit legacy structure metadata | Preserve stable identities and reusable geometry after removing legacy-only fields |
| 3 | Completed SVG pages only | Classify deliberately across the full deck; do not let the exporter infer structure |

**Hard rule — complete native graph**: Preserve every supported native Layout,
including one unused by every output page. Create a definition-only
`layout_<layout_key>.svg` prototype for each otherwise unrepresented Layout and
record it in the unique `pptx_layouts` roster with a
`template:<basename>` source. A Master reachable only through such Layouts is
retained through their parent relationship. Do not silently drop identities or
synthesize a generated carrier page.

**Hard rule**: Decide from SVG/lock semantics, never from whether `design_spec.md` is at the workspace root or under `templates/`.

Classify each visible object:

| Classification | SVG representation |
|---|---|
| Fixed across every Layout under one Master | Root-level atomic element with `data-pptx-layer="master"` |
| Fixed only for one reusable Layout | Root-level atomic element with `data-pptx-layer="layout"` |
| Replaceable reusable content region | Root-level placeholder `<g>` with explicit design-zone bounds |
| Page-specific content or foreground overlay | Ordinary Slide-local SVG content without Master/Layout ownership |

**Hard rule — no Master/Layout groups**: A fixed Master or Layout visual must not be a `<g>`. Recursively expand every legacy/source group into individual root-level atomic elements. Compose and apply group transforms, opacity, inherited paint, clip behavior, and styles to each atom while preserving paint order. The restoration target preserves supported visual output and Master/Layout topology; it does not preserve source grouping as an editing unit.

**Hard rule — no visual redesign**: Do not change wording, geometry, paint, assets, or z-order except for the normalization required to flatten a fixed Master/Layout group. Render before and after any transform-flattening edit and require pixel equivalence.

**Hard rule — native metadata below structural layers**: Keep the complete lossless import artifact in the backup/evidence set. An unchanged imported shape may keep the source metadata already supported by the converter when it remains Slide-local or inside a slot; no additional opt-in marker exists. A logical `<g>` cannot become Master/Layout because those layers require direct atoms. Normalize fixed-layer objects into direct atom(s), rebuilding a preset when supported and otherwise keeping the current SVG fallback. Any geometry, paint, text, or fingerprint change invalidates stale source metadata. `data-pptx-native` remains reserved for chart/table markers.

---

## 4. Write the Structured SVG Contract

Every page root declares its final ownership:

```xml
<svg viewBox="0 0 1280 720"
     data-pptx-master="master-default"
     data-pptx-master-name="Default Master"
     data-pptx-layout="content-two-column"
     data-pptx-layout-name="Two Column">
```

Fixed visuals are direct atomic children:

```xml
<path id="master-brand-rule" data-pptx-layer="master" .../>
<rect id="layout-title-rule" data-pptx-layer="layout" .../>
```

An ordinary placeholder is one root-level group with exactly one compatible direct carrier:

```xml
<g id="title-slot"
   data-pptx-placeholder="title"
   data-pptx-placeholder-bounds="72 48 1136 72">
  <text id="title"
        data-pptx-placeholder-carrier="true"
        x="72" y="100">Actual title</text>
</g>
```

| Slot contract | Rule |
|---|---|
| `title`, `subtitle`, `body`, `date`, `footer`, `slide-number` | Use exactly one direct text carrier |
| `picture`, `media` | Use exactly one compatible direct image/media carrier |
| `chart`, `table` | Use one compatible direct native carrier only when the matching native-object contract is valid |
| Atomic `object` | Use exactly one compatible direct carrier |
| Composite `object` | Set `data-pptx-placeholder-binding="proxy"`; keep the visible children Slide-local inside the slot and declare no carrier |

**Hard rule — bounds**: Every slot group declares `data-pptx-placeholder-bounds="x y width height"` with finite values and positive width/height. Bounds describe the reusable design zone, not the current content's tight box.

**Hard rule — wrapper neutrality**: The slot `<g>` is an authoring boundary, not a rendered object. It may carry only `id` and `data-pptx-*` attributes. Move any transform, opacity, fill/stroke, filter, clip/mask, style, or class behavior onto the visible children before marking the group as a slot.

**Hard rule — proxy boundary**: `proxy` is allowed only for a composite `object` slot. Ordinary slots must use the default carrier binding.

**Zero-slot Layouts are valid**: A cover, poster, or purely visual Layout may declare no placeholder group. Do not manufacture a full-page `object` slot or a `utility` Layout.

Remove legacy `data-pptx-layout-kind`, `layout_strategy`, `distilled`, `utility`, and preserve-only ownership metadata from the restored SVG contract.

---

## 5. Replace the Project Lock

After every SVG has its final metadata, replace the legacy structure sections as one complete mapping:

```markdown
## pptx_structure
- mode: structured

## pptx_masters
- master-default: Default Master

## pptx_layouts
- cover-visual: master-default | Cover Visual | P01
- content-two-column: master-default | Two Column | P02

## page_pptx_layouts
- P01: cover-visual
- P02: content-two-column
```

**Hard rule**: `pptx_masters` contains every Master key exactly once. `pptx_layouts` contains every unique reusable Layout exactly once and declares its Master, picker name, and definition source. `page_pptx_layouts` contains exactly one assignment for every generated page. Each page root must match its assigned Layout definition. A Layout unused by generated pages uses `template:<basename>` as its definition source.

**Layout identity**: A Layout key is globally unique. Pages may reuse it only when their Layout atoms and slot id/type/index/bounds/binding/carrier contracts are identical. The same display name under two Masters still uses two different keys.

**Template adherence**: Keep `template_adherence: strict|adaptive` only when a template route already owns that policy. Strict pages keep the referenced contract. Adaptive pages that changed the contract receive a new Layout key and name.

---

## 6. Validate and Resume

Before flattening each affected page, render and retain its baseline outside `.preview/`:

```bash
python3 skills/ppt-master/scripts/visual_review.py "<project_path>" --pages "<page_stem>"
cp "<project_path>/.preview/<page_stem>.png" "<backup_path>/<page_stem>.before.png"
```

After restoring that page, render again and compare it with the retained baseline:

```bash
python3 skills/ppt-master/scripts/visual_review.py "<project_path>" --pages "<page_stem>"
python3 -c 'from PIL import Image, ImageChops; import sys; a=Image.open(sys.argv[1]).convert("RGBA"); b=Image.open(sys.argv[2]).convert("RGBA"); raise SystemExit(0 if a.size == b.size and ImageChops.difference(a, b).getbbox() is None else 1)' "<backup_path>/<page_stem>.before.png" "<project_path>/.preview/<page_stem>.png"
```

Require exit code 0. If the render differs, repair the transform/style materialization before continuing. Pure metadata edits that do not change or reparent visible children do not require this comparison.

Then run:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<project_path>"
```

Fix every error. The gate must confirm root Master/Layout identity, root-level atomic fixed elements, slot bounds, carrier/proxy rules, complete lock mappings, and same-key contract equality.

After the checker reports zero errors, return to `SKILL.md` Step 7.2 and Step 7.3. Run the commands sequentially with the same native-object, animation, narration, notes, and transition flags previously selected.

```markdown
## ✅ PPTX Structure Restoration Complete

- [x] Legacy SVG and lock artifacts backed up with source-evidence notes
- [x] Every page root declares one Master and one Layout
- [x] Fixed Master/Layout visuals are root-level atomic elements, never groups
- [x] Every slot has explicit bounds and a valid carrier or proxy contract
- [x] `spec_lock.md` contains complete `structured` Master and page mappings
- [x] Group-flattening edits are pixel-equivalent and the quality gate reports zero errors
- [x] Imported native metadata is used only through supported existing attributes on unchanged Slide-local/slot objects; Master/Layout objects remain direct atoms
- [ ] **Next**: Resume the canonical post-processing and release export steps
```
