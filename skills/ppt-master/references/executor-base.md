# Executor Common Guidelines

> Narrative skeleton and visual aesthetic come from this deck's locked files under [`modes/`](./modes/_index.md) and [`visual-styles/`](./visual-styles/_index.md). Technical constraints are in shared-standards.md.

**Hard rule — complete page SVG**: Every visible object intended for the exported slide MUST exist in the final page SVG or be explicitly referenced by it. Templates and `spec_lock.md` guide construction; they are not export-time overlays for missing visible content.

**Hard rule — route-specific PowerPoint structure**: Free-design, brand-only, and `template_reuse_scope: style` projects use `pptx_structure.mode: flat`: write no root Master/Layout identity, `data-pptx-layer`, or `data-pptx-placeholder`; every visible object remains Slide-local, and the root declares exactly one canonical `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`). Export materializes one clean project-owned Master plus one Blank Layout from the current lock. `template_reuse_scope: mirror|layout` projects use `mode: structured`: every page reads its locked Master/Layout row and declares the four root identity attributes from the first draft. Do not add `data-pptx-layout-kind` or duplicate identity with `data-pptx-page-role`. Add `data-pptx-role` only to structural page-frame objects whose package, page-number, or animation behavior is not already expressed by specialized metadata; the marked element uses a stable unique `id`. See [`semantic-svg.md`](./semantic-svg.md).

**Hard rule — supported PPTX route**: The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter. Step 7.2 still generates `svg_final/` as a mandatory self-contained visual preview that may be inserted as an SVG picture. Do not treat PowerPoint's manual Convert-to-Shape operation as an authoring target or compatibility requirement.

> Note: this rule covers page design only. Speaker notes, animations, transitions, narration, and direct native-PPTX workflows retain their separate artifacts and package-level processing.

---

## 1. Template Reuse Rules

### 1.0 Pre-generation Template Read

**Hard rule**: Read the compact template roster once, but never treat a summary as the full page prototype.

| Source list | Read path |
|---|---|
| Chosen template's `design_spec.md` (template capabilities) | `templates/design_spec.md` |
| Model-readable execution roster, when present | `templates/template_execution_manifest.json` |
| Selected mirror prototype's text-slot sidecar | The roster entry's `text_slots_path` under `templates/` |
| Every distinct chart name in `spec_lock.md page_charts` | `templates/charts/<chart_name>.svg` |
| Chart types in `design_spec.md §VII` not covered above | `templates/charts/<chart_name>.svg` |

When `template_execution_manifest.json` and the selected entry's `text_slots_path` exist, read the compact roster once for selection/orientation and the sidecar before authoring each mirror page; then read the selected complete `templates/<basename>.svg`, which remains the visual/structural authority. Layout reuse reads the selected complete SVG but does not need the mirror-only sidecar. When the manifest, selected entry, or sidecar is unavailable, batch-read every distinct `<basename>` in `spec_lock.md page_layouts` before page 1. On mirror, preserve text topology directly from the complete SVG under §1.1; missing derived metadata alone does not invalidate the workspace. Chart SVGs remain one-time batch reads.

`spec_lock.md` is the only file re-read per page (§2.1).

**Exception**: user mid-deck adds pages or swaps templates introducing a basename/chart absent from the original roster/batch → read the new file once, continue.

> The execution manifest reduces roster/context load; it never authorizes writing from selectors alone. The selected full SVG must be open before editing that page.

Resolve the per-page template SVG via `spec_lock.md page_layouts` (authoritative). There is no filename/page-type fallback.

**Resolution order (per page):**

1. `template_reuse_scope: mirror` → see §1.1. The installed workspace must support `replication_mode: mirror`.
2. `template_reuse_scope: layout` → resolve `P<NN>: <basename>` from `page_layouts`, retain the structure system, and apply the non-mirror skin/reflow rules below.
3. `template_reuse_scope: style` or no deck/layout template → flat free design: use template colors/typography/decoration/rhythm as style input, but write no native Master/Layout mapping or SVG structure metadata.
4. `mirror` / `layout` with no current-page `page_layouts` row → stop; adaptive mode still requires one selected input prototype.

> Note: `page_layouts` disambiguates the multiple content variants a template may ship; missing mappings are contract errors.

**Templates supply structure, not skin (`layout` scope)**: a chart or layout template's gradients, drop-shadows, palette, **and font sizes** are placeholder. Inherit its geometry, label / legend placement, and series-encoding logic; re-skin every fill / stroke to the deck's `visual_style` + `spec_lock.colors` — flat styles strip the gradients and shadows, gradient / glass styles repaint their own. Forbidden — shipping a template's default `<linearGradient>` / `cardShadow` / Tailwind fills unchanged. `mirror` scope is the exception: §1.1 preserves visuals verbatim.

**Font size is skin, not geometry (non-mirror).** A chart / layout template's hardcoded `font-size` values (often 11–16px, sized for the template's own dense placeholder text) are NOT inherited — classify each text into its `spec_lock.md` role and use that role's locked size, exactly as you re-skin color. **Structural roles (page title / body / subtitle / annotation / footnote) hold their one deck-wide size on every page** — the template's placeholder px never overrides it; same-role text drifting page to page is what makes a deck look unprofessional.

**Typography execution order (mandatory):**

1. Build a per-page text inventory from `design_spec.md §IX` + the current `notes/<NN>_*.md`.
2. Classify each text item before drawing. **Structural roles** (`title`, `subtitle` / `lead`, `body`, `annotation`, `footnote` / `page_number`) must map to their declared `spec_lock.typography` slot. A **one-off feature element** (a single hero number, an isolated emphasis label) may take an in-ramp intermediate value — the ramp is anchored on `body`, not a closed menu — but a feature size that **recurs** must be promoted to a declared slot. The failure mode this guards against is structural text silently inheriting the template's compact px, not legitimate feature sizing.
3. Copy the role's locked px value into `font-size` verbatim. Do this before placing the text; never start from a template `font-size` and then "adjust".
4. Layout from those locked sizes: compute line-height, wrapped line count, child `y` / `dy`, card padding, card height, column gaps, and available image/chart area from the chosen px values.
5. Only after this reflow may you inspect fit. If fit fails, move / resize containers or simplify local geometry first; do not reduce the role size merely because the inherited template slot was smaller.

**Geometry adapts to the type, never the reverse**: when the locked size is larger than the template's placeholder text, widen / heighten the card, open spacing, and recompute child `y` / `dy` to make room — do not shrink the font to fit the inherited container. A `font-size` change is a layout change: revise line-height and every downstream vertical coordinate that depends on it. For wrapped text, allocate at least the wrapped line count × line-height plus top / bottom padding; fixed `y` stacks copied from a smaller template are invalid once the locked role size is applied. The Executor renders the page it was given; page count and per-page density are the Strategist's call, fixed at confirmation — do **not** re-paginate, split the page, or drop authored content to cope with size here. Only when a single block still cannot fit after the geometry is fully reflowed may you shrink **that block** as a bounded last resort — and **only body text** is ever shrunk this way. Title, subtitle, annotation / caption, footnote and page number are **locked once set and never adjusted to fit** — their values hold across the whole deck. Step the overflowing body block's `font-size` down by `2`px at a time, and only if it still overflows step it down again, up to a cumulative floor of **`4`px below the locked body size** (e.g. `24` → no smaller than `20`). This is a **local, single-block** reduction — the deck-wide locked body size is unchanged on every other block and page. (The Executor works in **unitless px** throughout — spec_lock and SVG carry no `pt`.) If the block still overflows at the floor, surface a `warning:` rather than silently restructure the page. (Mirror templates are the exception: §1.1 preserves their sizes verbatim — there the source deck's typography *is* the spec.)

### 1.1 Mirror reuse — literal page replacement

When `spec_lock.md` confirms `template_reuse_scope: mirror`, Executor switches to a literal replacement path. The workspace capability `replication_mode: mirror` is a prerequisite, not the trigger by itself:

