> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Template Planning

Conditional extension for applying an installed Brand/Layout/Deck workspace to Stage 2 recommendations and the execution lock.

**Trigger**: Load only when Generate Step 3 copied an explicit workspace path into `<project_path>/templates/`. Bare template names, style words, and free-design projects do not trigger this module.

---

## 1. AI-Authored Template Application Plan

**Template vs preset**: A style mention and a template directory are different inputs. Bare names and style words map to a visual-style preset; only the installed workspace activates the rules below. Its fused `<project_path>/templates/design_spec.md` is the template-design source.

**Legacy template boundary**: A template containing `native_structure.json`, `source_template.pptx`, missing root Master identity, direct atomic placeholders, or old `baseline` / `preserve` / distillation metadata is not a Generate Step 3 input. Create a current workspace through [`create-template`](../workflows/create-template.md), preferably from the original PPTX when native topology matters. Do not mutate the input in place.

**No template-mode confirmation**: Never ask the user to select `template_reuse_scope`, `template_adherence`, `mirror`, `layout`, `style`, `strict`, or `adaptive`. These are internal execution values for the current exporter. The user communicates intent in natural language; explicit instructions such as “全部原样保留”, “从中选合适的页面”, “可以重组”, or “只参考视觉” are authoritative. Without an explicit instruction, Strategist decides.

Immediately before authoring the Stage-2 solution, load each relevant template
resource once per path + SHA and inspect:

- the installed `design_spec.md`, actual Page Roster, and relevant SVG prototypes;
- the current communication contract, source obligations, planned page count, and content shape of every planned page;
- the user's natural-language instructions, including any page names/numbers or elements they explicitly require.

Then author one plan that decides all of the following without presenting an option menu:

- whether the full prototype set, a relevant subset, or only the design language is useful;
- which prototype each generated page starts from, which template pages are skipped, and which prototypes are repeated or reordered;
- whether content is inserted directly, reorganized inside the existing structure, or rebuilt while retaining only visual language;
- which visible elements must remain literal because the user said so, and which may change to serve the current content.

Template size is evidence, not policy. A short template may use every prototype when the content genuinely fits; a 20–30 page source may contribute only a few suitable pages, or several pages may be reorganized into a new sequence. Never infer that all pages must be kept or that visible sample content is protected merely because it exists in the template.

Record the resulting exporter plan internally:

| Internal value | When the authored plan requires it |
|---|---|
| `template_reuse_scope: mirror` | The workspace has `replication_mode: mirror`, the plan calls for literal page reuse, and each page changes only allowed visible text values while preserving visual and text-node topology. |
| `template_reuse_scope: layout` | The plan reuses the template Master/Layout system and prototypes while allowing current-project content and appearance decisions. |
| `template_reuse_scope: style` | The plan uses only color, typography, decoration language, or rhythm and intentionally creates flat free-design pages. |
| `template_adherence: strict` | Every structured page fits an existing prototype contract without changing its Layout identity or slot topology. Mandatory for `template_reuse_scope: mirror`. |
| `template_adherence: adaptive` | Structured reuse remains useful, but at least one page needs a new explicit Layout under the selected Master. |

Write only the derived values to `spec_lock.md pptx_structure`; omit `template_adherence` for `style`. Do not put these internal values in `design_spec.md`, recommendation stage files, the Confirm UI, or `result.json`.

**Mandatory — natural-language Stage-2 plan**: Summarize which prototypes are used/skipped/repeated/reordered, what stays literal, and what may be replaced or reorganized. Write it to top-level `template_application.value` in `recommendations.stage2.json`; omit it without an active template. After Stage 2, re-read the confirmed `result.json` value (or exact chat answer), never the initial recommendation. Blank returns the decision to Strategist. Persist the effective plan on one line as `- **Template Application**: <prose>` in `design_spec.md §I`, then derive internal reuse/adherence values and mappings; never copy the prose to `spec_lock.md`. Do not add a questionnaire, internal controls, or fixed template-use options.

**Three-stage boundary**: An installed template changes the content of Stage 2, never the confirmation sequence. Run Stage 1 → Stage 2 → Stage 3 in order in both Confirm UI and chat fallback; do not skip a stage or treat template inspection as user confirmation. On browser timeout, return to the same stage in chat.

