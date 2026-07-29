# Mode: instructional

Teaching-led exposition. Decompose a concept into ordered, digestible parts and build understanding step by step. For training, tutorials, explainers, onboarding, science / knowledge sharing.

---

## 1. Narrative skeleton

**Decompose, then sequence**: break the subject into parts and present them in a deliberate order (simple → complex, prerequisite → dependent, overview → detail).

**Focused learning unit**: center each page on a coherent teaching step; related concepts may share a page when their relationship is what the learner needs to understand.

**Parallel exposition**: sibling concepts get parallel structure — same shape, same depth — so the audience can compare and map them.

**Ground abstraction**: use a concrete example or analogy when it clarifies the principle; sequence example and explanation according to the learner's prerequisite needs.

**Signpost**: orient the learner — what we covered, what comes next.

Titles state what the page teaches ("How attention weights are computed") — clear over clever.

---

## 2. Page-structure tendencies

- Numbered steps / ordered flows for processes; parallel cards for sibling concepts.
- Diagrams that build incrementally; annotate the part currently being explained.
- Concrete examples anchor abstract points when they improve transfer or comprehension.

> Step / flow / diagram geometry lives in [`templates/charts/`](../../templates/charts/); this mode decides *the learning order and granularity*.

---

## 3. Speaker-notes register

Patient, explanatory. Define before using; analogy then principle. Anticipate the learner's question and answer it. Steady pace; signpost transitions ("now that we have X, we can ask Y"). Conversational data. (Common framework: [`executor-notes.md`](../executor-notes.md) §1.)

---

## 4. Page skeleton example

```
Title:  "Step 2 — Scoring each token against the query"
Body:   concrete example (3 tokens) → the rule it illustrates → one diagram
Notes:  "Remember the query from the last page? Here's what it does next…"
```