1. **Per-page reference selection** — Strategist selects one mirror page per project page via `spec_lock.md page_layouts` (e.g., `P04: 015_content`). The basename is the mirror filename without extension; Strategist made this choice by reading `design_spec.md §V Page Roster` descriptions, not by guessing.
2. **Copy, don't fill** — open the referenced full mirror SVG immediately before authoring the page. Copy it as the starting point, then edit slide-specific text in place. Preserve every non-text element and every `data-pptx-*` structure attribute verbatim.
3. **What you may edit** — only the visible string values already carried by `<text>` and `<tspan>` nodes that express slide-specific content (title, body, captions, KPI labels, dates, page numbers). Keep the number, order, nesting relationship, and **all attributes** of every `<text>` / `<tspan>` node unchanged. Never merge or split nodes, move a string between nodes, add a new tspan, or delete an empty carrier. The selected `text_slots_path` sidecar exposes the expected selectors/counts/hashes, but the complete SVG remains authoritative.
4. **What you must not touch** — element positions, sizes, fonts, colors, fills, strokes, gradients, **which image each `<image>` points at**, `<g>` grouping, sprite-sheet `<svg viewBox>` wrappers, decorative `<rect>` / `<path>` / `<circle>` / `<polygon>` shapes, `<use data-icon="...">` markers, embedded chart data structures. Mirror's value is preserving the source deck's visual identity — any geometric / decorative drift defeats the purpose. **The `href` path is not the image**: normalizing a bare `href="cover_bg.png"` to `href="../images/<name>"` (when Step 3 relocated the asset to `images/`) points at the *same* image and changes nothing visual — that is an allowed path fix, not a fidelity edit. Leaving the bare href as-is is also fine; the exporter and live preview resolve bare hrefs against `images/` either way.
5. **Content fit** — if the replacement needs a different number of text segments/items, do not merge/split nodes, drop sourced content, or restructure the grid. Select a better mirror prototype and update the planning mappings, or report `warning: P<NN> content does not fit mirror reference <basename>; choose another prototype or change template_reuse_scope to layout/style`.
6. **Visible text editing** — mirror SVGs may keep literal source text rather than `{{...}}` authoring markers. Edit values in place while retaining imported semantic `data-pptx-placeholder` identity and exact text topology.
7. **Output filename** — follow the standard project SVG naming convention (`<NN>_<page_name>.svg` where `<NN>` matches the project page index, not the mirror source index). The mirror filename is the *reference*, not the *output*.

**Detecting mirror mode**: read `template_reuse_scope` from `spec_lock.md` before every page. `replication_mode: mirror` in the installed template only determines whether that confirmed scope is legal; it must never force mirror behavior when the confirmed scope is `layout` or `style`.

**Mirror + chart pages**: chart structures inside a mirror SVG are already drawn (axis, series, labels). Treat them as visual references — replace the data labels and series text content to match the project's chart spec, but do not redraw the chart from a `templates/charts/<name>.svg` baseline. A mirror template's `page_charts` entries are normally absent for this reason.

**Legacy template boundary**: A template with missing root Master identity, direct atomic placeholders, `data-pptx-layout-kind`, unmapped `baseline`, `preserve`, or `layout_strategy: distill` is not a fallback input. Stop and create a new current workspace through [`create-template`](../workflows/create-template.md) before generation.

### Page-Template Mapping Declaration (Required Output)

Before generating each page, output which template is used:

```
📝 **Template mapping**: `templates/03a_content_image_text.svg` (free-design routes may use "None")
🎯 **Adherence rules / layout strategy**: [specific description]
```

- **Content pages**: template defines only header/footer; content area is free
- **No template**: allowed only on free-design or brand-only routes

### 1.2 PowerPoint Master / Layout Mapping

This section applies only when a deck/layout template is confirmed with `template_reuse_scope: mirror|layout`. `page_layouts` selects the input SVG prototype, `pptx_masters` / `pptx_layouts` declare unique reusable output definitions, and `page_pptx_layouts` assigns every generated page before the first page is drawn. `template_reuse_scope: style`, free-design, and brand-only routes use `pptx_structure.mode: flat`, omit all four sections, skip the rest of §1.2, and keep every SVG object Slide-local.

**Hard rule — reuse-scope route**: `template_reuse_scope: mirror|layout` requires `pptx_structure.mode: structured`. `template_reuse_scope: style` requires `mode: flat` even though a template supplied its visual vocabulary. Missing mode or legacy values (`baseline`, `template`, `preserve`), `layout_strategy`, Layout-kind fields, partial mappings, and old direct placeholders stop generation. Create a new template workspace through [`create-template`](../workflows/create-template.md); do not upgrade the active SVG project in place.

**Hard rule — root identity**: A `page_pptx_layouts` row binds the page to one key in `pptx_layouts`; that unique definition supplies its Master key, Layout picker name, and prototype source. Put the declared Master key/name and Layout key/name on the root SVG. A Layout key belongs to exactly one Master and remains globally unique.

**Hard rule — atomic fixed layers**: Every `data-pptx-layer="master|layout"` visual is one direct root semantic atom that compiles to one DrawingML object. An ordinary marked `<g>` is forbidden; one validated compact authored-preset `<g>` emitted by `preset_shape_svg.py` is the sole group exception because it compiles to one native shape. When reconstructing source PPTX groups, recursively push supported transforms, paint, opacity, and z-order into atomic children. Repeat the identical ordered Master atom contract on every page using that Master and the identical ordered Layout atom contract on every page sharing that `(master, layout)` pair.

**Hard rule — PowerPoint paint order**: Direct children appear in this order: Master background atoms, Layout background atoms, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local content groups. Backgrounds are the inheritance plane beneath all shapes.

**Mandatory — slot authoring**: A reusable content slot is one direct root `<g id>` carrying `data-pptx-placeholder` and positive `data-pptx-placeholder-bounds`. A normal slot contains exactly one compatible direct drawable child marked `data-pptx-placeholder-carrier="true"`. Export unwraps that child into the real Slide placeholder binding. Decorations do not belong in the slot; move reusable decoration to a root Layout atom and keep page-specific labels/captions in another slot or Slide-local group.

**Mandatory — slot identity**: Preserve imported `data-pptx-placeholder-idx` values where available; otherwise omit the title index and assign unique indices only where repeated roles need disambiguation. Pages sharing one Layout key repeat the same slot ids/types/effective indices/default bounds/binding modes. Current text, crop, and Slide-local carrier geometry may differ.

**Composite proxy fallback**: A genuinely composite region may use a direct `<g data-pptx-placeholder="object" data-pptx-placeholder-binding="proxy">` with positive bounds. Its visible group remains Slide-local and export creates one hidden transparent matching placeholder proxy. This downgrade is valid only for `object`; do not use it for an ordinary title, body, picture, chart, table, or media slot.

**Forbidden — dummy carriers**: Never satisfy a carrier slot with tiny text, near-transparent glyphs, background-colored punctuation, or other fake content. Leave an intentionally blank text carrier empty/whitespace-only—the exporter emits a legal invisible U+200B run—or use the composite `object` proxy contract. If `strict` prototype binding cannot represent the completed composition, surface the mismatch; select a compatible prototype or create an explicit adaptive Layout instead of hiding the conflict.

**Zero-slot Layout**: A Layout may have no slot groups. Covers, posters, and fixed visual pages still declare their named Master/Layout and fixed atoms. Do not manufacture a full-page `object` slot or empty `utility` identity.

**Mandatory — per-page slot coverage**: On every mapped page, declare a slot for each standard role the page actually has: the page heading as `title`, a cover tagline as `subtitle`, the page number as `slide-number`, running footer text as `footer`, a hero / content image as `picture`, and a body block already authored as one merged text frame as `body`. A page shipping zero slots exports a Layout with no insertable placeholders — valid only for a genuinely fixed composition (see Zero-slot Layout above), never as the deck-wide default. Pages sharing one layout key ship the same slot set.

