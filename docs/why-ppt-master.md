# Why PPT Master

[English](./why-ppt-master.md) | [Chinese](./zh/why-ppt-master.md)

---

There's no shortage of AI presentation tools. This page explains what PPT Master does differently — and where it's not the right choice.

I'm [Hugo He](https://www.hehugo.com/), an investment & finance professional who builds presentations every day. PPT Master is an open-source tool I've spent extensive time refining — because I'm its most demanding user.

This page is the user-facing comparison. Its assumptions about what a presentation is, the jobs it serves, and the layers that determine quality come from [What Is a PPT?](./what-is-ppt.md). The project's long-term positioning, product promises, and capability boundaries live in [Project Positioning](./project-positioning.md).

A good presentation's cost cannot be measured by slide-drawing time alone. It requires several coupled kinds of work: defining the audience and intended outcome, selecting and verifying evidence, shaping the argument and narrative, designing a coherent visual system, constructing an editable native PowerPoint document, and preparing the deck for delivery, review, and reuse. These are not independent passes. Change the message or delivery context, and the outline, slide design, native objects, notes, and validation may all need to change. Much of the cost lies in coordination and rework, not in drawing one more slide.

That is the gap this project addresses. Compressing only one layer — drafting text, applying a theme, or rendering attractive pages — saves time only within that layer. PPT Master is designed to connect the reasoning, visual, and native-delivery layers, so time saved at one stage is not simply spent rebuilding the result at the next.

## 1. Native Depth — Command of PowerPoint's Feature Set

**This is the core differentiator.**

Editable is already table stakes — exporting each slide as an editable `.pptx` is nothing special anymore. The real question is *how deep the editability goes*: PPT Master authors PowerPoint's native object model itself, not a thin editable skin on top — and you reach it from chat:

- **Slide masters & layouts** — real `p:sldMaster` / `p:sldLayout` structure with inheritance (on template / structured routes), not the same chrome pasted onto every page
- **Native shapes** — preset geometry with working adjustment handles (block arrows, chevrons, callouts, flowchart nodes…), connectors, and freeform paths, not just rectangles
- **Native charts & tables, on demand** — data-backed chart and table objects with an Edit-Data workbook when you want them (trade-off note below)
- **The full text, picture, fill, and effect model** — run/paragraph formatting, picture crop and shape-clip, gradients, patterns, outer shadow, glow
- **Transitions, entrance animation, and speaker notes → voice narration** — real OOXML timing and package parts, not baked-in video
- **Template distillation on top** — hand it an existing deck and it extracts a reusable brand / layout / deck template; a layer of reuse built *above* the native primitives

And this depth is a **direction of travel, not a fixed list.** The project's north star is to keep converging with PowerPoint itself — an ongoing effort to build and integrate more of its native capabilities, release after release, narrowing the gap between what an AI can generate for you and what you could build by hand in PowerPoint.

So the boundary is honest, and it moves. Some things are out of scope today — **SmartArt** (a closed, brittle object model, deliberately left out and better rebuilt from ordinary native shapes), a few decorative effects (WordArt, reflection, soft edges), and embedded or legacy objects (OLE, video, macros, native equations). What's in and what's out is never hand-waved: the exact, feature-by-feature boundary — native / approximate / bake-required / unsupported — is published in the [PowerPoint ↔ SVG Mapping Guide](./powerpoint-svg-mapping.md).

And out of scope rarely means *can't* — more often it means *not yet* (the timing isn't right) or *not worth it* (for a niche effect, a quick manual tweak in PowerPoint beats the engineering cost). That call is easy to make precisely because PPT Master's output is a high-quality **draft you keep editing, not a sealed final deck** — the last mile is yours by design.

Put plainly: **the things that take fiddly manual work in PowerPoint — building a master, placing a native chart, distilling a template, wiring per-slide narration — you get from a sentence of chat.**

> **Why it's possible — SVG as the authoring language.** The AI generates a constrained SVG, then scripts compile SVG → DrawingML. SVG and DrawingML are the same kind of thing — absolute-coordinate 2D vector formats where rectangles, paths, gradients, and shadows map one-to-one — so conversion is a dialect translation, not a format bridge. That shared world-view is exactly why the output can be *deep* native PowerPoint instead of flattened boxes. Full rationale in [Technical Design](./technical-design.md).

> **The charts trade-off, stated honestly.** By default, charts and tables export as editable SVG-derived DrawingML shapes — chosen so they render pixel-consistently across PowerPoint / Keynote / LibreOffice / WPS. Pass `--native-charts-and-tables` and eligible ones become native data-backed Chart / Table objects instead. Both are fully editable; **the choice is yours** — cross-app fidelity or a live data workbook, decided by what this deck is for, not locked by the tool.

## 2. Logic First — a Deck Isn't Just Display; the Reasoning Matters More

A deck's value was never only how it looks. What usually decides whether it lands is the reasoning underneath: does the point hold, is the order right, is the hierarchy clear. That step comes before layout and often matters more — and PPT Master owns it too, not just the design that follows.

