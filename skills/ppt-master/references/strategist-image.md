> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Image Planning

Always-on Stage-2 rendering-candidate extension plus confirmed image elaboration and `design_spec.md §VIII` resource planning.

**Trigger**: Load before every fresh Stage-2 direction set. Apply §2 first from the rendering index, freeze each direction's exact bases, and only then read the deduplicated selected detail files before completing its behavior. [`strategist.md`](./strategist.md) independently owns source recommendation. A confirmed non-`none` source activates the applicable resource-planning sections; confirmed `none` stops before resources. Rendering candidates are authored once before confirmation and never backfilled from a later source toggle.

---

## 1. Proposed and Confirmed Image Plan

Before Stage 2, construct rendering candidates independently of the proposed source set. After confirmation, use this module within [`strategist.md`](./strategist.md)'s one-pass page carrier planning: run its eligibility and fit decisions inside that pass, then plan and route only the resulting image, lettering, and illustrated-icon jobs; map the confirmed source set through §h and honor explicit `image_notes` roles. This module never reopens the complete carrier mix as a separate pass, materializes a file, or adds a source. The confirmed non-`none` set is an allowed acquisition boundary, not coverage: use a suitable subset and leave irrelevant sources unused. Explicit must-use sources, assets, or page roles remain required. Asset inventory and judgment determine unconfirmed count, subject, placement, and composition without substituting an unconfirmed source.

For illustration, confirmed `none` stops and explicit user intent wins. Otherwise the locked visual style's `Illus.` propensity (`core` / `supportive` / `sparse`) tunes centrality and recurrence after the per-page composition scan; it never restricts eligible page types, element scale, or carrier combinations. When illustration is active, prefer one coherent family that can serve the actual page jobs, including recurring title/corner chrome, dominant anchors, supporting figures, and accents. A compact icon cue does not discharge a scene, subject, or visual-weight job that a photo or illustration family would serve.

**Context-first understanding for provided assets**: Do not visually scan `images/`. First infer identity, role, and crop / focus needs from source position and surrounding prose, captions / alt / titles, filename, user notes / confirmed `image_notes`, existing resource records, and CSV geometry. Inspect only one specific image when a remaining ambiguity would change selection, factual identity, page role, crop safety, or focal placement. Never inspect for inspiration, bulk-open the folder, or infer external facts / provenance from pixels. Record the result in §VIII. Leave an optional unresolved asset unused; route an unresolved must-use asset through failure recovery.

**Default — use Illustration Sheets when a compatible group benefits from a shared generation context**: illustration elements, illustrated-icon cues, and lettering may all use this path. [`image-generator.md`](./image-generator.md) §4.3 owns grouping and split decisions.

For each sheet, plan one unplaced `ai` Illustration Sheet row plus one placed `slice` row per used element; only slice rows enter `spec_lock.md images`, and one element row may serve several §IX pages. State each element's communication job, placement/reuse relationship, relative visual weight, energy, family, and shape without prescribing an effect stack. Use glyph-native expression by default; record a lettering-plus-illustration lockup only when the user explicitly requests it or the confirmed direction requires it. Lettering sheets use `text_policy: embedded`; the asset may carry the complete display title, while any required searchable, selectable, or outline-visible title remains an ordinary separate native text frame. [`image-generator.md`](./image-generator.md) §§4.3 and 5.3 own the controlled-default/high-expression boundary, artistic authorship, grid, key field, slicing, and execution details. Final Stage 2 chooses the AI execution path under `image-generator.md` §7; do not pre-empt or re-pick it here.

**Default — consider illustrated icons under confirmed AI permission**: when a
compact semantic job benefits from a project-specific illustrated cue, plan the
useful cues through the same sheet-to-slice contract. Each placed cue uses
`Type: Illustrated icon`, `Crop Policy: no-crop`, and an appropriate layout
recommendation; the parent remains an unplaced `Type: Illustration Sheet`.
There is no confirmation field or coverage quota. Illustrated cues may coexist
with base SVG/emoji icons when the overall visual system remains coherent, and
their slices stay out of `icons/`.

