# Executor Flat and Shared Core

Always-loaded Executor authority for flat SVG page authoring, shared by Default and Quick. Executor is the crew that builds the finished pages on the plan's structure: it receives the blueprint (§2), owns every decision judged on the canvas — carrier mix, geometry, composition, hierarchy, treatment — and draws from the expression vocabulary below. Items marked `Default only` bind to the persisted Design Spec / `spec_lock.md`; Quick applies the same craft to the transient anchors from [`quick-generate.md`](../workflows/profiles/quick-generate.md) §2, and its own pacing, single final checker, and export replace the Default gates and §6.

**Conditional branch routing** — evaluate every trigger once over the whole roster before P01 (Default: §IX; Quick: the frozen transient roster) and read the triggered modules then, in one batch, so that reading stays out of the page loop; a page that reaches a capability the sweep did not foresee reads its module at that moment, before that page's first SVG line:

| Trigger | Load |
|---|---|
| `pptx_structure.mode: structured` | [`executor-structured.md`](./executor-structured.md) |
| Any selected Chart/Table `family/key` reference, or a legacy `page_charts` row that resolves to a live Chart/Table SVG | [`executor-visualization.md`](./executor-visualization.md), then the resolver-returned Chart/Table branch |
| Any value-driven geometry, including a chart-family reference, mini chart, sparkline, inset, or small multiple | [`executor-chart.md`](./executor-chart.md) |
| Any semantic cell grid, including a table-family reference | [`executor-table.md`](./executor-table.md) |
| A page uses a preset pattern fill, or an independent Chart/Table object is resolved as `<object-key>=yes` | [`native-data-interface.md`](./native-data-interface.md) before emitting the pattern or replacement metadata |
| The per-page Structure decision is `yes` for the first time | [`executor-structure.md`](./executor-structure.md) + [`topology-assembly.md`](./topology-assembly.md) |
| A page's contour reaches beyond rectangle, rounded rectangle, circle, ellipse, and line — block arrow, chevron, callout, flowchart symbol, banner, star, bracket, connector preset — or needs a Boolean / freeform decision | [`native-shape-authoring.md`](./native-shape-authoring.md), read completely (the preset vocabulary is already resident) |
| A page's visual job reaches beyond the everyday block below — faux glass, constructed styles (hand-drawn, ink, riso, pixel, halftone, paper-cut, facets, gradient ribbon), gradient stroke, text picture/texture fill, gauge / sunburst / explicit arc geometry, freeform curves, transforms beyond rotate, or an unsupported effect needing a native-safe alternative | [`svg-effects.md`](./svg-effects.md) |
| Any image | [`executor-image.md`](./executor-image.md) + [`image-layout-spec.md`](./image-layout-spec.md) + [`image-layout-patterns.md`](./image-layout-patterns.md) + [`svg-image-embedding.md`](./svg-image-embedding.md) |
| Any nontrivial mathematical expression | [`native-formula.md`](./native-formula.md) |
| Any external or same-deck click hyperlink | [`native-hyperlinks.md`](./native-hyperlinks.md) |
| Any placed image is `Status: Sourced` or its filename has an `image_sources.json` record | [`executor-web-image.md`](./executor-web-image.md), after `executor-image.md` |
| Effective Speaker Notes outcome is enabled after all SVG pages pass | [`executor-notes.md`](./executor-notes.md) |

Evaluate branches from each object's actual information model, not only from a Chart/Table reference: a catalog family selects construction guidance, never native readiness, and page-local qualitative geometry never implies `pptx_structure.mode: structured`. Narrative skeleton and aesthetic come from the confirmed mode / visual-style values (Default: the lock; Quick: the active context): when a value names a catalog preset, read that one file; when it is `custom` with `*_references`, read only those files (one basis under its behavior, or several by their stated contributions); a `custom` without references reads no catalog file and follows its behavior prose alone; the planning indexes are never reopened. [`shared-standards-core.md`](./shared-standards-core.md) supplies the technical boundary and the fallback visual-quality and leading defaults.

**Hard rule — Shape-first page authority**: every visible object of the exported slide exists in the final page SVG or is explicitly referenced by it; templates and `spec_lock.md` guide construction and never supply content at export. Optional native Chart/Table metadata belongs to an independently selected object and never replaces the visible fallback ([`native-data-interface.md`](./native-data-interface.md)); a native formula marker keeps a matching SVG preview that export alone replaces ([`native-formula.md`](./native-formula.md)).

**Hard rule — flat PowerPoint structure**: free-design, brand-only, Style-only, and `template_reuse_scope: style` projects use `pptx_structure.mode: flat`: no root Master/Layout identity, `data-pptx-layer`, or `data-pptx-placeholder`; every object Slide-local; the root declares exactly one `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`). A Style supplies direction, rhythm, and expression defaults without prototypes; its identity-adjacent defaults yield to the final Brand/Deck identity and the lock, and beside Layout/Deck it changes only method. Add `data-pptx-role` only to page-frame objects whose package, page-number, or animation behavior no specialized marker expresses, with a stable unique `id` ([`semantic-svg.md`](./semantic-svg.md)).

