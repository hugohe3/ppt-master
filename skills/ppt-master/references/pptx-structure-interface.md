> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# PPTX Structure Interface

Conditional interface for PowerPoint Master, Layout, fixed-layer, and placeholder authoring. Load only when `spec_lock.md pptx_structure.mode` is `structured`.

**Cross-reference map**: unqualified §1.5 and §4.2 references point to [`shared-standards-core.md`](./shared-standards-core.md); this file's own sections are §1–§3.

## 1. PPTX Structure Routing

Every new SVG project declares one deterministic route. Free-design, brand-only, and `template_reuse_scope: style` projects use `pptx_structure.mode: flat`, omit `pptx_masters` / `pptx_layouts` / `page_pptx_layouts` / `page_layouts`, and author no Master/Layout/layer/placeholder metadata. Export keeps all represented content Slide-local while materializing one clean project-owned Master plus one Blank Layout from the current color/typography lock; stock content placeholders and unused built-in Layouts are removed, while the standard date/footer/slide-number capability hooks remain. Deck/layout template projects whose AI-derived lock records `template_reuse_scope: mirror|layout` use `mode: structured`; `standard` / `fidelity` templates use their authored contract, while mirror templates use the validated source identities and parentage declared by the newly materialized workspace.

**Hard rule — no structure inference**: Flat export performs no promotion or deduplication; every object stays Slide-local. Structured template export compiles only declared root identities, atomic fixed layers, and slot groups—it does not assign Layout families, cluster pages, infer placeholders, repair missing metadata, or migrate legacy contracts. Create a new current workspace through [`create-template`](../workflows/create-template.md) before generating structured pages.

**Layout reuse**: Reuse one Layout key only when its ordered fixed Layout atoms and slot ids/types/effective indices/default bounds/binding modes are identical. Different wording, data, imagery, crop, or Slide-local carrier geometry does not create a new Layout. A genuinely different reusable contract gets a new key even when both pages are semantically `content`.

**Zero-slot Layout**: A named Layout may contain no slots and no fixed Layout atoms. This is valid for a cover, poster, full-visual page, or other fixed composition. Do not manufacture an empty `utility` kind or full-page fake `object` slot.

**Adaptive change**: Template `strict` preserves the selected prototype contract. `adaptive` retains the prototype Master and may use a current or new Layout identity only when Strategist already declared it in the complete plan and lock. If construction proves that fixed Layout atoms or slot topology/bounds must change, stop and return upstream for Strategist to add or revise the definition and page mapping before authoring resumes; Executor never mutates a reused key or the lock.

## 2. Explicit PPTX Master / Layout / Placeholder Metadata

**Trigger**: This explicit metadata interface applies only to new pages generated from a current deck/layout template workspace with `template_reuse_scope: mirror|layout`. `spec_lock.md` declares `pptx_structure.mode: structured`, complete unique `pptx_masters` / `pptx_layouts` rosters, one `page_pptx_layouts` assignment per generated page, and `page_layouts` as authoring-prototype provenance. `template_reuse_scope: style`, free-design, and brand-only SVGs use `mode: flat` and none of these metadata fields.

**Project lock**: A Master row is `<master_key>: <PowerPoint picker name>`. A unique Layout row is `<layout_key>: <master_key> | <PowerPoint picker name> | <prototype source>`, where the source is a generated `P<NN>` or installed `template:<basename>`. A page assignment is `P<NN>: <layout_key>` under `page_pptx_layouts`. The SVG root values MUST match the assigned definition. A Layout key belongs to exactly one Master and must be globally unique. Reuse one key only when prototypes share identical ordered Layout atoms and slot ids/types/effective indices/default bounds/binding modes. An unused Layout uses a template SVG source and remains registered without a published carrier slide. Every structured route requires numeric `spec_lock.md` typography `title` / `body` rows.

**Template behavior**: Strict preserves the selected prototype's declared Master/Layout/slot contract. Adaptive retains its Master and realizes the current or new Layout key/name declared by Strategist. A construction-discovered change to fixed Layout atoms or slot topology/bounds returns upstream for plan/lock repair, readback, and validation before authoring resumes. Mirror-created prototypes preserve validated source identity, literal paint, typography, effects, atomic geometry, and referenced assets in a new workspace. `standard` / `fidelity` never make source topology authoritative; mirror does not synthesize a replacement topology or fill missing facts.

