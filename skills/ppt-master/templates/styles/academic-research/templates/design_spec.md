---
style_id: academic-research
kind: style
summary: Research-reporting method that builds a defensible claim from question, method, and result while keeping limitations visible.
keywords: [academic, research, thesis-defense, methodology, peer-review]
---

# Academic Research — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Academic Research |
| Best Fit | Thesis proposals and defenses, conference talks, lab meetings, grant and funding reviews, and research seminars |
| Reusable Intent | Let a skeptical, domain-literate audience judge whether the conclusion is earned — by seeing the question, the method, the actual result, and what the work does not establish |
| Sources | Authored in-repo as a bundled reference Style, 2026-08-07; distilled from research-presentation practice, not a single external document |

## II. Communication Method

- **Preferred Mode**: custom
- **Mode References**: instructional, pyramid
- **Mode Behavior**: Build the argument in the constructive order a research audience expects — question, prior work, approach, result, interpretation — because a conclusion stated before its method cannot be evaluated. Within that order, hold every claim to a pyramid's discipline: each conclusion resolves to the specific results that support it, and each result to the method that produced it. When time is short, compress the middle rather than inverting the order; the audience must still be able to trace conclusion back to evidence.
- **Argument Flow**: Establish the question and why it matters and remains open, position it against what is already known, make the approach reproducible enough to be judged, present results as observed rather than as desired, then interpret within stated limits. Sequence follows the logic of the work, not a required section roster; exploratory, confirmatory, and negative results each keep their own honest shape.
- **Page Message Discipline**: Give each page one finding, one method component, or one comparison, and title it with what it establishes rather than with a section label. Keep a figure and the claim it supports on the same page, and state the claim in words the audience can check against the figure. Never leave a result page whose takeaway exists only in narration.
- **Claim Discipline**: Keep observation, inference, hypothesis, and speculation distinct in wording and never let one drift into another across the talk. Report effect size with uncertainty rather than significance alone, state sample, condition, and analysis choices where they affect the reading, and present negative or null results without rhetorical softening. Distinguish correlation from cause explicitly, credit prior work precisely, and keep limitations in the talk rather than only in the paper.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Research question | Establish what is being asked and why it remains open | Show the gap concretely from prior work, not as a rhetorical premise | Keep the question dominant; one page, one question |
| Prior work positioning | Locate the contribution among what already exists | Represent prior work accurately, including where it succeeds; cite precisely | Organize by relationship to this work rather than chronologically |
| Contribution claim | State plainly what this work adds | Scope the claim to what the results actually support | Keep the claim isolated and unqualified by decoration; it will be quoted |
| Approach and method | Make the work judgeable and reproducible | Give the design, data, parameters, and choices that affect the result | Favor one clear schematic of the pipeline over dense procedural prose |
| Data and materials | Establish what the work was performed on | State provenance, size, collection, inclusion criteria, and known bias | Keep the descriptive facts scannable and the limitation visible, not buried |
| Result | Present what was actually observed | Show the data with uncertainty; do not present the summary alone | Let the figure dominate and state the reading in one line beside it |
| Comparison and ablation | Show what the result is relative to | Use fair baselines under matched conditions; report what was tuned | Align conditions on shared axes and mark the decisive difference |
| Interpretation | Say what the result means | Separate what follows from the data from what the authors believe | Keep interpretation visually distinct from the result it interprets |
| Limitation and threat | State what the work does not establish | Name real threats to validity and their direction, not ritual disclaimers | Give limitations a real page rather than a trailing bullet |
| Conclusion and future work | Close the question and point onward | Restate only what the evidence supports; keep future work honest about difficulty | Mirror the question page so the arc closes visibly |
| Supplementary detail | Hold material for questions and scrutiny | Retain full parameters, derivations, additional conditions, and sources | Allow high density; optimize for retrieval during questions |

## IV. Evidence & Data Expression