**Hard rule — supported PPTX route**: `svg_output/` through the project converter is the only generated-PPTX path; `svg_final/` is an optional preview and PowerPoint's manual Convert-to-Shape is not an authoring target ([`shared-standards-core.md`](./shared-standards-core.md) §4.2). Speaker notes, animations, transitions, narration, and native-PPTX workflows keep their own artifacts.

---

## Page Expression Core

Read this before §1: the expression vocabulary every page draws from — what exists, recalled here so it is available at the moment a page is composed. The contracts below bound how it is written, not whether it is available; the full manuals load on their routing triggers.

**Capability — typographic feature elements**: beyond the structural roles fixed by `typography` anchors, a page may carry a lead-in sentence, an inline emphasis run, a pull quote, a kicker, a hero number, a takeaway line — each its own feature element with its own size and treatment; a recurring one becomes a named role.

**Capability — inline emphasis is one editable frame**: a `<text>` paragraph may nest non-positional `<tspan>` runs with their own `fill`, `font-weight`, or `font-size`; export emits one DrawingML run per styled segment inside the same editable frame, and positioned line-break `<tspan>` children may themselves contain inline runs.

```xml
<text x="72" y="300" font-size="24" fill="#2E3230">腐朽但仍可加固接续的<tspan fill="#9E2B25" font-weight="bold">千年木梁，不做整体更换</tspan>；风化的古墙，只做防风化微创处理。</text>
```

