# Roadmap

[English](./roadmap.md) | [中文](./zh/roadmap.md)

---

> PPT Master is a solo-maintained open source project, driven by **priority rather than fixed timelines**. This roadmap is here to align expectations: what's already shipped, what's under ongoing maintenance and evolution, and what's intentionally out of scope. Priorities shift with user feedback and real usage signals — no committed delivery windows.
>
> **Where we are**: AI generates SVG from scratch → converts to DrawingML for natively editable PPTX. The core axis is **pixel-fidelity across four renderers** (PowerPoint / Keynote / LibreOffice / WPS) **+ real native shapes**. Every direction below serves that axis.

---

## Recent capability evolution

The past two months' structural capability growth. Single flags / incremental polish go to the commit log.

### 2026-03 — Native PPTX route takes shape

- **Direct export to natively editable PPTX** — `svg_to_pptx` adds glow / rotate / text-decoration / stroke-linejoin; the full SVG → DrawingML chain becomes usable
- Chart / layout template JSON indexes ship, AI selection path connected

### 2026-04 — Pipeline at scale

- **Source-less generation**: `topic-research` workflow supports "topic only, no source files"
- **PPTX export step-change**: SVG clipPath → DrawingML picture geometry, marker → native arrows, output consolidated to `exports/`
- **Chart library expands to 70 templates + three icon libraries** (simple-icons / phosphor-duotone / brand-logo)
- **`spec_lock.md` machine-readable contract**: Strategist locks the spec, Executor re-reads it before every page — cross-page consistency gets a real guarantee
- **Per-element animation on by default** + recorded narration / video export ([`workflows/generate-audio.md`](../skills/ppt-master/workflows/generate-audio.md))

### 2026-05 — Visual editing + AI image systematization

