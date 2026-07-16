# Project Positioning and Capability Boundary

[English](./project-positioning.md) | [Chinese](./zh/project-positioning.md)

---

This document defines PPT Master's long-term product position and the decision framework for adding, retaining, or removing capabilities. It is not a feature list or an execution manual.

This English file is the canonical policy source. The
[Chinese version](./zh/project-positioning.md) is a synchronized translation,
not an independent policy; update both in the same change.

[`workflows/routing.md`](../skills/ppt-master/workflows/routing.md) remains authoritative for current route selection. This document answers a different question: whether a proposed direction belongs in PPT Master at all.

## 1. Positioning

> **PPT Master is an open-source, chat-driven presentation authoring framework for AI agents. It turns a topic, source material, design references, or an existing PowerPoint into high-quality, natively editable, locally owned PowerPoint artifacts through explicit authoring and preservation contracts.**

PPT Master is not a model, a presentation SaaS, or a replacement for PowerPoint. It is the harness between a general-purpose AI agent and the presentation domain: workflows provide professional judgment and operating discipline, while deterministic tools handle conversion, validation, packaging, and repeatable file operations.

The primary deliverable remains a PowerPoint file that the user can continue editing. Reusable template workspaces, project sources, design specifications, previews, and validation artifacts are first-class supporting products because they make the final deck controllable, reproducible, and reusable.

## 2. The Problem PPT Master Solves

Creating a useful presentation is not a single file-conversion operation. It requires several kinds of work that general AI systems and existing presentation tools rarely combine well.

| Problem | PPT Master's response |
|---|---|
| General AI can understand material but does not reliably construct complex PowerPoint files | Give the agent presentation-specific planning, design, authoring, and validation contracts |
| Visually ambitious AI outputs are often flattened images or browser documents | Compile a constrained visual authoring format into real PowerPoint objects instead of flattening whole slides |
| Direct OOXML generation is too verbose and fragile for visual authoring | Let the agent author in a model-friendly visual language, then use deterministic compilers and package validators |
| Source facts, narrative structure, visual design, assets, and delivery are usually disconnected steps | Maintain one project lifecycle with explicit artifact ownership and handoffs |
| Existing decks may need redesign, content replacement, design reuse, or behavior-only enhancement | Select a mutation model whose preservation contract matches the user's intent |
| Hosted presentation tools create cost, privacy, and platform lock-in | Keep the workflow open, local-first, model-independent, and agent-independent |

The project's job is therefore not merely to “write a `.pptx`.” Its job is to make a general AI agent competent and reliable at presentation work while preserving the user's ability to inspect, edit, and own the result.

## 3. Target Users and Usage Model

PPT Master is primarily for people who:

- Have a topic, documents, data, visual references, brand assets, or an existing deck that must become a presentation.
- Care about design quality and native editability more than instant generation.
- Need local project ownership, transparent costs, and freedom to choose an AI agent or model.
- Are willing to review the direction and refine the generated deck in PowerPoint when needed.
- Can use a chat-driven AI IDE and a local Python environment, even if they do not write code themselves.

PPT Master is not optimized for users who primarily need zero-configuration browser generation, real-time team co-editing, or a guaranteed final deck with no human judgment or revision.

## 4. Product Promises

| Promise | Meaning | Boundary |
|---|---|---|
| Native editability | Preserve text, shapes, pictures, charts, tables, and presentation behaviors as real PowerPoint constructs where the selected route supports them | Do not use whole-slide screenshots as the canonical PPTX output; unsupported semantics must be explicit |
| High-quality starting point | Remove most of the work of turning raw material into a coherent, designed deck | Do not promise a perfect one-shot final; the model and user judgment still determine the ceiling |
| Source and intent fidelity | Keep sourced facts, user decisions, design recommendations, and derived artifacts distinguishable | Do not invent evidence or silently reinterpret a preservation request as redesign |
| User ownership | Keep artifacts local, portable, and usable outside one vendor's product | External model, search, image, or speech calls may still follow the user's chosen provider |
| Engineering reliability | Use explicit routes, contracts, validation gates, read-back checks, and recoverable project state | Do not hide failures behind silent fallbacks or publish an artifact that violates a required gate |
| Quality over speed | Favor coherent design, editability, and delivery reliability over the fastest possible output | Improve efficiency where quality remains intact; do not make low-quality parallel generation the default |

## 5. Product Capability Model

The capability model is broader than one generation pipeline, but narrower than a general office agent.

| Capability domain | Responsibility |
|---|---|
| Presentation understanding and planning | Convert a topic or source bundle into an audience-aware message, narrative structure, page plan, and explicit design direction |
| New presentation authoring | Create new slide visuals and compile them into a natively editable PowerPoint deck |
| Reusable presentation design systems | Create, combine, validate, and apply Brand, Layout, and Deck workspaces |
| Existing-deck adaptation | Redesign an existing deck, fill native slide shells with new content, or append native behaviors under distinct preservation contracts |
| Presentation expression | Use images, diagrams, charts, tables, formulas, notes, narration, transitions, and animation when they serve the communication goal |
| Review and delivery | Preview, inspect, validate, repair, export, read back, and preserve enough project state for later refinement or re-export |

