---
description: Edit Native PPTX route — import a finished PowerPoint deck into a source-preserving SVG workspace, reference unchanged pages, edit or recompose selected pages, add notes/narration/motion, and export a new PPTX
---

# Edit Native PPTX Route

> Run when the user brings an existing `.pptx` whose design must survive — as a template to fill with new content, as a deck to partially rewrite or restructure, or as a finished deck that only needs notes, narration, timings, or transitions. This route never regenerates the deck from scratch and never runs the Generate SVG pipeline.

The source deck becomes a `pptx_to_svg.py --roundtrip` workspace. Every source slide is available as a compact editable SVG plus immutable native backing. Pages the plan leaves untouched are **referenced**: export restores their original slide XML byte-for-byte. Pages the plan edits are rebuilt only where they changed; every unchanged object on them restores its native form. Notes, narration audio, and motion are overlays on the preserved slide and never rewrite visible content.

**Boundary against other routes**:

| User wants | Route |
|---|---|
| Fill a raw PPTX template with new content, keep its design | This route |
| Keep a finished PPTX, add speaker notes / narration / auto-advance / transitions | This route |
| Rewrite some pages of a finished PPTX, keep the rest exactly | This route |
| Drop, reorder, or repeat pages of an existing PPTX without redesign | This route |
| Regenerate every page with a new visual design (beautify, 1:1) | Generate PPTX, [`beautify-pptx`](./profiles/beautify-pptx.md) |
| Split / merge / re-outline an existing PPTX into a new deck | Generate PPTX, PPTX as source material |
| Create a reusable brand / style / layout / deck asset from the PPTX | [`create-template`](./create-template.md) |

**Hard rule — no Generate pipeline**: Do not run `pptx_template_import.py`, `project_manager.py init`, `finalize_svg.py`, or create `svg_output/` for this route. The round-trip workspace is the project; `svg_to_pptx.py --roundtrip` is the only exporter that restores source slides.

---

## 1. When to Run

| Pattern | Example |
|---|---|
| Raw PPTX called a template + new material or topic | "Use this PowerPoint template to make a deck about X" |
| Existing deck + selective reuse | "Only keep the pages that fit, in this order" |
| Existing deck + copy replacement | "Keep the design, swap in this text" |
| Existing deck + page-level rewrite | "Redo page 5 and 7, leave everything else" |
| Existing deck + page combination | "Merge the two market pages into one, drop the old chart, add the new KPI" |
| Existing deck as skeleton + a few new pages | "Keep the deck, add a summary page and a Q3 page in the same style" |
| Finished deck + delivery add-ons, visible slides stable | "Add narration and auto-play", "add fade transitions", "write speaker notes" |

**Deterministic routing**: Do not ask a route-choice question for these shapes. Ask one discriminator only when the request is ambiguous between preserving pages (this route) and redesigning them (Generate).

---

## 2. Inputs

🚧 **GATE**: The user has provided:

| Input | Required | Notes |
|---|---:|---|
| Source PPTX | Yes | Finished deck or template; the native design authority |
| New material | Only when content changes | Text, Markdown, documents, or URLs converted with `source_to_md.py`. A bare topic without facts is not enough: ask for material, or gather it from user-approved URLs before planning |
| Delivery intent | Optional | Audience, page count, must-keep / must-drop pages, notes, narration, transitions, auto-advance |

**Hard rule — facts**: Every substantive claim written into a page or a note comes from the user material; the §4.3 content mapping names the source for each page, and a page without one is dropped. Placeholder wording in the template is never carried into the output as content.

---

## 3. Import the Round-trip Workspace

Create the workspace directly under `projects/`; it is the project.

```bash
python3 skills/ppt-master/scripts/pptx_to_svg.py "<source.pptx>" \
  -o "projects/<slug>_<YYYYMMDD>" --inheritance-mode both --roundtrip
```

| Path | Content | Reading rule |
|---|---|---|
| `authoring-svg-flat/slide_NN.svg` | One compact editable SVG per source slide, in source order | Open only the pages you will edit or need to judge for reuse |
| `authoring-svg-flat/authoring_summary.json` | Roster plus per-page canvas, text, image, vector, placeholder, source-ref, and source-proxy counts | Read first; plan from it before opening any SVG |
| `images/`, `icons/imported/`, `audio/`, `video/`, `sounds/` | Source media and imported decorative vectors | Keep names. Export hashes materialized files; changed bytes rebuild every output page whose source Slide/Layout/Master/notes graph references that package part, and a format mismatch fails export |
| `notes/slide_NN.md` | Source speaker notes when present | Edit, delete, or add per output page (§6) |
| `native-payloads/`, `analysis/` | Immutable native backing and tool-owned contracts | Tool-owned; opening them costs context and changes nothing — do not read, edit, or quote |
| `sources/source.pptx` | Exact source package | Read only through `ppt_to_md.py "<workspace>/sources/source.pptx" -o "<workspace>/validation/source_readback.md"` when you need page text without opening every SVG (notes on unchanged pages, content mapping) |
| `validation/`, `exports/` | Diagnostics and published decks | Tool-written |

