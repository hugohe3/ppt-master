---
description: Generate source-intake stage that fills externally verifiable factual gaps before planning or direct SVG authoring.
---

# Topic Research Stage

> Factual preparation inside [`generate-pptx`](../generate-pptx.md) source intake. Default Generate hands its output to Strategist; Quick Generate's main agent consumes the same output. Run immediately for topic-only input, or after supplied material is converted and read when it leaves planning-critical factual gaps. Output is a research supplement plus stable fact provenance for project import.

This stage supplies facts needed to build the requested deck. It does not select,
download, or generate images. Default Generate resolves image selection in the
final Strategist plan and acquires AI / web / slice assets after confirmation;
Quick Generate resolves and acquires them later in its resource-preparation
phase without adding a confirmation gate.

## When to Run

| Material state | Action |
|---|---|
| Topic or requirements with no supporting facts | Research the factual baseline needed for the requested outcome |
| Supplied files or chat content cover only part of the requested outcome | After conversion and reading, research only the identified externally verifiable gaps |
| Supplied material already supports the requested outcome | Skip this stage and continue Generate Step 1 |
| User requires a closed corpus, source-only transformation, or no external enrichment | Skip this stage and keep planning within supplied material |

**Sufficiency test**: a gap exists when the active content owner would otherwise need to invent, omit, or leave unsupported an externally verifiable claim required by the user's requested outcome. File presence, source length, and a generic topic taxonomy do not decide sufficiency.

**Hard rule — preserve supplied facts**: supplement the user's material; never
silently replace it. Record a material source conflict in the research output
for the active content owner instead of choosing a different claim without
disclosure. Do not research omissions outside the requested scope.

---

## Step 1: Define the gap brief

**Clarification boundary**: Default Generate bundles only genuinely missing
scope or research-boundary decisions into one clarifier. Quick Generate applies
the defaults below and continues without interaction; stop only when a required
permission or safety boundary cannot be inferred responsibly. Skip clarification
when the request and supplied material are already clear.

| Item | Default if unspecified |
|---|---|
| Topic | From the user request |
| Requested scope / outcome | From the user request; otherwise broad overview |
| Supplied-material baseline | Facts and claims already available |
| Research gaps | Only facts needed to support the requested outcome |
| External-source boundary | External factual enrichment allowed; supplied facts remain authoritative inputs |
| Output language | Match user input |
| Target audience / communication intent | Use what is explicit; Default leaves final confirmation to Strategist, while Quick resolves routine gaps in active context |
| Research stem (`<research_slug>`) | `<topic_slug>_research`; choose another unused snake_case stem rather than overwrite an existing file |

Do not repeat the full default-pipeline confirmation here. Default Generate
confirms the complete communication contract in Step 4; Quick Generate adds no
confirmation stage.

---

## Execution Context

**Default — isolated research when available**: The main agent owns the sufficiency decision and gap brief. When the current AI editor supports and permits an isolated subagent with web/fetch access and write access to the declared outputs, dispatch exactly one research worker. Otherwise the main agent runs Steps 2–3 locally.

| Actor | Contract |
|---|---|
| Main agent | Supply the topic/outcome, baseline or relevant source paths, declared gaps, output language, two exact unused output paths, and this stage's absolute path as execution authority; use paths instead of pasting source bodies when possible |
| Research worker | Read the supplied stage file completely, then follow Steps 2–3 using the brief and declared source paths as its baseline; limit project writes to the two output artifacts; acquire no images and make no deck-planning or design decisions |

**Hard rule — isolated hand-off**: Raw page content and fetch transcripts stay in the worker context. In at most 250 words, return only `status`, exact artifact paths, covered/unresolved gap counts, external-fact count, and material conflicts; do not return page excerpts or duplicate the research narrative in chat. The two saved artifacts are the hand-off.

**Validation**: Before import, the main agent verifies both exact files exist, the Markdown contains `## Research Brief` and `## Sources`, the JSON parses with schema `ppt-master.fact-provenance.v1` and unique sequential IDs, and the two files agree. Return an invalid pair to the research worker for owning-artifact repair; use main-context web research only when isolated execution is unavailable.

---

## Step 2: Gather factual sources

Use the web search and fetch tools available in the active research context. An isolated worker without them returns `blocked: web-tools-unavailable`. If no usable research context has search/fetch tools, the main agent pauses and asks the user for authoritative URLs covering the declared gaps, then fetches each with:

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

**Stop condition**: stop when every declared gap has enough sourced evidence for
the active content owner to decide whether and how to include it. Do not expand
into unrelated overview / history / outlook sections merely to make the
research look complete.

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
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources projects/<project_name> [<source_paths...>] projects/<research_slug>.md projects/<research_slug>.facts.json
```

The Research Brief remains evidence-facing context, not a locked presentation
contract. Default Generate has Strategist read the imported material, confirm
the complete contract, and select the content, page roster, and image resource
plan before Step 5 acquisition. Quick Generate has the current agent read the
same facts, decide those routine details in active context, and continue to its
resource-preparation phase.

```markdown
## ✅ Topic Research Complete
- [x] Research execution: <isolated worker | main-context fallback>
- [x] Research supplement: `projects/<research_slug>.md` (N declared gaps covered)
- [x] Fact provenance: `projects/<research_slug>.facts.json` (N external facts)
- [x] Artifact contract validated: `## Research Brief`, `## Sources`, `ppt-master.fact-provenance.v1`, unique sequential IDs, and Markdown/JSON agreement
- [x] No images acquired inside this factual-research stage
- [ ] **Next**: return to [`generate-pptx`](../generate-pptx.md) Step 1, then import all source artifacts in Step 2
```
