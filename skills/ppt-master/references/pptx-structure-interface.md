> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# PPTX Structure Interface

Conditional interface for PowerPoint Master, Layout, fixed-layer, and placeholder authoring. In Generate, load only for Default `spec_lock.md pptx_structure.mode: structured` or Quick structured Slide authoring from an installed Layout/Deck owner.

**Cross-reference map**: unqualified §1.5 and §4.2 references point to [`shared-standards-core.md`](./shared-standards-core.md); this file's own sections are §1–§3. Exporter and read-back mechanics live in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md#structured-export-mechanics).

## 1. PPTX Structure Routing

Every new SVG project declares one deterministic route:

| Project | `pptx_structure.mode` | Structure metadata |
|---|---|---|
| Free-design, brand-only, `template_reuse_scope: style` | `flat` | none; omit `pptx_masters` / `pptx_layouts` / `page_pptx_layouts` / `page_layouts`; export materializes one clean project-owned Master plus one Blank Layout from the lock and keeps every object Slide-local |
| Layout/Deck template with `template_reuse_scope: mirror\|layout` | `structured` | §2; `standard` / `fidelity` templates use their authored contract, mirror templates use the validated source identities and parentage of the compact workspace |

**Quick exception**: Lock-row/Strategist statements in this file are Default-only. Quick keeps free/Brand/Style-only flat; an installed Layout/Deck owner is structured unless visual-only, with identities on SVG roots and title/body anchors inferred from slot carriers.

**Hard rule — no structure inference**: Flat export promotes and deduplicates nothing. Structured export compiles only declared root identities, atomic fixed layers, and slot groups; it never assigns Layout families, clusters pages, infers placeholders, repairs missing metadata, or migrates legacy contracts. Create a current workspace through [`create-template`](../workflows/create-template.md) before generating structured pages.

**Layout reuse**: Reuse one Layout key only when its ordered fixed Layout atoms and slot ids/types/effective indices/default bounds/binding modes are identical. Different wording, data, imagery, crop, or Slide-local carrier geometry does not create a new Layout; a genuinely different reusable contract gets a new key even when both pages are semantically `content`. A Layout may have zero slots and zero fixed atoms — valid for a cover, poster, or full-visual page; do not manufacture an empty `utility` kind or a full-page fake `object` slot.

**Adaptive change**: `strict` preserves the prototype. `adaptive` retains its Master and uses only a Layout declared in Default's plan/lock or permitted by Quick's frozen Template Application. Required atom/slot-contract changes return Default for repair/readback/validation; Quick creates a new Layout only under that permission. Never mutate a reused key.

## 2. Explicit PPTX Master / Layout / Placeholder Metadata

**Trigger**: new pages generated from a current deck/layout workspace with `template_reuse_scope: mirror|layout`. `spec_lock.md` declares `pptx_structure.mode: structured`, complete unique `pptx_masters` / `pptx_layouts` rosters, one `page_pptx_layouts` assignment per generated page, and `page_layouts` as authoring-prototype provenance.

**Project lock rows**: Master `<master_key>: <PowerPoint picker name>`; unique Layout `<layout_key>: <master_key> | <PowerPoint picker name> | <prototype source>` where the source is a generated `P<NN>` or installed `template:<basename>`; page assignment `P<NN>: <layout_key>` under `page_pptx_layouts`. SVG root values MUST match the assigned definition. A Layout key belongs to exactly one Master and is globally unique; an unused Layout uses a template SVG source and stays registered without a published carrier slide. Every structured route requires numeric `spec_lock.md` typography `title` / `body` rows — they become the Master text styles.

