---
style_id: incident-postmortem
kind: style
summary: Blameless incident review method that reconstructs a timeline, separates contributing factors from blame, and commits to verifiable actions.
keywords: [postmortem, incident, reliability, root-cause, blameless]
---

# Incident Postmortem — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Incident Postmortem |
| Best Fit | Production incident reviews, outage reports, quality and safety investigations, security event debriefs, and reliability retrospectives |
| Reusable Intent | Let an organization learn from a failure — what happened, what allowed it, and what will change — without the account bending toward defending anyone |
| Sources | Authored in-repo as a bundled reference Style, 2026-08-07; distilled from blameless-postmortem practice, not a single external document |

## II. Communication Method

- **Preferred Mode**: briefing
- **Argument Flow**: State what happened and what it cost, reconstruct the timeline from detection through recovery, examine what allowed the failure to occur and to persist undetected, then commit to changes that address those conditions. Facts before interpretation, and interpretation before action; depth follows severity rather than a fixed report template.
- **Page Message Discipline**: Give each page one fact, one factor, or one action, and title it with what it establishes. Keep every timeline entry with its timestamp, source, and time zone. Never mix the reconstruction of what happened with the judgment of what should have happened on the same page — the audience must be able to accept the facts before weighing the analysis.
- **Claim Discipline**: Keep observed event, inferred sequence, contributing factor, and hypothesis distinct at all times, and mark anything unconfirmed as unconfirmed. Describe what people knew and saw at each moment rather than what hindsight makes obvious, and attribute outcomes to conditions and systems rather than to individuals — name roles and systems, not people at fault. Report actual impact rather than the estimate that best protects the team, and never close a factor as resolved when the underlying condition remains.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Incident summary | Give the whole event in one reading | State severity, duration, scope, and impact with the same numbers used everywhere else | One glanceable page; it will be quoted and forwarded on its own |
| Impact assessment | Establish what it actually cost | Quantify affected users, transactions, data, revenue, or safety exposure with measurement basis | Keep the measured impact dominant; state uncertainty rather than rounding to comfort |
| Timeline | Reconstruct what happened in order | Give timestamps with time zone and source for detection, escalation, mitigation, and recovery | Let chronology drive the composition; keep the detection and mitigation gaps visible |
| Detection and alerting | Show how and when it became known | State what alerted, what did not, and how long it took to reach someone who could act | Make the detection delay legible rather than folded into the timeline |
| Response and mitigation | Show what was done and what worked | Distinguish actions that helped, had no effect, or worsened the situation, with the information available at the time | Keep decision points visible with what was known at each |
| Contributing factors | Explain what allowed the failure | Give multiple factors — technical, procedural, and organizational — without collapsing to a single cause | Show how factors combined; resist a single-box root-cause diagram when reality was layered |
| Systemic condition | Identify what makes recurrence likely | Connect the incident to conditions that persist beyond it, including prior similar events | Keep the condition primary over the specific trigger that happened to fire |
| What went well | Preserve what should be protected | Name the controls, practices, and decisions that limited the damage | Give it real space; a review that only lists failures teaches the wrong lesson |
| Corrective action | Commit to verifiable change | Give owner, date, verification method, and the factor it addresses; distinguish prevention from detection from mitigation | Keep action, owner, and verification in direct correspondence |
| Open question | Preserve what remains unknown | State what could not be determined and what evidence would settle it | Keep unknowns visible rather than resolving them with plausible narrative |
| Supporting evidence | Hold the material the review rests on | Retain logs, graphs, configurations, and traces with timestamps and sources | High density; organized for verification rather than for reading in order |

## IV. Evidence & Data Expression