**Hard rule — source proxies are atomic**: An `<image data-pptx-source-proxy="native-restore">` element stands for an unsupported native object (SmartArt, complex effects, media frames). Leave it unchanged to restore the original object; a Slide-local proxy may be deleted; an inherited Master/Layout proxy stays. Editing a proxy or its preview asset fails export.

---

## 4. Plan the Output Deck

**Default — layout-first selection (may override when the user fixes the page mapping)**: Treat the roster as a slide library, not an outline. A source page's layout already encodes a rhetorical shape — hero statement, lead-then-detail, comparison, stepwise progression, metric row, dense explanation. Match each target message to a page whose structure expresses that same logic; drop the content or the page rather than force a fit. Use fewer pages than the source when that reads better; repeat one good layout for several messages when they share its pattern.

**Default — source order is not the outline (may override when the user asks to preserve it)**: The target story controls output order. Source slides may move, be omitted, or be reused several times.

**Default — skeleton first (may override when the user asks for new pages)**: The source deck is the reference material and the skeleton of the output. Most output pages keep a source page's structure; sub-content may be recombined freely across pages, and new pages are added where the story needs them rather than as a rule.

### 4.1 Page plan

Write `page_plan.json` at the workspace root only when the output differs from the source roster (subset, reorder, repeat, or a copied page). Without the file, export is the identity round trip and every page is referenced or edited in place.

```json
{
  "schema": "ppt-master.roundtrip-page-plan.v1",
  "pages": [
    {"source_slide": 1},
    {"source_slide": 4, "svg": "chapter_market.svg"},
    {"source_slide": 7},
    {"source_slide": 7, "svg": "kpi_second_half.svg"},
    {"source_slide": 12}
  ]
}
```

| Field | Rule |
|---|---|
| `pages` | Complete output order; non-empty |
| `source_slide` | One-based source index of the page whose native slide backs this output page |
| `svg` | Authoring filename inside `authoring-svg-flat/`; omit to use that source page's `slide_NN.svg`. To reuse one source page twice, copy its SVG to a new name (`cp slide_07.svg kpi_second_half.svg`) and list the copy — every output page needs a distinct file, and every extra file must appear in the plan |

Only `schema` and `pages` at the root and `source_slide` / `svg` per page are accepted; the exporter rejects any other field.

**Forbidden — plans the exporter refuses** (fail-closed, fix the plan instead of forcing):
- A same-deck slide jump whose destination is omitted or repeated (include the target exactly once, or remove the link from the page)
- Unknown, duplicated, or cross-owned `svg` filenames; `source_slide` out of range

Omitting a source slide deliberately drops the audio, video, or undecodable payloads only that slide owns; export prints a note listing them.

**Combining pages**: One output page always has exactly one skeleton — its `source_slide`. To merge several source pages, pick the page whose layout carries the result as the skeleton, then copy the needed elements from the other pages' SVGs into it and delete what the merged page no longer needs. Bring an object across pages only through the adopt command below — never by pasting raw SVG, because source refs are page-local and a pasted object would be mistaken for one of the skeleton's own. The adopted object keeps its visual form by materializing effective inherited presentation attributes (including `font-family`, `fill`, `opacity`, and CSS-resolved values) and composing ancestor transforms onto the copy. It loses its native identity and is rebuilt from SVG, so the combined page counts as `rebuilt`. A source proxy (§3) cannot leave its own page; a merge that needs one keeps that page as the skeleton instead.

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py \
  "projects/<slug>_<YYYYMMDD>/authoring-svg-flat" \
  --adopt-object slide_05.svg:<element-id> --into chapter_market.svg
