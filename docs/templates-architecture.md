# Template Architecture: Brand / Style / Layout / Deck

[English](./templates-architecture.md) | [Chinese](./zh/templates-architecture.md)

---

> This is the **architecture alignment document**. It defines the four template kinds at the data-model layer, the field sets of each `design_spec.md`, and the multi-path installation + segment-ownership rules. Audience: contributors and AI workflows; answers "what should / shouldn't a template directory contain; how do they combine when multiple are supplied".
>
> For user-facing usage (how to trigger, how to pick), see [`templates-guide.md`](./templates-guide.md); not repeated here.

---

## 1. The four kinds

| Kind | Library workspace root | What it writes | What it does NOT write | Originating workflow |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | Identity segment only: color / typography / logo / voice / icon style | No canvas, page structure, SVG roster | `workflows/create-template/create-brand.md` |
| **Style** | `templates/styles/<id>/` | Portable direction/method: communication method, page-role vocabulary, evidence/data expression, visual defaults, image/icon direction, advisory review focus | No identity truth, application contract, canvas, page structure, or SVG roster | `workflows/create-template/create-style.md` |
| **Layout** | `templates/layouts/<id>/` | Brand-neutral structure segment only: canvas / page structure / semantic text roles / page types / SVG roster | No brand identity and no recurring communication application | `workflows/create-template/create-layout.md` |
| **Deck** | `templates/decks/<id>/` | A recurring presentation family: descriptive application context + integrated identity + structure | — | `workflows/create-template/create-deck.md` |

Every newly created Layout/Deck SVG is a complete preview with root Master/Layout key and picker names, direct atomic Master/Layout elements, and top-level semantic slot groups. A normal slot has positive design-zone bounds and exactly one compatible carrier; composite `object` regions use explicit proxy binding, and zero-slot Layouts are valid. These specialized markers are authoritative; minimal `data-pptx-role` hints are added only for structural page-frame behavior they cannot express. Create Template derives `standard` / `fidelity` / `mirror` internally from the natural-language intent and source evidence. Authored strategies create new SVGs and structure; mirror materializes validated source facts. Strategist later derives strict/adaptive exporter behavior from the actual prototypes and current content. None of these implementation values is a required user choice. Generate accepts only the current nested workspace contract; older flat or semantic-legacy packages must be rebuilt through Create Template and are never upgraded in place.

The four are **parallel reusable-rule bundles**, not PowerPoint package-object types. In library scope, the physical directory and the frontmatter `kind` field correspond one-to-one:

Each installed spec keeps its own `kind` and id; there is no merged project spec and no combined capability label. The routing consequence is derived while reading: structure comes from an installed Layout or Deck, identity from an installed Brand or Deck, direction from an installed Style. A project-local Brand + Layout pair therefore has both capabilities installed without being promoted into a reusable library Deck or inventing application context. The current project's Stage-1 communication contract supplies that context. Strategist derives the template application plan internally; confirmation exposes the editable natural-language plan, not internal reuse/adherence mode controls.