**Hard rule — variable slot content**: “Per-page headings never stay Slide-local by default” means authoring them as `title` / `subtitle` slots; it never permits page-varying text or images to become fixed Layout atoms. Any such value that varies across pages sharing one Layout key MUST be carried by a slot or remain Slide-local.

**Mandatory — master/layout layer coverage**: On every mapped page, mark the deck-wide background and every-page chrome (footer bar, running logo) `data-pptx-layer="master"`, and mark the static framing that defines this layout key's composition (header rule, divider band, zone panels — including chrome repeated on every content page but absent from the cover) `data-pptx-layer="layout"`. A mapped page with zero `data-pptx-layer` marks exports a bare Master and an empty Layout — the layer marks, not the slide content, give each Layout its visible design.

**Layout identity**: Different keys differ in fixed Layout atoms or slot topology/default bounds/binding modes. Identical contracts should share one key. Current wording, imagery, crop, and Slide-local geometry never define identity.

**Template adherence**: Strict copies the prototype Master/Layout/slot contract exactly. Adaptive keeps the prototype Master and may change reusable Layout atoms or slots only under a new explicit Layout key/name. When the completed composition genuinely needs that change, update `spec_lock.md pptx_layouts` immediately while authoring the first affected page; later pages may reuse the new key only by repeating its exact contract. Changing only a label is not a new Layout.

**Layout-content boundary**: Mark only genuinely reusable fixed framing as a Master/Layout atom. Concrete titles, body copy, metrics, chart marks, images, and page-specific groups remain inside slot groups or ordinary Slide-local content groups. The exporter never infers or clusters structure.

**Background ownership**:

| Scope | SVG authoring |
|---|---|
| Deck-wide default | Direct full-canvas solid `<rect data-pptx-layer="master">` repeated identically on every page |
| Page-type default | Direct full-canvas solid `<rect data-pptx-layer="layout">` repeated on every page sharing that layout key |
| One-page exception | Direct full-canvas solid `<rect data-pptx-layer="slide">` |

The exporter writes these solid fills as real Master/Layout/Slide `p:bg`, not selectable full-canvas shapes. In structured mode, gradients, preset patterns, images, textures, and overlay panels remain explicit shapes or pictures; the generic background-promotion rule outside structured mode does not expand this ownership contract.

---

## 2. Design Parameter Confirmation (Mandatory Step)

Before the first SVG page, output a confirmation listing: the compact communication intent + desired audience outcome, canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan, and the live-preview URL reported by the launcher. If the preview launch failed, state that failure before generating SVGs instead of silently proceeding. Prevents purpose/spec/execution drift.

### 2.1 Per-page spec_lock re-read (Mandatory)

> Long decks drift off the declared palette/icons mid-deck due to context compression. `spec_lock.md` is the canonical execution reference — re-read it per page to bypass model memory.

**Hard rule**: Before generating **each** SVG page, `read_file <project_path>/spec_lock.md`. Use only values from this file, not from memory. Re-read the global `communication` section along with the technical locks. The current page's `design_spec.md §IX` brief must be in immediate context; if context was auto-compacted or the brief is not immediately available, re-read `design_spec.md` for that page before drawing.

**Per-page communication trace**: Read the current §IX `Core message` and `Audience move` before choosing composition. The page must advance at least one purpose named in `communication.communication_intent` and move the audience toward `communication.audience_outcome`; `communication.core_message` remains the deck-wide north star. A page that cannot state this movement is an upstream outline defect — surface `warning: P<NN> has no communication move` instead of compensating with decorative layout. Do not invent a new purpose, ask, or outcome at execution time. Structural pages may advance the contract by establishing relevance / tension / decision frame or by completing the final commitment; they are not exempt from having a reason to exist.

**Per-page reading-mode check**: Read `communication.consumption_mode` before choosing the page's composition. Apply it together with the authored §IX block texture and `page_rhythm`:

| `consumption_mode` | Page execution |
|---|---|
| `text` | Make the visible page independently understandable. Preserve complete prose, explicit labels / captions / sources, tables, and necessary detail; use bullets only for genuinely parallel or ordered items. |
| `balanced` | Keep the primary claim and its evidence on the page; let notes add interpretation and transitions. Mix prose, structured evidence, and necessary lists according to their semantic relationship. |
| `presentation` | Make one claim and one dominant visual expression legible at projection distance. Keep visible copy concise; put explanation and transitions in notes instead of creating paragraph dumps or compressed bullet prose. |

The §IX wording and sourced facts remain authoritative. Do not rewrite, drop, or invent content to force a mode at execution time. When the authored texture materially conflicts with the lock, render the least-destructive faithful composition and surface `warning: P<NN> content texture conflicts with consumption_mode <value>` as an upstream outline issue; do not encode this subjective judgment in the checker.

**Per-block expression**: render each `design_spec.md §IX Content` block in its written texture — a full-sentence block as wrapped prose, a fragment/label block as bullets/keywords. **Never split a full-sentence block into a bullet list** — splitting loses the information that the block was continuous reasoning, not a set of parallel points; not because a bullet lays out easier, and not because an inherited template slot is shaped as a list. If a block carries no clear texture, infer the mode from its wording and the page layout.

- **Prose render recipe**: one `<text>` per paragraph; wrap lines with sibling `<tspan>` where the first line uses `dy="0"` and every subsequent line repeats the parent `<text>`'s **exact `x`** and the **same positive relative `dy`** (the line-height). Equal relative `dy` + matching `x` + the same effective `font-size` lets lines flow inside one PowerPoint paragraph; a font-size change preserves a new paragraph inside the same text frame, while a growing/cumulative `dy`, an irregular gap, or a mismatched `x` (e.g. `x="0"` under `<text x="60">`) may split them into separate single-line boxes. Set the line-height `dy` from the font size × a line-height factor. **Default — line-height by density (may override per content fit)**: ~1.4–1.5× for dense / small-body blocks (CLReq comfortable minimum), 1.6–2.0× for large-type, sparse, or `breathing` blocks. Fit about width ÷ font-size CJK glyphs per line (Latin fits roughly twice that); the last line runs short. Use the body ramp size, not a new one.
- **Template precedence**: when an inherited template slot is a bullet list but the §IX block is prose, the prose wins — widen or reflow the container to hold the paragraph, or drop that card; do not pour the sentence back into the list slot.
- **Mode precedence**: the locked mode shapes voice / register, not §IX's authored titles or page order. When a `§IX` title is a user-authored topic label, keep it — do not upgrade it to an assertion just because the mode (e.g. `pyramid`) favors them; mode title-tendencies apply only to AI-drafted titles.

> Note: block-level phrasing, applied *within* the page's `page_rhythm` density (below), not against it.

