# PowerPoint Feature ↔ Project SVG Mapping Guide

[中文版](./zh/powerpoint-svg-mapping.md)

## Purpose and authority

This guide answers one question from the PowerPoint user's point of view: **for a PowerPoint feature, what project representation owns it, and what survives export or import?** PowerPoint semantics are therefore the primary index. SVG elements appear only as the implementation of a specific PowerPoint capability.

This is a public capability map, not a second syntax specification and not a promise to convert arbitrary SVG or arbitrary OOXML. The normative contract remains [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md). When this guide and that contract differ, the contract wins. A feature not listed here is not implicitly supported.

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
| Presentation slide size | Root SVG `viewBox`, selected through the project canvas contract | Presentation width and height; `1 SVG px = 9,525 EMU` at 96 DPI | `Native-stable`; imported coordinates are projected onto the SVG canvas | Every page must use the selected canvas; a root transform is forbidden |
| Slide | One complete `svg_output/<slide>.svg` page | One `p:sld` with its relationships | Reconstructed as one complete SVG page | SVG is the visible page authority; notes and package behavior are separate |
| Object position and size | Absolute SVG coordinates and element bounds | `a:xfrm` offsets and extents | `Native-normalized` through coordinate conversion | Values must be finite and use the registered coordinate grammar |
| Z-order | SVG source order, back to front | PowerPoint shape-tree order | Reconstructed in shape-tree order | Do not rely on browser-only stacking behavior |
| Rotation, scale, translation, and mirror | Supported SVG transform forms | DrawingML transform or normalized geometry | `Native-normalized`; matrices may be decomposed | Skew and shear outside the registered transform contract are not accepted |
| Theme colors and fonts | Roles locked in `spec_lock.md`; canonical SVG uses the resolved values | Theme-aware tokens where an exact locked role can be retained; otherwise direct DrawingML values | `Native-stable` for registered roles | New pages must not invent unlocked colors, fonts, or text sizes |
| PowerPoint-only package identity | `spec_lock.md` structure declarations and the package builder | Presentation, Master, Layout, relationship, and content-type registrations | Read back from package structure, not inferred from page appearance | Final-package read-back must match the declared roster |

See [`canvas-formats.md`](../skills/ppt-master/references/canvas-formats.md) for supported canvases and the normative standards for the exact unit grammar.

## 2. Master, Layout, background, and placeholder features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Free-design deck structure | `pptx_structure.mode: flat`; page content remains slide-local | One clean project Master and one Blank Layout, with represented objects on slides | `Native-stable` package topology for the flat route | No authored Master/Layout/layer/placeholder metadata is allowed |
| Template-backed deck structure | `pptx_structure.mode: structured` plus explicit Master/Layout/page assignments | Declared `p:sldMaster`, `p:sldLayout`, registrations, and slide parentage | `Native-stable` within the explicit structure contract | The exporter never guesses a Master, Layout, or placeholder topology |
| Slide Master | Root Master identity plus atomic `data-pptx-layer="master"` objects | Reusable Master part and picker identity | Source structure is restored by template/import workflows | Master atoms must be direct, stable, and identical across their slides |
| Slide Layout | Root Layout identity plus atomic `data-pptx-layer="layout"` objects | Reusable Layout part under one Master | Source Layouts can be restored; adaptive authoring may allocate a new Layout | Reuse a Layout key only when its fixed atoms and slot contract are identical |
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
| Generic object placeholder | One compatible carrier, or an explicit composite proxy binding | `p:ph` type `obj` | Native binding; composite visible content remains ordinary shapes | Composite slots must use the registered proxy downgrade |
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
| Arrowhead line | `<line>` or supported path with registered start/end markers | Native DrawingML line head/tail ends | `Native-normalized`; marker size is approximate | Marker definitions must follow the conditional marker contract |
| Native connector | Authored preset connector fragment with connector metadata | `p:cxnSp` | Imported connectors retain compact connector metadata | `Native-stable` for the registered preset/connector schema |
| Freeform shape | `<path>` | `p:sp` with `a:custGeom` | Imported custom geometry reconstructs as a path | `Native-normalized`; SVG arcs are converted to cubic segments |
| Polygon | `<polygon>` | Closed custom geometry | `Native-normalized` | Points must be finite and valid |
| Polyline | `<polyline>` | Open custom geometry | `Native-normalized` | Points use the same finite, registered grammar as other generated geometry |
| PowerPoint preset shape | Registry-generated authored preset fragment | One editable preset `p:sp` | Preset identity and adjustments can survive import/export | Use [`preset_shape_svg.py`](../skills/ppt-master/scripts/preset_shape_svg.py); do not hand-invent metadata |
| Imported preset shape | Import metadata plus its visible SVG fallback | Restored preset when the payload is valid and unchanged | `Native-stable` within the import contract | Unsupported presets remain explicit diagnostic fallbacks, not guessed geometry |
| Action button shape | Authored `actionButton*` preset fragment | Visual preset geometry only | Shape geometry can round-trip | No click action, navigation target, or hyperlink is created |
| Group | `<g>` | `p:grpSp`, or a documented flatten/collapse for a special carrier | Grouped content can reconstruct as `<g>` | Structural atoms and placeholder contracts override ordinary grouping |
| Reused local symbol | Registered same-document `<use>` contract or project icon placeholder | Expanded editable shapes in the generated slide | Original symbol graph is not promised on import | External use, unsupported symbol features, and structural metadata reuse are rejected |
| Icon | `<use data-icon="library/name">` resolved by the project icon pipeline | Editable vector primitives/group after expansion | Reconstructed geometry, not the original library reference | Icon identifiers are case-sensitive and must exist in the synchronized library |
| SmartArt / DiagramML | No main SVG object mapping | Main redesign route may rebuild the meaning with ordinary shapes | `Direct preservation` in native/template routes; otherwise a preview or explicit fallback | Do not label a decorative group as native SmartArt |

