# Shared SVG Core Standards

Mandatory reference for every route that authors or regenerates slide visuals through SVG. It owns XML validity, the closed generated-authoring surface, page closure, semantic grouping, shared visual-quality defaults, and fidelity vocabulary. The complete closed grammar that the checker and exporter enforce — mapping tables, accepted-but-warned spellings, rejection boundaries, import-side metadata — lives in [`svg-contract.md`](../scripts/docs/svg-contract.md); this file keeps the form the model writes.

**Conditional module routing**:

| Trigger | Load |
|---|---|
| Default or Quick Generate at the executor-base routing trigger (the first visual job beyond the everyday block); other routes when noncanonical/alpha paint, advanced line or text treatment, gradient/filter/effect, transform, freeform/radial geometry, or constructed style is used | [`svg-effects.md`](./svg-effects.md) |
| A page will use a preset pattern fill or evaluate native chart/table replacement | [`native-data-interface.md`](./native-data-interface.md) before deciding eligibility or emitting metadata |
| Default structured lock, or Quick installed Layout/Deck structured authoring | [`pptx-structure-interface.md`](./pptx-structure-interface.md) |

Design defaults that apply when no higher authority speaks are collected in §6.

**Fidelity labels**:

| Label | Meaning |
|---|---|
| `Native-stable` | Generated PPTX uses the corresponding native DrawingML property or object and retains the documented semantics within the technique-specific limits. |
| `Native-normalized` | Export targets an editable DrawingML equivalent, but normalizes the SVG into another structure such as a freeform, run property, or simplified paint/effect. |
| `Approximate` | DrawingML has no exact SVG equivalent; export targets the intended effect through a documented approximation, and material differences require output review. |
| `Bake-required` | The runtime effect is outside the native contract; pre-render it into an image or rebuild it with explicit supported geometry. |

**Reading rules**:

- **Required** / **Forbidden** statements are non-negotiable technical boundaries.
- **Conditional** contracts apply only when the corresponding feature is used.
- **Reference — not a constraint** passages expose capabilities and recipes; they do not require every page or visual style to use them.
- The locked `visual_style` controls whether and how strongly a compatible effect is used. It never expands the technical boundary.

**Hard rule — generated authoring is fail-closed**: `svg_output/` and reusable template SVGs may use only properties and conditional interfaces explicitly listed in this file or a triggered module in the routing table above. `svg_quality_checker.py` and exporter preflight share one validator: unknown inline visual properties and unmapped conditional contracts are errors; documented compatible spellings remain valid input and receive recommendation warnings that never require modification or block export. A recipe never expands converter support, and the fidelity labels describe only the `svg_output/` → PPTX path — not reconstruction after PPTX import, nor pixel identity across PowerPoint, LibreOffice, Keynote, and WPS.

---

## 1. Required Foundation, Forbidden Features, and Conditional Interfaces

### 1.0 Text characters: must be well-formed XML

SVG is strict XML. Two rules for all text and attribute values:

| Character category | Required form | Forbidden form |
|---|---|---|
| Typography & symbols (em dash, en dash, ©, ®, →, ·, NBSP, full-width punctuation, emoji…) | **Raw Unicode characters** — write `—` `–` `©` `®` `→` directly | HTML named entities — `&mdash;` `&ndash;` `&copy;` `&reg;` `&rarr;` `&middot;` `&nbsp;` `&hellip;` `&bull;` etc. |
| XML reserved characters (`&`, `<`, `>`, `"`, `'`) | **XML entities only** — `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`) | Bare `&` `<` `>` (e.g. `R&D`, `error < 5%`) |

One offending character invalidates the file and aborts export.

**Structural blacklist** (exhaustive for globally forbidden syntax; not a positive allowlist):