**Mandatory — scan decorative-lettering candidates before selection**: When
confirmed image usage retains `ai`, scan the complete page roster once before
writing §VIII. Confirmed `ai` is a Permission, not coverage: never create
lettering merely to justify the AI source or because no other AI-image job was
found. Candidate discovery asks two questions—is the wording stable, and could
an artistic treatment plausibly communicate better than native type. When
either answer is no, create no lettering row and keep the wording as native
editable text. Page role, character count, word count, line count, kind of noun,
and locked style never pre-filter candidates; a complete long title, multi-word
phrase, and multi-line lockup are as eligible as a short mark. Preserve each
full exact character sequence as one intended mark when its hierarchy belongs
to the art; never trim, rewrite, or split it merely to ease generation. Passing
both questions exposes a possible job rather than selecting it. Compare every
candidate inside the complete page and deck carrier mix, then choose any
coherent set whose artistic treatment wins that fit; zero selected marks
remains valid and needs no skip explanation or coverage quota. Materialize each
selected mark as an ordinary `ai` row or group compatible marks through the
§4.3 sheet/element rows rather than leaving it as a planning suggestion. Let
letterform character, treatment, and practical generation needs guide grouping.
An asset may carry the complete long or multi-line
title as its display layer. Keep an ordinary native title/subtitle in a
separate text frame wherever the page needs a searchable,
selectable, or outline-visible heading. Chrome and body remain native text. A
confirmed `none`, explicit no-AI instruction,
editable-only hook, or Offline Manual path does not activate this proactive
rule; an explicit user-required lettering asset still follows the ordinary
resource contract.

**Mandatory — image-treatment path scan, not a quota**: Per selected image choose `none` (unchanged), `native` (SVG crop/clip, transform, opacity, frame/depth, overlap), or `prepared derivative` (separate pixel blur/tone or cutout/registered layers); `none` is valid.

When a subject crosses a native title, panel, frame, or shape, the prepared path is mandatory: plan a clean full-canvas base plus minimum registered RGBA layers; set full-canvas members `no-crop`; name their shared source/registration in `Reference`; suggest `#A2-03`. A shared plate requires padded-bbox-disjoint objects and independent final crops. Use `user` only when every final asset is supplied, otherwise `ai`; [`image-generator.md`](./image-generator.md) §4.4 owns preparation. An independent floating cutout may use `#A2-01`.

## 2. AI Image Strategy — always propose three; lock only for confirmed `ai`

Before any rendering detail, use the already-loaded [`image-renderings/_index.md`](./image-renderings/_index.md) as the sole rendering-basis catalog authority. First author exactly three complete, project-fit solution intents; use the index to freeze each intent's exact rendering bases, then read once only the deduplicated referenced sibling files. Project one complete `image_strategy` into each direction regardless of `recommend.image_usage`. Every candidate carries localized `name`, `rendering: custom`, `visual`, `mood`, and non-empty localized `behavior`. Mood includes a recognizable real-world analogy. All three must credibly serve their owning whole solution; rendering treatments and bases may coincide when other components express the direction difference. Do not force artificial safe / shifted / bold extremes. Image colors always inherit that direction's deck HEX roles; never add an image palette or alter deck colors to rescue a rendering.

Every direction is a `custom` rendering, unconstrained by how it relates to the catalog. It may use catalog material in any way or none, including carrying one complete preset treatment unchanged. Name every actual id in the visible behavior and read only those files after selection; when several are named, each owns a distinct line, texture, depth, material, or mood contribution. Reference count has no fixed cap, and a second basis is never required. With no catalog basis, name none and read none. Under a template it obeys inherited identity and application. Only a confirmed custom locks its edited behavior as `image_rendering_behavior`; when catalog material is actually used, also project the exact ids as `image_rendering_references`, otherwise omit that field. Unselected candidates remain recommendation-only. Do not write a separate fourth `custom_candidates.image_strategy`; ignore legacy `image_palette`.

The UI hides these candidates while AI is not selected. If the user adds AI, it reveals the already-authored three without another backend recommendation; source selection never creates or rewrites rendering candidates. After confirmation, Image_Generator reads only the selected preset or exact custom references and must not blend unselected candidate identities.

