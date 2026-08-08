> Default Generate also loads [`executor-base.md`](./executor-base.md); a selected chart-family SVG is adapted through [`executor-visualization.md`](./executor-visualization.md), while independent native readiness and metadata remain exclusively in [`native-data-interface.md`](./native-data-interface.md).

# Executor Chart Branch

Conditional Executor authority for value-driven SVG geometry, plot-area markers, and the [`verify-charts`](../workflows/stages/verify-charts.md) handoff.

**Trigger**: load whenever source values determine visible geometry, including bar length/height, point position, arc angle, polygon vertex, connector or flow width/path, bubble center/radius, duration position, area, or another quantitative visual variable. Mini charts, sparklines, insets, and small multiples count even without a catalog reference.

**Boundary**:

| Information model | Route |
|---|---|
| Values, dates, or durations determine geometry or another visual variable | This branch |
| Qualitative order, grouping, containment, causality, or named zones determine topology | [`executor-structure.md`](./executor-structure.md) |
| A row header and column header jointly address each body fact | [`executor-table.md`](./executor-table.md) |

---

## 1. Value-driven Geometry

**Hard rule — data owns the marks**: derive every quantitative mark from the authoritative values and one explicit scale/encoding. Do not eyeball positions, preserve sample values from a catalog preview, or alter data to improve composition.

Construct the chart in this order:

1. Resolve the data domain, categories, units, baseline, scale, and any radius/color/bin mapping.
2. Establish the plot frame, axes/grid or radial frame, and legend needed to decode those mappings.
3. Calculate marks from the values, including cumulative, derived, or hierarchical geometry where the chosen chart requires it.
4. Add data labels, axis/category labels, annotations, units, source notes, and visible exceptions from the active page contract.
5. Apply project typography, palette, effects, and container treatment without changing the encoding.

**Per-object completeness**: preserve every authoritative series, category, point, label, unit, qualifier, source, and scale cue needed to read the chart. When the source cannot determine a required scale or derived value, return the ambiguity upstream in Default or resolve it from explicit source facts in Quick; never fabricate it at draw time.

**Hard rule — schedule geometry**: A schedule is a Gantt chart when dates or
durations determine each task bar's `x` and `width`, even if the source was a
PowerPoint table object. A qualitative stage × lane placement without that
mapping belongs to [`executor-structure.md`](./executor-structure.md).

**Selected reference**: when the page has a `chart/<key>` primary reference, [`executor-visualization.md`](./executor-visualization.md) owns its resolution and flexible adaptation. This branch still owns the actual value-to-geometry calculation. A chart authored from scratch follows the same geometry contract without loading a catalog SVG.

**Incidental microvisual**: draw a small value-driven trend or indicator accurately. It enters §2 and the verification handoff only when Default §IX or the Quick active-context decision promotes it to a coordinate-verified data object; do not infer that promotion from its appearance after drawing.

---

## 2. Plot-area Marker

### 2.1 Chart Plot-Area Marker (Mandatory per verified chart object)

> [`verify-charts`](../workflows/stages/verify-charts.md) enumerates Default pages from Design Spec §IX and Quick pages from the still-active authoring decisions. A missing marker invokes that stage's declared fallback and adds avoidable derivation work.

**Hard rule — object-scoped marker**: every Default chart object given a
semantic key in §IX `Visualization`, and every Quick chart object promoted for
coordinate verification, has one page-local `kebab-case` object key. Wrap that
object in `<g id="<object-key>">`; put exactly one marker inside its plot-area
group after the axes and before the first data mark. Use
`id="<object-key>-chartArea"` so several charts can coexist without duplicate
IDs. New pages prefix the marker payload with `object=<object-key> |`. A legacy
unscoped marker and `<g id="chartArea">` are accepted only when the page has
exactly one verified chart object.

**Rectangular plot area**:

```xml
<g id="revenue-trend">
  <g id="revenue-trend-chartArea">
    <!-- axes -->
    <!-- chart-plot-area: object=revenue-trend | x_min,y_min,x_max,y_max -->
    <!-- data marks -->
  </g>
</g>
```

**Radial plot area**:

```xml
<!-- chart-plot-area: object=share-pie | pie | center: cx,cy | radius: r -->
<!-- chart-plot-area: object=share-donut | donut | center: cx,cy | outer-radius: r1 | inner-radius: r2 -->
<!-- chart-plot-area: object=capability-radar | radar | center: cx,cy | radius: r -->
```

| Value | Derivation |
|---|---|
| `x_min` | X coordinate of the Y-axis line or leftmost data boundary |
| `y_min` | Y coordinate of the topmost grid line or data boundary |
| `x_max` | X coordinate of the rightmost axis endpoint or data boundary |
| `y_max` | Y coordinate of the X-axis baseline or bottom data boundary |
| `cx, cy` | Absolute center after accounting for containing translate transforms |
| `r`, `r1`, `r2` | Visible outer/inner radii used by the authored radial geometry |

Calculator-supported SVGs in `templates/charts/` carry the same comment, and
single-object previews may retain the legacy unscoped payload and
`id="chartArea"`. A qualitative structure or cell-grid table does not gain a
marker merely because it contains numbers.

### 2.2 Authoring-time Check

After writing each page containing verified charts, confirm marker count and
object ownership before continuing:

```bash
rg -n "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

The number of markers must equal the number of promoted chart objects, and each
marker must sit under its matching object wrapper. One marker somewhere on a
multi-chart page is insufficient.

Technical SVG/PPT constraints remain in [`shared-standards-core.md`](./shared-standards-core.md).

---

## 3. Verification Handoff

Coordinate calibration is a conditional post-generation stage, not part of the page-authoring loop. After all SVG pages exist, run [`verify-charts`](../workflows/stages/verify-charts.md) whenever the active profile declares at least one page with value-driven chart geometry.

| Active profile | Verification page list |
|---|---|
| Default Generate | Design Spec §IX, with the stage's explicit legacy §VII fallback |
| Quick Generate | Still-active page decisions cross-checked one-for-one against plot-area markers |

Do not run `svg_position_calculator.py` during the initial draft. The stage calibrates completed SVG geometry against the declared plot area, handles direct/decomposable/formula/manual modes, repairs genuine coordinate mismatches, and then returns to the active profile's checker order.
