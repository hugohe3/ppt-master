# Roadmap

[English](./roadmap.md) | [Chinese](./zh/roadmap.md)

---

> PPT Master is a solo-maintained open source project, driven by **priority rather than fixed timelines**. This roadmap aligns expectations: the direction of travel, what's in motion now, what may come when real demand shows, and what's intentionally out of scope. Priorities shift with user feedback and real usage signals — no committed delivery windows.

---

## Direction

The defining axis is **native depth**: author or preserve more of PowerPoint's own object model, behavior, and reusable structure, release after release — converging with PowerPoint itself. The [positioning charter](./project-positioning.md) states the full thesis; the [PowerPoint ↔ SVG Mapping Guide](./powerpoint-svg-mapping.md) records the current boundary honestly, feature by feature.

Today that axis is expressed through four explicit artifact routes: **Generate PPTX** authors newly designed slides through constrained SVG → DrawingML; **Create Template** produces reusable Brand / Style / Layout / Deck workspaces; **Fill Native PPTX** and **Enhance Native PPTX** preserve existing packages through scoped OOXML operations.

---

## Coverage map

A presentation is four layers: what is on the slide, how it is arranged, how it behaves, and how the document itself is structured. The tables below map each layer against what PPT Master does today.

**Read this as a map, not a backlog.** *Bounded by design* and *Not on the path* are settled end states, not unfinished cells — a blank there is a decision, not a debt. Only *Signal-driven* rows are open, and their reasoning lives in [Future directions](#future-directions--signal-driven) rather than being repeated here.

| Status | Meaning |
|---|---|
| **Systematized** | Has its own authoring contract and checker coverage; actively refined |
| **Covered** | Works today without a dedicated specification system |
| **Bounded by design** | Deliberately stops where it stops; the reason is recorded |
| **Signal-driven** | Worth doing when real demand shows; not a commitment |
| **Not on the path** | Evaluated and declined — see [Non-goals](#non-goals) |

### Layer 1 — Visible objects

| Object | Status | Notes |
|---|---|---|
| Text | Systematized | Role anchors deck-wide, bounded per-occurrence adjustment, hierarchy and paragraph rules, natively editable runs |
| Vector shapes | Systematized | primitive → Office preset → Boolean → freeform construction ladder, with native conversion rules |
| Lines & connectors | Asymmetric by design | Native `p:cxnSp` export is implemented, and endpoint attachment is restored on the preserve/mirror round-trip from a source deck. Newly authored connectors deliberately stay unconnected, and hand-written endpoint/site metadata is not accepted |
| Icons | Systematized | Bundled libraries with per-project sync; project icons are prepared material |
| Logo | Bounded by design | Brand workspaces describe how to install officially supplied artwork; no workspace bundles a logo |
| Images | Systematized | Acquisition, generation, treatment, cropping, layout, composition, embedding, provenance |
| Charts | Systematized | Dedicated authoring reference; SVG by default, native Chart replacement available as an explicit opt-in |
| Tables | Systematized | Dedicated authoring reference; six cell-grid grammars, native Table replacement on the same opt-in |
| Diagrams | Systematized | Six relationship atoms — `order`, `link`, `parent`, `membership`, `contrast`, `overlap` |
| Formulas | Implemented | Standalone block formulas and same-paragraph inline formulas compile from a strict LaTeX subset to editable PowerPoint OMML; SVG previews are authoring-only and no formula image fallback is emitted. PowerPoint 2010+ is supported; non-PowerPoint clients are outside the contract |
| Audio & video | Covered / Signal-driven | Narration audio embeds per slide today; arbitrary video, background music, and media compression are planned modules in the Enhance route |
| SmartArt | Asymmetric by design | Source diagram parts are read for their content and structure; generated decks redraw that content through the ordinary shape pipeline. DiagramML is never edited and native SmartArt regeneration is not promised |
| 3D models, OLE objects | Signal-driven | No read or authoring path today |

*Illustration* is deliberately absent from this table. It is a composite result — an image, an SVG, or a group of shapes — not a seventh carrier, and listing it beside *Images* would reintroduce the category confusion this layering removes.

### Layer 2 — Composition

| Concern | Status | Notes |
|---|---|---|
| Background | Systematized | Solid and gradient page backgrounds export as PowerPoint-native slide backgrounds; the picture case is signal-driven |
| Layering & grouping | Systematized | Explicit z-order and group contracts, including registered base/subject layer pairs |
| Grid, alignment, whitespace | Systematized | Composition-geometry vocabulary carried by every visual style |
| Palette | Systematized | Declared HEX values are the truth source; anchors locked deck-wide |
| Typography | Systematized | One size per structural role, locked across the deck |
| Visual effects | Systematized | Dedicated effects reference; native effects on authored preset shapes remain signal-driven |
| Reading path | Systematized | Entry, progression, hierarchy, and endpoint are validated per page |

### Layer 3 — Behavior

| Concern | Status | Notes |
|---|---|---|
| Page transitions | Systematized | Includes on-demand transition sounds from a bundled CC0 catalog |
| Object animation | Systematized | Off by default and opt-in; per-object configuration is explicit |
| Auto-advance | Covered | Derived from narration lead-in, audio duration, and page-tail padding |
| Media playback | Covered | Narration audio; arbitrary embedded media follows the Layer 1 row above |
| Hyperlinks | Systematized | Whole-object and inline-text links author through standard SVG `<a href>`, export as native external or same-deck click relationships, and reconstruct on supported PPTX import |
| Actions & navigation | Bounded by design | An `actionButton*` preset maps visual geometry only — preset appearance never invents action behavior or navigation targets |

### Layer 4 — Document structure

| Concern | Status | Notes |
|---|---|---|
| Theme | Covered | Generated per deck from the locked palette and typography |
| Master / Layout | Systematized | Real `p:sldMaster` / `p:sldLayout` parts on structured routes |
| Placeholders | Systematized | Template workspace contracts, with strict/adaptive exporter behavior derived per deck |
| Speaker notes | Systematized | Exported with a real notes master |
| Narration | Systematized | Per-slide audio with provider provenance |
| Subtitles | Systematized | Word-timed regrouping across supported providers into shared compact SRT |
| Document metadata | Covered | Set at export rather than left to the packaging library |
| Accessibility (alt text, reading order) | Signal-driven | Image manifests already carry `alt_text`, but it is not yet written to DrawingML `descr` — this is wiring, not a missing specification |
| Comments, revisions, collaboration state | Not on the path | Office collaboration surface, outside the authoring product |

---

## In progress / Next

Actively underway or up next — no committed timeline.

- **Calibrate the recently landed systems on real decks** — multi-deck intake, the material-divergence field, the spot-illustration system, and structured template creation have all shipped; what they need now is real-usage signal, not more mechanism. No pre-emptive thresholds or quotas.
- **Prompt slimming** — compress per-role prompt token footprint and improve cache hit rate without sacrificing quality. This is the indirect cost/speed lever; the boundary with quality-sacrificing speedups is drawn under Non-goals.

---

## Future directions — signal-driven

Candidates already evaluated as "worth doing when real demand shows", listed so the intent is public. None is a commitment.

- **Keep closing the native-coverage gaps** recorded in the [mapping guide](./powerpoint-svg-mapping.md) — release after release, move more "SVG-only" cells toward native PowerPoint structure and behavior.
- **Effects on authored preset shapes** (e.g. a native drop-shadow) — waits for a precise preset-effect contract plus checker coverage; until then, a stock shape that needs a shadow conservatively stays ordinary SVG.
- **Picture slide backgrounds as native background fill** — solid/gradient page backgrounds already export as PowerPoint-native slide backgrounds; the picture case is demand-driven.
- **Accessibility delivery** — image manifests already carry `alt_text` for planning and confirmation, so alt text and reading order are a matter of connecting existing data to DrawingML `descr` and shape order, not of designing a new contract. Cheaper than the other open items on the map; waits for demand all the same.

---

## Shipped milestones

One line per month. Full detail lives in the [release notes](https://github.com/hugohe3/ppt-master/releases) and the commit log.

| When | Theme |
|---|---|
| 2026-03 | **Native PPTX route takes shape** — the SVG → DrawingML chain becomes usable; chart/layout template indexes ship |
| 2026-04 | **Pipeline at scale** — topic-only generation, 70 chart templates + three icon libraries, the `spec_lock` cross-page consistency contract, per-element animation and narration/video export |
| 2026-05 | **Visual editing + AI-image systematization** — Live Preview with deterministic in-place editing (built on [@WodenJay](https://github.com/WodenJay)'s [PR #85](https://github.com/hugohe3/ppt-master/pull/85)), template workspaces from PPTX, the rendering × palette × type image system, and the legacy raster LaTeX renderer |
| 2026-06 | **Mode & visual-style dual catalogs + intake expansion** — 5 narrative modes × 18 visual styles (+ `custom`), content-faithful beautify profile, multi-deck intake, spot-illustration pipeline, web-image quality gates, source-conversion fidelity gains (caption recognition from [@suay1113](https://github.com/suay1113)'s [PR #191](https://github.com/hugohe3/ppt-master/pull/191), hyperlink preservation distilled from [@ZhaoZuohong](https://github.com/ZhaoZuohong)'s [PR #155](https://github.com/hugohe3/ppt-master/pull/155)) |
| 2026-07 | **Positioning charter + native masters & layouts + token efficiency** ([v4.0.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)) — three-pass staged confirmation UI, real `p:sldMaster` / `p:sldLayout` export, `--native-charts-and-tables` opt-in, motion-export hardening, chart template library compacted |

---

## Non-goals

The directions below come up repeatedly and have been evaluated as **not on the path**. Listing them is not a value judgment on the underlying need — they simply do not fit this project's product direction. If you specifically need these capabilities, consider other tools or forking.

### Blindly refill arbitrary PPTX placeholder systems

**Issues**: [#53](https://github.com/hugohe3/ppt-master/issues/53), [#118](https://github.com/hugohe3/ppt-master/issues/118)

The Generate PPTX route is built around full control of newly authored shapes, text, and layout. A structured PPTX can inform a reviewed reusable package in two explicit ways: `standard` / `fidelity` author a new SVG and Master/Layout system from visual evidence, while `mirror` materializes a new workspace from the complete set of supported source facts actually present, including unused Layout definitions. Neither path modifies the source PPTX or recovers absent design intent. Generic "open any PPTX and blindly refill every placeholder" remains a different product shape.

**The basic need is actually simple**: if you just need "replace Excel data into fixed positions in a PPT template", have the AI write a few lines of `python-pptx`. You don't need this pipeline.

> **Supported boundaries**: Fill Native PPTX (`template-fill-pptx`) directly refills selected source slides. Create Template (`create-template`) derives an internal authored or mirror implementation from the natural-language request and source evidence. Strategist later derives strict/adaptive exporter behavior from the actual template and current content. What remains out of scope is unreviewed, schema-free substitution against arbitrary third-party placeholder systems.

### Make native PowerPoint charts the default

**Issues**: [#99](https://github.com/hugohe3/ppt-master/issues/99), [#100](https://github.com/hugohe3/ppt-master/issues/100)-class

Pixel-fidelity across the four renderers (PowerPoint / Keynote / LibreOffice / WPS) is the project's spine. Switching the default route to native PowerPoint charts breaks that — the same PPTX renders different chart layouts across renderers. Charts as SVG is **by design**, not a capability gap.

The narrow exception is the `data-pptx-replace-with` marker: independently planned supported data charts and pure text-grid tables can carry a PowerPoint-native Chart/Table replacement payload when their semantic object key is recorded as `<object-key>=yes` in the Design Spec §IX `Native-ready` map; `no` and incidental microvisuals remain ordinary shapes. §VII only records selected reusable references. Exporting with `--native-charts-and-tables` activates prepared markers for users who deliberately trade cross-renderer fidelity for a data-backed object and its chart/table-specific editing model — the activated objects preserve the deck's chart-area / plot / axis / gridline / label colors and native table formatting rather than snapping to PowerPoint's default theme (see the [v4.0.0 release notes](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)). The default export path and editable SVG-derived shape system are unchanged.

### uv as default / required dependency

**Issue**: [#111](https://github.com/hugohe3/ppt-master/issues/111)

`pip + requirements.txt` is the only official install path because it works in every Python environment with no extra learning cost. uv is a fine tool, but making it default raises the bar for new users. If you personally prefer uv, use it in your fork — it won't affect the main line.

### Pure speed optimization

**Issue**: [#97](https://github.com/hugohe3/ppt-master/issues/97)

In the cost / speed / quality triangle this project picks **quality**. ~20 minutes for a high-quality PPTX is the current reasonable point.

Will do: indirect improvements via prompt slimming / cache hit rate.

Explicit `quick-generate` is a user-selected workflow shortcut: it skips
Strategist, confirmation, and the first-page gate, then authors SVG, runs one
lockless final quality gate, and exports the final PPTX. Because the whole
planning phase no longer happens — the Strategist reference load, the
`design_spec.md` / `spec_lock.md` artifacts, and the staged confirmation round
trip — its token cost disappears with it, while per-page SVG authoring is
unchanged. It keeps the same visual/resource capabilities and final blocking
standard, but without a confirmed design contract, first-page calibration, or
resumable decision history it does not promise the same design decisions or
wall-clock time as Default.

The default Generate pipeline continues to prefer quality over speed.

### Standalone CLI / hosted SaaS / desktop app form factors

The product form is a **chat-driven workflow / skill inside an agent-capable AI tool** (Claude Code, Codex, Cursor, VS Code agents, and others).

Won't do: standalone CLI (`ppm`-style), SaaS web service, Electron shell. Any "make it run independently of chat" proposal will be declined. Chat is the interaction core, not a wrapper.

---

## Feedback channels

- **Issues**: [github.com/hugohe3/ppt-master/issues](https://github.com/hugohe3/ppt-master/issues) — bugs / proposals
- **Discussions**: [github.com/hugohe3/ppt-master/discussions](https://github.com/hugohe3/ppt-master/discussions) — usage / experience sharing
- **Email**: heyug3@gmail.com

Before proposing a new direction, scan the **Non-goals** above. If your request falls there, it's unlikely to land — but we're happy to discuss other paths to your underlying need.
