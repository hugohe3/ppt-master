# PowerPoint Feature ↔ Project SVG Mapping Guide

[中文版](./zh/powerpoint-svg-mapping.md)

## Purpose and authority

This guide answers one question from the PowerPoint user's point of view: **for a PowerPoint feature, what project representation owns it, and what survives export or import?** PowerPoint semantics are therefore the primary index. SVG elements appear only as the implementation of a specific PowerPoint capability.

This is a public capability and import-behavior map, not a second generated-SVG syntax specification and not a promise to convert arbitrary SVG or arbitrary OOXML. The canonical generated-authoring contract remains [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md); when generated syntax differs, that contract wins. PPTX import recovery modes and user-visible degradation belong to §11 here and to the [conversion command reference](../skills/ppt-master/scripts/docs/conversion.md), while the parser implementation remains the exact source of truth. A feature not listed here is not implicitly supported.

The main route compiles **project-canonical SVG**, not general browser SVG:

```text
PowerPoint intent
    ↔ project-canonical SVG or an explicit sidecar
    ↔ DrawingML / PPTX package semantics
```

Some PowerPoint features have no honest SVG equivalent. They are shown as sidecar/package features, direct-PPTX preservation features, or unsupported features instead of being forced into decorative SVG metadata.

## How to read the tables

Each row owns one PowerPoint capability. The mapping cardinality is not always one object to one object: one SVG text node may produce several PowerPoint runs, a native chart marker group may collapse into one `p:graphicFrame`, and an imported PowerPoint object may be reconstructed as several SVG elements.

| Term | Meaning |
|---|---|
| `Native-stable` | Export uses the corresponding editable DrawingML property or object within the documented limits. |
| `Native-normalized` | Export remains editable, but the source is normalized into an equivalent DrawingML structure. |
| `Approximate` | PowerPoint has no exact counterpart; review the generated PPTX when the effect is material. |
| `Bake-required` | Pre-render to an image or rebuild with supported explicit geometry. |
| `Sidecar/package` | The capability belongs to a project sidecar or PPTX package writer, not the SVG page design. |
| `Direct preservation` | A direct-PPTX workflow may retain the source OOXML; the main SVG compiler does not recreate it. |
| `Unsupported` | The main generation route has no registered mapping and must not guess. |

“Import” below means semantic reconstruction by the PPTX-to-SVG route, not recovery of the original SVG syntax. It does not promise the original `<defs>` graph, `<use>` structure, path commands, or `<tspan>` layout.

## 1. Presentation, slide, and coordinate model

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Presentation slide size | Root SVG `viewBox="0 0 W H"`, selected through the project canvas contract | Presentation width and height; `1 SVG px = 9,525 EMU` at 96 DPI | `Native-stable`; imported custom PPTX sizes may use compatible fractional dimensions | Values must be finite with a zero origin and positive supported dimensions; every public page/internal Layout prototype must match the lock; a root transform is forbidden |
| Slide | One complete `svg_output/<slide>.svg` page | One `p:sld` with its relationships | Reconstructed as one complete SVG page | SVG is the visible page authority; notes and package behavior are separate |
| Object position and size | Absolute SVG coordinates and element bounds | `a:xfrm` offsets and extents | `Native-normalized` through coordinate conversion | Values must be finite and use the registered coordinate grammar |
| Z-order | SVG source order, back to front | PowerPoint shape-tree order | Reconstructed in shape-tree order | Do not rely on browser-only stacking behavior |
| Rotation, scale, translation, and mirror | Supported SVG transform forms | DrawingML transform or normalized geometry | `Native-normalized`; matrices may be decomposed | Skew and shear outside the registered transform contract are not accepted |
| Theme colors and fonts | Roles locked in `spec_lock.md`; canonical SVG uses the resolved values | Theme-aware tokens where an exact locked role can be retained; otherwise direct DrawingML values | `Native-stable` for registered roles | New pages must not invent unlocked colors, fonts, or text sizes |
| PowerPoint-only package identity | `spec_lock.md` structure declarations and the package builder | Presentation, Master, Layout, relationship, and content-type registrations | Read back from package structure, not inferred from page appearance | Final-package read-back must match the declared roster |

See [`canvas-formats.md`](../skills/ppt-master/references/canvas-formats.md) for supported canvases and [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md) §4.1 for the normative root-`viewBox` contract.

## 2. Master, Layout, background, and placeholder features

