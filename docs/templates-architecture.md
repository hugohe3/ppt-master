# Template Architecture: Brand / Layout / Deck

> This is the **architecture alignment document**. It defines the three template kinds at the data-model layer, the field sets of each `design_spec.md`, and the multi-path fusion + conflict resolution rules. Audience: contributors and AI workflows; answers "what should / shouldn't a template directory contain; how do they combine when multiple are supplied".
>
> For user-facing usage (how to trigger, how to pick), see [`templates-guide.md`](./templates-guide.md); not repeated here.

---

## 1. The three kinds

| Kind | Library workspace root | What it writes | What it does NOT write | Originating workflow |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | Identity segment only: color / typography / logo / voice / icon style | No canvas, page structure, SVG roster | `workflows/create-template/create-brand.md` |
| **Layout** | `templates/layouts/<id>/` | Structure segment only: canvas / page structure / page types / SVG roster | No brand identity (no logo, no locked brand color) | `workflows/create-template/create-layout.md` |
| **Deck** | `templates/decks/<id>/` | All segments: identity + structure + middle (template overview) | — | `workflows/create-template/create-deck.md` (default child) |

Every newly created Layout/Deck SVG is a complete preview with root Master/Layout key and picker names, direct atomic Master/Layout elements, and top-level semantic slot groups. A normal slot has positive design-zone bounds and exactly one compatible carrier; composite `object` regions use explicit proxy binding, and zero-slot Layouts are valid. These specialized markers are authoritative; minimal `data-pptx-role` hints are added only for structural page-frame behavior they cannot express. `standard` / `fidelity` author new SVGs and new structure without preserving or distilling source topology. Mirror materializes a new workspace from validated authoring IR: a native PPTX contributes only supported facts still present in its package, while a current-contract SVG template contributes only its declared contract. It never reconstructs missing topology from a legacy SVG; fixed-layer source groups that are valid inputs are mechanically expanded into direct atoms. Strict keeps the selected declared Layout contract; adaptive retains the Master and may create a new Layout identity while authoring. Both export through `pptx_structure.mode: structured`. A flat directory with `design_spec.md` at its root remains a supported compatibility shape only when its SVGs satisfy the current contract. Semantic-legacy packages must be replaced by a newly created template workspace; they are never upgraded in place.

The three are **parallel reference bundles**. In library scope, the physical directory and the frontmatter `kind` field correspond one-to-one:

```yaml
# templates/brands/anthropic/templates/design_spec.md
---
kind: brand
...
---

# templates/layouts/presentation_core/templates/design_spec.md
---
kind: layout
native_structure_mode: structured
...
---

# templates/decks/china_merchants_bank/templates/design_spec.md
---
kind: deck
native_structure_mode: structured
...
---
```

### Output scope is separate from kind

`create-template` confirms where a Layout/Deck workspace is placed. This execution choice does not add a fourth kind and does not add a PPTX structure mode:

| Scope | Workspace root | Core workspace | Discovery |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind>/<id>/` | Required `templates/`; optional `images/`, `icons/`, and on-demand `exports/` | Register in the matching global index |
| `project` | `projects/<name>/` | The same routing contract | No global index update |

Both roots have the same core shape:

```text
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   └── *.svg
├── images/                     # optional; SVG href uses ../images/<name>
├── icons/
│   └── imported/               # optional; canonical imported vector assets
└── exports/                    # optional; requested review or required multi-Master evidence
    └── <id>_template_preview.pptx
