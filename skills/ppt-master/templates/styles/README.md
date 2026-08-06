# Style Workspaces

**Style = a roster-free reusable communication method plus coordinated design defaults.** It can carry argument flow, page-role vocabulary, evidence and data-expression discipline, visual-system defaults, image/icon direction, and additional review focus. It does not own a current project's communication contract, reusable brand identity, page geometry, SVG prototypes, or a recurring application contract.

Style is a fourth independent template kind alongside [`brands/`](../brands/), [`layouts/`](../layouts/), and [`decks/`](../decks/). It is not a replacement for the mode or visual-style catalogs.

## Axis Separation

| Axis | Meaning |
|---|---|
| Template `kind: style` | A portable workspace that coordinates reusable method and non-binding design defaults |
| Final Stage-2 `mode` | The current deck's confirmed narrative and persuasion skeleton |
| Final Stage-2 `visual_style` | The current deck's confirmed shape, composition, whitespace, typography-character, and texture lock |
| Internal `template_reuse_scope: style` | A flat current-project export plan that reuses no Master/Layout structure |

These names are separate contracts. Style-only and Style + Brand naturally produce a flat application plan, while Style fused with a Layout or Deck may use structured reuse. `kind: style` therefore never forces the internal reuse scope when another workspace supplies structure.

## Selection, Precedence, and Fusion

Selection follows the parent README's Default Stage-1
[`generate-pptx`](../../workflows/generate-pptx.md) template-choice contract.
Its Style choices come only from `styles_index.json`; no
directory scan or bare-name match is allowed. A supplied exact root appears in
the same selector, defaults Stage 1 to template mode, and preselects that
specific candidate only when it is the sole supplied root. A
consulting label or visual description remains a brief and does not activate
this workspace. A non-free confirmation runs the
common installation/fusion stage after Stage 1 and before Stage 2; template-aware reading begins
in final Stage 2 from the project-local copy. Quick applies a supplied exact
Style root directly and otherwise uses free design; its current agent reads the
installed copy before authoring flat pages.

| Decision | Precedence |
|---|---|
| Current project communication contract, mode, visual style, palette, typography, images, and icons | Latest explicit user instruction and confirmed project values |
| Exact identity values | Brand, then Deck identity; both override overlapping Style fallback values |
| Reusable communication method and evidence discipline | Style, applied only where compatible with the current project contract |
| Reusable structure | Compatible Layout, then Deck structure; Style never supplies structure |
| Recurring application context | Deck, subordinate to the current project's Stage-1 communication contract |

Style fallback values seed the final Stage-2 solution when the corresponding decision remains open. They are not identity truth and do not bypass confirmation. If a Style method and a Deck application contract materially conflict, surface the mismatch; do not silently weaken either one.

## `design_spec.md` Contract

The frontmatter is intentionally small:

```markdown
---
style_id: <slug>
kind: style
summary: <one-line reusable method and design-default fit>
keywords: [<three-to-five discovery tags>]
---
```

The seven required body sections are:

| § | Title | Owned content |
|---|---|---|
| I | Style Overview | Display name, best fit, reusable intent, and provenance |
| II | Communication Method | Argument flow, page-message discipline, claim treatment, and an optional mode seed |
| III | Page Role Vocabulary | Semantic roles with communication jobs, evidence obligations, and non-geometric composition tendencies |
| IV | Evidence & Data Expression | Claim/evidence trace, chart/table/source behavior, and native-editability preference |
| V | Visual System Defaults | Composition, density, decoration, color behavior, typography character, and optional visual-style/fallback seeds |
| VI | Image & Icon Direction | Rendering, usage, framing, and icon treatment without asset selection |
| VII | Review Focus | Extra checks used only after the user explicitly activates visual review |

`Fallback Color Scheme` and `Fallback Typography` are optional subsections under §V. They remain lower-priority defaults, never Brand identity. A preset mode, visual style, or image rendering resolves to a real ID in its matching catalog. A custom seed includes its behavior prose and lists only catalog references actually used as comma-separated IDs; use `Mode References`, `Visual Style References`, or `Image Rendering References` respectively.

Section VII contains exactly one non-localized `<!-- visual-review-trigger: explicit-user-only -->` marker. Its surrounding explanation and checks may use the user's language; the marker lets validation enforce that Review Focus is advisory and never activates visual review.

**Forbidden — identity, structure, or application ownership**:

- Do not write `primary_color`, official color provenance, Logo, Voice & Tone, Icon Style, canvas fields, page count/types, `replication_mode`, `native_structure_mode`, or placeholder fields.
- Do not write Template Overview, Signature Design Elements, Page Roster, SVG filenames, Master/Layout identities, slot geometry, fixed page sequences, or reusable application audience/outcome rules.
- Do not write the current project's audience, objective, outcome, core message, delivery context, artifact afterlife, content outline, page assignments, icon inventory, or image-resource list.

## Workspace and Creation

Every Style workspace contains one portable source file and no page or asset payload:

```text
<template_workspace>/
└── templates/
    └── design_spec.md
```

Do not create empty `images/`, `icons/`, or `exports/` directories. Existing initialized-project scaffolding may remain untouched but is not Style output.

1. Enter [`workflows/create-template.md`](../../workflows/create-template.md), which dispatches method/default output to [`create-style.md`](../../workflows/create-template/create-style.md).
2. Validate with `svg_quality_checker.py --template-mode`.
3. In library scope, register with `register_template.py <id> --kind style`.

The discovery source of truth is [`styles_index.json`](./styles_index.json).
Each entry is `style_id → { summary, keywords }`; the index never duplicates
the full method or defaults. The Default Stage-1 template controls read this
file as their complete registered-Style catalog, and chat discovery returns
exact roots from the same entries. Choosing an entry and submitting Stage 1
activates installation;
reading a name in ordinary prose does not.
