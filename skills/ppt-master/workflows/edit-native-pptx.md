---
description: Edit Native PPTX route — import a finished PowerPoint deck into a source-preserving SVG workspace, reference unchanged pages, edit or recompose selected pages, add notes/narration/motion, and export a new PPTX
---

# Edit Native PPTX Route

> Run when the user brings an existing `.pptx` whose design must survive — a template to fill, a deck to partially rewrite or restructure, or a finished deck that only needs notes, narration, timings, or transitions. Never regenerates from scratch and never runs the Generate SVG pipeline.

The source deck becomes a `pptx_to_svg.py --roundtrip` workspace: every slide is a compact editable SVG plus immutable native backing. Untouched pages are **referenced** and restored byte-for-byte; edited pages rebuild only what changed while unchanged objects restore natively; notes, narration, and motion are overlays that never rewrite visible content.

| User wants | Route |
|---|---|
| Fill a raw PPTX template with new content, keep its design; add notes / narration / auto-advance / transitions; rewrite some pages and keep the rest; drop, reorder, or repeat pages without redesign | This route |
| Regenerate every page with a new visual design (1:1) | Generate PPTX, [`beautify-pptx`](./profiles/beautify-pptx.md) |
| Split / merge / re-outline into a new deck | Generate PPTX, PPTX as source material |
| Create a reusable brand / style / layout / deck asset | [`create-template`](./create-template.md) |

**Hard rule — no Generate pipeline**: never run `pptx_template_import.py`, `project_manager.py init`, or `finalize_svg.py`, and never create `svg_output/`; the round-trip workspace is the project and `svg_to_pptx.py --roundtrip` is the only exporter that restores source slides.

---

## 1. When to Run

Raw PPTX called a template + new material or topic; existing deck + selective reuse ("only keep the pages that fit, in this order"), copy replacement, page-level rewrite ("redo page 5 and 7"), page combination ("merge the two market pages"), or a few new pages in the same style; finished deck + delivery add-ons with visible slides stable. Never ask a route-choice question for these shapes; ask one discriminator only when preserving (this route) and redesigning (Generate) are genuinely ambiguous.

---

## 2. Inputs

🚧 **GATE**: source PPTX (required — the native design authority); new material only when content changes (text, Markdown, documents, or URLs converted with `source_to_md.py`; a bare topic without facts is not enough — ask for material or gather it from user-approved URLs); optional delivery intent (audience, page count, must-keep / must-drop pages, notes, narration, transitions, auto-advance).

**Hard rule — facts**: every substantive claim in a page or note comes from the user material; the §4.3 content mapping names the source for each page and a page without one is dropped; template placeholder wording never becomes output content.

---

## 3. Import the Round-trip Workspace

```bash
python3 skills/ppt-master/scripts/pptx_to_svg.py "<source.pptx>" -o "projects/<slug>_<YYYYMMDD>" --inheritance-mode both --roundtrip
```

| Path | Content | Reading rule |
|---|---|---|
| `authoring-svg-flat/slide_NN.svg` | One compact editable SVG per source slide, in order | Open only pages you will edit or must judge for reuse |
| `authoring-svg-flat/authoring_summary.json` | Roster plus per-page canvas, text, image, vector, placeholder, source-ref, and proxy counts | Read first; plan from it before opening any SVG |
| `images/`, `icons/imported/`, `audio/`, `video/`, `sounds/` | Source media and imported vectors | Keep names; changed bytes rebuild every output page whose source graph references that part, and a format mismatch fails export |
| `notes/slide_NN.md` | Source speaker notes | Edit, delete, or add per output page (§6) |
| `native-payloads/`, `analysis/` | Immutable native backing and tool-owned contracts | Do not read, edit, or quote |
| `sources/source.pptx` | Exact source package | Read only through `ppt_to_md.py "<workspace>/sources/source.pptx" -o "<workspace>/validation/source_readback.md"` when you need page text without opening every SVG |
| `validation/`, `exports/` | Diagnostics and published decks | Tool-written |

**Hard rule — source proxies are atomic**: an `<image data-pptx-source-proxy="native-restore">` stands for an unsupported native object (SmartArt, complex effects, media frames). Leave it to restore the original; a Slide-local proxy may be deleted, an inherited Master/Layout proxy stays; editing a proxy or its preview asset fails export.

---

## 4. Plan the Output Deck

**Defaults (may override when the user fixes the mapping, asks to preserve order, or asks for new pages)**: treat the roster as a slide library, not an outline — a source page's layout already encodes a rhetorical shape (hero statement, lead-then-detail, comparison, progression, metric row, dense explanation), so match each target message to a page whose structure expresses the same logic and drop content or the page rather than force a fit; the target story controls order, so source slides may move, be omitted, or be reused; the source deck is the skeleton — most output pages keep a source structure, sub-content recombines freely, and new pages appear where the story needs them.

### 4.1 Page plan

