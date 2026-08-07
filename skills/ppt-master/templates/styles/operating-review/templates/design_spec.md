---
style_id: operating-review
kind: style
summary: Recurring business-review method that separates result, variance, cause, and owned commitment without softening bad numbers.
keywords: [business-review, metrics, variance, operations, accountability]
---

# Operating Review — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Operating Review |
| Best Fit | Monthly and quarterly business reviews, operational performance readouts, program status reviews, and recurring metric reporting to an accountable audience |
| Reusable Intent | Let an audience that already knows the business see what happened, why it differs from plan, and what the owner will do — in the same shape every period, so periods can be compared |
| Sources | Authored in-repo as a bundled reference Style, 2026-08-07; distilled from operating-cadence reporting practice, not a single external document |

## II. Communication Method

- **Preferred Mode**: custom
- **Mode References**: briefing, pyramid
- **Mode Behavior**: Open at the level of a briefing — the period's results stated plainly, without preamble or rediscovery of context the audience already holds. Then resolve every material variance the way a pyramid resolves a question: the deviation, the cause that explains most of it, the evidence for that cause, and the committed response. Depth follows materiality, not agenda symmetry: a metric on plan gets a line, a metric off plan gets the full chain. Keep the page shape stable across periods so a returning audience compares rather than re-orients.
- **Argument Flow**: Report the period against plan, isolate what materially deviated, explain each deviation by cause rather than by narrative, and close every explanation with an owned action and a date. Cover on-plan areas briefly and spend the review on what changed; never let the sequence of business units substitute for the sequence of what matters.
- **Page Message Discipline**: For every page, state the result and its direction against plan in the title or an equally dominant line, and put the number that establishes it in view. Keep a metric, its variance, and its explanation on the same page. Never title a page with a metric name alone when the page exists because that metric moved.
- **Claim Discipline**: Keep actual, plan, forecast, and prior-period values explicitly labeled and never interchangeable. Separate what happened from why it happened and from what will be done; attribute a cause only with evidence and say "cause not yet established" when it is not. Report misses in the same voice and prominence as beats, and never restate a target retroactively to convert a miss into a hit.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Period scorecard | Show the whole period's standing at once | Give actual, plan, and variance for each headline metric with consistent units and period | Keep one glanceable field where status reads before any number is examined |
| Result against plan | Establish what a metric actually did | State value, plan, variance, and comparison basis; keep the definition identical to prior periods | Make the variance, not the raw value, the visually dominant fact |
| Trend and trajectory | Show whether the movement is direction or noise | Show enough history to judge normal variation; mark definition or scope changes on the series | Let the series carry the page and annotate only the decision-relevant point |
| Variance driver | Explain what accounts for the deviation | Decompose into drivers that sum honestly to the total; leave a named residual rather than forcing closure | Make the dominant driver visually primary and keep the decomposition auditable |
| Segment breakdown | Locate where the result is concentrated | Use consistent segment definitions across periods; disclose reclassification | Order by contribution and keep small segments visible rather than lumped without note |
| Exception and watch item | Surface what is off track or newly at risk | Pair each item with threshold, trigger, exposure, and owner | Keep exceptions in one predictable place; never scatter them into good news |
| Corrective action | State what will be done about the gap | Tie each action to a specific variance, an owner, a date, and an expected effect | Keep action, owner, and date in direct visual correspondence |
| Prior commitment status | Close the loop on what was promised last period | Report each prior action as done, in progress, or missed, with the same wording as when committed | Make the status verdict readable before the explanation |
| Forecast and assumption | State where the period ends up and on what basis | Name the assumptions the forecast depends on and what would invalidate them | Keep the assumption visible beside the number it produces |
| Supporting detail | Preserve the depth needed to interrogate a number | Retain definition, method, source system, period, and known data quality limits | Allow high density while keeping the number-to-source path traceable |

## IV. Evidence & Data Expression