Preset-shape selection and its exact atomic fragment contract are documented in [`native-shape-authoring.md`](../skills/ppt-master/references/native-shape-authoring.md).

## 4. PowerPoint text features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Text box | `<text>` | Editable `p:sp` with `p:txBody` | Reconstructed as `<text>` and, when needed, `<tspan>` | Text must be well-formed XML and use registered attributes |
| Mixed formatting within a line | Non-positioned `<tspan>` runs | DrawingML runs in one text frame | `Native-normalized`; registered run formatting remains editable | Positioning that changes frame geometry may split the result |
| Multiple paragraphs | Mergeable text/tspan structure | Multiple `a:p` paragraphs in one text frame | `Native-normalized` | Strict independently positioned lines may remain separate text boxes |
| Font family | Canonical `font-family` resolved against the project lock | Direct typeface or registered theme font | `Native-stable` within installed/font-substitution limits | Unlocked or unavailable fonts are reported by validation |
| Font size | Finite unitless SVG pixels, for example `font-size="24"` | DrawingML hundredths of a point; `1 px = 0.75 pt` | `Native-stable` after unit conversion | Generated authoring uses only unitless px; registered legacy units are compatible input and warn, while unknown units error; DrawingML minimum is 1 pt |
| Bold, italic, underline, and strike | Registered text attributes on `<text>`/`<tspan>` | DrawingML run properties | `Native-stable` | Only documented values are accepted |
| Text fill and transparency | Canonical fill plus run alpha | DrawingML run fill and alpha | `Native-normalized` | Use the semantic alpha channel, not an unregistered CSS effect |
| Text outline | Registered stroke on text | DrawingML run outline | `Native-normalized` | Review when outline carries fine visual meaning |
| Text alignment | `text-anchor` and registered paragraph semantics | Paragraph alignment plus normalized text-frame position | `Native-normalized` | Browser layout heuristics are not part of the contract |
| Vertical text-frame alignment | No canonical generated-SVG control; generated text boxes use top anchoring | Top-anchored DrawingML text body | Imported vertical text may be normalized, but the main route does not expose a general authoring control | Do not infer vertical alignment from SVG baseline or browser layout behavior |
| Character spacing | Registered `letter-spacing` | DrawingML character spacing | `Native-normalized` | Unsupported CSS typography is rejected |
| Bulleted paragraph | Recognized leading bullet form | Native DrawingML bullet | `Native-normalized` | Only the registered bullet grammar is promoted |
| Rotated text | Supported transform on the text object | Rotated text shape | `Native-normalized` | Skewed text and browser-only transforms are unsupported |
| Text shadow or glow | Supported filter/effect contract | One native outer shadow or glow | `Approximate` | One supported effect graph only; review material effects |
| WordArt, text warp, or text-on-path | No registered main-route mapping | Not generated as native WordArt | `Bake-required` or rebuild with ordinary text/geometry | Browser rendering does not imply PowerPoint support |