```

Empty optional directories are omitted; do not add placeholder files. A preview PPTX is derived review evidence, not a source template asset. It is generated on request and is mandatory for a multi-Master package gate. Step 3 reads the workspace root and consumes `templates/` plus any existing `images/` and `icons/`; it ignores `exports/`. Library `exports/` directories are Git-ignored.

Imported vectors use `data-icon="imported/<name>"` and have one canonical file
at `icons/imported/<name>.svg`. Workspace-aware validation and export resolve
that root path directly; `templates/icons/` is not part of the package shape.

PPTX import uses a two-level metadata model. The temporary lossless SVG keeps native-shape metadata, hidden carriers, and preview evidence as immutable payload backing; `svg_authoring_view.py` creates the editable authoring IR bundle, whose lightweight SVGs carry document-local source refs and whose manifest stores only paths and initial hashes. Authored modes use project-canonical SVG and compact authored-preset groups only for exact registered preset matches. Mirror materializes templates from the IR and reuses converter-supported payload only for unchanged Slide-local/slot refs; fixed structural layers remain direct atoms, unsupported or edited objects keep their SVG fallback, and final templates contain no IR-only refs. Export compiles only the declared SVG structure and never infers ownership.

Both scopes retain `kind: layout` or `kind: deck` in portable frontmatter. `output_scope` and `target_project` stay in the workflow brief and are not persisted into `design_spec.md`.

Before any final write, resolve the selected workspace root, require an empty `templates/` root, and check all planned image and icon destination filenames for conflicts. Check a preview-PPTX destination when review was requested or the confirmed roster contains multiple Masters. Project scope additionally requires an initialized target project. Fail before writing anything; never merge or overwrite.

### Segment partition

To make multi-path fusion override cleanly, every field belongs to a named segment. **Default fusion granularity is whole-segment replacement**:

| Segment | Sections it contains | Override owner |
|---|---|---|
| **Identity** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand |
| **Structure** | Portable canvas/page-type metadata, structure-owned Signature rules, SVG Page Roster, and the SVG Master/Layout/slot contract | layout |
| **Middle** | Template Overview (use cases / design intent / page rhythm narrative) | deck only; brand / layout don't write this |

### Why Deck is its own kind

A deck is the **full identity + structure reference** derived from an existing PPT or confirmed design direction — its geometry, color palette, and typefaces form one coherent system. Its value is "validated cohesion", which a free layout + brand combo can't always reach.

Its construction depends on replication mode. `standard` / `fidelity` author a new system from visual reference; mirror maps validated source identities and parentage one-to-one into a new workspace. Once packaged, either form is a complete reference solution that can be overridden by an explicitly supplied brand or layout.

---

## 2. `design_spec.md` schema per kind

The schema only specifies the **required** fields. "Don't write what isn't necessary" — if a field isn't listed here, don't add it.

### Brand schema

**Frontmatter**

```yaml
---
brand_id: <slug>
kind: brand
summary: <one-line use cases, including primary color>
primary_color: "<HEX>"
---
```

**Body sections** (full identity segment)

| § | Title | Required fields |
|---|---|---|
| I | Brand Overview | Brand Name / Use Cases / Tone |
| II | Color Scheme | role / HEX / provenance (`fact` official truth \| `approx` derived) / notes |
| III | Typography | role / family / weight |
| IV | Logo | file / form / usage + clearspace and lockup rules |
| V | Voice & Tone | formality / person / emoji / abbreviation policy |
| VI | Icon Style | preference (stroke / filled / duotone …) + recommended libraries |

**Forbidden**: canvas viewBox, page types, SVG roster — those are layout's responsibility.

### Layout schema

**Frontmatter**

```yaml
---
layout_id: <slug>
kind: layout
category: general | scenario | government | special
native_structure_mode: structured
summary: <one-line use cases>
keywords: [tag1, tag2, tag3]
canvas_format: <ppt169 | ppt43 | a4 | ...>
canvas_width: <pixels>
canvas_height: <pixels>
canvas_viewbox: "0 0 <width> <height>"
source_canvas_width: <pixels>     # when a PPTX/SVG source canvas is known
source_canvas_height: <pixels>
source_viewbox: "0 0 <width> <height>"
replication_mode: standard | fidelity | mirror
page_count: <N>
page_types: [<cover, toc, chapter, content, ending, ...>]
---
```

**Body sections** (personality-only structure segment)

| § | Title | Required fields |
|---|---|---|
| IV | Signature Design Elements | Layout-specific grid, zones, image behavior, density rhythm, neutral framing, and slot conventions |
| V | Page Roster | Every SVG file, Layout key, picker name, intended content, and slot behavior |

`Placeholder Overrides` is conditional and appears only when the layout changes
the canonical authoring vocabulary. The frontmatter `summary` carries concise
selection context. Layouts omit the deck-only Template Overview.

**Forbidden**: Color Scheme, Typography, brand logo, brand voice & tone, Icon Style, or official-truth color (`provenance: fact`). Neutral SVG paint is allowed only as review scaffolding; it is not an identity segment. Color and typography are decided in the Strategist confirmation stage or supplied by another template kind.

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
category: brand | general | scenario | government | special
native_structure_mode: structured
summary: <one-line use cases>
keywords: [tag1, tag2, tag3]
canvas_format: <ppt169 | ...>
canvas_width: <pixels>
canvas_height: <pixels>
canvas_viewbox: "0 0 <width> <height>"
source_canvas_width: <pixels>     # when a PPTX/SVG source canvas is known
source_canvas_height: <pixels>
source_viewbox: "0 0 <width> <height>"
replication_mode: standard | fidelity | mirror
page_count: <N>
primary_color: "<HEX>"
---
```