- **Argument Trace**: Every stated result traces to a defined metric and source system, every explanation traces to evidence, and every action traces to the variance it addresses. Where a cause is asserted without evidence, label it as hypothesis; where data is incomplete, show the gap rather than the estimate alone.
- **Charts**: Choose the chart from the operating question: trend for direction, waterfall for variance decomposition, comparison for segments, distribution when averages conceal. Keep axis scale, period window, and metric definition identical to prior periods, show the plan or threshold line wherever variance is the point, and annotate the driver directly on the mark. Never truncate an axis to dramatize a movement, and never change scale between periods without saying so.
- **Tables**: Build the scorecard as a table with a fixed column contract — actual, plan, variance, prior period — and one row shape. Keep units, signs, and rounding consistent, mark restated or reclassified rows explicitly, and encode status in a declared, legible way rather than color alone. Avoid tables that hide the variance behind raw values.
- **Sources**: Attach metric definition, source system, extraction date, and period to the data it produces, and keep them stable across periods. Label estimates, preliminary figures, and anything subject to restatement, and note any definition change at the point of first appearance.
- **Native Editability**: Prefer editable native charts and tables for scorecards, trends, and variance data. Recurring reviews are refreshed rather than rebuilt, so keep the numbers and their structure editable in place instead of pasting a flattened image of a dashboard.

## V. Visual System Defaults

- **Preferred Visual Style**: data-journalism
- **Composition**: Build every page around the metric-to-variance-to-action relationship, and keep that arrangement identical across periods. Fix a stable position for the status region, the number region, and the commentary region so a returning audience reads by position. Give the scorecard one dominant field and let detail pages inherit its ordering.
- **Density**: Support genuinely dense operating data through disciplined alignment, consistent number formatting, and whitespace that separates result from explanation. Let the scorecard and the exception page breathe; let supporting detail tighten under one grid without dropping below readable scale or hiding rows.
- **Decoration**: Use flat planes, hairline rules, and restrained status marks. Every visual device earns its place by encoding status, grouping, or comparison. Avoid gauge ornaments, gradient KPI cards, glow, oversized arrows, and decorative dashboard chrome that mimics a product interface without carrying data.
- **Color Behavior**: Keep a neutral field and reserve color for declared status — on plan, watch, off plan — plus one accent for the metric under discussion. Fix the status mapping for the whole deck and every future period, and never apply a status color decoratively or to signal emphasis. Always pair status color with a shape, label, or position so it survives grayscale printing and color-vision differences. Any confirmed Brand or Deck identity replaces these tendencies.
- **Typography Character**: Use a compact, neutral sans-serif with genuinely tabular figures so columns of numbers align and periods compare by eye. Keep number formatting, sign convention, and unit placement identical throughout, keep commentary economical, and derive hierarchy from weight and alignment rather than containers. Exact families remain current-project or resolved identity decisions.

### Fallback Color Scheme

| Role | HEX | Purpose |
|---|---|---|
| Field | #FFFFFF | Neutral ground for dense reporting pages |
| Surface | #F4F6F8 | Grouped regions, table banding, and scorecard cells |
| Ink | #1E293B | Primary text, headline numbers, and rules |
| On plan | #2E7D5B | Metric meeting or exceeding its declared threshold |
| Watch | #B7791F | Metric within tolerance but trending toward a breach |
| Off plan | #B4342C | Metric breaching its declared threshold |
| Focus | #2B6CB0 | The metric or driver currently under discussion |

## VI. Image & Icon Direction

- **Preferred Image Rendering**: digital-dashboard
- **Image Usage**: Operating reviews are data documents; use imagery only where it is itself evidence — a site condition, a physical defect, a customer artifact, or a screen whose state is the finding. Never insert stock or atmospheric imagery to soften a bad period or fill a sparse page.
- **Image Treatment**: Crop to the evidentiary subject, keep any embedded numbers or interface text legible at the rendered slide size, and caption with date, location, and source. Present evidence images unretouched beyond cropping and exposure. Avoid decorative full-bleed treatment and synthetic text inside generated images.
- **Icon Treatment**: Use one coherent icon family at consistent weight, and only to mark status, direction, or a recurring item class. Keep each mapping fixed across periods and never let an icon alone carry a status that must survive printing. Avoid decorative icon grids, mixed icon languages, and directional icons whose meaning inverts between metrics where lower is better.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- Each page's result and its direction against plan are identifiable at the rendered slide size.
- Actual, plan, forecast, and prior-period values remain explicitly labeled and never visually interchangeable.
- Variance, not raw value, is the dominant fact wherever the page exists because something moved.
- Status color is consistent with its declared mapping and remains readable in grayscale and for color-vision differences.
- Axis scales, period windows, and metric definitions match prior periods, or the change is marked on the page.
- Numbers align in tabular columns with consistent units, signs, and rounding.
- Every corrective action shows its owner and date; misses are as prominent as beats.
