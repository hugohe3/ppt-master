# Native Formula Specification

Authoring contract for editable PowerPoint math generated from exact LaTeX, inline in Slide-local prose or as a standalone block. Compiler profile, normalization, reverse import, and compatibility live in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md#native-formula-compiler).

## 1. Trigger and Ownership

**Trigger**: a page contains structural mathematical notation — fraction, radical, integral, n-ary expression, limit, matrix, delimiter construction, accent, or complex script.

| Layer | Ownership |
|---|---|
| Default Strategist | Record exact mathematical content as a canonical delimiter-free LaTeX expression body; do not classify its implementation |
| Default Executor | Decide ordinary text versus inline versus block native math, then author the marker and SVG preview |
| Active Quick context | Both responsibilities directly |
| SVG-to-PPTX exporter | Compile marker LaTeX to editable Office Math and replace only the registered preview |

| Content form | Authoring choice |
|---|---|
| Short variables, percentages, simple assignments, notation such as `O(n log n)` | Ordinary editable SVG text |
| One-line structural math in prose whose native-height envelope fits the reserved row/module space | Inline marker |
| Matrix, `cases`, `aligned`, multiline derivation, standalone high-structure expression, or vertically expanding math that cannot fit its prose row | Block marker |

Formula handling is not a user-confirmed policy, image resource, manifest, or `spec_lock.md images` entry.

---

## 2. Canonical Markers

### 2.1 Inline formula

```xml
<text x="120" y="240" font-size="28" fill="#173B57">
  The ratio <tspan data-pptx-inline-formula="\frac{a_i}{b_i}">aᵢ/bᵢ</tspan> remains stable.
</text>
```

**Hard rule — one leaf run**: non-empty delimiter-free LaTeX in `data-pptx-inline-formula` on a leaf `<tspan>` (the compiler strips one complete outer `$…$` / `$$…$$` / `\(…\)` / `\[…\]` pair) with one non-empty direct preview string, no surrounding whitespace, no child element, and no `x`, `y`, `dx`, `dy`, or paragraph-layout metadata — spacing belongs to the surrounding text. The marker inherits its computed size and visible solid fill; local `\color` / `\textcolor` and `\boldsymbol` / `\bm` scopes apply to formula runs and structural control glyphs. Exported math uses the project text language and Cambria Math.

**Hard rule — Slide-local ordinary text only**: never inside a structured Layout placeholder, Master/Layout layer, imported preserved `txBody`, geometry transport subtree, another inline marker, or a `data-pptx-replace-with` subtree. Export keeps the surrounding runs in the same `a:p` and replaces only the marker run with `a14:m > m:oMath`.

**Hard rule — reserve native height**: the parsed formula structure, not its flat preview, is vertical layout truth. Keep adjacent content outside the native ascent/descent of fractions, radicals, nested scripts, n-ary limits, and accents; exporter and checker use the same envelope. If the prose row or module cannot reserve that space, isolate the formula line or use the block marker.

### 2.2 Block formula

```xml
<g id="quadratic-formula" data-pptx-replace-with="formula"
   data-pptx-x="190" data-pptx-y="245"
   data-pptx-width="900" data-pptx-height="180"
   data-pptx-bounds="190 245 900 180">
  <metadata type="application/json"><![CDATA[
    {"latex":"\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}",
     "display":"block","font_size":42,"color":"#173B57","align":"center"}
  ]]></metadata>
  <text x="640" y="345" text-anchor="middle"
        font-size="42" fill="#173B57">(-b ± √(b²−4ac)) / 2a</text>
</g>
```

**Hard rule — block metadata is truth**: one direct `<metadata type="application/json">` child with non-empty `latex`, `display: block`, `font_size` in `(0, 400]`, a visible `color`, and `align: left|center|right`; finite `data-pptx-x/y`, positive `data-pptx-width/height`, and matching root-coordinate `data-pptx-bounds`. Export replaces the whole group with `a14:m > m:oMathPara > m:oMath`.

**Hard rule — preview is SVG, never fallback**: every preview is semantically equivalent ordinary SVG text/shapes/lines/paths — no `<image>`, `<foreignObject>`, visible raw LaTeX, or runtime renderer. The exporter discards the preview and emits no picture branch.

---

## 3. Source, Failure, and Validation

**Accepted input**: every explicitly named command in Microsoft's documented [Microsoft 365 LaTeX profile](https://learn.microsoft.com/en-us/office/math/latex) and [mhchem profile](https://learn.microsoft.com/en-us/office/math/latex.mhchem) — symbols, fractions and binomials, roots, scripts, delimiters and `\middle`, accents, limits, n-ary operators, functions, matrix and equation-array environments, CD diagrams, fonts and local colors, boxes and phantoms, spacing, 0–9 argument macros, `\ce` chemistry. Unknown commands or environments, Microsoft's explicitly unsupported commands, unsupported mhchem arrows, unescaped `%` comments, invalid macros, and resource-limit overflow block conversion: PPT Master never leaks unresolved LaTeX into a released slide.

**Hard rule — repair LaTeX upstream**: unsupported source or an invalid marker blocks the page. Rewrite within the profile without changing the planned mathematics, or return it to the content owner. Never substitute a PNG, flatten structural math into ordinary text, hand-write OMML, or leave raw LaTeX visible.

**Validation**: the first-page/final SVG checker validates every marker, compiles its LaTeX, and applies the shared native-height envelope to page/module text bounds; native export repeats validation and uses that envelope for the generated text frame. Output is standard editable Office Math for PowerPoint 2010+; WPS, Keynote, and LibreOffice receive no embedded fallback and are outside the rendering/editability contract.