- **Argument Trace**: Every timeline entry traces to a log, alert, message, ticket, or human account with its source named. Every contributing factor traces to timeline evidence, and every action traces to a factor. Where the account depends on recollection rather than record, mark it as such.
- **Charts**: Use time-series charts aligned to the same clock and time zone as the timeline, with detection, escalation, mitigation, and recovery marked on the axis. Show enough pre-incident history to establish normal behavior, keep scales unbroken, and annotate what each deviation corresponds to. Never crop a window so the anomaly looks smaller or the recovery looks faster than it was.
- **Tables**: Use tables for the timeline, impact breakdown, and action commitments. Keep one row shape, give the timeline consistent timestamp precision and a stated time zone, and record each action with owner, date, verification, and the factor it addresses. Mark estimated impact figures explicitly.
- **Sources**: Attach system, query, and retrieval time to every log excerpt, metric, or graph. State the time zone once, prominently, and use it consistently. Distinguish automated record from human recollection, and note where evidence was lost, rotated, or unavailable.
- **Native Editability**: Prefer editable native tables for timeline and action commitments, since these are tracked and updated after the review closes. Keep monitoring graphs and log excerpts as captured evidence at original fidelity rather than redrawing them; a redrawn graph is no longer the record.

## V. Visual System Defaults

- **Preferred Visual Style**: swiss-minimal
- **Composition**: Build each page around one fact and keep the timeline's spatial direction consistent wherever it recurs. Fix a stable position for timestamp, event, and source so entries are compared by eye. Give the summary, systemic condition, and action pages room; let evidence pages carry density under one grid.
- **Density**: The document is read after the meeting by people who were not there, so pages must stand alone. Keep the summary and factor pages readable at a glance and let timeline and evidence pages hold real detail without hiding entries or truncating identifiers.
- **Decoration**: Effectively none. This is a factual record; visual restraint is part of its credibility. Use hairline rules, clear separation, and consistent marks only. Avoid alarm graphics, dramatic red gradients, warning ornament, and any device that adds emotional weight to a page that should carry evidence.
- **Color Behavior**: Keep a neutral field and reserve color for declared severity and state, with the mapping fixed across the document and consistent with the organization's existing severity scale where one exists. Always pair severity color with a label so it survives printing and color-vision differences. Never use color to signal fault or to emphasize a page rhetorically. Any confirmed Brand or Deck identity replaces these tendencies.
- **Typography Character**: Use a plain, neutral sans-serif with a genuinely monospaced companion for timestamps, identifiers, log excerpts, and commands. Keep timestamp precision and format identical throughout, keep log text unwrapped and legible, and derive hierarchy from weight and alignment rather than containers. Exact families remain current-project or resolved identity decisions.

### Fallback Color Scheme

| Role | HEX | Purpose |
|---|---|---|
| Field | #FFFFFF | Neutral ground for a factual record |
| Surface | #F2F4F6 | Grouped regions, timeline banding, and evidence blocks |
| Ink | #1F2933 | Primary text, timestamps, and rules |
| Normal | #4A5568 | Pre-incident baseline and unaffected state |
| Degraded | #B7791F | Partial impact, elevated risk, or detection gap |
| Critical | #B4342C | Full impact window and breached threshold |
| Recovered | #2E7D5B | Mitigation effective and service restored |

## VI. Image & Icon Direction

- **Preferred Image Rendering**: digital-dashboard
- **Image Usage**: Use images only as evidence — monitoring screens, alert states, error output, configuration, or physical conditions where relevant. Never insert conceptual or atmospheric imagery into an incident record.
- **Image Treatment**: Present captured evidence unaltered beyond cropping, with timestamps and axis labels left visible and legible at the rendered slide size. Redact only personal data or credentials, and mark every redaction. Caption with system, query, and time zone. Avoid full-bleed treatment and synthetic text inside generated images.
- **Icon Treatment**: Use icons sparingly, only to mark severity, state, or event class, with one coherent family and a fixed mapping. Never let an icon alone carry severity that must survive printing, and never use expressive or emotive icons in a factual record.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- The document stands alone for a reader who was not in the room.
- Timestamps carry consistent precision and a stated time zone wherever they appear.
- Detection, escalation, mitigation, and recovery points are visible on both the timeline and any aligned chart.
- Observed fact, inference, and unconfirmed hypothesis remain distinguishable throughout.
- The account describes what responders knew at each moment rather than what hindsight makes obvious, and attributes outcomes to systems and conditions rather than to named individuals.
- Severity color matches its declared mapping and remains readable with its label in grayscale.
- Log excerpts, identifiers, and graph axes are legible and untruncated.
- Every corrective action shows owner, date, verification method, and the factor it addresses.
