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

**Read this as a map, not a backlog.** *Bounded by design* and *Asymmetric by design* are settled shapes, not unfinished cells — a blank there is a decision, not a debt. *Not planned* rows say in the row why they are not being worked on. Only *Signal-driven* rows lean open, and their reasoning lives in [Future directions](#future-directions--signal-driven) rather than being repeated here. Positions that have actually been argued out live in [Non-goals](#non-goals); this map describes, it does not adjudicate.

| Status | Meaning |
|---|---|
| **Systematized** | Has a dedicated authoring contract; applicable, objectively decidable parts receive validation; actively refined |
| **Covered** | Works today without a dedicated specification system |
| **Bounded by design** | Deliberately stops where it stops; the reason is recorded |
| **Asymmetric by design** | Supported on one side only — typically reading or preserving a source deck, but not authoring |
| **Signal-driven** | Worth doing when real demand shows; not a commitment |
| **Not planned** | Not being considered right now; the reason is in the row |

### Layer 1 — Visible objects

| Object | Status | Notes |
|---|---|---|
| Text | Systematized | Role anchors deck-wide, bounded per-occurrence adjustment, hierarchy and paragraph rules, natively editable runs |
| Native WordArt & warped text | Not planned | AI-generated decorative lettering is the preferred visual carrier, with ordinary editable text as the fallback. Native WordArt, text warp, and text-on-path would add a separate authoring and compatibility surface without improving that path, so they are not generated |
| Vector shapes | Systematized | primitive / Office-preset atoms → independent composition → Boolean only when one contour requires it → necessary freeform construction ladder, with native conversion rules |
| Lines & connectors | Asymmetric by design | Native `p:cxnSp` export is implemented, and endpoint attachment is restored on the preserve/mirror round-trip from a source deck. Newly authored connectors stay unconnected. Binding them would first require deciding which lines are real edges and which are decoration — an intent judgment that no geometric threshold settles, and one that is made by the AI wherever it is placed, so moving it upstream to authoring buys no reliability. The result would be some arrows in a diagram following their node and others not |
| Icons | Systematized | Bundled SVG libraries with per-project sync; project icons are prepared material. Illustrated semantic cues remain generated slices under `images/` for ordinary image composition and never become icon-library entries |
| Logo | Bounded by design | A logo is always existing artwork, never designed here: brand workspaces install officially supplied files as prepared assets — bundled brand presets ship official marks with recorded usage rules — and the simple-icons library covers real company / product marks |
| Images | Systematized | Acquisition, generation, treatment, cropping, layout, composition, embedding, provenance |
| Charts | Systematized | Dedicated authoring reference; SVG by default, native Chart replacement available as an explicit opt-in |
| Tables | Systematized | Dedicated authoring reference; six reusable cell-grid references, with custom grids still available; native Table replacement uses the same opt-in |
| Diagrams | Systematized | Six relationship atoms — `order`, `link`, `parent`, `membership`, `contrast`, `overlap` |
| Formulas | Systematized | Standalone block and same-paragraph inline formulas compile every explicitly documented Microsoft 365 LaTeX / mhchem input to editable OMML, with documented native normalizations and fail-closed handling outside the profile. PPTX import rebuilds validator-clean, PPT Master-owned OMML into normalized formula markers with visible SVG previews; arbitrary third-party OMML and original LaTeX spelling recovery remain outside the contract. No image fallback is emitted. The package target remains PowerPoint 2010+; the executable profile is pinned to the stated Microsoft documentation versions, while repository verification is compiler/OMML/package-level rather than complete Microsoft 365 UI certification. Non-PowerPoint clients remain outside the contract |
| Narration & animation audio | Systematized | Per-slide narration audio, plus native transition and object sounds drawn from the bundled CC0 catalog |
| Arbitrary video & background music | Not planned | A one-off, content-specific insert that is faster to place by hand in PowerPoint, and the AI cannot pick the file for you. Background music additionally pulls in narration-mixing decisions that are out of scope. Media already present in a source deck is preserved unchanged through the Fill and Enhance routes |
| SmartArt | Asymmetric by design | Source diagram parts are read for their content and structure; generated decks redraw that content through the ordinary shape pipeline. DiagramML is never edited and native SmartArt regeneration is not promised |
| 3D models, OLE objects | Not planned | Both need the host application or a recent Office build on the opening machine and fall back to a still preview elsewhere — the cross-renderer problem this project avoids by design. Inserting one by hand takes seconds. Objects already present in a source deck are preserved unchanged |
| Ink & camera feeds (Cameo) | Not planned | Hand-drawn annotation and live camera objects are presenter-session surfaces rather than generated design content, and both depend on recent Office builds. Such parts already present in a source deck pass through source-preserving routes as untouched package structure |

*Illustration* is deliberately absent from this table. It is a composable result—an image, transparent slice, SVG, or group of shapes—not a seventh carrier. It may combine with any other suitable page carrier; listing it beside *Images* would reintroduce the category confusion this layering removes.

### Layer 2 — Composition

| Concern | Status | Notes |
|---|---|---|
| Background | Systematized | Solid and gradient page backgrounds export as PowerPoint-native slide backgrounds; the picture case is signal-driven |
| Layering & grouping | Systematized | Explicit z-order and group contracts, including registered base/subject layer pairs |
| Illustration composition | Systematized | Planned per page as a coherent element family; when generation is available, compatible assets may be batch-generated on keyed sheets, strictly alpha-sliced, then reused as fixed title/corner chrome or recomposed as anchors, supporting figures, and accents alongside text, shapes, photos, and lettering |
| Grid, alignment, whitespace | Systematized | Shared composition contract plus composition-geometry vocabulary carried by each visual style |
| Palette | Systematized | Declared HEX values are the truth source for named semantic roles; reusable role anchors stay stable deck-wide, while contextual derivatives and sparse page-local accents remain available |
| Typography | Systematized | One deck-wide size anchor per structural role, with bounded `±2px` per-occurrence adjustment and a sparse non-structural Hero/Display exception |
| Visual effects | Systematized | Dedicated effects reference; one registered outer shadow or glow compiles to one editable native effect on supported basic objects and compact authored preset shapes |
| Reading path | Systematized | Each page plan declares one primary emphasis anchoring entry, progression, hierarchy, and endpoint; visual review checks the most prominent element and anchor placement against that declaration |

### Layer 3 — Behavior

| Concern | Status | Notes |
|---|---|---|
| Page transitions | Systematized | Includes on-demand transition sounds from a bundled CC0 catalog; PPTX import reconstructs exact current-registry transitions into the canonical sidecar |
| Object animation | Systematized | Off by default and opt-in; per-object configuration is explicit, and PPTX import reconstructs the finite exact-duration current-registry subset into the canonical sidecar |
| Auto-advance | Covered | Derived from narration lead-in, audio duration, and page-tail padding |
| Media playback | Covered | Narration audio and animation sounds play natively; media already present in a source deck keeps its playback settings |
| Hyperlinks | Systematized | Whole-object and inline-text links author through standard SVG `<a href>`, export as native external or same-deck click relationships, and reconstruct on supported PPTX import |
| Actions & navigation | Systematized | Navigation is authored explicitly by wrapping the target in a hyperlink anchor, including same-deck slide jumps. An `actionButton*` preset contributes visual geometry only — appearance alone never implies an action. Mouse-over triggers, custom shows, macro or program execution, and raw `ppaction://` injection stay outside the contract |
| Zoom (summary / section / slide) | Not planned | An Office-build-dependent navigation object that falls back to a static picture in other renderers — the cross-renderer degradation this project avoids by design. Same-deck jumps are covered by native hyperlink slide targets |

### Layer 4 — Document structure

| Concern | Status | Notes |
|---|---|---|
| Slide size | Systematized | The canvas contract selects the presentation format; the SVG `viewBox` is the single geometry truth with fail-closed validation, and every page in a deck must agree on one format |
| Theme | Systematized | Lock-backed Default export derives each deck's `clrScheme`, major/minor fonts, and Master title/body size defaults from its palette and typography contract. Lockless Quick keeps converter-default Theme scaffolding while writing SVG-derived page colors and fonts as direct values |
| Font embedding | Bounded by design | Fonts are never embedded in the package; a brand or web face leads only after confirmed availability on the target system, otherwise export uses a safe family and keeps the intended face recorded in the Design Spec |
| Slide sections | Asymmetric by design | Source-preserving native workflows retain existing section metadata as untouched package structure. Routes that generate or rebuild a slide roster do not author PowerPoint Sections because page roles and optional Design Spec Parts do not form one required, route-wide section contract. Sections change only how the thumbnail rail organizes a deck and never change page appearance; grouping a long deck by hand in PowerPoint takes about a minute and is done once |
| Master / Layout | Systematized | Real `p:sldMaster` / `p:sldLayout` parts on structured routes |
| Placeholders | Systematized | Template workspace contracts, with strict/adaptive exporter behavior derived per deck |
| Date, footer & slide-number fields | Bounded by design | Structured template routes author real date / footer / slide-number placeholders under the placeholder contract. Free-design decks deliberately keep drawn page numbers and footers as ordinary text: a page numeral is often a design element rather than a standard field, telling the two apart is an intent judgment, and inserting a standard field by hand in PowerPoint takes seconds and is done once |
| Speaker notes | Systematized | Exported with a real notes master |
| Narration | Systematized | Per-slide audio with provider provenance |
| Subtitles | Systematized | Word-timed regrouping across supported providers into shared compact SRT |
| Document metadata | Covered | Set at export rather than left to the packaging library |
| Accessibility (alt text, reading order) | Not planned | AI-generated images carry an `alt_text` field and web-scraped images record the page's often-empty `alt` attribute, but shapes, charts, diagrams, and user-supplied images have no description at all — full coverage means authoring descriptions for every non-text object, not connecting existing data. Reading order is not a separate property in PowerPoint: it is the shape order, which carries the page's visual layering and is not set independently of it |
| Macros & Office extension XML | Asymmetric by design | Never authored — the generated route does not synthesize VBA; existing macro or extension parts persist only where a macro-aware source-preserving workflow keeps the owning package parts unchanged |
| Comments, revisions, collaboration state | Not planned | Office collaboration surface, outside the authoring product |

---

## In progress / Next

Actively underway or up next — no committed timeline.

- **Calibrate the recently landed systems on real decks** — multi-deck intake, the material-divergence field, the composable-illustration system, and structured template creation have all shipped; what they need now is real-usage signal, not more mechanism. No pre-emptive thresholds or quotas.
- **Prompt slimming** — compress per-role prompt token footprint and improve cache hit rate without sacrificing quality. This is the indirect cost/speed lever; the boundary with quality-sacrificing speedups is drawn under Non-goals.

---

## Future directions — signal-driven

Candidates already evaluated as "worth doing when real demand shows", listed so the intent is public. None is a commitment.

- **Keep closing the native-coverage gaps** recorded in the [mapping guide](./powerpoint-svg-mapping.md) — release after release, move more "SVG-only" cells toward native PowerPoint structure and behavior.
- **Picture slide backgrounds as native background fill** — solid/gradient page backgrounds already export as PowerPoint-native slide backgrounds; the picture case is demand-driven.

---

## Shipped milestones

One line per month. Full detail lives in the [release notes](https://github.com/hugohe3/ppt-master/releases) and the commit log.

| When | Theme |
|---|---|
| 2026-03 | **Native PPTX route takes shape** — the SVG → DrawingML chain becomes usable; chart/layout template indexes ship |
| 2026-04 | **Pipeline at scale** — topic-only generation, 70 chart templates + three icon libraries, the `spec_lock` cross-page consistency contract, per-element animation and narration/video export |
| 2026-05 | **Visual editing + AI-image systematization** — Live Preview with deterministic in-place editing (built on [@WodenJay](https://github.com/WodenJay)'s [PR #85](https://github.com/hugohe3/ppt-master/pull/85)), template workspaces from PPTX, the rendering × palette × type image system, and the legacy raster LaTeX renderer |
| 2026-06 | **Mode & visual-style dual catalogs + intake expansion** — 5 narrative modes × 18 visual styles (+ `custom`), content-faithful beautify profile, multi-deck intake, composable-illustration pipeline, web-image quality gates, source-conversion fidelity gains (caption recognition from [@suay1113](https://github.com/suay1113)'s [PR #191](https://github.com/hugohe3/ppt-master/pull/191), hyperlink preservation distilled from [@ZhaoZuohong](https://github.com/ZhaoZuohong)'s [PR #155](https://github.com/hugohe3/ppt-master/pull/155)) |
| 2026-07 | **Positioning charter + native masters & layouts + token efficiency** ([v4.0.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)) — three-pass staged confirmation UI, real `p:sldMaster` / `p:sldLayout` export, `--native-charts-and-tables` opt-in, motion-export hardening, chart template library compacted |
| 2026-08 | **Template library + page-image reconstruction + native math and links + AI imagery as composition** ([v4.5.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.5.0), [v4.6.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.6.0), [v4.7.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.7.0), [v4.8.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.8.0)) — brand / style / layout workspace library, visualizations split by information model with structure as a composition grammar, the Codex-supported `image-to-pptx` profile, video delivery carrying native animation sound, three editable whole-solution design directions, editable OMML formulas across the documented Microsoft 365 profile, native hyperlink authoring, composable AI illustration families and decorative lettering, task-driven image sourcing with isolated thumbnail review, transition and object-animation reverse import, and the four-layer coverage map |

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
unchanged. It keeps the same page-level visual and resource-authoring
capabilities and the shared SVG/resource blocking standards. It does not run
Spec Lock alignment checks; its package keeps converter-default Theme
scaffolding instead of deriving Theme colors, fonts, and Master title/body size
defaults from a lock. Without a confirmed design contract, first-page
calibration, or resumable decision history it does not promise the same design
decisions or wall-clock time as Default.

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
