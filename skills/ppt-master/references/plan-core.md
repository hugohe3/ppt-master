# Planning Core

The planning craft shared by both Generate runtimes: what a deck plan decides before any page is drawn, and how to decide it well. Default Strategist reads it in the Step 4 batch and persists the results in `design_spec.md` / `spec_lock.md` ([`strategist.md`](./strategist.md) owns the confirmation stages and artifact grammar); Quick reads it in §2 and keeps the same decisions in active context ([`quick-generate.md`](../workflows/profiles/quick-generate.md) owns its commands and boundaries). "The page brief" below means §IX in Default and the transient page decision in Quick.

Everything here is a plan-only or Reference decision under [`ownership.md`](../../../docs/rules/ownership.md): content, relationships, roster, rhythm, identity anchors, and resources bind; macro composition, motif, and pattern suggestions are References the Executor adjusts freely.

---

## 1. Communication Contract

Six answers describe what the deck must do. Default seeds them as Stage-1 recommendations the user may retain, edit, or clear; Quick resolves them from the request and sources without asking.

| Field | Question it answers |
|---|---|
| `audience` | Who exactly must receive this communication, and what do they already know / care about? |
| `communication_intent` | What must the presentation accomplish? It may combine several purposes and state priority or sequence. |
| `audience_outcome` | What observable change means the communication succeeded — what will the audience know, understand, believe, decide, or do? |
| `core_message` | Which claim(s), decision ask(s), or action(s) must land even if little else is remembered? |
| `delivery_context` | What is primary — presenter-led, reader-led, hybrid (which leads), or recorded/self-running (no live presenter; narration, timing, transitions, playback)? What secondary use, occasion, and time constraint remain? One open field, never an enum. |
| `artifact_afterlife` | What must the file support afterward — review, approval, audit, archive, hand-off, reuse, or nothing? |

**Communication intent is open-ended**: *inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off* are prompts, never a checkbox list or a `primary_job`; several purposes keep their relationship in prose ("report progress and expose risk first; then obtain a decision"). The contract is not the narrative mode: intent says what change is needed, `mode` is one Stage-2 way to organize the argument.