Write `page_plan.json` at the workspace root only when the output differs from the source roster (subset, reorder, repeat, or a copied page); without it export is the identity round trip.

```json
{
  "schema": "ppt-master.roundtrip-page-plan.v1",
  "pages": [
    {"source_slide": 1},
    {"source_slide": 4, "svg": "chapter_market.svg"},
    {"source_slide": 7},
    {"source_slide": 7, "svg": "kpi_second_half.svg"}
  ]
}
```

`pages` is the complete non-empty output order; `source_slide` is the one-based source index whose native slide backs the page; `svg` is the authoring filename inside `authoring-svg-flat/`, omitted to use that page's `slide_NN.svg` — to reuse a source page twice, copy its SVG under a new name and list the copy, since every output page needs a distinct file and every extra file must appear in the plan. Only these fields are accepted. **Forbidden — plans the exporter refuses**: a same-deck slide jump whose destination is omitted or repeated; unknown, duplicated, or cross-owned `svg` filenames; `source_slide` out of range. Omitting a slide drops the audio, video, or undecodable payloads only it owns (export prints a note). With a plan, presentation-level sections and custom shows are dropped and slide ids renumbered.

**Combining pages**: one output page has exactly one skeleton (`source_slide`). To merge, pick the page whose layout carries the result, then bring objects from other pages only through the adopt command — never pasted raw SVG, because source refs are page-local. The adopted object materializes its effective inherited presentation attributes and ancestor transforms, loses native identity, and makes the page `rebuilt`; a source proxy cannot leave its page, so a merge that needs one keeps that page as the skeleton. The object lands at the end of the target page for normal editing.

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "projects/<slug>_<YYYYMMDD>/authoring-svg-flat" --adopt-object slide_05.svg:<element-id> --into chapter_market.svg
```

**New pages** need a skeleton too: copy the closest source page under a new name, list it with that page's `source_slide`, delete its Slide-local content, and author on the empty canvas (inherited proxies stay); the page is `rebuilt`.

### 4.2 Enhancement modules

| Module | Default | Carrier |
|---|---|---|
| Speaker notes | Source notes travel with every page; add or rewrite only where planned | `notes/<svg-stem>.md` |
| Narration audio | Off unless requested; implies notes on every output page | [`generate-audio`](./stages/generate-audio.md) → `audio/<stem>.*` |
| Auto-advance from narration | On when narration is requested | `svg_to_pptx.py --use-narration-timings` |
| Page transitions | Preserve source; replace only on request | `svg_to_pptx.py -t <effect>` or per-slide rows in `animations.json` |
| Object animations | Preserve source; author only on explicit request | `animations.json`, [`animations.md`](../references/animations.md) |
| Native chart / table data | Source data unless the plan edits it | Inline JSON authority; export needs `--native-charts-and-tables` (§7) |

### 4.3 Confirmation

⛔ **BLOCKING**: present one plan and wait for explicit confirmation before editing any SVG, writing notes, generating audio, or exporting: the output roster (output page → source slide → referenced / edited / new copy, with a one-line reason per edited or dropped page), the content mapping (which material goes where, what is dropped for lack of a fitting layout), each enhancement module on/off with its effect and duration, and any §4.1 fail-closed case the plan must avoid. Chat confirmation suffices; write `page_plan.json` afterwards.

---

## 5. Edit Pages

Load [`shared-standards-core.md`](../references/shared-standards-core.md) before the first edit; [`svg-effects.md`](../references/svg-effects.md) only when authoring new visual elements; [`native-data-interface.md`](../references/native-data-interface.md) only when changing native chart or table data.

**Hard rule — edit only planned pages**: a referenced page is never opened for writing; export proves it by listing it under `passthrough` / `cloned_passthrough` or `patched`, never `rebuilt`. **Hard rule — edit in place, keep identity**: change text, paint, position, or content inside the existing tree and keep every `data-pptx-*` attribute on objects you did not intend to change — surviving attributes restore natively, rewritten objects convert from your SVG. Never paste a page from `svg_output/` conventions or another deck over a round-trip page.

| Edit | Rule |
|---|---|
| Text replacement | Fit the slot's visual capacity from its geometry and font size, not the old placeholder length; resolve overflow by rewriting shorter → splitting across another selected page → choosing a larger source layout; shrinking type is last and never deck-wide |
| Cover / chapter pages | Replace title, subtitle, author, section label only |
| Dense content pages | Compress to the slot count the page has; move overflow to another selected page |
| Native tables / charts | Imported objects carry `data-pptx-native-authority="json"`: edit cell text or categories/series values in the inline JSON, keep structure and formatting from the source, and export with `--native-charts-and-tables` — without it the stale preview ships |
| Images | Point the existing `<image>` at a new file under `images/`; keep the frame |
| New elements | Canonical compact SVG per shared standards; icons via `icon_sync.py "<workspace>" <lib/name>`; AI images via `image_gen.py --manifest` when wanted |
| Objects from another page | `--adopt-object` only (§4.1); proxies cannot move |
| Source proxies | Leave or delete; never edit (§3) |

**Mandatory after editing** — refresh the summary, then run the capacity gate:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "projects/<slug>_<YYYYMMDD>/authoring-svg-flat" --refresh-summary
python3 skills/ppt-master/scripts/svg_quality_checker.py "projects/<slug>_<YYYYMMDD>" --roundtrip
```

