# Minimal Semantic SVG Markers

PPT Master uses rendering-neutral compiler hints only where ordinary SVG cannot express PowerPoint Master, Layout, placeholder, native-object, or package behavior.

## 1. Boundary

| Marker | Placement | Purpose |
|---|---|---|
| `data-pptx-page-role` | Root `<svg>` on flat pages only | Classify a free-design/brand-only page as `cover`, `toc`, `section`, `content`, or `ending`. |
| `data-pptx-master` / `data-pptx-master-name` | Root `<svg>` | Bind the page to one named PowerPoint Slide Master. |
| `data-pptx-layout` / `data-pptx-layout-name` | Root `<svg>` | Bind the page to one named Layout under that Master. |
| `data-pptx-layer="master"` | Direct atomic child of root | Promote one fixed visual object to the named Master. |
| `data-pptx-layer="layout"` | Direct atomic child of root | Promote one fixed visual object to the named Layout. |
| `data-pptx-placeholder` | Direct child `<g id>` of root | Declare one reusable Layout slot whose visible content remains Slide-local. |
| `data-pptx-role` | Structural page-frame element | Supply package, page-number, or animation behavior not already expressed by specialized metadata. |

The completed SVG remains the full visible page. Removing the metadata must not change browser rendering. Do not copy visible text, geometry, style, or asset values into metadata.

**Hard rule — route boundary**: Free-design and brand-only pages use `pptx_structure.mode: flat`, declare one canonical root `data-pptx-page-role`, and omit every Master/Layout/layer/placeholder marker in this document. Deck/layout template pages declare their final Master and Layout before drawing begins and omit `data-pptx-page-role`; the structured exporter compiles that contract and never selects, clusters, distills, or visually infers it.

**Hard rule — specialized metadata wins**: Use Master/Layout/placeholder metadata for native structure, `data-pptx-replace-with` for optional PowerPoint-native Chart/Table replacement, and the imported/authored shape metadata defined in [`shared-standards.md`](./shared-standards.md) §§1.4–1.5. Do not duplicate those facts with `data-pptx-role`.

---

## 2. Master and Layout Atoms

On structured deck/layout template routes, Master and fixed Layout visuals are atomic root children:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-master="master-default"
     data-pptx-master-name="Default Master"
     data-pptx-layout="content-two-column"
     data-pptx-layout-name="Two Column">
  <rect id="master-bg" data-pptx-layer="master"
        x="0" y="0" width="1280" height="720" fill="#F8FAFC"/>
  <path id="layout-rule" data-pptx-layer="layout"
        d="M72 132H1208" stroke="#CBD5E1"/>
</svg>
```

| Requirement | Rule |
|---|---|
| Placement | Every Master/Layout atom is a direct child of the root SVG and has a stable unique `id`. |
| Grouping | A `<g>` may not carry `data-pptx-layer="master|layout"`. Imported PowerPoint groups are recursively flattened and their transform/style/opacity/z-order semantics are pushed into atomic children. |
| Atomicity | One marked child must compile to one DrawingML object. A nested crop `<svg>` is allowed only when it is the supported single-picture carrier, not an arbitrary container. |
| Consistency | Pages sharing one Master key repeat the identical ordered Master atom contract. Pages sharing one `(master, layout)` pair repeat the identical ordered Layout atom contract. |
| Ownership | Concrete titles, body text, metrics, charts, tables, images, and page-specific decoration stay Slide-local or inside a declared slot. |

> Note: Flattening a source PPTX group preserves supported appearance and native-layer ownership, but intentionally does not preserve the source group-editing hierarchy.

---

## 3. Layout Slots

### 3.1 Carrier-bound slot

Use one direct root group as the authoring boundary and one compatible direct child as the visible PowerPoint placeholder carrier:

```xml
<g id="title-slot"
   data-pptx-placeholder="title"
   data-pptx-placeholder-bounds="72 48 1136 72">
  <text id="title-carrier"
        data-pptx-placeholder-carrier="true"
        x="72" y="100">Actual title</text>
</g>
```

| Requirement | Rule |
|---|---|
| Placement | The slot `<g id>` is a direct root child. Structural metadata may not be nested below it. |
| Bounds | `data-pptx-placeholder-bounds="x y width height"` is mandatory, finite, and positive. It describes the reusable design zone, not the current glyph/content tight bounds. |
| Carrier | The group contains exactly one compatible direct drawable child marked `data-pptx-placeholder-carrier="true"`. Export unwraps that child into the real Slide placeholder binding. |
| Identity | `data-pptx-placeholder-idx` is optional; effective indices must be unique within one Layout. Preserve a source index when reconstructing an existing PPTX. |
| Fixed decoration | Reusable decoration does not belong in the slot. Author it as a root Layout atom. Page-specific labels/captions use another slot or remain Slide-local. |

Canonical placeholder values are `title`, `subtitle`, `body`, `picture`, `chart`, `table`, `object`, `media`, `date`, `footer`, and `slide-number`. Carrier compatibility is defined in [`shared-standards.md`](./shared-standards.md) §7.

### 3.2 Explicit composite proxy

When one reusable region is a composite object that cannot bind to one real PowerPoint placeholder, declare the downgrade explicitly:

```xml
<g id="hero-composite-slot"
   data-pptx-placeholder="object"
   data-pptx-placeholder-binding="proxy"
   data-pptx-placeholder-bounds="544 160 664 472">
  <rect x="544" y="160" width="664" height="472" fill="#E2E8F0"/>
  <text x="576" y="214">Visible composite content</text>
</g>
```

The visible group stays Slide-local. Export creates one hidden transparent matching placeholder proxy. Proxy binding is valid only for `object`; it is an explicit fallback, not the default slot form.

### 3.3 Zero-slot Layout

A Layout may contain no slot groups. Cover, poster, full-visual, or other fixed-composition pages still declare their Master/Layout root identity and any fixed atoms; do not manufacture a full-page `object` placeholder merely to make the Layout non-empty.

---

## 4. Minimal Structural Roles

Use `data-pptx-role` only when no specialized marker owns the behavior:

| Value | Compiler behavior |
|---|---|
| `background` | Treat an otherwise unmarked background as static page framing for animation. |
| `decoration` | Exclude decorative framing from automatic entrance animation. |
| `header`, `footer`, `logo`, `watermark`, `chrome` | Identify Slide-local static framing without claiming Master/Layout ownership. |
| `page-number` | Identify a Slide-local number when no `slide-number` placeholder exists. |

Do not add structural roles to ordinary titles, body copy, cards, KPIs, diagrams, charts, icons, or images.

---

## 5. Validation and Migration

For structured deck/layout template projects, validation rejects:

- a missing root Master/Layout identity or a page-to-lock mismatch;
- a Master/Layout `<g>`, nested structure marker, missing/stale id, or inconsistent shared atom contract;
- a slot without positive bounds, a carrier-bound slot without exactly one compatible carrier, or a proxy binding on a non-`object` slot;
- incomplete page mappings, cross-Master Layout-key reuse, or conflicting same-key Layout contracts.

Legacy structured/template SVGs using unmapped `baseline`, `preserve`, `layout_strategy: distill`, `data-pptx-layout-kind`, `distilled`, `utility`, direct atomic placeholders, or an incomplete Master identity are not a second supported structured contract. Run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) before generation or export. An explicit `mode: flat` free-design/brand-only project is current and intentionally has no Master identity. When original PPTX/native facts exist, migration restores those identities first; otherwise the main Agent explicitly derives structured template metadata. Export never performs that derivation.