```

The object lands at the end of the target page; then edit its position and content like any authored element.

**New pages**: A brand-new page also needs a skeleton so it inherits the deck's Master/Layout (background, logo, page number). Copy the closest source page under a new name, list it in the plan with that page's `source_slide`, delete its Slide-local content, and author the new content on the empty canvas; inherited proxies stay. The page counts as `rebuilt`.

> Note: with a plan present, presentation-level sections and custom shows are dropped and slide ids are renumbered; visible slides are unaffected.

### 4.2 Enhancement modules

| Module | Default | Carrier |
|---|---|---|
| Speaker notes | Source notes travel with every page; add or rewrite only where the plan says | `notes/<svg-stem>.md` |
| Narration audio | Off unless requested; implies notes on every output page | [`generate-audio`](./stages/generate-audio.md) → `audio/<stem>.*` |
| Auto-advance from narration | On when narration is requested | `svg_to_pptx.py --use-narration-timings` |
| Page transitions | Preserve source; replace only on request | `svg_to_pptx.py -t <effect>` or per-slide rows in `animations.json` |
| Object animations | Preserve source; author only on explicit request | `animations.json`, see [`animations.md`](../references/animations.md) |
| Native chart / table data | Source data unless the plan edits it | Inline JSON authority on the page; export needs `--native-charts-and-tables` (§7) |

### 4.3 Confirmation

⛔ **BLOCKING**: Present one plan and wait for explicit confirmation before editing any SVG, writing notes, generating audio, or exporting:

| Item | Show |
|---|---|
| Output roster | Ordered list: output page → source slide → referenced unchanged / edited / new copy, with a one-line reason for each edited or dropped page |
| Content mapping | Which material goes to which page; anything dropped for lack of a fitting layout |
| Enhancement modules | Each module on/off with its effect and duration where relevant |
| Known refusals | Any §4.1 fail-closed case the plan must avoid |

Chat confirmation is sufficient; write `page_plan.json` after confirmation.

---

## 5. Edit Pages

Load [`shared-standards-core.md`](../references/shared-standards-core.md) before the first edit. Load [`svg-effects.md`](../references/svg-effects.md) only when authoring new visual elements, and [`native-data-interface.md`](../references/native-data-interface.md) only when changing native chart or table data.

**Hard rule — edit only planned pages**: A page marked referenced is not opened for writing. Export proves it: a referenced page appears under `passthrough` / `cloned_passthrough` (no overlay) or `patched` (notes or motion overlay only) in the receipt (§7) — never under `rebuilt`.

**Hard rule — edit in place, keep identity**: Change text, paint, position, or content inside the existing page tree. Keep every `data-pptx-*` attribute on objects you did not intend to change; an object whose source attributes survive is restored natively, an object you rewrote is converted from your SVG. Do not paste a page from `svg_output/` conventions or another deck over a round-trip page.

| Edit | Rule |
|---|---|
| Text replacement | Fit the slot's visual capacity from its geometry and font size, not the old placeholder length. Resolve overflow in this order: rewrite shorter → split across another selected page → choose a larger source layout; shrinking type is last and never deck-wide. §5's capacity gate rejects text that leaves its frame |
| Cover / chapter pages | Replace title, subtitle, author, section label only |
| Dense content pages | Compress material to the slot count the page already has; move overflow to another selected page |
| Native tables | Imported tables carry `data-pptx-native-authority="json"`; edit cell text in that inline `ppt-master.semantic-table.v2` JSON and keep row/column structure unless the design calls for a different table. Export with `--native-charts-and-tables` (§7) — without it the stale preview ships |
| Native charts | Imported charts carry the same JSON authority; edit categories and series values there and leave chart type and formatting to the source. Same export flag |
| Images | Replace by pointing the existing `<image>` at a new file under `images/`; keep the frame |
| New elements | Author canonical compact SVG per shared standards; icons come from `icon_sync.py "<workspace>" <lib/name>`; AI images from `image_gen.py --manifest` when the user wants generated visuals |
| Objects from another page | Use `--adopt-object` (§4.1); it strips source identity, inlines cross-page vector assets, and keeps chart/table JSON authority. Never paste raw SVG across pages; proxies cannot move |
| Source proxies | Leave or delete; never edit (§3) |

**Mandatory after editing** — refresh the summary (page-plan copies are accepted), then run the capacity gate:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py \
  "projects/<slug>_<YYYYMMDD>/authoring-svg-flat" --refresh-summary
python3 skills/ppt-master/scripts/svg_quality_checker.py "projects/<slug>_<YYYYMMDD>" --roundtrip
```

🚧 **GATE**: The checker's `--roundtrip` mode estimates edited text against its frame and canvas. Errors block export until the text is rewritten, split, or moved to a larger layout; warnings are reviewed and either fixed or accepted with a stated reason. The exporter remains the final gate and fails closed on a page it cannot restore or convert.

---

## 6. Notes, Narration, and Motion

Skip this section when no module in §4.2 is enabled beyond preserving source notes.

**Notes** — keyed by output SVG stem:

| Case | Behavior |
|---|---|
| `notes/<stem>.md` exists for a canonical page | Replaces source notes; delete the file to remove source notes |
| `notes/<stem>.md` exists for a copied page | Notes for that output page only |
| No file for a copied page | Inherits the source page's notes |

**Hard rule — spoken prose only**: `svg_to_pptx.py` embeds each note verbatim and `notes_to_audio.py` reads it aloud verbatim, so a heading, bullet, `[tag]`, or duration line is spoken and shown. Write 2–5 natural sentences per content page, one or two for cover / chapter / ending, transitions as prose, one language per deck. Source the content from the page's SVG text or the §3 read-back plus the user material; a note never adds a claim the page or material does not carry.

