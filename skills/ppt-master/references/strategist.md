# Role: Strategist

## Core Mission

Receive source documents, analyze content, plan the design, and output the **Design Specification & Content Outline** (`design_spec`) plus its execution lock. The planning craft shared with Quick is [`plan-core.md`](./plan-core.md); this file owns the confirmation stages, the three-direction construction, and the artifact grammar.

## Pipeline Context

| Previous Step | Current | Next Step |
|--------------|---------|-----------|
| Project creation + template-candidate preparation complete | **Strategist**: Stage 1 communication/template confirmation → installation handoff → Stage 2 solution + Design Spec | Image_Generator or Executor |

Canvas formats and their typography scale start: [`canvas-formats.md`](canvas-formats.md).

---

## 1. Strategist Confirmation Stage

🚧 **GATE — whole-document authoring**: Generate Step 4 reads `${SKILL_DIR}/templates/design_spec_reference.md`, authors the complete Design Spec once, passes Gate 1, then reads `${SKILL_DIR}/templates/spec_lock_reference.md` and authors the complete lock once. No scaffolds, no placeholder patching; `project_manager.py validate` owns grammar.

⛔ **BLOCKING**: present professional recommendations for the fields below and wait for explicit user confirmation. Generate Step 3 prepares candidates only. Stage 1 confirms the communication contract and the template/free-design choice together (the recommendation independent of every candidate); the selected workspaces are installed before Stage 2.

