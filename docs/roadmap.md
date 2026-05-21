# Roadmap

[English](./roadmap.md) | [中文](./zh/roadmap.md)

---

> PPT Master is a solo-maintained open source project, driven by **priority rather than fixed timelines**. This roadmap is here to align expectations: what's being worked on, what's planned, and what's intentionally out of scope. Priorities shift with user feedback and real usage signals — no committed delivery windows.
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

---

## P0 — Active focus

Strong rationale, work in progress.

### 1. Capability-backing example decks (Style demo P0)

As the community enters its growth phase, example decks shift from "show visual contrast" to "prove the capability bar" — making it obvious why Gamma / Manus-style tools can't replace PPT Master.

P0 three picks each stress-test a core capability:

- **Dashboard / data-dense report** — stress-tests real native shapes + complex chart structure. A page with 6-10 charts is where shape-vs-Excel-native paths diverge the most
- **Brutalist newsprint / extreme information density** — stress-tests text position precision + cross-page consistency. Wall-to-wall small type with irregular columns only survives later editing because shapes are real
- **Blueprint / isometric technical drawing** — stress-tests geometric shape generalization + chart structure extensibility. Whitepaper / product architecture / industrial design scenarios

---

## P1 — Planned, not scheduled

### 1. Template architecture consolidation

SKILL.md Step 3 (Template Option) has known inconsistencies (defaults to not reading `layouts_index.json` but issues soft prompts based on its contents, bare name resolution is ambiguous, `design_spec.md` fields are unstandardized). These are **intentional transitional state** — to be addressed in one pass when the architecture firms up, not as scattered fixes.

Pre-requisites: `layouts_index.json` field convention, template naming convention, `design_spec.md` standard field set, brand-and-layout composition rules.

### 2. AI image: Mood as an independent dimension

Palette files currently carry "hue", "saturation" and "contrast/temperament" all together, making them long. Plan: extract an independent Mood dimension (subtle / balanced / bold), slim down palette files.

### 3. P1 example decks

- **Academic / IEEE style** — Times/Computer Modern serif + dual-column + formulae + numbered references. Editable PPTX academic papers are a real gap in the market
- **Maximalism / Y2K cyber** — extreme palette + mixed renderings is the hardest combination to keep consistent, the cleanest evidence that Strategist h.5 lock-in works

### 4. Model compatibility matrix doc

"What can Claude / Codex / Gemini / domestic models actually produce" gets answered case-by-case in issues. Plan: a comparison doc covering minimum runnable model, recommended config, and measured performance per axis (alignment / cross-page consistency / chart structure).

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
