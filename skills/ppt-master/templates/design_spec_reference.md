# Design Spec Structure

Project-level `design_spec.md` is a human-readable English-heading Markdown artifact. [`schemas/design_spec.schema.json`](./schemas/design_spec.schema.json) provides structural lint for readable sections and page projection; it is not an execution lock and does not require textual equality with `spec_lock.md`. Authoring starts from [`scaffolds/design_spec.md`](./scaffolds/design_spec.md).

Strategist reads the complete final confirmation once, writes this artifact from that retained state plus source analysis, and audits every confirmed field here. Afterward, `spec_lock.md` is authored from the completed Design Spec plus current project/page/template context; normal lock authoring never reopens `result.json`.

## 1. Create the artifact

Run the scaffold command once, then replace every `[fill]` value while preserving the section headings:

```bash
python3 skills/ppt-master/scripts/project_manager.py scaffold-spec <project_path>
```

The command refuses to shadow any recognized existing design-spec artifact, including legacy filenames. Re-running it in an otherwise equivalent empty project produces the same bytes.

---

## 2. Section contract

| Section | Required content | Conditional content |
| --- | --- | --- |
| I. Project Information | Project and confirmed communication context | `Template Application` prose when template-active |
| II. Canvas Specification | Format, dimensions, viewBox, margins | — |
| III. Visual Theme | Mode, visual style, colors | `### AI Image Strategy` when §VIII contains an `ai` row |
| IV. Typography System | Per-role stacks and locked size slots | Additional recurring roles when used |
| V. Layout Principles | Page regions and project spacing | Template-specific constraints only when active |
| VI. Icon Usage Specification | Approved icon inventory | Empty table when no icons are used |
| VII. Visualization Reference List | Candidates and independent charts/tables with `Native-ready`, or empty | Incidental microvisuals stay in §IX |
| VIII. Image Resource List | Rows with `Layout pattern` and `Crop Policy`, or empty | AI columns apply only to `ai` rows |
| IX. Content Outline | Complete ordered execution roster; one Slide block per final page, matching the exact Page Count; each has `Audience move` | Page-specific facts, charts, images, and template mappings |
| X. Speaker Notes Requirements | Filename and content policy | — |

**Hard rule**: Keep all ten `##` headings, even when §VII or §VIII contains no rows. Do not add a second schema description inside the project artifact.

---

## 3. Machine validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reads the Markdown directly. It reports missing or out-of-order I–X sections, unresolved `[fill...]` scaffold placeholders, missing per-slide `Audience move`, and a missing §III `AI Image Strategy` when an §VIII table selects `ai` acquisition.

The schema owns structure only. Strategist role modules own field meaning, recommendation logic, page planning, image policy, and template policy. `spec_lock.md` owns stable execution anchors and routing selected in context; it is not an exhaustive value projection. On divergence, repair the Design Spec from the retained final state when Gate 1 fails, then re-author affected lock anchors from the audited Design Spec and current context. Never reopen `result.json` merely to author or validate the lock, and never use the lock to overwrite a valid Design Spec decision.

---

## 4. Minimal filled shape

```markdown
## III. Visual Theme

### Theme Style
- **Mode**: briefing
- **Visual style**: swiss-minimal

### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | `#FFFFFF` | Canvas |

## IX. Content Outline

#### Slide 01 - Decision frame
- **Audience move**: undecided → understands the decision
- **Layout**: claim + evidence
- **Title**: Choose the funded path
```

Use the scaffold for the complete shape; this excerpt is not a second template.
