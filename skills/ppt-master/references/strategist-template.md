> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Template Planning

Conditional extension for applying an installed Brand/Style/Layout/Deck workspace to Stage 2 recommendations and the execution lock.

**Trigger**: Load only after Stage 1 confirms a library or explicit workspace selection and the post-confirmation apply stage installs it into `<project_path>/templates/` or confirms in-place consumption. Bare template names, style words, and free-design projects do not trigger this module.

---

## 1. AI-Authored Template Application Plan

**Inputs**: every installed `<project_path>/templates/design_spec.<kind>.<id>.md` is a template-design source; read all of them. A `design_spec.style.*.md` file marks an active Direction / method segment. Bare names and style words stay interpretive input and never resolve to a local path. Library/explicit provenance never affects precedence. A legacy or incomplete Layout/Deck is not a Step 3 input — rebuild it through [`create-template`](../workflows/create-template.md), preferably from the original PPTX; never mutate the input.

**Hard rule — no Stage-1 influence**: Do not load this module, the template spec, prototypes, assets, or template canvas while authoring Stage 1, and never revise a confirmed Stage 1 to match the workspace.

**Outputs**:

| Output | Form |
|---|---|
| `recommendations.stage2.json` top-level `template_application.value` | One concise natural-language paragraph; omitted without a template |
| `design_spec.md §I` | `- **Template Application**: <prose>` persisted from the confirmed `result.json` value (or exact chat answer); blank returns the decision to Strategist |
| `spec_lock.md pptx_structure` | Only the derived internal values below (§3); never in `design_spec.md`, stage files, the Confirm UI, or `result.json` |

| Internal value | When the plan requires it |
|---|---|
| `template_reuse_scope: mirror` | Workspace has `replication_mode: mirror`, the plan reuses pages literally, and each page changes only allowed visible text values while preserving visual and text-node topology |
| `template_reuse_scope: layout` | The Master/Layout system and prototypes are reused while current-project content and appearance decisions remain open |
| `template_reuse_scope: style` | A Style-only workspace is active, or only communication/design direction, color, typography, decoration, composition, or rhythm is reused and pages are flat free-design |
| `template_adherence: strict` | Every structured page fits an existing prototype contract without changing Layout identity or slot topology; mandatory for `mirror` |
| `template_adherence: adaptive` | Structured reuse stays useful but at least one page needs a new explicit Layout under the selected Master |

**Procedure** — immediately before authoring the Stage-2 solution, load each relevant resource once per path + SHA: every installed spec with its Page Roster and every complete Slide prototype (Layout first, otherwise Deck; a mirror scope note about omitted source identities is evidence, not a page-candidate list); the Identity, Structure, Reusable Application Context, and Direction / method owners resolved under [`apply-template-workspace`](../workflows/stages/apply-template-workspace.md) §5; the confirmed communication contract, source obligations, planned page count, and content shape of every page; the user's natural-language instructions including required page names/numbers or elements. Then author one plan, without an option menu, that decides: for Layout/Deck, whether the full prototype set, a subset, or only the design language is useful, which prototype each page starts from, which pages are skipped, repeated, or reordered; whether content is inserted directly, reorganized inside existing structure, or rebuilt under the resolved Direction / method; for Style, which communication method, visual language, composition rhythm, and expression defaults are adopted without inventing prototypes; which visible elements stay literal because the user said so. Re-read an installed SVG when a prototype detail is uncertain — never memory, a semantic label, or the source PPTX.

**Judgment**: Template size is evidence, not policy — a short template may use every prototype when content fits; a 20–30 page source may contribute a few pages or be reorganized into a new sequence. Never infer that all pages must be kept or that sample content is protected merely because it exists. Natural-language instructions win; otherwise decide from content and installed state. Common readings — reference-led redesigns after full-roster study; augment-only freezes non-slot objects, permits slot edits, and only adds; replacement-only changes information carriers and preserves the rest — are examples, not modes; use reference-led when nothing fits better. Never ask the user to choose internal reuse/adherence values.

**Hard rule — Slide prototypes drive authoring**: every template SVG is a complete Slide prototype with resolved Master + Layout + Slide context; use these files for `page_layouts`. Standalone Master/Layout definition SVGs are invalid. An unselected authored prototype may still supply a `pptx_layouts` definition; mirror exposes only actual source Slides.

**Plan wording**: for Layout/Deck, state prototype use/order, what stays literal, and what may change, naming exact SVG basenames for prototype-specific exceptions rather than roles such as "cover". For Brand/Style, state identity or Direction / method constraints and free composition unless structure comes from another workspace.

**Two-stage boundary**: an installed template changes the content of final Stage 2, never the confirmation sequence. Run Stage 1 → Stage 2 in order in both Confirm UI and chat fallback; template inspection is not user confirmation. On browser timeout, return to the same stage in chat.

---

## 2. Scenario Fit and Inherited Design

