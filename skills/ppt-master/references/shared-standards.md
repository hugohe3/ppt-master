# Shared Technical Standards

Common technical constraints for PPT Master, eliminating cross-role file duplication.

---

## 1. SVG Banned Features Blacklist

The following are **forbidden** in generated SVGs — PPT export breaks otherwise:

### 1.0 Text characters: must be well-formed XML

SVG is strict XML. Two rules for all text and attribute values:

| Character category | Required form | Forbidden form |
|---|---|---|
| Typography & symbols (em dash, en dash, ©, ®, →, ·, NBSP, full-width punctuation, emoji…) | **Raw Unicode characters** — write `—` `–` `©` `®` `→` directly | HTML named entities — `&mdash;` `&ndash;` `&copy;` `&reg;` `&rarr;` `&middot;` `&nbsp;` `&hellip;` `&bull;` etc. |
| XML reserved characters (`&`, `<`, `>`, `"`, `'`) | **XML entities only** — `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`) | Bare `&` `<` `>` (e.g. `R&D`, `error < 5%`) |

One offending character invalidates the file and aborts export. Numeric refs (`&#160;` / `&#xa0;`) are XML-legal but discouraged.

**Structural blacklist** (in addition to the character rules above):

| Banned Feature | Description |
|----------------|-------------|
| `mask` | Masks |
| `<style>` | Embedded stylesheets |
| `class` | CSS selector attributes (`id` inside `<defs>` is a legitimate reference and is NOT banned) |
| External CSS | External stylesheet links |
| `<foreignObject>` | Embedded external content |
| `<symbol>` + `<use>` | Symbol reference reuse |
| `textPath` | Text along a path |
| `@font-face` | Custom font declarations |
| `<animate*>` / `<set>` | SVG animations |
| `<script>` / event attributes | Scripts and interactivity |
| `<iframe>` | Embedded frames |

> **`marker-start` / `marker-end` is conditionally allowed** — see §1.1 for constraints. The converter maps qualifying markers to native DrawingML `<a:headEnd>` / `<a:tailEnd>`.
>
> **`clipPath` on `<image>` is conditionally allowed** — see §1.2 for constraints. The converter maps qualifying clip shapes to native DrawingML picture geometry (`<a:prstGeom>` or `<a:custGeom>`).
>
> **`<pattern>` fills are conditionally allowed** — see §7 *Pattern Fill* for the required `data-pptx-pattern` annotation and the closed OOXML preset enum. Hand-drawn pattern geometry is NOT honored; the converter emits the named PPTX preset only. Missing or invalid preset values produce diagonal stripes (warning) or schema-failed PPTX (error).
>
> **Replacing `<mask>` effects** — DrawingML has no per-pixel alpha. Route by effect:
> - Image gradient overlay (vignette/fade/tint) → stacked `<rect>` with `<linearGradient>`/`<radialGradient>` (§6 Image Overlay)
> - Non-rectangular image crop (circle/rounded/hexagon) → `clipPath` on `<image>` (§1.2)
> - Inner glow / soft-edge → `<filter>` with `<feGaussianBlur>` (§6 Glow)
> - Drop shadow → filter shadow or layered rect (§6 Shadow)
>
> Pixel-level alpha effects (text-knockout image fills, arbitrary alpha composites) have no PPT path — bake into the source image at Image_Generator stage.

---

### 1.1 Line-end Markers (Conditionally Allowed)

`marker-start` and `marker-end` on `<line>` and `<path>` elements are allowed **only** when the referenced `<marker>` satisfies all of the following:

| Requirement | Reason |
|-------------|--------|
| Marker `<marker>` element defined inside `<defs>` | Converter looks up marker defs via id index |
| `orient="auto"` | DrawingML arrow auto-rotates along the line tangent; other orient values will not round-trip |
| Marker shape is **one of**: closed 3-vertex path/polygon (triangle), closed 4-vertex path/polygon (diamond), `<circle>` / `<ellipse>` (oval) | These three map cleanly to DrawingML `type="triangle" / "diamond" / "oval"`. Any other shape is silently dropped with a warning. |
| Marker child's `fill` **matches** the parent line's `stroke` color | In DrawingML the arrow head inherits the line color — a mismatched marker fill will look wrong on export. |
| `markerWidth` / `markerHeight` roughly in `3–15` range | Mapped to `sm` (<6) / `med` (6–12) / `lg` (>12) size buckets. |

**Use boundary**:

- `marker-start` / `marker-end`: only for connector arrows where the line is primary
- For block / chunky / solid arrows (arrow body is the visual object), use standalone closed `<path>` / `<polygon>`; see `templates/charts/chevron_process.svg` or `templates/charts/process_flow.svg`

**Supported DrawingML mapping**:

| SVG Marker Shape | DrawingML Output |
|------------------|------------------|
| `<path d="M0,0 L10,5 L0,10 Z"/>` (triangle) | `<a:tailEnd type="triangle" w="med" len="med"/>` |
| `<polygon points="0,0 10,5 0,10"/>` | `<a:tailEnd type="triangle" w="med" len="med"/>` |
| 4-vertex closed path/polygon | `<a:tailEnd type="diamond" .../>` |
| `<circle cx="5" cy="5" r="4"/>` | `<a:tailEnd type="oval" .../>` |

**Recommended template** — a standard arrow-head definition ready to reuse:

```xml
<defs>
  <marker id="arrowHead" markerWidth="10" markerHeight="10" refX="9" refY="5"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 Z" fill="#1976D2"/>
  </marker>
</defs>
<line x1="100" y1="200" x2="400" y2="200" stroke="#1976D2" stroke-width="3"
      marker-end="url(#arrowHead)"/>
```

> ⚠️ Unclassifiable marker shapes (curved paths, multi-segment, >4 vertices) are silently dropped — line renders without arrow. Use a manual `<polygon>` for exotic shapes.

---

### 1.2 Image Clipping (Conditionally Allowed)

`clip-path` on `<image>` elements is allowed when the referenced `<clipPath>` satisfies the following:

| Requirement | Reason |
|-------------|--------|
| `<clipPath>` element defined inside `<defs>` | Converter looks up clip defs via id index |
| Contains a **single** shape child | First child is used; multiple children are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (with rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| Used **only on `<image>` elements** | Non-image elements with clip-path are **forbidden** |

**Use boundary**:

- Only on `<image>` for non-rectangular crops (circular avatars, rounded frames, hexagons)
- NOT on shapes (`<rect>`/`<circle>`/`<path>`/`<g>`/`<text>`) — draw the target shape directly. A rect clipped to a circle is just a circle.
- PowerPoint's SVG renderer doesn't handle `clipPath`; only the Native PPTX converter does.

**Supported DrawingML mapping**:

| SVG Clip Shape | DrawingML Output | Use Case |
|----------------|------------------|----------|
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse"/>` | Circular avatar, oval frame |
| `<rect rx="..."/>` | `<a:prstGeom prst="roundRect"/>` with adj value | Rounded rectangle photo frame |
| `<path>` / `<polygon>` | `<a:custGeom>` with path commands | Hexagon, diamond, custom shape |

**Recommended template** — circular image clip:

```xml
<defs>
  <clipPath id="avatarClip">
    <circle cx="200" cy="200" r="100"/>
  </clipPath>
</defs>
<image href="../images/photo.jpg" x="100" y="100" width="200" height="200"
       clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice"/>
```

**Rounded rectangle clip** — for card-style image frames:

```xml
<defs>
  <clipPath id="cardClip">
    <rect x="60" y="120" width="400" height="250" rx="16"/>
  </clipPath>
</defs>
<image href="../images/banner.jpg" x="60" y="120" width="400" height="250"
       clip-path="url(#cardClip)" preserveAspectRatio="xMidYMid slice"/>
```

> ⚠️ `clip-path` on non-image elements is FORBIDDEN — quality checker errors out. Draw target geometry directly.

---

## 2. PPT Compatibility Alternatives

| Banned Syntax | Correct Alternative |
|---------------|---------------------|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">...</g>` | Set `fill-opacity` / `stroke-opacity` on each child element individually |
| `<image opacity="0.3"/>` | Overlay a `<rect fill="background-color" opacity="0.7"/>` mask layer after the image |

**Mnemonic**: PPT does not recognize rgba, group opacity, or image opacity.

> Arrows: prefer `marker-end` for connector lines (§1.1) — converter produces native auto-rotating arrow heads. For block/chunky arrows, use standalone closed shapes; see `templates/charts/chevron_process.svg` and `templates/charts/process_flow.svg`.

---

## 3. Canvas Format Quick Reference

> See [`canvas-formats.md`](canvas-formats.md) for the full format table (presentations / social / marketing) and the format-selection decision tree.

---

## 4. Basic SVG Rules

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

- **viewBox** MUST match the canvas dimensions; it is the single source of truth for canvas size. Root `width`/`height` are optional compatibility attributes and are not used as PPT Master canvas authority.
- **Background**: Use `<rect>` to define the page background color
- **`<tspan>`** has two purposes: (1) manual line breaks (use `dy` or explicit `y`); (2) inline run formatting on the same line (color/weight/size). `<foreignObject>` is FORBIDDEN. See "Single logical line" rule below.
- **Fonts**: every `font-family` stack MUST resolve to pre-installed exported Latin / EA typefaces (Microsoft YaHei / SimSun / Arial / Times New Roman / Consolas …); `@font-face` is FORBIDDEN. Full rule: [`strategist.md §g`](strategist.md).
- **Styles**: inline only (`fill=""`, `font-size=""`); `<style>`/`class` FORBIDDEN (`id` inside `<defs>` is fine)
- **Colors**: HEX only; transparency via `fill-opacity`/`stroke-opacity`
- **Images**: `<image href="../images/xxx.png" preserveAspectRatio="xMidYMid slice"/>`
- **Icons**: `<use data-icon="<library>/<name>" x="" y="" width="48" height="48" fill="#HEX"/>` (auto-embedded post-processing). Always include library prefix. One stylistic library per deck (`chunk-filled`/`tabler-filled`/`tabler-outline`/`phosphor-duotone`); `simple-icons` only for real brand marks. See [`../templates/icons/README.md`](../templates/icons/README.md).

### Inline Text Runs (Single Logical Line = Single `<text>`)

One logical line — even with mixed colors/weights/sizes — MUST be one `<text>` with inline `<tspan>` children. Never use multiple adjacent `<text>` elements. The converter maps each `<tspan>` to a `<a:r>` run within the same PPT text frame, keeping the line as one editable shape.

✅ **DO** — one `<text>` → one text frame with three runs:

```xml
<text x="100" y="200" font-size="24" fill="#333333">
  实现<tspan fill="#1A73E8" font-weight="bold">10倍</tspan>效率提升
</text>
```

❌ **DON'T** — three side-by-side `<text>` elements become three separate text frames in PPT (breaks edit-as-one-line, risks alignment drift, makes spacing fragile):

```xml
<text x="100" y="200" font-size="24" fill="#333333">实现</text>
<text x="160" y="200" font-size="24" fill="#1A73E8" font-weight="bold">10倍</text>
<text x="240" y="200" font-size="24" fill="#333333">效率提升</text>
```

**⚠️ Inline tspans must NOT carry `x`/`y`/`dy`** — those mark a new line, and `flatten_tspan` will split into a separate text frame. `dx` is safe (kerning, stays inline). Only set `x`/`y`/`dy` on tspans that genuinely start a new line.

**Multi-line `<text>` with per-line emphasis works**: an outer line-break tspan (with `x` + `dy` or `y`) MAY contain nested inline tspans for color/weight/size — converter walks nested tspans and emits one run per styled segment:

```xml
<text x="80" y="190" font-size="18" fill="#333333">
  <tspan x="80" dy="0">完成率<tspan fill="#4CAF50" font-weight="bold">98%</tspan>超预期</tspan>
  <tspan x="80" dy="35">成本降低<tspan fill="#F44336" font-weight="bold">¥120万</tspan></tspan>
</text>
```

❌ **DON'T** — same-line column jump via `<tspan x="...">`:

```xml
<text x="100" y="200" font-size="18" fill="#333333">
  <tspan x="100">左列</tspan><tspan x="600" font-weight="bold">右列</tspan>
</text>
```

`x` on a tspan starts a new line, splitting into two independent text frames. For two-column layouts, write two `<text>` elements.

**Default — lift key information.** Uniform-styled paragraphs read as walls of text. Wrap these in `<tspan fill="..." font-weight="bold">`:

- **Numerical results** — percentages, multipliers (`10x`), absolute amounts (`¥120万`)
- **Contrasts** — gain/loss, before/after, target/actual
- **One or two load-bearing nouns per sentence** — the term that carries the insight

Do NOT highlight: connectives, common verbs, every noun, decorative adjectives, structural text (footer/axis/legend/page number/labels).

Color: use the deck's primary brand color for emphasis. Reserve green/red for actual positive/negative semantics.

❌ **DON'T** — uniform-styled paragraph buries the insight:

```xml
<text x="80" y="200" font-size="20" fill="#333333">
  2024年公司营收同比增长35%达到12亿元创历史新高
</text>
```

✅ **DO** — same line, key data lifted:

```xml
<text x="80" y="200" font-size="20" fill="#333333">
  2024年公司营收同比<tspan fill="#1A73E8" font-weight="bold">增长35%</tspan>达到<tspan fill="#1A73E8" font-weight="bold">12亿元</tspan>创历史新高
</text>
```

### Element Grouping (Mandatory)

Wrap logically related elements in top-level `<g id="...">` groups. Produces PowerPoint groups in PPTX, making slides easier to select/move/edit and providing stable anchors for optional per-element entrance animation.

> ⚠️ Only `<g opacity="...">` is banned (§2). Plain `<g>` for grouping is required.

**Animation-ready rule**: direct children of `<svg>` should be semantic groups, not raw drawing atoms. Aim for **3–8 top-level content `<g id>` groups per slide** (the 3–8 budget excludes page chrome — see below); each content group becomes one entrance step under the chosen `--animation-trigger` mode (one click in `on-click`, one cascade slot in `after-previous`, parallel in `with-previous`).

**Chrome groups are excluded automatically.** Existing `data-pptx-layer` and `data-pptx-placeholder="slide-number"` semantics are read first. Otherwise, explicit `data-pptx-role` values `background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, and `logo` identify static page framing. For marker-free legacy SVGs, ids remain a compatibility fallback using these tokens after splitting on `-` / `_`: `background`, `bg`, `decoration` / `decorations` / `decor`, `header`, `footer`, `chrome`, `watermark`, `pagenumber` / `pagenum` / `page-number`, `nav`, `logo`, `rule`. Keep the `<g>` wrapper for editing/grouping.

Minimal structural roles also drive slide-master promotion in the default native export: `logo` / `footer` / `header` / `watermark` / `chrome` elements drawn **before** content and repeated **verbatim** across pages may move into the slide master (pages without them, like covers, are isolated automatically). A `data-pptx-placeholder="slide-number"` text, or a free-design `data-pptx-role="page-number"` text, whose content exactly equals the page's display number becomes a self-renumbering PowerPoint field. Exact id tokens remain a fallback only when specialized/minimal markers are absent.

**What to group**:

| Grouping Unit | Contains |
|---------------|----------|
| Card / panel | Background rect + (optional shadow only if the card floats over a photo/colored panel — see §6) + icon + title + body text |
| Process step | Number circle + icon + label + description |
| List item | Bullet / number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + accent decoration |
| Page footer | Page number + branding |
| Decorative cluster | Related decorative shapes (rings, orbs, dots) |

**Do not**:

- Put the whole slide into one giant `<g>`; that leaves only one animation step.
- Leave many top-level `<rect>` / `<text>` / `<path>` elements ungrouped; fallback animation is capped at 8 primitives and dense flat pages may skip animation.
- Split every icon, text line, or decorative mark into separate top-level groups; that creates too many click steps.
- Use anonymous top-level groups. Every top-level semantic group needs a descriptive `id`.

**Example**:

```xml
<g id="card-benefits-1">
  <!-- This card floats over a colored panel — shadow is appropriate. On a flat white canvas, omit the filter. -->
  <rect x="60" y="115" width="565" height="260" rx="20" fill="#FFFFFF" filter="url(#shadow)"/>
  <use data-icon="chunk-filled/bolt" x="108" y="163" width="44" height="44" fill="#0071E3"/>
  <text x="105" y="270" font-size="56" font-weight="bold" fill="#0071E3">10×</text>
  <text x="250" y="270" font-size="30" font-weight="bold" fill="#1D1D1F">Faster</text>
  <text x="105" y="310" font-size="18" fill="#6E6E73">Reduce production time from days to hours.</text>
</g>
```

**Naming**: descriptive `id` on top-level `<g>` is **required** (e.g., `card-1`, `step-discover`, `header`, `footer`). Each top-level `<g id>` becomes one anchor for per-element entrance animation in PPTX export; without it, the exporter falls back to at most 8 top-level primitives or skips animation on dense pages.

---

## 5. Post-processing Pipeline (3 Steps)

Must be executed in order — skipping or adding extra flags is FORBIDDEN:

```bash
# 1. Split speaker notes into per-page note files
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (icon embedding, image crop/embed/optimization, text flattening, rounded rect to path)
python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX (embeds speaker notes by default)
python3 scripts/svg_to_pptx.py <project_path>
# Output (default-flow mode):
#   exports/<project_name>_<timestamp>.pptx           ← native pptx (canonical output)
#   backup/<timestamp>/svg_output/                    ← Executor SVG source backup (always written)
#
# Add --svg-snapshot to additionally emit:
#   exports/<project_name>_<timestamp>_svg.pptx      ← SVG snapshot pptx (sibling of native pptx)
```

**Optional animation flags** (only when the user asks):
- `-t <effect>` — page transition (`fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random` / `none`; default `fade`)
- `-a <effect>` — per-element entrance animation (`fade` / `auto` / `mixed` / `random` / one of 22 named effects / `none`; **default `none`** — pages appear as a whole, no auto element builds; opt in with `auto`, which maps effect from group id — image-like ids cycle zoom/dissolve/circle/box/diamond/wheel, other matches map to a single effect, unmatched ids cycle fade/wipe/fly/zoom). Anchors on top-level `<g id="...">` groups.
- `--animation-trigger {on-click,with-previous,after-previous}` — Start mode matching PowerPoint's animation-pane Start dropdown. Default `after-previous` (cascade on slide entry; pace via `--animation-stagger <seconds>`); `on-click` advances per click; `with-previous` plays all groups together.
- `--animation-config <path>` — optional object-level animation sidecar. Default: `<project>/animations.json` when present.
- `--auto-advance <seconds>` — kiosk-style auto-play

**Optional recorded narration** (only when the user asks for narrated/video export):

```bash
python3 scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
```

- `notes_to_audio.py` reads split `notes/*.md` files and writes one audio file per slide to `audio/`. Default `edge` output is MP3; configured cloud providers may output MP3 or WAV depending on provider settings.
- `--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide needs matching `m4a` / `mp3` / `wav` audio, every duration must be readable by `ffprobe`, and `on-click` object animation is rejected.
- `--recorded-narration audio` embeds matching audio, keeps speaker notes, and sets slide timings from audio duration.
- `--narration-audio-dir audio` is the lower-level embedding path for partial audio coverage; it does not prepare a complete recorded-timings export.
- Long-audio import and automatic long-audio splitting are not supported.

Full reference: [`animations.md`](animations.md).

**Prohibited**:
- NEVER use `cp` as a substitute for `finalize_svg.py`
- NEVER force `-s output` for the legacy/preview pptx (PowerPoint's internal SVG parser drops icons and rounded corners). Default auto-split already gives native the high-fidelity source it needs without affecting legacy.
- NEVER use `--only` in the standard pipeline; keep it for explicit one-product diagnostics or compatibility checks

> Source-directory split: by default `svg_to_pptx.py` reads `svg_output/` for the native pptx (preserves icon `<use>`, image `preserveAspectRatio` as native picture-crop metadata, rounded rect `rx/ry` → `prstGeom roundRect`) and `svg_final/` for the legacy/preview pptx (PowerPoint's internal SVG parser needs the flattened form). Pass `-s output` or `-s final` only when you specifically want both products to read from a single source.

**Default — raster size control**: `finalize_svg.py` optimizes raster images using a rendered-size budget of `2x` display pixels with a `2560px` maximum dimension; it may crop pixels for the flattened SVG snapshot. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: it downscales only oversized full source images to `--image-max-dimension 2560`, keeps display cropping as editable PPT picture-crop metadata, and does not shrink a picture merely because its current SVG placement is small. Opaque PNG photos may become JPEG; transparent assets remain PNG. Use `finalize_svg.py --no-compress` / a higher `--max-dimension` only for diagnostic SVG snapshots, `svg_to_pptx.py --no-image-optimize` only when the native PPTX must retain original image bytes, and `svg_to_pptx.py --image-sizing display --image-scale 2` only for aggressive size reduction.

**Re-run rule**: Any change to `svg_output/` after post-processing requires re-running Steps 2-3. Step 1 only re-runs if `notes/total.md` changed.

---

## 6. Shadow & Overlay Techniques

> `<mask>` elements and `<image opacity="...">` are banned. Always use stacked `<rect>` or gradient overlays instead (see §2).

### Shadow

> **Shadow is restraint, not default.** The "designed" feel comes from absence, not abundance.

#### When to use

Only when the element genuinely floats above another layer:
- Card / quote bubble / annotation on a photo or colored panel
- Single primary CTA or "recommended" item picked out from peers
- Overlay layer (callout, tooltip, modal emphasis)
- Floating image card on a textured background

#### When NOT to use

- Background panels / dividers / decorative bars — they are the floor
- Equal peer cards in a 2/3/4-up grid — keep all flat
- Containers with visible border, gradient fill, or strong tint — redundant
- Body-text paragraph containers — disrupts scan rhythm
- Decorative lines / dividers / icons — they are symbols, not objects
- Pages with only one content container — no second layer to lift above
- Dark backgrounds — black shadows vanish; use 1px low-opacity white stroke or outer glow

**Reference — not a constraint**: 2-3 shadowed elements per page usually reads cleanest; before adding a 4th, check the extra layering earns its weight — a genuinely complex dashboard may justify more.

#### Single light source per page

All `feOffset` on a page must share the same `dx`/`dy` direction. Default: `dx="0"`, `dy="4"`-`dy="8"` (light from upper front).

#### Restraint over visibility

Standard: "the shadow is felt, not seen." If noticed, it's too strong.
- Resting cards: `flood-opacity` 0.06-0.10
- Raised elements (CTA, overlay): max `flood-opacity` 0.20
- Above 0.20 = Office 2007 hard-shadow look
- Color: near-black at low opacity, or a darker tint of background. Brand-color shadow only on accent elements sharing that hue.

#### Two-tier elevation maximum

A page may have at most two non-floor tiers.

| Tier | When | dy | stdDeviation | flood-opacity |
|------|------|----|--------------|---------------|
| Floor (no shadow) | Backgrounds, peer-grid cards, dividers, body-text containers | — | — | — |
| Resting | Cards on photos/panels, secondary callouts | 2-4 | 4-8 | 0.06-0.10 |
| Raised | Primary CTA, focused/recommended card, overlay | 6-10 | 10-16 | 0.12-0.20 |

#### Don't stack visual-weight tools

Pick **one** per container: shadow, border, gradient fill, or strong tint. Stacking = instant template look.

---

#### Filter Soft Shadow — Recommended

Best for: cards, floating panels, elevated elements. The `svg_to_pptx` converter automatically converts `feGaussianBlur` + `feOffset` into native PPTX `<a:outerShdw>`.

```xml
<defs>
  <filter id="softShadow" x="-15%" y="-15%" width="140%" height="140%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="12"/>
    <feOffset dx="0" dy="6" result="offsetBlur"/>
    <feFlood flood-color="#000000" flood-opacity="0.10" result="shadowColor"/>
    <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
    <feMerge>
      <feMergeNode in="shadow"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
<rect x="60" y="60" width="400" height="240" rx="12" fill="#FFFFFF" filter="url(#softShadow)"/>
```

Recommended parameters (see "Two-tier elevation maximum" above for tier guidance):
```
stdDeviation:   4–16       (resting cards: 4–8;  raised elements: 10–16)
flood-opacity:  0.06–0.10  (resting cards — default)
                0.12–0.20  (raised elements only — primary CTA, overlay)
                NEVER     > 0.20  (Office 2007 hard-shadow look)
dy:             2–10       (resting: 2–4;  raised: 6–10)
dx:             0–2        (must match every other shadow on the page — single light source)
```

#### Colored Shadow

Best for: accent buttons, brand-colored cards. Use the element's own color family instead of black.

```xml
<filter id="colorShadow" x="-15%" y="-15%" width="140%" height="140%">
  <feGaussianBlur in="SourceAlpha" stdDeviation="10"/>
  <feOffset dx="0" dy="6" result="offsetBlur"/>
  <feFlood flood-color="#1A73E8" flood-opacity="0.20" result="shadowColor"/>
  <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
  <feMerge>
    <feMergeNode in="shadow"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

Replace `flood-color` with the element's brand color. Keep `flood-opacity` 0.12-0.20. Reserve for the single primary CTA per page — using on every button defeats the cue.

#### Glow Effect

Best for: title highlights, key metrics, hero text. The converter automatically converts `feGaussianBlur` without `feOffset` into native PPTX `<a:glow>`.

```xml
<defs>
  <filter id="titleGlow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="blur"/>
    <feFlood flood-color="#1A73E8" flood-opacity="0.45" result="glowColor"/>
    <feComposite in="glowColor" in2="blur" operator="in" result="glow"/>
    <feMerge>
      <feMergeNode in="glow"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
<text x="640" y="360" text-anchor="middle" font-size="48" fill="#1A73E8" filter="url(#titleGlow)">Key Insight</text>
```

Recommended parameters:
```
stdDeviation:   4–8      (smaller = subtle, larger = prominent)
flood-color:    brand color or accent color (NOT black)
flood-opacity:  0.35–0.55  (stronger than shadow for visibility)
```

**vs shadow**: no `<feOffset>` (or dx=0/dy=0). The converter uses this to distinguish glow from shadow.

#### Layered Rect Shadow — High-Compatibility Fallback

Best for: maximum compatibility with older PowerPoint versions. Stack 2–3 semi-transparent rectangles behind the main card:

```xml
<!-- Shadow layers (back to front, largest offset first) -->
<rect x="68" y="72" width="400" height="240" rx="16" fill="#000000" fill-opacity="0.03"/>
<rect x="65" y="69" width="400" height="240" rx="14" fill="#000000" fill-opacity="0.05"/>
<rect x="62" y="66" width="400" height="240" rx="12" fill="#1A73E8" fill-opacity="0.04"/>
<!-- Main card -->
<rect x="60" y="60" width="400" height="240" rx="12" fill="#FFFFFF"/>
```

### Image Overlay

#### Linear Gradient Overlay — Most Common

Best for: image+text pages. Gradient direction should match text position (text on left → gradient darkens toward left).

```xml
<image href="..." x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>
<defs>
  <linearGradient id="imgOverlay" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#1A1A2E" stop-opacity="0.85"/>
    <stop offset="55%"  stop-color="#1A1A2E" stop-opacity="0.30"/>
    <stop offset="100%" stop-color="#1A1A2E" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#imgOverlay)"/>
```

#### Bottom Gradient Bar

Best for: cover slides and full-image pages with bottom title.

```xml
<defs>
  <linearGradient id="bottomBar" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.72"/>
  </linearGradient>
</defs>
<rect x="0" y="380" width="1280" height="340" fill="url(#bottomBar)"/>
```

#### Radial Gradient Overlay — Vignette Effect

Best for: full-screen atmosphere slides; draws attention to the center.

```xml
<defs>
  <radialGradient id="vignette" cx="50%" cy="50%" r="70%">
    <stop offset="0%"   stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.58"/>
  </radialGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#vignette)"/>
```

#### Brand Color Overlay

Best for: slides needing strong visual brand identity.

```xml
<defs>
  <linearGradient id="brandOverlay" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#005587" stop-opacity="0.80"/>
    <stop offset="100%" stop-color="#005587" stop-opacity="0.10"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#brandOverlay)"/>
```

### Quick-Reference Table

| Scenario | Recommended Technique | Avoid |
|----------|-----------------------|-------|
| Card / panel shadow (only when floating over photo/colored panel) | Filter soft shadow (`flood-opacity` 0.06–0.10, single light source) | Hard black shadow, full-page abundance |
| Equal peer cards in a grid | All flat (no shadow) | Lifting every card uniformly |
| Page-section background panel | Flat fill, no shadow | Treating panels as floating cards |
| Accent / CTA button (one per page) | Colored shadow (same hue family, `flood-opacity` 0.12–0.20) | Generic gray shadow, applying to every button |
| Title / metric highlight | Glow filter (brand color, no offset) | Overuse on body text |
| Text over image | Linear gradient overlay (direction matches text side) | Uniform flat opacity over whole image |
| Cover / full-image slide | Bottom gradient bar + brand color | Solid black overlay |
| Atmosphere / hero slide | Radial vignette | Unprocessed raw image |
| Max PPT compatibility needed | Layered rect shadow | Filter-based shadow |

---

## 7. Stroke, Text & Shape Effects

### stroke-dasharray — Dashed / Dotted Lines

Converts to native PPTX `<a:prstDash>`. Use preset patterns for best results:

| SVG Value | PPTX Preset | Best For |
|-----------|-------------|----------|
| `4,4` | Dash | General dashed lines, separators |
| `2,2` | Dot (sysDot) | Subtle dotted borders, placeholder outlines |
| `8,4` | Long dash | Timeline connectors, flow arrows |
| `8,4,2,4` | Long dash-dot | Technical drawings, dimension lines |

```xml
<rect x="60" y="60" width="400" height="240" rx="12"
  fill="none" stroke="#999999" stroke-width="2" stroke-dasharray="4,4"/>

<line x1="100" y1="360" x2="1180" y2="360"
  stroke="#CCCCCC" stroke-width="1" stroke-dasharray="2,2"/>
```

### stroke-linejoin

Controls how line segments join at corners. Supported values convert to native PPTX line join types:

| SVG Value | PPTX Equivalent | Best For |
|-----------|-----------------|----------|
| `round` | Round join | Smooth polyline charts, organic shapes |
| `bevel` | Bevel join | Technical diagrams |
| `miter` | Miter join (default) | Sharp-cornered rectangles, arrows |

```xml
<polyline points="100,200 200,100 300,200" fill="none"
  stroke="#1A73E8" stroke-width="3" stroke-linejoin="round"/>
```

### text-decoration

Supported text decorations convert to native PPTX text formatting:

| SVG Value | PPTX Equivalent | Best For |
|-----------|-----------------|----------|
| `underline` | Single underline | Emphasis, links, key terms |
| `line-through` | Strikethrough | Removed items, before/after comparisons |

```xml
<text x="100" y="200" font-size="20" fill="#333333" text-decoration="underline">Important Term</text>

<!-- Per-tspan decoration -->
<text x="100" y="240" font-size="18" fill="#333333">
  Regular text <tspan text-decoration="line-through" fill="#999999">old value</tspan> new value
</text>
```

### Gradient Fill — linearGradient & radialGradient

Gradients defined in `<defs>` and referenced via `fill="url(#id)"` convert to native PPTX `<a:gradFill>`. Use them as shape fills (not just overlays) for polished surfaces.

**Linear gradient** — best for buttons, header bars, background panels:

```xml
<defs>
  <linearGradient id="btnGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#1A73E8"/>
    <stop offset="100%" stop-color="#0D47A1"/>
  </linearGradient>
</defs>
<rect x="540" y="600" width="200" height="48" rx="24" fill="url(#btnGrad)"/>
```

**Radial gradient** — best for spotlight backgrounds, circular accents:

```xml
<defs>
  <radialGradient id="spotBg" cx="50%" cy="50%" r="70%">
    <stop offset="0%" stop-color="#1A73E8" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#1A73E8" stop-opacity="0"/>
  </radialGradient>
</defs>
<circle cx="640" cy="360" r="300" fill="url(#spotBg)"/>
```

### Pattern Fill — `<pattern>` with PPTX preset annotation

`<pattern>` fills convert to native PPTX `<a:pattFill prst="...">` — but only PPTX's built-in preset patterns are reachable. The converter does **not** render hand-drawn `<path>` geometry inside the pattern; instead it reads two annotations off the `<pattern>` element and emits the matching DrawingML preset.

**Prefer explicit geometry when spacing matters.** A `<pattern>` renders at PowerPoint's **fixed preset density** — you cannot reproduce a specific tile size (e.g. a 40px grid). For grids / textures whose spacing or line weight is part of the design, draw the lines as **one `<path>` with all lines as subpaths** (`M40 0V720 M80 0V720 … M0 40H1280 …`, `fill="none" stroke=…`) — the converter supports `M/L/H/V` and multi-subpath, so it becomes **one editable vector shape that reproduces the exact spacing** across all four renderers. Reserve `<pattern>` + `data-pptx-pattern` for **round-tripping an existing PPTX** (decks imported via `pptx_to_svg`), where the source genuinely used a native preset fill. For pure display where no PPT-side editing is needed, `--svg-snapshot` is the other faithful option.

**Required annotations** (only when you intentionally use a `<pattern>` preset):

| Attribute | Purpose | Without it |
|---|---|---|
| `data-pptx-pattern="<preset>"` | Names the PPTX preset (one of the enum below) | Falls back to `ltUpDiag` — diagonal stripes, not your geometry |
| Child `<rect fill="<bg-hex>"/>` | Background color of the pattern tile | `bg` falls back to `#FFFFFF`, painting over the page background |

The child `<path>`'s `stroke` becomes the foreground color (the pattern's line color).

```xml
<defs>
  <pattern id="bpGrid" x="0" y="0" width="40" height="40"
           patternUnits="userSpaceOnUse" data-pptx-pattern="lgGrid">
    <rect width="40" height="40" fill="#0E2A47"/>
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#2D4A6B" stroke-width="0.6"/>
  </pattern>
</defs>
<rect width="1280" height="720" fill="url(#bpGrid)"/>
```

**Valid `data-pptx-pattern` values** (OOXML `ST_PresetPatternVal` — closed enum, anything outside makes PowerPoint open with "needs to be repaired"):

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid` — common typo)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

> `svg_quality_checker.py` warns on missing `data-pptx-pattern` and errors on values outside the enum. Catch these pre-export — PowerPoint's repair dialog hides which pattern broke.

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

**Chart typography**: Native classic chart typography mirrors the visible SVG
fallback. Copy fallback chart text sizes into metadata using the same px-style
unit as SVG text (`1px = 0.75pt`). Put the shared visible chart font in
`style.font_family`, and override local chart text objects or `data_labels`
with `font_family` only when the fallback visibly differs. If omitted, the
exporter infers the shared font family and base chart text size from visible
fallback text inside the native marker, but explicit metadata remains the
stable contract when roles differ. Typical mappings are chart title
(`title_font_size`), chart subtitle (`subtitle_font_size`), chart labels
(`axis_font_size`, shared by axis titles / ticks / legend unless the fallback
differs), and notes (`note_font_size`). Use `axis_title_font_size`,
`legend_font_size`, or per-entry companion `font_size` only when the fallback
visibly uses a separate size. When no explicit fallback size exists for a role,
default to compact PowerPoint text: `title_font_size: 16` (12pt),
`subtitle_font_size: 12` (9pt), `axis_font_size: 12` (9pt), and
`note_font_size: 12` (9pt).

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
cylinder, pyramid variants, and `surface`) are intentionally unsupported. They
add compatibility risk without meaningful presentation value.

Native chart legends are off by default because right-side legends routinely
steal plot area in PPT. Add `show_legend: true` only when the legend is needed;
`legend_position` defaults to `bottom` and also accepts `top`, `left`, or
`right`.

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

### Theme Font Inheritance (Baseline and Template Export)

New projects derive PowerPoint theme fonts from `spec_lock.md` typography when
native export uses `baseline` or `template` structure mode:

- `title_family` (falling back to `font_family`) becomes the theme major font.
- `body_family` (falling back to `font_family`) becomes the theme minor font.
- SVG text whose resolved exported face matches either locked family emits
  DrawingML `+mj-*` / `+mn-*` tokens instead of a fixed typeface.
- When major and minor resolve to the same face, ordinary slide-local text uses
  the minor role; semantic `title` placeholders are forced to major, while all
  other semantic placeholders are forced to minor.
- Local emphasis, code, brand, or other families that do not match the locked
  title/body faces remain concrete per-run fonts and do not change with the
  theme.

This substitution is package-only: the SVG stays the live-preview truth, and
the installed theme resolves the tokens to the same concrete fonts on initial
open. Changing the PowerPoint theme later can therefore update matching text
without changing the SVG geometry or the first export's visual design.

`preserve` mode never rewrites source theme fonts, and `flat` remains the
diagnostic slide-local/fixed-font comparison path. A project without a usable
`spec_lock.md` typography section keeps the legacy concrete-font behavior.

### Theme Color Inheritance (Baseline and Template Export)

Native `baseline` and `template` export also derive the PowerPoint color scheme
from `spec_lock.md` colors. The canonical mapping is:

| Lock role | PowerPoint scheme slot |
|---|---|
| `bg` / `background` / `master_bg` | `lt1` |
| `secondary_bg` / `bg_secondary` | `lt2` |
| `text` / `body_text` | `dk1` |
| `text_secondary` | `dk2` |
| `primary` | `accent1` |
| `accent` | `accent2` |
| `secondary_accent` | `accent3` |
| `border` | `accent4` |
| First two additional non-black/non-white roles | `accent5` / `accent6` |

The converter promotes an exact locked HEX to `a:schemeClr` only when its
usage is compatible with the role: backgrounds prefer background roles, text
prefers text/accent roles, strokes prefer `border`, and chart series use only
the primary/accent family. This prevents the same literal HEX from coupling
unrelated semantics such as a white page background and fixed white inverse
text. Gradients, patterns, bullets, native tables, and exact native-chart
series colors follow the same rule. Shadows, effects, unmatched local colors,
and additional palette roles remain concrete `a:srgbClr` values.

The initial rendering is unchanged because every scheme slot resolves to the
same locked HEX. A later PowerPoint theme edit can update only the promoted
roles; it does not rewrite the SVG or local exceptions. `preserve` never
rewrites the imported source color scheme, `flat` keeps concrete colors for
diagnostics, and projects without a usable colors section retain legacy fixed
colors.

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

### transform: rotate — Element Rotation

Rotation converts to native PPTX `<a:xfrm rot="...">`. Supported on all element types: `rect`, `circle`, `ellipse`, `line`, `path`, `polygon`, `polyline`, `image`, and `text`.

```xml
<!-- Rotated decorative element -->
<rect x="100" y="100" width="60" height="60" fill="#1A73E8" fill-opacity="0.1"
  transform="rotate(45, 130, 130)"/>

<!-- Rotated text label -->
<text x="50" y="400" font-size="14" fill="#999999"
  transform="rotate(-90, 50, 400)">Y-Axis Label</text>
```

**Syntax**: `rotate(angle)` or `rotate(angle, cx, cy)` where `cx,cy` is the rotation center. Positive angles rotate clockwise.

### Arc Paths — Donut / Pie Charts

Calculate arc endpoint coordinates precisely with trigonometry. Never estimate — small errors produce wildly wrong shapes.

**Calculation formula** (center `cx,cy`, radius `r`, angle `θ` in degrees):
```
x = cx + r × cos(θ × π / 180)
y = cy + r × sin(θ × π / 180)
```

**Key rules**:
1. Start at **-90°** (12 o'clock position) and go clockwise
2. Each sector spans `percentage × 360°`
3. Use **large-arc flag = 1** when the sector is > 180°, **0** otherwise
4. sweep-direction = 1 (clockwise) for outer arc, 0 (counter-clockwise) for inner arc returning
5. **Always verify** that the sum of all sector angles equals 360° and that the last sector's end point matches the first sector's start point

**Example — 75% donut sector** (center 400,400, outer r=180, inner r=100):
```
Start angle: -90°    → outer(400, 220), inner(400, 300)
End angle: -90+270=180° → outer(220, 400), inner(300, 400)
Large-arc flag: 1 (270° > 180°)

<path d="M 400,220 A 180,180 0 1,1 220,400 L 300,400 A 100,100 0 1,0 400,300 Z"/>
```

### Polygon Arrows on Diagonal Lines

> For connector lines prefer `marker-end`/`marker-start` (§1.1). For chunky/wide solid/non-connector arrows, use standalone polygon or path.

Horizontal/vertical lines can use simple point offsets for `<polygon>` arrowheads. Diagonal lines need triangle vertices rotated to match line direction.

**Method** — calculate triangle points using the line's direction vector:

```
Given line from (x1,y1) to (x2,y2):
1. Direction vector: dx = x2-x1, dy = y2-y1
2. Normalize: len = √(dx²+dy²), ux = dx/len, uy = dy/len
3. Perpendicular: px = -uy, py = ux
4. Arrow tip = (x2, y2)
5. Back point 1 = (x2 - ux×12 + px×5,  y2 - uy×12 + py×5)
6. Back point 2 = (x2 - ux×12 - px×5,  y2 - uy×12 - py×5)
```

**Example — diagonal line** from (260,310) to (370,430):
```
dx=110, dy=120, len≈162.8, ux=0.676, uy=0.737
px=-0.737, py=0.676
Tip: (370, 430)
Back1: (370-8.1-3.7, 430-8.8+3.4) = (358.2, 424.6)
Back2: (370-8.1+3.7, 430-8.8-3.4) = (365.6, 417.8)

<polygon points="370,430 365.6,417.8 358.2,424.6" fill="#C8A96E"/>
```

⚠️ Never use a fixed downward/rightward triangle on a diagonal line — arrow will point wrong.

---

## 8. Project Directory Structure

```
project/
├── svg_output/    # Raw SVGs (Executor output, contains placeholders)
├── svg_final/     # Post-processed final SVGs (finalize_svg.py output)
├── images/        # Image assets (user-provided + AI-generated)
├── notes/         # Speaker notes (.md files matching SVG names)
│   └── total.md   # Complete speaker notes document (before splitting)
├── templates/     # Project templates (if any)
└── *.pptx         # Exported PPT file
```