---

## 2. Scenario Fit and Inherited Design

**Mandatory — decide from the §1 inspection**: For an installed `kind: deck`, compare the retained Template Overview with the confirmed audience, intent, outcome, delivery context, artifact afterlife, and source obligations. Compare the retained Page Roster/relevant SVG prototypes with required narrative roles, content shapes, slots, and capacity. Reopen a resource only when its path + SHA changed. The template describes what exists; it never overrides the current project or own required/optional/repeatable or fixed/replaceable/example-only policy. For `kind: layout`, compare only structural roles, slots, and capacity.

| Internal scope | Appropriate when |
|---|---|
| `mirror` | The artifact repeats a known form; literal appearance and text topology are requirements; new content fits existing roles and slots. |
| `layout` | The structural system and brand continue, but the communication outcome requires reflow, new emphasis, or an adaptive Layout. |
| `style` | Only visual identity is reusable, or the outcome requires a different sequence, density, or composition system. |

When the communication contract conflicts with the workspace, choose and state the best-fit application plan in the complete Stage-2 solution. Surface the mismatch only when it materially limits the result; do not respond with a mode questionnaire. Template capability constrains what is legal; scenario fit decides what is useful.

> Internal note: `content_divergence` controls source reorganization; the AI-derived `template_reuse_scope` records the reused layer; `template_adherence` records whether a structured plan keeps or extends existing Layout identities.

**Template design precedence**: User overrides win. Otherwise template colors and title/body stacks are fixed anchors, not industry defaults. Each of ≥3 Stage-2 directions still carries all six palette roles and complete font objects: repeat fixed values and vary only template-open roles. Keep declared icon and image constraints.

---

## 3. Structured Lock Planning

For `mirror` / `layout`, write `pptx_structure.mode: structured` plus `template_adherence: strict|adaptive`; mirror always writes `strict`. Do not write legacy `baseline`, `template`, `preserve`, `layout_strategy`, or Layout-kind rows.

- **Master roster**: Write one `pptx_masters` row per Master as `<master_key>: <picker name>` and copy the workspace's prototype roster. Keys use 1–64 ASCII letters, digits, dots, underscores, or hyphens, start with a letter/digit, and contain no spaces; human-readable spaces belong only in the picker name. Master visuals are root-level atomic elements and may never be `<g>`.
- **Reusable Layout roster**: Write every unique Layout once as `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`. Copy installed `template:<basename>` sources, including currently unused Layouts. A new adaptive Layout uses its first generated `P<NN>` as source. Reuse a key only when fixed atoms and slot ids/types/indices/bounds/binding modes are identical. Name authored keys after composition, never page topic. A Layout may intentionally have zero slots; do not manufacture an empty `utility` kind or full-page fake slot.
- **Page assignment**: Write exactly one `page_pptx_layouts` row per page. Each key must exist in `pptx_layouts`. Check that distinct compositions do not collapse into role-only keys and that one skeleton does not split into topic-specific keys.
- **Slot planning**: Each reusable slot is a direct root `<g id>` with `data-pptx-placeholder`, positive design-zone bounds, and exactly one compatible direct carrier. Bounds come from the intended safe area, column, panel inset, or media frame—not sample text ink. A genuinely composite region may use only the explicit `object` + `proxy` downgrade.
- **Adaptive refinement**: Initial definitions are complete. If construction shows that reusable framing or slot topology/bounds must change, return to Strategist to add a definition sourced from that page and update its assignment before execution resumes. Executor never mutates or extends the contract; export only compiles declared structure and never discovers or clusters Layouts.
- **Input prototypes**: Add one `page_layouts` row per page. Strict preserves that SVG's contract; adaptive keeps its Master and may declare a new output Layout; mirror also preserves literal visuals and text-node topology.

**Chart compatibility**: Use `page_layouts` together with `page_charts` only when the selected prototype shell is compatible. For a chart page without an exact roster match, adaptive mode starts from the closest neutral prototype and declares an output Layout; strict mode selects an existing compatible Layout or revises the outline. Never omit `page_layouts` on a structured route.
