> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Template Planning

Conditional extension for applying an installed Brand/Layout/Deck workspace to Stage 2 recommendations and the execution lock.

**Trigger**: Load only when Generate Step 3 copied an explicit workspace path into `<project_path>/templates/`. Bare template names, style words, and free-design projects do not trigger this module.

---

## 1. Reuse Scope and Adherence

**Template vs preset**: A style mention and a template directory are different inputs. Bare names and style words map to a visual-style preset; only the installed workspace activates the rules below. Its fused `<project_path>/templates/design_spec.md` is the template-design source.

**Legacy template boundary**: A template containing `native_structure.json`, `source_template.pptx`, missing root Master identity, direct atomic placeholders, or old `baseline` / `preserve` / distillation metadata is not a Generate Step 3 input. Create a current workspace through [`create-template`](../workflows/create-template.md), preferably from the original PPTX when native topology matters. Do not mutate the input in place.

**Template reuse confirmation**: Surface `template_reuse_scope` only for an installed `kind: deck` or `kind: layout` workspace. Omit it for brand-only workspaces.

| Reuse scope | Planning and export behavior |
|---|---|
| `mirror` | Mirror workspaces only. Start from the full selected page, preserve literal visuals and text-node topology, and replace only allowed visible text values. |
| `layout` | Reuse the template Master/Layout system and input prototypes, but allow project-controlled reflow/re-skinning and explicit adaptive Layouts. |
| `style` | Reuse only color, typography, decoration language, and rhythm. Plan `pptx_structure.mode: flat` with no template structure mappings. |

**Deterministic language mapping**: “不要严格复用”, “只参考风格”, “参考这个风格”, and “不必照搬版式” recommend `style` unless the user explicitly asks to retain the layout system, in which case recommend `layout`. “原样复刻”, “替换内容”, and “保持模板页面外观” recommend `mirror` only when `replication_mode: mirror` is available. A bare workspace path with no stronger language defaults to `layout`.

For `mirror` / `layout`, surface `template_adherence`. Hide it for `style`.

| Value | Planning and export behavior |
|---|---|
| `strict` | Map every page to one template SVG. Keep its explicit Master/Layout/slot contract and output Layout key unchanged. |
| `adaptive` | Map every page to the closest template SVG. Keep the template Master contract, but allow a new explicit Layout key when content requires a structural adaptation. |

**Default — layout + adaptive**: For a workspace path without stronger language, recommend `layout` and `adaptive`. Preselect `strict` only when the user explicitly asks to keep the selected Layout contract unchanged. Record the confirmed scope in `design_spec.md §I` and `spec_lock.md pptx_structure`; record adherence only for `mirror` / `layout`.

---

## 2. Scenario Fit and Inherited Design

**Mandatory — consume the stored contract at the decision point**: Immediately before recommending reuse for an installed `kind: deck`, re-read `<project_path>/templates/design_spec.md`. Compare its five `## I. Template Overview` application-contract rows with the confirmed audience, intent, outcome, delivery context, artifact afterlife, and source obligations. Compare every `## V. Page Roster` content-policy value with the required narrative/page roles, including required / optional / repeatable status and fixed / replaceable / example-only content. Treat the contract as applicability evidence, never as the current project's truth; do not copy it into blank Stage-1 fields or infer fields it does not declare. For `kind: layout`, no application contract exists: compare only the roster's structural roles, slots, and capacity.

| Scope | Appropriate when |
|---|---|
| `mirror` | The artifact repeats a known form; literal appearance and text topology are requirements; new content fits existing roles and slots. |
| `layout` | The structural system and brand continue, but the communication outcome requires reflow, new emphasis, or an adaptive Layout. |
| `style` | Only visual identity is reusable, or the outcome requires a different sequence, density, or composition system. |

When the communication contract conflicts with the workspace, surface the mismatch. Template capability constrains what is legal; scenario fit decides what is useful.

> Note: `content_divergence` controls source reorganization; `template_reuse_scope` controls the reused layer; `template_adherence` controls strictness inside `mirror` / `layout`.

**Template design precedence**: User overrides win. Otherwise lock declared colors and title/body font stacks from the fused template `design_spec.md` directly; skip generic color/font candidates and do not adjust template values to fit an industry default. Keep the workspace's declared icon and image constraints when producing those conditional plans.

---

## 3. Structured Lock Planning

For `mirror` / `layout`, write `pptx_structure.mode: structured` plus `template_adherence: strict|adaptive`. Do not write legacy `baseline`, `template`, `preserve`, `layout_strategy`, or Layout-kind rows.

- **Master roster**: Write one `pptx_masters` row per Master as `<master_key>: <picker name>` and copy the workspace's prototype roster. Keys use 1–64 ASCII letters, digits, dots, underscores, or hyphens, start with a letter/digit, and contain no spaces; human-readable spaces belong only in the picker name. Master visuals are root-level atomic elements and may never be `<g>`.
- **Reusable Layout roster**: Write every unique Layout once as `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`. Copy installed `template:<basename>` sources, including currently unused Layouts. A new adaptive Layout uses its first generated `P<NN>` as source. Reuse a key only when fixed atoms and slot ids/types/indices/bounds/binding modes are identical. Name authored keys after composition, never page topic. A Layout may intentionally have zero slots; do not manufacture an empty `utility` kind or full-page fake slot.
- **Page assignment**: Write exactly one `page_pptx_layouts` row per page. Each key must exist in `pptx_layouts`. Check that distinct compositions do not collapse into role-only keys and that one skeleton does not split into topic-specific keys.
- **Slot planning**: Each reusable slot is a direct root `<g id>` with `data-pptx-placeholder`, positive design-zone bounds, and exactly one compatible direct carrier. Bounds come from the intended safe area, column, panel inset, or media frame—not sample text ink. A genuinely composite region may use only the explicit `object` + `proxy` downgrade.
- **Adaptive refinement**: Initial definitions are complete. If construction changes reusable framing or slot topology/bounds, Executor creates one new definition sourced from that page and updates its assignment; it never mutates a reused contract silently. Export only compiles declared structure and never discovers or clusters Layouts.
- **Input prototypes**: Add one `page_layouts` row per page. Strict preserves that SVG's contract; adaptive keeps its Master and may declare a new output Layout; mirror also preserves literal visuals and text-node topology.

**Chart compatibility**: Use `page_layouts` together with `page_charts` only when the selected prototype shell is compatible. For a chart page without an exact roster match, adaptive mode starts from the closest neutral prototype and declares an output Layout; strict mode selects an existing compatible Layout or revises the outline. Never omit `page_layouts` on a structured route.
