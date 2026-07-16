# Project Positioning and Capability Boundary

[English](./project-positioning.md) | [Chinese](./zh/project-positioning.md)

---

This document defines PPT Master's long-term product position and the test for adding, retaining, or removing capabilities. It is a product policy, not a feature list or execution manual.

This English file is the canonical policy source. The [Chinese version](./zh/project-positioning.md) is a synchronized translation, not an independent policy; update both in the same change.

[`workflows/routing.md`](../skills/ppt-master/workflows/routing.md) remains authoritative for current route selection. This document answers the more fundamental question: whether a proposed direction belongs in PPT Master at all.

## 1. Positioning

> **PPT Master is an open-source, chat-driven workflow that lets AI reason the argument into shape first, then design and produce a real, editable PowerPoint — not slide images or a thin editable skin. Its defining axis is native depth: author or preserve more of PowerPoint's own object model, behavior, and reusable structure, release after release.**

The input may be a topic, source material, data, design references, brand assets, or an existing `.pptx`. The main pipeline creates a new deck; other explicit routes and profiles can distill reusable Brand / Layout / Deck workspaces, fill an existing PowerPoint with new content, redesign it, or add native presentation behavior while preserving what their contracts promise to keep.

That native depth is a direction of travel, not a fixed checklist. PPT Master's north star is to keep converging with PowerPoint itself, narrowing the gap between what an AI can generate and what a skilled user can build by hand. The [PowerPoint ↔ SVG Mapping Guide](./powerpoint-svg-mapping.md) records the current boundary honestly, feature by feature.

In form, PPT Master is a workflow — a "skill" — that runs inside any agent-capable AI tool. It is not a model, a hosted presentation SaaS, or a replacement for PowerPoint. The workflow supplies presentation-specific reasoning, contracts, and quality gates; deterministic tools handle conversion, validation, packaging, and repeatable file operations; the chosen model still sets the quality ceiling.

The primary deliverable is a high-quality PowerPoint draft that the user can present and continue refining, not a sealed final deck. Reusable template workspaces, project sources, design specifications, previews, and validation artifacts are first-class supporting products because they make that deck controllable, reproducible, and reusable.

## 2. Product Thesis

A useful deck has two layers: the reasoning that makes the argument work, and the PowerPoint construction that makes the result usable. PPT Master owns both.

| Axis | Position | Product consequence |
|---|---|---|
| Logic first | Settle the core message, narrative mode, outline, hierarchy, and evidence before drawing slides | The deck's structure is reasoned about, not blindly inherited from source order |
| Native depth | Editability is table stakes; the real question is how much of PowerPoint the result actually contains | Author or preserve genuine PowerPoint shapes, text, pictures, charts, tables, slide masters and layouts, notes, transitions, animation, and package behavior where the selected route supports them |
| Honest editability | The output is a draft the user keeps editing, not a flattened image and not a promise of one-shot perfection | Trade-offs between visual fidelity, data-backed objects, cross-app rendering, and preservation stay explicit |
| User control | The workflow, project state, and output belong to the user | Costs remain transparent, data stays local apart from chosen provider calls, and no editor, model, or platform becomes mandatory |

Direct OOXML is too verbose and fragile to serve as the AI's general visual authoring language, while flat images throw away the native object model. PPT Master therefore combines model-friendly visual authoring with deterministic compilation and direct package operations, choosing the mutation contract that matches the user's intent.

The project's job is not merely to write a `.pptx`. It is to make a general-purpose AI agent competent and reliable at presentation work while preserving the user's ability to inspect, edit, and own the result.

## 3. Target Users and Usage Model

PPT Master is primarily for people who:

- Have a topic, documents, data, visual references, brand assets, or an existing deck that must become a presentation.
- Care about the logic of the deck and the depth of its PowerPoint editability, not merely whether the file opens as `.pptx`.
- Prefer coherent design and reliable delivery over instant generation.
- Need local project ownership, transparent costs, and freedom to choose an AI agent, model, and provider.
- Accept that the model sets the ceiling and are willing to review the direction and finish the last mile in PowerPoint when needed.
- Can use a chat-driven AI tool and a local Python environment, even if they do not write code themselves.

PPT Master is not optimized for users who primarily need zero-setup browser generation, instant slides, real-time team co-editing, or a guaranteed final deck with no human judgment or revision.

## 4. Product Promises