**Capability — native contour families**: beyond rectangle, rounded rectangle, circle, ellipse, and line, the complete Office vocabulary is drawable and stays editable in PowerPoint — block arrows and chevrons for direction and steps, flowchart symbols for process and decision, callouts, brackets and braces, stars and banners, bent and curved connectors, equation shapes, and the basic-shape family (triangles, hexagons, parallelograms, trapezoids, pies, arcs, frames) — each through `preset_shape_svg.py`, with Merge Shapes results through `shape_boolean_svg.py`. [`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) is the full list; §3.0 owns selection and encoding.

**Reference — everyday device menu (not a constraint, not a quota)**: the pieces most slides are built from.

| Device | Typical job | Realization |
|---|---|---|
| Gradient block or band | Cover / chapter field, title backing, zone separation | `<linearGradient>` / `<radialGradient>` in 2–3 stops of the deck hue |
| Rounded card | One content module among peers, a feature or option block | `<rect rx>` in `secondary_bg`; a shadow only when it floats over a photo or colored panel |
| Icon with label | Feature markers, list prefixes, step or category cues | `<use data-icon>` at 32–48 px in an accent or primary role |
| Numbered circle or badge | Ordered steps, ranked items, chapter marks | `<circle>` + centered number; oversized numeral for a chapter |
| Color swatch | A color, material, or sample that the content names | `<circle>` / `<rect>` filled with the subject's own value, labeled with its name and HEX |
| KPI card | Metric name + hero number + trend or comparison | Card + number at the hero size + small annotation; icon optional |
| Takeaway box | One-sentence conclusion under a title | Tinted band (`fill-opacity` 0.06–0.10) with the sentence in lead size |
| Divider or rule | Separate sections, columns, header from body | Hairline `<line>` in `divider`, or a 2 px accent bar |
| Full-bleed image + scrim | Cover, chapter divider, mood page | Image `slice` + directional gradient scrim + floating title |
| Framed or shaped picture | Portrait, product, place, evidence photo | Circle / rounded clip on `<image>`, hairline frame, caption |
| Quote block | Pull quote, testimonial, source sentence | Oversized quotation mark or accent rule + text at lead size + attribution |
| Timeline or step strip | Ordered events or stages | Baseline `<line>` with ticks/nodes, or chevron presets, labels above/below |
| Process or decision diagram | Flow, branch, input → output, cycle | Flowchart / block-arrow / chevron presets as nodes and direction, `<line>` or connector presets between them, labels native |
| Callout or annotation | A remark attached to an object or region | Callout preset, bracket, or leader line + short native text |
| Display text with gradient or glow | Hero number, cover word, or chapter numeral that should read luminous or material | Text `fill="url(#…)"` or `filter="url(#titleGlow)"` on that one element; body copy never ([`svg-effects.md`](./svg-effects.md) §6.7 / §6.4) |
| Accent gradient rule or band | Title underline, section marker, KPI baseline carrying the deck hue with direction | 2–4 px `<rect>` / `<line>` filled by a 2-stop primary → accent gradient |
| Elevated primary object | The one card, image, or CTA that sits above the page | `softShadow` at resting opacity on that object; peers stay flat |
| Duotone or brand-wash image | A photo that must join the deck palette instead of fighting it | Wash gradient over the picture, or a prepared duotone derivative ([`svg-effects.md`](./svg-effects.md) §6.5 / §6.12) |

**Reference — layout structures (starting points; proportion follows information weight)**: 16:9 values for 1280×720 — safe area 1200×640 with 40 px margins; title band ≈ 100 px, content field ≈ 500 px, footer ≈ 40 px.

| Content relationship | Useful starting structure | Starting geometry |
|---|---|---|
| One focal claim | Centered single column, negative space, or full-bleed field + floating text | Column 800–1000 px wide; a negative-space page leaves 40–60% empty |
| Equal comparison | Symmetric split or a true matrix / four quadrants | 1:1 with a 40–60 px gap; quadrants ≈ 560×250 with 20–30 px gaps |
| Dominant evidence + takeaway | Asymmetric split with one dominant field | 3:7 / 2:8, heavy side 840–1024 px |
| Parallel sequence | Three columns, process line, chevron strip, or Z-pattern / waterfall | Three columns with 30–40 px gaps |
| Core + surrounding forces | Center-radiating or hub-spoke | Hub 200–300 px with 4–6 satellites |
| Wide visual + explanation | Top-bottom split, or figure-text overlap for a hero moment | Visual ≥ 55% of the field |
| Page-field organization | One large surface, outline, aperture, or off-canvas contour organizes the zones instead of a card per unit | Field spans two or more zones |

Repeating symmetric card grids without a page job is the failure mode these structures exist to avoid; a page-field, outline carrier, nested field, or continuity construction is compared before stacked cards or uniform equal columns ([`native-shape-authoring.md`](./native-shape-authoring.md) §2.1 composition lenses — page field, outline carrier, nested fields, continuity, depth and contrast, deck language).

**Reference — page-level recipes (back to front; omit every layer without a job)**: cover = hero field → optional scrim/wash → purposeful opening/contour → native title; divider = image band or quiet field → restrained wash → recurring geometry → number/title; text-led explanation = quiet field → recurring material/contour → native hierarchy → local emphasis; process/system = context field → native relation lines → nodes/labels → optional state/direction focus; evidence/metric = context field → local contrast → native leaders/labels/metric → optional focus/elevation; comparison = matched planes → shared wash/divider → matched labels → one difference marker; closing = receded field → echoed contour/gradient → native action → raised accent; cross-page motif = reuse contour, gradient direction, line language, texture, or light logic and vary scale, crop, position by page job. Full stacks and stops: [`svg-effects.md`](./svg-effects.md) §6.13.

**Reference — image composition families (any image page)**: `P1` single visual (side, band, inset, hero), `P2` image as canvas with native overlay, `P3` multi-visual (grid, collage, sequence, compare); modifiers `M1` reveal / crop / registration, `M2` tone / focus / contrast (scrim, wash, vignette, spotlight), `M3` framing / placement / depth; prepared-asset `A` treatments and cross-page `C` continuity. Catalog and situation router: [`image-layout-patterns.md`](./image-layout-patterns.md); integration decision: [`executor-image.md`](./executor-image.md).

**Reference — visual job router (recall; the full table is [`svg-effects.md`](./svg-effects.md) §6.1)**: missing direction, continuous value, or center focus → gradient or channel alpha; unclear elevation or boundary → one-light shadow, restrained glow, or hairline; copy and image not integrating → scrim, fade, wash, vignette, spotlight, or faux glass; unclear relationship state → dash for draft/optional, marker for direction, gradient stroke for flow, frame/contour for boundary; a load-bearing figure lost in a scan → inline emphasis run; display text needing silhouette or material → outline, gradient, picture/texture fill, tracking, glow; a style asking for hand, print, pixel, facets, layers, or ribbon → the matching constructed recipe; an unmatched silhouette, radial hierarchy, or gauge → freeform, explicit arc/sector, or calculated arrowhead.

**Reference — everyday effects and aesthetic defaults (self-contained; the full contract and rarer techniques are [`svg-effects.md`](./svg-effects.md))**:

- **Color**: 60-30-10 as the starting proportion (dominant field ≈ 60%, support ≈ 30%, accent ≈ 10%), body text contrast ≥ 4.5:1, hue count following encoding and natural assets; cover and chapter pages may use the theme color as a large field; same-hue gradients add depth; the accent color goes on the key number or word to create focus, not everywhere; cool tones read technical, warm tones energetic, dark fields grave; trends use green up / red down / gray flat with the deck's polarity roles.
- **Rhythm and weight**: follow a data-heavy page with a breathing page; balance visual weight — dark or large elements are heavy, light or small ones light — across left/right and top/bottom; a chapter may share one carrier system while chapters vary, provided each repetition has a page job. A content page may add a one-sentence takeaway band under the title and a muted source note at the page bottom (title voice belongs to the locked mode).
- **Depth through restraint**: depth comes from rhythm (flat vs lifted, dense vs spacious), not shadows everywhere — shadow 2–3 genuinely floating objects per page at most (card over a photo or colored panel, the primary CTA, an overlay) and keep peer-grid cards, dividers, and body containers flat; reach for weight, spacing, accent bars, and tints before shadow; pick one weight tool per container (shadow, border, gradient fill, or strong tint — never stacked); one light source per page (`dx="0"`, `dy="4"`–`"8"`); the shadow is felt, not seen — resting `flood-opacity` 0.06–0.10, raised at most 0.20 (above that is the Office 2007 look); on dark fields use a light hairline or a restrained glow instead of black shadow.
- **Image overlays**: a directional scrim darkest beside the text (`0.88 → 0.30 → 0`), a bottom fade under a lower title (`0 → 0.72`), a radial vignette for atmosphere (`0 → 0.58`), or a brand wash (`0.80 → 0.10`); never a uniform flat opacity over the whole image or a solid black plate.
- **Lines**: `stroke-dasharray` `4,4` separator, `2,2` placeholder outline, `8,4` timeline or flow connector, `8,4,2,4` dimension line; `marker-end` for connector arrowheads; divider hairlines at 0.2–0.3 alpha.
- **Inline emphasis**: lift numerical results, before/after contrasts, and one or two load-bearing nouns per sentence as bold runs in the primary color; never connectives, common verbs, every noun, decorative adjectives, or structural text (footer, axis, legend, page number); reserve green/red for real polarity.

```xml
<defs>
  <filter id="softShadow" x="-15%" y="-20%" width="130%" height="150%">
    <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000000" flood-opacity="0.10"/>
  </filter>
  <filter id="titleGlow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="b"/>
    <feFlood flood-color="#1A73E8" flood-opacity="0.45" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="field" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#1A73E8"/><stop offset="100%" stop-color="#0D47A1"/>
  </linearGradient>
  <linearGradient id="scrim" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#1A1A2E" stop-opacity="0.85"/>
    <stop offset="55%" stop-color="#1A1A2E" stop-opacity="0.30"/>
    <stop offset="100%" stop-color="#1A1A2E" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="60" y="60" width="400" height="240" rx="12" fill="#FFFFFF" filter="url(#softShadow)"/>   <!-- card floating over a photo/panel -->
<image href="../images/cover.jpg" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>
<rect x="0" y="0" width="1280" height="720" fill="url(#scrim)"/>   <!-- text sits on the dark side -->
```

---

## 1. Effect Capability Discovery

**Reference — effects are a triggered module**: the everyday block above covers gradients, cards, shadow, glow, scrims, dashes, and inline emphasis for most pages. Load [`svg-effects.md`](./svg-effects.md) when the pre-P01 sweep or a page's job reaches beyond it (routing table above); once loaded, its §6.1 Visual Job Router recalls candidates and §6.13 offers coordinated page recipes, and it stays in context for the rest of the run. Active cross-page continuous action additionally loads [`animations.md`](./animations.md) §3.1 before authoring both endpoints.

**Hard rule — discovery does not expand compatibility**: follow `svg-effects.md` syntax and fallbacks; source/backdrop blur, blend mode, `<mask>` / per-pixel masking, dense texture, and skew stay baked or alternative-only.

**Default — author motion endpoints while pages are still being written (may override when the deck has no continuous action)**: effects, transitions, and Morph pair keys are post-processing, but the two visible endpoint states are not. Only an explicit user motion instruction, an enabled Custom Animations outcome, or an existing `animations.json` activates this; a §IX Motion suggestion alone does not. A sequence that should read as one action (slide-in, flip, push-in, progressive reveal, pan) is authored now as consecutive pages, each continuing endpoint in a compatible direct-root group (ids or geometry may differ; `animations.json` binds them later). A deck exported without both states cannot gain the motion by a flag; adding a page is a §IX roster change and returns to Strategist.

---

## 2. Blueprint Intake

Executor receives the plan and builds on it: Default reads the retained `design_spec.md` and `spec_lock.md`; Quick holds the same decisions as transient §2 anchors. The plan owns what must be true about every page — content, `Relationships`, roster, rhythm, resources, identity; Executor owns how it looks. Pipeline mechanics of the Default run — context validity and rereads, roster invariance, the five-page lock re-read, recovery from a missing artifact, the pre-P01 parameter confirmation, and the gate cadence — are owned by [`generate-pptx.md`](../workflows/generate-pptx.md) Step 6, not restated here.

### 2.1 Execution context and binding

> Quick has no Design Spec or lock: apply the binding, Reference, content-vs-expression, reading-mode, `page_rhythm`, and anchor rules here to its transient §2 anchors.

**Hard rule — binding selection vs realization**: Strategist-selected content and `Relationships`, roster and `page_rhythm`, resource paths, structured-template routing keys, core fonts, palette and spacing anchors, icon-library/stroke anchors, crop boundaries, and any field labeled `(binding)` bind. Everything else — the carrier mix, geometry, composition, and which prepared icon serves a page — is realization, plus the sparse local garnish allowed below. Missing or unresolved material stops execution and returns upstream; never search, generate, download, sync, invent, or substitute it.

**Reference — planning sketches are adjusted freely**: §V/§IX `Layout`, cover/closing composition, capability recommendations, §III motif direction, Chart/Table `family/key` references, §VIII image-layout patterns, and Motion suggestions are starting sketches: adjust or replace each for the page's purpose, with no upstream repair or stated reason; they carry no binding semantics (what must hold is in the binding fields above), and a `(binding)` field is followed literally. Executor owns final carrier choice, page-scale composition, information-preserving visualization, geometry, spacing, coordinates, native construction, and effects.

**Hard rule — content vs expression**: §IX owns each page's semantic content — complete preferred wording and block texture at `complete` depth, a short block list at `brief` — and its wording is not verbatim unless marked literal. Executor may paraphrase, condense repetition, regroup or reorder within the page, and switch among prose, bullets, keywords, labels, or visual annotation when fit or readability benefits, provided the result stays information-equivalent: the `Core message`, `Audience move`, and every claim, fact, value, proper name, qualifier, relationship, evidence, and literal requirement survive. Never add a claim, move content across pages, or drop information to fit a layout; quotation marks and first person only for wording the source itself gives as a quote — reported speech stays reported; return an unfit or underspecified block for Design Spec repair. Use named lock roles literally where they apply, apply an optional `Template Application`, and choose page-local values from the Design Spec, style, content, and composition rather than forcing every object into a lock row. Read sources only to resolve listed `Fact IDs` or verify required claims, quotes, names, or data; never to add content.

**Per-page communication trace**: read `communication.objective`, `communication.core_message`, and the page's §IX `Core message` + `Audience move` before composing. The page must advance the objective and make that move; a page that cannot state its move is an outline defect — surface `warning: P<NN> has no communication move` rather than decorating around it, and never invent a purpose at execution time. Structural pages advance the contract by establishing relevance, tension, or the decision frame, or by completing the final commitment.

**Mandatory — per-page Structure decision**: before drawing, read the page's §IX `Relationships` (Quick: the transient relationship statement), then `Visualization` and `Content`, and decide whether geometry must carry that qualitative `order`, `link`, `parent`, `membership`, `contrast`, or `overlap` relationship — from the semantic relationship alone; a missing line is a Design Spec defect: repair that §IX block first (continuous run) or return upstream, never infer the relationship at execution — loading [`executor-structure.md`](./executor-structure.md) and [`topology-assembly.md`](./topology-assembly.md) at the first `yes`; a suggested carrier, topology, or composition does not decide it. `no` stays on this base path; `yes` applies that grammar and keeps the relationship statement in active page context with no catalog reference, lock row, or artifact. A Chart/Table reference never substitutes.

**Per-page reading-mode check**: apply `communication.consumption_mode` with the §IX block texture and `page_rhythm` — `text`: the visible page stands alone (complete prose, explicit labels / captions / sources, tables, necessary detail); `balanced`: the primary claim and its evidence on the page, enabled notes adding interpretation and transitions; `presentation`: one claim and one dominant visual legible at projection distance, concise copy, enabled notes carrying explanation — and with notes disabled never omit required content on the assumption that notes carry it. Never drop or invent facts to force a mode; when the authored texture materially conflicts with the lock, render the least-destructive faithful composition and surface `warning: P<NN> content texture conflicts with consumption_mode <value>` (a judgment, not a checker rule).

**Default — authored texture (may override when information-equivalent)**: start from each §IX block's written texture (`complete`) or expand its block phrasing (`brief`) under the reading mode. Keep prose where continuity carries cause, argument, narrative, qualification, or emphasis; use bullets or keywords only for genuinely parallel or ordered material or a clearer information-equivalent structure — never because a list is easier to lay out or a template exposes a list slot. An inherited slot never overrides the content relationship — widen, reflow, or drop the card before converting prose to fill a list slot; the locked mode shapes voice and register, not §IX's authored titles or page order (a user-authored topic label stays a label even when the mode favors assertions). Block-level phrasing applies *within* the page's `page_rhythm` density, not against it.

**Hard rule — one paragraph, one text frame**: one `<text>` per prose paragraph with positioned `<tspan>` line breaks, never sibling `<text>` elements ([`shared-standards-core.md`](./shared-standards-core.md) §4.2); start from its leading ranges, then adjust for typeface, reading distance, explicit requirements, and locked style.

**Execution anchors and contextual values**:

- Icons: any SVG prepared under `<project_path>/icons/` is usable; `icons.library` records the primary bundled style and `icons.inventory` indexes the synced pool without assigning icons to pages or limiting other project-local assets; `simple-icons` entries are real brand marks, not a library. Illustrated icons are transparent slices under `images/` and follow [`executor-image.md`](./executor-image.md) — never moved into `icons/`, added to the inventory, or rendered through `<use data-icon>`.
- Colors: core roles keep their meaning; derive tints, shades, alpha, gradients, and effects, preserve natural asset colors, and use sparse page-local accents that never become a competing or recurring palette.
- Spacing: §V anchors (page margin, block gap, column gutter, corner radius, body leading) are deck-wide identity; depart only for a page job, never to make content fit.
- Families: resolve by role — exact `<role>_family`, then `title_family` / `body_family`, then legacy `font_family`; never flatten a declared override. A sparse export-safe accent family may style short non-structural display or ornament only; recurrence needs upstream selection.
- Sizes: map every structural text item to a declared `typography` role and write its anchor or a value within `±2` px, as unitless px with at most two decimals; peers on one page stay consistent, and bounded adjustment creates no new role. Never inherit a template placeholder size. `lead` / `subtitle` carry the page's primary claim; `footnote` / `annotation` carry footnotes, page numbers, and credits.
- **Sparse display-size exception**: a short non-structural Hero/Display element may use one undeclared size at most twice across the deck without a lock row. The third occurrence makes it recurring — stop, return to Strategist to name the role in the Design Spec and lock, then read back and validate before reuse. Never for titles, body, subtitles, annotations, footnotes, captions, data labels, or card copy, and never imitated with nearby sizes.
- **Outside-band recovery**: structural text reflows geometry and uses the declared band; a sparse display occurrence keeps its value while its deck-wide count stays ≤2. Never flatten a justified distinction or add a role to silence the checker; mirror pages keep exact source typography.
- **Prepared decorative lettering**: place the approved AI/slice file as an image and keep the editable title/subtitle in separate native frames; never rebuild it from glyph copies or WordArt, and never invent a missing asset when the plan kept the wording native.
- Images reference only files listed under `images`; math loads [`native-formula.md`](./native-formula.md) — simple notation stays text, one-line structural prose goes inline only when its native height fits the reserved row, matrices and multiline or vertically expanding math go block; exact LaTeX plus preview, never an image.

Return upstream before a derived or accent identity becomes recurring or structural; garnish, `±2` px adjustments, and two sparse display occurrences need no lock row, and the lock is never expanded to silence a comparison.

**Per-page layout rhythm — `page_rhythm`**: before drawing, apply the page's tag (key `P<NN>` matching §IX):

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). `mirror` follows its prototype; `layout` retains its structure system; `style` / free design preserves the §IX cover hook or closing takeaway; the recommended composition is a Reference. |
| `dense` | Information-heavy: card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. The baseline. |
| `breathing` | Low-density impact page: naked text, dividers, whitespace, or full-bleed imagery carry the structure; proportions follow information weight. Hero quote, single large number with one line, full-bleed image with floating caption, section transition. |

Mechanical repetition comes from reusing one carrier and topology without a page job, not from cards themselves; vary rhythm when the content relationship changes. Missing or empty `page_rhythm` → `warning: spec_lock.md missing/empty page_rhythm — defaulting all pages to dense` once, all pages `dense`. Tag missing for a page → `warning: spec_lock.md page_rhythm tag not found for P<NN> — falling back to dense` once per deck, `dense`; never invent a tag.

---

## 3. Execution Guidelines

**Per-page composition (craft; the vocabulary is the Page Expression Core)**:

- **Mandatory — resolve the page carrier mix before coordinates**: in one page-level decision, choose the background field, editable text and optional lettering, native geometry/lines, prepared photos/scenes/illustration/icon assets, and applicable visualizations — their combination, visual weight, z-order, and local construction from the page message and hierarchy, using only prepared resources and preserving every binding resource job. The resolved style controls treatment and emphasis, never carrier eligibility, image source, or the native vocabulary. Recall the vocabulary here: the style's §1 `Composition geometry`, the Page Expression Core above, and — once triggered — [`svg-effects.md`](./svg-effects.md) §6.1 and [`native-shape-authoring.md`](./native-shape-authoring.md) §2.1.
- **Default — stage each page with the style's composition geometry (may override when another page-fit move is stronger)**: an SVG page is a canvas, not a DOM. A preset uses its style's §1 `Composition geometry`; a `custom` executes `visual_style_behavior` first and takes §1 geometry only from the exact `visual_style_references` the behavior assigns a shape or composition job; an unreferenced custom follows its behavior alone. Every listed move is generative vocabulary; when the move reaches beyond basic primitives, [`native-shape-authoring.md`](./native-shape-authoring.md) §2.1's exact-fit gate applies (loading it then).
- **Default — consider the planned motif (may override when another coherent expression serves the deck better)**: when §III `Theme` recommends a cross-page motif, decide whether it earns a continuity job; if adopted, vary scale, crop, density, position, and content interaction by page role. An explicit user/template motif binds.
- **Ordinary carriers stay ordinary**: cards, icon-and-label rows, color swatches, soft shadows, and gradient fields are everyday carriers — use them whenever content groups, compares, enumerates, or names a color, material, or sample, with one shared treatment for peers; reach for a device by page job and let the locked style set its treatment. When the subject is a color or material, draw it: a swatch is content, its value comes from the source, and it needs no lock row.
- **Reference — semantic geometry over preset stacks**: for ascending, converging, breaking-through, or stacking relationships, compose faithful primitives and exact presets as one geometry system; a Boolean only when the contour must merge, open, or fragment; one page-specific path only when neither works.
- **Inherited containers**: keep meaningful template frames and restyle radius, fill, stroke, and depth from the Design Spec and lock; Chart/Table reference adaptation belongs to [`executor-visualization.md`](./executor-visualization.md), and preview effects never override project styling.
- **Fact provenance**: resolve each §IX `Fact ID` from `sources/*.facts.json` and keep the value unchanged; render a compact source footnote (name + short URL/domain) when space permits and state attribution naturally in enabled notes. For `Data class: scenario`, place a visible localized `Scenario data` / `情景数据` label beside the KPI/chart and say in notes that it is illustrative. Never attach a fact ID to scenario data or let an unlabeled invented KPI look factual. An organizing framework, grouping, or label the source does not state is the deck's reading — say so on the page (e.g. `整理` / `our reading`) or in enabled notes, never presented as the source's structure.

**Technical contract (the exporter's needs; the complete SVG boundary is [`shared-standards-core.md`](./shared-standards-core.md))**:

- **Element grouping (Mandatory)**: wrap each logical Slide-local body unit in a descriptive, page-unique top-level `<g id>` with root-coordinate `data-pptx-bounds="x y width height"`; a helper-authored preset atom stays top-level with `data-pptx-frame` and no bounds; nested groups need none. Give a root background image or full-canvas scrim/decoration rectangle a stable `id` plus `data-pptx-role="background"` / `"decoration"` instead of a wrapper. Thresholds, exemptions, and the Morph staging marker: [`shared-standards-core.md`](./shared-standards-core.md) §4.3.
- **Reference — nested edit groups**: a top-level group may contain descriptive nested `<g>` groups for meaningful subunits; they need no bounds and create no animation step, with no default depth or quota.
- **Default — bounds are the module zone, not a glyph box (may skip when no text is estimable)**: make each zone as generous as the canvas and siblings allow without overlap. An untransformed line spans `y − 0.85 × font_size` to `y + 0.35 × font_size`. **Width is calibrated once, then estimated**: before P01 the route runs `python3 ${SKILL_DIR}/scripts/text_measure.py calibrate` (Default from the lock with `--outline`, Quick with `--role` arguments) and keeps its per-role table — CJK and Latin ≈ chars per 100 px, plus each role's longest planned line — in context; every later page sizes its zones from that arithmetic (characters ÷ the role's chars-per-100-px × 100; the estimator already carries the wrapping headroom) — write the sentence first, then fit the zone to it; no per-page measurement, no line-by-line tool calls, and never trim wording to satisfy an estimate. Reach for `calibrate --role` or `measure|wrap|box` again only for a role or size that was never calibrated. When text does not fit, first expand a zone with unused space, then reflow or switch texture (prose → points) before dropping a qualifier; larger bounds never repair off-canvas text.
- **Spec adherence**: binding color, canvas, typography, identity, resource, and template anchors hold; layout and other References apply under §2.1 without becoming locks.
- **Template structure**: inherit the native framework only for `template_reuse_scope: mirror|layout`; `style` uses the flat route.
- **Main-agent ownership**: SVG generation runs in the main agent, never a sub-agent — pages share upstream context for cross-page continuity.

**Checkpoints**:

- **Mandatory — per-page module line**: before drawing each page, write one line `P<NN> modules: core[, structure][, native-shape][, effects][, image][, native-data][, chart | table | formula | link | web-image]` naming the triggered modules the page uses; a module the pre-P01 sweep did not read is read completely before that page's first SVG line, and a page whose carrier mix uses a module's capability without naming it is a defect the carrier receipt exposes.
- **Phased generation** (recommended):
  1. **Visual Construction Phase**: generate all pages sequentially, applying every triggered branch while drawing. **MUST embed one object-scoped plot-area marker** per §IX-named or Quick-promoted value-driven chart object ([`executor-chart.md`](./executor-chart.md) §2); calibration follows in [`verify-charts`](../workflows/stages/verify-charts.md). Write every `<object-key>=yes` native marker plus JSON metadata atomically ([`native-data-interface.md`](./native-data-interface.md) §2) and stamp its baseline before the page's gate — `python3 ${SKILL_DIR}/scripts/stamp_native_fallbacks.py <project_path>/svg_output/<page>.svg --write`, rerun after any visible edit inside the marker group. **Reach for native presets** per §3.0 as you draw, decided by the object's intent, never by scanning finished paths; several presets for one page go through one `preset_shape_svg.py render-batch --input -` round (gradient/pattern paint stays ordinary SVG; a justified §6.4 shadow/glow stays on the helper-authored shape).
  2. **Quality gates**: owned by the route — [`generate-pptx.md`](../workflows/generate-pptx.md) Step 6 (first-page, final, carrier receipt) or [`quick-generate.md`](../workflows/profiles/quick-generate.md) §4 (one lockless final check). Run each checker unfiltered, review the complete issue set, fix every error plus selected warnings in one consolidated pass, verify once; never check between individual fixes, never `cat` a passing report, never defer errors past `finalize_svg.py` (it rewrites SVG and masks violations). Every `warning` is advisory.
  3. **Logic Construction Phase (conditional)**: after the gates pass, generate speaker notes for narrative continuity only when the effective Speaker Notes outcome is enabled.

### 3.0 Native Shape Selection

**Hard rule — contour before encoding**: choose the page-fit contour from the full native vocabulary — [`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md), read completely before the first page — before its authoring form; when the roster sweep or a page reaches beyond rectangle, rounded rectangle, circle, ellipse, and line, read [`native-shape-authoring.md`](./native-shape-authoring.md) completely before choosing. Rectangle, rounded rectangle, circle, and ellipse are preset contours even in short SVG syntax; easier syntax never selects a contour. Block arrows, chevrons, banners, callouts, flowchart nodes, stars, and other Office symbols come from `preset_shape_svg.py`, never plain paths or fake rectangles. No Design Spec selection, scorer, or inventory gates this choice.

**Mandatory — independent per-page geometry move**: after the Structure result and any topology, decide the page's geometry before writing coordinates; when it reaches beyond basic primitives, apply [`native-shape-authoring.md`](./native-shape-authoring.md) §2.1 (loading it then); it owns exact-fit comparison, composition lenses, relationship and carrier fit, contour-family choice, the reader effect of a generic or undrawn result, the running geometry signature, and the materialization boundary for both Structure results. Keep the decision in active context; never change the Structure result.

Materialize through [`native-shape-authoring.md`](./native-shape-authoring.md) §1's table: an ordinary primitive when the exporter maps it to the same contour, otherwise the helper fragment; `<line>` for a straight relationship and a `bentConnector*` / `curvedConnector*` preset for a stock bend or curve (both export unconnected); independent siblings for a page-level system; `shape_boolean_svg.py` only when one contour must merge, cut, or fragment; ordinary path/polygon only for geometry none of those express. A directional solid object is a `shape` preset such as `rightArrow` or `chevron`; `actionButton*` presets are geometry only.

**Hard rule — freeform is the last tier**: before hand-authoring a stock-looking `<path>` / `<polygon>`, complete contour selection, simplest exact materialization, independent composition, and the Boolean gate; avoiding a helper or drawing faster is not an exception, while data-defined geometry and a genuinely locked organic/hand-drawn contour qualify by semantics. This applies only while drawing a new object; export never scans or upgrades ordinary SVG.

**Hard rule — helper-written metadata and scope**: `data-pptx-authoring`, `data-pptx-prst`, `data-pptx-frame`, adjustment metadata, and registry paths are written only by the preset helper (hand-written values fail the checker); rerun it when geometry or paint changes and never edit a direct path. Both helpers print only their stdout fragment(s): read and insert each through the normal page edit, never redirect, loop, or batch output into `svg_output/`.

### SVG File Naming Convention

`<index>_<page_name>.svg` with one roster-wide zero-padded width (`01_cover.svg` … `12_end.svg`, or `001_cover.svg` … `120_end.svg`), matching the deck language and page title.

---

## 4. Icon Usage

Strategist chooses at most one primary bundled stylistic library and may select `simple-icons` alone or alongside it for real brand marks; Executor draws from the complete prepared project-local pool ([`../templates/icons/README.md`](../templates/icons/README.md)). Any SVG under `<project_path>/icons/<lib>/` is prepared material; authoring, preview, finalization, and export resolve only complete case-sensitive `library/name` references there (`tabler-outline/award`, never `Award`; custom files keep their exact case), with no global or template-source fallback.

```xml
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>
<!-- stroke-style libraries (tabler-outline) may add stroke-width 1.5 | 2 | 3 -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="2"/>
```

**Hard rule — color and stroke**: always `fill="#HEX"` on `<use data-icon>`, never `stroke` or `fill="none"`, even for stroke libraries. `stroke-width` (`tabler-outline` only) is `1.5`, `2`, or `3`; a declared `spec_lock.md icons.stroke_width` applies deck-wide, and new authoring declares it, and a legacy stroke-library lock without it uses `2` with one warning. `finalize_svg.py` embeds placeholders automatically.

**Missing project-local icon** (`test -f "<project_path>/icons/<lib>/<name>.svg"`) → return to Strategist's preparation / `icon_sync.py` gate; Executor never searches the global library, picks an alternative, or copies a candidate. Executor may combine project-local icons freely across namespaces and styles but may not acquire a new one or treat a globally resolvable file as prepared.

---

## 5. Font Usage

Default reads typography from `spec_lock.md` (Quick: its transient §2 anchor): `<role>_family` → `title_family` / `body_family` → legacy `font_family`; sparse accents follow §2.1. Under [`native-formula.md`](./native-formula.md), blocks use marker style and inline math inherits size and solid fill, exporting in Cambria Math with the project text language.

**Default — locked-stack realization (may vary treatment)**: express the Design Spec Character Reference through scale, weight, spacing, color, and composition while keeping the locked family; put the common stack on root `<svg>`, omit matching descendants, and override at the nearest clear `<g>`, `<text>`, or `<tspan>`.

**Hard rule — target faces**: every `font-family` stack resolves to target-installed/approved Latin and EA faces. PPTX writes one face per script: the first named Latin face fills `latin`, the first named CJK face fills `ea` (and `latin` when no Latin face is named), and a generic family fills `latin` only when it precedes every named face. Fonts are not embedded; missing-face substitution is viewer-selected. **Missing `typography.font_family`** → stop and return to Generate Step 4 / [`strategist.md`](strategist.md) §6.2; never infer a stack from `design_spec.md`.

---

## 6. Completion and Export (Default only)

After every page passes the final quality check, load [`executor-notes.md`](./executor-notes.md) only when the effective Speaker Notes outcome in `design_spec.md §I` is enabled, then proceed to the route's conditional motion handling and [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7, which owns post-processing and export.