Imported inherited-shape visibility remains an immutable analysis fact until a
structured mirror is materialized. The final mirror root carries that fact with
the two optional canonical booleans below so export can write the preserved source
package fields without inferring visibility from which shapes happen to be
present. Authored `standard` / `fidelity` templates normally omit both and use
the default `true`. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).

**Master text-style contract**: Flat and structured export map the declared
`title` anchor to every `a:defRPr` in Master `p:titleStyle`. Level 1 in both
`p:bodyStyle` and `p:otherStyle` uses the declared `body` anchor; levels 2–9
use a deterministic descending hierarchy from `15/16` through `8/16` of that
size, rounded to 0.5 pt and floored at the smaller of 8 pt or the body size.
Existing per-level indentation and bullet properties remain unchanged.

| Master style | Locked source | XML field changed |
|---|---|---|
| `p:titleStyle` | `typography.title` | Every `a:defRPr@sz` |
| `p:bodyStyle` | `typography.body` | Level 1 plus derived level 2–9 `a:defRPr@sz` |
| `p:otherStyle` | `typography.body` | Level 1 plus derived level 2–9 `a:defRPr@sz` |

**Hard rule — narrow scope**: This Master update changes only Master
`p:txStyles//a:defRPr@sz`; it preserves level indentation, bullet, margin, and
paragraph settings. It does not rewrite direct run sizes on generated slides,
so the initial slide rendering remains controlled by the authored SVG. Missing
`title` or `body` rows fail flat or structured export.

