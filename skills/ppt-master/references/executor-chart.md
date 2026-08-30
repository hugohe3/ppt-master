> Default Generate also loads [`executor-base.md`](./executor-base.md); a selected chart-family SVG is adapted through [`executor-visualization.md`](./executor-visualization.md), while native readiness and metadata remain exclusively in [`native-data-interface.md`](./native-data-interface.md).

# Executor Chart Branch

Conditional Executor authority for value-driven SVG geometry, plot-area markers, and the [`verify-charts`](../workflows/stages/verify-charts.md) handoff.

**Trigger**: source values determine visible geometry — bar length/height, point position, arc angle, polygon vertex, connector or flow width/path, bubble center/radius, duration position, area, or another quantitative visual variable. Mini charts, sparklines, insets, and small multiples count even without a catalog reference.

| Information model | Route |
|---|---|
| Values, dates, or durations determine geometry or another visual variable | This branch |
| Qualitative order, grouping, containment, causality, or named zones determine topology | [`executor-structure.md`](./executor-structure.md) |
| A row header and column header jointly address each body fact | [`executor-table.md`](./executor-table.md) |

---

## 1. Value-driven Geometry

**Hard rule — data owns the marks**: derive every quantitative mark from the authoritative values and one explicit scale/encoding. Do not eyeball positions, preserve sample values from a catalog preview, or alter data to improve composition. A schedule is a Gantt chart when dates or durations determine each task bar's `x` and `width`, even if the source was a PowerPoint table; a qualitative stage × lane placement belongs to `executor-structure.md`.

Construct in this order: (1) resolve data domain, categories, units, baseline, scale, and any radius/color/bin mapping; (2) establish the plot frame, axes/grid or radial frame, and legend needed to decode them; (3) calculate marks from the values, including cumulative, derived, or hierarchical geometry; (4) add data labels, axis/category labels, annotations, units, source notes, and visible exceptions from the page contract; (5) apply project typography, palette, effects, and container treatment without changing the encoding.

**Perceptual reading**: choose the least ambiguous presentation of the same data. Preserve source or semantic order when it carries meaning; otherwise sort for the page's comparison task. Prefer direct series labels when legible; keep legends, grid lines, and ticks only when they materially reduce lookup effort. Comparable panels share domain, scale, and category order unless a disclosed difference is the message. Magnitude bars and columns start from zero; interval marks keep their authoritative domain; any non-zero baseline or axis break is explicit and never exaggerates. A dual-axis chart is valid only when both series share the exact time/category domain and units and identities stay unambiguous; otherwise separate the views.

**Reference — chart color and annotation conventions**: a monochromatic depth scheme reads cleaner than rainbow — the primary series in the full theme color, a comparison series in the same hue at about 60% alpha, baselines as a gray dashed line, the accent color only on the key data points; positive / warning / negative trends use the deck's green / yellow / red polarity roles. Place direct data labels at bar ends or beside points instead of a legend where they stay legible; annotate genuine inflection points in words ("policy change", "product launch"); mark an industry average or target as a gray dashed comparison baseline; keep units and precision consistent within one chart; add a muted source note where attribution or provenance matters.

**Per-object completeness**: preserve every authoritative series, category, point, label, unit, qualifier, source, and scale cue. For a `<object-key>=yes` chart, the JSON mirrors the drawn fallback item by item in the same edit — legend labels verbatim, point-level exception colors as `point_colors`, the axis scale, `plot_area` from the plot-area marker, visible data labels or summary figures as `data_labels` or companion text, actual label/axis/grid colors (omit `text_color` and siblings rather than guess). When the source cannot determine a required scale or derived value, return the ambiguity upstream in Default or resolve it from explicit source facts in Quick; never fabricate at draw time.

**Selected reference**: with a `chart/<key>` primary reference, [`executor-visualization.md`](./executor-visualization.md) owns resolution and adaptation; this branch still owns the value-to-geometry calculation. A chart authored from scratch follows the same contract. An incidental microvisual (small trend or indicator) is drawn accurately but enters §2 and verification only when Default §IX or the Quick active-context decision promotes it to a coordinate-verified object.

---

## 2. Plot-area Marker

### 2.1 Chart Plot-Area Marker (Mandatory per verified chart object)

**Hard rule — object-scoped marker**: every Default chart object keyed in §IX `Visualization`, and every Quick chart object promoted for coordinate verification, has one page-local `kebab-case` object key. Wrap it in `<g id="<object-key>">`; place exactly one marker inside its plot-area group `id="<object-key>-chartArea"`, after the axes and before the first data mark, with payload prefix `object=<object-key> |`. A legacy unscoped marker with `<g id="chartArea">` is accepted only when the page has exactly one verified chart object.

```xml
<g id="revenue-trend">
  <g id="revenue-trend-chartArea">
    <!-- axes -->
    <!-- chart-plot-area: object=revenue-trend | x_min,y_min,x_max,y_max -->
    <!-- data marks -->
  </g>
</g>
```

```xml
<!-- chart-plot-area: object=share-pie | pie | center: cx,cy | radius: r -->
<!-- chart-plot-area: object=share-donut | donut | center: cx,cy | outer-radius: r1 | inner-radius: r2 -->
<!-- chart-plot-area: object=capability-radar | radar | center: cx,cy | radius: r -->
```

| Value | Derivation |
|---|---|
| `x_min` / `x_max` | X of the Y-axis line or leftmost data boundary / rightmost axis endpoint or data boundary |
| `y_min` / `y_max` | Y of the topmost grid line or data boundary / X-axis baseline or bottom data boundary |
| `cx, cy` | Absolute center after containing translate transforms |
| `r`, `r1`, `r2` | Visible outer/inner radii of the authored radial geometry |

Calculator-supported SVGs in `templates/charts/` carry the same comment. A qualitative structure or cell-grid table gains no marker merely because it contains numbers. A missing marker invokes the verify stage's declared fallback and adds avoidable derivation work.

### 2.2 Authoring-time Check

After each page containing verified charts: `rg -n "chart-plot-area" <project_path>/svg_output/<current_page>.svg` — marker count equals promoted chart objects and each marker sits under its object wrapper.

**Native layout handoff**: for a native-ready classic chart whose authored plot rectangle must stay fixed, copy that absolute rectangle into metadata `plot_area`; omit it for PowerPoint automatic layout. The comment alone does not affect export; the closed schema is [`native-data-interface.md`](./native-data-interface.md) §2.

---

## 3. Verification Handoff

Coordinate calibration is a conditional post-generation stage. After all SVG pages exist, run [`verify-charts`](../workflows/stages/verify-charts.md) whenever the active profile declares at least one page with value-driven chart geometry: Default enumerates Design Spec §IX (with the stage's legacy §VII fallback); Quick cross-checks still-active page decisions one-for-one against plot-area markers. Do not run `svg_position_calculator.py` during the initial draft; the stage calibrates completed geometry against the declared plot area, repairs genuine mismatches, and returns to the profile's checker order.
