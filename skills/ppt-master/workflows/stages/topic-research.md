---
description: Generate source-intake stage that fills factual gaps and records adopted webpage provenance before planning or direct SVG authoring.
---

# Topic Research Stage

> Factual preparation inside the active Generate profile's source intake: Default hands its output to Strategist, Quick's main agent consumes it. Run immediately for topic-only input, or after supplied material is converted and read when it leaves planning-critical factual gaps. Output is exactly a research supplement plus stable fact provenance for project import. The facts JSON is provenance, not a page-download queue: `import-sources` imports the pair without fetching `source_url` values; a page may be fetched later only through the bounded image fallback below. This stage makes no deck image selection and performs no image search or generation.

## When to Run

| Material state | Action |
|---|---|
| Topic or requirements with no supporting facts | Research the factual baseline for the requested outcome |
| Supplied material covers only part of the outcome | After conversion and reading, research only the identified externally verifiable gaps |
| Supplied material already supports the outcome | Skip; continue the profile's source preparation |
| User requires a closed corpus, source-only transformation, or no external enrichment | Skip; plan within supplied material |

**Sufficiency test**: a gap exists when the content owner would otherwise have to invent, omit, or leave unsupported an externally verifiable claim the requested outcome needs; file presence, source length, and topic taxonomy do not decide it.

**Hard rule — preserve supplied facts**: supplement the user's material, never silently replace it; record a material source conflict in the research output instead of choosing a different claim without disclosure. Do not research omissions outside the requested scope.

---

## Step 1: Define the gap brief

| Item | Default if unspecified |
|---|---|
| Topic / scope / outcome | From the request; otherwise broad overview |
| Supplied-material baseline | Facts and claims already available |
| Research gaps | Only facts needed to support the outcome |
| External-source boundary | External enrichment allowed; supplied facts remain authoritative |
| Output language | Match user input |
| Audience / communication intent | Use what is explicit; Default leaves confirmation to Strategist, Quick resolves routine gaps in context |
| Research stem `<research_slug>` | `<topic_slug>_research`, or another unused snake_case stem rather than overwriting |

Default bundles only genuinely missing scope or research-boundary decisions into one clarifier; Quick applies the defaults and continues, stopping only when a required permission or safety boundary cannot be inferred responsibly. Do not repeat the full-pipeline confirmation here.

---

## Execution Context

**Default — isolated research when available**: the main agent owns the sufficiency decision and brief. When the host supports an isolated subagent with web/fetch access and write access to the declared outputs, dispatch exactly one research worker with the topic/outcome, baseline or source paths, declared gaps, output language, two exact unused output paths, and this stage's absolute path as execution authority (paths, not pasted source bodies). The worker reads this file completely, follows Steps 2–3, limits project writes to the two artifacts, and makes no image, deck-planning, or design decisions. Otherwise the main agent runs Steps 2–3 locally.

**Hard rule — isolate retrieval, not research**: raw page content stays in the worker context. The 250-word limit applies only to its chat receipt (`status`, artifact paths, covered/unresolved gap counts, external-fact count, material conflicts), never to the artifacts. After validation and import, the content owner reads the complete imported pair into the main context; never use the receipt as content.

**Validation**: before import, verify both files exist, the Markdown contains `## Research Brief` and no source list or URL, the JSON parses with schema `ppt-master.fact-provenance.v1` and unique sequential IDs, and the two agree. Return an invalid pair to the worker for repair; use main-context research only when isolation is unavailable.

---

## Step 2: Gather factual sources

Use the search and fetch tools available in the research context; an isolated worker without them returns `blocked: web-tools-unavailable`. With no usable search/fetch context, pause and ask the user for authoritative URLs covering the gaps, then fetch each with `web_to_md.py <URL> -o projects/<research_slug>_web_sources/<source_slug>.md --no-images` (remote image links stay in the Markdown; nothing is downloaded).

Orient (map authoritative sources to the gaps) → deep fetch (read the highest-signal primary pages in full) → targeted fill (search only for gaps still unsupported). Prefer primary sources, official sites, institutional releases, standards, and original research; then authoritative reference works and academic sources; then reputable reporting; avoid unsourced reposts, unverifiable summaries, and stock-aggregator pages.

**Adopted webpage boundary**: record a URL only in the matching fact's `source_url`, and only when it materially supports that fact — never because its images may be useful, and never from unopened search results or a separate image-search pass. Stop when every declared gap has enough sourced evidence for the content owner to decide inclusion; do not add overview/history/outlook sections to look complete.

---

## Step 3: Save the factual supplement

Write `projects/<research_slug>.md` and `projects/<research_slug>.facts.json` — under `projects/`, never the repository root; never overwrite an existing user file; no research-image manifest or downloaded images.

The Markdown begins with a compact `## Research Brief` (baseline, declared gaps, known audience/intent, requested outcome), then organizes the body by gap with concrete facts only, flags material conflicts, and cites claims by `fact_id`; no `## Sources` or URLs — the JSON is the only URL authority. The JSON records every externally sourced claim that may enter the deck (especially quantitative, date, ranking, attribution, and named-entity claims) with immutable sequential IDs — correct a claim under the same ID, never reuse a removed ID; no user-supplied claims or invented scenario values; an empty `facts` array when nothing external is retained.

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

---

## Hand-off

After project initialization, import the pair with the user sources; the facts JSON is an ordinary source file and no webpage is retrieved:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources projects/<project_name> [<source_paths...>] projects/<research_slug>.md projects/<research_slug>.facts.json
```

If planning later exposes a required gap, return here and repair the pair before continuing; Strategist or Quick never consumes a newly fetched claim without updating it. The imported pair is the compact evidence-facing content authority, not a locked contract: Default's Strategist reads both files completely before confirmation; Quick's agent does the same before its content, design, and resource decisions.

**Single-page image fallback**: only after normal web-image providers, ranked thumbnail pages, and materially different queries fail may an image owner with visual capability select one relevant `source_url` from the facts JSON and fetch that one page package with `web_to_md.py "<source_url>" -o <project_path>/sources/<source_slug>.md`, review the companion `<source_slug>_files/` package, and copy only accepted images into `<project_path>/images/` — never pass the URL to `import-sources`, which would promote every companion image into the pool. Fetch another page only after the current package has no usable image; without vision, retain `Needs-Manual`.

```markdown
## ✅ Topic Research Complete
- [x] Research execution: <isolated worker | main-context fallback>
- [x] Research supplement: `projects/<research_slug>.md` (N declared gaps covered)
- [x] Fact provenance: `projects/<research_slug>.facts.json` (N external facts)
- [x] Artifact contract validated: `## Research Brief`, no Markdown source list, `ppt-master.fact-provenance.v1`, unique sequential IDs, Markdown/JSON agreement
- [x] Adopted webpage URLs: N unique `source_url` values; no webpage auto-imported, no image copied into the runtime pool
- [ ] **Next**: Default returns to [`generate-pptx`](../generate-pptx.md) Step 2; Quick returns to [`quick-generate`](../profiles/quick-generate.md) §2. Import the sources plus research pair, then fully read the imported pair before planning or direct SVG authoring
```
