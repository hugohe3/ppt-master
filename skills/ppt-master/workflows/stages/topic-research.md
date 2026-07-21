---
description: Generate Step 1 intake stage that fills externally verifiable factual gaps before Strategist confirmation.
---

# Topic Research Stage

> Strategist-owned factual preparation inside [`generate-pptx`](../generate-pptx.md) Step 1. Run immediately for topic-only input, or after supplied material is converted and read when it leaves planning-critical factual gaps. Output is a research supplement plus stable fact provenance for Step 2 import.

This stage supplies facts needed to plan the requested deck. It does not select, download, or generate images; image selection belongs to the final Strategist plan, and AI / web / slice acquisition runs in Generate Step 5 after final confirmation.

## When to Run

| Material state | Action |
|---|---|
| Topic or requirements with no supporting facts | Research the factual baseline needed for the requested outcome |
| Supplied files or chat content cover only part of the requested outcome | After conversion and reading, research only the identified externally verifiable gaps |
| Supplied material already supports the requested outcome | Skip this stage and continue Generate Step 1 |
| User requires a closed corpus, source-only transformation, or no external enrichment | Skip this stage and keep planning within supplied material |

**Sufficiency test**: a gap exists when the Strategist would otherwise need to invent, omit, or leave unsupported an externally verifiable claim required by the user's requested outcome. File presence, source length, and a generic topic taxonomy do not decide sufficiency.

**Hard rule — preserve supplied facts**: supplement the user's material; never silently replace it. Record a material source conflict for Strategist review instead of choosing a different claim without disclosure. Do not research omissions outside the requested scope.

---

## Step 1: Define the gap brief

⛔ **BLOCKING**: confirm only missing scope or research-boundary decisions as one bundled clarifier. Skip when the request and supplied material already make them clear.

| Item | Default if unspecified |
|---|---|
| Topic | From the user request |
| Requested scope / outcome | From the user request; otherwise broad overview |
| Supplied-material baseline | Facts and claims already available |
| Research gaps | Only facts needed to support the requested outcome |
| External-source boundary | External factual enrichment allowed; supplied facts remain authoritative inputs |
| Output language | Match user input |
| Target audience / communication intent | Use what is already explicit; leave final confirmation to the main Strategist stage |
| Research stem (`<research_slug>`) | `<topic_slug>_research`; choose another unused snake_case stem rather than overwrite an existing file |

Do not repeat the full main-pipeline confirmation here. Generate Step 4 still confirms the complete communication contract and deck solution after the factual inputs are ready.

---

## Step 2: Gather factual sources

Use the web search and fetch tools supplied by the current IDE. If none are available, pause and ask the user for authoritative URLs covering the declared gaps, then fetch each with:

```bash
python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <URL>
```

| Phase | Action |
|---|---|
| Orient | Search only far enough to map authoritative sources to the declared gaps |
| Deep fetch | Read the highest-signal primary or authoritative pages in full |
| Targeted fill | Search only for gaps still unsupported after those reads |

| Priority | Source |
|---|---|
| 1 | Primary sources, official sites, institutional releases, standards, or original research |
| 2 | Authoritative reference works and reputable academic sources |
| 3 | Reputable reporting or analysis when primary evidence is unavailable |
| Avoid | Unsourced reposts, unverifiable summaries, and stock-aggregator pages |

**Stop condition**: stop when every declared gap has enough sourced evidence for the Strategist to decide whether and how to include it. Do not expand into unrelated overview / history / outlook sections merely to make the research look complete.

---

## Step 3: Save the factual supplement

Write two artifacts under `projects/`:

| Artifact | Path |
|---|---|
| Research supplement | `projects/<research_slug>.md` |
| Fact provenance | `projects/<research_slug>.facts.json` |

**Hard rule — location and preservation**: write both files under `projects/`, never the repository root. Do not overwrite an existing user file; choose a new research stem instead. This stage creates no image folder.

Begin the research Markdown with a compact `## Research Brief` containing the supplied-material baseline, declared gaps, audience / intent already known, and requested outcome. Organize the body by gap, include concrete facts only, flag material conflicts, and end with `## Sources` listing every URL used.

Write every externally sourced claim that may enter the deck to `<research_slug>.facts.json` with a stable sequential ID, especially quantitative, date, ranking, attribution, and named-entity claims. Do not include user-supplied claims or invented scenario values. When no external claim is retained, write the schema with an empty `facts` array.

```json
{
  "schema": "ppt-master.fact-provenance.v1",
  "topic": "<topic>",
  "facts": [
    {
      "fact_id": "F001",
      "claim": "One concise, presentation-ready factual claim",
      "source_title": "Authoritative page title",
      "source_url": "https://example.org/source",
      "classification": "external",
      "retrieved_at": "YYYY-MM-DD"
    }
  ]
}
```

IDs are immutable within the file. Correct a claim under the same ID; never reuse a removed ID for a different fact. The research Markdown and provenance file must agree.

---

## Hand-off

Import the research supplement and provenance alongside any user-supplied sources in Generate Step 2:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources projects/<project_name> [<source_paths...>] projects/<research_slug>.md projects/<research_slug>.facts.json --move
```

The Research Brief remains evidence-facing context, not a locked presentation contract. Strategist reads all imported source material, then confirms the complete contract and decides the content, page roster, and image resource plan. Generate Step 5 acquires only the selected image rows after that confirmation.

```markdown
## ✅ Topic Research Complete
- [x] Research supplement: `projects/<research_slug>.md` (N declared gaps covered)
- [x] Fact provenance: `projects/<research_slug>.facts.json` (N external facts)
- [x] No images acquired before Strategist confirmation
- [ ] **Next**: return to [`generate-pptx`](../generate-pptx.md) Step 1, then import all source artifacts in Step 2
```
