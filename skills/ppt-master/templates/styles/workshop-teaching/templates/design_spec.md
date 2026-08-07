---
style_id: workshop-teaching
kind: style
summary: Learn-by-doing training method that sequences objective, worked demonstration, practice, and honest checks for understanding.
keywords: [training, workshop, teaching, practice, onboarding]
---

# Workshop Teaching — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Workshop Teaching |
| Best Fit | Hands-on workshops, technical enablement, onboarding curricula, internal training, tutorials, and certification preparation |
| Reusable Intent | Move learners from not being able to do something to doing it unaided, with the deck usable both live and as later self-study material |
| Sources | Authored in-repo as a bundled reference Style, 2026-08-07; distilled from instructional-design practice, not a single external document |

## II. Communication Method

- **Preferred Mode**: instructional
- **Argument Flow**: State what the learner will be able to do, establish the minimum concept needed to attempt it, demonstrate it worked through completely, then hand it over for practice and check whether it landed. Introduce a concept at the moment it is needed to act, and let the size of each cycle follow task difficulty rather than a fixed lesson template.
- **Page Message Discipline**: Give each page one concept, one step, or one exercise, and title it by what the learner does or understands there. Keep an instruction and everything needed to follow it on the same page; never split a procedure so the learner must hold earlier steps from memory. Keep exercise pages visually distinct from teaching pages so a learner scanning later can find them.
- **Claim Discipline**: Keep rule, convention, recommendation, and personal preference distinct, and say which is which. Show the common mistake and why it is tempting rather than only the correct path, mark simplifications as simplifications, and name where the real thing is more complicated instead of leaving a false sense of completeness.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Learning objective | State what the learner will be able to do afterward | Express the outcome as an observable action, not as topic coverage | Keep the objective dominant and unadorned; it is a contract, not a chapter cover |
| Prerequisite and setup | Establish what must already be true before starting | List exact versions, access, and environment; make the verification step explicit | Keep the checklist scannable and its verification command or check unmistakable |
| Concept anchor | Give the minimum mental model required to act | Ground the concept in the task at hand; mark deliberate simplifications | Use one clarifying diagram or analogy rather than a full theoretical treatment |
| Worked demonstration | Show the task performed completely | Show every step including the unglamorous ones, with real input and real output | Keep step, action, and result visible together and preserve their order |
| Guided practice | Hand the task to the learner with support | State the task, the starting point, the success condition, and where to get unstuck | Make the instruction and success condition unmistakably separate from explanation |
| Common mistake | Prevent the error the learner is about to make | Show the wrong result and its actual cause, not a scolding | Place the incorrect and corrected states in direct correspondence |
| Reference card | Give something the learner returns to during and after | Keep exact syntax, names, and defaults; stay consistent with the demonstration | Allow high density under a strict grid, optimized for lookup rather than reading |
| Understanding check | Reveal whether it actually landed | Ask for application, not recall; make the correct answer verifiable by the learner | Keep the question dominant and any answer separated from the prompt |
| Recap and next step | Consolidate what was learned and where to go next | Tie each point back to the stated objective; name the next capability honestly | Mirror the objective structure so progress is visible |

## IV. Evidence & Data Expression

- **Argument Trace**: Every teaching page traces back to a stated learning objective and forward to something the learner does. Content that serves neither is cut rather than kept as background interest.
- **Charts**: Use charts to teach a relationship, not to impress. Build up a complex chart in stages instead of revealing it complete, label directly on the mark, keep units and scale explicit, and annotate what the learner should read from it. Never leave a chart whose takeaway is only spoken aloud.
- **Tables**: Use tables for syntax, parameters, options, and comparison of approaches. Keep one row shape, mark defaults and required fields, and order rows by teaching sequence or lookup convenience rather than internal implementation order.
- **Sources**: Cite versions, documentation, and standards next to the instruction they govern, and date anything that changes across releases. Distinguish official documented behavior from local convention or personal practice.
- **Native Editability**: Prefer editable native tables for reference cards and parameter lists so learners and later instructors can correct or extend them. Keep code, commands, and configuration as real selectable text rather than screenshots wherever the learner is expected to type or copy them.

## V. Visual System Defaults

- **Preferred Visual Style**: sketch-notes
- **Composition**: Build the page around the single action or idea it teaches, with a consistent place for the instruction and a consistent place for its result. Keep procedural order legible spatially — steps read in one direction and never wrap ambiguously. Preserve a stable page position for the recurring exercise and check regions so learners locate them without searching.
- **Density**: Keep teaching and practice pages light enough to follow while doing something else. Allow density only on reference cards, and keep even those legible at the rendered slide size and in print. Give a new concept its own page rather than compressing two into one.
- **Decoration**: Use hand-adjacent warmth — light annotation, arrows, circling, and margin marks — where it directs attention or shows relationship. Keep decoration functional: an arrow points at something specific, a highlight marks the part that changed. Avoid ornamental doodles, clip-art mascots, and decorative frames that crowd the working area.
- **Color Behavior**: Keep a light, calm field and assign color a teaching job: what is new, what changed, what is correct, what is wrong. Fix that mapping and reuse it throughout so a learner reads state without a legend. Ensure correct and incorrect remain distinguishable without relying on color alone. Any confirmed Brand or Deck identity replaces these tendencies.
- **Typography Character**: Use a warm, highly legible sans-serif with a genuinely monospaced companion for anything the learner types. Keep instruction text plain and generously spaced, keep code unwrapped and copyable in shape, and let weight and scale mark step boundaries instead of decorative containers. Exact families remain current-project or resolved identity decisions.

## VI. Image & Icon Direction

- **Preferred Image Rendering**: sketch-notes
- **Image Usage**: Use images where seeing the real thing prevents error — actual screens, real output, physical setup, or the state a learner should recognize. Prefer a clear explanatory drawing over a decorative photograph, and never illustrate a step with an image that does not show that step.
- **Image Treatment**: Crop to the region the learner acts on and keep interface text legible at the rendered slide size, magnifying the relevant detail rather than shrinking the full window. Mark the exact target with a consistent callout, keep screenshots current with the taught version, and caption what to look for. Avoid full-bleed atmospheric imagery and synthetic text inside generated images.
- **Icon Treatment**: Use one coherent icon family at consistent weight to mark recurring page kinds — demonstration, practice, warning, check — and keep each mapping fixed for the whole deck. Never rely on an icon alone to carry a safety-relevant warning. Avoid decorative icon grids and mixed icon languages.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- Each page teaches one thing, and its objective is identifiable at the rendered slide size.
- Every instruction is followable from the page alone, without recalling a previous page.
- Code, commands, and interface text remain legible at the rendered slide size and are not truncated.
- Exercise, warning, and check pages are visually distinguishable from teaching pages at a glance.
- Color meanings for new, changed, correct, and incorrect stay consistent and survive without color alone.
- Callouts point at the exact target rather than a general region.
- Reference pages stay dense but legible, with a lookup path that does not require reading in order.