**Body sections** (personality-only complete reference)

| § | Title | Segment |
|---|---|---|
| I | Template Overview | Middle |
| II | Color Scheme | Identity |
| III | Typography | Identity; omit only when the shared default stack is used |
| IV | Signature Design Elements | Template-specific identity motifs and reusable structural grammar |
| V | Page Roster | Structure |
| VI | Assets | Identity/supporting assets; omit when none |
| VII | Placeholder Overrides | Structure vocabulary; omit when none |

Portable canvas fields, `page_count`, and the explicit SVG roster carry the
rest of the structure contract. General spacing, font-ratio, SVG, and
placeholder rules remain centralized and are not copied into each deck spec.
Deck still owns the complete identity + structure reference; omitted
conditional sections mean “shared default or no asset”, not “another kind owns
this segment”.

---

## 3. The three index files

Each index maps one-to-one with its physical directory; fields are trimmed to what Strategist actually needs to pick (following the "meta + summary" pattern from `charts_index.json`, but preserving structured metadata that helps selection).

These indexes cover library scope only. A project-root workspace is intentionally absent from all three indexes and remains usable through its explicit `projects/<name>/` path. Because both scopes use the same workspace shape, moving or copying the complete core workspace between them does not require asset-path rewriting; only library registration changes.

### `templates/brands/brands_index.json`

```json
{
  "<brand_id>": {
    "summary": "Anthropic brand identity — AI/LLM tech talks, developer conferences",
    "primary_color": "#D97757"
  }
}
```

- Keep `primary_color` — Strategist needs the dominant color at first glance when picking a brand
- Drop `keywords` — summary already carries the English equivalents; AI matches via natural language (same approach as the charts library)

### `templates/layouts/layouts_index.json`

```json
{
  "<layout_id>": {
    "summary": "Standard academic defense layout — cover/toc/chapter/content/ending",
    "canvas_format": "ppt169",
    "page_count": 5,
    "page_types": ["cover", "toc", "chapter", "content", "ending"]
  }
}
```

- Add `canvas_format` / `page_count` / `page_types` — Strategist needs to judge "can this skeleton hold my deck?" quickly
- No `primary_color` — layouts have no identity

### `templates/decks/decks_index.json`

```json
{
  "<deck_id>": {
    "summary": "China Telecom government-enterprise briefing deck",
    "canvas_format": "ppt169",
    "page_count": 5,
    "primary_color": "#XXXXXX"
  }
}
```

- Includes `primary_color` (decks carry identity) + structural metadata
- Does not expand `page_types` — decks share the same page-type set as layouts; redundant to record

---

## 4. Multi-path fusion and conflict resolution

### Override priority (implicit dispatch)

When the user supplies a set of paths in their initial message, Step 3 fuses them into `<project>/templates/design_spec.md` per the table below:

| User paths | Fusion behavior |
|---|---|
| (none) | Skip Step 3, free design |
| brand only | Copy brand wholesale; structure stays free design |
| layout only | Copy layout wholesale; identity stays free design (Strategist fields e/f/g decide) |
| deck only | Copy deck wholesale |
| brand + layout | brand provides identity, layout provides structure (follows existing SKILL.md fusion table) |
| brand + deck | brand overrides deck's identity segment at segment level; structure + middle come from deck |
| layout + deck | layout overrides deck's structure segment at segment level; identity + middle come from deck |
| brand + layout + deck | brand overrides identity + layout overrides structure + deck provides middle; deck's original identity/structure segments are discarded wholesale |

### Whole-segment replacement (default granularity)

Fusion defaults to **whole-segment integer replacement** — e.g. on deck + brand, the entire Color Scheme / Typography / Logo / Voice / Icon Style five sections come from brand. **No implicit field-level mixing** (you will never get "primary from brand, secondary from deck").

Field-level micro-adjustment goes through the existing Strategist confirmation stage path — the user says in chat "use the anthropic brand but change primary to #FF0000", and Strategist adjusts fields e/g. Step 3 fusion does not add field-level syntax.

### Same-kind multiple paths = git-style conflict resolution

User supplies `brands/anthropic` + `brands/google` (or any same-kind permutation):