**Route boundary**: Free-design and brand-only projects in the main SVG pipeline remain on `pptx_structure.mode: flat` from planning through export; `flat` is not a provisional state awaiting an exporter upgrade. Repeated logos, footers, or layouts never cause export to switch to `structured`, promote content into a Master/Layout, infer placeholders, or deduplicate objects. Output that requires reusable native Master, Layout, or placeholder behavior must enter Step 3 with a validated deck/layout template workspace; when none exists, run [`create-template`](../skills/ppt-master/workflows/create-template.md) first and return to the main pipeline with that workspace. The minimal Master and Blank Layout emitted by flat export are PPTX package scaffolding, not a design master derived from the slides. Filling new content into a raw PPTX template remains the [`template-fill-pptx`](../skills/ppt-master/workflows/template-fill-pptx.md) route.

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Free-design deck structure | `pptx_structure.mode: flat`; page content remains slide-local | One clean project Master and one Blank Layout, with represented objects on slides | `Native-stable` package topology for the flat route | No authored Master/Layout/layer/placeholder metadata is allowed |
| Template-backed deck structure | `pptx_structure.mode: structured` plus explicit Master/Layout/page assignments | Declared `p:sldMaster`, `p:sldLayout`, registrations, and slide parentage | `Native-stable` within the explicit structure contract | The exporter never guesses a Master, Layout, or placeholder topology |
| Slide Master | Root Master identity plus atomic `data-pptx-layer="master"` objects; one validated compact authored-preset `<g>` counts as one semantic atom | Reusable Master part and picker identity | Source structure is restored by template/import workflows | Master atoms must be direct, stable, and identical across their slides; ordinary or expanded authored groups do not qualify |
| Slide Layout | Root Layout identity plus atomic `data-pptx-layer="layout"` objects; one validated compact authored-preset `<g>` counts as one semantic atom | Reusable Layout part under one Master | Source Layouts can be restored; adaptive authoring may allocate a new Layout | Reuse a Layout key only when its fixed atoms and slot contract are identical; ordinary or expanded authored groups do not qualify |
| Imported inherited-shape visibility | PPTX `p:sld@showMasterSp` and `p:sldLayout@showMasterSp`; layered analysis records normalized source booleans outside visible SVG | No new generated-authoring marker; source-preserving workflows retain the package fields | `Native-stable` for imported visual/analysis facts: Slide false hides Layout and Master shapes; Layout false hides only Master shapes | Backgrounds, Slide-local objects, placeholder inheritance, part SVGs, and parent relationships remain intact; flat import omits only the suppressed inherited shapes |
| Strict template Layout | Selected prototype contract | Existing declared Layout topology is preserved | `Native-stable` when the page follows the prototype | Fixed Layout atoms and slot structure may not change |
| Adaptive template Layout | Selected Master plus an explicit current or newly declared Layout | A new Layout identity may be created when reusable structure changes | `Native-stable` after the lock and page mapping are updated | Never mutate a reused Layout key silently |
| Slide background fill outside structured mode | First eligible full-canvas `<rect>`, direct or in a simple single-child group, with a registered solid, linear/radial gradient, or preset-pattern fill | Native slide `p:bg` | Fidelity follows the corresponding paint row below | Transform, filter, clip, rounding, visible stroke, or an unmapped fill prevents promotion |
| Master/Layout/slide background fill in structured mode | One direct full-canvas solid `<rect>` in the declared structural layer | Native `p:bg` at Master, Layout, or slide scope | `Native-stable` | Explicit scoped background ownership is intentionally solid-only |
| Gradient or pattern backdrop in structured mode | Ordinary gradient/pattern `<rect>` on its declared Master/Layout layer or as slide-local content | Editable shape on the owning part | Fidelity follows the corresponding paint row below | Structured export disables generic background promotion; do not use `data-pptx-layer="slide"` |
| Picture backdrop | Ordinary project `<image>` on its declared Master/Layout layer or as slide-local content | Editable `p:pic` on the owning part | Fidelity follows the picture rows below | An image element is never promoted to `p:bg` |
| Title placeholder | Structured slot group with one text carrier | Layout and slide `p:ph` of type `title` | `Native-stable` | Carrier count, bounds, type, and effective index must match the Layout contract |
| Subtitle placeholder | Structured slot group with one text carrier | `p:ph` type `subTitle` | `Native-stable` | Same slot rules as title |
| Body placeholder | Structured slot group with one text carrier | `p:ph` type `body` | `Native-stable` | A multiline carrier remains one text frame |
| Date, footer, and slide-number placeholders | Structured text slots | `p:ph` types `dt`, `ftr`, and `sldNum`, with matching Layout header/footer flags | `Native-stable` | Placeholder indices must be unique and legal |
| Picture placeholder | Structured slot with one image or supported crop carrier | `p:ph` type `pic` | `Native-stable` within the picture contract | The slot must contain exactly one compatible direct carrier |
| Chart or table placeholder | Structured slot with one matching native-object carrier | `p:ph` type `chart` or `tbl` | `Native-stable` only on native Chart/Table export | Requires valid JSON metadata and `--native-charts-and-tables` |
| Generic object placeholder | One compatible carrier—including one validated compact authored-preset `<g>`—or an explicit composite proxy binding | `p:ph` type `obj` | Native binding; composite visible content remains ordinary shapes | Composite slots must use the registered proxy downgrade; expanded authored groups are not single-object carriers |
| Media placeholder | One image or supported crop carrier | `p:ph` type `media` | Native placeholder binding only | It does not synthesize video or audio from decorative SVG content |
| Empty text placeholder | Empty or whitespace-only marked text carrier | Invisible U+200B run at the legal 1 pt minimum, producing one native text shape | `Native-stable` | Do not add a dummy dash, sub-1 pt text, or background-colored visible glyph |
| Page role such as cover/content/ending | Flat-route root `data-pptx-page-role` compiler hint | Routing/validation hint; not a native PowerPoint page type | No independent OOXML object | Structured pages use explicit Master/Layout identity instead |
| Slide sections and custom shows | No SVG mapping | Not authored by the main generation route | `Direct preservation` where a source-preserving workflow owns them | Do not encode them as visual metadata |