**Missing `spec_lock.md`** → stop before drawing and report the missing gate artifact. Recover through [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §3; do not generate from `design_spec.md` alone or silently downgrade.

**Missing field in an existing lock**: follow [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2.

**Forbidden — values outside the lock**:

- Colors (fill / stroke / stop-color) MUST come from `colors`
- Icons MUST come from `icons.inventory`; library MUST equal `icons.library`
- Font family from `typography`: use role override (`title_family` / `body_family` / `emphasis_family` / `code_family`) if declared, else fall back to `font_family`
- Font sizes follow a **ramp anchored on `typography.body`**, not a closed menu. **Structural roles — page title, body, subtitle, annotation / caption, footnote / page number — render at one consistent size deck-wide, taken from their `spec_lock` slot; never re-pick a structural role's size page by page or carry a template's placeholder px.** This locks the **role**, not every glyph: a page may still carry deliberate typographic hierarchy — a lead-in sentence, an inline emphasis figure, a pull-quote, a kicker, a hero number — but each of those is its **own role / feature element** with its own size, **applied consistently deck-wide** (declare a recurring one as its own `spec_lock` slot). In-band intermediate sizes are for exactly these feature elements. What is banned is the *same* role drifting size to fit a container or by page whim — that scatter is what reads as unprofessional. Sizes outside every band require extending the lock first.
- **The page's core message is primary — render it ≥ `body`.** The one-idea / key-claim / key-takeaway line a page is built around is its most important text; map it to the locked `lead` or `subtitle` slot (≥ `body`), never to a sub-`body` size. Demoting it below body while data callouts or labels sit larger inverts the hierarchy — the failure this prevents. If no `lead` / `subtitle` slot is locked for a recurring core-message line, surface it (per below) instead of improvising a smaller one. A footnote / page number / source credit uses the locked `footnote` (or `annotation`) slot — never an invented sub-`annotation` size; and the body-shrink last resort (§1.0) bottoms out at `body − 4`px, a hard floor never crossed.
- **Write the locked px verbatim; at most 2 decimals.** `font-size` MUST be the exact px from `spec_lock.typography` — if `body` is `24`, write `24`; never substitute a "rounder" or PowerPoint-familiar number (`20` / `18` / `36`). The system is px-only — there is no pt to convert, and a remembered pt-style value written as px renders the whole deck the wrong size. Prefer whole numbers (sizes are clean even px); keep a decimal only for a slot that genuinely carries one in `spec_lock`. Never emit long tails like `20.8026`: the exporter rounds the final size to 1 decimal pt, so extra px precision is wasted noise.
- Images MUST reference files listed under `images`; no invented filenames
- Formula PNGs are images with `Acquire Via: formula`; place a `Rendered` file only from its listed path, use the normal placeholder for `Needs-Manual`, and never recreate the formula as text.

If a page needs a value not in `spec_lock.md`, surface it — do not silently invent one. When an intentional deck-wide or recurring color, type role/size, icon, or image is approved, extend `spec_lock.md` **before** drawing the first affected object, re-read the lock, and only then author the page; do not draw with a temporary hardcoded value and retroactively silence drift warnings.

**Per-page layout rhythm — `page_rhythm` section**:

Before drawing each page, look up its entry in `page_rhythm` (key format `P<NN>` matching the page index in §IX of `design_spec.md`) and apply the corresponding layout discipline:

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). With `template_reuse_scope: mirror`, follow the selected prototype verbatim except visible text values. With `layout`, retain the selected structure system while realizing the page's §IX intent. With `style` or free design, realize §IX directly — for the cover deliver its `Cover impact` and for a closing page its `Closing impact`, never a default centered title + subtitle or generic "Thank you" sign-off. |
| `dense` | Information-heavy. Card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. This is the baseline behavior. |
| `breathing` | Low-density impact page. Avoid **multi-card grid layouts** — do not organize content as multiple parallel rounded containers (3-card row, 4-card KPI grid, 2×2 matrix rendered as cards). Use naked text blocks, dividers, whitespace, or full-bleed imagery as the content structure. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine — the rule is about grid structure, not about the `rx` attribute. Proportions follow information weight (not a preset ratio). Typical forms: hero quote, single large number with one-line interpretation, full-bleed image with floating caption, section transition. |

> Without rhythm variation, every page defaults to card grids (the "AI-generated" look). `page_rhythm` is the only narrative lever that survives context compression.

**Missing or empty `page_rhythm` section — fixed compatibility default** → emit `warning: spec_lock.md missing/empty page_rhythm — defaulting all pages to dense` once, fall back to `dense` for all pages.

**Tag not found for current page — fixed compatibility default** → emit `warning: spec_lock.md page_rhythm tag not found for P<NN> — falling back to dense` once per deck (aggregate; do not repeat per page), fall back to `dense`. Do not invent a tag.

**Per-page template lookup — `page_layouts` section (`mirror` / `layout` only)**:

Before drawing each page, look up its entry in `page_layouts` to decide which basename to inherit (the SVG itself was loaded in §1.0):

- Entry present (e.g., `P04: 03a_content_image_text`) → inherit the corresponding full SVG. The basename **must match** an actual file in the chosen template directory. If it does not, stop before drawing and report the invalid mapping; neither `strict` nor `adaptive` may fall back to free design inside a structured template deck.
- No entry for this page with `template_reuse_scope: mirror|layout` → stop before drawing and report the missing Strategist mapping. Adaptive mode still requires one selected complete template SVG; flexibility applies to the post-design output Layout, not to whether an input prototype exists.
- Whole section absent while `template_reuse_scope: mirror|layout` is present → stop before drawing; the current template contract is incomplete.
- `template_reuse_scope: style` → the whole section must be absent; do not perform per-page prototype lookup.

Do **not** invent a prototype entry, and do **not** assume a structured template just because `templates/` exists. For `mirror` / `layout`, a missing or invalid `page_layouts` row is an upstream contract error. `style` is a separate flat deck route, never a per-page fallback.

**Per-page PowerPoint layout lookup — `template_reuse_scope: mirror|layout` only**:

- When `pptx_structure.mode` is `flat` (including `template_reuse_scope: style`), skip this lookup and the structured scaffold below. `pptx_masters`, `pptx_layouts`, `page_layouts`, and the corresponding SVG metadata must all be absent; each root still declares its canonical `data-pptx-page-role`.
- With `template_reuse_scope: mirror|layout`, `pptx_structure.mode` must equal `structured`; any other or missing value is rejected. Do not migrate an invalid structured contract in place: create a new current-contract workspace through Create Template before generation resumes.
- Read the current page assignment as `P<NN>: <layout_key>`. Resolve the assigned Layout key in `pptx_layouts`, then resolve its Master key in `pptx_masters`. Missing, malformed, or partial mappings stop before drawing.
- Write matching root Master/Layout key and picker names. Do not write `data-pptx-layout-kind` or `data-pptx-page-role`.
- On strict template use, the row and SVG contract match the selected prototype exactly.
- On adaptive template use, retain the prototype Master. If the final composition changes fixed Layout atoms or slot topology/bounds, allocate a new key/name and update this row before completing the page.
- A Layout key may repeat across non-adjacent pages only when its fixed atoms and slot contracts are identical.

**Structured template-page scaffold**:

```xml
<svg viewBox="…"
     data-pptx-master="<master-key>" data-pptx-master-name="<master-name>"
     data-pptx-layout="<layout-key>" data-pptx-layout-name="<layout-name>">
  <rect id="master-bg" data-pptx-layer="master" …/>              <!-- one atomic Master object -->
  <text id="master-footer" data-pptx-layer="master" …>…</text>   <!-- no Master/Layout g -->
  <path id="layout-rule" data-pptx-layer="layout" …/>            <!-- one atomic Layout object -->
  <g id="title-slot" data-pptx-placeholder="title"
     data-pptx-placeholder-bounds="60 36 1160 64">
    <text id="title-carrier" data-pptx-placeholder-carrier="true" …>…</text>
  </g>
  <g id="body-slot" data-pptx-placeholder="body"
     data-pptx-placeholder-idx="1"
     data-pptx-placeholder-bounds="60 120 470 500">
    <text id="body-carrier" data-pptx-placeholder-carrier="true" …>…</text>
  </g>
  <g id="picture-slot" data-pptx-placeholder="picture"
     data-pptx-placeholder-idx="2"
     data-pptx-placeholder-bounds="570 120 650 500">
    <image id="picture-carrier" data-pptx-placeholder-carrier="true" …/>
  </g>
  <g id="content-block-1">…</g>                                  <!-- 3–8 content groups -->
  <g id="content-block-2">…</g>
</svg>
```

On structured template pages, Master/Layout atoms and slot groups are direct root children and precede ordinary content groups. Structural metadata nested inside an ordinary content group fails export. Flat pages use ordinary top-level semantic groups only.

**Per-page chart reference — `page_charts` section**:

Before drawing each page, look up its entry in `page_charts` to decide which chart structure applies (the SVG itself was loaded in §1.0):

- Entry present (e.g., `P09: timeline_horizontal`) → adapt the corresponding chart SVG already in context. Apply project colors/typography/density; do not copy verbatim. Cross-reference `templates/charts/charts_index.json` for the chart's purpose summary if needed.
- No entry for this page → either no chart on this page, or a chart that didn't match any catalog template (Strategist's `no-template-match` fallback). Design the visualization from scratch using `design_spec.md §VII` for guidance.
- Whole section absent → no chart pages in this deck.