**Layout level-one text-default contract**: For every text-bearing placeholder
whose first prototype run has a direct `a:rPr@sz`, explicit Layout export copies that
size to the generated Layout prompt run and
`p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr@sz`. It does not rewrite Slide direct
runs or Layout levels 2–9. This preserves the layout-specific size when
level-one placeholder text is inserted or reset; placeholders without a direct
prototype size remain unchanged.

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-master="master-default"` | root `<svg>` | Binds the slide to one generated Slide Master key |
| `data-pptx-master-name="Default Master"` | root `<svg>` | Sets the Master picker/display name |
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Sets the PowerPoint layout-picker name; defaults from the layout key |
| `data-pptx-show-master-shapes="false"` | root `<svg>` | Accepts exact lowercase `true` or `false` and writes the assigned Layout's `p:sldLayout@showMasterSp`; every SVG using the same Layout key must repeat the same value; omission means `true` |
| `data-pptx-show-inherited-shapes="false"` | root `<svg>` | Accepts exact lowercase `true` or `false` and writes this Slide's `p:sld@showMasterSp`; `false` hides inherited Layout and Master shapes without removing backgrounds, placeholders, parts, or parent relationships; omission means `true` |
| `data-pptx-layer="master"` | direct semantic atom | Moves one repeated static object/background into the named Slide Master; ordinary `<g>` is forbidden, while one validated compact authored-preset `<g>` (§1.5) is an atomic exception |
| `data-pptx-layer="layout"` | direct semantic atom | Moves one repeated static object/background into the selected Layout; ordinary `<g>` is forbidden, while one validated compact authored-preset `<g>` (§1.5) is an atomic exception |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | Writes a one-page override as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct slot `<g id>` | Declares a reusable Layout slot whose visible content remains Slide-local |
| `data-pptx-bounds="x y width height"` | slot `<g>` | Supplies the positive reusable design-zone frame in SVG user units with at most two decimals per value |
| `data-pptx-idx="1"` | slot `<g>` | Retains an imported source Layout placeholder index; optional for reconstructed layouts |
| `data-pptx-carrier="true"` | one compatible direct child of a normal slot | Binds that visible child as the real Slide placeholder carrier |
| `data-pptx-binding="proxy"` | composite `object` slot `<g>` only | Keeps the visible group ordinary and creates one hidden transparent binding proxy |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

**Hard rule — explicit only**: On a structured `template_reuse_scope: mirror|layout` route, every SVG requires the four root Master/Layout identity attributes. Optional inherited-shape visibility uses only exact lowercase `true` / `false`; other spellings fail, and omission means `true`. Every Master/Layout atom and slot requires a unique stable `id` and is a direct root child. Layouts with zero slots are valid. `data-pptx-layout-kind`, `distilled`, and `utility` are legacy metadata and fail the structured contract. Flat `template_reuse_scope: style`, free-design, and brand-only pages omit the structural markers and visibility attributes; ordinary groups still use the shared `data-pptx-bounds` module contract.

**Layer order**: Author the SVG in PowerPoint paint order: Master background,
Layout background, optional Slide background, remaining Master atoms, remaining Layout atoms,
then slot groups and Slide-local content groups. Backgrounds are a special inheritance
plane beneath every shape; this order keeps standalone SVG preview and
PowerPoint rendering aligned. The exporter rejects interleaved layers.

**Solid background ownership**: Structured export deliberately narrows scoped
background ownership to a direct full-canvas solid `<rect>` and disables the
generic conversion-level promotion described in §4.2. Mark the solid rect
`data-pptx-layer="master"` for the deck-wide default,
`data-pptx-layer="layout"` for a page-type override, or
`data-pptx-layer="slide"` for a one-slide override. An unmarked direct
full-canvas solid rect in the background plane is also treated as Slide scope.
A Layout background overrides the Master background; a Slide background
overrides both. Use the Master for a globally stable color and the Layout for
cover/section/content variants under the same design language. Gradient and
preset-pattern rects remain ordinary shapes on declared Master/Layout layers
or as Slide-local content; images remain pictures. Textures, transformed rects,
and visible-stroke rects also remain ordinary objects.

| Placeholder value | Direct carrier inside slot `<g>` | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | one `<text data-pptx-carrier="true">` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | one `<text data-pptx-carrier="true">` | `dt`, `ftr`, `sldNum` |
| `picture` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `pic` |
| `chart`, `table` | one matching `data-pptx-replace-with` marker group, marked as carrier | `chart`, `tbl` |
| `object` | one text, image, basic SVG shape, or validated compact authored-preset `<g>` marked as carrier; alternatively the slot group declares `binding="proxy"` | `obj` |
| `media` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `media` |

**Text slot carrier**: A multiline text placeholder must remain one
native text frame. Use the default paragraph merge; `--no-merge` cannot supply
several line shapes as one
PowerPoint placeholder prototype/binding. Leave strict-line text Slide-local
when separate frames are the required result.

For a materialized mirror, an imported text carrier may additionally keep the
source shape's positive `data-pptx-frame="x y width height"`. That frame owns
the Slide carrier `a:xfrm`; the converter reconstructs text-body insets from the
visible SVG anchor/baseline instead of shrinking the shape to glyph bounds.
`data-pptx-bounds` remains the reusable Layout default and may
legitimately differ. Do not add `data-pptx-frame` to an authored
`standard` / `fidelity` carrier merely to duplicate its Layout bounds.

**Blank text carrier**: Leave a marked text carrier empty or whitespace-only
when the placeholder must remain visually blank. Export materializes one
invisible U+200B run so the carrier still becomes a native PowerPoint text
shape. Do not insert a dummy dash, shrink text below the DrawingML 1pt minimum,
or hide a visible glyph with opacity/background paint; those workarounds either
leak content or produce a PPTX that PowerPoint repairs.

`title` is normally type-matched without an index in reconstructed layouts; if
an imported source title explicitly has one, preserve that exact index. Every
indexed placeholder on one layout uses a unique OOXML UInt32 index. Structured export writes the semantic type on both the Layout and Slide carrier (except `obj`, whose OOXML default is already `obj`) so PowerPoint and `python-pptx` retain the same identity. A composite object slot instead keeps its visible group ordinary and uses a hidden transparent proxy.
Date, footer, and slide-number placeholders enable their matching Layout `p:hf`
flags; a date placeholder also gets a `datetimeFigureOut` field in the reusable
Layout definition. The current Slide keeps its authored date content.

Because an omitted `p:ph@idx` has the effective value `0`, an omitted-index
title reserves `0`; no other placeholder on that Layout may use the same
effective index.

**Slot prototype**: The prototype source declared by the unique Layout definition supplies that Layout's placeholder formatting. `data-pptx-bounds` supplies the reusable default frame and is mandatory on every slot. Derive it from
the intended design zone, column, panel inset, safe area, or picture frame —
never from text length, glyph width, line count, or a tight content bounding
box. Repeat the same slot ids/types/effective indices/default bounds/binding modes on every slide using that Layout. The Layout owns the reusable `p:ph`; normal visible carriers keep a matching Slide binding so approved rendering stays identical. A composite `object` proxy adds one hidden transparent binding shape to suppress empty inherited placeholder paint. Bounds define the Layout default only; actual Slide content and local carrier geometry may differ.

**Final-package read-back gate**: After writing a temporary structured PPTX and before publishing it, export reopens the package and
verifies that each published Slide targets exactly one Layout, one Layout key always resolves to the
same part, different keys do not collapse onto one part, and every declared Layout—including one unused by all published Slides—is
registered through its Master and the Presentation. Physical Slide/Layout/
Master part rosters, their content-type overrides, and their Presentation/
Master registrations must be exact. It also verifies the Layout picker name,
Master picker identity, placeholder type and effective index, matching `p:hf` flags, explicit design-zone frame, direct prompt size, and level-one default size.
Every owned `p:bg` is checked as an exact zero-or-one payload against the pre-
promotion result; this includes preserving the base Master background when no
authored Master background replaces it. During the same export, every finished
Slide, Layout, and Master must reproduce its exact top-level shape-name roster
and order after packaging. The gate verifies that each carrier-bound slot owns the expected Slide binding, each composite visible carrier remains ordinary, and every composite binding proxy is hidden. A zero-slot Layout must read back with no placeholder. Later slides may keep different Slide-local geometry; only the reusable
Layout frame is checked against the explicit/prototype contract. Any mismatch
fails export without replacing the requested output.

**Static structure consistency**: Repeat the same master element ids on every
slide and the same layout element ids on every slide sharing a layout. Their
generated OOXML must be identical within the affected master/layout group.
Static structure may carry shapes, text, or images; non-image/external
relationships are rejected. Every static object is atomic. An ordinary
`<g data-pptx-layer="master|layout">` is forbidden; the validated compact
authored-preset group from §1.5 is the sole group exception because it compiles
to one native object. A full-canvas first rect may be marked as a Master or
Layout background.

**Native object slot carriers**: `chart` / `table` slots require
`--native-charts-and-tables`; fallback groups contain several shapes and cannot map to one
PowerPoint placeholder. `object` is the generic PowerPoint content slot and
uses either one carrier object—including one validated compact authored-preset
group—or the explicit composite proxy downgrade. `media` currently binds
an authored image/crop to a native `media` placeholder; it does not synthesize
video or audio media from a decorative SVG group.

## 3. Legacy Template Input Boundary

Existing structured/template projects or packages that carry `native_structure.json` / `source_template.pptx`, `pptx_structure.mode: baseline|template|preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled` / `utility`, direct atomic placeholders, or an incomplete root Master identity are not generation/export inputs and are never upgraded in place. Create a separate current workspace through [`create-template`](../workflows/create-template.md). A project explicitly declaring `pptx_structure.mode: flat` is the current free-design/brand-only route and needs no conversion merely because it has no Master/Layout metadata.

| Available source | Allowed create-template behavior |
|---|---|
| Original PPTX Type A | `standard` / `fidelity` author new topology; `mirror` preserves supported Master/Layout/placeholder facts that still exist in the package |
| Legacy or unstructured SVG Type B | `standard` / `fidelity` use pages as visual/contextual reference and author a complete new contract; old metadata is not output topology |
| Complete current SVG Type B | `mirror` may preserve the explicit current contract in a new workspace; authored modes may replace it |

Without an original PPTX or complete current Type B contract, do not claim mirror or source-topology recovery. After template creation, Generate PPTX Step 3 authors new structured `svg_output/` pages; the exporter only compiles those declarations and never derives, repairs, or migrates structure.

---