| Stage | Items | Role |
|---|---|---|
| **1 — communication contract + template choice** | `primary_language` · `c` audience · open-ended communication intent · audience outcome · core message / delivery context (primary + optional secondary) / artifact afterlife · `content_divergence` (all prose may be blank) · `a` canvas · explicit `free_design` or `templates` choice and selected roots | confirmed together; candidates never influence the communication recommendation |
| **2 — final solution + production** (authored once from the user's *actual* Stage 1) | reading mode (`delivery_purpose`, PPT only) · `d` mode + visual style · `b` page count · `e` color · `f` icon · `g` typography · `h` image source + generated-image rendering · conditional template application · conditional AI-image acquisition path · generation mode · refine-spec toggle · `design_spec_depth` · proactive speaker notes / custom animations / narration audio | one coherent plan from the confirmed contract; exporter reuse/adherence stays internal |

**Stage 1 fields**: record composite intent in prose, never one catalog label. Editable prose fields are drafts: confirmation keeps the current text and blanks, and a cleared field is never repopulated.

**Stage 2 scope**: confirm narrative spine, reading density, page budget, visual system, image direction, production mechanics, and how an installed template is used (inspecting only project-local specs and prototypes). Stage 2 never chooses or installs a template.

**Selected direction**: `design_directions.selected` is the actual zero-based index (`0`, `1`, or `2`) of the strongest fit, chosen after all three §d directions are complete. With an installed template it is the viable direction that best expresses its resolved context under [`strategist-template.md`](./strategist-template.md). Array order never determines preference.

**Production defaults**: proactive defaults are notes `true`, custom animations `false`, narration `false`. An earlier explicit instruction overrides the matching recommendation; narration requires notes. Recommend `design_spec_depth: brief` (the same author draws the pages); recommend `complete` only for `split`, `refine_spec: true`, a preservation profile, or a requested hand-off document. Author each stage once; launch/wait mechanics are [`generate-pptx.md`](../workflows/generate-pptx.md) Step 4.

**Default — continuity-aware whole solution (may override when a scene reset communicates better)**: before recommending page count or production mechanics, judge whether adjacent beats can stay within one recognizable mental map while a visible state changes. Where that lowers cognitive switching and motion has a named job, let it shape the spine, rhythm, visual approach, and notes/narration segmentation, and recommend `proactive_custom_animations: true`. Plan such neighbors as visible states of one scene: recognizable anchors kept, the delta legible, each enabled notes/narration segment aligned with its state, every state page still carrying content and an `Audience move`. Reset when the map changes or continuity adds nothing. One positive signal, not the only one: topic or wording repetition alone is insufficient, and a `Motion suggestion` never changes the effective outcome.

**Hard rule — Stage-1 source boundary**: the evidence Stage 1 may use is fixed by [`generate-pptx.md`](../workflows/generate-pptx.md) Step 4; template controls on the same surface are confirmation state, not evidence. Load [`strategist-template.md`](./strategist-template.md) only after Stage 1 is confirmed and the selection installed.

> **Execution discipline**: Stage 1 is the first BLOCKING checkpoint; its receipt is intermediate and never ends the task. In the same run, install/fuse the selection, complete the handoff, author fresh Stage 2, and enter the final wait. After final confirmation proceed without another pause unless refinement is enabled; the only opt-in exception is [`refine-spec`](../workflows/stages/refine-spec.md), offered with the split-mode note and never entered unprompted.
>
> **Presentation surface**: apply the sticky per-run surface decision in [`confirm-surface.md`](./confirm-surface.md) and author the Stage-1/Stage-2 payloads in its shapes; the chat/delegated branch keeps equivalent state without fabricating receipts. Stage 1 writes canonical BCP-47 `primary_language`; Stage 2 carries exactly three immutable `design_directions`; the final result stores only current component values, never a direction id. Server lifecycle: [`confirm_ui.md`](../scripts/docs/confirm_ui.md).

**Confirmed-value semantics** — confirmation preserves the value and the owning field's semantic type, applied to that property, not the whole object:

| Type | Consumption |
|---|---|
| Literal requirement | Preserve the exact contracted value, pixels, wording, or topology. |
| Semantic requirement | Preserve facts, relationships, intent, prohibitions, and completeness; expression may change. |
| Identity anchor | Keep recurring identity stable without creating an exhaustive allowlist. |
| Reference | A starting sketch: Executor adjusts or replaces it freely for the page's purpose, with no upstream repair or stated reason. It carries no binding semantics; label it `(binding)` only when the user, a template, or a resource contract requires that property. |
| Permission / default | An allowed candidate/source boundary or preference; may stay unused, with no quota. |

Explicit *must*, *only*, *exactly*, *verbatim*, *do not*, or `no-crop` wording strengthens only the named property; accepting a recommendation keeps the field's default type.

**Authority chain — materials → Strategist preparation → realization**: user inputs bound materials and acquisition. Strategist owns sufficiency, gap-filling, and selection — roster and content, `Relationships`, prepared resources and paths, structured-template routing, fonts, palette anchors, icon library/stroke and curated pool, crop bans, and optional Chart/Table references. Strategist sketches macro composition, focus, and continuity as Reference (binding only when labeled `(binding)`), never a carrier mix, element geometry, or authoring method. Native construction is an Executor capability, not a resource.

| Acquisition step | Timing |
|---|---|
| Topic research and its two-artifact pair | May precede confirmation; facts URLs are never auto-expanded; one adopted webpage becomes a reviewable source package only after normal image search fails |
| AI / web / slice acquisition | After final confirmation plus §VIII/lock |
| Icons | Synced during authoring without page assignment |
| Every resource before Executor | Has a path and a terminal or `Needs-Manual` state |

Missing material returns upstream, never invented or substituted.

⛔ **GATE — final confirmation is consumed once into the Design Spec**: use the complete final object already read by Generate Step 4 (`stage: final`, `status: confirmed`) or the chat path's final visible summary; never reopen `result.json` during Design Spec or lock authoring. Consume every present field by its semantic type and owner without omission, substitution, or silent strengthening/weakening. Decide only what was left unconfirmed; keep a cleared prose field empty. An unhonorable requirement stays visible and follows [`failure-recovery.md`](../workflows/governance/failure-recovery.md).

### a. Canvas Format Confirmation

Recommend from the scenario and project initialization ([`canvas-formats.md`](canvas-formats.md)). A template canvas is not Stage-1 evidence; Stage 2 later checks whether selected structure serves the confirmed canvas.

### b. Page Count Confirmation

Page count craft — the Stage-1 range, the exact count chosen after Stage 1, and the roster invariance after Gate 1 — is [`plan-core.md`](./plan-core.md) §3.

### c. Communication Contract Confirmation

Seed the six contract fields of [`plan-core.md`](./plan-core.md) §1 as open-prose recommendations when the source and request support them; the user may retain, edit, or clear every field, and none requires a non-empty answer. Intent stays open-ended and is never a checkbox list or a `primary_job`.

**Hard rule — confirmed current value wins**: submit every Stage-1 prose field exactly as it stands at confirmation. Blank means no explicit constraint (downstream judgment from source and request) and is never restored to the recommendation. A profile-declared `locked: true` field is the only read-only exception.

**Reading mode** (PPT only, Stage 2): `text` / `balanced` (default) / `presentation`, kept under the compatibility key `delivery_purpose`; what each mode carries is [`plan-core.md`](./plan-core.md) §2. It drives page grammar, granularity, density, and the §b recommendation; the §g body baseline is a consequence.

**Material divergence** (`content_divergence`): a free-text Stage-1 field the user fills in their own words — never a set of options and never recommended from source analysis; blank is a balanced default. The spectrum and the facts-stay-sourced Hard rule are [`plan-core.md`](./plan-core.md) §3. Apply it only while authoring §IX and record it in `design_spec.md §I`, never in the lock. Beautify seeds and locks verbatim preservation; Edit Native PPTX does not surface it.

**Fact provenance** and the intent → outline-obligation checklist are [`plan-core.md`](./plan-core.md) §3 and §1; apply both while authoring §IX, preserving the user's priority and sequence.

### d. Style Objective Confirmation

**Stage 2 only** — tools that serve the confirmed scenario, never substitutes for defining it. Two independent layers, each locking one preset or `custom`; output `d. Mode: <mode> + Visual style: <visual_style>`.

**Hard rule — top-down direction construction**: author three complete, project-fit solution intents from the confirmed contract and source before touching any catalog basis. The three mode/style/rendering indexes are the only basis selectors. Freeze each direction's exact reference ids from the index summaries, read once only the deduplicated union of those detail files, then write the behaviors. Never force safe / shifted / bold archetypes, glob a catalog, read an unselected sibling, or write bespoke prose as an enum value.

**Direction serialization**: every direction serializes `mode: custom`, `visual_style: custom`, and `image_strategy.rendering: custom`, each with visible non-empty behavior prose. A custom may use catalog material in any way or none; one preset carried unchanged is valid. References record only actual sources, each owning a distinct executable contribution, never a decorative second basis.

**Three plainly different designs**: the three directions differ as designs *before* any field is written. Whichever components a design requires carry the difference; mode, style, rendering, bases, color, type, and icons are each free to coincide. A different name, note, or reference count alone is no difference, and identical projections are not three solutions. Where authoritative truth fixes components, the open ones carry the difference. Where nothing is open, keep the projections identical and state that boundary.

#### Layer 1 — Communication mode

🚧 **GATE**: [`modes/_index.md`](./modes/_index.md) is the sole mode-basis authority; basis selection follows the §d Hard rule.

The narrative + persuasion skeleton: one preset from `pyramid` / `narrative` / `instructional` / `showcase` / `briefing`, or `custom` with behavior — one value per deck, never several simultaneous modes.

| Input | Mode derivation |
|---|---|
| **User outline or structure** | Preserve its facts and relationships, then apply `content_divergence`. An ordinary outline is a Reference (regroup, reorder, retitle when the contract benefits); it becomes authoritative only when presented as the final page plan or with an explicit ask to keep order, titles, or wording — record that promotion in `design_spec.md`. Still lock a mode for register and voice; `briefing` imposes the least. |
| **Beautify** ([`beautify-pptx.md`](../workflows/profiles/beautify-pptx.md)) | Extracted content is authoritative and verbatim: one source slide = one §IX page in order, every block transcribed word-for-word, never reshaped, condensed, merged, split, or reworded; all three mode behaviors keep that boundary and may share `briefing`. Color (e) and typography (g) are whatever the beautify plan confirmed (source identity by default) locked as truth. Charts, tables, and images are regenerated from extracted data in the inherited style with values frozen (catalog references in §VII, unmatched plans in §IX, pictures in §VIII). Layout, hierarchy, rhythm, and rendering are what gets redesigned. |
| **No user structure** | Derive each solution from `communication_intent`, `audience_outcome`, source texture, and delivery context, then project its custom mode; directions may share bases or behavior when the whole solutions differ. |

Record the mode and rationale in `design_spec.md` (with every catalog basis a custom uses), then project `- mode:` — and for custom `- mode_behavior:` plus `- mode_references:` only when catalog material is used — to `spec_lock.md`; Executor reads only those references.

#### Layer 2 — Visual style

🚧 **GATE**: [`visual-styles/_index.md`](./visual-styles/_index.md) is the sole style-basis authority; basis selection follows the §d Hard rule.

The visual aesthetic — shape language, decoration density, whitespace rhythm, typographic character, texture — anchoring e, f, g, and h. It carries no color (it governs how the HEX locked at `e` is *used*). When the deck has AI images the style's paired rendering keeps layout and illustration in one aesthetic.

| Input | Style derivation |
|---|---|
| **User named a style** (chat, template, beautify) | It is truth: the required basis or inherited anchor in every behavior. Derive each direction through the open dimensions; when all variation is forbidden let the other components carry the difference and say so in the note. |
| **No description** | Project one complete custom aesthetic per solution, written as the carriers and techniques it *uses* — containers, icons, swatches, shadows, gradients, image treatments, native shapes — never as a list of avoidances. A locked prohibition removes that tool from every page; write one only when the user or material requires it. Behaviors differ when the designs genuinely differ, never to meet a quota; no forced bases, safe-to-bold ladder, or deliberate extreme. |

**Direction name and note**: give each direction a `name` and one- or two-sentence `note` in the confirmed UI language (plain keys). Confirm UI's localized labels such as `瑞士极简`, `柔和圆角`, `编辑出版` are optional vocabulary, never a required mapping, and the note exposes no catalog ids.

**Forbidden — a non-catalog name as `visual_style`**: the field is literal `custom`; prose lives in `visual_style_behavior` and `visual_style_references` holds only first-column catalog ids (a "Paired rendering" id such as `flat` or `digital-dashboard` is a rendering, not a style). Generic words — flat / modern / clean / simple / minimal — are not behavior: state the executable shape language, composition, density, whitespace, typography, and texture, which may match one preset exactly.

Record the style and rationale in `design_spec.md`, then project `- visual_style:` — and for custom `- visual_style_behavior:` plus `- visual_style_references:` only when catalog material is used — to `spec_lock.md`.

**Conditional template workspace**: when the Stage-1 choice is installed under `<project_path>/templates/`, read [`strategist-template.md`](./strategist-template.md) before completing Stage 2 — installed spec and prototypes only, never the library root. It covers the editable application plan, confirmed-value consumption, prototype selection, reuse/adherence derivation, inherited precedence, and structured-lock planning; it decides how to use the template, never which one.

**Downstream effect**: e / f / g / h realize mode + style — e.g. `showcase` + `dark-tech` → one luminous accent on a dark field, a clean sans paired with mono, minimal glow icons, the `digital-dashboard` rendering.

### e. Color Scheme Recommendation

**Hard rule**: user-specified colors are truth — lock supplied HEX, brand colors, or natural-language directives (templates follow inherited-design precedence). Every direction fills all six roles (`background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, `body_text`), repeating fixed roles and varying only open ones; never an empty palette. In §III derive the standard `secondary_text` and `divider` neutrals and project them to `spec_lock.md colors`; §V fixes the five deck-wide spacing anchors.

Palette precedence, proportion, contrast, recall anchors, and the neutral tiers to lock are [`plan-core.md`](./plan-core.md) §6.1; Strategist owns the reusable positive / warning / negative roles and every locked neutral tier.

### f. Icon Usage Confirmation

One single-select base identity (A emoji / B built-in library / C custom / D none), not a material whitelist — the option table, the illustrated-icon and brand-mark boundaries, and the library line are [`plan-core.md`](./plan-core.md) §6.3.

**Mandatory — bundled SVG resources**:

1. At confirmation decide only the generic library and stroke: one primary stylistic library per pool, chosen from the four characters in the [icon README](../templates/icons/README.md) table; `simple-icons` is prepared from content for real brand marks and is never a confirmation choice. This governs catalog selection, not the prepared pool — user, template, imported, custom, and previously prepared files under `<project_path>/icons/` stay valid whatever their namespace.
2. For a stroke library (currently `tabler-outline`) lock one deck-wide `stroke_width` from `{1.5, 2, 3}` (default `2`).
3. After approval, when writing §VI / the lock, materialize the curated pool before Executor starts (Executor cannot sync; which icons a page uses is realization, never a preassignment). Put known basenames in the final batch; search an uncertain one under [README § Searching for Icons](../templates/icons/README.md); copy and validate in one batch — `python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name> …]` — keeping each successful case-sensitive `lib/name` (bundled basenames are lowercase). Record each synced path with broad scenarios in §VI and the same pool, primary library, and any `stroke_width` in `spec_lock.md icons` (`simple-icons/*` ids join the inventory without becoming a second library; other prepared icons stay usable).

🚧 **GATE — missing icon = re-pick now**: on non-zero exit, search the missing concept only in the chosen library (or `simple-icons` for a brand), re-pick, and rerun the final batch until clean; never carry a missing icon forward or switch libraries to fill it. Search only unresolved concepts; never load or rebuild a full index.

### g. Typography Plan Confirmation (Font + Size)

🚧 **GATE**: apply the chosen custom behavior and only the already-loaded `visual_style_references` files. The title carries the character; the body may stay neutral.

**Family selection**: user/template typography is authoritative — repeat fixed stacks with `typography.fixed: true` in every direction (reasonable repetition is non-blocking; no extra font round). Each direction carries `heading` / `body` `primary`, `css`, and a positive `body_size`, plus `english` only for a non-English deck. Delivery target, concrete-face naming, family count, brand/web faces, near-equivalent splits, contrast/concord pairing, and the PPT-safe face recall are [`plan-core.md`](./plan-core.md) §6.2; the Confirm UI catalog is manual choice, not a whitelist. Across the direction set include both a concord and a contrast pairing unless the user or template fixes the stack.

**Role extension after confirmation**: add recurring roles under [`plan-core.md`](./plan-core.md) §6.2 while authoring §IX and §IV; confirmation is not reopened, and one compact `Role rationale` line in §IV names any added role.

**Size anchors — px only** ([`plan-core.md`](./plan-core.md) §6.2 owns the ratios and the recurring-role scan). **Mandatory**: take Confirm UI `body_size` / `sizes` verbatim — a manually edited anchor stays pinned and a canvas change never rescales it — and declare every recurring role before locking so no structural text depends on Executor's display exception.

#### Mathematical and hyperlink content

Record equations and links in §IX under [`plan-core.md`](./plan-core.md) §3 — never a policy, manifest, PNG, §VIII row, or lock entry; Executor owns the text-versus-native decision and returns here only for a content-level correction.

### Resource Need and Reference Planning (non-blocking; no user confirmation)

Resource need from the roster, the native-construction Hard rule, the capability opportunity signals, and the communication-job menu are [`plan-core.md`](./plan-core.md) §5; derive §VIII rows from that need and use existing fields only (icon basis and pool in §VI; image, lettering, or illustrated-icon resources in §VIII). Each capability hands off as follows:

| Capability | Design Spec handoff |
|---|---|
| Image composition | Propose a permitted source; when selected, apply [`strategist-image.md`](./strategist-image.md), record a concise §VIII `Image pattern` in ordinary words, and state how several images relate in §IX `Images` |
| Composable illustration family | Plan transparent elements by compatible family under `strategist-image.md`, record fixed reuse or adaptive variation in §VIII `Reference`, and describe each page's carrier relationships in §IX |
| AI decorative lettering asset | Under `strategist-image.md`: preserve every exact string, group compatible marks, keep chrome/body native; the asset may carry the complete title as its display layer while a native title/subtitle stays in a separate frame wherever a searchable, selectable, or outline-visible heading is needed; never shorten copy toward a wordmark |
| Motion | Optional §IX `Motion suggestion`: the communication job, the units involved, and their meaningful order or initial → end state; effects, ids, options, and timing stay with Executor, and a suggestion never activates the custom stage |

The information-model rule, the Chart/Table vocabulary Reference, and the validation command are [`plan-core.md`](./plan-core.md) §3 and §5.2; validate every selected reference before the lock.

Write §VII as `Page | Family | Template | Usage` for each `chart|table` reference (Usage = semantic purpose; omit no-match), e.g. `| P03 | chart | line_chart | Compare the source metrics over time |`. **Native-ready boundary**: give every independent data chart and pure text-grid table in §IX `Visualization` a unique page-local `kebab-case` key and write one `Native-ready` map `<key>=yes|no; ...`; the `yes` / `no` criterion and what stays unlisted are [`plan-core.md`](./plan-core.md) §5.2.

### h. Image Source Recommendation

Source ids (`none` / `provided` / `ai` / `web` / `placeholder`), the credentials Hard rule, and visual grounding before `none` are [`plan-core.md`](./plan-core.md) §5.1; Generate Step 5 is the first capability check.

If `images/` is non-empty, run `python3 scripts/analyze_images.py <project_path>/images` and read `analysis/image_analysis.csv` before recommending (rerun after changes).

**Proactive illustrated icons and lettering**: before each Stage-2 `recommend.image_usage`, run [`strategist-image.md`](./strategist-image.md)'s illustrated-icon and decorative-lettering candidate scan over the complete roster. A selected mark may be the sole AI job and may support an `ai` recommendation in `image_notes.value`. Zero is valid without explanation; explicit no-AI or editable-only requirements win.

**Recommendation output**: `recommend.image_usage` is one source id or an array (`none` exclusive). `image_notes.value` carries each source's intended jobs, authoritative assets, preferred/avoided imagery, placeholder tolerance, and — when `ai` is proposed — how generated visuals contribute, including any anticipated illustration, illustrated-icon, or lettering role: an open strategy, not an enum, allowlist, page assignment, count, or manifest. On confirmation map `ai→ai`, `web→web`, `provided→user`, `placeholder→placeholder` into §VIII `Acquire Via`.

**Always-on decision module; conditional resource extension**: the fixed planning batch (this module, the decision indexes, the icon contract, the Chart/Table vocabularies) is loaded before the directions. After the three intents are frozen, [`strategist-image.md`](./strategist-image.md) authors one complete custom rendering per direction before AI is decided. `recommend.image_usage` is derived independently from source needs; a confirmed non-`none` set activates its resource-planning sections, and confirmed `none` writes no rows while keeping the rendering candidates and composition vocabulary.

### Speaker Notes Requirements

Resolve the effective outcome as latest explicit instruction → final Stage 2 `proactive_speaker_notes` → default `true`; enabled Narration Audio requires enabled notes and names that dependency in provenance.

| Effective outcome | Design Spec §X |
|---|---|
| `enabled` | Record filename policy, content/source handling, total duration, notes style, and presentation purpose |
| `disabled` | Keep §X and write `Generation: disabled`; do not invent note requirements |

Note files match SVG names (`01_cover.svg` → `notes/01_cover.md`; `notes/slide01.md` stays compatible); split files carry no `#` headings while `notes/total.md` does. A user-marked final/literal script keeps its wording and order: segment it by scene while resolving §IX, record source and verbatim policy in §X `Content`, and let Generate freeze `notes/total.md` after the roster and lock pass — never copy it into on-slide `Content`.

---

## 2. Mode & Visual-Style Catalogs (Reference for Confirmation Item d)

Mode: [`modes/_index.md`](./modes/_index.md) → `pyramid` / `narrative` / `instructional` / `showcase` / `briefing`. Visual style: [`visual-styles/_index.md`](./visual-styles/_index.md) → presets + `custom`. Basis selection follows the §d Hard rule; Executor later reads one locked preset file or a custom's exact references ([`generate-pptx`](../workflows/generate-pptx.md) Step 6).

---

## 3. Color Selection Reference

Owned by [`plan-core.md`](./plan-core.md) §6.1: precedence, proportion, anchor tiers, and polarity ramps live there; §e owns the six confirmed roles.

---

## 4. Composition Reference and Motif

The §IX `Composition` line and the cross-page motif recommendation are [`plan-core.md`](./plan-core.md) §4: both are References Executor adjusts or declines; the motif's continuity job and reuse mode go in §III `Theme`.

---

## 5. Template Flexibility Principle

Free-design patterns are starting points, not quotas: recommend a macro direction from reading mode, page rhythm, and content, and leave exact composition and spacing to Executor within the locked typography anchors. An active template workspace is governed only by [`strategist-template.md`](./strategist-template.md).

## 6. Workflow & Deliverables

### 6.1 Content Planning Strategy

Outline and, when enabled, notes strategy follow the locked mode ([`modes/_index.md`](./modes/_index.md), then the preset file or the custom's references plus behavior). Within any mode, reading-mode carriage and per-block expression are [`plan-core.md`](./plan-core.md) §2 and §3: record the mode as **Reading Mode** in `design_spec.md §I` (lock key `consumption_mode`), and write §IX at the confirmed depth so Executor can retain it with the lock until context invalidation.

### 6.2 Planning Artifact Content

Generate Step 4 owns the sequence: `design_spec.md` is the complete human-readable decision, `spec_lock.md` its context-selected execution subset; `result.json` is consumed once and never reopened; refinement edits the same Design Spec, and the files are never parallel interpretations. A later explicit notes/animation/narration instruction updates only the affected §I outcome and provenance, after Generate's notes/audio dependency gate, without reopening Confirm UI or touching the lock. Animation provenance is final Stage 2 `false`, explicit objects-off, or explicit all-motion-off; only the last includes transitions.

1. With the retained final confirmation, read `${SKILL_DIR}/templates/design_spec_reference.md`.
2. Compose the whole Design Spec in context and create `design_spec.md` once from the schema marker through §X. §I records production mechanics — one effective outcome plus provenance each for Speaker Notes, Custom Animations, and Narration Audio (latest explicit instruction → final Stage-2 proactive value → default enabled / disabled / disabled; narration enabled requires notes). §IX is the complete ordered roster: title, core message, **Audience move**, **Relationships** (the page's semantic units and their source-stated relationship, or `none`, at every depth), content at the confirmed depth, optional Composition Reference, exact mathematics, capability recommendations, visualization/image references, sourced `Fact IDs`, and `Data class: scenario` for invented data. After Gate 1 and any refine approval, roster ids/count/order and semantic content are authoritative (a continuous run may repair within the confirmed range per `executor-base.md` §2.1); everything else in a block is a Reference under §1 Confirmed-value semantics unless labeled `(binding)`.
3. Compare `design_spec.md` with the final confirmation field by field and repair every omission before refinement or the lock.
4. When enabled, run [`refine-spec`](../workflows/stages/refine-spec.md) on that file; no lock before explicit approval.
5. Read `${SKILL_DIR}/templates/spec_lock_reference.md` and create or resynchronize the lock once from the approved Design Spec and context — identity, refinements, stable roles and routing; no page-local values, no reopened evidence, no new recommendation.

| Confirmed state | Required Design Spec realization |
|---|---|
| Communication contract and `content_divergence` | §I records the contract; §IX realizes every stated purpose, outcome, priority, and source-treatment constraint |
| Canvas, reading mode, and page count | §I records the confirmed input and exact resolved count; §IX contains that many ordered pages, one slide each |
| Mode, visual style, palette, and generated-image rendering | §I and §III record the selected direction as identity anchors; core roles stay stable, page-local expression contextual |
| Typography, including derived family overrides and every visible role size | §IV records Character/upgrade References, resolved heading/body stacks, recurring support-role stacks justified by §IX, and exact `body`, `title`, `subtitle`, `annotation` anchors; never drop a declared override or re-derive an anchor |
| Icons | §VI records the confirmed base library / no-icon / custom path and content-driven `simple-icons` marks; illustrated-icon families are §VIII AI resources |
| Confirmed image-source set, `image_notes`, AI strategy | §VIII uses only permitted sources and includes every explicitly required source, asset, or page role; an unused permitted source needs no row |
| Natural-language template application | §I records it; layout/prototype choices realize it without dropping a requested use or exclusion |
| AI-image path, generation mode, refine-spec toggle | §I records them as production mechanics for their owning stage |
| Proactive notes, animations, narration | §I records the three effective outcomes with provenance; §X records note requirements or `Generation: disabled`; none enters the lock; §IX Motion suggestions stay advice |
| Explicit final/literal narration script | §IX segments by scene with a supporting visible state each; §X records source and verbatim policy; Generate freezes `notes/total.md` after Gate 2 |

⛔ **GATE 1 — active-decision fidelity**: no lock until the Design Spec passes that comparison and any refinement is approved. Missing or substituted values, unapplied revisions, or silently changed semantic types block despite schema validity; bounded Reference adaptation and unused Permission remain valid.

⛔ **GATE 2 — lock context fidelity**: the lock may normalize syntax and add justified recurring roles but never changes identity, discards a refinement, introduces a direction, or becomes a field copy or allowlist. On contradiction return to Gate 1 (fresh recovery reads persisted final evidence once only when active state is absent).

**Execution lock content**: `spec_lock.md` carries communication, stable color/type anchors, icons, images, page rhythm, Chart/Table references, and route-specific structure; qualitative relationships stay in §IX. Grammar — section set, typography projection (`title_family` + `body_family` + every `<role>_family` and size anchor), `page_visualizations`, flat/structured `pptx_structure` — is [`spec_lock_reference.md`](../templates/spec_lock_reference.md) §2–4. Never re-derive a confirmed anchor, collapse distinct stacks into `font_family`, or drop a recurring role.

**Lock vs page-local values**: derived paint and sparse local garnish may stay in one SVG. New base colors, structural fonts, resources, or recurring identity patterns require upstream repair, and Executor never reverse-projects a local choice as planning fact.

**Hard rule — a lock prohibition is the user's**: `forbidden` takes the technical baseline plus prohibitions the user stated in their own words, each quoted verbatim and tagged `(user)` ([`spec_lock_reference.md`](../templates/spec_lock_reference.md) §2). A confirmed direction's behavior stays identity prose and is never projected into a prohibition.

- **Communication trace is mandatory**: keep the full contract in §I and project only `audience`, `objective` (one execution sentence preserving intent and the `audience_outcome` success condition), `core_message`, and `consumption_mode` into `spec_lock.md communication`. Before finalizing §IX, every named purpose has an outline obligation and every Slide block — cover, divider, closing included — has an `Audience move`; a page that advances nothing is merged, rewritten, or cut. Tools enforce presence, not quality.
- **Custom behavior is concise and executable**: one resolved `mode_behavior` / `visual_style_behavior` sentence or short paragraph plus exact `*_references` only when catalog entries are used; no selection history.
- **page_rhythm is mandatory**: one of `anchor` / `dense` / `breathing` per §IX page — what breaks the uniform card-grid feel; consumer omission behavior is `executor-base.md` §2.2's.
- **Fact IDs and scenario labels**: list the stable IDs actually used per page, never one whose claim is absent; mark invented KPIs, targets, and ratios `Data class: scenario` and say which values they are.
- **Whole-roster rhythm check, cover impact, and closing impact** are [`plan-core.md`](./plan-core.md) §4 and apply while composing §IX; the cover hook and closing takeaway bind, their compositions are References, and Beautify preservation is exempt.
- **pptx_structure and page_visualizations**: free-design, brand-only, and `template_reuse_scope: style` write `mode: flat` and omit every structured mapping section; `mirror|layout` writes `mode: structured` with `template_adherence` and the four mapping sections under [`strategist-template.md`](./strategist-template.md). Project at most one §VII `P<NN>: <chart|table>/<key>` per page; grammar in [`spec_lock_reference.md`](../templates/spec_lock_reference.md) §3–4.

---

## 7. Project Boundary

Generate owns project initialization and supplies `<project_path>`; Strategist writes only the two planning artifacts at that root plus explicitly triggered resource manifests.

## 8. Handoff

After validation, return to the Generate Step 4 checkpoint; the route owns whether Step 5 runs and how execution proceeds.
