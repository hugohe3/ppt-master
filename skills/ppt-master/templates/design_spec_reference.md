# Design Spec Structure

Project-level `design_spec.md` is an English-heading Markdown artifact. Its machine contract is [`schemas/design_spec.schema.json`](./schemas/design_spec.schema.json); authoring starts from [`scaffolds/design_spec.md`](./scaffolds/design_spec.md).

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
| I. Project Information | Project and confirmed communication context | Template reuse rows only when a template workspace is active |
| II. Canvas Specification | Format, dimensions, viewBox, margins | — |
| III. Visual Theme | Mode, visual style, colors | `### AI Image Strategy` when §VIII contains an `ai` row |
| IV. Typography System | Per-role stacks and locked size slots | Additional recurring roles when used |
| V. Layout Principles | Page regions and project spacing | Template-specific constraints only when active |
| VI. Icon Usage Specification | Approved icon inventory | Empty table when no icons are used |
| VII. Visualization Reference List | Selected candidates or an empty table | Only pages with visualization work |
| VIII. Image Resource List | Image acquisition and placement rows or an empty table | AI-only columns apply to `ai` rows |
| IX. Content Outline | Ordered Slide blocks; each has `Audience move` | Page-specific facts, charts, images, and template mappings |
| X. Speaker Notes Requirements | Filename and content policy | — |

**Hard rule**: Keep all ten `##` headings, even when §VII or §VIII contains no rows. Do not add a second schema description inside the project artifact.

---

## 3. Machine validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reads the Markdown directly. It reports missing or out-of-order I–X sections, unresolved `[fill...]` scaffold placeholders, missing per-slide `Audience move`, and a missing §III `AI Image Strategy` when an §VIII table selects `ai` acquisition.

The schema owns structure only. Strategist role modules own field meaning, recommendation logic, page planning, image policy, and template policy. `spec_lock.md` owns the compact execution values; on divergence, the lock wins.

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
