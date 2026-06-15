# Mode: instructional

Teaching-led exposition. Decompose a concept into ordered, digestible parts and build understanding step by step. For training, tutorials, explainers, onboarding, science / knowledge sharing.

---

## 1. Narrative skeleton

**Decompose, then sequence**: break the subject into parts and present them in a deliberate order (simple → complex, prerequisite → dependent, overview → detail).

**One concept per page**: each page teaches a single idea well; do not stack unrelated concepts.

**Parallel exposition**: sibling concepts get parallel structure — same shape, same depth — so the audience can compare and map them.

**Show, then tell**: lead with a concrete example or analogy, then state the principle. A worked example beats an abstract definition.

**Signpost**: orient the learner — what we covered, what comes next.

Titles state what the page teaches ("How attention weights are computed") — clear over clever.

---

## 2. Page-structure tendencies

- Numbered steps / ordered flows for processes; parallel cards for sibling concepts.
- Diagrams that build incrementally; annotate the part currently being explained.
- A concrete example anchors each abstract point.

> Step / flow / diagram geometry lives in [`templates/charts/`](../../templates/charts/); this mode decides *the learning order and granularity*.

---

## 3. Speaker-notes register

Patient, explanatory. Define before using; analogy then principle. Anticipate the learner's question and answer it. Steady pace; signpost transitions ("now that we have X, we can ask Y"). Conversational data. (Common framework: [`executor-base.md §8`](../executor-base.md).)

---

## 4. Page skeleton example

```
Title:  "Step 2 — Scoring each token against the query"
Body:   concrete example (3 tokens) → the rule it illustrates → one diagram
Notes:  "Remember the query from the last page? Here's what it does next…"
```
