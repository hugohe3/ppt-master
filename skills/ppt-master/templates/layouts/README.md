# Layout Templates

**Layout = a structure-only reusable template bundle**: canvas, Master/Layout structure, page types, slot geometry, semantic text roles, alignment/wrapping/capacity behavior, and the SVG roster — no brand color, typeface/weight identity, final type scale, logo, voice, or icon style (those come from a Brand/Deck or the confirmation stage). A layout may describe the content shapes and delivery conditions its geometry supports but never owns a communication objective, audience outcome, narrative sequence, boilerplate, or example content downstream must preserve — a structurally useful "board update" page stays a Layout; a board-update sequence with required decision, risk, and action roles is a Deck. Neutral colors, safe fonts, and provisional sizes in prototypes are preview values, not identity or a locked scale; Strategist inspects the prototypes and content, decides how much structure to reuse, and writes the exporter plan automatically. The shared kind and workspace model lives in the parent [`README.md`](../README.md).

| Axis | Layout behavior |
|---|---|
| Template kind | `layout`: structure only |
| Internal creation strategy | AI-derived `standard` / `fidelity` for a new system or `mirror` for validated source materialization; tool provenance, not a user choice — Layout mirror additionally requires a brand-neutral, application-neutral source (otherwise author through `standard` / `fidelity` or create a Deck; removing rules is never mirror) |
| Application planning | Strategist decides literal, structural, or style-only use and any strict/adaptive value |
| PPTX structure | The workspace is `structured`; the plan decides whether pages compile its structure or use it as visual reference |

[`layouts_index.json`](./layouts_index.json) (`layout_id → { summary, canvas_format, page_count, page_types }`) is the discovery source of truth; this README defines the kind and enumerates no layouts.

## Selection and identity boundary

Selection follows the parent contract: Layout choices come only from the index (no directory scan or bare-ID/style-phrase match); a supplied exact root joins the selector and is preselected only when sole; [`apply-template-workspace`](../../workflows/stages/apply-template-workspace.md) installs it before Stage 2; Quick applies a supplied exact root directly and authors the installed Master/Layout/slot contract as lockless structured Slides unless the user explicitly requests visual-only flat use.

## `design_spec.md` contract

Portable structural metadata plus rules unique to this layout; no Template Overview, application contract, or identity section — the frontmatter `summary` carries selection context.

```markdown
---
layout_id: <slug>
kind: layout
category: general | scenario | government | special
summary: <one-line structural use case>
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
page_types: [cover, toc, chapter, content, ending]
---

# [Layout Name] — Design Specification

## IV. Signature Design Elements
## V. Page Roster
## VII. Placeholder Overrides      # omit when none
```

`replication_mode` records how the workspace was produced. `Signature Design Elements` describes only reusable structure (grids, zones, image behavior, density rhythm, text roles, alignment/wrapping/capacity, slot conventions) and introduces no palette, typeface identity, type scale, objective, or narrative sequence; `Page Roster` lists every SVG with Layout key, picker name, content shape, and slot behavior.

## Structured SVG and slot contract

Every SVG is a complete preview declaring one root Master and Layout; fixed visuals are direct atoms; a slot is a top-level `<g id>` with positive design-zone bounds and exactly one compatible carrier; zero-slot Layouts are valid; a typed `picture` / `chart` / `table` slot promises no inserted picture or native object — the generated Slide supplies content and native replacement stays an explicit export choice. Use canonical `{{PLACEHOLDER}}` names ([`template-designer.md`](../../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template)) with a `placeholders:` frontmatter map for overrides. `standard` / `fidelity` author new SVGs and structure; `mirror` preserves source identities, parentage, assignments, placeholder facts, and supported visuals without synthesis; legacy contracts are never upgraded in place, and a flat directory shape alone is not a legacy signal.

## Workspace and creation

`templates/` (spec + prototypes), optional `images/` (`../images/<name>`), optional `icons/imported/`, and `exports/<layout_id>_template_preview.pptx` as review evidence. Library scope writes `skills/ppt-master/templates/layouts/<layout_id>/` and updates the index; project scope uses an initialized `projects/<name>/` root without registration. Enter [`create-template.md`](../../workflows/create-template.md) (dispatching to [`create-layout.md`](../../workflows/create-template/create-layout.md)), validate with `svg_quality_checker.py --template-mode`, run `template_preview_pptx.py` on request and always for multiple Masters, and in library scope register with `register_template.py <id> --kind layout`. General SVG/PPT rules stay in [`shared-standards-core.md`](../../references/shared-standards-core.md) and [`pptx-structure-interface.md`](../../references/pptx-structure-interface.md); see [`styles/`](../styles/) to combine method and direction with this structure.