| Promise | Meaning | Boundary |
|---|---|---|
| Native depth | Author or preserve genuine PowerPoint objects, reusable structure, and presentation behavior where the selected route supports them | Never use whole-slide screenshots as the canonical generated PPTX; unsupported semantics and lossy trade-offs must be explicit |
| Logic before layout | Reason about the message, narrative, page order, and information hierarchy before visual authoring | A route whose contract is to preserve wording or structure must keep that promise instead of silently reframing the deck |
| A high-quality editable draft | Remove most of the work between raw material and a coherent, designed deck that remains open to refinement | Do not promise a perfect one-shot final; the model and user judgment still determine the ceiling |
| Source and intent fidelity | Keep sourced facts, user decisions, design recommendations, and derived artifacts distinguishable | Do not invent evidence or silently reinterpret a preservation request as redesign |
| Transparent, predictable cost | Keep PPT Master free and open source; the user pays only for the AI and optional providers they choose | Do not add proprietary credits, per-seat fees, or a presentation-platform subscription layer |
| Data stays local | Convert, author, validate, and export on the user's machine | AI model, search, image, and speech providers may still receive the inputs required for calls the user chooses |
| No platform lock-in | Let any agent-capable AI tool and compatible model drive the workflow, and keep outputs portable | Do not promise identical quality across models or identical rendering across presentation applications |
| Engineering reliability | Use explicit routes, preservation contracts, validation gates, read-back checks, and recoverable project state | Do not hide failures behind silent fallbacks or publish an artifact that violates a required gate |
| Quality over speed | Favor deck coherence, native editability, and delivery reliability over the fastest possible output | Improve efficiency where quality remains intact; do not make low-quality parallel generation the default |

## 5. Product Capability Model

The capability model is broader than one generation pipeline, but deliberately narrower than a general office agent.

| Capability domain | Responsibility |
|---|---|
| Presentation reasoning | Turn a topic or source bundle into an audience-aware message, narrative mode, outline, page plan, and explicit design direction |
| Native presentation authoring | Create new slide visuals and compile them into a real, natively editable PowerPoint deck |
| Reusable presentation design | Distill, create, combine, validate, and apply Brand, Layout, and Deck workspaces |
| Existing-deck adaptation | Redesign an existing deck, fill native slide shells with new content, or add native behaviors under distinct preservation contracts |
| PowerPoint expression | Use images, diagrams, charts, tables, formulas, notes, narration, transitions, and animation when they serve the communication goal |
| Review and delivery | Preview, inspect, validate, repair, export, read back, and retain enough local project state for later refinement or re-export |

These are product responsibilities, not a mandate to expose every responsibility as a top-level route or a separate workflow file. Routes exist only when inputs, mutation rules, invariants, or output lifecycles genuinely differ.

## 6. What the Project Owns Versus What It Integrates

PPT Master may integrate general-purpose capabilities without becoming a general-purpose platform for them.

| Area | PPT Master owns | PPT Master does not own |
|---|---|---|
| Research | Decide what evidence the deck needs, preserve provenance, and turn findings into presentation content | A general web-research engine for tasks unrelated to presentations |
| Images | Decide whether an image is needed and own its role, style, source, placement, provenance, and readiness | A universal image-generation or photo-management platform |
| Audio | Own speaker notes, voice choice in presentation context, per-slide narration, timing, and PowerPoint embedding | A general audio studio, podcast platform, or speech-provider marketplace |
| Data visualization | Choose the visual form, preserve values, validate geometry, and expose the editability / fidelity trade-off | A general business-intelligence or spreadsheet product |
| Templates and brands | Define reusable presentation identity, Master / Layout structure, slots, assets, and composition contracts | Recover historical design intent that is absent from the source file |
| PowerPoint editing | Own presentation-specific generation, filling, redesign, and scoped native enhancement | Replace the complete PowerPoint editing surface or support arbitrary OOXML mutation |

Provider diversity may be bundled to preserve openness and practical usability, but provider-specific behavior stays behind stable integration boundaries. The presentation workflow owns selection and output semantics; no individual provider should redefine the product boundary.

## 7. Stable Technical Strategy

The technical architecture serves the positioning; it is not the positioning itself.

- **Constrained SVG → DrawingML** is the primary authoring and compilation path for newly designed slides: the AI works in a model-friendly visual language, and deterministic tools build native PowerPoint objects.
- **Direct OOXML operations** preserve an existing PowerPoint package when that package — rather than a regenerated visual design — is the artifact the user wants to keep.
- **Template workspaces** declare reusable brand identity and, where applicable, Master / Layout, slot, and asset structure before new slides are authored; structure is not guessed after the fact.
- **Sidecars and package-level stages** own notes, narration, transitions, animation, and other presentation behavior that does not belong in static page SVG.
- **Project artifacts and validation gates** keep the process inspectable, resumable, testable, and safe to re-export.

