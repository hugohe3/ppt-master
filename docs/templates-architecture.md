# Template Architecture: Brand / Layout / Deck

> This is the **architecture alignment document**. It defines the three template kinds at the data-model layer, the field sets of each `design_spec.md`, and the multi-path fusion + conflict resolution rules. Audience: contributors and AI workflows; answers "what should / shouldn't a template directory contain; how do they combine when multiple are supplied".
>
> For user-facing usage (how to trigger, how to pick), see [`templates-guide.md`](./templates-guide.md); not repeated here.

---

## 1. The three kinds

| Kind | Physical dir | What it writes | What it does NOT write | Originating workflow |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | Identity segment only: color / typography / logo / voice / icon style | No canvas, page structure, SVG roster | `workflows/create-brand.md` |
| **Layout** | `templates/layouts/<id>/` | Structure segment only: canvas / page structure / page types / SVG roster | No brand identity (no logo, no locked brand color) | `workflows/create-template.md` (layout branch) |
| **Deck** | `templates/decks/<id>/` | All segments: identity + structure + middle (template overview) | — | `workflows/create-template.md` (deck branch, default) |

The three are **parallel reference bundles**. The physical directory and the frontmatter `kind` field correspond one-to-one:

```yaml
# templates/brands/anthropic/design_spec.md
---
kind: brand
...
---

# templates/layouts/academic_defense/design_spec.md
---
kind: layout
...
---

# templates/decks/招商银行/design_spec.md
---
kind: deck
...
---
```

### Segment partition

To make multi-path fusion override cleanly, every field belongs to a named segment. **Default fusion granularity is whole-segment replacement**:

| Segment | Sections it contains | Override owner |
|---|---|---|
| **Identity** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand |
| **Structure** | Canvas Specification / Page Structure / Page Types / SVG Roster | layout |
| **Middle** | Template Overview (use cases / design intent / page rhythm narrative) | deck only; brand / layout don't write this |

### Why Deck is its own kind

A deck is the **full replica** of an existing PPT — the SVG geometry was drawn for that color palette and those typefaces, and identity + structure have been combat-tested together in the source deck. Its value is "validated cohesion", which a free layout + brand combo can't always reach.

But a deck is **not "an immutable replica"** — it's "a replica that serves as the default base, overridable by explicitly-supplied brand / layout". This gives users maximum freedom: by default you get a complete solution; when needed, swap identity or structure explicitly.

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
summary: <one-line use cases>
canvas_format: <ppt169 | ppt43 | a4 | ...>
page_count: <N>
page_types: [<cover, toc, chapter, content, ending, ...>]
---
```

**Body sections** (full structure segment + Template Overview)

| § | Title | Required fields |
|---|---|---|
| I | Template Overview | Use Cases / Design Intent / Page Rhythm suggestions |
| II | Canvas Specification | Format / Dimensions / viewBox / Margins / Content Area |
| III | Page Structure | General Layout Grid / Decorative DNA / Navigation rules |
| IV | Page Types | Per-page role (cover / toc / chapter / content / ending …) + variant descriptions |
| V | SVG Page Roster | File list + purpose, each file mapped to a III/IV role |

**Forbidden**: brand logo, brand voice & tone, official-truth color (`provenance: fact`) — those belong to brand. Layouts have no fallback color or typography by definition: identity segments are not written here; color and typography are decided live in Strategist's Eight Confirmations.

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
summary: <one-line use cases>
canvas_format: <ppt169 | ...>
page_count: <N>
primary_color: "<HEX>"
---
```

**Body sections** (full identity + full structure + middle)

| § | Title | Segment |
|---|---|---|
| I | Template Overview | Middle |
| II | Canvas Specification | Structure |
| III | Color Scheme (with provenance) | Identity |
| IV | Typography | Identity |
| V | Logo | Identity |
| VI | Voice & Tone | Identity |
| VII | Icon Style | Identity |
| VIII | Page Structure | Structure |
| IX | Page Types | Structure |
| X | SVG Page Roster | Structure |

