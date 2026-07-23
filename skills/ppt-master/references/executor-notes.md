> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core.

# Executor Speaker-notes Branch

Conditional late-stage authority for generating the complete speaker-notes document.

**Trigger**: load only after all SVG pages pass the final quality check.

## 1. Complete Speaker-notes Document

Write the complete deck to `notes/total.md` in one batch for coherent transitions. Use `# <number>_<page_title>` per page and `---` between pages; only the heading is stripped before TTS.

**Pure spoken narration**: `notes_to_audio.py` reads the body verbatim. Write prose only; never add Markdown list/bullet markup, stage markers, key-point labels, duration lines, or other metadata.

**Length follows content**: size natural sentences to semantic burden. Two to five is typical, not a cap; anchor pages may use less and dense pages more. Honor `design_spec.md` style, detail, and source rules. Duration is pacing guidance only: never pad, repeat, compress, or omit meaning to hit it.

## 2. Final-SVG Grounding and Coverage

**Hard rule — the final SVG is the visible page authority**: read every finalized `svg_output/<slide>.svg` in slide order. Use the locked plan and approved sources for context; never write from the outline or core message alone.

Before drafting, internally inventory the visible title/subtitle and every information-bearing direct-root `<g id>`; structured placeholder content still counts. Coverage requires its unique claim, evidence, example, relationship, qualifier, or implication—not merely its label—to enter the narration.

- Text blocks, comparisons, and processes retain every independent fact or relationship; combine related short groups causally or comparatively.
- Charts, tables, and KPIs state the takeaway, decisive values or trend, comparison basis, implication, and material uncertainty—not every axis, row, or cell.
- Quotes retain the decisive clause, material attribution, and relevance. Explain semantic images or text-free diagrams only from the SVG plus locked plan/source; never infer facts from appearance.
- Speak a source or page-local footer only when attribution, uncertainty, or qualification changes the argument. Omit backgrounds, decoration, repeated chrome, page numbers, and fixed Master/Layout atoms.

Form one coherent argument in intended reading/reveal order: proposition → evidence or mechanism → implication or bridge. DOM order need not be speaking order. A sentence may cover related groups and a complex group may need several sentences, but no independent group may disappear to meet a sentence count. Keep the inventory internal: never vocalize IDs, positions, colors, icons, repetitive "this card shows" descriptions, or coverage markers.

## 3. Reading Mode and TTS

| `consumption_mode` | Notes emphasis |
|---|---|
| `text` | Interpret and connect a self-contained page; synthesize every independent SVG information group rather than omitting it. |
| `balanced` | Connect visible claim and evidence, explain the trade-off, and bridge forward. |
| `presentation` | Carry reasoning, context, and supporting detail intentionally omitted from the sparse page. |

Put transitions naturally in the opening sentence when useful; never label them. Keep one language. Spell out digits or symbols when literal TTS would sound wrong (for example, Chinese "百分之六十八" rather than "68%").

After `notes/total.md` is complete, return to Generate Step 7.1; the route authority owns splitting and its success criterion.
