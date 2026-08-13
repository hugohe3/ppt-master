# Native Formula Specification

Shared authoring contract for standalone editable PowerPoint formulas generated
from exact LaTeX metadata.

## 1. Trigger and Ownership

**Trigger**: A page contains structural mathematical notation such as a
fraction, radical, integral, n-ary expression, limit, matrix, multiline
derivation, delimiter construction, accent, or complex script.

| Layer | Ownership |
|---|---|
| Default Strategist | Record exact mathematical content as a delimiter-free LaTeX expression body; do not classify or choose its implementation |
| Default Executor | Decide ordinary inline text versus a structural block; for a block, transfer that exact expression into metadata and author the marker plus SVG preview |
| Active Quick context | Perform both content and authoring responsibilities directly |
| SVG-to-PPTX exporter | Compile marker LaTeX to editable Office Math and replace the preview subtree |

Executor normally keeps short variables, percentages, simple assignments, and
notation such as `O(n log n)` as ordinary editable SVG text. The Strategist's
`Mathematical content` field does not pre-decide that classification. Formula
handling is not a user-confirmed policy, image resource, manifest, or
`spec_lock.md images` entry.

---

## 2. Canonical Marker

```xml
<g id="quadratic-formula"
   data-pptx-replace-with="formula"
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

**Hard rule — metadata is truth**: Write one direct
`<metadata type="application/json">` child with non-empty `latex`. Its value is
the expression body only: omit `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`
source delimiters. Current authoring uses `display: block`; `font_size` is
`> 0` and `<= 400` px, `color` is visible, and `align` is `left`, `center`, or
`right`.
Give the group finite `data-pptx-x/y`, positive `data-pptx-width/height`, and
matching root-coordinate `data-pptx-bounds`. The exporter always activates
formula replacement; `--native-charts-and-tables` does not control it.

**Supported subset**: basic text, numbers, operators, Greek/symbol commands,
fractions, radicals, scripts, `\sum` / `\prod` / `\int` with limits, `\left` /
`\right` delimiters, matrix variants, `cases`, `aligned`, text/math styles,
accents, and spacing. Unknown commands or environments fail closed.

**Hard rule — SVG children are preview only**: Author a semantically equivalent
preview with ordinary SVG text/shapes/lines/paths. Do not use `<image>`,
`<foreignObject>`, raw LaTeX text, or another runtime renderer. PPTX export
discards the marker's visible children and inserts one editable Office Math
object; the preview is not packaged as a fallback.

**Compatibility boundary**: Native formula output targets Microsoft PowerPoint
2010+ Office Math. The ordinary child subtree keeps the SVG preview readable,
but a PPTX opened in WPS, Keynote, LibreOffice, or another non-PowerPoint
renderer has no embedded formula fallback and is not guaranteed to display it.

---

## 3. Failure and Validation

**Hard rule — repair LaTeX upstream**: An unsupported command, invalid marker,
or compiler/checker failure blocks the page and returns it from validation to
authoring. Executor rewrites the delimiter-free expression with the supported
LaTeX subset without changing the planned mathematics; if that cannot preserve
the content, return it to the content owner for correction. Never substitute a
PNG, flatten structural math into ordinary text, hand-write OMML, or leave raw
LaTeX visible.

**Validation**: The first-page/final SVG checker validates the marker and
compiles its LaTeX before release; native export repeats validation.