| Banned Feature | Description |
|----------------|-------------|
| `mask` | Masks |
| `<style>` | Embedded stylesheets |
| `class` | CSS selector attributes |
| External CSS | External stylesheet links |
| `<foreignObject>` | Embedded external content |
| `textPath` | Text along a path |
| `@font-face` | Custom font declarations |
| `<animate*>` / `<set>` | SVG animations |
| `<script>` / event attributes | Scripts and interactivity |
| `<iframe>` | Embedded frames |

**Hard rule — inline visual-property allowlist**: inline `style` may carry only paint/line (`fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `stroke-linecap`, `stroke-linejoin`, `fill-opacity`, `stroke-opacity`, `vector-effect`), text (`font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor`, `letter-spacing`, `text-decoration`), alpha and definition paint (`opacity`, `stop-color`, `stop-opacity`, `flood-color`, `flood-opacity`), the §2.1 literal geometry properties, and preview-only `shape-rendering`. `filter`, `clip-path`, `marker-start` / `marker-end`, and `baseline-shift="super|sub"` on `<tspan>` are direct attributes, never inline style.

**Default — ordinary generated paint**: new solid paint uses uppercase six-digit `#RRGGBB`; `fill` / `stroke` may instead use lowercase `none` or an exact local `url(#id)`. Alpha channels, dashes, two-stop gradients, and the shadow/glow filters of `executor-base.md`'s everyday block need no further file; load [`svg-effects.md`](./svg-effects.md) (executor-base routing trigger) before any other alternative color spelling, cap/join choice, gradient stroke or text fill, filter form, transform beyond rotate, or constructed paint/effect. Ordinary text uses a non-empty `font-family`, a finite positive unitless-px `font-size`, `font-weight` `normal` / `bold` / an integer hundred, `font-style` `normal` / `italic`, and `text-anchor` `start` / `middle` / `end` on `<svg>`, `<g>`, or `<text>` (never `<tspan>`); tracking, underline/strike, outline, gradient, and filter text treatments follow `svg-effects.md` §6.7.

**Hard rule — compact inherited authoring**: put common typography presentation attributes on `<svg>`, with a direct `font-family` whenever text is visible; root paint/effects are forbidden. Put shared typography or paint on the nearest meaningful `<g>` and keep true child overrides explicit. The source stays valid, browser-visible, semantic, locally editable SVG; never use classes/stylesheets, aliases/private keys, encoded payloads, precision loss, or unrelated indirection. `--canonical-authoring` reports drift from the compact form as an advisory warning.

> **Conditional interfaces**: `marker-start` / `marker-end` — §1.1. `clipPath` on `<image>` — §1.2. Static same-document `<use>` — §1.3. Imported native-shape metadata — §1.4. Authored native preset fragments — §1.5. Inline geometry, simple gradients, filters, and approximate group opacity — §2 and [`svg-effects.md`](./svg-effects.md). PPT preset patterns and native chart/table/template metadata — [`native-data-interface.md`](./native-data-interface.md) and [`pptx-structure-interface.md`](./pptx-structure-interface.md). Arbitrary per-pixel compositing (text knockouts, multi-layer image text, alpha composites) is bake-required; the one registered exception is the single-image text picture fill in `svg-effects.md` §6.3.

---

### 1.1 Line-end Markers (Conditional Contract)

`marker-start` / `marker-end` on `<line>` and `<path>` reference one local `<marker>` in `<defs>` with `orient="auto"` (or `auto-start-reverse`) whose single child is one of the five DrawingML line ends: a 3-vertex closed polygon (triangle), a simple concave 4-vertex closed polygon (stealth), an open 3-vertex path (arrow), a simple convex 4-vertex closed polygon (diamond), or one `<circle>` / `<ellipse>` (oval). Closed shapes take a fill matching the parent stroke; the open arrow takes `fill="none"` and a matching stroke. Any other marker shape blocks export. Grammar detail and import behavior: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.1.

---

### 1.2 Image Clipping (Conditional Contract)

`clip-path` maps natively only on `<image>`: one local `<clipPath>` in `<defs>` containing exactly one `<circle>`, `<ellipse>`, `<rect>` (optional `rx`/`ry`), `<path>`, or `<polygon>`, with no `clip-rule` / `fill-rule`. Circle, ellipse, and rect clips must exactly cover the image frame and become preset picture geometry; a path or polygon becomes custom geometry inside the frame, so use it whenever the contour does not cover the full frame. `clip-path` on shapes, groups, or text is forbidden — author the target geometry directly. Mapping table: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.2.

---

### 1.3 Static Same-Document `<use>` (Conditional Contract)

Author `href="#id"` to a `<symbol>` (finite positive `viewBox`, artwork inside it, instance `width` / `height` positive unitless) or to a primitive, `<g>`, `<text>`, or `<image>`. This pipeline departs from browser SVG in two ways: finalization and native export clone the referenced primitives into each instance (PowerPoint keeps no symbol graph, and PPTX import never reconstructs `<use>`), and the reused subtree may carry no layer, placeholder, or chart/table replacement metadata. Limits and forbidden forms: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.3.

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <defs>
    <symbol id="statusDot" viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet">
      <circle cx="10" cy="10" r="8" fill="#16A34A"/>
    </symbol>
    <g id="legendRow">
      <rect width="120" height="32" rx="8" fill="#F1F5F9"/>
      <text x="42" y="22" font-size="16" fill="#0F172A">Ready</text>
    </g>
  </defs>
  <use href="#statusDot" x="80" y="120" width="32" height="32"/>
  <use href="#legendRow" x="120" y="120"/>
</svg>
```

---

### 1.4 Imported Native PowerPoint Shapes (Conditional Contract)

`pptx_to_svg.py` emits rendering-neutral metadata (`data-pptx-object`, `data-pptx-shape-id`, `data-pptx-frame`, `data-pptx-prst`, `data-pptx-av-*`, `data-pptx-part`, payload and effect diagnostics) for objects that originate from `p:sp`, `p:cxnSp`, or `p:grpSp`. It applies only to lossless import SVGs and unchanged imported objects on import, mirror, and round-trip routes; ordinary authored SVG never writes these attributes, and export never downgrades an unknown preset or unsupported effect silently. The complete metadata, representation split, precision, proxy, and registry contract: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.4.

---

### 1.5 Authored Native PowerPoint Presets (Conditional Contract)

New SVG pages and project-owned canonical templates may opt one complete geometric object into a native DrawingML preset through the deterministic fragment helper. Selection lives in [`native-shape-authoring.md`](./native-shape-authoring.md); the helper prints one compact atomic `<g data-pptx-authoring="preset">` carrying preset, frame, adjustments, and base paint once, plus the registry-generated visible paths — no carrier, wrapper, or fingerprint.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

Append `--filter-id softShadow` only when that id already names one direct page-level [`svg-effects.md`](./svg-effects.md) §6.4 filter definition.

**Hard rule — helper-only metadata**: never add or edit authored preset metadata or registry paths by hand; regenerate the whole fragment when preset, frame, adjustment, fill, stroke, stroke width, or the filter reference changes, and replace it with ordinary SVG when free contour editing is required. The helper accepts `none` or six-digit solid HEX paint, optional channel opacity, stroke width, cap, join, and one shape-only filter; gradients, patterns, and other treatments stay ordinary SVG. Text stays outside the atomic fragment. Checker and exporter rerender every fragment from its metadata and fail closed on any drift; machine contract, template-ownership rules, and fidelity boundary: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.5.

---

## 2. Conditional Compatibility Mappings

### 2.1 Literal Geometry Lengths and Inline Geometry

**Hard rule — direct geometry length grammar**: write `x`, `y`, `width`, `height`, `rx`, `ry`, `cx`, `cy`, `r`, `x1`…`y2`, `dx`, `dy`, and `stroke-width` as finite unitless ordinary decimals in the page `viewBox` space (`x="120"`, `stroke-width="2"`); sizes and radii are non-negative. `px` is read-compatible and warns; every other unit, percentage, expression, or exotic numeric spelling is an error, and an invalid explicit value never falls back to a default. The same geometry properties may instead appear in the element's own `style` as `px` literals (`style="x:120px"`); zero may be unitless, and the pipeline materializes them as XML attributes. Line endpoints, text positions, path data, and points remain XML attributes. Complete grammar: [`svg-contract.md`](../scripts/docs/svg-contract.md) §2.1.

### 2.2 Group Opacity Compatibility

**Default — descendant alpha (may preserve compatible group opacity)**: put alpha on the affected descendant paint, text run, picture, or supported effect. `<g opacity>` remains accepted (`Approximate`, multiplied into descendants, fidelity warning only) because DrawingML has no isolated group-alpha model.

---

## 3. Canvas Format Quick Reference

Use the already locked canvas id and exact viewBox. [`canvas-formats.md`](canvas-formats.md) owns format selection; this core owns only SVG conformance on that canvas. The lockless [`quick-generate`](../workflows/profiles/quick-generate.md) profile uses its first SVG to establish the canvas; every remaining page must use the identical viewBox.

---

## 4. Required Page Contract and Conditional Packaging

### 4.0 Complete Page-Design Contract

| Concern | Requirement |
|---|---|
| Visible slide result | The completed `svg_output/<slide>.svg` MUST contain every visible text, image, shape, diagram, chart/table fallback, background, and template-derived layout element intended for that slide. External visual assets are valid when the SVG references them explicitly. |
| Template/control inputs | Templates, `design_spec.md`, and `spec_lock.md` guide authoring. Do not depend on them to add visible elements after the page SVG is complete. |
| PPTX translation | The exporter may map represented SVG content to DrawingML/native objects and deduplicate represented elements into Master/Layout/Slide parts. It MUST NOT invent visible slide content absent from the SVG. |
| Excluded package behavior | Speaker notes, animations, transitions, narration audio, PPTX relationships, and direct native-PPTX workflows remain separately owned. They are not part of the SVG page-design contract. |

**Hard rule — page-design closure**: A final page SVG is complete but does not own the whole PPTX package. Its ordinary content and SVG-first Chart/Table markers are authoritative. For `data-pptx-native-authority="json"`, inline JSON is authoritative and the visible subtree is a derived, possibly approximate preview; authority never moves to a sidecar.

### 4.1 Semantic SVG Marker Contract

Semantic markers are minimal compiler hints. Flat pages declare one root `data-pptx-page-role` and omit Master/Layout/layer/placeholder markers. Structured pages carry their final root identity, layer atoms, slots, and native-object metadata from authoring start and omit `data-pptx-page-role`. Use `data-pptx-role` with a stable `id` only when no specialized marker expresses page-frame behavior. Keep ordinary visible content in SVG attributes/text; [`semantic-svg.md`](semantic-svg.md) owns the vocabulary.

- **Canvas authority**: new authoring writes `viewBox="0 0 W H"` with positive integer pixels from the lock, or from the first SVG under `quick-generate`; all pages and Layout prototypes in one build share it, optional root `width`/`height` never override it, and a root `<svg>` transform is forbidden. Export quantizes once at `1 SVG px = 9,525 EMU`.
- **Font portability**: resolve an explicit user/template delivery target first; otherwise default to Windows Microsoft PowerPoint with locale following the deck's primary language. Exported Latin/EA faces must be installed or approved on that target. The authoring host's fonts affect SVG preview and measurement only and MUST NOT select PPTX faces; a local counterpart may appear only as a preview tail that preserves the same export resolution. `@font-face` remains forbidden; the typography contract lives in [`strategist.md §g`](strategist.md).
- **Icon placeholders**: `<use data-icon="library/name">` is a pipeline-specific form, distinct from local SVG reuse. Follow the contract in [`../templates/icons/README.md`](../templates/icons/README.md).
- **Local reuse**: ordinary same-document `<use>` follows §1.3.

### 4.2 Editability, Package Promotion, and Text Leading

These forms are needed only when the stated PPT behavior matters:

| Desired behavior | Required form |
|---|---|
| One editable PPT text frame with mixed formatting or multiline prose | Use one `<text>` per logical paragraph and non-positional `<tspan>` children for inline runs. Per-run `fill` / `font-weight` / `font-size` is retained: export walks nested runs and emits one DrawingML run per styled segment, so an emphasised phrase stays inside the same editable frame, and a positioned line-break `<tspan>` may itself contain inline runs. Keep the first line as direct text; later lines use direct positioned `<tspan>` children that repeat parent `x` with positive relative `dy`; an all-`<tspan>` form may start at `dy="0"`. Default retains these breaks without PowerPoint wrapping; `--reflow-text` may join eligible lines. A font-size change, list marker, or larger accepted gap starts another paragraph. Sibling `<text>` elements are forbidden as one paragraph's line breaks; they remain valid for independent frames. |
| Stable object grouping or object-level animation anchor | Wrap the intended object in `<g id="...">`. Content grouping is **mandatory** per §4.3 — a top-level `<g id>` is also the animation anchor; it is not an optional convenience. |
| Native PowerPoint background promotion | Outside structured mode, make the first visual layer a direct full-canvas `<rect>` (or one inside a simple single-child group) with a solid, linear/radial gradient, or preset-pattern fill and no transform, filter, clip, rounding, or visible stroke; export writes it as Slide `p:bg`. Structured routes follow [`pptx-structure-interface.md`](./pptx-structure-interface.md). |
| Free-design / brand-only PowerPoint structure | Use `pptx_structure.mode: flat`: keep objects Slide-local and author no Master/Layout identities, layers, or slots; export emits one clean Master plus Blank Layout. |
| Reusable template-based PowerPoint Layout | Default maps page prototypes through `page_layouts` and Master/Layout definitions through `page_pptx_layouts`; Quick authors the selected Master/Layout/slot contract in every output SVG and its all-or-none gate infers structured packaging. Never infer ownership from repeated Slide-local geometry. |

**Default — leading by role and density (may be overridden for user, template, typeface, legibility, or locked visual-style fit)**: For direct positioned `<tspan>` rows, start multiline titles around `1.2–1.3 × font-size`, dense / small body around `1.4–1.5 ×`, ordinary body around `1.5–1.6 ×`, and large / sparse / breathing body around `1.6–2.0 ×`. These are starting ranges, not checker quotas; display headlines may be tighter when the selected style calls for it. Author the spacing as positive relative `dy`, not CSS/SVG `line-height`, which has no registered DrawingML mapping.

**Hard rule — supported shape conversion**: every editability claim here refers to the project converter reading `svg_output/`. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture; PowerPoint's manual Convert-to-Shape operation is unsupported and never narrows the authoring contract.

### 4.3 Element Grouping (Mandatory)

**Hard rule — root groups protect body-text layout**: every visible direct root `<g>` except a compact helper-authored preset atom declares positive root-coordinate `data-pptx-bounds="x y width height"` sized as the intended module zone. On flat pages, maximize ordinary zones within canvas/sibling space without overlap; the checker fails root-group overlap beyond `1px`, warns on module text overflow through `5%` and fails above it, and fails any larger root-`viewBox` text overflow. Bounds do not clip or reflow. Structured slots, structural-role groups, and a wholly off-canvas Morph endpoint marked `data-pptx-morph-staging="true"` are the only exemptions; thresholds and estimator detail: [`svg-contract.md`](../scripts/docs/svg-contract.md) §4.

Wrap each logical Slide-local body unit in one descriptive top-level `<g id>`; group count follows the page's semantic units, and each group becomes one stable animation target when animation is enabled. Nested implementation groups may remain anonymous, need no bounds, and create no animation step; use them only when internal subunits (icon + title, value + label, repeated rows) are useful to edit — there is no default nesting pattern, depth, or quota. Titles, direct atomic Master/Layout elements, and canvas-level static framing — background images and full-canvas scrim/decoration rectangles — may remain root primitives; on flat pages give such framing a stable `id` plus `data-pptx-role="background"` / `"decoration"` and never add a `<g>` solely to silence an ungrouped-element advisory.

**Structural atoms and slots are excluded automatically.** `data-pptx-layer` and `data-pptx-placeholder` semantics are read first; otherwise explicit `data-pptx-role` values (`background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, `logo`) mark Slide-local static framing (§4.1, [`semantic-svg.md`](semantic-svg.md)). A normal slot group has exactly one direct compatible carrier; several drawing atoms require the explicit composite `object` proxy fallback. Native chart/table carrier groups retain their specialized [`native-data-interface.md`](./native-data-interface.md) contract.