These are product responsibilities, not a mandate to expose every responsibility as a top-level route or a separate workflow file. Routes exist only when inputs, mutation rules, invariants, or output lifecycles genuinely differ.

## 6. What the Project Owns Versus What It Integrates

PPT Master may rely on general-purpose capabilities without becoming a general-purpose platform for them.

| Area | PPT Master owns | PPT Master does not own |
|---|---|---|
| Research | Determining what evidence a deck needs, preserving provenance, and turning findings into presentation content | A general web research engine for tasks unrelated to presentations |
| Images | Deciding whether an image is needed, its role, style, source, placement, provenance, and readiness | A universal image-generation or photo-management platform |
| Audio | Speaker notes, voice choice in presentation context, per-slide narration, timing, and PowerPoint embedding | A general audio studio, podcast platform, or speech-provider marketplace |
| Data visualization | Choosing the visual form, preserving values, validating geometry, and selecting the editability/fidelity trade-off | A general business-intelligence or spreadsheet product |
| Templates and brands | Explicit reusable presentation identity, layout, Master/Layout, slot, asset, and composition contracts | Recovering historical design intent that is absent from a source file |
| PowerPoint editing | Presentation-specific generation, filling, redesign, and scoped native enhancement | Replacing the complete PowerPoint editing surface or supporting arbitrary OOXML mutation |

Provider diversity may be bundled to preserve openness and practical usability, but provider-specific behavior should remain behind stable integration boundaries. The presentation workflow owns selection and output semantics; no individual provider should redefine the product boundary.

## 7. Stable Technical Strategy

The technical architecture serves the positioning; it is not the positioning itself.

- **Constrained SVG to DrawingML** is the primary authoring and compilation path for newly designed slides.
- **Direct OOXML operations** are preservation paths for cases where the existing PowerPoint package is the artifact to keep.
- **Template workspaces** declare reusable design structure before new slides are authored; structure is not inferred after the fact.
- **Project artifacts and validation gates** make the process inspectable, resumable, and testable.

The implementation may evolve, but five invariants should remain stable:

1. Do not flatten the canonical deck into one image per slide.
2. Make editability, visual fidelity, and preservation trade-offs explicit.
3. Select an authoring or mutation contract before changing the artifact.
4. Keep source, author, derived, and delivery artifacts distinguishable.
5. Fail closed when required semantics cannot be represented safely; do not claim unsupported fidelity.

## 8. Non-goals

PPT Master is not intended to become:

- A fully autonomous replacement for human presentation judgment.
- A general office assistant, research platform, image platform, or audio platform.
- A complete PowerPoint clone, full browser-canvas editor, real-time collaboration service, or presentation SaaS.
- An arbitrary SVG-to-PPTX or arbitrary OOXML conversion service.
- A system that reconstructs missing historical Master/Layout intent from a finished PPTX or SVG.
- An in-place upgrader that grafts inferred template structure onto existing files.
- A speed-first generator that sacrifices deck coherence or output reliability.

These non-goals do not forbid presentation-specific use of research, images, audio, native objects, or existing decks. They prevent supporting infrastructure from becoming an independent product with a different user promise.

## 9. Capability Admission and Reduction Test

Evaluate every proposed capability in this order:

1. **User job** — What real presentation task does it complete?
2. **Owned result** — What presentation artifact, decision, or quality property does it create or protect?
3. **Invariant** — What must remain unchanged, and what is allowed to change?
4. **Product layer** — Is it a core capability, an integrated presentation extension, a replaceable provider adapter, or repository maintenance?
5. **Validation** — Can success and failure be checked without relying on a vague claim?
6. **Evidence** — Is there a real user need, repeated workflow, or demonstrated failure that justifies the maintenance cost?

| Decision | Use when |
|---|---|
| Add or retain as core | The capability directly completes a presentation job and requires presentation-specific contracts or validation |
| Retain as an integrated extension | The capability is optional, but its planning and output semantics are specific to presentations |
| Place behind a stable integration boundary | The underlying service is general-purpose or provider-specific, while PPT Master owns the presentation-specific selection and output contract |
| Move to repository tooling | The capability maintains the repository, examples, installation, or contributor workflow rather than creating presentations |
| Retire | It duplicates another authority, has no active consumer, makes an unverifiable promise, or adds more maintenance than presentation value |

The number of files or workflows is not itself a reason to add or remove a capability. The deciding factor is whether ownership and product value are clear.

## 10. North-Star Outcome

A successful PPT Master session should look like this:

> The user gives an AI agent a topic, source material, design references, a reusable template, or an existing PowerPoint; confirms the important content and design choices; and receives a coherent, natively editable, validated PowerPoint artifact plus enough local project state to review, refine, reuse, or re-export it.

Future work should improve this outcome in the following priority order:

1. Output correctness, native editability, and delivery reliability.
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