For specialized or regulated paper-figure subjects, preserve the prompt depth required by [`image-generator.md`](./image-generator.md) §4.2 rather than shortening to a generic brief. Scan the outline for genuine image-led pages, list the proposed hero pages in Stage-2 `image_notes` so the user can retain, edit, or remove them in the same confirmation, then mark only the confirmed pages' AI rows `page_role: hero_page`; local is the default. `text_policy: embedded` is reserved for stable figure-internal identifiers or lettering deliberately fused into the artwork; page titles, editable data values/labels, and prose remain SVG. Resolve confirmed provided assets through the context-first boundary above before writing §VIII.

## 3. Image Resource List

Add §VIII rows only for planned images; permitted unused sources create no row. Fill filename, dimensions/ratio, layout suggestion, crop, purpose/type, acquisition, status, reference, and conditional AI fields. `Acquire Via` is `ai`, `web`, `user`, `placeholder`, or `slice`; status follows [`svg-image-embedding.md`](./svg-image-embedding.md). Keep any unavailable planned/required asset `Pending` or `Needs-Manual`; never delete or reclassify it to appear complete. After final confirmation, project each placed row into `spec_lock.md images` as `<path> | source=<Acquire Via> | pattern=<Layout pattern> | crop=<adaptive|no-crop>` and omit unplaced source/sheet rows. Preserve exact confirmed `source`/`crop`; keep non-empty `pattern`, including optional catalog ids, as preferred expression rather than locked geometry.

**Prepared derivatives**: Keep canonical; `Reference`: `Derived from <bare filename>; treatment=<operation>;`. Deterministic child: distinct `.png`, inherits acquisition; §4.4 follows `user`/`ai` above. Lock placed children; [`image-base.md`](./image-base.md) §2–3 owns preparation.

References describe visual intent: AI uses subject + intent + composition without repeating rendering or HEX; web records exact subject, view/mood, focal/quiet region, and crop safety with positive quality cues; Image_Searcher later derives a separate short, specific provider query without rewriting this locked intent, while complete entity names or necessary disambiguation may use more words. When page use depends on stable image composition, put its subject/quiet zones, boundary or direction, intended overlap/seam, and approximate share only when needed in `Reference` or the matching §IX block—not only in `Layout pattern`.

**Prepared-user fast path**: For initial imported or user-supplied assets confirmed as `provided`, copy the exact `Filename` basename and derive `Dimensions` / `Ratio` from that row's EXIF-corrected `Width` / `Height` / native `AspectRatio` in the latest `analysis/image_analysis.csv`; `SourceDisplayRatio` is source-context metadata, not the bitmap crop ratio. Drop source-side directories, set `Acquire Via: user` and `Status: Existing`, and decide the remaining §VIII fields normally. Existing §VIII / lock / provenance-manifest records override this inference. Assets declared as `ai`, `web`, `slice`, or manual fulfillment retain that provenance and advance through their own status lifecycle after entering `images/`; location never reclassifies them as `user / Existing`.

**Mandatory**: each placed row gets one executable `Layout pattern`. It is preferred expression, not locked geometry; optional hierarchical ids from the already-read [`image-layout-patterns.md`](./image-layout-patterns.md) must be exact. They are prompt lookup handles for Executor, not exporter effect codes. Executor may adopt, adapt, or decline the suggestion while preserving resource identity/source, must-use status, crop/content, and explicit user/template constraints; layout-only changes need no upstream rewrite.

**Default — action-bearing image plan (may override when restraint better serves the page)**: For a `hero_page` or other image-led row, name an image/content or image/shape action—not position, size, crop, or legibility scrim alone. Plain split and full bleed remain valid when clearest.

Choose narrative intent before dimensions, then apply the already-read [`image-layout-spec.md`](./image-layout-spec.md) to the actual page region. Techniques needing a cutout, blurred crop, or desaturated copy require that prepared asset. Write `Crop Policy: no-crop` whenever cropping could remove required pixels, labels, evidence, identity, or edge content; screenshots, charts, certificates/contracts, dense diagrams, logos, and product markings are common triggers rather than an exhaustive list. Otherwise write `Crop Policy: adaptive`: Executor may use complete display or a focal-safe crop, and the value never commands cropping.

Judge `text_policy` per AI row using [`image-generator.md`](./image-generator.md) §5.3; paper figures, academic schematics, panel comparisons, data-axis graphics, and stable decorative lettering are positive triggers for reconsidering an all-`none` plan. Step 5 dispatches pending `ai` / `slice` rows to Image_Generator and pending `web` rows to Image_Searcher.