---

## 3. Execution Guidelines

- **Proximity**: group related elements with tight spacing; separate unrelated groups
- **Element grouping (Mandatory)**: wrap every logical Slide-local content unit — title, core-message line, each content block, card, list item, and diagram — in a top-level `<g id="...">` with a descriptive, page-unique id. Nested implementation groups within that unit may remain anonymous; they are not independent animation targets. Flat free-design/brand-only pages use ordinary semantic groups for every logical unit. On structured template pages, slot `<g>` elements are already semantic groups and direct Master/Layout atoms are the required exception to grouping. Authored native preset fragments (`preset_shape_svg.py`) already are one atomic `<g id>` each and count as one ordinary content group. When a preset needs labels or decorations, put the preset and those siblings inside a separate parent content group; never put them inside the preset group itself.
- **Spec adherence**: follow color, layout, canvas format, and typography in the spec
- **Template structure**: inherit the native visual framework only for `template_reuse_scope: mirror|layout`; `style` uses the flat route
- **Main-agent ownership**: SVG generation must run in the main agent (not sub-agents) — pages share upstream context for cross-page visual continuity
- **Generation rhythm**: lock global design context first, then generate pages sequentially in one continuous context. No batched groups (e.g., 5 at a time).
- **Fact provenance**: when a §IX page lists `Fact IDs`, resolve each ID from `sources/*.facts.json` and keep the claim/value unchanged. Render a compact source footnote using the source name and a short URL/domain when space permits; state the attribution naturally in speaker notes. When §IX says `Data class: scenario`, place a visible localized `Scenario data` / `情景数据` label adjacent to the affected KPI/chart and state naturally in notes that the number is illustrative. Never attach an external fact ID to scenario data or let an unlabeled invented KPI look factual.
- **Default — stage each page with the style's composition geometry (may override when the content genuinely calls for a plain grid)**: an SVG page is a canvas, not a DOM. Before defaulting to stacked rounded-rect cards or uniform equal columns, pick one page-scale move from the locked visual style's §1 `Composition geometry` (a bleed shape, diagonal split, oversized numeral, orbit rings, …) to stage the page's primary zone. Card grids are one option among many, not the house layout.
- **Reference — image-led promotional pages (not a constraint)**: for travel, venue, product-introduction, hospitality, event, real-estate, and brochure-style decks, let images define the page skeleton before placing text. Consult [`image-layout-patterns.md`](image-layout-patterns.md) §Imported Deck Patterns and prefer patterns such as `#74` TOC image-navigation cards, `#75` asymmetric chapter banners, `#77` photo mosaic with a text cell, `#78` ambient banner + evidence photo + text panel, `#79` ribbon-header image cards, and `#80` side hero image + staggered evidence cards before falling back to plain left/right image-text splits.
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: generate all SVG pages sequentially for visual consistency. Use layout judgment for chart marks during the draft. **MUST embed plot-area markers** per §3.1 below on every chart page — coordinate calibration is a post-generation step (see [`verify-charts`](../workflows/stages/verify-charts.md)) that depends on these markers — and **native object metadata** per §3.2 on every eligible data-chart page. **Reach for native presets** per §3.0 as you draw each page: a block arrow, chevron, banner/ribbon, callout, standard flowchart node, or star is authored through `preset_shape_svg.py` at draw time — decided by the object's intent as you create it, never by scanning finished paths, and never committed to a bare `<path>`/`<polygon>` when a preset expresses it (a gradient fill/stroke or a pattern fill is the one paint exception — keep those ordinary SVG). **First-page gate (Mandatory)**: after completing the first page, run `python3 scripts/svg_quality_checker.py <project_path> --stage first-page` and fix every error before drawing page 2. This stage validates only the first authored page with a partial structure roster; future declared pages are not reported missing.
  2. **Quality Check Gate**: run `python3 scripts/svg_quality_checker.py <project_path> --stage final --json` on `svg_output/`. Any `error` (banned/unsupported features, invalid values, unresolved references, viewBox mismatch, etc.) MUST be fixed on the offending page before proceeding — regenerate and re-check. Every `warning` is advisory: it never sends the page back for required modification, never authorizes automatic rewriting of compatible user syntax, and needs no acknowledgement/disposition line. Recommendation warnings describe the generated-SVG default; fidelity/quality warnings may be surfaced when material, while the existing input remains releasable. Prototype-identical diagnostics are recorded as `inherited`, source conversion losses as `source-import`, changed/new advisories as `introduced`, and release failures as `blocking` in `exports/svg_quality_report.json`. If release truly depends on a condition, it belongs in `errors`. Do NOT defer error handling to after `finalize_svg.py` — finalize rewrites SVG and masks some violations.
  3. **Logic Construction Phase**: after SVGs pass the quality check, batch-generate speaker notes for narrative continuity.

### 3.0 Native Preset Shape Selection

**Reach for a native preset whenever one expresses a complete object — this is
the default, not the exception.** Block arrows, chevrons, banners / ribbons,
callouts, flowchart nodes, stars, and other Office symbols should be **authored
as presets** via `preset_shape_svg.py`, not drawn as plain `<path>`s or faked
with rectangles: presets are what give the slide real PowerPoint shapes with
adjustment handles and the designed, non-flat-card look. When a page calls for
one of these, use the preset. Apply the decision gate in
[`native-shape-authoring.md`](./native-shape-authoring.md) to pick the right
shape and to keep only the exceptions below as ordinary SVG.

| Decision | Action |
|---|---|
| Plain rect / symmetric round rect / circle / ellipse | Keep the ordinary SVG primitive; it is already natively editable. |
| Exact single-preset match | Call `preset_shape_svg.py render` and paste its complete stdout fragment into the current hand-authored SVG. |
| Stock shape that needs a gradient fill/stroke or a pattern fill | Keep ordinary SVG — the helper paints `none` or a solid HEX on both fill and stroke only ([`native-shape-authoring.md`](./native-shape-authoring.md) §5). |
| Page-specific, compound, organic, branded, icon, or data geometry | Keep ordinary SVG path/polygon geometry. |
| Similar-looking contour only | Never guess; keep ordinary SVG. |

This automatic decision applies only before drawing a new object. Do not scan
existing SVG, classify path contours, or upgrade ordinary SVG during export.

**Hard rule**: do not hand-write `data-pptx-authoring`, `data-pptx-prst`,
`data-pptx-frame`, adjustment metadata, or registry paths. The helper generates
one compact atomic `<g>` from the shared 187-shape registry, with semantic
metadata and base paint written once. Rerun the helper when geometry or paint
changes; never edit one of its direct paths.

For chart-template and diagram authoring, thin relationships use ordinary
`<line>` / supported open `<path>` geometry with registered arrow markers;
solid directional blocks use ordinary `shape` presets such as `rightArrow` or
`chevron`. Do not select a connector-family preset merely because two nodes are
related, and never hand-add endpoint/site metadata. Connector-family presets
remain available only for an explicit request for a standalone unconnected
`p:cxnSp`; imported Connector topology stays under the preserve/mirror contract.
`actionButton*` presets provide visual geometry only, not actions or hyperlinks.

**Hard rule — narrow helper scope**: the helper prints one shape fragment to
stdout. It does not write a page or choose layout. Read the fragment and insert
it through the normal `apply_patch` page edit; never redirect, loop, or batch it
into `svg_output/`.

### 3.1 Chart Plot-Area Marker (MANDATORY on every chart page)

