# Native Diagrams — Selection & Placement Reference

> Lazy-loaded reference. Load **only** when `spec_lock.md page_diagrams` has at
> least one entry (Strategist matched a page to a native diagram). If that section
> is empty/absent, this file is never read. Peer to [`image-generator.md`](./image-generator.md)
> and the chart catalog — same "scan an index, match by content shape" pattern.

A **native diagram** is a pre-designed, fully-editable DrawingML figure lifted
verbatim from a real deck and stored in `templates/native_diagrams/`. Unlike a
`templates/charts/` SVG (which Executor *redraws* from scratch using the template
as reference), a native diagram is **spliced in as-is** via a placeholder and only
recolored — so an elaborate, polished figure arrives pixel-faithful and still
native-editable, at near-zero authoring cost.

---

## 1. When a native diagram is the right vehicle (vs the alternatives)

For any page whose content is a *structural relationship* (hierarchy / flow /
convergence / comparison / composition / cycle), there are four vehicles. Pick by
content-shape **and** the deck's visual ambition (set once in §d Style Objective):

| Vehicle | Use when |
|---|---|
| Native diagram | The relationship maps to a polished, dimensional figure. Spliced in as-is + recolored to the deck palette — any deck can use it once recolored; keep the treatment consistent across the deck's structural pages. |
| `charts/` SVG template | The deck is flat / minimalist, OR the figure needs structural surgery (different slot count, custom axes) the native diagram can't flex to. |
| Hand-drawn SVG | No catalog entry fits; the page wants a bespoke layout. |
| AI image (`image-generator`) | The page wants atmosphere / a scene / a hero, not an editable structural figure. |

> **Visual-cohesion guardrail**: Native diagrams carry a deliberate **3D /
> dimensional idiom** — recolor adapts their *color* to the deck palette, but the
> glossy/volumetric *treatment* stays. There is **no hard style gate** (recolored,
> they drop into any deck); it is a soft cohesion call — once you use them, use them
> **consistently** across the deck's structural pages rather than scattering a single
> glossy figure into otherwise-flat pages. Strategist sets this direction once, from
> §d Style Objective, before matching pages.

---

## 2. Selecting a specific diagram

Source of truth: [`templates/native_diagrams/diagrams_index.json`](../templates/native_diagrams/diagrams_index.json),
shape `{ meta, diagrams }`. Scan the `diagrams.*.pick` lines in one pass (same as
the chart catalog) and match each candidate page by:

1. **`scenario`** (content-first — start here) — the business content the figure
   serves: *capability map / maturity model / platform or tech stack / roadmap /
   two-sided platform / module portfolio …*. A PPT expert thinks in scenarios first
   ("I'm making a capability-hub page"), then narrows by structure.
2. **`type` / `use`** — the underlying relationship: `framework` (hub-spoke) /
   `funnel` / `pyramid` / `layered-platform` / `isometric-stack` / `matrix` /
   `cycle` / `list-row` / `timeline` / `bowtie` (hourglass converge-diverge).
3. **`slots` / `slot_of`** — item count **and what the count means**: `slot_of`
   encodes the parallel grain — `columns` (N-栏 comparison) / `tiers` / `layers` /
   `spokes` / `cells`. Match the page's item count to the range.
4. **`holds`** — does the content per item fit? `short-label` figures break if you
   have a sentence per node; use a `label+desc` figure for richer items.
5. **`footprint`** — the figure's natural region shape, for *where* it goes:
   `wide-band` (a horizontal strip — needs full width, not a narrow column) /
   `tall-center` (pyramid/funnel/tower — fits a half-width column) /
   `centered-compact` (a hub concentrated mid-slide — flexible region) /
   `full-bleed` (panorama/architecture — full-slide only). Match it to the slide
   region you've reserved.
6. **`density`** — how small it can shrink and stay legible: `low` works as an
   in-page element; `high` needs most of the slide (see §3).
7. **`text_load`** — overall copy the figure carries: `light` (labels only) /
   `medium` / `heavy` (text in every cell). Match to page rhythm — a `breathing`
   page wants `light`; a `dense` page can take `heavy`.
8. **`motif`** — node vocabulary (`sphere` / `card` / `cube` / `ring` / `tower` /
   `pyramid` / `mixed`). Prefer one that echoes the deck's other elements (a
   card-based deck pairs with a `card`/`cube` motif, not glossy spheres).
9. **`conf`** — `refined` = hand-verified distinguishing entry (trust it);
   `high` = studied; `approx` = contact-sheet read — sanity-check the thumbnail in
   `gallery.html` before relying on an `approx` pick.

> **Distinguishing within a type** (e.g. choosing among many `framework`s): rely on
> `subform` + `distinct` + the differentiated `pick` (refined entries cross-reference
> siblings — "Skip if radial hub (031)"). `type` alone does not discriminate.

Skip `selectable: false` entries (cover / notice / table). One native diagram per
page (it is the page's primary figure).

---

## 3. Placing it (Executor) — the `data-native-diagram` placeholder

Native diagrams are resolved at SVG→PPTX conversion time (peer to `<use data-icon>`
and `<image>`). Executor writes a placeholder rect; the converter splices the
component in, scaled to the rect.

> Resolver: [`native_diagram_resolver.py`](../scripts/svg_to_pptx/native_diagram_resolver.py).

```xml
<rect data-native-diagram="<key>"
      x=".." y=".." width=".." height=".." fill="none"/>
```

- **`data-native-diagram`** = the chosen `<key>` from `page_diagrams`.
- **Region sizing by `density`**: `high` → near-full-slide (respect canvas margins);
  `medium` → ≥ half-slide; `low` → may be a smaller region. The whole figure
  (including its text) scales to the rect — so do **not** shrink a text-bearing
  diagram into a tiny region or its labels become illegible. When in doubt, give it
  the page.
- The rect itself does not render (it's replaced); keep `fill="none"` (a dashed
  light stroke is fine as a preview marker). The figure only appears in the PPTX,
  not in the SVG preview.

---

## 4. Limits

- **Charts not lifted** — entries are diagram/figure structures only; data charts
  (`graphicFrame`) stay with `templates/charts/`.
- **No structural surgery** — you cannot add a tier or remove a spoke; the figure is
  frozen. If the content needs a different slot count, pick a different `key` or use
  a `charts/` template.
- **Composed assets** (`type: composite`) are pre-combined figures — use as-is.
