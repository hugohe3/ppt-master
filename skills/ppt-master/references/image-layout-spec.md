> See [`svg-image-embedding.md`](./svg-image-embedding.md) for SVG image syntax and crop-policy enforcement.

# Image Layout Specification

Neutral geometry and review rules for every image or rendered-formula placement. This file calculates the selected composition; it never chooses a resource, pattern, or automatic left/right or top/bottom layout.

**When to run**: whenever an image or rendered formula will be placed. Use the current page composition to select its region first, then apply the relevant single-item, adjacent, overlay, or multi-item calculation below.

---

## 1. Ownership and Inputs

| Role | Owns |
|---|---|
| Default Strategist | Resource choice, semantic role, crop boundary, and preferred image/content or image/shape relationship |
| Image_Generator | Composition inside each generated bitmap for its planned container |
| Default Executor | Final SVG regions and geometry; may adapt the preferred relationship while preserving binding resource, content, and crop constraints |
| Quick Generate main agent | The planning and realization decisions above in one active context |

This specification and [`image-layout-patterns.md`](./image-layout-patterns.md) are the always-read geometry and composition vocabulary; [`svg-image-embedding.md`](./svg-image-embedding.md) owns embedding. Default and Quick SVG authoring also load [`svg-effects.md`](./svg-effects.md) and [`native-shape-authoring.md`](./native-shape-authoring.md) before realization, so apply their contracts directly when a selected construction needs effects, preset geometry, or Boolean geometry. Other routes follow their own documented load triggers.

### 1.1 Geometry notation

| Symbol | Meaning |
|---|---|
| `(x0, y0, W, H)` | Current selected page region |
| `(ws, hs)` | Measured source width and height |
| `R = ws / hs` | Source aspect ratio |
| `Q = W / H` | Selected-region aspect ratio |
| `g`, `gx`, `gy` | Gap between adjacent regions, columns, or rows |
| `ax`, `ay` | Horizontal and vertical anchor fractions in `[0,1]` |

All dimensions must be finite and positive. Derive `R` from current measured source data rather than a requested or previously planned size.

---

## 2. Aspect-Ratio Placement

### 2.1 Contain

Contain keeps the complete source visible inside `(W,H)`:

```text
if R >= Q:
    w = W
    h = W / R
else:
    h = H
    w = H × R

x = x0 + ax × (W - w)
y = y0 + ay × (H - h)
```

Centered contain uses `ax = ay = 0.5`. SVG realization normally maps this to a legal `meet` anchor.

### 2.2 Fill

Fill covers `(W,H)` without distortion and crops overflow:

```text
if R >= Q:
    h = H
    w = H × R
else:
    w = W
    h = W / R

overflow_x = w - W
overflow_y = h - H
x = x0 - ax × overflow_x
y = y0 - ay × overflow_y
```

Centered fill uses `ax = ay = 0.5`. SVG realization normally maps this to a legal `slice` anchor. Use fill only when the active crop boundary permits the computed loss and the anchor protects the declared focal content.

### 2.3 Mode selection

| Need | Geometry |
|---|---|
| Complete source, formula, evidence, or edge content | Contain |
| Region coverage with a focal-safe crop | Fill |
| Complete source plus a detail view | One contain placement plus a separately justified crop |
| Irregular or repeated source windows | Apply the selected region math first, then load the owning crop/shape reference |

---

## 3. Single Image or Formula

Place a standalone item by applying §2 to its selected region. The region itself comes from the page hierarchy; source ratio determines the item geometry inside it, not the page structure.

For an item adjacent to another region, divide only the available selected region. Let `q_item` and `q_other` be positive visual weights for the image/formula and the other content.

### 3.1 Horizontal adjacency

```text
available = W - g
item_width  = available × q_item / (q_item + q_other)
other_width = available - item_width
```

Both regions use height `H`. Place either region first according to the selected composition; no fixed share is implied.

### 3.2 Vertical adjacency

```text
available = H - g
item_height  = available × q_item / (q_item + q_other)
other_height = available - item_height
```

Both regions use width `W`. Place either region first according to the selected composition.

### 3.3 Overlay and inset

An overlay keeps the image region and overlay region independently measurable. An inset selects a child region `(xi, yi, Wi, Hi)` inside the current region, then reapplies §2 using the same source ratio. Do not derive either region from an assumed percentage; size it from the actual hierarchy, copy, focal content, and required separation.

---

## 4. Multiple Images

### 4.1 Equal grid

For `c` columns and `r` rows:

```text
cell_width  = (W - (c - 1) × gx) / c
cell_height = (H - (r - 1) × gy) / r

cell_x(col) = x0 + col × (cell_width + gx)
cell_y(row) = y0 + row × (cell_height + gy)
```

Use equal cells when peer comparison is the message. Apply contain or fill independently to each source within its cell.

### 4.2 Weighted tracks

For column weights `u[1]…u[c]` and row weights `v[1]…v[r]`:

```text
available_width  = W - (c - 1) × gx
available_height = H - (r - 1) × gy

column_width[j] = available_width  × u[j] / sum(u)
row_height[k]   = available_height × v[k] / sum(v)
```

Use weighted tracks when one item is primary. A spanning item receives the sum of its tracks plus the internal gaps it crosses.

### 4.3 Free multi-item composition

For montage, arc, overlap, or another non-grid arrangement, assign one explicit region to every item and verify the union against `(W,H)`. Reuse one gap/rhythm system where separation is intended; overlap is explicit geometry, not a negative-gap accident.

---

## 5. Rendered Formula Geometry

Treat a rendered formula as an aspect-ratio source and apply contain within its selected mathematical region. Centering is the default geometric anchor; align to a nearby baseline or relation only when the page composition defines that relationship.

For `n` vertically stacked formula regions with equal lanes:

```text
lane_height = (H - (n - 1) × g) / n
lane_y[i]   = y0 + i × (lane_height + g)
```

Contain each formula independently in its lane. When formulas are visual peers, a common effective scale may improve comparison; otherwise let their selected regions reflect their semantic weight and source ratios.

---

## 6. Composition Checks

| Check | Required response |
|---|---|
| Computed width or height is non-positive | Re-select the page regions or reduce gaps |
| Contain leaves unusable residual space | Recompose the surrounding regions; do not stretch the source |
| Fill removes focal or required content | Change anchor, enlarge the region, or use contain |
| Adjacent text/content region cannot carry its material | Reweight or change the selected relationship |
| Equal cells imply equality that the content does not have | Use weighted tracks or a free composition |
| Peer images use inconsistent visual scale without meaning | Normalize their regions or make the hierarchy explicit |
| Formula symbols become unreadable at the intended viewing size | Enlarge its region or restructure the page |
| Gaps, alignments, or overlaps drift without purpose | Recalculate from the shared region and gap values |

The final geometry must express the active page hierarchy, preserve the selected resource relationships, and remain valid under the conditionally loaded technical contracts.