## 5. PowerPoint picture features

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Picture | `<image>` with a project asset or data URI | `p:pic`, media part, and relationship | Reconstructed as `<image>` | Source must resolve, and dimensions must be valid |
| Stretch picture to frame | `preserveAspectRatio="none"` | Stretched native picture frame | `Native-stable` | `none` must stand alone; it intentionally changes the source aspect ratio |
| Crop picture to fill | One registered alignment plus explicit `slice` | Native `a:srcRect` crop | `Native-stable` when source dimensions are readable | Alignment is case-sensitive; unknown modes and extra tokens are errors |
| Fit picture inside frame | Omitted default, or one registered alignment plus explicit `meet` | Native fitted picture frame | `Native-normalized` | Alignment-only shorthand is compatible input that receives a normalization recommendation |
| Picture transparency | Atomic image `opacity` | Native `a:alphaModFix` | `Native-stable` | Value must be finite and within the accepted opacity grammar |
| Picture clipped to a shape | Image-only registered `clip-path` | Picture preset or custom geometry | `Native-normalized` | Arbitrary masks are not accepted |
| Imported cropped picture | Nested crop SVG representation produced by import | Native `a:srcRect` on re-export | `Native-stable` within the crop contract | Do not manually generalize nested SVG into an unrestricted feature |
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
| Outline scaling under transforms | Exact `vector-effect="none"` or `vector-effect="non-scaling-stroke"` | Choice resolved into native line width | `Native-normalized` | Other values are rejected; generated spelling is exact and lowercase |
| Dashed or dotted outline | Registered dash array | Preset or custom DrawingML dash | `Native-normalized` | Unsupported dash semantics are rejected |
| Line cap and join | Registered cap/join values | Native line cap/join properties | `Native-stable` | Only documented values are accepted |
| Line arrowheads | Registered start/end markers | Native head/tail end properties | `Approximate` for marker size | See the conditional marker contract |
| Outer shadow | One supported shadow filter graph | Native outer shadow in `a:effectLst` | `Approximate` | Unsupported graph shapes are not silently simplified |
| Glow | One supported glow filter graph | Native glow in `a:effectLst` | `Approximate` | Review when the glow carries semantic emphasis |
| Whole-object transparency | Atomic element `opacity` | Alpha distributed into supported native channels | `Native-normalized` | Prefer channel-specific alpha unless the whole atomic object fades |
| Group transparency | Compatible `<g opacity>` | Descendant-normalized approximation | `Approximate` with a warning | Generated SVG should prefer descendant alpha |
| Inner shadow, soft edge, reflection, blur, turbulence, blend mode, or arbitrary mask | No registered native mapping | Explicit geometry alternative or raster asset | `Bake-required` | Converter and checker must not invent a visual downgrade |

## 7. PowerPoint tables

| PowerPoint feature | Project representation | PPTX result | Import and fidelity | Validation boundary |
|---|---|---|---|---|
| Visually drawn table | Ordinary SVG shapes, lines, and text | Independent editable PowerPoint shapes | Fidelity follows each component row | It is not a native table and has no PowerPoint table editing model |
| PowerPoint-native table | One `<g data-pptx-replace-with="table">` with child `<metadata type="application/json">` and a visible fallback | `p:graphicFrame` containing `a:tbl` when native Chart/Table replacement is enabled | Imported supported tables reconstruct a fallback plus replacement metadata | Metadata must form the registered rectangular schema; requires `--native-charts-and-tables` |
| Merged table cells | Canonical native-table merge metadata | Native horizontal/vertical merge semantics | `Native-stable` within the closed schema | Overlapping, ambiguous, or non-rectangular merges are rejected |
| Table cell formatting | Registered native-table cell formatting fields | Native cell fill, border, text, and alignment | `Native-normalized` | Fields outside the closed schema are not guessed |
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
| Preset shape | SVG primitive/path plus compact preset metadata when supported |
| Custom geometry | `<path>` |
| Text body | `<text>` and `<tspan>` runs/paragraphs |
| Picture | `<image>`, or the registered nested crop representation |
| Connector | Line/path plus connector metadata |
| Group | `<g>` |
| Supported native table/chart | Visible fallback plus native-object metadata |
| Unsupported graphic frame or SmartArt | Explicit preview, placeholder, or unsupported status |

This is semantic reconstruction, not a syntax round trip. Master/Layout restoration belongs to the template-structure workflows; an ordinary visual import does not infer reusable topology from slide appearance.

## 12. Validation ownership

The three layers have deliberately different jobs:

| Layer | Responsibility |
|---|---|
| Prompt, template, and examples | Generate only the canonical representation for each PowerPoint feature |
| `svg_quality_checker.py` | Reject invalid/unsupported mappings; warn but allow registered compatible spellings or fidelity risks |
| `svg_to_pptx.py` and package read-back | Normalize compatible input, compile DrawingML, and reject any result that would be ambiguous, structurally inconsistent, or invalid |

A warning is not permission to guess. It is reserved for a deterministic supported mapping whose spelling or fidelity deserves attention. Missing mappings, invalid units, malformed metadata, broken structure contracts, and potentially repair-triggering DrawingML are errors.

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