Translate every purpose named in the intent into an outline obligation (a reasoning checklist, not a classifier; preserve the user's priority and sequence):

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

---

## 2. Reading Mode

`text` / `balanced` (default) / `presentation`, kept under the compatibility key `delivery_purpose` (lock key `consumption_mode`). **Reading mode controls information carriage, not communication intent** — `delivery_purpose` is the compatibility key; the body baseline is a consequence:

| Reading mode | Primary carrier | §IX page grammar | Granularity / rhythm | Speaker notes |
|---|---|---|---|---|
| `text` · read-close | page / document | complete assertions, short prose paragraphs, captions, tables, and necessary detail; bullets only for genuinely parallel or ordered items | fewer, fuller pages; leans `dense` | supplemental context, not a substitute for missing page logic |
| `balanced` · business (default) | page + presenter | one primary claim with concise explanation, structured evidence, or a necessary list | moderate granularity; mixed rhythm | interpretation and transitions |
| `presentation` | presenter + visuals | one claim per page, keywords / short phrases, a large visual or hero number; no paragraph dumps or prose compressed into fragments | more, sparser pages; leans `anchor` / `breathing` | carries explanation, transitions, and supporting detail |

With notes disabled the last column is unavailable: every required meaning stays on the page or the confirmed presenter channel. Derive the initial mode from `audience`, `delivery_context`, and `artifact_afterlife`: asynchronous review, reference, approval, audit, and leave-behind lean `text`; presenter-led projection, large rooms, launches, and classrooms lean `presentation`; hybrid review / roadshow leans `balanced`, and `balanced` when live projection and durable afterlife both matter. A confirmed `presentation` supports afterlife through notes, appendix pages, captions, and visible sources rather than crowding slides. A `presentation` deck and a `text` deck from the same source and contract must differ in page grammar, count, text volume, visual burden, density, rhythm, and notes — not only in font size; page count stays the user's call. Default records it as **Reading Mode** in `design_spec.md §I` (lock key `consumption_mode`) and Quick keeps it in context; `page_rhythm` leans are a bias, not a quota; preservation paths honor it only in styling and notes.

---

## 3. Content

**Default — open `page_count` as a narrow range (may override when an exact count is supplied or locked)**: narrow enough to judge at a glance. After Stage 1 choose one exact count from source volume, audience outcome, delivery context/afterlife, and reading mode, then author the complete §IX roster; *exactly*, *1:1*, or preservation fixes it. After Gate 1 and any refine approval, the roster's ids, count, and order are invariant — Executor never adds, drops, merges, splits, or reorders without Design Spec repair or reconfirmation.

**Material divergence**: how closely the deck follows the source versus how freely it reshapes it — a spectrum from *stay close* (track structure and wording, tune for clarity) through *balanced* (re-architect into a narrative under the chosen mode, keeping all substance) to *free* (regroup, reframe, expand, connect, invent structure and transitions). Default reads it from the user's own words in the `content_divergence` field; Quick reads it from the request; blank is a balanced default. **Hard rule — facts stay sourced however free the user asks**: divergence develops what is in the source and never licenses outside facts, figures, or claims — that is [`topic-research`](../workflows/stages/topic-research.md)'s job; `mode` and divergence are orthogonal.

**Fact provenance contract**: when `sources/*.facts.json` exists, read it before outlining and cite its stable `fact_id` values as `Fact IDs: F001, ...` on every §IX page that uses an external quantitative or factual claim; invented demo KPIs, ratios, targets, and roadmap numbers carry `Data class: scenario` and never a `fact_id`. One page may hold both classes as long as each number's class is unambiguous.

**Per-block expression**: the semantic relationship chooses the form — prose for cause, argument, interpretation, and narrative continuity; bullets or numbers only for genuinely parallel, ordered, or enumerable items, never because copy is long or a template exposes a list slot. In `presentation`, distill one assertion and move explanation into enabled notes (or keep it on the page when notes are off). Source texture is a secondary cue. Default writes §IX at the confirmed `design_spec_depth`: at `complete` depth write usable phrasing into §IX; at `brief` depth one bullet per block in the phrasing that fits, leaving page copy to authoring — neither is a skeleton: every claim, fact, relationship, and qualifier is present, and written wording is preferred wording unless literal preservation applies (Executor adapts under [`executor-base.md`](./executor-base.md) §2.1). §IX is the page brief at the confirmed depth; Executor retains it with the lock until context invalidation. Quick writes the same brief in context at whichever depth authoring needs.

**Mandatory — information model, not source object type**: qualitative `order` / `link` / `parent` / `membership` / `contrast` / `overlap` is written on the page's §IX `Relationships` line (its units and their source-stated relationship, or `none`; no catalog key, grammar atom, coordinate, shape, or named model — Executor decides at runtime whether geometry carries it); values, dates, or durations that determine geometry are a Chart; row header × column header facts are a Table, each compared against the complete loaded vocabulary.

**Mathematical and hyperlink content**: Record every source-backed equation under `Mathematical content` in the applicable §IX block as a LaTeX body without `$…$`, `$$…$$`, `\(…\)`, or `\[…\]` delimiters — never classified as inline or block, never invented for decoration, and never a policy, manifest, PNG, §VIII row, or lock entry; Executor owns the text-versus-native decision and returns here only for a content-level correction, including when the documented Microsoft 365 input profile cannot preserve the planned content. Record every explicit or source-backed link as the linked text/object plus its exact absolute URI or 1-based same-deck slide target — never guessed, never carrier-selected, never a manifest or lock entry; Executor authors it under [`native-hyperlinks.md`](./native-hyperlinks.md).

---

## 4. Roster and Rhythm

**Page rhythm**: give every page one tag — `anchor` (structural: cover, chapter, TOC, ending), `dense` (information-heavy; the baseline), or `breathing` (a low-density pause) — as a body-content frame and density judgment per page rather than one uniform fill; the tag is what breaks the uniform card-grid feel, and leans by reading mode are a bias, not a quota.

**Mandatory — whole-roster rhythm check**: while composing §IX, compare neighbors and section arcs — chapter entries visibly reset; same-density, same-resource, or same-relationship runs are intentional sub-arcs; a repeated motif carries a continuity job; any visible-state sequence keeps a recognizable map while its next change is legible; each section follows a mode-fitting progression (including framework → explanation/evidence → judgment/action when it serves); the final arc resolves the objective before a genuine ending lowers load. Same section, equal density, one style, and precedent establish no sub-arc. Repair roster, `Composition`, and `page_rhythm` in place; preserve intentional continuity, legitimately all-`dense` material, and 1:1 order; add no filler — a `breathing` page marks a real pause and must stand alone. No field, lock row, artifact, or second pass.
**Cover impact is mandatory**: give `P01` one concrete hook from the source's strongest claim, metaphor, number, moment, or conflict plus one optional composition Reference in ordinary words (a distilled display phrase may carry the cover while the complete title stays a native subtitle; with no suitable image, a native-SVG hook). The hook binds; the composition is a Reference. `P01` stays `anchor`, defaulting away from generic content-page templates unless content, user, or template makes a card grid, agenda, or equal-weight columns the clearest cover. Beautify preservation is exempt.

**Closing impact (only when the deck closes)**: for a genuine conclusion, CTA, or final takeaway, name the binding takeaway plus a recommended composition; never an information-empty "Thank you", contact-only slide, or cover reprise (an explicit contact/event CTA may serve), and never an invented closing page. Preservation is exempt.

**Reference — a starting sketch, never a constraint**: a §IX `Composition` line names the macro relationship the page's content suggests (one focal claim, equal comparison, dominant evidence + takeaway, parallel sequence, core + surrounding forces, wide visual + explanation) in ordinary words; Executor owns the structure and geometry that realize it (its layout-structure vocabulary lives in [`executor-base.md`](./executor-base.md) Page Expression Core) and adjusts or replaces the line freely after reading the page. Never write element-level sizes or coordinates into §IX.

Once the roster and planned resources are known, recommend a cross-page motif or element family when it can carry identity or meaning — title/corner ornaments, a directional contour, an opening, a line lattice, an oversized numeral — recording its continuity job and reuse mode (Default: §III `Theme`, mentioned only in the §IX `Composition` blocks that benefit; Quick: the transient motif system in context); Executor owns its geometry and may decline it; no motif field, lock row, or quota.

---

## 5. Resources

**Default — resource need from the roster (may stay implicit when a page's need is obvious)**: while composing the roster, decide which pages need a prepared image, lettering, or illustrated-icon resource — the jobs only a prepared file can serve — and derive the resource rows (Default §VIII; Quick the operational manifests) from that need. The page's carrier mix itself (background, text, native geometry, imagery, icons, visualizations and their weights) is Executor's page decision and is never planned. Plan an image, lettering, or illustrated-icon resource only when the page assigns it a plausible job. Macro composition stays Reference; resource identities and explicit requirements keep their authority.

**Hard rule — native construction stays downstream**: record each page's relationships, resource roles, and any useful macro composition or visual-system Reference; never inventory or bind a preset, primitive, Connector, Boolean/freeform operation, coordinates, or authoring method. A technique may appear only as optional inspiration inside a macro Reference.

| Capability | Opportunity signal |
|---|---|
| Image composition | Image-as-canvas, editorial crop, collage, cutout, or meaningful focus / comparison / evidence units carry the page better than an adjacent rectangle |
| Composable illustration family | Pages benefit from coherent reusable title/corner ornaments, dominant anchors, supporting figures, compact illustrated-icon cues, or accents mixing with text, shapes, photos, or lettering |
| AI decorative lettering asset | Any stable display string — a complete long or multi-line title, cover hook, chapter word, place or product name, dish or exhibit name, year, hero number, pull quote, motif word — reads better with a material, dimensional, hand-rendered, or illustrative treatment than as ordinary text |
| Motion | A section/state change or continuity across adjacent pages, or a reveal / emphasis / movement order within a page, clarifies sequence, causality, comparison, or hierarchy |

Every communication job maps to a prepared resource or an information model; this menu never satisfies the Executor's per-page topology decision:

| Communication job | Prepared resource or information model |
|---|---|
| Real subject, place, product, evidence, atmosphere, or scene benefits from visual grounding | Supplied/extracted, web, AI, or sliced image |
| Reusable title/corner decoration, a dominant illustrated anchor, supporting figure, or accent strengthens compositions | A coherent AI illustration family as transparent `slice` assets, combined freely with other carriers |
| A compact semantic cue clarifies a category, process, KPI, state, or navigation item | Prepared project-local SVG/emoji icon, an illustrated-icon `slice`, or both |
| A real company, product, service, or social brand must appear as itself | The exact mark from `simple-icons` or supplied assets; not a user-facing library choice |
| Values, categories, time, weights, or duration determine mark geometry | Value-driven chart |
| Sequence, hierarchy, role, region, or relationship determines topology | Qualitative structure |
| Rows, columns, cells, headers, merges, alignment form the model | Cell-grid table |
| A stable display string reads better with a material, dimensional, hand-rendered, or illustrative treatment | Decorative lettering per the rule below, as an image beside a native title |

### 5.1 Image source

| Source id | Approach | Use when |
|---|---|---|
| `none` | No images | No source owns a meaningful communication job |
| `provided` | User-provided assets | Existing images carry factual, brand, product, or narrative authority |
| `ai` | AI-generated | Invented or deliberately stylized scenes, illustrations, backgrounds, metaphors, decorative lettering, or another generated treatment |
| `web` | Web-sourced | Named or evidence-bearing real-world subjects that must appear as themselves, plus generic photographic mood, background, or scene jobs |
| `placeholder` | Deferred | The image is required but will be supplied later |

**Hard rule — credentials never decide image need**: a missing `IMAGE_BACKEND`, host generation, or stock credential never justifies `none` or the deletion of a planned web role; do not inspect configuration or probe a provider — acquisition (Default Step 5; Quick §2 resource preparation) is the first capability check. When `ai` is included, preserve an explicit user path instruction, otherwise recommend `auto`.

**Default — visual grounding before `none` (may override when the full-roster review finds no image job)**: honor an explicit no-image requirement; otherwise, when the audience must recognize, experience, compare, or choose an externally verifiable subject, place, product, or setting, plan `provided` / `web`, and plan `ai` where invented or stylized expression materially improves a visual job. Mixed sources serve different roles; a rendering candidate resolves how imagery looks, never whether a real subject appears as itself.

**Mandatory — per-image source decision**: outside Image to PPTX, decide each page image's source separately — supplied/extracted when it carries authority, web when an externally verifiable subject must appear as itself, AI when invented or stylized expression matters more than documentary identity; mixed sources are normal. A visual style, `Illus.` propensity, or rendering resolves how imagery looks, never its source: a named place, building, product, artwork, or person stays a web/supplied candidate however illustrative the deck, and a subject deliberately not shown as itself is stated with its reason in the final report.

**Mandatory — image treatment and subject layers**: choose per image: `none`; a native SVG treatment (crop viewport, opacity, frame, scrim, shadow); or a prepared derivative. A subject that crosses native content requires a clean full-canvas base plus a registered RGBA cutout (`#A2-03`). A prepared derivative never overwrites its source, never becomes another derivative's parent, never has its output equal its input, and is derived only after that source is itself final. Where fidelity forbids adding a label, symbol, line, or geometry cue to a new color encoding, preserve the source encoding instead.

**Mandatory — illustration families and illustrated icons**: when the resource-need review selects a composable family, resolve it before authoring — elements may repeat as title/corner chrome or vary as anchors, figures, and accents on any page — batching compatible elements through Illustration Sheets under [`image-generator.md`](./image-generator.md) §4.3 and splitting only for geometry, detail, or quality conflicts. When it selects illustrated-icon cues and AI is not forbidden, prepare them as transparent slices under `images/`; grouping, count, and coexistence with SVG icons follow page fit, with no quota and never as SVG inventory.

**Reference — decorative-lettering candidates**: when AI is not forbidden, any display string in the frozen roster is a candidate on two questions — is the wording stable, and could an artistic treatment communicate better than native type? Page role, length, line count, kind of noun, and resolved style never pre-filter: a cover hook, chapter word, place or product name, dish or exhibit name, year, hero number, pull quote, or motif word all qualify, a two-character mark and a two-line lockup equally, and a phrase is never trimmed to feel more "wordmark-like"; type over photography or a busy field is often exactly where native text reads pasted-on. Compare candidates inside the whole page and deck mix and select any coherent set whose treatment wins; selecting none is valid without explanation. For each selected mark keep a native title wherever the page needs a searchable, selectable, or outline-visible heading — the lettering is the display layer, the editable wish is answered by the native layer. Prepare the set without a separate request: exact approved strings, one ordinary AI item or grouped Illustration Sheets with transparent slices, grouped by character and treatment, with role, placement/background relationship, weight, and energy given to the model under `image-generator.md` §5.3's controlled-default/high-expression boundary; chrome and body stay native. Never invent or alter copy or create lettering to justify AI.

### 5.2 Chart and Table references

**Reference — Chart/Table vocabularies**: the loaded vocabularies list what can be selected; they rank nothing, and custom objects and qualitative composition stay outside them. Choose at most one flexible `family/key` per page (children and qualitative relationships stay in §IX), keep `no-template-match` in §IX when none fits (never serialized), and validate every selected reference before the lock, correcting a failed selection by re-reading the complete vocabulary/registry:

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  <family>/<key> [<family>/<key> ...]
```

**Native-ready boundary**: give every independent data chart and pure text-grid table a unique page-local `kebab-case` key and a `<key>=yes|no` native-ready decision — `yes` by default, `no` only when [`native-data-interface.md`](./native-data-interface.md) §2 cannot express the object; qualitative compositions and incidental microvisuals stay unlisted. Default writes §VII and the `Native-ready` map; Quick keeps the key and decision in context.

---

## 6. Visual System

**Mode and visual style**: one communication mode ([`modes/_index.md`](./modes/_index.md)) and one visual style ([`visual-styles/_index.md`](./visual-styles/_index.md)) per deck, each a preset or a `custom` with executable behavior prose; style carries no color and never narrows carrier eligibility. Default authors three directions under [`strategist.md`](./strategist.md) §d; Quick resolves one directly.

### 6.1 Color

**Reference — not a constraint**: no universal palette — user / brand → active template → project-specific proposal from content and style; 60-30-10 is the starting proportion, body contrast at least 4.5:1 (WCAG AA), hue count follows encoding, style, and natural assets; how color is *used* on a page (fields, gradients, accent placement, mood) is Executor's craft. `scripts/config.py` industry anchors (finance/business navy `#003366`, technology bright blue `#1565C0`, healthcare teal `#00796B`, government red `#C41E3A`) and polarity ramps (positive `#2E7D32 → #4CAF50 → #81C784`, warning `#F57C00 → #FFA726 → #FFD54F`, negative `#C62828 → #EF5350 → #E57373`) are recall aids, never default locks; brand identities come from a Brand/Deck workspace, never a memorized list. The plan owns reusable positive / warning / negative roles; Executor derives tints, shades, alpha, gradients, and effects.

**Anchor recurring semantic roles, not every paint** (Default locks them; Quick keeps them as context anchors): add neutral roles the style and page plan give a stable meaning — `surface`, `grid`, `scrim`, `overlay`, `block-shade` — and leave page-local tints, gradient stops, shadow/glow colors, and one-off tones to execution, promoting one only when it becomes a reusable named role.

| Style trait | Extra neutral tiers to anchor |
|---|---|
| Layers panels / charts (e.g. `data-journalism`, `swiss-minimal`) | `surface` (panel lift), `grid` (hairline, lighter than dividers) |
| Text over imagery / dark field (e.g. `photo-editorial`, `glassmorphism`, `dark-tech`) | `scrim` / `overlay` for legibility |
| Print / hand-drawn fills (e.g. `chalkboard`, `zine`) | `block-shade`, one step off the field |

### 6.2 Typography

**Family selection**: user/template typography is authoritative. Delivery target: an explicit user/template target first, otherwise Windows Microsoft PowerPoint (owner: [`shared-standards-core.md`](./shared-standards-core.md) §4.1) — the authoring host's installed fonts never select a face; name concrete faces installed or approved on that target; at most four families; a brand/web face leads only after user-confirmed installation, otherwise export a safe face and keep it as a Design Spec reference (fonts are not embedded; CSS tails are preview aids, not PowerPoint fallbacks). Avoid near-equivalent splits (YaHei↔PingFang, SimSun↔Songti, Arial↔Helvetica↔Segoe UI, Times↔Times New Roman). Fonts in one deck form contrast (different family, weight, or proportion) or concord (one family throughout); across the direction set include both a concord and a contrast pairing unless the user or template fixes the stack, and never default to title = body without a reason.

**Reference — PPT-safe faces (recall, not a whitelist; one concrete named face per script — a stack carries at most one Latin face and one CJK face and never a fallback list of alternatives, because export takes the first named face of each script)**: CJK sans `Microsoft YaHei` / `SimHei`, CJK serif `SimSun` / `FangSong` / `KaiTi` (their macOS counterparts `PingFang SC` / `Heiti SC` / `Songti SC` are preview aliases, never the named face), Latin sans `Arial` / `Calibri` / `Segoe UI` / `Verdana` / `Trebuchet MS`, Latin serif `Times New Roman` / `Georgia` / `Cambria` / `Palatino` / `Garamond`, mono `Consolas` / `Courier New`, display `Impact` / `Arial Black`. Let the locked style's character pick the axis and lead the title — `Microsoft YaHei` / `Arial` are the neutral members, never the automatic lead; a neutral sans title where the style asks for character is the failure to avoid. Non-pre-installed directions — retro/pixel Press Start 2P / VT323, rounded Nunito / Quicksand / OPPO Sans (safe substitute `Trebuchet MS` / `Verdana`), modern web Inter / HarmonyOS Sans / Source Han, calligraphic 隶书 / 华文行楷 / 华文新魏 (safe substitute `KaiTi` / `FangSong`, titles only), brand faces — need target installation or stay Design Spec references.

**Role extension after confirmation**: while composing the roster, add a lowercase snake_case role with an exact stack only for a recurring role that materially needs a different family (`annotation`, `footer`, `footnote`, `data`, `emphasis`, `quote`, `code`), coherent with the confirmed heading/body system and locked style; one-off garnish stays omitted and Default names any added role in one compact `Role rationale` line in §IV.

**Size anchors — px only**: every layer carries bare px; PowerPoint pt (`px × 0.75`) is an export result. Take the initial body anchor and sanity band from [`canvas-formats.md`](canvas-formats.md) § Typography Scale Start, never rederived here.

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

Scan the roster before fixing anchors and declare every recurring role (`lead` at least body size; `footnote`; chart annotations when used; and the display roles the `anchor` page count makes recurring — chapter numerals, hero numbers), one deck-wide anchor each, snapped to clean even px (body 24 → title 42, subtitle 32, lead 30, annotation 18, footnote 16). Executor's ±2 px band and its two-occurrence display exception are [`executor-base.md`](./executor-base.md) §2.1; declare every recurring role so no structural text depends on that exception.

### 6.3 Icons

One single-select base identity, not a material whitelist:

| Option | Approach | Suitable Scenarios |
|--------|----------|-------------------|
| **A** | Emoji | Casual, playful, social media |
| **B** | Built-in generic icon library | Recurring compact semantic cues in one coherent SVG style |
| **C** | Custom project icons | Supplied, template-carried, or imported assets |
| **D** | No base icons | No shared generic base-icon identity is selected |

AI illustrated icons are not a base option, add-on, field, or key — like decorative lettering they are a downstream image carrier §h and [`strategist-image.md`](./strategist-image.md) may choose, with slices under `images/` (never `icons/`, `icons.inventory`, or `<use data-icon>`); they may coexist with base icons. Real brand marks are identity assets: any company, product, service, or social identity in the content may use its exact supplied or `simple-icons` mark under every base choice, with no extra option. Library inventory, prefixes, and placeholder syntax: [`../templates/icons/README.md`](../templates/icons/README.md).

One primary stylistic library per pool, chosen from the four characters in the [icon README](../templates/icons/README.md) table, with `stroke_width` from `{1.5, 2, 3}` for a stroke library; `simple-icons` is prepared from content for real brand marks. The pool is curated for broad semantic fit and synced before authoring; which icon a page uses is realization, never a preassignment.
