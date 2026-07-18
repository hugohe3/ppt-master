# Template Architecture: Brand / Layout / Deck

[English](./templates-architecture.md) | [Chinese](./zh/templates-architecture.md)

---

> This is the **architecture alignment document**. It defines the three template kinds at the data-model layer, the field sets of each `design_spec.md`, and the multi-path fusion + conflict resolution rules. Audience: contributors and AI workflows; answers "what should / shouldn't a template directory contain; how do they combine when multiple are supplied".
>
> For user-facing usage (how to trigger, how to pick), see [`templates-guide.md`](./templates-guide.md); not repeated here.

---

## 1. The three kinds

| Kind | Library workspace root | What it writes | What it does NOT write | Originating workflow |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | Identity segment only: color / typography / logo / voice / icon style | No canvas, page structure, SVG roster | `workflows/create-template/create-brand.md` |
| **Layout** | `templates/layouts/<id>/` | Brand-neutral structure segment only: canvas / page structure / semantic text roles / page types / SVG roster | No brand identity and no recurring communication application | `workflows/create-template/create-layout.md` |
| **Deck** | `templates/decks/<id>/` | A recurring presentation family: descriptive application context + integrated identity + structure | — | `workflows/create-template/create-deck.md` |

Every newly created Layout/Deck SVG is a complete preview with root Master/Layout key and picker names, direct atomic Master/Layout elements, and top-level semantic slot groups. A normal slot has positive design-zone bounds and exactly one compatible carrier; composite `object` regions use explicit proxy binding, and zero-slot Layouts are valid. These specialized markers are authoritative; minimal `data-pptx-role` hints are added only for structural page-frame behavior they cannot express. Create Template derives `standard` / `fidelity` / `mirror` internally from the natural-language intent and source evidence. Authored strategies create new SVGs and structure; mirror materializes validated source facts. Strategist later derives strict/adaptive exporter behavior from the actual prototypes and current content. None of these implementation values is a required user choice. A flat directory with `design_spec.md` at its root remains a supported compatibility shape only when its SVGs satisfy the current contract. Semantic-legacy packages must be replaced by a newly created template workspace; they are never upgraded in place.

The three are **parallel reusable-rule bundles**, not PowerPoint package-object types. In library scope, the physical directory and the frontmatter `kind` field correspond one-to-one:

The fused project-level `design_spec.md` retains the existing routing `kind`: `deck` when both identity and structure are present, `layout` when only structure is present, and `brand` when only identity is present. For a project-local Brand + Layout composition, this label means “both capabilities are installed”; it does not promote that composition into a reusable library Deck or invent application context. The current project's Stage-1 communication contract supplies that context. Strategist derives the template application plan internally; the confirmation page exposes no template mode controls.

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