> Deck is the union of all identity + structure fields, with no optional sections. This keeps fusion's segment-level replacement granularity uniform.

---

## 3. The three index files

Each index maps one-to-one with its physical directory; fields are trimmed to what Strategist actually needs to pick (following the "meta + summary" pattern from `charts_index.json`, but preserving structured metadata that helps selection).

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
    "summary": "China Merchants Bank transaction banking deck",
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
| layout only | Copy layout wholesale; identity stays free design (Strategist e/f/g confirmations decide) |
| deck only | Copy deck wholesale |
| brand + layout | brand provides identity, layout provides structure (follows existing SKILL.md fusion table) |
| brand + deck | brand overrides deck's identity segment at segment level; structure + middle come from deck |
| layout + deck | layout overrides deck's structure segment at segment level; identity + middle come from deck |
| brand + layout + deck | brand overrides identity + layout overrides structure + deck provides middle; deck's original identity/structure segments are discarded wholesale |

### Whole-segment replacement (default granularity)

Fusion defaults to **whole-segment integer replacement** — e.g. on deck + brand, the entire Color Scheme / Typography / Logo / Voice / Icon Style five sections come from brand. **No implicit field-level mixing** (you will never get "primary from brand, secondary from deck").

Field-level micro-adjustment goes through the existing Strategist Eight Confirmations path — the user says in chat "use the anthropic brand but change primary to #FF0000", and Strategist adjusts in confirmations e/g. Step 3 fusion does not add field-level syntax.

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
> - deck: `templates/decks/招商银行/` (base)
> - brand: `templates/brands/anthropic/` (identity override)
> - layout: `templates/layouts/academic_defense/` (structure override)
> - conflicts resolved: Color Scheme from anthropic (user picked a)
```

This lets both AI and humans trace which segment came from where.

---

## 5. Relationship with SKILL.md Step 3

**Trigger rule unchanged** — still "explicit directory path only" (see [[feedback-template-explicit-path-only]]). The `kind` field decides **how AI handles the path after triggering**:

| User path's `kind` | Step 3 action (per-kind branch) |
|---|---|
| `kind: brand` | Copy design_spec + logos + asset subdirs to `<project>/templates/` |
| `kind: layout` | Copy design_spec + SVG roster + assets to `<project>/templates/` |
| `kind: deck` | Copy design_spec + SVG roster + logos + all assets to `<project>/templates/` |
| Multi-path | Fuse into one `design_spec.md` per the table above; merge SVG / logo files from each source |
| Same-kind multiple | Run the "git-style conflict resolution" prompt above to determine the merge |

### Strategist Eight Confirmations narrowing per kind

When a deck path is supplied, the user already has a complete solution; the Eight Confirmations narrow to "target audience / page count / outline / tone tweaks" — deck-content fields. Other fields reuse the locked values directly. The narrowing rules live in `references/strategist.md` and `spec_lock_reference.md`.

---

## 6. Relationship with workflows

| Workflow | Produces |
|---|---|
| `workflows/create-brand.md` | brand directory (identity-only), reverse-engineered from brand assets |
| `workflows/create-template.md` | layout or deck directory, internal kind branch: default to deck (user supplies an existing PPT; extract full identity + structure); when the user explicitly says "structure only / drop the brand color", go to the layout branch |

After production, the frontmatter `kind` field determines whether the file lands under `templates/brands/` / `templates/layouts/` / `templates/decks/`.

---

## 7. Non-goals (rejection list paired with this framing)

- **No field-level override syntax in the fusion layer** — field-level adjustment uses the existing Strategist Eight Confirmations path
- **No batch conflict resolution for three or more of the same kind** — ask the user to narrow it down in chat first
- **No bilingual name mapping table** — templates are named in their brand / scenario's native language (Chinese templates use Chinese names; English templates use snake_case); no forced unification
