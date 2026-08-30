> See [`svg-image-embedding.md`](./svg-image-embedding.md) for SVG image syntax and crop-policy enforcement.

# Image Layout Specification

Neutral geometry and review rules for every image placement. This file calculates the selected composition; it never chooses a resource, pattern, or an automatic left/right or top/bottom layout. Whenever an image will be placed, select its region from the current page composition first, then apply the matching single-item, adjacent, overlay, or multi-item calculation.

---

## 1. Ownership and Inputs

Default Strategist owns resource choice, semantic role, crop boundary, and the preferred image/content or image/shape relationship; Image_Generator owns composition inside each generated bitmap for its planned container; Default Executor owns final SVG regions and geometry and may adapt the preferred relationship while preserving binding resource, content, and crop constraints; Quick's main agent holds all of these in one context. This specification and [`image-layout-patterns.md`](./image-layout-patterns.md) are the always-read geometry and composition vocabulary; [`svg-image-embedding.md`](./svg-image-embedding.md) owns embedding; [`svg-effects.md`](./svg-effects.md) and [`native-shape-authoring.md`](./native-shape-authoring.md) load on their executor-base triggers — effects beyond the everyday block, a contour beyond basic primitives, or Boolean geometry — so apply them when a construction reaches that far.

### 1.1 Geometry notation

`(x0, y0, W, H)` current selected region; `(ws, hs)` measured source size; `R = ws / hs` source aspect; `Q = W / H` region aspect; `g`, `gx`, `gy` gaps between regions, columns, rows; `ax`, `ay` anchor fractions in `[0,1]`. All dimensions are finite and positive; derive `R` from current measured source data, never a requested or previously planned size.

---

## 2. Aspect-Ratio Placement

### 2.1 Contain

Keeps the complete source visible inside `(W,H)`; centered contain uses `ax = ay = 0.5` and normally maps to a legal `meet` anchor.

```text
if R >= Q: w = W; h = W / R   else: h = H; w = H × R
x = x0 + ax × (W - w);  y = y0 + ay × (H - h)
```

### 2.2 Fill

Covers `(W,H)` without distortion and crops overflow; centered fill uses `ax = ay = 0.5` and normally maps to a legal `slice` anchor. Use fill only when the active crop boundary permits the computed loss and the anchor protects the declared focal content.

```text
if R >= Q: h = H; w = H × R   else: w = W; h = W / R
overflow_x = w - W;  overflow_y = h - H
x = x0 - ax × overflow_x;  y = y0 - ay × overflow_y
```

### 2.3 Mode selection

**Reference — narrative intent before geometry**: decide whether the image is the page (hero / full-bleed: image fills the canvas or dominant zone, title floats over a gradient or scrim — covers, dividers, breathing pages), a backdrop (atmosphere: low-contrast image behind text), a coequal block (side-by-side: image and text read together — most content pages), or an accent (small image beside related text, no ratio matching); do not default every image page to side-by-side. For side-by-side, the source ratio shapes the item inside its region (§2–§3), not the page split; on portrait canvases (Xiaohongshu, Story) side columns become narrow, so stacked regions usually serve better.

Complete source, evidence, or edge content → contain; region coverage with a focal-safe crop → fill; complete source plus a detail view → one contain placement plus a separately justified crop; irregular or repeated source windows → the selected region math first, then the owning crop/shape reference.

---

## 3. Single Image

Apply §2 to the selected region; the region comes from the page hierarchy and the source ratio determines the item geometry inside it, not the page structure. For an item adjacent to another region, divide only the available region by positive visual weights `q_item` and `q_other` — no fixed share is implied, and either region may be placed first:

```text
horizontal: available = W - g;  item_width  = available × q_item / (q_item + q_other);  other_width  = available - item_width   (both use height H)
vertical:   available = H - g;  item_height = available × q_item / (q_item + q_other);  other_height = available - item_height  (both use width W)
```

**Overlay and inset**: an overlay keeps the image region and overlay region independently measurable; an inset selects a child region `(xi, yi, Wi, Hi)` inside the current region and reapplies §2 with the same source ratio. Size either from the actual hierarchy, copy, focal content, and required separation, never an assumed percentage.

---

## 4. Multiple Images

### 4.1 Equal grid

For `c` columns and `r` rows — use equal cells when peer comparison is the message, applying contain or fill independently per cell:

```text
cell_width = (W - (c - 1) × gx) / c;  cell_height = (H - (r - 1) × gy) / r
cell_x(col) = x0 + col × (cell_width + gx);  cell_y(row) = y0 + row × (cell_height + gy)
```