**Narration audio**: Run [`generate-audio`](./stages/generate-audio.md) Steps 1–4 with the workspace path after notes are complete (`notes_to_audio.py "<workspace>" --provider <p> --voice <v> --rate <r>`); the source deck's own media in `audio/` (imported files not named after a page) is left alone. `notes_to_audio.py` resolves the roster from `page_plan.json` (copies inherit source notes) and refuses an incomplete roster, listing the missing stems. Audio lands at `audio/<stem>.*` per output page. Stop after audio generation; §7 integrates it.

**Motion**: Load [`animations.md`](../references/animations.md) when transitions or object animations are requested. `animations.json` rows are keyed by output SVG stem; a copied page inherits its source row unless it has its own.

**Hard rule — rebuilt animation targets**: Rebuilding an object that a source animation targets (for example a chart whose data you edited) leaves that animation without a target, and export stops with `Edited slide removed source animation target(s)`. Give that page its own row so its motion becomes explicit — `"<stem>": {"animation": {"effect": "none"}}` drops the source build, or author the page's animation in the row — then export again.

---

## 7. Export and Validate

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py "projects/<slug>_<YYYYMMDD>" --roundtrip
```

| Request | Add |
|---|---|
| Replace transitions deck-wide | `-t <effect> [--transition-duration <s>]` |
| Narration with auto-advance | `--recorded-narration audio --use-narration-timings` (round-trip export reads the workspace `animations.json` by default) |
| Per-slide motion | `--animation-config animations.json` |
| Object animation policy | `-a <preset>` (default `none`) |
| Strip all notes | `--no-notes` |
| Native chart / table data edited | `--native-charts-and-tables` |

Export writes into `exports/` and prints the exact output path (a `_narrated` or `_native_charts_tables` suffix may apply — use the printed path in every later command) plus one receipt:

```text
Round-trip export summary: output_pages=N passthrough=P cloned_passthrough=C patched=M rebuilt=R
```

| Bucket | Meaning | Assert |
|---|---|---|
| `passthrough` | Identity page, original XML and relationships | Referenced pages without a plan and without any notes/motion overlay |
| `cloned_passthrough` | Planned page, original XML on a cloned part | Referenced pages with a plan and without any overlay |
| `patched` | Source shape XML is kept while shape order, notes, transitions, animation, or narration timing may change | Pages with z-order-only edits or package overlays that do not rebuild a source shape |
| `rebuilt` | Visible authoring or a referenced materialized resource changed | Exactly the pages marked edited in §4.3 plus every output page that references a changed resource — a delivery-only job must show `rebuilt=0` |

**Validation**:

```bash
python3 skills/ppt-master/scripts/pptx_delivery_check.py "<printed_output.pptx>" \
  > "projects/<slug>_<YYYYMMDD>/validation/<output_stem>.delivery.json"
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py \
  "<printed_output.pptx>" -o "projects/<slug>_<YYYYMMDD>/validation/readback.md"
```

| Check | Expected |
|---|---|
| Delivery check | No structural errors; review advisories |
| Slide count | Equals plan length, or source count without a plan |
| Key titles and replaced text | Present in the read-back |
| Notes count | Matches planned notes |
| Receipt buckets | Match the confirmed roster |

```markdown
## ✅ Edit Native PPTX Complete

- [x] Round-trip workspace imported at `projects/<slug>_<YYYYMMDD>/`
- [x] Plan confirmed by the user; `page_plan.json` written when the roster differs from the source
- [x] Only planned pages edited; `authoring_summary.json` refreshed; `svg_quality_checker.py --roundtrip` reports no errors
- [x] Notes / audio / motion prepared as confirmed
- [x] `svg_to_pptx.py --roundtrip` receipt matches the confirmed roster
- [x] Delivery JSON and read-back written under `validation/`
- [x] Final deck at the exporter's printed `exports/` path
```

---

## 8. Current Boundary

| Capability | Status |
|---|---|
| Reference unchanged pages byte-for-byte; select / reorder / repeat / omit pages | Supported |
| Edit text, paint, images, native table cells, native chart data on selected pages | Supported; unchanged objects restore natively; chart/table data edits export only with `--native-charts-and-tables` |
| Author new elements on an edited page | Supported through canonical compact SVG |
| Preserve SmartArt, complex effects, embedded media | Supported as atomic source proxies; not editable |
| Notes, narration audio, auto-advance, transitions, object animations | Supported as overlays keyed by output page |
| Delete inherited source notes on a copied page | Not supported; give the copy its own `notes/<stem>.md` |
| Edit a source proxy, change slide size, add Master/Layout structure | Not supported; use Create Template → Generate for a new structure |