Before a single slide is drawn, the Strategist reads your source, settles on the core message, and picks a narrative **mode** — `pyramid` (conclusion-first persuasion), `narrative` (story), `instructional` (teaching), `showcase` (impress), or `briefing` (neutral information) — then builds the outline and information hierarchy the visuals go on to serve. From the same material, `pyramid` leads with the conclusion and stacks the support beneath it, while `briefing` lays the facts out evenly and takes no side — a different mode gives the whole deck a different skeleton. Split, merge, reorder, cut, reframe: the structure is reasoned about, not inherited from whatever order your source happened to be in.

This is the less obvious half of the value. A beautiful deck built on a muddled argument is still muddled. PPT Master works the **logic layer and the visual layer**, which is why the output reads like someone thought about it rather than just formatted it — and because both layers stay yours to edit, you keep control of the argument, not only the pixels.

## 3. Transparent Cost — You Pay Your AI Provider, Not Another Subscription

PPT Master itself is free and open source. The only cost is your own AI model usage.

It's also **deliberately built to run inside a coding agent**, and there's a cost reason behind that. Many coding agents come with a **flat subscription plan**, and under a flat plan one more deck doesn't cost extra — so you can generate in bulk on a subscription you're already paying for. Prefer a **direct, per-token API** instead? That's simply a different price structure. Either path works, and which one you take is up to you — that's part of the design.

Either way, PPT Master adds no layer of its own on top of your AI spend: no PPT-platform subscription, no proprietary credits, no per-seat fee.

---

## 4. Data Privacy — 100% Local

Your files never leave your machine. Source documents are converted locally, SVGs are generated locally, PPTX is exported locally. The only external communication is between you and your AI editor — no different from how you normally use it.

No third-party server stores your source documents or output. This matters for finance, government, and any organization with data residency requirements.

---

## 5. Fully Open — No Lock-in on Editors or Models

Your workflow shouldn't be held hostage by any single company. Today you depend on their platform; tomorrow they raise prices, change the rules, or shut down — and everything you've built on top of it is gone. That's not what open source should look like.

PPT Master is a framework, not a plugin for a specific IDE. **On editors:** Claude Code, Codex, Cursor, and whatever comes next all work. **On models:** Claude produces the best results, but GPT, Gemini, and others can all drive PPT Master — the difference is in layout precision, and as models improve, these gaps will narrow.

The choice is yours — and it doesn't stop at editors and models. Native chart objects or cross-app-stable shapes, one canvas format or another, a template or free design: the trade-offs that matter stay in your hands, decided per deck. Handing you those choices instead of locking a path is the whole point of open source.

---

## Features

### Any Narrative Skeleton × Any Visual Style

A deck's design is set by two independent axes you combine freely: the **narrative skeleton** (mode, see the section above) decides how it argues, and the **visual style** decides how it looks — 18 built-ins from `swiss-minimal` and `editorial` to `dark-tech`, `brutalist`, and `ink-wash`, each with a `custom` option. Any one pairs with any other, locked once at confirmation and held stable across the deck.

The [examples/](../examples/) directory spans government fiscal analysis, AI architecture, editorial magazine, data journalism, Swiss grid, Memphis pop, risograph zine, and more.

### Full Source-Document Input

Feed it almost anything: PDF, DOCX, PPTX, EPUB, HTML, LaTeX, RST, web URLs, WeChat articles, Markdown, or plain text — all usable as source material for a deck.

### Multi-Format Output

Output is not limited to standard 16:9 and 4:3 slide ratios. Xiaohongshu 3:4, WeChat/Instagram 1:1, vertical Story 9:16, A4 print — same pipeline, just specify the format.

PowerPoint remains the project's core presentation artifact. When the same pipeline is used for social cards or print pages, those are adjacent canvas outputs — not a redefinition of the project's presentation focus.

---

## Where PPT Master Is Not the Right Choice

Being honest about limitations:

| Limitation | Detail |
|---|---|
| **Setup required** | Install Python, clone repo, configure AI editor. Not a "open browser and go" experience. |
| **Slower generation** | 10–20 min for a 10-page deck (serial page-by-page for cross-slide consistency). SaaS tools take seconds. |
| **No collaboration** | Local files, no real-time co-editing, no share links. |
| **No full freeform canvas** | The browser live preview supports direct edits — select to change text/color/font/size, drag or arrow-key to reposition, with undo — plus click-to-annotate for AI rewrites. What it isn't is a full freeform canvas (a drag-anywhere visual editor): no on-canvas resize handles, and re-exporting to PPTX stays a chat step. |

**If you want zero-setup, instant slides in a browser** — a hosted SaaS tool is a better fit.

**If you want deep native PowerPoint output — masters and layouts, native shapes and connectors, data-backed charts and tables, gradients / patterns / shadows / glow, vector icons, transitions and entrance animation, speaker notes turned into voice narration and video, and template distillation on top — with predictable cost, local data, and no lock-in** — that's what PPT Master is built for.