```
AI: You supplied two brands. Detected segment-level conflicts:
    - Color Scheme (Anthropic orange-red vs Google multi-color)
    - Typography (Styrene/AnthropicSans vs GoogleSans/Roboto)
    - Logo (Anthropic mark vs Google mark)
    - Voice & Tone (restrained vs friendly)
    - Icon Style (stroke vs filled)

    (a) all from Anthropic / (b) all from Google / (c) pick per segment?
```

Rules:
- No implicit ordering — every cross-source segment difference is reported as a conflict
- Only when the user picks `(c)` does AI walk through each segment
- Field-level conflict resolution is out of scope — segment-level only
- `layout × 2`, `deck × 2`, `brand × 2` handled the same way
- Max two of any one kind (more than that — ask the user to converge in chat first)

### Provenance

When fusion happens (any multi-path case), the resulting `<project>/templates/design_spec.md` carries a provenance block immediately under its H1:

```markdown
> **Fused from:**
> - deck: `templates/decks/china_merchants_bank/` (base)
> - brand: `templates/brands/anthropic/` (identity override)
> - layout: `templates/layouts/presentation_core/` (structure override)
> - conflicts resolved: Color Scheme from anthropic (user picked a)
```

This lets both AI and humans trace which segment came from where.

---

## 5. Relationship with SKILL.md Step 3

**Trigger rule stays path-based** — an explicit workspace-root path is still required (see [[feedback-template-explicit-path-only]]), and bare names never trigger. Step 3 first resolves `<workspace>/templates/design_spec.md`; for directory-shape compatibility, it also accepts a flat root containing `<workspace>/design_spec.md` when the SVGs already satisfy the current contract. Packages using legacy semantics such as `native_structure_mode: template`, missing Master identity, direct atomic placeholders, or distillation-era markers are rejected; `create-template` must produce a new workspace before generation continues. The only narrow handoff exception is a `create-template` run in the current conversation: after validation, it may pass its exact workspace root directly into Step 3. The `kind` field decides **how AI handles the path after triggering**:

| User path's `kind` | Step 3 action (per-kind branch) |
|---|---|
| `kind: brand` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| `kind: layout` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| `kind: deck` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| Multi-path | Fuse one `design_spec.md` per the table above, then merge the existing portable roots after resolving collisions |
| Same-kind multiple | Run the "git-style conflict resolution" prompt above to determine the merge |

Bitmaps share the workspace `images/` pool and template SVGs reference them through `../images/`. If the explicit input root is already the target project's root, Step 3 consumes the workspace in place: do not copy it onto itself and do not move its assets again. Otherwise, the complete core workspace is portable: it may be copied from a project root to a library root, from the library to a project, or reused from another workspace without changing its internal structure. Registration is the only scope-specific step.

### Strategist confirmation stage narrowing per kind

When a deck path is supplied, the user already has a complete solution; the Strategist confirmation stage narrows to "target audience / page count / outline / tone tweaks" — deck-content fields. Other fields reuse the locked values directly. The narrowing rules live in `references/strategist.md` and `spec_lock_reference.md`.

---

## 6. Relationship with routes and child workflows

| Route or child workflow | Produces |
|---|---|
| `workflows/create-template.md` | Fixed Create Template entry and shared scope, confirmation, preflight, structured-authoring, registration, completion, and handoff contract; dispatches exactly one child workflow |
| `workflows/create-template/create-brand.md` | Identity-only Brand workspace; no SVG roster and empty optional directories are omitted |
| `workflows/create-template/create-layout.md` | Brand-neutral structural Layout workspace with a structured SVG roster |
| `workflows/create-template/create-deck.md` | Integrated identity-and-structure Deck workspace with a structured SVG roster; selected by default when both segments are requested |

In library scope, the frontmatter `kind` field determines which workspace parent is used under `templates/brands/` / `templates/layouts/` / `templates/decks/`. Project scope keeps the same kind semantics at the project workspace root. A complete workspace may move between scopes without reshaping; add or remove only the library index registration.

---

## 7. Non-goals (rejection list paired with this framing)

- **No field-level override syntax in the fusion layer** — field-level adjustment uses the existing Strategist confirmation stage path
- **No batch conflict resolution for three or more of the same kind** — ask the user to narrow it down in chat first
- **No bilingual name mapping table** — templates are named in their brand / scenario's native language (Chinese templates use Chinese names; English templates use snake_case); no forced unification
- **No output-scope structure fork or CLI flag** — output scope is a `create-template` brief decision; both layout/deck scopes declare `native_structure_mode: structured`
