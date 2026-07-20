---
description: Main-pipeline intake stage that gathers source material for topic-only requests.
---

# Topic Research Stage

> Generate-PPTX intake stage. Run before [`generate-pptx`](../generate-pptx.md) Step 1 when the user supplies only a topic or requirements with no source files. Output is a research document, a stable fact-provenance file, and an image folder, all shaped to feed `project_manager.py import-sources` directly.

This stage is **context-independent**: it owns source acquisition when no file exists; subsequent [`generate-pptx`](../generate-pptx.md) steps proceed normally with the produced materials as input.

## When to Run

| User-supplied input | Action |
|---|---|
| Topic name only (e.g. "做一个关于宫崎骏的 PPT") | Run this stage before Generate Step 1 |
| Requirement description without facts (e.g. "介绍我们公司新产品") | Run this stage before Generate Step 1 |
| ≥1 page of substantive content already in chat | Skip — feed chat content into [`generate-pptx`](../generate-pptx.md) Step 1 directly |
| Source file attached (PDF / DOCX / URL / Markdown) | Skip — go to [`generate-pptx`](../generate-pptx.md) Step 1 source conversion |

---

## Step 1: Confirm topic

⛔ **BLOCKING**: confirm scope as a single bundled clarifier. Skip when the user's initial message already covers it.

| Item | Default if user did not specify |
|---|---|
| Topic | (from user input) |
| Scope / focus | Broad overview |
| Depth | General-knowledge level |
| Output language | Match user input |
| Target audience | Audience implied by the request; otherwise state a provisional general audience |
| Research-facing communication intent | Open prose describing what the eventual presentation should accomplish; may combine several purposes |
| Desired audience outcome | What the audience should know, understand, believe, decide, or do after the presentation |
| Slug for files (`<topic_slug>`) | snake_case English identifier derived from topic |

**Forbidden — itemized confirmation**: do NOT ask each row separately. One bundled clarifier or none.

**Communication intent is not a pick-list.** You may mention inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off as examples that help the user answer, but never ask them to select one label. Preserve multiple purposes plus their priority / sequence. This intake captures only the subset needed to aim research; main-pipeline Stage 1 confirms the full communication contract—audience, outcome, core message / ask, delivery context, artifact afterlife, and source-treatment intent—after the facts exist. Every editable Stage-1 prose field may remain blank after confirmation. Stage 2 confirms reading mode with the complete deck solution.

---

## Step 2: Gather via web search

**Tools** — use the web search and web fetch tools the current IDE provides:

| IDE | Web search | Web fetch |
|---|---|---|
| Claude Code | `WebSearch` | `WebFetch` |
| Cursor / Codebuddy / VS Code + Copilot | provider-equivalent built-in | provider-equivalent built-in |
| None available | — | fallback below |

**Fallback when no IDE web tools** — pause, ask the user for 2–4 authoritative URLs (Wikipedia / official site / institutional release), then fetch each:

```bash
python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <URL>
```

**Search strategy**:

| Phase | Action |
|---|---|
| Landscape | One broad search; identify authoritative sources |
| Deep fetch | Pull 2–4 highest-signal pages in full |
| Targeted fill | Search for subtopics the deep fetch flagged |

**Source priority**:

| Tier | Source |
|---|---|
| 1 | Wikipedia / Wikimedia Commons |
| 2 | Official sites, institutional releases |
| 3 | Reputable news / academic articles |
| Avoid | Stock-aggregator watermarked images, social-media reposts without source |

**Stop condition**: stop when gathered material covers overview / history / key aspects / impact / sources with concrete facts and named entities. Endless searching produces noise.

---

## Step 3: Save materials

Three artifacts under `projects/`:

| Artifact | Path |
|---|---|
| Research document | `projects/<topic_slug>.md` |
| Fact provenance | `projects/<topic_slug>.facts.json` |
| Image folder | `projects/<topic_slug>/` |

**Hard rule — naming**: filename (without `.md`) and folder name MUST match. **Hard rule — location**: under `projects/`, never the repository root.

**Document structure** — begin with a compact `## Research Brief` carrying Target audience, Communication intent, and Desired audience outcome in open prose. Then let section layout follow the topic: person → biography / works / impact; technology → background / mechanism / applications / outlook; company → overview / products / market / culture. The file MUST end with a `## Sources` section listing the URLs used.

**Content density** — concrete facts (dates, names, numbers, quotes). Skip filler prose; the Strategist composes final slide copy.

**Fact provenance** — write every externally sourced, verifiable claim that may enter the deck to `<topic_slug>.facts.json` with a stable sequential ID, especially quantitative, date, ranking, attribution, and named-entity claims. Do not put invented demonstration values in this file; Strategist marks those as `scenario` later. When research yields no external claims, still write the schema with an empty `facts` array.

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

IDs are immutable within the file. If a claim is corrected, update its value/source under the same ID; if a claim is removed, do not silently reuse its ID for a different fact. The research Markdown and `facts.json` must agree.

**Images**:

| Decision | Rule |
|---|---|
| Quantity | Cover the deck's likely scenes (cover, key aspects, key entities); the Strategist decides the final cut |
| Resolution | Prefer originals. Wikimedia: strip `/thumb/` and the `Npx-` prefix from the URL to get full resolution |
| License | Wikimedia / public-domain / CC-licensed; avoid stock-aggregator watermarks and unsourced uploads |
| Filename | descriptive English snake_case (`joe_hisaishi_concert.jpg`, not `image1.jpg`) |

```bash
mkdir -p "projects/<topic_slug>"
curl -L -o "projects/<topic_slug>/<descriptive_name>.<ext>" "<image_url>"
```

---

## Hand-off

Output a checkpoint, then continue with the main pipeline. The artifacts feed directly into Step 2's `import-sources`:

The Research Brief is evidence-facing context, not a locked presentation contract. Strategist reads it when preparing Stage 1, then confirms / edits the full contract with the user before choosing narrative mode, template reuse, or visual direction.

```markdown
## ✅ Topic Research Complete
- [x] Document: `projects/<topic_slug>.md` (N sections)
- [x] Facts: `projects/<topic_slug>.facts.json` (N external facts)
- [x] Images: `projects/<topic_slug>/` (N files)
- [ ] **Next**: [`generate-pptx`](../generate-pptx.md) Step 2 →
  `project_manager.py init <project_name> --format <format>`
  `project_manager.py import-sources projects/<project_name> projects/<topic_slug>.md projects/<topic_slug>.facts.json projects/<topic_slug>/*.* --move`
```

`<project_name>` is the user's chosen project identifier (typically `<format>_<topic_slug>`, e.g. `ppt169_joe_hisaishi`); `--move` removes the research artifacts from `projects/<topic_slug>` after they are imported and deletes the folder itself once it is empty.