# templates/decks/中国电信/templates/design_spec.md
---
kind: deck
native_structure_mode: structured
...
---
```

### Native PowerPoint objects are compilation targets

Project template kinds do not map one-to-one to PresentationML objects:

| Project contract | Native projection |
|---|---|
| **Brand** | Theme colors/fonts/effects plus logo and other fixed identity-asset rules |
| **Layout** | Master/Layout/Placeholder topology, reusable geometry, semantic text roles, and spatial slot behavior |
| **Deck** | The Brand and Layout projections plus descriptive recurring-application context and actual prototypes |

A Slide Master may contain both structural geometry and brand visuals. Source
ownership remains separated—Layout owns topology, placement, semantic text
roles, and spatial behavior; Brand owns identity values and assets. Under
downstream `layout` scope, export resolves final placeholder formatting from
those rules plus the confirmed reading mode/type scale; `mirror` preserves
literal source formatting and text topology. Export then compiles the
applicable rules into the same native Master/Layout graph. Theme is therefore
an implementation projection of resolved identity—whether supplied by Brand,
Deck, or the current project—not a fourth template kind.

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
| **Application** | Template Overview: recurring situations, audiences/outcomes, delivery assumptions, and representative narrative/page roles | deck only; brand / layout don't write this |

### Why Deck is its own kind

A Deck encodes a **recurring presentation family**, not merely a pre-combined
Brand and Layout. It describes the communication situations the template
serves, the audience outcomes it supports, and representative narrative/page
roles. Identity and structure are integrated around that context, while the
current Strategist decides which prototypes and content to use.

`standard` / `fidelity` author a new complete system from confirmed evidence;
mirror maps validated source identities and parentage one-to-one into a new
workspace. Mirror preserves source facts but does not prove that the source is
a reusable Deck: creation still has to identify the stable application rules.
A source that yields only identity becomes Brand; a brand-neutral reusable
structure becomes Layout; a branded structural system or scenario-bearing
content grammar becomes Deck.

This also constrains creation mode: Layout mirror is valid only when the source
contract is already brand-neutral and application-neutral. Removing brand
paint, fonts, logos, fixed identity objects, or reusable application rules is
authorship, so a source outside that boundary must either use `standard` /
`fidelity` to create a new Layout or retain those facts as Deck mirror.

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

**Body sections** (package-specific structure segment)

| § | Title | Required fields |
|---|---|---|
| IV | Signature Design Elements | Layout-specific grid, zones, image behavior, density rhythm, neutral framing, semantic text roles, alignment/wrapping/capacity behavior, and slot conventions |
| V | Page Roster | Every SVG file, Layout key, picker name, intended content, and slot behavior |

`Placeholder Overrides` is conditional and appears only when the layout changes
the canonical authoring vocabulary. The frontmatter `summary` carries concise
selection context. Layouts omit the deck-only Template Overview.

`category: scenario` is discovery fit only. A Layout may be optimized for a
content shape or delivery setting, but it must not prescribe the communication
objective, audience outcome, required narrative sequence, fixed boilerplate,
or example content. If those rules are reusable, create a Deck instead.

**Forbidden**: Color Scheme, brand typeface/weight identity, final resolved type scale, brand logo, brand voice & tone, Icon Style, or official-truth color (`provenance: fact`). A Layout may retain semantic text roles, alignment, wrapping, and capacity because those are structural; neutral SVG paint/font/size values are review scaffolding only. Final color and typography are resolved in the Strategist confirmation stage or supplied by another template kind.

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
category: brand | general | scenario | government | special
native_structure_mode: structured
summary: <one-line recurring presentation family and intended outcome>
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

**Body sections** (application + integrated identity/structure)

| § | Title | Segment |
|---|---|---|
| I | Template Overview | Application |
| II | Color Scheme | Identity |
| III | Typography | Identity; omit only when the shared default stack is used |
| IV | Signature Design Elements | Template-specific identity motifs and reusable structural grammar |
| V | Page Roster | Structure |
| VI | Assets | Identity/supporting assets; omit when none |
| VII | Placeholder Overrides | Structure vocabulary; omit when none |

Template Overview identifies the recurring presentation family, intended
audiences and outcomes, delivery/reading assumptions, and representative
narrative or page roles. Page Roster factually describes each prototype's
Master/Layout/slot contract, visual character, intended role, and capacity. It
must not assign required/optional/repeatable or fixed/replaceable/example-only
policy; Strategist derives those decisions for the current content.

Portable canvas fields, `page_count`, and the explicit SVG roster carry the
rest of the structure contract. General spacing, font-ratio, SVG, and
placeholder rules remain centralized and are not copied into each deck spec.
Omitted conditional sections mean “shared default or no asset”, not “another
kind owns this segment”.

---

## 3. The three index files

Each index maps one-to-one with its physical directory; fields are trimmed to what Strategist actually needs to pick, following the compact "meta + summary" pattern used by [`charts_index.json`](../skills/ppt-master/templates/charts/charts_index.json) while preserving structured metadata that helps selection.

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
    "summary": "China Telecom government-enterprise briefing for explaining a plan and aligning next actions",
    "canvas_format": "ppt169",
    "page_count": 5,
    "primary_color": "#XXXXXX"
  }
}
```

- Includes `primary_color` (decks carry identity) + structural metadata
- `summary` leads with the recurring presentation family and outcome, not merely visual tone
- The detailed application contract stays in Template Overview; this compact index does not duplicate it

---

## 4. Multi-path fusion and conflict resolution

### Override priority (implicit dispatch)

When the user supplies a set of explicit workspace-root paths, Step 3 fuses them into `<project>/templates/design_spec.md` per the table below:

| User paths | Fusion behavior |
|---|---|
| (none) | Skip Step 3, free design |
| brand only | Copy brand wholesale; structure stays free design |
| layout only | Copy layout wholesale; identity stays free design (Strategist fields e/f/g decide) |
| deck only | Copy deck wholesale |
| brand + layout | brand provides identity, layout provides structure; this is a project-local assembled input, not a reusable Deck application contract |
| brand + deck | brand overrides deck's identity segment at segment level; structure + application come from deck |
| layout + deck | layout may override deck structure only when it can express the Deck's required narrative/content roles; identity + application come from deck |
| brand + layout + deck | brand overrides identity + a compatible layout overrides structure + deck provides application; deck's original identity/structure segments are discarded wholesale |