- **Live Preview enters the main pipeline** ([`workflows/live-preview.md`](../skills/ppt-master/workflows/live-preview.md)) — browser preview, click elements to write annotations, say "apply my annotations" and the AI rewrites that region (built on [@WodenJay](https://github.com/WodenJay)'s [PR #85](https://github.com/hugohe3/ppt-master/pull/85))
- **Replicate any PPTX as a template** ([`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md)) — PPTX → SVG reverse + OOXML theme / master / layout / asset extraction
- **AI image three-dimension system** rendering × palette × type + Strategist h.5 lock, downstream consumes a fixed contract
- **AI image `hero_page` dual-track** — local insert + full-canvas hero image coexist
- **Brand identity preset subsystem** ([`workflows/create-brand.md`](../skills/ppt-master/workflows/create-brand.md)) — extract and reuse brand palette / typography / logo / voice
- **Visual self-review workflow** ([`workflows/visual-review.md`](../skills/ppt-master/workflows/visual-review.md)) — rubric-based per-page check of AI-generated SVGs
- **AI image: Type concept boundary clarification** — Type is now narrowed to "the internal geometric skeleton of a local infographic block" (11 real skeletons); the four pseudo-types (hero / background / portrait / typography) fold back into `page_role: hero_page` plus four composition primitives (single-subject / portrait / typographic / atmospheric); hero_page text layering rule (visual keywords embedded, editable text via SVG overlay)
- **Brutalist AI newspaper example deck shipped** ([`examples/ppt169_brutalist_ai_newspaper_2026/`](../examples/ppt169_brutalist_ai_newspaper_2026/)) — first of the three P0 capability-backing demos: wall-to-wall small type + irregular columns + halftone monochrome + single-spot red + real native shapes; 10-page editorial annual report stressing text-position precision and cross-page consistency
- **Kubernetes Blueprint example deck shipped** ([`examples/ppt169_kubernetes_blueprint_2026/`](../examples/ppt169_kubernetes_blueprint_2026/)) — second of the three P0 capability-backing demos: isometric technical-drawing aesthetic + blueprint cyan/amber palette + hand-authored SVG geometry (no raster images) + custom drawing-in animation; 10-page Kubernetes architecture walkthrough stressing geometric shape generalization and chart-structure extensibility
- **AI image `custom` escape hatch** — `rendering` / `palette` / hero composition each accept `custom` + a one-paragraph `*_behavior` prose, replacing the false "default to vector-illustration / cool-corporate" fallback; end-to-end contract spans [`image-renderings/_index.md`](../skills/ppt-master/references/image-renderings/_index.md) §1.5, [`image-palettes/_index.md`](../skills/ppt-master/references/image-palettes/_index.md) §2, Strategist h.5 hard-rule (≤1 custom per dimension; one candidate may carry both), spec_lock fields, and Image_Generator Step 2 consumption branch
- **Template architecture: three-kind consolidation** ([`docs/templates-architecture.md`](./templates-architecture.md)) — brand / layout / deck split into three independent dirs with per-kind schemas + segment-level fusion + git-style conflict resolution; SKILL.md Step 3 dispatches per `kind`, trigger rule remains "explicit path only"
- **Pattern fill PPTX safety net** — `svg_quality_checker.py` now warns on `<pattern>` without `data-pptx-pattern` (silent fallback to `ltUpDiag`) and errors on values outside OOXML `ST_PresetPatternVal` (schema-failed PPTX that won't open); `shared-standards.md §7` documents the closed preset enum and the required `<rect fill="<bg>"/>` child convention
- **LaTeX math formula rendering shipped** ([`scripts/latex_render.py`](../skills/ppt-master/scripts/latex_render.py)) — Strategist locks one of three policies (`mixed` / `render-all` / `text-only`) inside the Typography confirmation and writes an explicit `images/formula_manifest.json`; the renderer walks a codecogs → quicklatex → mathpad → wikimedia fallback chain and emits transparent PNGs that land in §VIII as `Acquire Via: formula` / `Status: Rendered` rows; formula-heavy decks (academic / engineering / educational) finally have a native rendering route. Formula selection is a Strategist decision — the renderer never scans source files for `$...$` markers
- **Live preview direct editing — L1 / L2 / L3** ([`workflows/live-preview.md`](../skills/ppt-master/workflows/live-preview.md)) — the browser editor gains deterministic in-place edits with no AI round-trip: text content (L1), presentation attributes like fill / stroke / font-size (L2), and on-canvas geometry (L3) — drag a selected element to move it, arrow-key nudge (`Shift` = 10px), multi-select, plus a right-click overlap picker for stacked shapes. Edits stage with `Ctrl+Z` undo + coalescing and write to `svg_output/` on **Apply changes**; moves persist through finalize / export (moved text frames, promoted multi-line tspans, repositioned icons all reproduce in the PPTX). Re-export stays chat-driven; on-canvas resize handles are not yet implemented (resize via the geometry inputs)

### 2026-06 — Mode & visual-style dual catalogs

- **Three executors retired → mode + visual-style dual catalogs** ([`references/modes/`](../skills/ppt-master/references/modes/) + [`references/visual-styles/`](../skills/ppt-master/references/visual-styles/)) — the old three `executor-*.md` (general / consultant / consultant-top) entangled domain · audience · persuasion · narrative on one axis; split into two orthogonal catalogs (following the `image-renderings` pattern: flat dir + `_index` + on-demand read + Strategist locks one). **mode** = narrative skeleton (`pyramid` / `narrative` / `instructional` / `showcase`; consultant + top merge into pyramid since their narrative core is identical); **visual-style** = SVG layout aesthetic (`swiss-minimal` / `editorial` / `soft-rounded` / `dark-tech`, each paired with an image-rendering, **zero HEX** — color truth stays in confirmation e + image-palettes). Strategist `§d` locks `mode` + `visual_style` independently into `spec_lock`; Executor loads the two locked files; any mode × any style. Render coordinates stay in `templates/charts/`
- **Prompt constraint-strength decoupling** ([`docs/rules/prompt-style.md`](rules/prompt-style.md) §4) — three explicit strength tiers — rule (`Hard rule` / `Forbidden`) / default (`Default — … may override`) / reference (`Reference — not a constraint`) — plus an "objective failure vs taste" test and a checker boundary, so the model can tell "must keep vs may deviate" at a glance; the visual-style catalog is Reference-strength throughout
- **visual-style catalog grows to 18, aligned with image-renderings + examples reclaimed** — first four distilled from the [examples library](../examples/) (`brutalist` / `blueprint` / `memphis` / `zine`), then six filling in the hand-drawn / textured renderings that have a layout twin (`sketch-notes` / `ink-notes` / `chalkboard` / `paper-cut` / `vintage-poster` / `pixel-art`), then four more reclaimed from still-uncovered example aesthetics: `ink-wash` (rice-paper whitespace, from 藏拙 / 李子柒) · `glassmorphism` (dark frosted-glass + gradient light, from glassmorphism_demo, split out of soft-rounded) · `photo-editorial` (full-bleed photography dominates, text captions, from Pritzker / fashion_weekly) · `data-journalism` (Bloomberg/Economist multi-column micro-charts + sidebars, from global_ai_capital). The catalog is regrouped into five families (corporate-product / editorial-publication / expressive-print / hand-drawn-brush / specialty). **The test**: a rendering earns a visual-style twin only when it defines a whole-page layout language, not merely how an inserted image looks — so photo-*led composition* gets `photo-editorial` (paired with corporate-photo), while purely atmospheric renderings (nature / warm-scene / fantasy-animation) stay imagery-only and just pair with a layout style. Zero HEX, Reference strength throughout
- **mode catalog grows to 5: add `briefing`** — fills the "neutral information delivery" cell: no thesis, no story, no teaching, no spectacle — topic titles, even weight, complete and scannable, for status updates / reference decks / catalogs / meeting packs / FAQs that inform without arguing. The five now partition presentation *intent* more nearly MECE: persuade (pyramid) · tell a story (narrative) · teach (instructional) · impress (showcase) · simply inform (briefing). `_index` gains a `briefing` vs `pyramid` tie-breaker ("if you'd have to invent a thesis to fit pyramid, it's briefing"). Five presets plus a `custom` escape hatch for a bespoke direction none of them captures (a special cadence, a multi-mode fusion, a particular posture) — either user-requested or Strategist-recommended, confirmed like every lock; a deck always locks one value, and a fusion is one `custom` describing the acts. The only thing to avoid is defaulting to `custom` when a preset genuinely fits. Mirrors the truth-precedence rule that a user-authored outline or direction overrides the mode

---

## In progress / Next

Directions actively underway or up next, with no committed timeline.

- **Validate and calibrate the new mode / visual-style system on real decks** — the 5 modes + 18 visual-styles + the `custom` escape hatch are all still design-stage, unproven at this scale on real decks. The next step is not more presets but running real decks across the new modes / styles / custom and tightening from real signal: where the Strategist mis-selects a mode or style, where the Executor doesn't honor a style's discipline, whether a `custom` lock reads clearly at confirmation. Then adjust the auto-selection tables and the per-mode / per-style wording accordingly. Mode boundary-gray-zone polish folds into this — calibrate from real use, not speculation; no further presets planned

---

## Ongoing maintenance directions

Long-running improvements with no committed timeline. Only real directions are listed; specific fixes / single flags go to the commit log.

- **Prompt slimming** — compress per-role prompt token footprint and improve cache hit rate without sacrificing quality, for indirect cost / speed gains. Complements "Pure speed optimization" below: indirect optimization yes, quality-sacrificing speedups no.

---

## Non-goals

The directions below come up repeatedly and have been evaluated as **not on the path**. Listing them is not a value judgment on the underlying need — they simply don't fit this project's main route. If you specifically need these capabilities, consider other tools or forking.

### Read arbitrary PPTX templates → fill text only

**Issues**: [#53](https://github.com/hugohe3/ppt-master/issues/53), [#118](https://github.com/hugohe3/ppt-master/issues/118)

PPT Master's main route is "AI generates SVG from scratch → DrawingML", with the whole pipeline built around full control of every shape / text / layout. "Parse existing PPTX placeholders + only refill text" is a different product shape requiring handling of arbitrary master / theme / placeholder systems — orthogonal to where this architecture invests.

**The basic need is actually simple**: if you just need "replace Excel data into fixed positions in a PPT template", have the AI write a few lines of `python-pptx`. You don't need this pipeline.

### Switch to native PowerPoint charts (Excel-native chart)

**Issues**: [#99](https://github.com/hugohe3/ppt-master/issues/99), [#100](https://github.com/hugohe3/ppt-master/issues/100)-class

Pixel-fidelity across the four renderers (PowerPoint / Keynote / LibreOffice / WPS) is the project's spine. Switching to native PowerPoint charts breaks that — the same PPTX renders different chart layouts across renderers. Charts as SVG is **by design**, not a capability gap.

If you need data-driven native Excel charts, pick a different tool or manually replace charts in PowerPoint post-export — this project won't build that path in.

### uv as default / required dependency

**Issue**: [#111](https://github.com/hugohe3/ppt-master/issues/111)

`pip + requirements.txt` is the only official install path because it works in every Python environment with no extra learning cost. uv is a fine tool, but making it default raises the bar for new users. If you personally prefer uv, use it in your fork — it won't affect the main line.

### Pure speed optimization

**Issue**: [#97](https://github.com/hugohe3/ppt-master/issues/97)

In the cost / speed / quality triangle this project picks **quality**. ~20 minutes for a high-quality PPTX is the current reasonable point.

Will do: indirect improvements via prompt slimming / cache hit rate.
Won't do: trading quality for "throw a few pages together" speed.

If speed-sensitive and quality-tolerant, Gamma / similar AI tools are a better fit.

### CLI / SaaS / desktop app form factors

The product form is firmly **chat-driven AI IDE skill** (Claude Code / Cursor / VS Code + Copilot / Codebuddy).

Won't do: standalone CLI (`ppm`-style), SaaS web service, Electron shell. Any "make it run independently of chat" proposal will be declined. Chat is the interaction core, not a wrapper.

---

## Feedback channels

- **Issues**: [github.com/hugohe3/ppt-master/issues](https://github.com/hugohe3/ppt-master/issues) — bugs / proposals
- **Discussions**: [github.com/hugohe3/ppt-master/discussions](https://github.com/hugohe3/ppt-master/discussions) — usage / experience sharing
- **Email**: heyug3@gmail.com

Before proposing a new direction, scan the **Non-goals** above. If your request falls there, it's unlikely to land — but we're happy to discuss other paths to your underlying need.