```yaml
# templates/brands/anthropic/templates/design_spec.md
---
kind: brand
...
---

# templates/styles/consulting-decision/templates/design_spec.md
---
kind: style
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
| **Style** | No reusable package structure; confirmed method and visual defaults guide flat Slide-local authoring |
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
Deck, or the current project—not another template kind. Style fallback colors
and fonts are proposal seeds, not Theme identity truth.

### Output scope is separate from kind

`create-template` confirms where a workspace is placed. This execution choice does not add another kind and does not add a PPTX structure mode:

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

Empty optional directories are omitted; do not add placeholder files. A preview
PPTX is derived review evidence, not a source template asset. It is generated
on request and is mandatory for a multi-Master package gate. Step 3 records the
workspace root as candidate input without reading its content. After Stage 1
selects it, the apply stage consumes `templates/` plus any existing `images/`
and `icons/`; it ignores `exports/`. Library `exports/` directories are
Git-ignored.

Imported vectors use `data-icon="imported/<name>"` and have one canonical file
at `icons/imported/<name>.svg`. Workspace-aware validation and export resolve
that root path directly; `templates/icons/` is not part of the package shape.

PPTX import uses a two-level metadata model. The temporary lossless SVG keeps native-shape metadata, hidden carriers, and preview evidence as immutable source/package evidence; `svg_authoring_view.py` creates the editable authoring IR bundle, whose lightweight SVGs carry document-local source refs and whose manifest stores only paths and initial hashes. Authored modes use project-canonical SVG and compact authored-preset groups only for exact registered preset matches. Mirror publishes the reviewed current IR as its visible tree; source refs validate identity and recover only supported non-visible semantics, fixed structural layers remain direct atoms, unsupported or edited objects keep their SVG fallback, and final templates contain no IR-only refs. Export compiles only the declared SVG structure and never infers ownership.

Both scopes retain their selected `kind` in portable frontmatter. `output_scope` and `target_project` stay in the workflow brief and are not persisted into `design_spec.md`.

Before any final write, resolve the Design Spec and every real destination. Library scope requires an empty `templates/` root. Project scope requires an initialized project and rejects a bare spec, a same-kind spec, or invalid qualified naming; distinct kinds may coexist. Adding Deck beside Layout preserves the Layout roster, while adding Layout beside Deck uses isolated validation and an atomic structural replacement. Both scopes reject unrelated asset and preview collisions before writing. Never leave partial output.

### Segment partition

To make multi-path ownership resolve cleanly, every field belongs to a named segment. **A resolved segment is applied whole**:

| Segment | Sections it contains | Override owner |
|---|---|---|
| **Identity** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand |
| **Direction / method** | Communication Method / Page Role Vocabulary / Evidence & Data Expression / Visual System Defaults / Image & Icon Direction / Review Focus | style; defaults remain subordinate to user-confirmed choices and owning identity/structure segments |
| **Structure** | Portable canvas/page-type metadata, structure-owned Signature rules, SVG Page Roster, and the SVG Master/Layout/slot contract | layout |
| **Application** | Template Overview: recurring situations, audiences/outcomes, delivery assumptions, and representative narrative/page roles | deck only; brand / layout don't write this |

### Why Deck is its own kind

A Deck encodes a **recurring presentation family**, not merely a pre-combined
Brand and Layout. It describes the communication situations the template
serves, the audience outcomes it supports, and representative narrative/page
roles. Identity and structure are integrated around that context, while the
current Strategist decides which prototypes and content to use.

`standard` / `fidelity` inspect the full confirmed source inventory and author a
new complete system. Mirror emits one complete prototype per source Slide and
preserves only that Slide roster plus each Slide's reachable Layout/Master
parentage; source Layouts or Masters that no source Slide reaches are outside
the mirror contract. Authored modes may re-author useful unreferenced source
structures as new complete Slide prototypes. Mirror preserves those in-scope
source facts but does not prove that the source is a reusable Deck: creation
still has to identify the stable application rules.
A source that yields only identity becomes Brand; reusable method and visual
direction without prototypes becomes Style; a brand-neutral reusable structure
becomes Layout; a branded structural system or scenario-bearing content grammar
becomes Deck.

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

### Style schema

**Frontmatter**

```yaml
---
style_id: <slug>
kind: style
summary: <one-line portable method and visual direction>
keywords: [tag1, tag2, tag3]
---
```

**Body sections** (direction/method segment)

| § | Title | Required content |
|---|---|---|
| I | Style Overview | Name, broad best fit, reusable intent, and sources; no bound audience/outcome |
| II | Communication Method | Preferred mode seed, argument flow, page-message discipline, and evidence discipline |
| III | Page Role Vocabulary | Open roles with communication jobs, evidence obligations, and composition tendencies; no order/count |
| IV | Evidence & Data Expression | Claim/evidence rules, fact/assumption/implication/recommendation distinction, chart/table/source guidance |
| V | Visual System Defaults | Visual-style seed, composition, density, decoration, rhythm, and optional fallback palette/type defaults |
| VI | Image & Icon Direction | Rendering, usage, and treatment guidance without an inventory or page mapping |
| VII | Review Focus | Extra checks used only when the user separately enables visual review |

Style writes no SVG and never owns official Brand identity, Deck application,
canvas, page count/order, Master/Layout/placeholder structure, or page-specific
resources. Its palette and typography values are overrideable fallbacks:
user-confirmed choices and Brand/Deck identity values take precedence. Review
Focus cannot activate visual review. `kind: style` identifies this reusable
package; it is distinct from the final Stage-2 `visual_style` choice and from the
internal `template_reuse_scope: style` flat-export value.

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

## 3. The four index files

Each of these four indexes maps one-to-one with its physical directory, and its fields are trimmed to what Strategist needs to select a reusable workspace. Visualization uses a separate boundary: planning reads the objective [`chart-vocabulary.md`](../skills/ppt-master/templates/charts/chart-vocabulary.md) and [`table-vocabulary.md`](../skills/ppt-master/templates/tables/table-vocabulary.md), while [`charts_index.json`](../skills/ppt-master/templates/charts/charts_index.json) and [`tables_index.json`](../skills/ppt-master/templates/tables/tables_index.json) remain machine registries. Qualitative Structure has no index because Executor generates it from page relationships.

These indexes cover library scope only. A project-root workspace is intentionally absent from all four indexes and remains usable through its explicit `projects/<name>/` path. Because both scopes use the same workspace shape, moving or copying the complete core workspace between them does not require asset-path rewriting; only library registration changes.

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

### `templates/styles/styles_index.json`

```json
{
  "<style_id>": {
    "summary": "Answer-first, evidence-led decision-document defaults without page prototypes or brand identity",
    "keywords": ["consulting", "decision-support", "evidence"]
  }
}
```

- Keep `keywords` because method/direction discovery is semantic and has no structural roster to summarize
- Do not add canvas, page count, or primary color; Style owns neither structure nor identity truth

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

## 4. Multi-path installation and segment ownership

### Installation copies; it never merges

When Stage 1 confirms registered and/or specified workspace roots, the
post-confirmation apply stage parses every root's real `kind` and installs each
selected workspace as **its own** project-local file:

```
<project>/templates/design_spec.brand.mckinsey.md
<project>/templates/design_spec.style.consulting-decision.md
<project>/templates/design_spec.layout.presentation_core.md
```

The body of each file is copied unchanged; only one provenance line is
prepended under its H1:

```markdown
> **Installed from**: `skills/ppt-master/templates/brands/mckinsey/` (library)
```

There is no merged project spec and no combined capability label. A bare
`<project>/templates/design_spec.md` is the older single-kind shape: that
project is itself one workspace and is never consumed as an installed template.
Current project-scope Create Template writes the kind-qualified name instead, so
the two shapes never share one directory — mixing them is rejected rather than
silently resolved.

`library` / `explicit` records discovery provenance only and never changes
ownership.

### Segment ownership is resolved while reading

The consuming role — Default final Stage 2, or Quick's agent before authoring —
reads every installed spec and, when Layout/Deck owns structure, every installed
SVG prototype, then resolves these segments in context:

| Segment | Starting owner |
|---|---|
| Identity | Brand, otherwise Deck, otherwise unresolved until final Stage 2; Style supplies fallback candidates only |
| Direction / method | Style, otherwise unresolved until final Stage 2; actual Deck prototypes and Signature facts inform compatibility only |
| Structure | Layout when present, otherwise Deck, otherwise unresolved/free design until final Stage 2 |
| Reusable application context | Deck only; retained for final Stage-2 comparison, never used as the current project's application contract |

Current user instructions and final confirmation override every starting
owner. Brand identity remains authoritative over Style palette/type fallbacks.
Style alone, or Style with Brand, uses flat page authoring. Style with a Layout
or Deck follows the selected structural source. A Style never upgrades or
downgrades structure by itself.

**An owned segment governs visual weight, not only values.** When a segment
owner declares that a value should dominate, recede, or stay rare, that
instruction carries the same authority as the value itself — a Style's
whitespace or composition tendency never demotes a Brand's declared dominant
color into an incidental accent.

Before combining Style with Layout/Deck, verify that its communication method
and composition expectations can be realized by that reusable context and
structure. On mismatch, surface the conflicting template segments; do not
silently mix fields or retain a promise that the selected structure cannot
satisfy. Current-project fit begins only in final Stage 2 after Stage 1 is confirmed.

### Whole-segment application (default granularity)

A resolved segment is applied **whole** — e.g. on deck + brand, the entire
Color Scheme / Typography / Logo / Voice / Icon Style set comes from brand.
**No implicit field-level mixing** (you will never get "primary from brand,
secondary from deck").

Field-level micro-adjustment goes through the existing Strategist confirmation
stage path — the user says in chat "use the anthropic brand but change primary
to #FF0000", and Strategist adjusts fields e/g. Installation adds no
field-level syntax.

### Selection conflicts

The complete selection contains at most one contribution per kind. Layout and
Deck may coexist; Layout owns structure. A specified multi-kind root is atomic
and may coexist only with registered roots of non-overlapping kinds. Default rejects conflicts in the
Stage-1 selector and server receipt; Quick requires a narrower exact-root set
in chat. Installation never averages same-kind specs or chooses by path order.

### Traceability

Because nothing is merged, the installed set is self-describing: the file name
carries kind and id, the provenance line carries the source root, and the
remaining body is unchanged. Tracing which segment came from where is a
directory listing, not a merge reconstruction.

---

## 5. Relationship with Generate PPTX Stage 1

Default Generate [Step 3](../skills/ppt-master/workflows/generate-pptx.md#step-3-template-candidate-preparation)
only prepares candidate input. Stage 1 presents the communication contract and
the switchable free-design/template choice together. Ordinary requests start in
free design with detailed controls collapsed; explicit template intent or any
exact root starts in template mode. Exactly one supplied root is preselected,
while multiple roots remain unselected candidates. A bare template/brand name
or style phrase never resolves to or preselects a workspace. For every selected
root, the post-confirmation apply stage resolves either one library bare spec or
all project-qualified specs. Flat-root packages are not template workspaces.
Packages using legacy semantics such as
`native_structure_mode: template`, missing Master identity, direct atomic
placeholders, or distillation-era markers are rejected; `create-template` must
produce a new workspace before generation continues. The `kind` field decides
**how AI handles the selected path**:

| User path's `kind` | Step 3 action (per-kind branch) |
|---|---|
| `kind: brand` | Install the qualified identity spec and root-owned assets; structure remains free unless the set also contains Layout or Deck |
| `kind: style` | Install the qualified direction/method spec; require no Style-owned roster or assets and keep generated pages flat unless the set contains Layout or Deck |
| `kind: layout` | Install the qualified structure spec plus its root's SVG roster and assets; it takes structural precedence over Deck |
| `kind: deck` | Install the qualified application/identity/structure spec and assets; install its SVG roster only when no Layout is selected |
| Multi-kind root | Preserve every qualified spec and map shared assets once; keep exactly the effective Layout-or-Deck roster |
| Selection conflict | Reject duplicate kinds before installation |

Bitmaps share the workspace `images/` pool and template SVGs reference them through `../images/`. If the explicit input root is already the target project's root, the apply stage consumes the workspace in place: do not copy it onto itself and do not move its assets again. Otherwise, a project root is directly reusable by another project. Moving one contribution into the library keeps its spec body but changes placement from a qualified project filename to the bare spec inside a single-kind library workspace, followed by registration.

### Strategist confirmation stage behavior per kind

Installing a template does not narrow away the communication question. Stage 1 confirms the same open communication contract together with, but independently from, the template choice. The communication recommendation uses only the current request, source facts, conversation constraints, and project initialization; even template canvas is excluded. Only after Stage 1 closes and any selection is installed does final Stage 2 inspect that state and confirm the complete solution and production plan. Brand supplies identity constraints while structure stays free; Style supplies method and visual-default seeds while remaining flat; Layout exposes structural capability; Deck contributes descriptive reusable application context for comparison, not the current project's contract. For Style-only use, Strategist does not look for prototypes and deterministically records `template_reuse_scope: style` with flat structure. It otherwise inspects every effective prototype—Layout when present, otherwise Deck—and current content, then authors one page/prototype plan and records `mirror`, `layout`, or `style` only as internal exporter values. A mirror-authored workspace therefore enables literal reuse but never forces it.

Default still presents three template-compliant design directions. The Recommended direction is the viable one that most fully expresses the resolved template context; the other two vary only dimensions left open by that context and the user. Quick materializes no candidate set and directly executes that same recommended-direction rule.

Default confirms one natural-language `template_application` paragraph; Quick
freezes the same decision only in active context. Explicit user wording wins,
otherwise the agent decides from content and the complete SVG roster, with
reference-led use as the fallback. Reference, augment-only, and
replacement-only are descriptive patterns rather than fixed fields. Every
prototype-specific exception names the exact SVG basename. Runtime choice does
not change structural capability: free/Brand/Style-only output is flat, while
Layout/Deck output preserves explicit Master/Layout/slot metadata unless the
user explicitly requests visual-only use. Confirm UI exposes Free design / Use
templates and the prose field, but not internal reuse/adherence fields. Planning
semantics live in `references/strategist.md` and
`references/strategist-template.md`; `templates/schemas/spec_lock.schema.json`
owns the durable Default machine structure, while Quick validates the all-page
SVG structure contract directly.

---

## 6. Relationship with routes and child workflows

| Route or child workflow | Produces |
|---|---|
| `workflows/create-template.md` | Fixed Create Template entry and shared scope, confirmation, preflight, structured-authoring, registration, completion, and handoff contract; dispatches exactly one child workflow |
| `workflows/create-template/create-brand.md` | Identity-only Brand workspace; no SVG roster and empty optional directories are omitted |
| `workflows/create-template/create-style.md` | Direction/method-only Style workspace; no SVG roster, identity truth, application contract, native structure, or preview PPTX |
| `workflows/create-template/create-layout.md` | Brand-neutral structural Layout workspace with a structured SVG roster |
| `workflows/create-template/create-deck.md` | Recurring application contract with integrated identity/structure and a structured SVG roster; selected when the reusable artifact is branded or scenario-bearing, not merely because the source is a complete PPTX |

**One schema, two landing points.** Templates are a single contract that lands at two layers, and the only difference is what names the Design Spec:

| Layer | Container | Design Spec |
|---|---|---|
| Skill library | `templates/<kind_dir>/<template_id>/` already names the kind and id | `templates/design_spec.md` |
| Project | one flat `templates/` shared across kinds | `templates/design_spec.<kind>.<id>.md` |

The container disambiguates, and the filename carries only what the container cannot. A project root therefore holds at most one spec per kind while all four kinds may coexist, and each filename kind/id must match frontmatter `kind` and the matching `<kind>_id`; the bare and qualified shapes never mix in one directory. One `templates/` carries one active SVG roster: Layout when present, otherwise Deck. Deck's other segments remain installed when its structural roster is shadowed. Because the schema itself does not change with the layer, a project spec needs no field added to enter the library and none removed to leave it, and an installed spec is indistinguishable from one authored in place.

Selection follows the same principle: the unit is the workspace **root**, not the kind. A root contributes every kind it exposes, so pointing at a project that holds a Brand plus a Style applies both. Browsing the library by kind is only a way to find a root — `library` and `explicit` record how a root was discovered, never what it owns.

In library scope, the frontmatter `kind` field determines which workspace parent is used under `templates/brands/` / `templates/styles/` / `templates/layouts/` / `templates/decks/`. Project scope keeps the same kind semantics at the project workspace root. Project-to-project reuse preserves the complete root. Moving one contribution into or out of the single-kind library preserves its spec schema and assets but changes the spec filename placement and index registration.

---

## 7. Non-goals (rejection list paired with this framing)

- **No field-level override syntax in the installation layer** — field-level adjustment uses the existing Strategist confirmation stage path
- **No duplicate-kind selection** — narrow the chosen roots before installation; Layout plus Deck is resolved by structural precedence
- **No bilingual name mapping table** — templates are named in their brand / scenario's native language (Chinese templates use Chinese names; English templates use snake_case); no forced unification
- **No output-scope structure fork or CLI flag** — output scope is a `create-template` brief decision; both layout/deck scopes declare `native_structure_mode: structured`, while Brand/Style remain roster-free
- **No Theme kind** — Theme projects resolved identity from Brand, Deck, or the current project; Style fallback values are not identity truth
- **No automatic visual review from Style** — Review Focus supplements an already-enabled review pass and never triggers it
- **No automatic promotion of Brand + Layout into a reusable library Deck** — the composition may route as a project-local deck-capability bundle, while a reusable Deck still requires an application contract