**What to group** (one `<g id>` per unit):

| Grouping unit | Contains |
|---|---|
| Card / panel | Background rect + optional shadow (only if it floats over a photo/colored panel, [`svg-effects.md`](./svg-effects.md) §6.4) + icon + title + body text |
| Process step | Number/marker + icon + label + description |
| List item | Bullet / number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + accent decoration |
| Page footer | Page number + branding |
| Decorative cluster | Related decorative shapes (rings, dots, orbs) |

An authored native preset fragment (§1.5) is already an atomic `<g id>` and counts as one content group. Keep it top-level without `data-pptx-bounds` when it stands alone; when it needs a label or decoration, place the preset and those siblings inside a separate bounded parent content group, never inside the preset group itself.

**Forbidden**:

- One giant `<g>` around the whole slide (collapses to a single animation step).
- Many ungrouped Slide-local `<rect>` / `<text>` / `<path>` atoms — they have no stable sidecar target and selection/editing degrades.
- One top-level group per icon / text line / mark (too many animation steps).
- Anonymous top-level groups — every top-level semantic group needs a descriptive, page-unique `id` (`card-1`, `step-discover`, `header`, `footer`); it is the stable SVG-side animation and trace anchor.

```xml
<g id="card-benefits-1" data-pptx-bounds="60 115 565 260">
  <!-- Shadow only if the card floats over a colored panel; on flat white, omit it. -->
  <rect x="60" y="115" width="565" height="260" rx="20" fill="#FFFFFF" filter="url(#shadow)"/>
  <use data-icon="chunk-filled/bolt" x="108" y="163" width="44" height="44" fill="#0071E3"/>
  <g id="card-benefits-metric">
    <text x="105" y="270" font-size="56" font-weight="bold" fill="#0071E3">10×</text>
    <text x="250" y="270" font-size="30" font-weight="bold" fill="#1D1D1F">Faster</text>
  </g>
  <text x="105" y="310" font-size="18" fill="#6E6E73">Reduce production time from days to hours.</text>
</g>
```