Before applying a Layout override to a Deck, compare the Deck application
contract against the Layout's page roles, slot types, and capacity. If a
required role cannot be represented, surface a fusion conflict: keep the Deck
structure, choose another Layout, or explicitly revise the application
contract. Never retain an application promise that the selected structure
cannot satisfy.

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
> - deck: `templates/decks/中国电信/` (base)
> - brand: `templates/brands/anthropic/` (identity override)
> - layout: `templates/layouts/presentation_core/` (structure override)
> - conflicts resolved: Color Scheme from anthropic (user picked a)
```

This lets both AI and humans trace which segment came from where.

---

## 5. Relationship with Generate PPTX Step 3

**Trigger rule stays path-based** — an explicit workspace-root path is still required (see [Generate PPTX Step 3](../skills/ppt-master/workflows/generate-pptx.md#step-3-template-option)), and bare names never trigger. Step 3 first resolves `<workspace>/templates/design_spec.md`; for directory-shape compatibility, it also accepts a flat root containing `<workspace>/design_spec.md` when the SVGs already satisfy the current contract. Packages using legacy semantics such as `native_structure_mode: template`, missing Master identity, direct atomic placeholders, or distillation-era markers are rejected; `create-template` must produce a new workspace before generation continues. The only narrow handoff exception is a `create-template` run in the current conversation: after validation, it may pass its exact workspace root directly into Step 3. The `kind` field decides **how AI handles the path after triggering**:

| User path's `kind` | Step 3 action (per-kind branch) |
|---|---|
| `kind: brand` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| `kind: layout` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| `kind: deck` | Map workspace `templates/` plus existing `images/` and `icons/` to the matching project peers; ignore `exports/` |
| Multi-path | Fuse one `design_spec.md` per the table above, then merge the existing portable roots after resolving collisions |
| Same-kind multiple | Run the "git-style conflict resolution" prompt above to determine the merge |

Bitmaps share the workspace `images/` pool and template SVGs reference them through `../images/`. If the explicit input root is already the target project's root, Step 3 consumes the workspace in place: do not copy it onto itself and do not move its assets again. Otherwise, the complete core workspace is portable: it may be copied from a project root to a library root, from the library to a project, or reused from another workspace without changing its internal structure. Registration is the only scope-specific step.

### Strategist confirmation stage behavior per kind

Installing a template does not narrow away the communication question. Stage 1 always confirms the same open communication contract independently of the template. Brand supplies identity constraints while structure stays free; Layout exposes structural capability; Deck also contributes descriptive application context. After Stage 1, Strategist inspects the actual prototypes and current content, then authors one page/prototype plan and records `mirror`, `layout`, or `style` only as internal exporter values. A mirror-authored workspace therefore enables literal reuse but never forces it. The Confirm UI exposes no template-mode fields. Planning semantics live in `references/strategist.md` and `references/strategist-template.md`; `templates/schemas/spec_lock.schema.json` owns the machine structure.

---

## 6. Relationship with routes and child workflows

| Route or child workflow | Produces |
|---|---|
| `workflows/create-template.md` | Fixed Create Template entry and shared scope, confirmation, preflight, structured-authoring, registration, completion, and handoff contract; dispatches exactly one child workflow |
| `workflows/create-template/create-brand.md` | Identity-only Brand workspace; no SVG roster and empty optional directories are omitted |
| `workflows/create-template/create-layout.md` | Brand-neutral structural Layout workspace with a structured SVG roster |
| `workflows/create-template/create-deck.md` | Recurring application contract with integrated identity/structure and a structured SVG roster; selected when the reusable artifact is branded or scenario-bearing, not merely because the source is a complete PPTX |

In library scope, the frontmatter `kind` field determines which workspace parent is used under `templates/brands/` / `templates/layouts/` / `templates/decks/`. Project scope keeps the same kind semantics at the project workspace root. A complete workspace may move between scopes without reshaping; add or remove only the library index registration.

---

## 7. Non-goals (rejection list paired with this framing)

- **No field-level override syntax in the fusion layer** — field-level adjustment uses the existing Strategist confirmation stage path
- **No batch conflict resolution for three or more of the same kind** — ask the user to narrow it down in chat first
- **No bilingual name mapping table** — templates are named in their brand / scenario's native language (Chinese templates use Chinese names; English templates use snake_case); no forced unification
- **No output-scope structure fork or CLI flag** — output scope is a `create-template` brief decision; both layout/deck scopes declare `native_structure_mode: structured`
- **No fourth Theme kind** — Theme projects resolved identity from Brand, Deck, or the current project; it is not a separate user-facing reusable contract
- **No automatic promotion of Brand + Layout into a reusable library Deck** — the composition may route as a project-local deck-capability bundle, while a reusable Deck still requires an application contract
