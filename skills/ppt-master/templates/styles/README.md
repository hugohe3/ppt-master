# Style Workspaces

**Style = a roster-free reusable communication method plus coordinated design defaults**: argument flow, page-role vocabulary, evidence and data-expression discipline, visual-system defaults, image/icon direction, and review focus. It owns no current-project communication contract, brand identity, page geometry, SVG prototypes, or application contract, and does not replace the mode or visual-style catalogs. The shared kind and workspace model lives in the parent [`README.md`](../README.md).

## Axis Separation

`kind: style` (a portable workspace of method and non-binding defaults), final Stage-2 `mode` (the deck's confirmed narrative skeleton), final Stage-2 `visual_style` (the deck's confirmed composition and texture lock), and internal `template_reuse_scope: style` (a flat export plan reusing no structure) are separate contracts. Style-only and Style + Brand produce a flat plan; a Style beside a Layout or Deck may use structured reuse — `kind: style` never forces the reuse scope when another workspace supplies structure.

## Selection, Precedence, and Installation

Selection follows the parent contract: Style choices come only from `styles_index.json`; a supplied exact root joins the selector and is preselected only when sole; a consulting label or visual description is a brief and never activates a workspace; Quick applies a supplied exact root directly and reads the installed copy before authoring flat pages.

| Decision | Precedence |
|---|---|
| Current contract, mode, visual style, palette, typography, images, icons | Latest explicit user instruction and confirmed project values |
| Exact identity values | Brand, then Deck; both override overlapping Style fallbacks |
| Reusable method and evidence discipline | Style, where compatible with the current contract |
| Reusable structure | Layout, otherwise Deck; Style never supplies structure |
| Recurring application context | Deck, subordinate to the Stage-1 contract |

Style fallbacks seed the Stage-2 solution when a decision is open; they are not identity truth and never bypass confirmation. Surface a material Style/Deck conflict rather than weakening either.

## `design_spec.md` Contract

Frontmatter: `style_id`, `kind: style`, `summary`, `keywords` (three to five) only. Required body sections: I Style Overview (name, best fit, intent, provenance); II Communication Method (argument flow, page-message discipline, claim treatment, optional mode seed); III Page Role Vocabulary (roles with jobs, evidence obligations, non-geometric tendencies); IV Evidence & Data Expression; V Visual System Defaults (composition, density, decoration, color behavior, typography character, optional visual-style seed and `Fallback Color Scheme` / `Fallback Typography` subsections — lower-priority defaults, never identity); VI Image & Icon Direction (rendering, usage, framing, icon treatment without asset selection); VII Review Focus (checks used only after the user activates visual review, containing exactly one non-localized `<!-- visual-review-trigger: explicit-user-only -->` marker). A preset seed resolves to a real catalog ID; a custom seed carries behavior prose and lists only the catalog references it uses (`Mode References`, `Visual Style References`, `Image Rendering References`).

**Forbidden — identity, structure, or application ownership**: no `primary_color`, color provenance, Logo, Voice & Tone, Icon Style, canvas fields, page count/types, `replication_mode`, `native_structure_mode`, or placeholder fields; no Template Overview, Signature Design Elements, Page Roster, SVG filenames, Master/Layout identities, slot geometry, fixed sequences, or application audience/outcome rules; no current-project audience, objective, outcome, core message, delivery context, afterlife, outline, page assignments, icon inventory, or image list.

## Workspace and Creation

A Style workspace is one file — `<template_workspace>/templates/design_spec.md` — with no page or asset payload; never create empty `images/`, `icons/`, or `exports/`. Enter [`create-template.md`](../../workflows/create-template.md), which dispatches to [`create-style.md`](../../workflows/create-template/create-style.md); validate with `svg_quality_checker.py --template-mode`; in library scope register with `register_template.py <id> --kind style`. [`styles_index.json`](./styles_index.json) maps `style_id → { summary, keywords }` and is the only discovery source; reading a name in prose never activates a workspace.