---

## 5. Workflow Authority

Serial post-processing and export belong to [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7 and, for the direct-generation exception, [`quick-generate.md`](../workflows/profiles/quick-generate.md). This file defines SVG authoring boundaries only; project structure, commands, quality-gate order, and export products are intentionally outside it.

---

## 6. Shared Aesthetic Baseline

**Default — shared aesthetic baseline (may be overridden by explicit user, installed template / brand, or locked / Quick-resolved visual-style requirements)**: Required / Forbidden technical contracts remain absolute. When a higher authority is silent, build clear hierarchy through typography and leading, alignment, negative space, purposeful imagery / icons, shapes, and repetition. Deliberate tightness, imbalance, off-axis placement, or container-heavy structure remains valid when that authority calls for it.

| Concern | Shared default |
|---|---|
| Text-block rhythm | Use §4.2 leading. Make the baseline step into a new paragraph visibly larger than the intra-paragraph line step; keep the extra gap between list items smaller than paragraph separation but large enough to scan each item. Repeated peer blocks share one rhythm unless their hierarchy differs. |
| Typography roles | Use the fewest semantic text roles that preserve hierarchy, and make their differences legible at slide-thumbnail scale. Consolidate near-neighbor sizes that serve the same role; otherwise distinguish roles through a deliberate combination of size, weight, color, position, and surrounding space. |
| Viewing-distance legibility | Resolve delivery context and viewing distance before fixing density and type scale. Preserve necessary text at a readable scale by applying only actions the active route's content and page invariants permit: restructure, shorten, split, or reflow. If none is permitted, surface the unresolved fit instead of silently miniaturizing it. Do not turn this into one universal font-size floor: captions and metadata may be smaller when their role and context remain legible. |
| Contrast and semantic encoding | Within the active profile's fidelity boundary, keep meaning-bearing text distinguishable from its actual background. For newly authored distinctions, combine luminance, weight, scale, shape, position, or explicit labeling; color may reinforce meaning but never carry a required distinction alone. When fidelity requires preserving source-only color encoding, reproduce it rather than inventing a cue. Reserve lower-contrast treatment for genuinely secondary metadata that remains legible. |
| Natural wrapping | Break at semantic phrase or punctuation boundaries where possible. Reflow the text frame or adjust neighboring geometry before using any permitted local size reduction. Let the final line run naturally shorter; avoid mechanically equal lines or a stranded single-character / single-word line when an earlier natural break preserves meaning. |
| Content field | Establish the usable body frame before placing modules. Divide it into one or a small set of macro-regions from information weight and reading order: use unequal weight when the information differs, while true peers may share equal weight. Give each region its own local axes / micro-grid while retaining only the cross-region anchors the composition needs. On a dense page, let the planned content system organize that frame; create breathing room through gutters, module spacing, and intentional voids between semantic clusters. Unorganized residual space that leaves content stranded in one part of the frame is leftover blank, not negative space. |
| Alignment and proximity | Establish shared axes from the current composition. Align related titles, copy, labels, images, and diagram nodes to those edges, centers, or baselines; group related elements more tightly than unrelated groups so spacing carries hierarchy. Break an axis only when the offset performs hierarchy, direction, or tension. |
| Visual weight | Judge weight from area, darkness, saturation, density, stroke, image detail, and elevation together. Distribute it to support the focal path; symmetry is optional, and deliberate imbalance may create direction. |
| Boundary strength | Boundaries range from spacing / alignment, rule / bracket, and tint field through outline, filled panel, and true floating layer; choose the strength from the relationship. Peer relationships use comparable strength while focus, hierarchy, or material difference may use a different one. |
| Containers | A card or panel expresses grouping, hierarchy, boundary, capacity, or a distinct material plane; peer containers share treatment unless a semantic difference justifies contrast. An unplanned repeated web-card grid is a carrier / topology problem, not a reason to suppress meaningful borders, shapes, or containers. |
| Titles and page chrome | Treat the semantic page title as part of the current composition rather than an automatic fixed header band; its position, scale, and relationship may change with page role while preserving the active route's content invariants. Add or retain running headers, footers, and page numbers only when they carry navigation, identity, attribution, or another explicit page job. Fidelity profiles preserve required source chrome. |

**Reference — effects vocabulary**: the executor core carries the everyday effects; [`svg-effects.md`](./svg-effects.md) loads on its routing trigger, and its §6.1 Visual Job Router lists the visual jobs an effect can serve. Whether any compatible technique is added is the author's call.

**Reference — where expression lives**: §4.2 owns editable text form, including per-run inline emphasis and leading; §4.3 owns grouping. §1.4's imported-PowerPoint metadata applies only to import, mirror, and round-trip routes.
