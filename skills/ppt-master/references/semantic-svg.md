# Minimal Semantic SVG Markers

Rendering-neutral compiler hints, used only where ordinary SVG cannot express PowerPoint Master, Layout, placeholder, native-object, or package behavior. The completed SVG remains the full visible page: removing the metadata must not change browser rendering, and metadata never copies visible text, geometry, style, or asset values.

## 1. Boundary

| Marker | Placement | Purpose |
|---|---|---|
| `data-pptx-page-role` | Root `<svg>` on flat pages only | Classify a free-design/brand-only page as `cover`, `toc`, `section`, `content`, or `ending` |
| `data-pptx-master` / `-master-name`, `data-pptx-layout` / `-layout-name` | Root `<svg>` on structured pages | Bind the page to one named Master and one Layout under it |
| `data-pptx-layer="master\|layout"` | Direct atomic child of root | Promote one fixed visual object to the Master or Layout |
| `data-pptx-placeholder` | Direct child `<g id>` of root | Declare one reusable Layout slot whose visible content stays Slide-local |
| `data-pptx-role` | Structural page-frame element | Package, page-number, or animation behavior no specialized metadata already expresses |

**Hard rule — route boundary**: free-design, brand-only, and `template_reuse_scope: style` pages use `pptx_structure.mode: flat`, declare one root `data-pptx-page-role`, and omit every Master/Layout/layer/placeholder marker. Only Default `template_reuse_scope: mirror|layout` pages or Quick pages authoring an installed Layout/Deck owner's structure declare Master and Layout before drawing and omit `data-pptx-page-role`; the exporter compiles that contract and never selects, clusters, distills, or infers it.

**Hard rule — specialized metadata wins**: Master/Layout/placeholder metadata for native structure, `data-pptx-replace-with` for native Chart/Table/Formula replacement, and the shape metadata of [`shared-standards-core.md`](./shared-standards-core.md) §§1.4–1.5 are never duplicated with `data-pptx-role`.

---

## 2. Master and Layout Atoms

Structured routes only — attribute table, layer order, and consistency rules in [`pptx-structure-interface.md`](./pptx-structure-interface.md) §2. Canonical form:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"
     data-pptx-master="master-default" data-pptx-master-name="Default Master"
     data-pptx-layout="content-two-column" data-pptx-layout-name="Two Column">
  <rect id="master-bg" data-pptx-layer="master" x="0" y="0" width="1280" height="720" fill="#F8FAFC"/>
  <path id="layout-rule" data-pptx-layer="layout" d="M72 132H1208" stroke="#CBD5E1"/>
</svg>
```

Every atom is a direct root child with a stable unique `id` that compiles to one DrawingML object; a `<g>` may not carry the layer attribute except the one validated compact authored-preset group. Concrete titles, body text, metrics, charts, tables, images, and page-specific decoration stay Slide-local or inside a declared slot.

---

## 3. Layout Slots

Structured routes only — placeholder values, carrier compatibility, and bounds derivation in [`pptx-structure-interface.md`](./pptx-structure-interface.md) §2. Canonical forms:

```xml
<g id="title-slot" data-pptx-placeholder="title" data-pptx-bounds="72 48 1136 72">
  <text id="title-carrier" data-pptx-carrier="true" x="72" y="100">Actual title</text>
</g>

<g id="hero-composite-slot" data-pptx-placeholder="object" data-pptx-binding="proxy"
   data-pptx-bounds="544 160 664 472">
  <rect x="544" y="160" width="664" height="472" fill="#E2E8F0"/>
  <text x="576" y="214">Visible composite content</text>
</g>
```

A carrier-bound slot holds exactly one compatible direct child marked `data-pptx-carrier="true"`; reusable decoration is a root Layout atom, not slot content. The proxy form is the explicit `object`-only downgrade for a composite region: the visible group stays Slide-local and export adds one hidden transparent placeholder. A Layout may have zero slots.

---

## 4. Minimal Structural Roles

Use `data-pptx-role` only when no specialized marker owns the behavior:

| Value | Compiler behavior |
|---|---|
| `background` | Treat an otherwise unmarked background as static page framing for animation |
| `decoration` | Exclude decorative framing from automatic entrance animation |
| `header`, `footer`, `logo`, `watermark`, `chrome` | Slide-local static framing without Master/Layout ownership |
| `page-number` | Slide-local number when no `slide-number` placeholder exists |

On flat pages a direct root background image or full-canvas scrim/decoration rectangle may carry the role and remain a primitive with a stable unique `id`; do not add a `<g>` solely to avoid an ungrouped-element advisory. Never add structural roles to ordinary titles, body copy, cards, KPIs, diagrams, charts, icons, or images.

---

## 5. Validation and Migration

Structured validation rejects a missing or lock-mismatched root identity, an ordinary Master/Layout `<g>`, nested structure markers, missing/stale ids, inconsistent shared atom contracts, slots without positive bounds or exactly one compatible carrier, proxy binding on a non-`object` slot, incomplete page mappings, cross-Master key reuse, and conflicting same-key contracts. Legacy metadata and the input boundary are in [`pptx-structure-interface.md`](./pptx-structure-interface.md) §3; export never derives, repairs, or migrates structure.
