---
style_id: mbb-consulting
kind: style
summary: Strategy-document method in the MBB consulting convention — answer-first argument at document density with numbered exhibits, a key-message column, footnotes, and action titles on every page.
keywords: [consulting, strategy-document, MBB-style, document-density, exhibits]
---

# MBB Consulting — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | MBB Consulting |
| Best Fit | Strategy documents read at desk distance in the top-tier strategy-consulting convention: market and portfolio diagnoses, priority recommendations, board and management decision papers |
| Reusable Intent | Make each page deliver a decision-relevant answer with traceable proof at document density — several numbered exhibits, a key-message column, and footnoted sources per page — while leaving identity and the current communication contract open to the project |
| Sources | Method inherited from `consulting-decision` ([GitHub Issue #241](https://github.com/hugohe3/ppt-master/issues/241)); document-density page conventions confirmed 2026-09-05 from the EV market-priority deck (example `ppt169_ev_market_priorities`) |

## II. Communication Method

- **Preferred Mode**: pyramid
- **Argument Flow**: Define the governing decision or question, the overall answer, its key supporting arguments, the evidence required for each argument, and any unresolved assumptions or evidence gaps. Maintain the trace `overall answer → key support → page message → evidence`; adapt the sequence to the current project instead of imposing a fixed roster.
- **Page Message Discipline**: For every planned page, identify one governing question, answer it through an assertion title or equally dominant message, and place the supporting proof visibly beneath or beside that answer. Use supporting subquestions only when their relationship matters; avoid topic-only titles.
- **Claim Discipline**: Keep facts, assumptions, implications, and recommendations semantically distinct. Cite facts, name uncertainty in assumptions, derive implications from visible evidence, and pair recommendations with their rationale and action. Keep recommendation and implication wording consistent across the deck; never promote an unsupported claim to a conclusion.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Executive synthesis | State the governing decision and overall answer | Show the few supports that make the answer credible and identify any material gap | Numbered findings with page references stacked in the main column, an inference panel and a basis-numbers strip beneath them, and a dark decision-ask column at the right |
| Recommendation | Specify the action and why it is preferable | Connect the action to diagnosis, expected effect, dependencies, and trade-offs | A priority table with a tier column and evidence-page column, a totals strip, and a tier-meaning block beneath it |
| Situation / complication / resolution | Establish context, surface the tension, and resolve the governing question | Distinguish observed conditions from the interpretation that creates the tension | Let the contrast between current reality and the answer carry the page |
| Driver decomposition | Explain what determines an outcome or decision | Use distinct supported branches; preserve real overlap or acknowledged gaps | Make the governing relationship primary and branches easy to compare |
| Current-state diagnosis | Identify the condition that matters and its causes | Separate observation from interpretation and tie each diagnosis to evidence | Two numbered exhibits side by side, a third panel beneath them (compact comparison table, KPI strip, or note), and a key-message column ending in an implication panel |
| Comparison / benchmark | Clarify a decision through alternatives, peers, periods, or standards | State basis, units, period, and comparability; never invent a benchmark | Align comparable evidence and emphasize only decision-relevant differences |
| Process / operating model | Explain how work, ownership, or decisions flow | Show actors, handoffs, dependencies, controls, and failure points that the source supports | Prioritize causal or operational flow over decorative process art |
| Roadmap | Translate the recommendation into sequenced action | Connect phases to outcomes, dependencies, milestones, and decision gates | Stage chevrons across the top, an outputs row, tier lanes as a matrix, and a decision-gate box with dated thresholds at the bottom |
| Risk / mitigation | Expose uncertainty and the response it requires | Pair each risk with likelihood or trigger evidence, impact, mitigation, and owner when known | A risk register table (risk, trigger baseline → threshold, impact, response, monitoring data), a monitoring-cadence column, an implication panel, and a reference-values strip |
| Decision request | Ask for the decisions and name what happens without them | Show each ask with its rationale pages, the action within a fixed window, the owner, and the consequence of not deciding | Numbered asks in aligned columns (ask, action, owner, consequence) over a milestone strip and a review-date line |
| Appendix / evidence | Preserve detail needed to audit or deepen the argument | Retain source, period, method, definitions, and limitations | Full data tables as numbered exhibits, a calculation-method block, and a source-and-licence block with links |

## IV. Evidence & Data Expression

- **Argument Trace**: Every page message must trace back to one key support for the overall answer and forward to visible proof. Keep missing evidence or unresolved assumptions explicit instead of concealing the gap with confident wording.
- **Charts**: Choose the chart from the decision question and comparison logic. Number every exhibit (A, B, C) with a solid badge, a bold title stating what it shows, and a unit line; label every value directly, put deltas and multiples as companion text at bar ends or line ends, and omit gridlines and value axes. Annotate the decision-relevant change in the accent colour, retain units, and footnote each calculation. Separate observation from interpretation and never invent a baseline, peer, target, or trend.
- **Tables**: Derive columns and row groups from the comparison or decision logic. Align units and periods, preserve hierarchy, distinguish facts from assumptions, and emphasize only the differences that affect the answer. Compact comparison tables sit beneath exhibits as a third panel; full tables carry a tier or judgment column and an evidence-page column. Use color only when it carries a declared meaning.
- **Sources**: Number footnotes at the bottom-left of every page with the source line beneath them, and reference footnote numbers from titles, unit lines, and labels. Retain source, period, scope, and measurement basis; label estimates, proxies, scenario values, and computed values as such. Do not present unattributed or unsupported statements as facts.
- **Native Editability**: Prefer editable native charts, tables, and business shapes when the supported interface fits the intended object and editability is useful. Otherwise retain a legible editable shape-based representation rather than sacrificing fidelity or meaning.

## V. Visual System Defaults

- **Preferred Visual Style**: custom
- **Visual Style References**: swiss-minimal
- **Visual Style Behavior**: A strategy-document page, not a keynote slide. Every content page carries one fixed chrome: a two-line action title at the top-left with a hairline beneath it, a unit / exhibit-index line under the title, a section tracker and draft marker at the top-right, numbered footnotes with a source line at the bottom-left, and the page number at the bottom-right. Exhibits carry an A / B / C badge, a bold title, and a unit line; a right-hand column of numbered key messages closes with a tinted implication panel. The cover is the only dark full-bleed field; every other page is a white field ruled by hairlines, with no cards and no shadows.
- **Composition**: Fill each content page with five to seven distinct modules on one grid. The default diagnosis page is two exhibits side by side over a third full-width panel (compact comparison table, KPI strip with captions, or note block), plus the key-message column and its implication panel. Table pages pair the table with a totals strip and a meaning block; roadmap pages stack stage chevrons, an outputs row, tier lanes, and a decision gate; decision pages align ask, action, owner, and consequence columns over a milestone strip and a review line; the cover adds a document-structure strip and headline figures. Whitespace separates modules; it never stands in for a missing module.
- **Density**: Document density read at desk distance. On a 1280-px canvas: action titles near 24 px, body and key messages near 14 px, exhibit titles near 13 px, annotations and chart labels 11–12 px, footnotes 10 px. Each exhibit takes roughly a third of the page height; small tables use 18–22 px rows with hairline separators, a bold first column, right-aligned numerals, and one tinted band for the emphasized tier. Synthesis, roadmap, decision, and appendix pages keep the same chrome and density; only the cover drops below four modules.
- **Decoration**: Hairline rules and solid numbered badges are the only ornament. Implication and inference panels use a light-grey surface with a thin accent bar on the left edge; nothing else is boxed, shaded, or filled. Avoid cards, gradients, glows, decorative icons, and filled callouts.
- **Color Behavior**: One deep dominant carries titles, badges, primary series, and axes; one saturated accent marks the point of each exhibit (the emphasized bar, the priority tier, the highlighted figure, the implication bar); a light tint of the accent carries the secondary series; a grey ramp carries context, category labels, unit lines, and footnotes; one negative colour is reserved for declines and risk triggers. Tints of one family order series; never rainbow-code. Any confirmed Brand or Deck identity replaces these tendencies; never imply a consultancy-specific or trademarked palette.
- **Typography Character**: One compact sans-serif family for all editable text, with a lining-figure companion for numerals in charts, tables, KPI strips, and badges. Hierarchy comes from weight, size steps, letter-spaced small labels for trackers and column headers, and alignment — never from containers. Exact families and locale coverage remain current-project or resolved identity decisions.

### Fallback Color Scheme

| Role | HEX | Purpose |
|---|---|---|
| Field | #FFFFFF | Page field on every page except the cover |
| Dominant | #051C2C | Titles, badges, primary series, axes, and the cover field |
| Accent | #2251FF | The point of each exhibit: emphasized bar, priority tier, highlighted figure, implication bar |
| Accent tint | #8FB8FF | Secondary series and secondary text on the cover |
| Body | #333333 | Body copy, key messages, and table text |
| Muted | #7F7F7F | Category labels, unit lines, trackers, and footnotes |
| Hairline | #B7B7B7 | Axes and dividers |
| Grid | #E3E3E3 | Table row separators and dashed connectors |
| Surface | #F7F7F7 | Implication and inference panels, alternating lanes |
| Negative | #B3261E | Declines, negative deltas, and risk triggers |

### Fallback Typography

| Role | Primary | Fallback Tail | Character |
|---|---|---|---|
| Titles and body | Microsoft YaHei | Arial | Compact neutral sans; bold for action titles, exhibit titles, and badges |
| Numerals and data | Arial | Helvetica | Lining figures for chart labels, tables, KPI strips, page numbers |

## VI. Image & Icon Direction

- **Preferred Image Rendering**: minimalist-swiss
- **Image Usage**: Use images only when they provide evidence, necessary context, or a causal explanation that shapes the decision. Default to sparse imagery; keep data and business structures editable instead of replacing them with decorative illustrations.
- **Image Treatment**: Crop for the evidentiary subject, use restrained framing or a functional scrim, and retain a nearby caption or source when the image supports a claim. Avoid gratuitous full bleed, synthetic text inside images, and atmospheric imagery that weakens the argument.
- **Icon Treatment**: Use one coherent icon family with consistent stroke or fill treatment, only when an icon clarifies a role, state, or relationship. Avoid logos, consultancy-specific marks, decorative icon grids, and mixed visual languages; actual icon selection remains a project decision.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- The intended answer is identifiable quickly at the rendered slide size.
- The governing question is actually answered rather than repeated as a topic.
- Visible evidence supports the message and is spatially connected to it.
- Facts, assumptions, implications, and recommendations remain distinguishable and semantically consistent.
- Direct labels, sources, hierarchy, and annotations remain legible at the rendered slide size.
- Every content page shows five to seven modules: numbered exhibits with unit lines, a key-message column with an implication panel, numbered footnotes, and a source line.
- Dense pages retain one clear scan path and do not hide overflow or structural ambiguity.
- No unsupported claim is presented as established evidence; unresolved gaps remain visible.