**Mandatory — decide from the §1 inspection**: for `kind: deck`, compare the retained Template Overview with the confirmed audience, intent, outcome, delivery context, afterlife, and source obligations, and its Page Roster and SVG roster with required narrative roles, content shapes, slots, and capacity; Deck application is reusable context, never the current contract or an override. For `kind: layout`, compare only structural roles, slots, and capacity. For an active Style segment, compare its communication method with the current contract and its composition requirements with any selected Layout/Deck structure. Surface a material incompatibility; never silently weaken one segment to make it fit. Reopen a resource only when its path + SHA changed.

| Internal scope | Appropriate when |
|---|---|
| `mirror` | The artifact repeats a known form; literal appearance and text topology are requirements; new content fits existing roles and slots |
| `layout` | The structural system and brand continue, but the outcome requires reflow, new emphasis, or an adaptive Layout |
| `style` | Only direction is reused, a Style-only workspace is active, or the outcome requires a different sequence, density, or composition system |

When the communication contract conflicts with the workspace, state the best-fit plan in the Stage-2 solution and surface the mismatch only when it materially limits the result; no mode questionnaire. Template capability constrains what is legal; scenario fit decides what is useful. (`content_divergence` controls source reorganization; `template_reuse_scope` records the reused layer; `template_adherence` records whether a structured plan keeps or extends Layout identities.)

**Precedence**: explicit current user instructions and final confirmation win. The installed set contributes at most one of each kind; all four may coexist. Brand overrides Deck identity. Layout overrides Deck structure; Deck keeps application context and identity not overridden by Brand; without Layout, Deck owns structure. Style owns Direction / method only: its visual values are candidate defaults that yield to resolved Brand/Deck identity, and its preferred Mode / Visual Style seed the single final locks. Style takes this segment ahead of ordinary Stage-2 defaults; active prototypes and Deck Signature facts remain compatibility constraints.

**Default — template-led recommendation (may override for explicit user or confirmed-contract requirements)**: all three directions obey the same resolved template context. Repeat fixed Brand/Deck palette roles and complete fonts with `typography.fixed: true`; keep resolved icon/image constraints and vary only open roles or dimensions. Mark as `design_directions.selected` the viable direction that most fully expresses the template-owned structure, visual language, and application rules. Never weaken template use or split its segments across cards to manufacture alternatives. Style Review Focus never activates [`visual-review`](../workflows/stages/visual-review.md); only an explicit user request does.

---

## 3. Structured Lock Planning

| Plan | Lock rows |
|---|---|
| Style-only or Style + Brand | `pptx_structure.mode: flat`, `template_reuse_scope: style`; omit `template_adherence` and every structured mapping section |
| `mirror` / `layout` | `pptx_structure.mode: structured`, `template_adherence: strict\|adaptive` (mirror always `strict`); no legacy `baseline`, `template`, `preserve`, `layout_strategy`, or Layout-kind rows |

A Style installed alongside Layout/Deck changes only Direction / method and never forces flat/structured routing; a literal `mirror` plan is compatible only when the Style segment requires no visual or topology change.

- **Master roster**: one `pptx_masters` row per Master as `<master_key>: <picker name>`, copied from the workspace roster. Keys are 1–64 ASCII letters/digits/dots/underscores/hyphens starting with a letter or digit; spaces belong only in the picker name. Master visuals are root-level atoms, never `<g>`.
- **Reusable Layout roster**: every unique Layout once as `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`. Each installed `template:<basename>` is a complete Slide prototype, including ones not selected for this deck; a new adaptive Layout uses its first generated `P<NN>`. Reuse a key only when fixed atoms and slot ids/types/indices/bounds/binding modes are identical. Name authored keys after composition, never page topic. Zero-slot Layouts are valid; do not manufacture an empty `utility` kind or a full-page fake slot.
- **Page assignment**: exactly one `page_pptx_layouts` row per page; each key must exist in `pptx_layouts`. Check that distinct compositions do not collapse into role-only keys and that one skeleton does not split into topic-specific keys.
- **Slot planning**: each reusable slot is a direct root `<g id>` with `data-pptx-placeholder`, positive design-zone bounds from the safe area, column, panel inset, or media frame — not sample text ink — and exactly one compatible direct carrier. A genuinely composite region uses only the explicit `object` + `proxy` downgrade.
- **Adaptive refinement**: initial definitions are complete. If construction shows that reusable framing or slot topology/bounds must change, return to Strategist to add a definition sourced from that page and update its assignment before execution resumes. Executor never mutates the contract; export only compiles declared structure.
- **Input prototypes**: one `page_layouts` row per page using a complete Slide prototype. Strict preserves that SVG's contract; adaptive keeps its Master and may declare a new output Layout. Mirror preserves authored visuals and text-node topology; a JSON-first Chart/Table may regenerate only its derived preview children.

**Visualization compatibility**: use `page_layouts` with optional Chart/Table `page_visualizations` only when the prototype shell can carry the actual §IX information model; the reference changes neither Layout identity, slot topology, nor visualization type. Qualitative relationships stay in §IX and are composed Slide-locally. Without an exact match, adaptive starts from the closest neutral prototype and declares an output Layout; strict selects an existing compatible Layout or revises the outline. Never omit `page_layouts` on a structured route or write legacy `page_charts`.