The exact structured metadata and slot grammar live in the [PPTX structure section of the normative standards](../skills/ppt-master/references/shared-standards.md#pptx-structure-routing).

Internal identifiers and PowerPoint display names are separate concerns: Master and Layout keys use the restricted project ASCII identifier grammar, while picker names may contain spaces. Every Layout definition also names its parent Master and one explicit prototype source. The normative standards own the exact row syntax.

## 3. PowerPoint shapes and drawing objects

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Rectangle | `<rect>` | Editable `p:sp` with `a:prstGeom prst="rect"` | `Native-stable`; imports as a primitive when possible | Use registered paint, line, and transform properties only |
| Symmetric rounded rectangle | `<rect>` with equal supported corner radii | `a:prstGeom prst="roundRect"` with adjustment | `Native-stable` | Asymmetric corners follow the freeform row |
| Circle or ellipse | `<circle>` or `<ellipse>` | `a:prstGeom prst="ellipse"` | `Native-stable` | Bounds and radii must be finite and positive where required |
| Straight line | `<line>` | Editable line/freeform shape | `Native-normalized` | Browser-only line effects are rejected |
| Arrowhead line | `<line>` or supported path with registered triangle, stealth, arrow, diamond, or oval start/end markers | Native DrawingML line head/tail ends | `Native-normalized`; marker size is approximate | Marker definitions must follow the conditional marker contract |
| Native connector | Compact project-authored preset group with connector metadata and direct visible paths | `p:cxnSp` | Imported connectors retain the expanded round-trip evidence needed for source topology | `Native-stable` for the registered preset/connector schema |
| Freeform shape | `<path>` | `p:sp` with `a:custGeom` | Imported custom geometry reconstructs as a path | `Native-normalized`; SVG arcs are converted to cubic segments |
| Polygon | `<polygon>` | Closed custom geometry | `Native-normalized` | Points must be finite and valid |
| Polyline | `<polyline>` | Open custom geometry | `Native-normalized` | Points use the same finite, registered grammar as other generated geometry |
| PowerPoint preset shape | Registry-generated compact `<g>` with preset intent/base paint and direct visible `<path>` children | One editable preset `p:sp` | Preset identity and adjustments can survive import/export | Quality check and export rerender the registry dynamically; canonical authoring has no hidden carrier, preview wrapper, or stored preview hash |
| Imported preset shape | Expanded import/round-trip group with a hidden native carrier, visible preview evidence, and freshness metadata | Restored preset when the payload is valid and unchanged | `Native-stable` within the import contract | Unsupported presets remain explicit diagnostic fallbacks, not guessed geometry |
| Action button shape | Compact authored `actionButton*` preset group | Visual preset geometry only | Shape geometry can round-trip | No click action, navigation target, or hyperlink is created |
| Group | `<g>` | `p:grpSp`, or a documented flatten/collapse for a special carrier | Grouped content can reconstruct as `<g>` | Structural atoms and placeholder contracts override ordinary grouping |
| Reused local symbol | Registered same-document `<use>` contract or project icon placeholder | Expanded editable shapes in the generated slide | Original symbol graph is not promised on import | External use, unsupported symbol features, and structural metadata reuse are rejected |
| Icon | `<use data-icon="library/name">` resolved by the project icon pipeline | Editable vector primitives/group after expansion | Reconstructed geometry, not the original library reference | Icon identifiers are case-sensitive and must exist in the synchronized library |
| SmartArt / DiagramML | No main SVG object mapping | Main redesign route may rebuild the meaning with ordinary shapes | `Direct preservation` in native/template routes; otherwise a preview or explicit fallback | Do not label a decorative group as native SmartArt |

Project-authored presets deliberately use a compact representation, while PPTX
import keeps the expanded evidence needed for lossless round-trip decisions.
The exact machine contract remains in
[`shared-standards.md`](../skills/ppt-master/references/shared-standards.md), and
preset selection and authoring behavior are documented in
[`native-shape-authoring.md`](../skills/ppt-master/references/native-shape-authoring.md).

## 4. PowerPoint text features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Text box | `<text>` | Editable `p:sp` with `p:txBody` | Reconstructed as `<text>` and, when needed, `<tspan>` | Text must be well-formed XML and use registered attributes |
| Mixed formatting within a line | Non-positioned `<tspan>` runs | DrawingML runs in one text frame | `Native-normalized`; registered run formatting remains editable | Positioning that changes frame geometry may split the result |
| Multiple paragraphs | Mergeable text/tspan structure | Multiple `a:p` paragraphs in one text frame | `Native-normalized` | Strict independently positioned lines may remain separate text boxes |
| Significant text whitespace | Exact `xml:space="default"` or `xml:space="preserve"` on `<text>`/`<tspan>` | Normalized or preserved U+0020 text in editable DrawingML runs | `Native-normalized`; inline run ownership is retained | Uses the project Chromium/SVG2 contract: LF/TAB become spaces, `default` collapses across runs, `preserve` retains them, and Unicode spacing characters remain literal; CSS `white-space` and legacy SVG 1.1 newline deletion are outside the mapping |
| Font family | Canonical `font-family` resolved against the project lock | Direct typeface or registered theme font | `Native-stable` within installed/font-substitution limits | Unlocked or unavailable fonts are reported by validation |
| Font size | Finite unitless SVG pixels, for example `font-size="24"` | DrawingML hundredths of a point; `1 px = 0.75 pt` | `Native-stable` after unit conversion | Generated authoring uses only unitless px; registered legacy units are compatible input and warn, while unknown units error; DrawingML minimum is 1 pt |
| Font weight | Registered `font-weight` on `<text>`/`<tspan>` | DrawingML regular/bold run switch | `Native-normalized`; numeric weights collapse to the DrawingML boolean boundary | The exact value grammar and aliases belong to [`shared-standards.md` §6.7](../skills/ppt-master/references/shared-standards.md#67-advanced-text-treatments) |
| Italic, underline, and strike | Registered `font-style` / `text-decoration` on `<text>`/`<tspan>` | DrawingML italic, underline, and strike run properties | `Native-stable` for registered tokens | Unknown tokens are rejected; the exact grammar belongs to [`shared-standards.md` §6.7](../skills/ppt-master/references/shared-standards.md#67-advanced-text-treatments) |
| Text fill and transparency | Canonical fill plus run alpha | DrawingML run fill and alpha | `Native-normalized` | Use the semantic alpha channel, not an unregistered CSS effect |
| Text outline | Registered stroke on text | DrawingML run outline | `Native-normalized` | Review when outline carries fine visual meaning |
| Text alignment | Registered `text-anchor` and paragraph semantics | Paragraph alignment plus normalized text-frame position | `Native-normalized` | Run-level anchoring and browser baseline heuristics are unsupported; exact placement belongs to [`shared-standards.md` §6.7](../skills/ppt-master/references/shared-standards.md#67-advanced-text-treatments) |
| Vertical text-frame alignment | No canonical generated-SVG control; generated text boxes use top anchoring | Top-anchored DrawingML text body | Imported vertical text may be normalized, but the main route does not expose a general authoring control | Do not infer vertical alignment from SVG baseline or browser layout behavior |
| Character spacing | Registered `letter-spacing` | DrawingML character spacing | `Native-normalized` | Unsupported CSS typography, out-of-range DrawingML spacing, and negative tracking that collapses a generated run advance or text-frame extent to a non-positive value are rejected under [`shared-standards.md` §6.7](../skills/ppt-master/references/shared-standards.md#67-advanced-text-treatments) |
| Bulleted paragraph | Recognized leading bullet form | Native DrawingML bullet | `Native-normalized` | Only the registered bullet grammar is promoted |
| Rotated text | Supported transform on the text object | Rotated text shape | `Native-normalized` | Skewed text and browser-only transforms are unsupported |
| Text shadow or glow | Supported filter/effect contract | One native outer shadow or glow | `Approximate` | One supported effect graph only; review material effects |
| WordArt, text warp, or text-on-path | No registered main-route mapping | Not generated as native WordArt | `Bake-required` or rebuild with ordinary text/geometry | Browser rendering does not imply PowerPoint support |

## 5. PowerPoint picture features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Picture | `<image>` with explicit positive dimensions and exactly one project-asset or image data-URI source | `p:pic`, media part, and relationship | Reconstructed as `<image>` | Source must resolve, use a registered format, and contain decodable bytes matching its MIME/extension; invalid frames or media fail before packaging |
| Explicit complex-SVG picture | A direct `<image>` referencing a tight, self-contained `.svg` created from one exact `<g id>` by `extract_svg_pictures.py` during `create-template` normalization | One `p:pic` backed by SVG media | Reconstructed as one `<image>`; its internal paths are not promoted to separate PowerPoint shapes | Selection is explicit and limited to `standard` / `fidelity`; no import, repetition, Master/Layout, finalize, or export heuristic may convert a group into this representation automatically |
| Stretch picture to frame | `preserveAspectRatio="none"` | Stretched native picture frame | `Native-stable` | `none` must stand alone; it intentionally changes the source aspect ratio |
| Crop picture to fill | One registered alignment plus explicit `slice` | Native `a:srcRect` crop | `Native-stable` when source dimensions are readable | Alignment is case-sensitive; unknown modes and extra tokens are errors |
| Fit picture inside frame | Omitted default, or one registered alignment plus explicit `meet` | Native fitted picture frame | `Native-normalized` | Alignment-only shorthand is compatible input that receives a normalization recommendation |
| Picture transparency | Atomic image `opacity` | Native `a:alphaModFix` | `Native-stable` | Value must be finite and within the accepted opacity grammar |
| Picture clipped to a shape | Registered image/crop-wrapper `clip-path` with one SVG-namespace shape | Picture preset or custom geometry | `Native-normalized` | Circle/ellipse/rect presets must cover the complete picture frame; use path/polygon for partial or offset contours; masks and winding-rule-dependent contours are not accepted |
| Imported cropped picture | Exact SVG-namespace nested crop wrapper produced by import, containing one direct unit-frame image in the visual root/`g` tree | Native signed `a:srcRect` on re-export | `Native-stable` within the crop contract, including negative crop values | Any generalized nested viewport, non-visual/render-only owner, extra visual child, unrepresentable crop window, redundant uncropped wrapper, or unresolved clip-marker pair is rejected |
| Picture recolor, artistic filter, blur, or complex mask | No general authoring mapping | Rebuild with supported overlays or pre-render | `Bake-required` | Arbitrary SVG filters and blend modes fail the main contract |

## 6. PowerPoint fill, line, and effect features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| No fill | `fill="none"` | `a:noFill` | `Native-stable` | Use lowercase canonical spelling in generated SVG |
| Solid fill | Locked canonical `fill="#RRGGBB"` | `a:solidFill`, with a theme token when the locked role is exactly reusable | `Native-stable` | Compatible color spellings may warn; malformed or unlocked generated values fail |
| Fill transparency | Opaque fill plus `fill-opacity` | Native alpha | `Native-stable` | Generated values are finite unitless numbers from 0 to 1 |
| Linear gradient fill | Registered `<linearGradient>` in `<defs>` | Native `a:gradFill` | `Native-normalized` | Stops, coordinates, transforms, and references must follow the closed contract |
| Radial gradient fill | Registered `<radialGradient>` | Centered circular DrawingML gradient | `Approximate` | Review focal/radius-sensitive designs |
| Pattern fill | Annotated project pattern definition | Native `a:pattFill` | `Native-normalized` | Only registered PowerPoint preset patterns are supported |
| No outline | `stroke="none"` or the registered absence of a line | `a:noFill` under `a:ln` | `Native-stable` | Do not simulate absence with zero-width ambiguous CSS |
| Solid outline | Registered `stroke` and width | Native `a:ln` | `Native-stable` | Width and paint must use canonical units/grammar |
| Compound outline | No registered single-stroke SVG representation | Explicit geometry alternative or baked asset | `Bake-required` for the compound-line identity | Tolerant PPTX import omits the unsupported outline and reports it; strict import rejects non-`sng` `cmpd` |
| Inside-aligned outline | No registered ordinary SVG stroke representation | Explicit inset geometry or baked asset | `Bake-required` for exact outline alignment | Tolerant PPTX import omits the unsupported outline and reports it; strict import rejects non-`ctr` `algn` |
| Pattern, image, or group-derived outline paint | No registered line-paint SVG mapping | Explicit geometry alternative or baked asset | `Bake-required` | Tolerant PPTX import omits the unsupported outline and reports it; strict import rejects it instead of inventing a solid color |
| Outline scaling under transforms | Exact `vector-effect="none"` or `vector-effect="non-scaling-stroke"` | Choice resolved into native line width | `Native-normalized` | Other values are rejected; generated spelling is exact and lowercase |
| Dashed or dotted outline | Registered dash array | Preset or custom DrawingML dash | `Native-normalized` | Unsupported dash semantics are rejected |
| Line cap and join | Registered cap/join values | Native line cap/join properties | `Native-stable` within the fixed join contract | Import accepts one join; miter requires exact `lim="800000"` |
| Line arrowheads | Registered start/end markers | Native head/tail end properties | `Approximate` for marker size | Only triangle, stealth, arrow, diamond, and oval follow the conditional marker contract |
| Outer shadow | One supported shadow filter graph | Native outer shadow in `a:effectLst` | `Approximate`; one imported shape/connector source `outerShdw` is reconstructed only when its non-zero offset remains classifiable | Zero-offset source shadows and unsupported graph shapes are not silently reclassified |
| Glow | One supported glow filter graph | Native glow in `a:effectLst` | `Approximate`; one imported shape/connector source glow keeps the registered radius conversion | Review when the glow carries semantic emphasis |
| Imported text-run effect | Unchanged `metadata[data-pptx-part="txbody"]` on a logical shape; import-only blocking effect status for inherited Layout/Master list styles plus vertical, relationship-bearing, and table-cell fallback routes | Original slide-local native run effect inside `p:txBody` | `Native-stable` only while the raw slide-local payload remains usable; inherited effects, edits, or fallback routes that would drop a non-empty run `effectLst` / `effectDag` block | Not public authoring syntax; a table-cell run effect also disables the native Table replacement payload |
| Whole-object transparency | Atomic element `opacity` | Alpha distributed into supported native channels | `Native-normalized` | Prefer channel-specific alpha unless the whole atomic object fades |
| Group transparency | Compatible `<g opacity>` | Descendant-normalized approximation | `Approximate` with a warning | Generated SVG should prefer descendant alpha |
| Inner shadow, soft edge, reflection, blur, turbulence, blend mode, or arbitrary mask | No registered native mapping | Explicit geometry alternative or raster asset | `Bake-required`; PPTX import keeps the base object and emits blocking diagnostics for unsupported shape/connector effects, picture/group effect DAGs, and non-empty picture/group effect lists | Handled object effects cannot be reclassified or omitted; text-run safety follows the unchanged-`txBody` row above |

## 7. PowerPoint tables

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Visually drawn table | Ordinary SVG shapes, lines, and text | Independent editable PowerPoint shapes | Fidelity follows each component row | It is not a native table and has no PowerPoint table editing model |
| PowerPoint-native table | One `<g data-pptx-replace-with="table">` with child `<metadata type="application/json">` and a visible fallback | `p:graphicFrame` containing `a:tbl` when native Chart/Table replacement is enabled | Imported supported tables reconstruct a fallback plus replacement metadata | Metadata must form the registered rectangular schema; requires `--native-charts-and-tables` |
| Merged table cells | Canonical native-table merge metadata | Native horizontal/vertical merge semantics | `Native-stable` within the closed schema | Overlapping, ambiguous, or non-rectangular merges are rejected |
| Table cell formatting | Registered native-table cell formatting fields | Native cell fill, border, text, and alignment | `Native-normalized` | Fields outside the closed schema are not guessed; imported non-empty run effects block instead of normalizing into an effect-free cell |
| Unsupported native table feature | SVG fallback or direct source preservation | Visible fallback remains, or source OOXML stays on a direct route | Explicit fallback / `Direct preservation` | Do not extend JSON ad hoc |

PowerPoint-native Chart/Table objects are opt-in. Default export keeps the SVG fallback as independently editable DrawingML shapes for visual stability; native export instead provides the object's data-source and table/chart-specific editing model, and may normalize appearance.

Imported chart groups classify their visible fallback with `data-pptx-fallback-kind="source-preview|normalized|placeholder"`; `placeholder` alone denotes the reconstruction-only fallback. `data-pptx-replacement-status` instead records why a fallback-only chart or table import cannot make an active replacement claim. Imported groups in this contract use `data-pptx-import-source="pptx"` and active claims may carry `data-pptx-fallback-sha256` for stale-edit protection. Legacy `data-pptx-native*`, `data-pptx-visual-status`, and `data-pptx-route-status` spellings remain read-compatible but are not canonical authoring.

## 8. PowerPoint charts

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Visually drawn chart | Ordinary SVG geometry and text | Independent editable PowerPoint shapes | Fidelity follows each component row | It has no “Edit Data” workbook |
| PowerPoint-native classic chart | One `<g data-pptx-replace-with="chart">` with registered JSON data in `<metadata type="application/json">` and a visible fallback | `p:graphicFrame`, classic chart part, and embedded workbook | Supported imports reconstruct a fallback plus replacement metadata | Chart type and data must match the closed schema; requires `--native-charts-and-tables` |
| Native ChartEx chart | Same marker interface with a supported ChartEx family | `cx:chart` part and embedded workbook | Supported families can reconstruct semantically | Only the registered family/field combinations are accepted |
| Chart title, legend, axes, labels, and series formatting | Registered native-chart metadata | Native chart properties | `Native-normalized` | Exact fields and supported families remain normative in `shared-standards.md` |
| Chart caption, source, or footnote | Ordinary companion SVG text outside the replacement marker | Editable slide text boxes beside the chart | `Native-stable` as text | Do not hide slide prose inside chart JSON |
| Edited SVG fallback with stale replacement metadata | Updated visible SVG plus stale hash | Default export keeps the visible SVG; native replacement fails | Explicit safety behavior | The compiler never discards a newer visual edit silently |
| Unsupported 3D or deferred chart family | SVG-drawn chart, baked asset, or direct source preservation | No guessed native chart | Fallback / `Direct preservation` | Unsupported aliases must fail native validation |

The exhaustive chart/table schemas and supported family list intentionally remain in the [normative replacement contract](../skills/ppt-master/references/shared-standards.md#powerpoint-native-chart--table-replacement-markers-opt-in).

## 9. PowerPoint playback and package features

These capabilities belong to PPTX package semantics. Their absence from page SVG is deliberate.

| PowerPoint feature | Owning project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Speaker notes | `notes/<slide>.md` sidecar | Notes Slide part and relationship | `Sidecar/package` | Notes are not SVG text and do not affect page geometry |
| Slide transition | CLI options or `animations.json` | `p:transition` | `Sidecar/package` | Unknown effects or invalid durations fail; no silent `fade` fallback |
| Object entrance animation | `animations.json` targeting stable top-level SVG group IDs | Root `p:timing` animation tree | `Sidecar/package`; the group ID is only the target anchor | Static structural layers and placeholders cannot be animated |
| Narration audio | `audio/` asset plus recorded-narration export option | Media relationship, audio carrier, and timing | `Sidecar/package` | Asset, slide association, and timing must validate |
| Automatic slide advance | Explicit transition timing or narration-derived duration | `advTm`/advance behavior | `Sidecar/package` | Click-driven animation is incompatible with recorded narration |
| Hyperlink or action | No main SVG compiler mapping | Not created by page SVG | `Direct preservation` where a native route retains source OOXML | An action-button preset supplies visual geometry only |
| Comment or review thread | No SVG or generation-side mapping | Not authored | `Direct preservation` only when explicitly owned by another route | Do not convert review metadata into visible slide content automatically |
| Relationship not owned by a mapped feature | No generic SVG escape hatch | Not generated | `Direct preservation` where applicable | Arbitrary relationship injection is unsupported |

See [`animations.md`](../skills/ppt-master/references/animations.md) and [`audio-narration.md`](./audio-narration.md) for the sidecar workflows.

## 10. Other PowerPoint-native features

| PowerPoint feature | Main-route status | Supported alternative | Boundary |
|---|---|---|---|
| SmartArt / DiagramML | No native SVG compiler mapping | Reconstruct meaning with shapes, or preserve through a native/template route | A screenshot or fallback must be explicit |
| OLE or embedded Office object | Unsupported in the SVG route | Direct preservation or a rendered preview | Do not manufacture package relationships from SVG metadata |
| Native equation / OMML | Unsupported in the SVG route | Render a formula asset or preserve native OOXML directly | A rendered formula is a picture, not an editable equation |
| Video | Unsupported as an SVG-authored media object | Direct preservation or an explicit poster/link workflow outside this contract | A `media` placeholder does not create video |
| 3D model | Unsupported | Direct preservation or baked preview | No browser-SVG approximation is treated as native 3D |
| Macro / VBA | Unsupported | Preserve only through a macro-aware direct workflow | The normal generated `.pptx` route does not synthesize VBA |
| Arbitrary Office extension XML | Unsupported | Direct preservation by an owning native workflow | The SVG compiler has no generic OOXML passthrough |

## 11. Reverse mapping: PPTX to project SVG

The importer reconstructs supported PowerPoint semantics into the same project vocabulary used by export:

| PowerPoint source object | Project SVG reconstruction |
|---|---|
| Preset shape | Expanded preset group with native carrier and visible preview evidence when supported |
| Custom geometry | `<path>` |
| Text body | `<text>` and `<tspan>` runs/paragraphs |
| Picture | `<image>`, or the registered nested crop representation |
| SVG picture with raster compatibility fallback | `<image>` sourced from the `asvg:svgBlip` relationship; the ordinary `a:blip` relationship is used only when the SVG relationship or media part is unavailable |
| Connector | Expanded line/path preview plus connector/frame/topology evidence |
| Group | `<g>` |
| Supported native table/chart | Visible fallback plus native-object metadata |
| Unsupported graphic frame or SmartArt | Explicit preview, placeholder, or unsupported status |

This is semantic reconstruction, not a syntax round trip. Master/Layout restoration belongs to the template-structure workflows; an ordinary visual import does not infer reusable topology from slide appearance.

### Import operating modes and recovery boundary

`pptx_to_svg.py` defaults to tolerant import because its inputs are user-owned or third-party PPTX files. `--strict` is available for parser development, contract verification, and reproducing the first source violation. Strict generated-SVG validation and export remain unchanged.

| Source condition | Default tolerant import | `--strict` | Diagnostic result |
|---|---|---|---|
| Recognized color semantics with unrelated source metadata | Canonicalize the recognized color and modifiers | Reject the noncanonical structure | Warning with part, slide, and shape context where available |
| Unsupported fill, outline, effect, image fill, text body, or style property | Keep the object and omit only the unsupported property or feature | Stop at the first violation | Warning names the omitted feature and fallback |
| Unsupported object that cannot be recovered property-by-property | Replace that object with a visible diagnostic placeholder; omit it only when it has no usable frame | Stop at the first violation | Warning identifies the source object |
| Unsupported slide or part background | Omit that background and continue the page/part | Stop at the first violation | Warning identifies the owning part |
| Corrupt package/XML or missing required package structure | Stop; no safe page-level recovery exists | Stop | Clean command error; no raw Python traceback |

Every successful run writes `<output>/conversion-report.json`. The report records the mode, slide and warning counts, stable reason code, source message, chosen fallback, package part, and—when available—slide index plus shape id/name/kind. Tolerant import is therefore not silent: it maximizes usable output while making every contract recovery reviewable.

## 12. Validation ownership

The four layers have deliberately different jobs:

| Layer | Responsibility |
|---|---|
| Prompt, template, and examples | Generate only the canonical representation for each PowerPoint feature |
| `svg_quality_checker.py` | Reject invalid/unsupported mappings; warn but allow registered compatible spellings or fidelity risks |
| `svg_to_pptx.py` and package read-back | Normalize compatible input, compile DrawingML, and reject any result that would be ambiguous, structurally inconsistent, or invalid |
| `pptx_to_svg.py` | In default tolerant mode, preserve the usable deck and report source-owned degradation at the narrowest safe boundary; in `--strict` mode, stop at the first unsupported or malformed source construct |

A generated-SVG warning is not permission to guess. It is reserved for a deterministic supported mapping whose spelling or fidelity deserves attention. Missing mappings, invalid units, malformed metadata, broken structure contracts, and potentially repair-triggering generated DrawingML remain errors. Import diagnostics describe explicit loss or normalization of source-owned content; they never authorize the importer to invent unsupported semantics.

## 13. Adding or changing a mapping

Treat a mapping change as a compiler change, not as a permissive SVG parser tweak:

1. Name the PowerPoint capability and its intended editable DrawingML result.
2. Define one canonical project-SVG or sidecar representation in [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md).
3. State accepted compatible input separately from generated authoring.
4. Implement export, and implement import only when semantic reconstruction is supported.
5. Add checker classification: error for invalid/ambiguous input, warning only for deterministic compatible or approximate input.
6. Perform focused regression verification on the generated SVG, PPTX package, PowerPoint rendering, and reverse import where applicable.
7. Update the matching English and Chinese row in this guide.

Implementation entry points:

- Export: [`svg_to_pptx.py`](../skills/ppt-master/scripts/svg_to_pptx.py) and `scripts/svg_to_pptx/`
- Import: [`pptx_to_svg.py`](../skills/ppt-master/scripts/pptx_to_svg.py) and `scripts/pptx_to_svg/`
- Validation: [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py)
- Canonical contract: [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md)