**Template behavior**: Strict preserves the selected prototype's Master/Layout/slot contract. Adaptive realizes only a Layout allowed by §1 and never mutates a reused key. Mirror-created prototypes preserve validated source identity, parentage, slots, meaning, and similar presentation in compact new SVG; paint/geometry nodes need not be isomorphic. `standard` / `fidelity` never make source topology authoritative; mirror does not synthesize replacement topology or fill missing facts. Imported inherited-shape visibility is an analysis fact carried by the two optional root booleans below; authored `standard` / `fidelity` templates normally omit both (see [`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary)).

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-master="master-default"` | root `<svg>` | Binds the slide to one generated Slide Master key |
| `data-pptx-master-name="Default Master"` | root `<svg>` | Master picker/display name |
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Layout picker name; defaults from the layout key |
| `data-pptx-show-master-shapes="false"` | root `<svg>` | Optional; exact lowercase `true` / `false`; the assigned Layout's `showMasterSp`, repeated identically by every SVG sharing the key; omission means `true` |
| `data-pptx-show-inherited-shapes="false"` | root `<svg>` | Optional; exact lowercase `true` / `false`; this Slide's `showMasterSp` — `false` hides inherited shapes without removing backgrounds, placeholders, parts, or parents; omission means `true` |
| `data-pptx-layer="master"` / `"layout"` | direct semantic atom | Moves one repeated static object/background into the Master or the selected Layout; ordinary `<g>` is forbidden, one validated compact authored-preset `<g>` (§1.5) is the atomic exception |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | One-page background override written as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct slot `<g id>` | Reusable Layout slot whose visible content stays Slide-local |
| `data-pptx-bounds="x y width height"` | slot `<g>` | Mandatory positive reusable design-zone frame in SVG user units, at most two decimals per value |
| `data-pptx-idx="1"` | slot `<g>` | Retains an imported source placeholder index; optional for reconstructed layouts |
| `data-pptx-carrier="true"` | one compatible direct child of a normal slot | Binds that visible child as the real Slide placeholder carrier |
| `data-pptx-binding="proxy"` | composite `object` slot `<g>` only | Keeps the visible group ordinary and creates one hidden transparent binding proxy |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

| Placeholder value | Direct carrier inside slot `<g>` | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | one `<text data-pptx-carrier="true">` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | one `<text data-pptx-carrier="true">` | `dt`, `ftr`, `sldNum` |
| `picture`, `media` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `pic`, `media` |
| `chart`, `table` | one matching `data-pptx-replace-with` marker group, marked as carrier; requires `--native-charts-and-tables` | `chart`, `tbl` |
| `object` | one text, image, basic SVG shape, or validated compact authored-preset `<g>` marked as carrier; or the slot declares `binding="proxy"` | `obj` |

**Hard rule — explicit only**: on a structured route every SVG carries the four root identity attributes; every Master/Layout atom and slot is a direct root child with a unique stable `id`; `data-pptx-layout-kind`, `distilled`, and `utility` are legacy and fail. Flat pages omit the structural markers and visibility attributes; ordinary groups still use the shared `data-pptx-bounds` contract. The `id` identifies an element; `data-pptx-layer`, never the `id`, decides ownership, and separate pages may repeat the same fixed-atom `id` under the same Master/Layout contract. Unmarked content is Slide-local.

**Layer order**: author in PowerPoint paint order — Master background, Layout background, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local content. Backgrounds are the inheritance plane beneath every shape; keeping this order aligns SVG preview with PowerPoint rendering.

**Solid background ownership**: only a direct full-canvas solid `<rect>` can own a scoped background. Mark it `layer="master"` for the deck-wide default, `layer="layout"` for a page-type variant under the same design language, `layer="slide"` for a one-slide override; Layout overrides Master, Slide overrides both. Gradient/pattern rects, textures, transformed rects, and visible-stroke rects remain ordinary shapes on declared layers or Slide-local; images remain pictures.

**Slot bounds**: derive `data-pptx-bounds` from the intended design zone, column, panel inset, safe area, or picture frame — never from text length, glyph width, line count, or a tight content box. Repeat the same slot ids/types/effective indices/default bounds/binding modes on every slide using that Layout; Slide content and local carrier geometry may differ from the default frame. A template-owned chart/table carrier may declare `data-pptx-native-authority="json"`; its metadata, marker identity, bounds, and slot binding are structural facts while its preview children are derived.

**Text carriers**: a multiline placeholder stays one native text frame, so leave strict-line text Slide-local when separate frames are required. Leave a carrier empty or whitespace-only when the placeholder must be visually blank — export materializes an invisible run; never insert a dummy dash, sub-1pt text, or an opacity-hidden glyph. A materialized mirror carrier may keep the source `data-pptx-frame`; do not add it to an authored `standard` / `fidelity` carrier merely to duplicate its bounds. `object` is the generic content slot; `media` binds an authored image/crop and does not synthesize video or audio from a decorative group.

## 3. Legacy Template Input Boundary

Projects or analysis packages carrying `analysis/native_structure.json` / `sources/source.pptx`, `pptx_structure.mode: baseline|template|preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled` / `utility`, direct atomic placeholders, or an incomplete root Master identity are not generation/export inputs and are never upgraded in place; create a separate current workspace through [`create-template`](../workflows/create-template.md). A project explicitly declaring `mode: flat` is the current free-design/brand-only route and needs no conversion.

| Available source | Allowed create-template behavior |
|---|---|
| Original PPTX Type A | `standard` / `fidelity` author new topology; `mirror` authors compact SVG from parsed evidence while preserving supported Master/Layout/placeholder facts that still exist in the package |
| Legacy or unstructured SVG Type B | `standard` / `fidelity` use pages as visual/contextual reference and author a complete new contract; old metadata is not output topology |
| Complete current SVG Type B | `mirror` may author a compact equivalent preserving the explicit current contract in a new workspace; authored modes may replace it |

Without an original PPTX or complete current Type B contract, do not claim mirror or source-topology recovery. After template creation, Generate Step 6 (or Quick §3) authors new structured `svg_output/` pages; the exporter only compiles those declarations.

---
