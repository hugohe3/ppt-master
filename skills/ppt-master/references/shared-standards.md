# Shared Technical Standards

This file is the sole authoring authority for SVG constraints shared across PPT
Master routes. Generated specs, templates, role prompts, and user-facing docs
may link here, but must not restate the rules.

The policy is intentionally negative:

- **Required** entries exist only when every SVG needs the same foundation.
- **Forbidden** entries identify constructs the pipeline rejects or cannot
  preserve safely.
- **Conditional** entries document features that work only through a restricted
  syntax, an approximation, an opt-in flag, or PPT-specific metadata.

Anything else already handled by the converter is freely usable and is not
listed as an "allowed feature." Unknown visual elements still fail quality
checking/export rather than being dropped silently.

---

## 1. Required Foundation, Forbidden Features, and Conditional Interfaces

### 1.0 Text characters: must be well-formed XML

SVG is strict XML. Two rules for all text and attribute values:

| Character category | Required form | Forbidden form |
|---|---|---|
| Typography & symbols (em dash, en dash, ©, ®, →, ·, NBSP, full-width punctuation, emoji…) | **Raw Unicode characters** — write `—` `–` `©` `®` `→` directly | HTML named entities — `&mdash;` `&ndash;` `&copy;` `&reg;` `&rarr;` `&middot;` `&nbsp;` `&hellip;` `&bull;` etc. |
| XML reserved characters (`&`, `<`, `>`, `"`, `'`) | **XML entities only** — `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`) | Bare `&` `<` `>` (e.g. `R&D`, `error < 5%`) |

One offending character invalidates the file and aborts export.

**Structural blacklist** (in addition to the character rules above):

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

The blacklist above is exhaustive for globally forbidden SVG syntax. Features
that require a restricted form are not globally forbidden; they are documented
under the conditional contracts below.

> **`marker-start` / `marker-end` is conditional** — see §1.1.
>
> **`clipPath` on `<image>` is conditional** — see §1.2.
>
> **Static same-document `<use>` is conditional** — see §1.3.
>
> **Inline CSS geometry, group opacity, simple gradients, and filters are
> conditional** — see §2 and §6.
>
> **PPT preset patterns and native chart/table/template metadata are
> conditional** — see §7.

DrawingML has no arbitrary per-pixel alpha-compositing path. Effects that rely
on one, including text-knockout image fills and arbitrary alpha composites,
must be baked into a raster asset before SVG export.

---

### 1.1 Line-end Markers (Conditional Contract)

`marker-start` and `marker-end` are supported on `<line>` and `<path>` only
when the referenced marker fits this native-arrow contract:

| Concern | Required form |
|---|---|
| Reference | Exact local `url(#id)` to a `<marker>` in `<defs>` |
| Orientation | `orient="auto"` |
| Shape | Closed 3-vertex path/polygon (triangle), closed 4-vertex path/polygon (diamond), or one `<circle>`/`<ellipse>` (oval) |
| Color parity | Marker fill matches the parent line stroke; DrawingML arrows inherit the line color |

The converter maps the three shapes to DrawingML triangle, diamond, and oval
line ends. Other marker shapes do not have a native mapping and are dropped
with a warning.

---

### 1.2 Image Clipping (Conditional Contract)

`clip-path` has a native picture-crop mapping only on `<image>` elements and
only under this contract:

| Concern | Required form |
|---|---|
| `<clipPath>` element defined inside `<defs>` | Converter looks up clip defs via id index |
| Contains a **single supported** shape child | The converter uses the first supported child; multiple shapes are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (with rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| Used **only on `<image>` elements** | Non-image elements with clip-path are **forbidden** |

| SVG clip shape | DrawingML output |
|---|---|
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse"/>` |
| `<rect rx="..."/>` | `<a:prstGeom prst="roundRect"/>` with adj value |
| `<path>` / `<polygon>` | `<a:custGeom>` with path commands |

`clip-path` on shapes, groups, or text is forbidden; author the target geometry
directly instead.

---

### 1.3 Static Same-Document `<use>` (Conditional Contract)

**Expansion contract**: Static local reuse is compile-time authoring shorthand. `finalize_svg.py` and
native export replace each qualifying instance with cloned primitive content;
PPTX-to-SVG import emits the resulting primitives and does **not** reconstruct
the original `<use>` / `<symbol>` structure.

| Concern | Required form |
|---|---|
| Reference syntax | Exact same-document fragment: `href="#id"` or `xlink:href="#id"`. If both attributes exist, their values MUST match. |
| Referenced target | One of `<symbol>`, `<g>`, `<use>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<polygon>`, `<polyline>`, `<text>`, or `<image>`. Nested local `<use>` is recursively expanded. |
| Instance position | `<use x>` / `<use y>` are finite unitless or `px` values; omitted values default to `0`. |
| Symbol viewport | A referenced `<symbol>` MUST have a finite four-number `viewBox` with positive width/height. Its `<use>` MUST have positive finite unitless or `px` `width` and `height`. |
| Aspect ratio | Default/aligned `meet` values and plain `preserveAspectRatio="none"` are supported. `slice`, `refX`, and `refY` are forbidden. |
| Viewport boundary | Symbol artwork MUST stay inside its `viewBox`; expansion does not reproduce symbol overflow clipping. |
| Internal references | Reusable subtrees use exact fragment forms: `href="#id"`, `xlink:href="#id"`, and `url(#id)`. The expander rewrites these references together with instance-local cloned IDs. |
| Structural metadata | Neither the `<use>` instance nor its referenced subtree may carry `data-pptx-layer*`, `data-pptx-native*`, or `data-pptx-placeholder*`. Author those objects directly instead of reusing them. |
| Safety limits | A reachable reference chain may contain at most 64 instances, and one SVG may expand at most 10,000 local `<use>` instances. |

**Forbidden — unsafe local references**:

- External/file/data URLs, missing targets, conflicting `href` / `xlink:href`,
  unsupported target elements, and circular reference chains
- Duplicate IDs on the referenced target, the `<use>` instance, or anywhere in
  the reused subtree
- Quoted/whitespace CSS fragment variants such as `url('#id')`; use exact
  `url(#id)` when an internal paint/filter/clip reference must be rewritten

**Contract example**:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
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
  <use xlink:href="#legendRow" x="120" y="120"/>
</svg>
```

---

## 2. Conditional Compatibility Mappings

### 2.1 Literal Inline Geometry

The following geometry properties may appear in the same element's
`style="..."`. The pipeline materializes them as
XML geometry attributes before SVG post-processing and native PPTX conversion.
An inline geometry declaration overrides an existing same-name XML attribute.

| Element | Recognized properties |
|---|---|
| `<rect>` | `x`, `y`, `width`, `height`, `rx`, `ry` |
| `<circle>` | `cx`, `cy`, `r` |
| `<ellipse>` | `cx`, `cy`, `rx`, `ry` |
| `<image>` | `x`, `y`, `width`, `height` |
| `<svg>` | `x`, `y`, `width`, `height` |
| `<use>` | `x`, `y`, `width`, `height` |

**Hard rule — inline geometry grammar**: every non-zero value is one finite
`px` literal, such as `120px` or `-8.5px`; exact zero may be unitless. `width`,
`height`, `rx`, `ry`, and `r` must be non-negative. Percentages, `auto`,
`calc()`, `var()`, `!important`, `inherit`, and every other unit are forbidden.
Do not put geometry on an unsupported element: line endpoints, text positions,
path data, and polygon/polyline points remain XML attributes.

**Forbidden — CSS geometry cascade**: `<style>`, `class`, selector rules,
external stylesheets, and imported styles remain forbidden. This contract is
only for literal declarations in an element's own `style` attribute; PPT Master
does not compute CSS cascade or custom properties. Root canvas authority remains
the `viewBox`, regardless of root `<svg>` compatibility width/height values.

### 2.2 Group Opacity Is Approximate

`<g opacity="0.3">...</g>` maps the group alpha onto each descendant shape,
text run, picture, and supported
shadow/glow effect. Nested group and child opacity values multiply. Overlapping
children may differ from SVG isolated-group compositing because DrawingML has no
equivalent group-alpha model. With `--native-objects`, transparent native
table/chart markers are rejected; omit that flag to export their SVG fallback.

---

## 3. Canvas Format Quick Reference

> See [`canvas-formats.md`](canvas-formats.md) for the full format table (presentations / social / marketing) and the format-selection decision tree.

---

## 4. Required Page Contract and Conditional Packaging

### 4.0 Complete Page-Design Contract

| Concern | Requirement |
|---|---|
| Visible slide result | The completed `svg_output/<slide>.svg` MUST contain every visible text, image, shape, diagram, chart/table fallback, background, and template-derived layout element intended for that slide. External visual assets are valid when the SVG references them explicitly. |
| Template/control inputs | Templates, `design_spec.md`, and `spec_lock.md` guide authoring. Do not depend on them to add visible elements after the page SVG is complete. |
| PPTX translation | The exporter may map represented SVG content to DrawingML/native objects and deduplicate represented elements into Master/Layout/Slide parts. It MUST NOT invent visible slide content absent from the SVG. |
| Excluded package behavior | Speaker notes, animations, transitions, narration audio, PPTX relationships, and direct native-PPTX workflows remain separately owned. They are not part of the SVG page-design contract. |

**Hard rule — page-design closure**: A final page SVG is the sole visual/design authority for that page on every SVG-authoring route. SVG is not the authority for the entire PPTX package.

### 4.1 Semantic SVG Marker Contract

Semantic markers are minimal compiler hints orthogonal to native SVG semantics.
Existing `data-pptx-layout` / layer / placeholder / native-object metadata is
authoritative and read first. A `baseline` / free-design root declares
`data-pptx-page-role`; template/preserve roots already declare their Layout.
Add `data-pptx-role` only when no specialized marker expresses the required
page-frame behavior; the element also uses a stable unique `id`. Do not classify
ordinary page content or move visible facts out of SVG attributes/text into
metadata. See
[`semantic-svg.md`](semantic-svg.md) for the canonical vocabulary and examples.

- **Canvas authority**: `viewBox` MUST match the selected canvas dimensions.
  Root `width` and `height` are optional and do not override it.
- **Font portability**: font families used by the deck must resolve to installed
  export faces. `@font-face` remains forbidden; the typography contract lives in
  [`strategist.md §g`](strategist.md).
- **Icon placeholders**: `<use data-icon="library/name">` is a pipeline-specific
  form, distinct from local SVG reuse. Follow the contract in
  [`../templates/icons/README.md`](../templates/icons/README.md).
- **Local reuse**: ordinary same-document `<use>` follows §1.3.

### 4.2 Conditional Editability and Package Promotion

These forms are needed only when the stated PPT behavior matters:

| Desired behavior | Required form |
|---|---|
| One editable PPT text frame with mixed inline formatting | Put the logical line in one `<text>` and use non-positional `<tspan>` children. A `tspan` with `x`, `y`, or `dy` starts a new positioned line and is flattened to another text frame. Separate `<text>` elements remain valid when separate frames are intended. |
| Stable object grouping or object-level animation anchor | Wrap the intended object in `<g id="...">`. Raw top-level primitives and anonymous groups remain valid when neither behavior is needed. |
| Native PowerPoint background promotion | Use a direct, full-canvas, solid `<rect>` without transform, filter, clip, rounding, or visible stroke. Other SVG backgrounds remain ordinary slide shapes. Template routes add the ownership metadata in §7. |
| Free-design page family/chrome extraction | Use the semantic markers in §4.1. Marker-free pages retain conservative filename/id fallbacks, but no visual content is inferred. |

**Hard rule — supported shape conversion**: Every PPT editability claim in this specification refers to the project converter reading `svg_output/` and emitting native DrawingML. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is unsupported; do not narrow the authoring contract to its undocumented SVG subset.

---

## 5. Workflow Authority

The serial post-processing and export workflow belongs to
[`SKILL.md` Step 7](../SKILL.md). This file defines SVG authoring boundaries
and intentionally does not mirror commands, flags, or output behavior.

---

## 6. Conditional Paint Servers and Filters

### 6.1 Simple Gradients

Gradient paint is conditional because the native route implements a simple
DrawingML subset, not the full SVG paint-server model:

- Define `linearGradient` or `radialGradient` as a direct child of `<defs>`
  with a unique `id`.
- Reference it with the exact local form `url(#id)` from a supported
  `fill`/`stroke` context.
- Put the intended colors and offsets directly on its `<stop>` children.
- Do not depend on external references, inherited gradient chains,
  `gradientTransform`, or `spreadMethod`; those semantics are not preserved by
  native export.

Native export reduces a linear gradient to its angle. A radial gradient becomes
a centered circular DrawingML gradient; SVG focal-point and radius geometry
(`cx`, `cy`, `r`, `fx`, `fy`) remains useful in browser preview but is not
preserved in the native object.

The quality checker validates the definition location, reference, and
fill/stroke context.

### 6.2 Shadow and Glow Filters

Filters are conditional native-effect metadata, not a general SVG filter
surface. An element's `filter` must be an exact local `url(#id)` reference to
a direct `<defs><filter>` definition that can be reduced to one DrawingML
outer shadow or glow.

The accepted graph may contain:

- `feDropShadow`; or `feGaussianBlur` with optional `feOffset` and `feFlood`
- `feComposite`, `feMerge`, and `feMergeNode` for the standard composition
- `feComponentTransfer` with a linear `feFuncA` for alpha adjustment

At least one `feDropShadow` or `feGaussianBlur` is required. A non-zero offset
selects an outer shadow; otherwise the exporter emits a glow. Other filter
primitives and arbitrary multi-effect graphs are forbidden because the
converter would otherwise approximate or ignore them.

---

## 7. Conditional PPT Interfaces

The interfaces below exist only for PPT behavior that ordinary SVG semantics
cannot express. Use them only when the corresponding native capability is
required.

### Pattern Fill — `<pattern>` with PPTX preset annotation

`<pattern>` requests one fixed DrawingML preset; the converter does not render
the tile's arbitrary geometry. Use this interface only when that preset mapping
is intended.

`data-pptx-pattern="<preset>"` is required to select the intended preset from
the enum below; without it, export falls back to `ltUpDiag`.

Pattern colors may come from importer metadata (`data-pptx-fg` /
`data-pptx-bg`) or from the pattern's child paint. Without metadata, the first
child `<rect>` fill becomes the background and the first stroke (or other fill)
becomes the foreground. A missing background defaults to white; a missing
foreground means no native pattern fill can be emitted. The child geometry
itself is never used as a repeatable tile.

**Valid `data-pptx-pattern` values** (OOXML `ST_PresetPatternVal` — closed enum, anything outside makes PowerPoint open with "needs to be repaired"):

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid` — common typo)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

`svg_quality_checker.py` warns when the annotation is missing and errors when
the preset is outside this enum.

### Native PPTX Table / Chart Markers (Opt-in)

Native PowerPoint tables and Excel-backed charts activate at export time only. The default chart/table route remains hand-authored SVG geometry so the deck stays pixel-stable across PowerPoint / Keynote / LibreOffice / WPS.

**Authoring — markers are standard on supported data charts and text-grid tables**: Executor writes the marker at draw time on every data chart whose type falls in the supported set and on every pure text-grid data table ([executor-base.md §3.2](executor-base.md)), so any deck can later form native objects without regeneration. Tables with merged or graphical cells stay unmarked on the SVG fallback route. The marker group supplies both: visible SVG fallback children for browser/live-preview rendering, and JSON metadata for `svg_to_pptx` native export.

**Hard rule — activation is the opt-in, dormant unless exported with `--native-objects`**: A marker only declares that a group is eligible for native export. Normal `svg_to_pptx.py` runs keep the fallback SVG children. Pass `--native-objects` only when editability in PowerPoint matters more than cross-renderer layout fidelity: it emits the PowerPoint object and skips the fallback children to avoid duplicates. Native styling preserves the core palette, text, axis, grid, and background colors where possible, but it is still a PowerPoint chart/table object rather than a pixel-identical SVG drawing.

| Marker | Native output | Required metadata |
|---|---|---|
| `<g data-pptx-native="table">` | `<p:graphicFrame>` with `<a:tbl>` | bounds + `columns` or `rows` |
| `<g data-pptx-native="chart">` | `<p:graphicFrame>` with `c:chart` / `cx:chart` + chart part + embedded workbook | bounds + `type`, plus chart data |

**Metadata placement**: Put JSON in a child `<metadata data-pptx-native="...">`. Attribute JSON (`data-pptx-json="..."`) is supported but harder to XML-escape correctly.

**Bounds**: Provide `x`, `y`, `width`, and `height` in metadata, or as
`data-pptx-x` / `data-pptx-y` / `data-pptx-width` / `data-pptx-height` on the
marker group. If any bound is omitted, the exporter infers the object frame
from the visible fallback geometry; this keeps SVG fallback and native object
placement aligned. Complete explicit bounds are absolute slide coordinates;
marker/ancestor `translate` and `scale` transforms apply only when at least one
bound is inferred. `x`, `y`, `width`, and `height` must be finite and resolve
inside PowerPoint's 32-bit DrawingML coordinate range; `width` and `height`
must resolve to at least one EMU. Native table frames must additionally resolve
to at least one EMU per resolved row and column.

**Validation**: `svg_quality_checker.py` validates native marker kind, JSON
metadata, bounds/fallback availability, table rows/columns, supported chart
type, and chart data shape before export.

```xml
<g id="p03-revenue-chart" data-pptx-native="chart">
  <metadata data-pptx-native="chart">
    {
      "x": 120, "y": 150, "width": 520, "height": 320,
      "type": "column",
      "title": "Revenue by Segment",
      "categories": ["Q1", "Q2", "Q3"],
      "series": [
        {"name": "Cloud", "values": [12, 15, 19]},
        {"name": "Services", "values": [8, 9, 11]}
      ]
    }
  </metadata>
  <!-- Visible SVG fallback for live preview / non-native export goes here. -->
</g>
```

**Table schema**: Native tables are rectangular DrawingML grids. Use `columns`
for the optional header row and `rows` for body rows; shorter rows are padded
with blank cells unless `strict_grid: true` is set. Tables may contain at most
1000 resolved rows and 1000 resolved columns. Use `column_widths` and
`row_heights` as relative weights. Weight lists must match the resolved grid,
contain finite non-negative numbers, and include at least one positive value.
If present, `header_rows` must be an integer from `0` through the resolved row
count. Write `strict_grid`, `style.band_row`, and cell `bold` as JSON booleans.
Cell objects accept `text`, `fill`, `color`,
`align`, `valign`, `bold`, `font_size`, `padding`, `border_color`, and
`border_width`; the same `padding`, `border_color`, and `border_width` keys may
also live under `style` as table defaults. Native table typography mirrors the
visible SVG fallback: put `style.font_family` and `style.font_size` on the
marker from the table text already drawn, then use `style.header_font_size` or
per-cell `font_size` only when the fallback visibly differs. If the fallback
has no explicit table font, use the deck body family and locked body size from
`spec_lock.md`.

**Hard rule — table metadata is the native source of truth**: Every row,
summary line, value, and cell-level style that must survive
`--native-objects` must be present in `columns` / `rows`. SVG fallback text is
discarded during native export. `svg_quality_checker.py` warns when visible
fallback `<text>` inside a native table marker does not appear in metadata.
For numeric or currency columns, use cell objects with `align: "r"`; SVG
`text-anchor="end"` does not carry into the native table.

**Forbidden — native merged table cells**: Do not use `rowSpan`, `colSpan`,
`gridSpan`, `hMerge`, `vMerge`, or top-level merge lists in native table
metadata. `svg_to_pptx.py --native-objects` rejects them so merged-cell tables
do not silently degrade into incorrect grids. Keep merged-cell tables on the
default SVG fallback route, or merge cells manually in PowerPoint after native
export.

**Category chart schema**: `column`, `bar`, `line`, `area`, `pie`,
`doughnut`, `pieOfPie`, `barOfPie`, and `radar` use `categories` plus
`series[].values`. Pie-family charts (`pie`, `doughnut`, `pieOfPie`, and
`barOfPie`) must have exactly one series; the exporter assigns per-category
slice colors so single-series charts do not collapse into one solid color.
Column and bar charts may set per-point colors with `series[].point_colors`
or `series[].pointColors`; the list must match `series[].values` length.
Classic category charts may set native PowerPoint data labels with
`data_labels`. Use `data_labels: true` for default value labels, or an object
with `show_value`, `position`, `number_format`, `font_size`, `font_family`,
`bold`, `color`, and optional per-point `colors`. Supported label positions
depend on chart type: clustered column/bar labels may use `outside_end`,
`inside_end`, `inside_base`, or `center`; stacked / percent-stacked column/bar
labels may use `inside_end`, `inside_base`, or `center`; line labels may use
`above`, `center`, or `best_fit`; area labels do not emit a native label
position. To label only selected data points, use `data_labels.points` with
zero-based `idx` plus optional per-point `position`, `number_format`,
`font_size`, `font_family`, `bold`, and `color`.

**Combo chart schema**: `combo` uses shared `categories` plus either `plots[]`
or typed `series[]`. Each plot supports `type: "column" | "line" | "area"`,
its own `series`, and optional `axis: "secondary"` for a right-side value axis.
Typed `series[]` accepts the same `type` and `axis` fields per series, and
adjacent compatible series are grouped into the same PowerPoint plot. Area
series may set `fill_opacity` / `fillOpacity` as a `0..1` SVG opacity value
when the SVG fallback uses a transparent area fill under an opaque line. A line plot with `area_fill: true`
is exported as a PowerPoint area chart under the hood; `fill_opacity` only sets
the fill style and does not trigger conversion by itself. Combo export layers
area plots below columns and lines while preserving the original series indices.
Line and area series may set `line_width` / `lineWidth` in SVG px units to
match fallback `stroke-width`.

**XY chart schema**: `scatter` and `bubble` use `series[].x` + `series[].y`; `bubble` also requires one `series[].size` / `series[].sizes` value per point. `series[].points` is also accepted as `[x, y]` / `[x, y, size]` tuples or `{x, y, size}` objects.

**Chart typography**: Metadata sizes use the same px-style unit as SVG text
(`1px = 0.75pt`). `style.font_family` and the role-specific
`title_font_size`, `subtitle_font_size`, `axis_font_size`,
`axis_title_font_size`, `legend_font_size`, and `note_font_size` fields are
required only when the native object must preserve typography that cannot be
inferred unambiguously from the visible fallback.

**Chart chrome metadata**: Text that is visually part of the chart must be in
metadata, not only in SVG fallback children; metadata MUST still match visible
fallback chrome. `title` becomes the native chart title on classic charts; it
is not an object name, so use `name` for semantic object naming. `subtitle`
becomes the second rich-text line of that classic chart title. `title`,
`subtitle`, and axis-title values may be strings or objects with `text`,
`font_size`, `font_family`, and `color` when the fallback uses local role
typography. `svg_quality_checker.py` rejects `title`, `subtitle`, or axis-title
metadata whose text is not visible inside the native marker's fallback. Direct
`--native-objects` export keeps the chart native but omits that inconsistent
chrome with a warning. chartEx keeps PowerPoint's empty `<cx:title>` and emits
the title / subtitle as companion editable text boxes until chartEx rich titles
are validated. Axis
titles are optional and explicit: use `axis_titles` with
`category`, `value`, `x`, `y`, or `secondary_value` keys, or the root aliases
`category_axis_title`, `value_axis_title`, `x_axis_title`, `y_axis_title`, and
`secondary_value_axis_title`; do not add semantic axis titles that are not
visible in the fallback. Set `show_value_axis_labels: false` when the fallback
keeps category labels but omits numeric value-axis tick labels, such as a radar
chart without radial coordinates. Native legends are metadata-controlled: use
`show_legend: true` and `legend_position` only when the fallback's legend is
meant to be replaced by PowerPoint's native legend.
Companion text such as `caption`, `source`, `note`, `notes`, `footnote`, and
`footnotes` is exported as editable PPT text boxes next to the native chart. A
companion entry may be a string or an object with `text`, `x`, `y`, `width`,
`height`, `font_size`, `color`, `align`, and `bold`; explicit bounds are
recommended so the native export matches the SVG fallback placement. Explicit
companion bounds are slide coordinates, not local coordinates inside a
transformed marker group. Use companion text for chart captions, source notes,
center labels, and freeform annotations; use `data_labels` for values that
belong to chart points.

**Chart color styling**: For classic native charts, `style.colors` sets series
colors. The exporter also writes explicit chart-area fill, plot-area fill,
axis line, gridline, and label text colors so PowerPoint does not substitute a
white/default-theme chart. If omitted, the exporter infers these colors from
the visible SVG fallback: the largest panel-like `<rect>` becomes the chart
background, fallback text supplies label color, and fallback strokes supply
axis/grid colors. Override any of them explicitly under `style` with
`chart_area_fill`, `plot_area_fill`, `text_color`, `axis_color`, and
`grid_color`; use `"none"` for transparent chart or plot area fill. Color
values may be `#RRGGBB`, `#RGB`, `rgb(...)` / `rgba(...)`, or common CSS names
such as `white`, `black`, and `gray`; the exporter normalizes them to 6-digit
OOXML RGB. Bar and column series also disable PowerPoint's negative-value
inversion so negative bars keep the same series fill instead of turning into
white/theme fill.

**PowerPoint chartEx schema**: `treemap`, `sunburst`, `histogram`, `pareto`,
`boxWhisker`, `waterfall`, and `funnel` use Office 2016+ chartEx parts. Use
these input shapes:

| Type | Required data |
|---|---|
| `treemap`, `sunburst` | `values` plus either `levels` (`levels[level][point]`) or path-style `categories` (`[["Region", "Group", "Leaf"], ...]`) |
| `treemap` display note | Top-level group labels default to `overlapping`; override with `parent_label_layout: "banner" \| "overlapping" \| "none"`. PowerPoint labels only the top level and leaves — intermediate levels group tiles spatially without labels (sunburst shows every ring). |
| `histogram` | `values` |
| `pareto`, `waterfall`, `funnel` | `categories` + `values`; `waterfall` also accepts `subtotals` / `subtotal_indices` point indexes |
| `boxWhisker` | `series[].values`; optional `series[].categories` per value |

> Note: chartEx files are valid PPTX and editable in PowerPoint; non-Microsoft
> renderers can display a limited subset.

**Stock chart schema**: `stock` uses numeric Excel date serials in
`categories` or `dates`, plus exactly four series in open / high / low / close
order. Use either `series` with four entries, or top-level `open`, `high`,
`low`, and `close` arrays.

**Deferred chart types**: Exploded pie / doughnut variants, `map`, `heatmap`,
`bullet`, and `gantt` are intentionally outside the current native-object
support boundary. The exporter fails fast for these types until each mapping is
implemented and validated one by one.

**Supported chart types**:

- `column`, `bar`: `clustered`, `stacked`, or `percentStacked` (`grouping`)
- `line`: `standard`, `stacked`, or `percentStacked` (`grouping`); `line` or `lineMarker` (`line_style`, default `line` / no markers)
- `area`: `standard`, `stacked`, or `percentStacked` (`grouping`)
- `pie`: exactly one series, per-slice colors
- `doughnut`: exactly one series, per-slice colors
- `pieOfPie`, `barOfPie`: exactly one series, per-slice colors
- `radar`, `radarMarkers`, `radarFilled`
- `scatter`: `marker` (default), `lineMarker`, `line`, `smoothMarker`, or `smooth` (`scatter_style`)
- `bubble`: x/y/size series
- `combo`: `column`, `line`, and `area` plots, optional secondary value axis
- `treemap`, `sunburst`: hierarchical chartEx charts
- `histogram`, `pareto`
- `boxWhisker`
- `waterfall`, `funnel`
- `stock`: open / high / low / close series

3D chart aliases (`3DColumn`, `3DBar`, `3DLine`, `3DArea`, `3DPie`, cone,
cylinder, pyramid variants, and `surface`) are unsupported.

Native legends are opt-in through `show_legend: true`; `legend_position`
defaults to `bottom` and accepts `top`, `left`, or `right`.

**Forbidden — native marker transforms**: Do not rotate, skew, or matrix-transform native table/chart marker groups. Translate / scale is accepted; complex transforms fail export because PowerPoint native table/chart frames do not preserve arbitrary SVG transforms.

### Baseline Layout Family Extraction

Native `baseline` export assigns layout families after every SVG page has been
converted. This package-only pass does not change SVG authoring or live preview.

| Root `data-pptx-page-role` | Output layout |
|---|---|
| `cover` | `Cover` |
| `toc` | `Agenda` |
| `section` | `Section` |
| `ending` | `Closing` |
| `content` | `Content` |

Marker-free legacy SVGs retain conservative filename-token fallback: explicit
cover / agenda / section / closing tokens select those families, and every
other page becomes `Content`. When a valid root marker exists, it is
authoritative even if the filename suggests another family.

Keep an existing `Cover` assignment when the Master chrome safety pass already
used it to hide promoted Master shapes from a minority page.

**Hard rule — no visual inference**: Keep every actual title, body, picture,
chart, table, and page-specific shape on the Slide. Baseline layouts do not
infer placeholders or promote visually similar content.

**Background rule**: Move a Slide `p:bg` to its family Layout only when every
slide in that family carries exactly the same explicit background. Otherwise,
keep each background on its Slide. Preserve whether each family shows or hides
the parent Master shape tree.

**Layout chrome rule**: After family assignment, move only the identical
leading prefix of explicitly marked chrome (`logo`, `footer`, `header`,
`watermark`, `chrome`) carried by every family member. Legacy id tokens are
consulted only when `data-pptx-role` is absent. Generated OOXML and
image relationships must match exactly, no animation may target the shapes,
and moving them behind Slide content must preserve z-order. Keep page numbers
and every non-identical object Slide-local.

### Explicit PPTX Master / Layout / Placeholder Metadata (Template Export)

**Trigger**: Deck/layout template routes set `spec_lock.md`
`pptx_structure.mode` to `template`; direct diagnostics may pass
`--pptx-structure template`. Both strict and adaptive template adherence use
this mode. Without either trigger, metadata stays visually dormant.

**Project lock**: In the standard project pipeline, template mode requires one
`pptx_layouts` row per page using
`P<NN>: <layout_key> | <PowerPoint layout name>`. The SVG root values MUST
match that row. Strict uses the selected template key/name. Adaptive may create
a new key/name while repeating the same Master contract. Reuse one layout key
only when pages share the same static Layout layer and placeholder contract;
different content is not a reason to create a new layout. Direct diagnostic
exports may pass the CLI flag without a spec lock.

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Sets the PowerPoint layout-picker name; defaults from the layout key |
| `data-pptx-layer="master"` | direct visual child | Moves one repeated static object/background into the slide master |
| `data-pptx-layer="layout"` | direct visual child | Moves one repeated static object/background into the selected layout |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | Writes a one-page override as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct visual child | Keeps actual content on the slide and maps it to a generated layout placeholder |
| `data-pptx-placeholder-bounds="x y width height"` | placeholder element | Overrides the reusable placeholder frame in SVG user units |
| `data-pptx-placeholder-idx="1"` | placeholder element | Retains an imported source layout placeholder index; optional for reconstructed layouts |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

**Hard rule — explicit only**: Template export never promotes visually similar
content by inference. Every SVG requires a root `data-pptx-layout`; every
master/layout/placeholder element requires a unique `id` and must be a direct
child of the root SVG.

**Layer order**: Author the SVG in PowerPoint paint order: Master background,
Layout background, optional Slide background, Master shapes, Layout shapes,
then slide-local content/placeholders. Backgrounds are a special inheritance
plane beneath every shape; this order keeps standalone SVG preview and
PowerPoint rendering aligned. The exporter rejects interleaved layers.

**Solid background ownership**: A direct full-canvas solid `<rect>` becomes a
real `p:bg`, not a selectable shape. Mark it `data-pptx-layer="master"` for the
deck-wide default, `data-pptx-layer="layout"` for a page-type override, or
`data-pptx-layer="slide"` for a one-slide override. An unmarked direct
full-canvas solid rect in the background plane is also treated as Slide scope. A
Layout background overrides the Master background; a Slide background
overrides both. Use the Master for a globally stable color and the Layout for
cover/section/content variants under the same design language. Gradients,
images, textures, transformed rects, and visible-stroke rects are not promoted
by this solid-background rule.

| Placeholder value | SVG element | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | direct `<text>` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | direct `<text>` | `dt`, `ftr`, `sldNum` |
| `picture` | direct `<image>` or imported crop `<svg>` | `pic` |
| `chart`, `table` | direct matching `data-pptx-native` marker group | `chart`, `tbl` |
| `object` | one direct text, image, or basic SVG shape | `obj` |
| `media` | direct `<image>` or imported crop `<svg>` | `media` |

`title` is normally type-matched without an index in reconstructed layouts; if
an imported source title explicitly has one, preserve that exact index. Every
indexed placeholder on one layout uses a unique non-negative index. Template
export writes the semantic type on both the Layout and Slide placeholder
(except `obj`, whose OOXML default is already
`obj`) so PowerPoint and `python-pptx` retain the same identity. A `date`
placeholder also enables the layout date flag and gets a
`datetimeFigureOut` field in the reusable Layout definition; the current
Slide keeps its authored date content.

**Placeholder prototype**: The first slide using a layout key supplies that
layout's placeholder formatting. `data-pptx-placeholder-bounds` supplies the
reusable frame; when omitted, the exporter uses the prototype object's native
DrawingML bounds. Repeat the same placeholder ids/types on every slide using
that layout. Actual slide content and local geometry may differ.

**Static structure consistency**: Repeat the same master element ids on every
slide and the same layout element ids on every slide sharing a layout. Their
generated OOXML must be identical within the affected master/layout group.
Static structure may carry shapes, text, or images; non-image/external
relationships are rejected. A full-canvas first rect/group may be marked as a
master or layout background.

**Native object placeholders**: `chart` / `table` placeholders require
`--native-objects`; fallback groups contain several shapes and cannot map to one
PowerPoint placeholder. `object` is the generic PowerPoint content slot and
must still resolve to one top-level DrawingML object. `media` currently binds
an authored image/crop to a native `media` placeholder; it does not synthesize
video or audio media from a decorative SVG group.

### Legacy Preserved Source Master / Layout Contract

**Trigger**: An existing project already ships `native_structure.json` and `source_template.pptx`, has strict template adherence, and sets `pptx_structure.mode: preserve`. Current `create-template` output does not emit this pair; retain this contract only for backward compatibility.

| Artifact | Authority |
|---|---|
| `source_template.pptx` | Original master/layout/theme/package parts |
| `native_structure.json` | Stable layout keys, picker names, parent masters, placeholder types/indices, source SHA-256 |
| `pptx_layouts` | Per-generated-page source layout selection |
| SVG metadata | Standalone preview layers and slide-content placeholder binding |

**Hard rule — source package wins**: Mark source master/layout visuals as direct `data-pptx-layer="master|layout"` preview children. Preserve export removes those generated copies and renders the original source parts. Unmarked content stays slide-local.

**Placeholder identity**: Keep actual content on the slide. Copy the source placeholder index into `data-pptx-placeholder-idx` when present; the exporter restores the source placeholder type/idx pair. Imported `subTitle`, `obj`, `media`, and `dt` placeholders retain distinct `subtitle`, `object`, `media`, and `date` semantic roles instead of collapsing into body/other. Multiple placeholders with the same semantic role require explicit indices.

**Multi-master boundary**: Preserve every source master already present in the package. Do not synthesize a new master merely for cover/section differences; rebuilt templates continue to prefer one master plus semantic layouts.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-layout="content"
     data-pptx-layout-name="Title and Content">
  <rect id="master-bg" data-pptx-layer="master"
        data-pptx-editable="false"
        width="1280" height="720" fill="#F8FAFC"/>
  <rect id="content-bg" data-pptx-layer="layout"
        data-pptx-editable="false"
        width="1280" height="720" fill="#FFFFFF"/>
  <g id="content-rule" data-pptx-layer="layout"
     data-pptx-editable="false">
    <line x1="48" y1="96" x2="1232" y2="96"
          stroke="#CBD5E1" stroke-width="2"/>
  </g>
  <text id="page-title" data-pptx-placeholder="title"
        data-pptx-placeholder-bounds="80 112 1120 72"
        x="80" y="158" font-size="40">Actual page title</text>
  <image id="hero-image" data-pptx-placeholder="picture"
         data-pptx-placeholder-bounds="680 210 480 320"
         x="680" y="210" width="480" height="320"
         href="../images/hero.png"/>
</svg>
```

---

## 8. Scope Boundary

Project structure, commands, quality-gate order, and export products are owned
by [`SKILL.md`](../SKILL.md). They are intentionally outside this SVG
authoring policy.