### 4.2 Weighted tracks

For column weights `u[1…c]` and row weights `v[1…r]` — use when one item is primary; a spanning item receives the sum of its tracks plus the internal gaps it crosses:

```text
column_width[j] = (W - (c - 1) × gx) × u[j] / sum(u);  row_height[k] = (H - (r - 1) × gy) × v[k] / sum(v)
```

### 4.3 Free multi-item composition

**Mandatory**: for montage, arc, overlap, or another non-grid arrangement, give every carrier a finite center `p[i] = (cx[i], cy[i])` and positive size `(w[i], h[i])` (optionally `s[i] × (w0, h0)` for a shared size rhythm), give every intended overlap an unambiguous front item through stacking rank `z[i]` (`area(V[i] ∩ V[j]) > 0` where `V[i]` is the visible carrier after its clip and any parent contour `P`), and verify the visible union against `(W,H)`. `P` must visibly control at least one structural role (outer silhouette, shared seam, reveal, or attachment path); otherwise use the region boundary and omit it.

**Default — shared direction (may override when deliberate disorder serves the communication job)**: select one direction generator and derive related carriers from shared geometry; an override still declares a bounded placement/angle rule so disorder is authored. For a straight direction `θ`: `d = (cos θ, sin θ)`, `n = (-sin θ, cos θ)`, `p[i] = p0 + t[i] × d + e[i] × n`, with `t[i]`, transverse `e[i]`, and optional `s[i]` as explicit sequences that reuse a progression when rhythm is intended.

| Generator | Executable rule |
|---|---|
| `vector` | Straight-frame equation with ordered `t[i+1] = t[i] + advance[i]`, `advance[i] > 0`; overlap is controlled through `advance[i]`, never an accidental negative gap |
| `shared-baseline` | Baseline `B(t) = b + t × d`; with `r[i]` the carrier's half-extent along `n`, `p[i] = B(t[i]) + r[i] × n` keeps one edge on the baseline while sizes vary |
| `curve-spine` | Ordered `u[i]` on `C(u)` with `‖C'(u[i])‖ > 0`; `d[i] = normalize(C'(u[i]))`, `n[i] = (-d[i].y, d[i].x)`, `p[i] = C(u[i]) + e[i] × n[i]`; at a zero derivative use the secant between nearest distinct samples or another generator |
| `panel` | One convex quadrilateral `A,B,C,D` in consistent winding with `F(u,v) = (1-u)(1-v)A + u(1-v)B + uvC + (1-u)vD`; split monotone `u`/`v` intervals, each cell using its four `F` corners |

**Reference — angle mechanisms**: clip-shape angle (bitmap upright, only the carrier contour or clip angled); parent-group rotation (build the arrangement, then rotate carriers, frames, and labels together around one pivot); tangent rotation (on `curve-spine`, rotate item `i` around `p[i]` by `atan2(d[i].y, d[i].x)`). **Forbidden — unsupported deformation**: no shear, skew, or true perspective; a `panel` is a set of 2D quadrilateral clips/crops, never a warped image plane.

---

## 5. Composition Checks

| Check | Required response |
|---|---|
| Computed width or height non-positive | Re-select the regions or reduce gaps |
| Contain leaves unusable residual space | Recompose the surrounding regions; never stretch |
| Fill removes focal or required content | Change anchor, enlarge the region, or use contain |
| Adjacent content region cannot carry its material | Reweight or change the relationship |
| Equal cells imply an equality the content lacks | Weighted tracks or free composition |
| Peer images use inconsistent scale without meaning | Normalize regions or make the hierarchy explicit |
| A free carrier lacks a center, size, or stacking order for an overlap | Supply it before drawing |
| Items meant as one system lack both a shared direction and a deliberate-disorder rule | Derive them from one vector, baseline, curve, panel, or bounded override |
| Per-item angles vary without a shared direction or disorder rule | One parent-group angle, shared clip direction, curve tangents, or a bounded angle rhythm |
| The parent contour affects no silhouette, seam, reveal, or attachment | Remove it or reconstruct the carriers from it |
| A panel depends on shear, skew, or perspective | Replace with 2D quadrilateral carriers and focal-safe crops |
| Gaps, alignments, or overlaps drift without purpose | Recalculate from the shared region and gap values |

The final geometry expresses the active page hierarchy, preserves the selected resource relationships, and stays valid under the conditionally loaded technical contracts.