- **Argument Trace**: Every conclusion traces to specific results, every result to a stated method, and every method choice to a reason. Where the chain breaks, say so on the page rather than letting the narrative bridge it.
- **Charts**: Show the data, not only its summary — distributions, individual points, or error structure where the sample allows. Always display uncertainty for estimated quantities and state what the interval represents. Keep axes honest and consistently scaled across compared panels, label log scales prominently, and annotate the specific comparison the claim rests on. Never truncate an axis, hide outliers, or select a subset without saying so.
- **Tables**: Use tables for parameters, dataset characteristics, and quantitative comparisons. Report uncertainty alongside every estimate, keep units and precision consistent, mark which figures come from prior work and which are reproduced here, and never bold a winning row without stating the comparison basis.
- **Sources**: Cite on the page where a claim, figure, dataset, or method appears, in a form the audience can resolve. Reproduce or adapt others' figures only with attribution, mark adaptations as such, and state funding or competing interests where they bear on interpretation.
- **Native Editability**: Prefer editable native charts and tables where the presentation itself carries the data, so numbers can be corrected before submission or defense. Figures produced by the analysis pipeline are evidence and belong here at their original fidelity — import them rather than redrawing them by hand, since a redrawn figure is no longer the result. Producing publication figures is outside this style's scope.

## V. Visual System Defaults

- **Preferred Visual Style**: swiss-minimal
- **Composition**: Build each page around one figure or one claim, with the reading of that figure placed immediately beside or beneath it. Keep a stable position for the claim line so the audience learns where to look. Reserve multi-panel composition for genuine comparisons and keep panel order, scale, and labeling consistent across them.
- **Density**: Research audiences accept detail but not clutter. Keep result pages to what supports one claim and move exhaustive conditions to supplementary pages. Let question, contribution, and limitation pages breathe; allow supplementary pages to tighten under one grid while staying legible at the rendered slide size.
- **Decoration**: Effectively none. Hairline rules, restrained emphasis, and clear panel separation only. Avoid gradient backgrounds, three-dimensional chart effects, drop-shadowed boxes, institutional ornament repeated on every page, and any device that adds visual weight without adding information.
- **Color Behavior**: Start neutral and let color encode a declared variable — condition, group, or method — with the mapping fixed across every figure in the talk. Keep the same entity the same color everywhere, ensure categories remain distinguishable for color-vision differences and in grayscale print, and never use color for emphasis where it already carries data meaning. Any confirmed Brand or Deck identity replaces these tendencies.
- **Typography Character**: Use a plain, highly legible sans-serif with proper mathematical and symbol rendering, and consistent treatment of variables, units, and species or gene names per the field's convention. Keep figure labels at a size readable from the back of a lecture room rather than inherited from a print figure. Exact families remain current-project or resolved identity decisions.

## VI. Image & Icon Direction

- **Preferred Image Rendering**: flat
- **Image Usage**: Use images where they are evidence or apparatus — micrographs, captured phenomena, experimental setup, instrumentation, or field conditions. Use a schematic where a mechanism or pipeline must be understood. Never insert decorative or conceptual imagery to fill a research page.
- **Image Treatment**: Present evidence images unretouched beyond declared cropping, brightness, and contrast, and state any adjustment applied. Include a scale bar wherever magnification matters, keep panel labels and annotations legible at the rendered slide size, and caption with condition, source, and date. Avoid full-bleed atmospheric treatment and synthetic text inside generated images.
- **Icon Treatment**: Use icons sparingly, only to mark a recurring condition, instrument, or step class, with one coherent family and a mapping fixed across the talk. Never let an icon stand in for a quantity, and avoid icon grids and institutional decoration.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- Each result page states its claim in words that can be checked against the figure on the same page.
- Figure labels, axis text, and scale bars remain legible from the back of a lecture room, not only on a laptop.
- Uncertainty is shown wherever a quantity is estimated, and axes are neither truncated nor inconsistently scaled across compared panels.
- The color-to-condition mapping stays identical across every figure and survives grayscale and color-vision differences.
- Observation, inference, and speculation remain distinguishable in wording throughout.
- Limitations occupy a real page rather than a trailing bullet.
- Citations resolve on the page where the claim, figure, or dataset appears.
- Supplementary pages stay dense but retrievable under questioning.