> The [`verify-charts`](../workflows/stages/verify-charts.md) stage enumerates chart pages from `design_spec.md §VII`, then reads each page's plot-area marker to feed `svg_position_calculator.py`. A missing marker invokes that stage's declared fallback and adds avoidable derivation work.

**Hard rule**: every SVG page that contains a data visualization chart includes a plot-area marker inside `<g id="chartArea">`, placed **after axis lines** and **before the first data element** (bar, line, area, point).

**Rectangular plot area** (bar / horizontal_bar / grouped_bar / stacked_bar / line / area / stacked_area / scatter / waterfall / pareto / butterfly):

```xml
<!-- chart-plot-area: x_min,y_min,x_max,y_max -->
```

**Radial charts** (pie / donut / radar):

```xml
<!-- chart-plot-area: pie | center: cx,cy | radius: r -->
<!-- chart-plot-area: donut | center: cx,cy | outer-radius: r1 | inner-radius: r2 -->
<!-- chart-plot-area: radar | center: cx,cy | radius: r -->
```

**How to determine coordinate values**:

| Value | Derivation |
|-------|------------|
| `x_min` | X coordinate of the Y-axis line (leftmost data boundary) |
| `y_min` | Y coordinate of the topmost grid line (highest data boundary) |
| `x_max` | X coordinate of the rightmost axis endpoint or grid line |
| `y_max` | Y coordinate of the X-axis baseline |
| `cx, cy` | Center point of pie/donut/radar (accounting for `transform="translate()"`) |
| `r` | Outer radius of the chart |

**Per-page verification** — after writing each chart SVG, confirm the marker exists:

