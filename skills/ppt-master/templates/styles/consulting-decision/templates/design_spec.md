---
style_id: consulting-decision
kind: style
summary: Answer-first, evidence-led decision-document method with restrained analytical design defaults.
keywords: [consulting, decision-support, answer-first, evidence, analytical]
---

# Consulting Decision — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Consulting Decision |
| Best Fit | Decision-oriented explanations, analytical reviews, recommendations, and evidence-heavy business documents |
| Reusable Intent | Make each page deliver a decision-relevant answer with traceable proof while leaving identity, geometry, and the current communication contract open to the project |
| Sources | [GitHub Issue #241](https://github.com/hugohe3/ppt-master/issues/241), opened 2026-07-22; reusable brief confirmed 2026-08-04 |

## II. Communication Method

- **Preferred Mode**: pyramid
- **Argument Flow**: Define the governing decision or question, the overall answer, its key supporting arguments, the evidence required for each argument, and any unresolved assumptions or evidence gaps. Maintain the trace `overall answer → key support → page message → evidence`; adapt the sequence to the current project instead of imposing a fixed roster.
- **Page Message Discipline**: For every planned page, identify one governing question, answer it through an assertion title or equally dominant message, and place the supporting proof visibly beneath or beside that answer. Use supporting subquestions only when their relationship matters; avoid topic-only titles.
- **Claim Discipline**: Keep facts, assumptions, implications, and recommendations semantically distinct. Cite facts, name uncertainty in assumptions, derive implications from visible evidence, and pair recommendations with their rationale and action. Keep recommendation and implication wording consistent across the deck; never promote an unsupported claim to a conclusion.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Executive synthesis | State the governing decision and overall answer | Show the few supports that make the answer credible and identify any material gap | Lead with the answer, then group proof by supporting argument |
| Recommendation | Specify the action and why it is preferable | Connect the action to diagnosis, expected effect, dependencies, and trade-offs | Keep the action dominant and its rationale visibly adjacent |
| Situation / complication / resolution | Establish context, surface the tension, and resolve the governing question | Distinguish observed conditions from the interpretation that creates the tension | Let the contrast between current reality and the answer carry the page |
| Driver decomposition | Explain what determines an outcome or decision | Use distinct supported branches; preserve real overlap or acknowledged gaps | Make the governing relationship primary and branches easy to compare |
| Current-state diagnosis | Identify the condition that matters and its causes | Separate observation from interpretation and tie each diagnosis to evidence | Pair each finding with the proof that establishes it |
| Comparison / benchmark | Clarify a decision through alternatives, peers, periods, or standards | State basis, units, period, and comparability; never invent a benchmark | Align comparable evidence and emphasize only decision-relevant differences |
| Process / operating model | Explain how work, ownership, or decisions flow | Show actors, handoffs, dependencies, controls, and failure points that the source supports | Prioritize causal or operational flow over decorative process art |
| Roadmap | Translate the recommendation into sequenced action | Connect phases to outcomes, dependencies, milestones, and decision gates | Make progression and ownership scannable without turning the page into a calendar ornament |
| Risk / mitigation | Expose uncertainty and the response it requires | Pair each risk with likelihood or trigger evidence, impact, mitigation, and owner when known | Keep risk and response in direct visual correspondence |
| Appendix / evidence | Preserve detail needed to audit or deepen the argument | Retain source, period, method, definitions, and limitations | Allow higher density while keeping the claim-to-source path legible |

## IV. Evidence & Data Expression

- **Argument Trace**: Every page message must trace back to one key support for the overall answer and forward to visible proof. Keep missing evidence or unresolved assumptions explicit instead of concealing the gap with confident wording.
- **Charts**: Choose the chart from the decision question and comparison logic. Use direct labels where practical, annotate the decision-relevant change, retain units and source lines, and remove legends, gridlines, effects, or chart furniture that do not aid interpretation. Separate observation from interpretation and never invent a baseline, peer, target, or trend.
- **Tables**: Derive columns and row groups from the comparison or decision logic. Align units and periods, preserve hierarchy, distinguish facts from assumptions, and emphasize only the differences that affect the answer. Use color only when it carries a declared meaning.
- **Sources**: Place citations close to the claim or data they support and retain source, period, scope, and measurement basis when available. Label estimates, proxies, and unresolved uncertainty; do not present unattributed or unsupported statements as facts.
- **Native Editability**: Prefer editable native charts, tables, and business shapes when the supported interface fits the intended object and editability is useful. Otherwise retain a legible editable shape-based representation rather than sacrificing fidelity or meaning.

## V. Visual System Defaults

- **Preferred Visual Style**: swiss-minimal
- **Composition**: Build the page around the message-to-proof relationship. Favor a few primary content regions—normally one to three—while allowing more when the argument genuinely needs them. Maintain one clear scan path, keep evidence dominant, and never detach a recommendation or implication into a decorative conclusion box that competes with its proof.
- **Density**: Support dense business material through concise assertions, disciplined alignment, compact but legible labels, and whitespace that separates reasoning layers. Let synthesis and recommendation pages breathe; let evidence and appendix pages tighten under a consistent grid without compressing below readable scale.
- **Decoration**: Use flat planes, hairline rules, restrained emphasis, and minimal elevation. Avoid ornamental cards, gradients, glows, decorative badges, and filled callout boxes that do not encode hierarchy, grouping, or evidence.
- **Color Behavior**: Start from a neutral field and reserve limited accents for semantic focus, change, risk, or recommendation. Use coherent tints for related series instead of rainbow coding. Any confirmed Brand or Deck identity replaces these tendencies; never imply a consultancy-specific or trademarked palette.
- **Typography Character**: Use a compact, authoritative sans-serif hierarchy suited to dense business documents across languages. Assertion titles are decisive, body text and annotations remain economical, and hierarchy comes from weight, scale, alignment, and spacing rather than ornamental containers. Exact families and locale coverage remain current-project or resolved identity decisions.

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
- Dense pages retain one clear scan path and do not hide overflow or structural ambiguity.
- No unsupported claim is presented as established evidence; unresolved gaps remain visible.
