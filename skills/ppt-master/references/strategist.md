# Role: Strategist

## Core Mission

Receive source documents, analyze content, plan the design, and output the **Design Specification & Content Outline** (`design_spec`) plus its execution lock.

## Pipeline Context

| Previous Step | Current | Next Step |
|--------------|---------|-----------|
| Project creation + template-candidate preparation complete | **Strategist**: Stage 1 communication/template confirmation → installation handoff → Stage 2 solution + Design Spec | Image_Generator or Executor |

Canvas formats and their typography scale start: [`canvas-formats.md`](canvas-formats.md).

---

## 1. Strategist Confirmation Stage

🚧 **GATE — whole-document authoring**: Generate Step 4 reads `${SKILL_DIR}/templates/design_spec_reference.md`, authors the complete Design Spec once, passes Gate 1, then reads `${SKILL_DIR}/templates/spec_lock_reference.md` and authors the complete lock once; no scaffolds, no placeholder patching; `project_manager.py validate` owns grammar.

⛔ **BLOCKING**: present professional recommendations for the fields below and wait for explicit user confirmation. Generate Step 3 prepares candidates only; Stage 1 confirms the communication contract and the template/free-design choice together (the recommendation independent of every candidate); the selected workspaces are installed before Stage 2.

| Stage | Items | Role |
|---|---|---|
| **1 — communication contract + template choice** | `primary_language` · `c` audience · open-ended communication intent · audience outcome · core message / delivery context (primary + optional secondary) / artifact afterlife · `content_divergence` (all prose may be blank) · `a` canvas · explicit `free_design` or `templates` choice and selected roots | confirmed together; candidates never influence the communication recommendation |
| **2 — final solution + production** (authored once from the user's *actual* Stage 1) | reading mode (`delivery_purpose`, PPT only) · `d` mode + visual style · `b` page count · `e` color · `f` icon · `g` typography · `h` image source + generated-image rendering · conditional template application · conditional AI-image acquisition path · generation mode · refine-spec toggle · `design_spec_depth` · proactive speaker notes / custom animations / narration audio | one coherent plan from the confirmed contract; exporter reuse/adherence stays internal |

Stage 1 records composite intent in prose, never one catalog label; editable prose fields are drafts — confirmation keeps the current text and blanks, and a cleared field is never repopulated. Stage 2 confirms narrative spine, reading density, page budget, visual system, image direction, production mechanics, and how an installed template is used (inspecting only project-local specs and prototypes); it never chooses or installs a template. Author the three whole-deck directions under §d, then set `design_directions.selected` to the strongest fit (with an installed template, the viable direction that best expresses its resolved context under [`strategist-template.md`](./strategist-template.md)) as the actual zero-based index (`0`, `1`, or `2`); array order never determines preference. Every direction carries a rendering candidate whether or not AI is proposed; generated images inherit deck colors. Proactive defaults are notes `true`, custom animations `false`, narration `false`; an earlier explicit instruction overrides the matching recommendation, and narration requires notes. Recommend `design_spec_depth: brief` (the same author draws the pages) and `complete` only for `split`, `refine_spec: true`, a preservation profile, or a requested hand-off document. Author each stage once; launch/wait mechanics are in [`generate-pptx.md`](../workflows/generate-pptx.md) Step 4.

**Default — continuity-aware whole solution (may override when a scene reset communicates better)**: before recommending page count or production mechanics, judge whether adjacent beats can stay within one recognizable mental map while a visible state changes; where that lowers cognitive switching and motion has a named job, let it shape the spine, rhythm, visual approach, and notes/narration segmentation, and recommend `proactive_custom_animations: true`; plan such neighbors as visible states of one scene — recognizable anchors kept, the delta legible, each enabled notes/narration segment aligned with its state, every state page still carrying content and an `Audience move`; reset when the map changes or continuity adds nothing. One positive signal, not the only one; topic or wording repetition alone is insufficient, and a `Motion suggestion` never changes the effective outcome.

**Hard rule — Stage-1 source boundary**: build the communication recommendation only from the current request, source facts, conversation constraints, and project-initialization state — before loading index summaries for a chat listing and without reading any candidate spec, prototype, asset, or template canvas; template controls on the same surface are confirmation state, not evidence. Load [`strategist-template.md`](./strategist-template.md) only after Stage 1 is confirmed and the selection installed.

> **Execution discipline**: Stage 1 is the first BLOCKING checkpoint; its receipt is intermediate and never ends the task. In the same run, install/fuse the selection, complete the handoff, author fresh Stage 2, and enter the final wait; after final confirmation proceed without another pause unless refinement is enabled — the only opt-in exception is [`refine-spec`](../workflows/stages/refine-spec.md), offered with the split-mode note and never entered unprompted.
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

**Authority chain — materials → Strategist preparation → realization**: user inputs bound materials and acquisition. Strategist owns sufficiency, gap-filling, and selection — roster and content, `Relationships`, prepared resources and paths, structured-template routing, fonts, palette anchors, icon library/stroke and curated pool, crop bans, and optional Chart/Table references — and sketches macro composition, focus, and continuity as Reference (binding only when labeled `(binding)`), never a carrier mix, element geometry, or authoring method. Topic research and its two-artifact pair may precede confirmation (facts URLs never auto-expanded; one adopted webpage may become a reviewable source package only after normal image search fails). AI/web/slice acquisition follows final confirmation plus §VIII/lock; icons are synced during authoring without page assignment; before Executor every resource has a path and a terminal or `Needs-Manual` state. Native construction is an Executor capability, not a resource; missing material returns upstream, never invented or substituted.

⛔ **GATE — final confirmation is consumed once into the Design Spec**: use the complete final object already read by Generate Step 4 (`stage: final`, `status: confirmed`) or the chat path's final visible summary; never reopen `result.json` during Design Spec or lock authoring. Consume every present field by its semantic type and owner without omission, substitution, or silent strengthening/weakening; decide only what was left unconfirmed; keep a cleared prose field empty; an unhonorable requirement stays visible and follows [`failure-recovery.md`](../workflows/governance/failure-recovery.md).

### a. Canvas Format Confirmation

Recommend from the scenario and project initialization ([`canvas-formats.md`](canvas-formats.md)). A template canvas is not Stage-1 evidence; Stage 2 later checks whether selected structure serves the confirmed canvas.

### b. Page Count Confirmation

**Default — open `page_count` as a narrow range (may override when an exact count is supplied or locked)**: narrow enough to judge at a glance. After Stage 1 choose one exact count from source volume, audience outcome, delivery context/afterlife, and reading mode, then author the complete §IX roster; *exactly*, *1:1*, or preservation fixes it. After Gate 1 and any refine approval, the roster's ids, count, and order are invariant — Executor never adds, drops, merges, splits, or reorders without Design Spec repair or reconfirmation.

### c. Communication Contract Confirmation

Seed these as open-prose recommendations when the source and request support them; the user may retain, edit, or clear every field, and none requires a non-empty answer:

| Field | Question it answers |
|---|---|
| `audience` | Who exactly must receive this communication, and what do they already know / care about? |
| `communication_intent` | What must the presentation accomplish? It may combine several purposes and state priority or sequence. |
| `audience_outcome` | What observable change means the communication succeeded — what will the audience know, understand, believe, decide, or do? |
| `core_message` | Which claim(s), decision ask(s), or action(s) must land even if little else is remembered? |
| `delivery_context` | What is primary — presenter-led, reader-led, hybrid (which leads), or recorded/self-running (no live presenter; narration, timing, transitions, playback)? What secondary use, occasion, and time constraint remain? One open field, never an enum. |
| `artifact_afterlife` | What must the file support afterward — review, approval, audit, archive, hand-off, reuse, or nothing? |

**Communication intent is open-ended**: *inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off* are prompts, never a checkbox list or a `primary_job`; several purposes keep their relationship in prose ("report progress and expose risk first; then obtain a decision"). The contract is not the narrative mode: intent says what change is needed, `mode` is one Stage-2 way to organize the argument.

**Hard rule — confirmed current value wins**: submit every Stage-1 prose field exactly as it stands at confirmation; blank means no explicit constraint (downstream judgment from source and request) and is never restored to the recommendation. A profile-declared `locked: true` field is the only read-only exception.

**Reading mode** (PPT only, Stage 2): `text` (read-close) / `balanced` (business, default) / `presentation`, kept under the compatibility key `delivery_purpose` but reasoned about as information carriage — how meaning divides among page, visuals, presenter, and enabled notes — driving page grammar, granularity, density, and the §b recommendation; the §g body baseline is a consequence, not the definition.

**Material divergence** (`content_divergence`): a free-text Stage-1 field the user fills in their own words — how closely the deck follows the source versus how freely it reshapes it — never a set of options and never recommended from source analysis; blank is a balanced default. Read it as a spectrum from *stay close* (track structure and wording, tune for clarity) through *balanced* (re-architect into a narrative under the locked mode, keeping all substance) to *free* (regroup, reframe, expand, connect, invent structure and transitions). **Hard rule — facts stay sourced however free the user asks**: divergence develops what is in the source and never licenses outside facts, figures, or claims — that is `topic-research`'s job; `mode` and divergence are orthogonal. Apply it only while authoring §IX and record it in `design_spec.md §I`, never in the lock; Beautify seeds and locks verbatim preservation, Edit Native PPTX does not surface it.

**Fact provenance contract**: when `sources/*.facts.json` exists, read it before outlining and cite its stable `fact_id` values as `Fact IDs: F001, ...` on every §IX page that uses an external quantitative or factual claim; invented demo KPIs, ratios, targets, and roadmap numbers carry `Data class: scenario` and never a `fact_id`. One page may hold both classes as long as each number's class is unambiguous.

When authoring §IX, translate every purpose named in the intent into an outline obligation (a reasoning checklist, not a classifier; preserve the user's priority and sequence):

| Intent named in the prose | Outline must enable |
|---|---|
| Inform | Relevant facts with enough context to know why they matter |
| Explain | Mechanism, relationship, cause, or meaning made traceable |
| Persuade | Claim + evidence + material objections / alternatives |
| Decide | Explicit decision ask + options + criteria + trade-offs + consequence of delay |
| Align | Shared frame + priorities + owners + next steps |
| Teach | Prerequisites + sequence + worked application / check for understanding |
| Report and account | Baseline + progress + variance + evidence + risk + ownership |
| Mobilize | Urgency + agency + concrete action + immediate next step |
| Record and hand off | Context + decisions + status + owners + unresolved items + durable provenance |

### d. Style Objective Confirmation

**Stage 2 only** — tools that serve the confirmed scenario, never substitutes for defining it. Two independent layers, each locking one preset or `custom`; output `d. Mode: <mode> + Visual style: <visual_style>`.

**Hard rule — top-down direction construction**: author three complete, project-fit solution intents from the confirmed contract and source before touching any catalog basis; the three mode/style/rendering indexes are the only basis selectors. Freeze each direction's exact reference ids from the index summaries, read once only the deduplicated union of those detail files, then write the behaviors. Every direction serializes `mode: custom`, `visual_style: custom`, and `image_strategy.rendering: custom`, each with visible non-empty behavior prose; a custom may use catalog material in any way or none — one preset carried unchanged is valid — and references record only actual sources, each owning a distinct executable contribution (never a decorative second basis). The three directions are plainly different designs *before* any field is written: whichever components a design requires carry the difference, and mode, style, rendering, bases, color, type, and icons are each free to coincide — a different name, note, or reference count alone is no difference, and identical projections are not three solutions. Where authoritative truth fixes components, the open ones carry the difference; where nothing is open, keep the projections identical and state that boundary. Never force safe / shifted / bold archetypes, glob a catalog, read an unselected sibling, or write bespoke prose as an enum value.

#### Layer 1 — Communication mode

🚧 **GATE**: [`modes/_index.md`](./modes/_index.md) is the sole mode-basis authority; read only the frozen sibling files once; a novel mode reads none.

The narrative + persuasion skeleton: one preset from `pyramid` / `narrative` / `instructional` / `showcase` / `briefing`, or `custom` with behavior — one value per deck, never several simultaneous modes.

- **User outline or structure** → preserve its facts and relationships, then apply `content_divergence`; an ordinary outline is a Reference (regroup, reorder, retitle when the contract benefits) and becomes authoritative only when presented as the final page plan or with an explicit ask to keep order, titles, or wording — record that promotion in `design_spec.md`. Still lock a mode for register and voice; `briefing` imposes the least.
- **Beautify** ([`beautify-pptx.md`](../workflows/profiles/beautify-pptx.md)) → extracted content is authoritative and verbatim: one source slide = one §IX page in order, every block transcribed word-for-word, never reshaped, condensed, merged, split, or reworded; all three mode behaviors keep that boundary and may share `briefing`. Color (e) and typography (g) are whatever the beautify plan confirmed (source identity by default) locked as truth; charts, tables, and images are regenerated from extracted data in the inherited style with values frozen (catalog references in §VII, unmatched plans in §IX, pictures in §VIII). Layout, hierarchy, rhythm, and rendering are what gets redesigned.
- **No user structure** → derive each solution from `communication_intent`, `audience_outcome`, source texture, and delivery context, then project its custom mode; directions may share bases or behavior when the whole solutions differ.

Record the mode and rationale in `design_spec.md` (with every catalog basis a custom uses), then project `- mode:` — and for custom `- mode_behavior:` plus `- mode_references:` only when catalog material is used — to `spec_lock.md`; Executor reads only those references.

#### Layer 2 — Visual style

🚧 **GATE**: [`visual-styles/_index.md`](./visual-styles/_index.md) is the sole style-basis authority; read only the frozen sibling files once; a novel style reads none.

The visual aesthetic — shape language, decoration density, whitespace rhythm, typographic character, texture — anchoring e, f, g, and h. It carries no color (it governs how the HEX locked at `e` is *used*), and when the deck has AI images the style's paired rendering keeps layout and illustration in one aesthetic.

- **User named a style** (chat, template, beautify) → it is truth: the required basis or inherited anchor in every behavior; derive each direction through the open dimensions, and when all variation is forbidden let the other components carry the difference and say so in the note.
- **No description** → project one complete custom aesthetic per solution, written as the carriers and techniques it *uses* — containers, icons, swatches, shadows, gradients, image treatments, native shapes — never as a list of avoidances (a locked prohibition removes that tool from every page; write one only when the user or material requires it). Behaviors differ when the designs genuinely differ, never to meet a quota; no forced bases, safe-to-bold ladder, or deliberate extreme. Give each direction a `name` and one- or two-sentence `note` in the confirmed UI language (plain keys); Confirm UI's localized labels such as `瑞士极简`, `柔和圆角`, `编辑出版` are optional vocabulary, never a required mapping, and the note exposes no catalog ids.

**Forbidden — a non-catalog name as `visual_style`**: the field is literal `custom`; prose lives in `visual_style_behavior` and `visual_style_references` holds only first-column catalog ids (a "Paired rendering" id such as `flat` or `digital-dashboard` is a rendering, not a style). Generic words — flat / modern / clean / simple / minimal — are not behavior: state the executable shape language, composition, density, whitespace, typography, and texture, which may match one preset exactly.

Record the style and rationale in `design_spec.md`, then project `- visual_style:` — and for custom `- visual_style_behavior:` plus `- visual_style_references:` only when catalog material is used — to `spec_lock.md`.

**Conditional template workspace**: when the Stage-1 choice is installed under `<project_path>/templates/`, read [`strategist-template.md`](./strategist-template.md) before completing Stage 2 — installed spec and prototypes only, never the library root. It owns the editable application plan, confirmed-value consumption, prototype selection, reuse/adherence derivation, inherited precedence, and structured-lock planning; it decides how to use the template, never which one.

**Downstream effect**: e / f / g / h realize mode + style — e.g. `showcase` + `dark-tech` → one luminous accent on a dark field, a clean sans paired with mono, minimal glow icons, the `digital-dashboard` rendering.

### e. Color Scheme Recommendation

**Hard rule**: user-specified colors are truth — lock supplied HEX, brand colors, or natural-language directives (templates follow inherited-design precedence). Every direction fills all six roles (`background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, `body_text`), repeating fixed roles and varying only open ones; never an empty palette. In §III derive the standard `secondary_text` and `divider` neutrals and project them to `spec_lock.md colors`; §V fixes the five deck-wide spacing anchors.

**Reference — not a constraint**: no universal palette — user / brand → active template → project-specific proposal from content and style; 60-30-10 is the starting proportion, body contrast at least 4.5:1 (WCAG AA), hue count follows encoding, style, and natural assets; how color is *used* on a page (fields, gradients, accent placement, mood) is Executor's craft. `scripts/config.py` industry anchors (finance/business navy `#003366`, technology bright blue `#1565C0`, healthcare teal `#00796B`, government red `#C41E3A`) and polarity ramps (positive `#2E7D32 → #4CAF50 → #81C784`, warning `#F57C00 → #FFA726 → #FFD54F`, negative `#C62828 → #EF5350 → #E57373`) are recall aids, never default locks; brand identities come from a Brand/Deck workspace, never a memorized list. Strategist owns reusable positive / warning / negative roles; Executor derives tints, shades, alpha, gradients, and effects.

**Lock recurring semantic anchors, not every paint**: add neutral roles the style and page plan give a stable meaning — `surface`, `grid`, `scrim`, `overlay`, `block-shade` — and leave page-local tints, gradient stops, shadow/glow colors, and one-off tones to execution, promoting one only when it becomes a reusable named role.

| Style trait | Extra neutral tiers to lock |
|---|---|
| Layers panels / charts (e.g. `data-journalism`, `swiss-minimal`) | `surface` (panel lift), `grid` (hairline, lighter than dividers) |
| Text over imagery / dark field (e.g. `photo-editorial`, `glassmorphism`, `dark-tech`) | `scrim` / `overlay` for legibility |
| Print / hand-drawn fills (e.g. `chalkboard`, `zine`) | `block-shade`, one step off the field |

### f. Icon Usage Confirmation

One single-select base identity, not a material whitelist:

| Option | Approach | Suitable Scenarios |
|--------|----------|-------------------|
| **A** | Emoji | Casual, playful, social media |
| **B** | Built-in generic icon library | Recurring compact semantic cues in one coherent SVG style |
| **C** | Custom project icons | Supplied, template-carried, or imported assets |
| **D** | No base icons | No shared generic base-icon identity is selected |

AI illustrated icons are not a base option, add-on, field, or key — like decorative lettering they are a downstream image carrier §h and [`strategist-image.md`](./strategist-image.md) may choose, with slices under `images/` (never `icons/`, `icons.inventory`, or `<use data-icon>`); they may coexist with base icons. Real brand marks are identity assets: any company, product, service, or social identity in the content may use its exact supplied or `simple-icons` mark under every base choice, with no extra option. Library inventory, prefixes, and placeholder syntax: [`../templates/icons/README.md`](../templates/icons/README.md).

**Mandatory — bundled SVG resources**:

1. At confirmation decide only the generic library and stroke. One primary stylistic library per pool (`icon_sync.py` rejects mixed batches): `chunk-filled` (fill, straight-line geometry, heavy, architectural), `tabler-filled` (fill, bezier curves, smooth, approachable), `tabler-outline` (stroke, airy, best for screen), `phosphor-duotone` (main shape + 20 % backplate, layered). A missing generic icon is replaced within the same library. `simple-icons` is never a Confirm UI choice: it holds brand marks only and may accompany any selection including `none`. This governs catalog selection, not the prepared pool — user, template, imported, custom, and previously prepared files under `<project_path>/icons/` stay valid whatever their namespace.
2. For a stroke library (currently `tabler-outline`) lock one deck-wide `stroke_width` from `{1.5, 2, 3}` (default `2`).
3. After approval, when writing §VI / the lock, materialize the curated pool before Executor starts (Executor cannot sync; which icons a page uses is realization, never a preassignment). Put known basenames in the final batch; search an uncertain one only inside the chosen library (or `simple-icons` for a brand) by the drawable object, never the abstract concept ([README § Searching for Icons](../templates/icons/README.md)); copy and validate in one batch — `python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name> …]` — keeping each successful case-sensitive `lib/name` (bundled basenames are lowercase); record each synced path with broad scenarios in §VI and the same pool, primary library, and any `stroke_width` in `spec_lock.md icons` (`simple-icons/*` ids join the inventory without becoming a second library; other prepared icons stay usable).

🚧 **GATE — missing icon = re-pick now**: on non-zero exit, search the missing concept only in the chosen library (or `simple-icons` for a brand), re-pick, and rerun the final batch until clean; never carry a missing icon forward or switch libraries to fill it. Search only unresolved concepts; never load or rebuild a full index.

### g. Typography Plan Confirmation (Font + Size)

🚧 **GATE**: apply the chosen custom behavior and only the already-loaded `visual_style_references` files. The title carries the character; the body may stay neutral.

**Family selection**: user/template typography is authoritative — repeat fixed stacks with `typography.fixed: true` in every direction (reasonable repetition is non-blocking; no extra font round). Each direction carries `heading` / `body` `primary`, `css`, and a positive `body_size`, plus `english` only for a non-English deck. Delivery target: an explicit user/template target first, otherwise Windows Microsoft PowerPoint (owner: [`shared-standards-core.md`](./shared-standards-core.md) §4.1) — the authoring host's installed fonts never select a face; name concrete faces installed or approved on that target (the Confirm UI catalog is manual choice, not a whitelist); at most four families; a brand/web face leads only after user-confirmed installation, otherwise export a safe face and keep it as a Design Spec reference (fonts are not embedded; CSS tails are preview aids, not PowerPoint fallbacks). Avoid near-equivalent splits (YaHei↔PingFang, SimSun↔Songti, Arial↔Helvetica↔Segoe UI, Times↔Times New Roman). Fonts in one deck form contrast (different family, weight, or proportion) or concord (one family throughout); across the direction set include both a concord and a contrast pairing unless the user or template fixes the stack, and never default to title = body without a reason.

**Reference — PPT-safe faces (recall, not a whitelist; name one concrete face per script, never a comma stack)**: CJK sans `Microsoft YaHei` / `SimHei`, CJK serif `SimSun` / `FangSong` / `KaiTi` (their macOS counterparts `PingFang SC` / `Heiti SC` / `Songti SC` are preview aliases, never the named face), Latin sans `Arial` / `Calibri` / `Segoe UI` / `Verdana` / `Trebuchet MS`, Latin serif `Times New Roman` / `Georgia` / `Cambria` / `Palatino` / `Garamond`, mono `Consolas` / `Courier New`, display `Impact` / `Arial Black`. Let the locked style's character pick the axis and lead the title — `Microsoft YaHei` / `Arial` are the neutral members, never the automatic lead; a neutral sans title where the style asks for character is the failure to avoid. Non-pre-installed directions — retro/pixel Press Start 2P / VT323, rounded Nunito / Quicksand / OPPO Sans (safe substitute `Trebuchet MS` / `Verdana`), modern web Inter / HarmonyOS Sans / Source Han, calligraphic 隶书 / 华文行楷 / 华文新魏 (safe substitute `KaiTi` / `FangSong`, titles only), brand faces — need target installation or stay Design Spec references.

**Role extension after confirmation**: while authoring §IX and §IV, add a lowercase snake_case role with an exact stack only for a recurring role that materially needs a different family (`annotation`, `footer`, `footnote`, `data`, `emphasis`, `quote`, `code`), coherent with the confirmed heading/body system and locked style; one-off garnish stays omitted, confirmation is not reopened, and one compact `Role rationale` line in §IV names any added role.

**Size anchors — px only**: every layer carries bare px; PowerPoint pt (`px × 0.75`) is an export result. **Mandatory**: take the initial body anchor and sanity band from [`canvas-formats.md`](canvas-formats.md) § Typography Scale Start (never rederived here), and take Confirm UI `body_size` / `sizes` verbatim — a manually edited anchor stays pinned and a canvas change never rescales it.

| Recurring role | Ratio to body |
|---|---:|
| Cover title / single-focus hero | 2.5–5× |
| Chapter title | 2–2.5× |
| Page title / KPI hero | 1.5–2× |
| Subtitle | 1.2–1.5× |
| Lead / subheading | 1.1–1.4× |
| Body | 1× |
| Annotation | 0.7–0.85× |
| Footnote / page number | 0.5–0.65× |

Scan §IX before locking and declare every recurring role (`lead` at least body size; `footnote`; chart annotations when used), one deck-wide anchor each, snapped to clean even px (body 24 → title 42, subtitle 32, lead 30, annotation 18, footnote 16). Executor may vary one occurrence within ±2 px; a short non-structural Hero/Display size may stay undeclared for at most two planned occurrences, and the third requires a named slot — structural text never uses that exception.

#### Mathematical and hyperlink content

Record every source-backed equation under `Mathematical content` in the applicable §IX block as a LaTeX body without `$…$`, `$$…$$`, `\(…\)`, or `\[…\]` delimiters — never classified as inline or block, never invented for decoration, and never a policy, manifest, PNG, §VIII row, or lock entry; Executor owns the text-versus-native decision and returns here only for a content-level correction, including when the documented Microsoft 365 input profile cannot preserve the planned content. Record every explicit or source-backed link as the linked text/object plus its exact absolute URI or 1-based same-deck slide target — never guessed, never carrier-selected, never a manifest or lock entry; Executor authors it under [`native-hyperlinks.md`](./native-hyperlinks.md).

### Resource Need and Reference Planning (non-blocking; no user confirmation)

**Default — resource need from the roster (may stay implicit when a page's need is obvious)**: while composing the roster, decide which pages need a prepared image, lettering, or illustrated-icon resource — the jobs only a prepared file can serve — and derive §VIII rows from that need. The page's carrier mix itself (background, text, native geometry, imagery, icons, visualizations and their weights) is Executor's page decision and is never planned. Use existing fields: the icon basis and pool in §VI; an image, lettering, or illustrated-icon resource in §VIII only when the page assigns it a plausible job. Macro composition stays Reference; resource identities and explicit requirements keep their authority.

**Hard rule — native construction stays downstream**: record each page's `Relationships`, resource roles, and any useful macro composition or visual-system Reference; never inventory or bind a preset, primitive, Connector, Boolean/freeform operation, coordinates, or authoring method. A technique may appear only as optional inspiration inside a macro Reference.

| Capability | Opportunity signal | Design Spec handoff |
|---|---|---|
| Image composition | Image-as-canvas, editorial crop, collage, cutout, or meaningful focus / comparison / evidence units carry the page better than an adjacent rectangle | Propose a permitted source; when selected, apply [`strategist-image.md`](./strategist-image.md), record a concise §VIII `Layout pattern` in ordinary words, and state how several images relate in §IX `Images` |
| Composable illustration family | Pages benefit from coherent reusable title/corner ornaments, dominant anchors, supporting figures, compact illustrated-icon cues, or accents mixing with text, shapes, photos, or lettering | Plan transparent elements by compatible family under `strategist-image.md`, record fixed reuse or adaptive variation in §VIII `Reference`, and describe each page's carrier relationships in §IX |
| AI decorative lettering asset | Any stable display string — a complete long or multi-line title, cover hook, chapter word, place or product name, dish or exhibit name, year, hero number, pull quote, motif word — reads better with a material, dimensional, hand-rendered, or illustrative treatment than as ordinary text | Under `strategist-image.md`: preserve every exact string, group compatible marks, keep chrome/body native; the asset may carry the complete title as its display layer while a native title/subtitle stays in a separate frame wherever a searchable, selectable, or outline-visible heading is needed; never shorten copy toward a wordmark |
| Motion | A section/state change or continuity across adjacent pages, or a reveal / emphasis / movement order within a page, clarifies sequence, causality, comparison, or hierarchy | Optional §IX `Motion suggestion`: the communication job, the units involved, and their meaningful order or initial → end state; effects, ids, options, and timing stay with Executor, and a suggestion never activates the custom stage |

**Mandatory — information model, not source object type**: qualitative `order` / `link` / `parent` / `membership` / `contrast` / `overlap` is written on the page's §IX `Relationships` line (its units and their source-stated relationship, or `none`; no catalog key, grammar atom, coordinate, shape, or named model — Executor decides at runtime whether geometry carries it); values, dates, or durations that determine geometry are a Chart; row header × column header facts are a Table, each compared against the complete loaded vocabulary.

**Reference — Chart/Table vocabularies**: the loaded vocabularies list what can be selected; they rank nothing, and custom objects and qualitative composition stay outside them. Choose at most one flexible `family/key` per page (children and qualitative relationships stay in §IX), keep `no-template-match` in §IX when none fits (never serialized), and validate every selected reference before the lock, correcting a failed selection by re-reading the complete vocabulary/registry:

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  <family>/<key> [<family>/<key> ...]
```

Write §VII as `Page | Family | Template | Usage` for each `chart|table` reference (Usage = semantic purpose; omit no-match), e.g. `| P03 | chart | line_chart | Compare the source metrics over time |`. **Native-ready boundary**: give every independent data chart and pure text-grid table in §IX `Visualization` a unique page-local `kebab-case` key and write one `Native-ready` map `<key>=yes|no; ...` — `yes` by default, `no` only when [`native-data-interface.md`](./native-data-interface.md) §2 cannot express the object; qualitative compositions and incidental microvisuals stay unlisted.

### h. Image Source Recommendation

| Source id | Approach | Use when |
|---|---|---|
| `none` | No images | No source owns a meaningful communication job |
| `provided` | User-provided assets | Existing images carry factual, brand, product, or narrative authority |
| `ai` | AI-generated | Invented or deliberately stylized scenes, illustrations, backgrounds, metaphors, decorative lettering, or another generated treatment |
| `web` | Web-sourced | Named or evidence-bearing real-world subjects that must appear as themselves, plus generic photographic mood, background, or scene jobs |
| `placeholder` | Deferred | The image is required but will be supplied later |

If `images/` is non-empty, run `python3 scripts/analyze_images.py <project_path>/images` and read `analysis/image_analysis.csv` before recommending (rerun after changes).

**Hard rule — credentials never decide image need**: a missing `IMAGE_BACKEND`, host generation, or stock credential never justifies `none` or the deletion of a planned web role; do not inspect configuration or probe a provider — Generate Step 5 is the first capability check. When `ai` is included, preserve an explicit user path instruction, otherwise recommend `auto`.

**Default — visual grounding before `none` (may override when the full-roster review finds no image job)**: honor an explicit no-image requirement; otherwise, when the audience must recognize, experience, compare, or choose an externally verifiable subject, place, product, or setting, propose `provided` / `web`, and propose `ai` where invented or stylized expression materially improves a visual job. Mixed sources serve different roles; a rendering candidate resolves how imagery looks, never whether a real subject appears as itself.

**Proactive illustrated icons and lettering**: before each Stage-2 `recommend.image_usage`, run [`strategist-image.md`](./strategist-image.md)'s illustrated-icon and decorative-lettering candidate scan over the complete roster; a selected mark may be the sole AI job and may support an `ai` recommendation in `image_notes.value`; zero is valid without explanation, and explicit no-AI or editable-only requirements win.

**Recommendation output**: `recommend.image_usage` is one source id or an array (`none` exclusive). `image_notes.value` carries each source's intended jobs, authoritative assets, preferred/avoided imagery, placeholder tolerance, and — when `ai` is proposed — how generated visuals contribute, including any anticipated illustration, illustrated-icon, or lettering role: an open strategy, not an enum, allowlist, page assignment, count, or manifest. On confirmation map `ai→ai`, `web→web`, `provided→user`, `placeholder→placeholder` into §VIII `Acquire Via`.

**Always-on decision module; conditional resource extension**: the fixed planning batch (this module, the decision indexes, the icon contract, the Chart/Table vocabularies) is loaded before the directions; after the three intents are frozen, [`strategist-image.md`](./strategist-image.md) authors one complete custom rendering per direction before AI is decided. `recommend.image_usage` is derived independently from source needs; a confirmed non-`none` set activates its resource-planning sections, and confirmed `none` writes no rows while keeping the rendering candidates and composition vocabulary.

### Speaker Notes Requirements

Resolve the effective outcome as latest explicit instruction → final Stage 2 `proactive_speaker_notes` → default `true`; enabled Narration Audio requires enabled notes and names that dependency in provenance.

| Effective outcome | Design Spec §X |
|---|---|
| `enabled` | Record filename policy, content/source handling, total duration, notes style, and presentation purpose |
| `disabled` | Keep §X and write `Generation: disabled`; do not invent note requirements |

Note files match SVG names (`01_cover.svg` → `notes/01_cover.md`; `notes/slide01.md` stays compatible); split files carry no `#` headings while `notes/total.md` does. A user-marked final/literal script keeps its wording and order: segment it by scene while resolving §IX, record source and verbatim policy in §X `Content`, and let Generate freeze `notes/total.md` after the roster and lock pass — never copy it into on-slide `Content`.

---

## 2. Mode & Visual-Style Catalogs (Reference for Confirmation Item d)

Mode: [`modes/_index.md`](./modes/_index.md) → `pyramid` / `narrative` / `instructional` / `showcase` / `briefing`. Visual style: [`visual-styles/_index.md`](./visual-styles/_index.md) → presets + `custom`. The three indexes are the only basis selectors; freeze each direction's bases from them and read only the deduplicated detail files; Executor later reads one locked preset file or a custom's exact references ([`generate-pptx`](../workflows/generate-pptx.md) Step 6).

---

## 3. Color Selection Reference

Owned by §e: precedence, proportion, anchor tiers, and polarity ramps live there.

---

## 4. Layout Reference and Motif

**Reference — a starting sketch, never a constraint**: a §IX `Layout` line names the macro relationship the page's content suggests (one focal claim, equal comparison, dominant evidence + takeaway, parallel sequence, core + surrounding forces, wide visual + explanation) in ordinary words; Executor owns the structure and geometry that realize it (its layout-structure vocabulary lives in [`executor-base.md`](./executor-base.md) Page Expression Core) and adjusts or replaces the line freely after reading the page. Never write element-level sizes or coordinates into §IX.

Once the roster and planned resources are known, recommend a cross-page motif or element family when it can carry identity or meaning — title/corner ornaments, a directional contour, an opening, a line lattice, an oversized numeral — recording its continuity job and reuse mode in §III `Theme` and mentioning it only in the §IX `Layout` blocks that benefit; Executor owns its geometry and may decline it; no motif field, lock row, or quota.

---

## 5. Template Flexibility Principle

Free-design patterns are starting points, not quotas: recommend a macro direction from reading mode, page rhythm, and content, and leave exact composition and spacing to Executor within the locked typography anchors. An active template workspace is governed only by [`strategist-template.md`](./strategist-template.md).

## 6. Workflow & Deliverables

### 6.1 Content Planning Strategy

Outline and, when enabled, notes strategy follow the locked mode ([`modes/_index.md`](./modes/_index.md), then the preset file or the custom's references plus behavior). Within any mode:

**Reading mode controls information carriage, not communication intent** — `delivery_purpose` is the compatibility key; the body baseline is a consequence:

| Reading mode | Primary carrier | §IX page grammar | Granularity / rhythm | Speaker notes |
|---|---|---|---|---|
| `text` · read-close | page / document | complete assertions, short prose paragraphs, captions, tables, and necessary detail; bullets only for genuinely parallel or ordered items | fewer, fuller pages; leans `dense` | supplemental context, not a substitute for missing page logic |
| `balanced` · business (default) | page + presenter | one primary claim with concise explanation, structured evidence, or a necessary list | moderate granularity; mixed rhythm | interpretation and transitions |
| `presentation` | presenter + visuals | one claim per page, keywords / short phrases, a large visual or hero number; no paragraph dumps or prose compressed into fragments | more, sparser pages; leans `anchor` / `breathing` | carries explanation, transitions, and supporting detail |

With notes disabled the last column is unavailable: every required meaning stays on the page or the confirmed presenter channel. Derive the initial mode from `audience`, `delivery_context`, and `artifact_afterlife`: asynchronous review, reference, approval, audit, and leave-behind lean `text`; presenter-led projection, large rooms, launches, and classrooms lean `presentation`; hybrid review / roadshow leans `balanced`, and `balanced` when live projection and durable afterlife both matter. A confirmed `presentation` supports afterlife through notes, appendix pages, captions, and visible sources rather than crowding slides. A `presentation` deck and a `text` deck from the same source and contract must differ in page grammar, count, text volume, visual burden, density, rhythm, and notes — not only in font size; page count stays the user's call. Record it as **Reading Mode** in `design_spec.md §I` (lock key `consumption_mode`); `page_rhythm` leans are a bias, not a quota; preservation paths honor it only in styling and notes.

**Per-block expression**: the semantic relationship chooses the form — prose for cause, argument, interpretation, and narrative continuity; bullets or numbers only for genuinely parallel, ordered, or enumerable items, never because copy is long or a template exposes a list slot. In `presentation`, distill one assertion and move explanation into enabled notes (or keep it on the page when notes are off). Source texture is a secondary cue. At `complete` depth write usable phrasing into §IX; at `brief` depth one bullet per block in the phrasing that fits, leaving page copy to authoring — neither is a skeleton: every claim, fact, relationship, and qualifier is present, and written wording is preferred wording unless literal preservation applies (Executor adapts under [`executor-base.md`](./executor-base.md) §2.1). §IX is the page brief at the confirmed depth; Executor retains it with the lock until context invalidation.

### 6.2 Planning Artifact Content

Generate Step 4 owns the sequence: `design_spec.md` is the complete human-readable decision, `spec_lock.md` its context-selected execution subset; `result.json` is consumed once and never reopened; refinement edits the same Design Spec, and the files are never parallel interpretations. A later explicit notes/animation/narration instruction updates only the affected §I outcome and provenance (animation provenance is final Stage 2 `false`, explicit objects-off, or explicit all-motion-off — only the last includes transitions), after Generate's notes/audio dependency gate, without reopening Confirm UI or touching the lock.

1. With the retained final confirmation, read `${SKILL_DIR}/templates/design_spec_reference.md`.
2. Compose the whole Design Spec in context and create `design_spec.md` once from the schema marker through §X. §I records production mechanics — one effective outcome plus provenance each for Speaker Notes, Custom Animations, and Narration Audio (latest explicit instruction → final Stage-2 proactive value → default enabled / disabled / disabled; narration enabled requires notes). §IX is the complete ordered roster: title, core message, **Audience move**, **Relationships** (the page's semantic units and their source-stated relationship, or `none`, at every depth), content at the confirmed depth, optional layout Reference, exact mathematics, capability recommendations, visualization/image references, sourced `Fact IDs`, and `Data class: scenario` for invented data. After Gate 1 and any refine approval, roster ids/count/order and semantic content are authoritative (a continuous run may repair within the confirmed range per `executor-base.md` §2.1); non-literal wording, texture, layout, cover/closing composition, capability recommendations, and image/visualization patterns stay References — starting sketches Executor adjusts freely — unless labeled `(binding)`.
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

⛔ **GATE 1 — active-decision fidelity**: no lock until the Design Spec passes that comparison and any refinement is approved; missing or substituted values, unapplied revisions, or silently changed semantic types block despite schema validity, while bounded Reference adaptation and unused Permission remain valid.

⛔ **GATE 2 — lock context fidelity**: the lock may normalize syntax and add justified recurring roles but never changes identity, discards a refinement, introduces a direction, or becomes a field copy or allowlist; on contradiction return to Gate 1 (fresh recovery reads persisted final evidence once only when active state is absent).

**Execution lock content**: `spec_lock.md` carries communication, stable color/type anchors, icons, images, page rhythm, Chart/Table references, and route-specific structure; qualitative relationships stay in §IX. Grammar — section set, typography projection (`title_family` + `body_family` + every `<role>_family` and size anchor), `page_visualizations`, flat/structured `pptx_structure` — is [`spec_lock_reference.md`](../templates/spec_lock_reference.md) §2–4; never re-derive a confirmed anchor, collapse distinct stacks into `font_family`, or drop a recurring role. Derived paint and sparse local garnish may stay in one SVG; new base colors, structural fonts, resources, or recurring identity patterns require upstream repair, and Executor never reverse-projects a local choice as planning fact. **Hard rule — a lock prohibition is the user's**: `forbidden` takes the technical baseline plus prohibitions the user stated in their own words, each quoted verbatim and tagged `(user)` ([`spec_lock_reference.md`](../templates/spec_lock_reference.md) §2); a confirmed direction's behavior stays identity prose and is never projected into a prohibition.

- **Communication trace is mandatory**: keep the full contract in §I and project only `audience`, `objective` (one execution sentence preserving intent and the `audience_outcome` success condition), `core_message`, and `consumption_mode` into `spec_lock.md communication`. Before finalizing §IX, every named purpose has an outline obligation and every Slide block — cover, divider, closing included — has an `Audience move`; a page that advances nothing is merged, rewritten, or cut. Tools enforce presence, not quality.
- **Custom behavior is concise and executable**: one resolved `mode_behavior` / `visual_style_behavior` sentence or short paragraph plus exact `*_references` only when catalog entries are used; no selection history.
- **page_rhythm is mandatory**: one of `anchor` / `dense` / `breathing` per §IX page — what breaks the uniform card-grid feel; consumer omission behavior is `executor-base.md` §2.1's.
- **Fact IDs and scenario labels**: list the stable IDs actually used per page, never one whose claim is absent; mark invented KPIs, targets, and ratios `Data class: scenario` and say which values they are.
- **Mandatory — whole-roster rhythm check**: while composing §IX, compare neighbors and section arcs — chapter entries visibly reset; same-density, same-resource, or same-relationship runs are intentional sub-arcs; a repeated motif carries a continuity job; any visible-state sequence keeps a recognizable map while its next change is legible; each section follows a mode-fitting progression (including framework → explanation/evidence → judgment/action when it serves); the final arc resolves the objective before a genuine ending lowers load. Same section, equal density, one style, and precedent establish no sub-arc. Repair roster, `Layout`, and `page_rhythm` in place; preserve intentional continuity, legitimately all-`dense` material, and 1:1 order; add no filler — a `breathing` page marks a real pause and must stand alone. No field, lock row, artifact, or second pass.
- **Cover impact is mandatory**: give `P01` one concrete hook from the source's strongest claim, metaphor, number, moment, or conflict plus one optional composition Reference in ordinary words (a distilled display phrase may carry the cover while the complete title stays a native subtitle; with no suitable image, a native-SVG hook). The hook binds; the composition is a Reference. `P01` stays `anchor`, defaulting away from generic content-page templates unless content, user, or template makes a card grid, agenda, or equal-weight columns the clearest cover. Beautify preservation is exempt.
- **Closing impact (only when the deck closes)**: for a genuine conclusion, CTA, or final takeaway, name the binding takeaway plus a recommended composition; never an information-empty "Thank you", contact-only slide, or cover reprise (an explicit contact/event CTA may serve), and never an invented closing page. Preservation is exempt.
- **pptx_structure and page_visualizations**: free-design, brand-only, and `template_reuse_scope: style` write `mode: flat` and omit every structured mapping section; `mirror|layout` writes `mode: structured` with `template_adherence` and the four mapping sections under [`strategist-template.md`](./strategist-template.md). Project at most one §VII `P<NN>: <chart|table>/<key>` per page; grammar in [`spec_lock_reference.md`](../templates/spec_lock_reference.md) §3–4.

---

## 7. Project Boundary

Generate owns project initialization and supplies `<project_path>`; Strategist writes only the two planning artifacts at that root plus explicitly triggered resource manifests.

## 8. Handoff

After validation, return to the Generate Step 4 checkpoint; the route owns whether Step 5 runs and how execution proceeds.