The implementation may evolve, but these invariants remain stable:

1. Do not flatten the canonical generated deck into one image per slide.
2. Keep the complete visible page design in its declared authoring source; do not invent missing visuals during export.
3. Make native editability, visual fidelity, data-backed objects, and preservation trade-offs explicit.
4. Select an authoring or mutation contract before changing the artifact.
5. Keep source, authored, derived, and delivery artifacts distinguishable.
6. Fail closed when required semantics cannot be represented safely; do not claim unsupported fidelity or silently substitute another behavior.

## 8. Non-goals

PPT Master is not intended to become:

- A zero-setup, instant-slide browser SaaS.
- A fully autonomous replacement for human presentation judgment or a system that promises a perfect final deck in one shot.
- A general office assistant, research platform, image platform, audio platform, or provider marketplace.
- A complete PowerPoint clone, full freeform browser canvas, or real-time collaboration service.
- An arbitrary SVG-to-PPTX or arbitrary OOXML conversion service.
- A system that reconstructs missing historical Master / Layout intent from a finished PPTX or SVG.
- An in-place upgrader that grafts inferred template structure onto existing files.
- A speed-first generator that sacrifices deck coherence, native editability, or delivery reliability.

These non-goals do not forbid presentation-specific use of research, images, audio, native objects, or existing decks. They prevent supporting infrastructure from becoming an independent product with a different user promise.

## 9. Capability Admission and Reduction Test

Evaluate every proposed capability in this order:

1. **User job** — What real presentation task does it complete?
2. **Core contribution** — Does it deepen native PowerPoint output, improve presentation reasoning, strengthen user control, or make delivery more reliable?
3. **Owned result** — What presentation artifact, decision, or quality property does it create or protect?
4. **Invariant** — What must remain unchanged, and what is allowed to change?
5. **Product layer** — Is it a core capability, an integrated presentation extension, a replaceable provider adapter, or repository maintenance?
6. **Validation** — Can success and failure be checked without relying on a vague claim?
7. **Evidence** — Is there a real user need, repeated workflow, or demonstrated failure that justifies the maintenance cost?

| Decision | Use when |
|---|---|
| Add or retain as core | The capability directly advances the presentation job or strengthens native depth, reasoning, user control, or reliability, and requires presentation-specific contracts or validation |
| Retain as an integrated extension | The capability is optional, but its planning and output semantics are specific to presentations |
| Place behind a stable integration boundary | The underlying service is general-purpose or provider-specific, while PPT Master owns the presentation-specific selection and output contract |
| Move to repository tooling | The capability maintains the repository, examples, installation, or contributor workflow rather than creating presentations |
| Retire | It duplicates another authority, has no active consumer, makes an unverifiable promise, or adds more maintenance than presentation value |

The number of files or workflows is not itself a reason to add or remove a capability. The deciding factor is whether ownership and product value are clear.

## 10. North-Star Outcome

A successful PPT Master session should look like this:

> The user gives an AI agent a topic, source material, design references, a reusable template, or an existing PowerPoint. The AI reasons the argument into shape before it designs, the user confirms the choices that matter, and the workflow returns a coherent, validated PowerPoint with deep native editability, plus enough local project state to present, refine, reuse, or re-export it.

Future work should improve this outcome in the following priority order:

1. Native depth, output correctness, and delivery reliability.
2. Content reasoning, narrative quality, and visual coherence.
3. Reuse of brands, layouts, decks, and existing PowerPoint assets.
4. Human review, correction, and controlled iteration.
5. Additional formats, providers, and convenience features that strengthen the first four priorities.

## 11. Relationship to Other Documents

| Document | Responsibility |
|---|---|
| This document | Long-term product position, promises, capability boundary, and admission test |
| [`why-ppt-master.md`](./why-ppt-master.md) | User-facing differentiation and reasons to choose the project |
| [`technical-design.md`](./technical-design.md) | Current architecture and implementation invariants |
| [`workflows/routing.md`](../skills/ppt-master/workflows/routing.md) | Current executable route selection |
| [`roadmap.md`](./roadmap.md) | Shipped work, active priorities, and explicitly deferred directions |