```bash
grep "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

> Calculator-supported data-chart templates in `templates/charts/` include this
> marker as a reference. If a data chart covered by §3.1 lacks it, that is a
> bug. Conceptual diagrams, frameworks, and other non-data visualizations in
> the same library do not use a plot-area marker.
- **Technical specs**: see [shared-standards.md](shared-standards.md) for SVG/PPT constraints
- **Card containers — use the documented patterns**: when a content page needs section cards (4 quadrants, parallel aspects, capability blocks, info cards), use the patterns codified in [`templates/charts/CHART_STYLE_GUIDE.md`](../templates/charts/CHART_STYLE_GUIDE.md) §11 — half-rounded section tab (§11.1), nested card border without stroke (§11.2), card-grid skeletons (§11.3), diagonal dashed relationship arrow for cross-quadrant relationships (§11.5), ground-anchor ellipse as a non-filter depth marker (§11.6), bidirectional interaction arrows for paired protocols (§11.7). Do not reinvent the "tinted full-rounded rect + white cover-rect to hide the bottom corners" hack; it survives in older templates but breaks SVG→PPTX color editing. Reference templates: [`labeled_card.svg`](../templates/charts/labeled_card.svg), [`quadrant_text_bullets.svg`](../templates/charts/quadrant_text_bullets.svg), [`kpi_cards.svg`](../templates/charts/kpi_cards.svg), [`matrix_2x2.svg`](../templates/charts/matrix_2x2.svg), [`team_roster.svg`](../templates/charts/team_roster.svg), [`client_server_flow.svg`](../templates/charts/client_server_flow.svg).
- **Reference — prefer semantic shapes over preset stacks (not a constraint)**: when a slide needs to express "ascending / converging / breaking through / stacking" — i.e., a relationship that goes beyond a generic arrow — prefer a single custom `<polygon>` or `<path>` that encodes the semantics geometrically, rather than stacking multiple preset arrows. A converging-tip path or a podium polygon reads faster than three arrows pointing at a label. Do not codify these as templates — they are page-specific; the rule is just "consider polygon before stacking presets."
- **Reference — visual depth through restraint (not a constraint)**: layered depth comes from rhythm (flat vs lifted, dense vs spacious), not from shadows everywhere. Shadow typically suits 2-3 genuinely floating elements per page (cards on photos, primary CTA, overlays); keep peer-grid cards, dividers, body containers flat. Reach for typography weight, spacing, accent bars, subtle tints **before** shadow.

### 3.2 PowerPoint-Native Chart/Table Replacement Marker (MANDATORY on eligible data-chart and text-grid table pages)

> `svg_to_pptx.py --native-charts-and-tables` replaces marked groups with PowerPoint-native Chart/Table objects (charts get an embedded Excel workbook). Markers stay dormant in the default export, whose SVG children become independently editable DrawingML shapes, but a deck without markers can never form data-backed native Chart/Table objects. Write the marker at draw time: the data is already in hand, and recovering it later costs a full re-read pass.

**Hard rule**: every data chart whose type appears in the **Supported chart types** list of [shared-standards.md](shared-standards.md) "PowerPoint-Native Chart / Table Replacement Markers" (the single authority for the eligible set, marker contract, and JSON schemas) gets `data-pptx-replace-with="chart"` plus one `<metadata type="application/json">` JSON child on its top-level `<g>`, transcribing the same data just plotted. Every pure text-grid data table gets `data-pptx-replace-with="table"` the same way, transcribing all visible cell text into `columns` / `rows`. The parent marker determines the JSON schema; do not duplicate a chart/table kind on the metadata child.

Generated authoring MUST omit `data-pptx-import-source` and
`data-pptx-fallback-sha256`: those attributes record imported-PPTX provenance
and its sealed fallback baseline. Never copy a static baseline from a chart
catalog or reusable template; normal content edits would make it stale.

`data-pptx-replace-with` is a **data-backed replacement claim**, not a generic label for a group that contains numbers and not a marker for ordinary PowerPoint shapes or connectors. Add it only when the matching JSON payload can be written in the same edit; if the object is meant to remain SVG geometry, do not add the marker.

- Chart types absent from that list and conceptual/diagrammatic graphics (process flows, cycles, quadrant cards, timelines, KPI cards) get **no marker** — `svg_quality_checker.py` rejects unsupported marker types.
- Canonical rectangular merged text cells may carry a table marker by putting anchor-only `row_span` / `col_span` in metadata and leaving covered cells blank. Nonrectangular/overlapping merges, nonblank covered cells, and graphical cells (icons, harvey balls, rating dots) get **no table marker** and stay on the SVG fallback route.
- Transcribe, don't restyle: `categories` / `series[].values` are the numbers just plotted; `style.colors` carries the series HEX values already used on the page (from `spec_lock.colors`).
- Data-point color: when a single column/bar series uses data-point colors in the fallback, copy those fills into `series[].point_colors` in category order.
- Data labels: when visible point values are part of the fallback chart, write `data_labels` instead of companion text; use `data_labels.points` for selected labels, and use `number_format`, `font_size`, `font_family`, and per-point `colors` / `color` when the fallback labels carry suffixes or color-coded text.
- Line markers: when the fallback line chart draws visible point nodes, set `line_style: "lineMarker"`; leave the default `line` only for line charts without nodes.
- Area-under-line: when a combo plot is drawn as a filled area under a line, keep `type: "line"`, add `area_fill: true`, and copy the area transparency into `series[].fill_opacity`; copy visible line `stroke-width` into `series[].line_width` for line/area series.
- Native chrome: write `title`, `subtitle`, axis titles, or `show_legend: true` only when the fallback visibly renders the same chrome inside the native chart's replacement scope. `title` is the PowerPoint chart title, not an object name; use `name` for page-semantic object naming (e.g. `p03-revenue-chart`). Write explicit `x`/`y`/`width`/`height` read from the drawn plot area; omission is the fallback — the exporter then infers the frame from the drawn fallback geometry.
- Value-axis labels: when the fallback keeps category labels but intentionally omits numeric value-axis tick labels, set `show_value_axis_labels: false`.
- Freeform chart text: transcribe center labels, source notes, and other in-chart annotations as companion `caption` / `note` / `notes` entries with explicit slide-coordinate bounds; do not rely on fallback `<text>` children to survive native export.
- Native chart typography mirrors the SVG fallback. Copy the fallback's shared chart font into `style.font_family` and visible chart text sizes into the matching metadata fields (`title_font_size`, `subtitle_font_size`, `axis_font_size`, `note_font_size`, etc.) only when role sizes differ; otherwise let the exporter infer them from visible fallback text. When a visible chart title, subtitle, or axis title needs its own size/color/font, write that field as an object with `text`, `font_size`, `font_family`, and `color`. Use `axis_title_font_size`, `legend_font_size`, or companion per-entry `font_size` only when the fallback visibly uses a separate size.
- Native table typography mirrors the SVG fallback. Write `style.font_family` and `style.font_size` from the visible table text; use `header_font_size` or per-cell `font_size` only when the fallback visibly does so. If the fallback has no explicit table font, fall back to the deck body family and locked body size from `spec_lock.md typography`.
- The marker group's transform stays translate/scale only (no rotate / matrix / skew).
- Visual parity is not a goal: the SVG drawing remains the designed visual and exports as editable DrawingML shapes; the native object is the data-backed counterpart with PowerPoint's chart/table-specific model. Never simplify the SVG design to match what a native object could show.

**Per-page verification** — after writing each eligible data-chart or text-grid table page, confirm the marker exists:

```bash
grep "data-pptx-replace-with" <project_path>/svg_output/<current_page>.svg
```

### SVG File Naming Convention

Format: `<NN>_<page_name>.svg` (two-digit number from 01; name matches the deck's language and the page title in the Design Spec).

Examples: `01_封面.svg` / `02_目录.svg` / `03_核心优势.svg`; `01_cover.svg` / `02_agenda.svg` / `03_key_benefits.svg`.

---

## 4. Icon Usage

Strategist chooses the library and inventory; Executor only implements. Library details and one-library rule: [`../templates/icons/README.md`](../templates/icons/README.md). This section defines placeholder syntax.

> **Resolution is project-first.** Strategist copied the chosen icons into `<project_path>/icons/<lib>/` (via `icon_sync.py`); `finalize_svg.py embed-icons` embeds from there, falling back to the global library per-icon. **Custom icons**: drop an `.svg` into `<project_path>/icons/<lib>/` (any `<lib>`, e.g. `custom/`) and reference it as `data-icon="<lib>/<name>"` — it embeds like any other. Reference only icons in the `spec_lock.md` inventory.

> **Icon identifiers are case-sensitive filenames.** For bundled libraries, copy the verified lowercase basename exactly (`tabler-outline/award`, never `tabler-outline/Award`) into `spec_lock.md` and every `data-icon` value. Custom icon identifiers preserve the custom file's exact case; the pipeline never silently lowercases names.

**Built-in icons — Placeholder method (recommended)**:

```xml
<!-- chunk-filled (straight-line geometry, sharp corners, structured) -->
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-filled (bezier-curve forms, smooth & rounded contours) -->
<use data-icon="tabler-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-outline (light, line-art style — screen-only decks) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- phosphor-duotone (single color + 20% backplate — soft depth without solid weight) -->
<use data-icon="phosphor-duotone/house" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- simple-icons (brand logos — used alongside the deck's primary library, only for real company/product marks) -->
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>

<!-- tabler-outline with thin / bold stroke (stroke-style libraries only) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="1.5"/>
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="3"/>
```

> ⚠️ **Color**: ALWAYS use `fill="#HEX"` on `<use data-icon="...">`. NEVER use `stroke` or `fill="none"`, even for stroke-style libraries.
>
> **stroke-width** (stroke-style libraries only, currently `tabler-outline`): allowed values `{1.5, 2, 3}`. If `spec_lock.md icons.stroke_width` is declared, all placeholders MUST use that value deck-wide. Ignored on non-stroke libraries.
>
> **Missing `icons.stroke_width` in an existing stroke-library lock — fixed compatibility default**: use `2`, emit one warning, and continue. New authoring must still declare the field.
>
> Icons are auto-embedded by `finalize_svg.py` — no need to run `embed_icons.py` manually.

**Searching for icons** — use terminal, zero token cost:
```bash
ls skills/ppt-master/templates/icons/chunk-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-outline/ | grep chart
ls skills/ppt-master/templates/icons/phosphor-duotone/ | grep house
ls skills/ppt-master/templates/icons/simple-icons/ | grep github
```

**Abstract concept → icon name** (names for `chunk-filled`; tabler libraries use their own equivalents — verify with `ls | grep`):

| Concept | chunk-filled | tabler-filled / tabler-outline |
|---------|-------|-------------------------------|
| Growth / Increase | `arrow-trend-up` | same |
| Decline / Decrease | `arrow-trend-down` | same |
| Success / Complete | `circle-checkmark` | `circle-check` |
| Warning / Risk | `triangle-exclamation` | `alert-triangle` |
| Innovation / Idea | `lightbulb` | `bulb` |
| Strategy / Goal | `target` | same |
| Efficiency / Speed | `bolt` | same |
| Collaboration / Team | `users` | same |
| Settings / Config | `cog` | `settings` |
| Security / Trust | `shield` | same |
| Money / Finance | `dollar` | `currency-dollar` |
| Time / Deadline | `clock` | same |
| Location / Region | `map-pin` | same |
| Communication | `comment` | `message` |
| Analysis / Data | `chart-bar` | same |
| Process / Flow | `arrows-rotate-clockwise` | `refresh` |
| Global / World | `globe` | `world` |
| Excellence / Award | `star` | same |
| Expand / Scale | `maximize` | same |
| Problem / Issue | `bug` | same |

> For self-evident names (home, user, file, search, arrow, etc.) — just `grep chunk-filled/` directly without consulting the table.

> ⚠️ **Icon validation**: only use icons from the Design Spec's approved inventory. Verify each via `ls | grep` before use. Mixing libraries within one deck is FORBIDDEN.

---

## 5. Visualization Reference

Chart SVGs referenced in **VII. Visualization Reference List** are loaded once via the §1.0 batch read. This section governs adaptation only.

**Hard rule**: adapt the loaded chart SVG; do not improvise from memory and do not replicate verbatim. Apply project colors, typography, content; preserve visualization type.

**Adaptation rules**:
- **Preserve**: visualization type (bar/line/pie/timeline/process/framework…) as specified
- **Adapt**: data, labels, colors (project scheme), dimensions
- **Freely adjust**: composition, axis ranges, grid, legend, spacing, decoration — as long as the chart stays accurate and readable
- **Forbidden**: changing visualization type without spec justification; omitting data points or structural elements from the outline

> Templates: `templates/charts/` (76 types). Index: `templates/charts/charts_index.json`

### 5.1 Chart Coordinate Calibration

Coordinate calibration runs as a **conditional post-generation stage**, not inside the Executor authoring loop. After SVG generation completes, if the deck contains data charts, run [`verify-charts`](../workflows/stages/verify-charts.md) before post-processing.

The executor's only obligation here is upstream: embed the `<!-- chart-plot-area ... -->` marker on every chart page during initial draft (§3.1). Verify-charts enumerates chart pages from `design_spec.md §VII` (authoritative deck plan) and uses the marker to feed `svg_position_calculator.py`.

> Do NOT run `svg_position_calculator.py` during the initial draft. The calculator calibrates already-generated SVGs against their declared plot areas; running it before the SVG exists has nothing to compare against.

---

## 6. Image Handling

Handle images by their status in the Design Spec's Image Resource List. Status enum and lifecycle: [`svg-image-embedding.md`](svg-image-embedding.md).

| Status | Source | Handling |
|--------|--------|----------|
| **Existing** | User-provided | Reference images directly from `../images/` directory |
| **Generated** | Generated by Image_Generator | Reference images directly from `../images/` directory |
| **Sourced** | Web-acquired by Image_Searcher | Reference from `../images/`. **Read [`image_sources.json`](image-searcher.md) to decide attribution** — see §6.1 below. |
| **Rendered** | Deterministic formula PNG | Reference from `../images/`; use `preserveAspectRatio="xMidYMid meet"` |
| **Needs-Manual** | Acquisition failed and file is absent | Use dashed border placeholder unless the expected file exists; the Step 7 readiness gate swaps placeholders for real files before export |
| **Placeholder** | Not yet prepared | Use dashed border placeholder |

**Reference syntax**: see [`svg-image-embedding.md`](svg-image-embedding.md).

**Template-bundled images**: when a template (deck / layout / brand) is applied, its bitmaps are copied into the project's `images/` alongside every other runtime image (SKILL.md Step 3). Reference them the same way — `../images/<name>` — and do **not** reproduce a template SVG's bare sibling href (e.g. `href="cover_bg.png"`): the template SVG is reference material, the rendered page lives in `svg_output/` and must point at `../images/`. `template_reuse_scope: mirror` (§1.1) is the one exception — it copies hrefs verbatim, and the exporter resolves those bare hrefs against `images/`.

**Placeholder**: Dashed border `<rect stroke-dasharray="8,4" .../>` + description text

**`no-crop` images**: when a `spec_lock.md images` entry ends with ` | no-crop`, size the container to the image's native ratio (from `analyze_images.py` or file dims) and use `preserveAspectRatio="xMidYMid meet"`. Untagged entries are croppable — default to `slice`.

**Formula images — declared-inference fallback for a missing `no-crop` flag**: rows with `Acquire Via: formula` or `Type: Latex Formula` MUST be treated as no-crop. For a rendered file, use dimensions in this order: current `analysis/image_analysis.csv`, `design_spec.md §VIII`, then `images/formula_manifest.json`. For a `Needs-Manual` row, size the dashed placeholder from the planned dimensions in §VIII, then the manifest; the Step 7 readiness gate re-analyzes the supplied file and reconciles the container before export. Do not normalize all formulas to one height unless the spec explicitly states that layout choice.

### 6.1 Inline Attribution for Sourced Images (web path)

Whenever the slide uses an image with `Status: Sourced`, look up the corresponding entry in `project/images/image_sources.json` and act on `license_tier`:

| `license_tier` | Action on this slide |
|---|---|
| `no-attribution` | Embed the `<image>` element only. **No credit element needed.** |
| `attribution-required` | Embed the `<image>` element **plus** a small inline `<text>` credit element per the visual spec in [image-searcher.md §7](./image-searcher.md). |
| `manual` | Embed the `<image>` element only. **No credit element** — a user-supplied `--from-url` replacement; verifying usage rights / any required credit is the user's responsibility. |

The credit text is **not** rendered by post-processing or export — it must be present in the SVG you produce. The shape of the credit element (size, position, color, multi-image source line, hero gradient overlay) is specified in [image-searcher.md §7](./image-searcher.md). Do not invent a different style.

Use `attribution_text` from the manifest entry as the **starting point**, then compress for the small-text constraint (drop URL, drop filename, keep "via Provider / License"). For CC0/PD images that landed in the `attribution-required` tier only because of upstream metadata quirks (rare), credits are still safe to render.

`svg_quality_checker.py` treats missing CC BY / CC BY-SA inline attribution as an **error**. Fix the offending SVG before post-processing.

**The manifest is the single source of truth for credits.** Do not duplicate license info into speaker notes or any other artifact.

---

## 7. Font Usage

Source of truth: `spec_lock.md typography`. Use `font_family` as default; override per role with `title_family` / `body_family` / `emphasis_family` / `code_family` if declared. LaTeX formulas that Strategist rendered are PNG images, not a `code_family` text role.

**Missing required field — `typography.font_family`** → stop and return to [`strategist.md`](strategist.md) §6 step 4 to repair `spec_lock.md`; do not infer a stack from `design_spec.md`.

**Hard rule**: every SVG `font-family` stack MUST resolve to pre-installed exported Latin / EA typefaces (Microsoft YaHei / SimHei / SimSun / Arial / Calibri / Segoe UI / Times New Roman / Georgia / Consolas / Courier New / Impact / Arial Black). PPTX has no runtime fallback — missing fonts degrade to Calibri.

---

## 8. Speaker Notes Generation Framework

### Task 1. Generate Complete Speaker Notes Document

After all SVG pages are finalized, enter Logic Construction Phase and write the full notes to `notes/total.md`. Batch-writing (not per-page) lets transitions plan coherently.

**Pure spoken narration**: notes are read aloud verbatim by `notes_to_audio.py` (TTS). Write only what should be spoken. No visible markers, no labeled meta-lines, no enumerated key-point lists, no duration annotations — anything you write outside the heading will be vocalized.

**Per-page structure**: `# <number>_<page_title>` heading (the `#` heading line is the only thing stripped before TTS), pages separated by `---`. Body is 2–5 natural sentences carrying the page's core message. Page-to-page transitions live inside the opening sentence as natural prose ("接下来……" / "Having framed X, let's turn to Y") — no bracketed `[过渡]` / `[Transition]` tags.

**Reading-mode note burden**:

| `consumption_mode` | Notes emphasis |
|---|---|
| `text` | Add interpretation or transition without reading the already self-contained page aloud. |
| `balanced` | Connect the visible claim and evidence, explain the trade-off, and bridge to the next page. |
| `presentation` | Carry the reasoning, context, and supporting detail intentionally omitted from the sparse projected surface. |

**Concrete examples** — same shape applies to any language; just write naturally in that language.

中文 deck：

```
# 02_市场格局

在明确了行业背景之后，我们来看具体的市场格局。当前线上零售集中度持续上升，前三大平台合计份额已经达到百分之六十八，腰部玩家正在被快速挤压，留给新进入者的窗口期不超过十八个月。这意味着我们的策略必须聚焦，而不是铺开。
```

英文 deck：

```
# 02_market_landscape

Having framed the industry backdrop, let's look at the actual market landscape. Online retail concentration keeps rising — the top three platforms now hold sixty-eight percent of combined share, mid-tier players are being squeezed fast, and the window for new entrants is under eighteen months. This means our strategy has to focus, not spread.
```

> 日本語 / 한국어 / 其他语言：照搬同样的结构，用对应语言自然书写即可。

**Number readability**: TTS reads digits and symbols literally. Prefer fully-spelled forms in the language being spoken when literal pronunciation would be awkward (e.g. Chinese "百分之六十八" reads better than "68%"; "1-2分钟" reads as "一减二分钟"). Plain integers and percentages in English are fine as-is.

**Common mistakes to avoid**:
- Leaving any bracketed stage marker (`[过渡]` / `[Transition]` / `[Pause]` / `[Data]` / `[Scan Room]` / `[Interactive]` / `[Benchmark]` etc.) in the text — they will be read aloud literally.
- Adding `要点：① …` / `Key points: (1) …` / `时长：2分钟` / `Duration: 2 minutes` / `Flex: …` lines — TTS will speak "要点 一 …".
- Mixing languages within one deck's notes.

### Task 2. Split Into Per-Page Note Files

Auto-split `notes/total.md` into per-page files in `notes/`.

**Naming**: match SVG names (`01_cover.svg` → `notes/01_cover.md`); `slide01.md` also supported (legacy).

---

## 9. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (canonical workflow: [`SKILL.md` Step 7](../SKILL.md)):

```bash
# 1. Split speaker notes
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons/images and flatten positioned text)
python3 scripts/finalize_svg.py <project_path>
# Output: svg_final/ self-contained SVG visual previews

# 3. Export PPTX
python3 scripts/svg_to_pptx.py <project_path>
# Output (default-flow mode):
#   exports/<project_name>_<timestamp>.pptx           ← native pptx (canonical output)
#   backup/<timestamp>/svg_output/                    ← Executor SVG source backup (always written)
```

`svg_final/` may be opened directly or manually inserted into PowerPoint as an SVG picture. It is not a second PPTX route. Use `-s final` only for converter diagnostics; release exports use the default `svg_output/` source. Manual Convert-to-Shape behavior is unsupported.