🚧 **GATE**: `--roundtrip` estimates edited text against its frame and canvas; errors block export until the text is rewritten, split, or moved to a larger layout, warnings are fixed or accepted with a stated reason. The exporter remains the final gate and fails closed on a page it cannot restore or convert.

---

## 6. Notes, Narration, and Motion

Skip when no §4.2 module beyond preserving source notes is enabled.

**Notes** are keyed by output SVG stem: `notes/<stem>.md` for a canonical page replaces source notes (delete the file to remove them); for a copied page it applies to that output page only, and without a file the copy inherits the source notes. **Hard rule — spoken prose only**: `svg_to_pptx.py` embeds and `notes_to_audio.py` reads each note verbatim, so a heading, bullet, `[tag]`, or duration line is spoken and shown. Write 2–5 natural sentences per content page, one or two for cover / chapter / ending, transitions as prose, one language per deck, sourced from the page's SVG text or the §3 read-back plus user material — a note never adds a claim the page or material does not carry.

**Narration audio**: run [`generate-audio`](./stages/generate-audio.md) Steps 1–4 with the workspace path after notes are complete; the source deck's own media in `audio/` is left alone; `notes_to_audio.py` resolves the roster from `page_plan.json` (copies inherit) and refuses an incomplete roster. Stop after audio; §7 integrates it.

**Motion**: load [`animations.md`](../references/animations.md) when transitions or object animations are requested; `animations.json` rows are keyed by output stem and a copied page inherits its source row unless it has its own. **Hard rule — rebuilt animation targets**: rebuilding an object a source animation targets leaves that animation without a target and export stops with `Edited slide removed source animation target(s)`; give the page its own row — `"<stem>": {"animation": {"effect": "none"}}` drops the source build, or author the page's motion — then export again.

---

## 7. Export and Validate

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py "projects/<slug>_<YYYYMMDD>" --roundtrip
```

Add `-t <effect> [--transition-duration <s>]` to replace transitions deck-wide; `--recorded-narration audio --use-narration-timings` for narration with auto-advance (round-trip export reads the workspace `animations.json` by default); `--animation-config animations.json` for per-slide motion; `-a <preset>` (default `none`) for object animation policy; `--no-notes` to strip notes; `--native-charts-and-tables` when chart/table data was edited. Export writes into `exports/`, prints the exact output path (a `_narrated` or `_native_charts_tables` suffix may apply — use the printed path afterwards), and one receipt:

```text
Round-trip export summary: output_pages=N passthrough=P cloned_passthrough=C patched=M rebuilt=R
```

`passthrough` = identity page with original XML (referenced, no plan, no overlay); `cloned_passthrough` = planned referenced page on a cloned part; `patched` = source shape XML kept while order, notes, transitions, animation, or narration timing changed; `rebuilt` = visible authoring or a referenced materialized resource changed — exactly the pages marked edited in §4.3 plus pages referencing a changed resource, and a delivery-only job must show `rebuilt=0`.

**Validation**: `pptx_delivery_check.py "<printed_output.pptx>" > ".../validation/<output_stem>.delivery.json"` (no structural errors; review advisories) and `ppt_to_md.py "<printed_output.pptx>" -o ".../validation/readback.md"` — slide count equals the plan length (or source count), key titles and replaced text present, notes count matches, receipt buckets match the confirmed roster.

```markdown
## ✅ Edit Native PPTX Complete
- [x] Round-trip workspace imported at `projects/<slug>_<YYYYMMDD>/`; plan confirmed; `page_plan.json` written when the roster differs
- [x] Only planned pages edited; `authoring_summary.json` refreshed; `svg_quality_checker.py --roundtrip` reports no errors
- [x] Notes / audio / motion prepared as confirmed; `--roundtrip` receipt matches the confirmed roster
- [x] Delivery JSON and read-back written under `validation/`; final deck at the printed `exports/` path
```

---

## 8. Current Boundary

Supported: referencing unchanged pages byte-for-byte with select / reorder / repeat / omit; editing text, paint, images, native table cells, and native chart data on selected pages (chart/table edits export only with `--native-charts-and-tables`); authoring new elements as canonical compact SVG; preserving SmartArt, complex effects, and embedded media as atomic proxies; notes, narration, auto-advance, transitions, and object animations as overlays keyed by output page. Not supported: deleting inherited source notes on a copied page (give the copy its own file); editing a source proxy; changing slide size; adding Master/Layout structure (use Create Template → Generate).
