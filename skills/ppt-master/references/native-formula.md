# Native Formula Specification

Shared authoring contract for editable PowerPoint math generated from exact
LaTeX, either inline in Slide-local prose or as a standalone block.

## 1. Trigger and Ownership

**Trigger**: A page contains structural mathematical notation such as a
fraction, radical, integral, n-ary expression, limit, matrix, delimiter
construction, accent, or complex script.

| Layer | Ownership |
|---|---|
| Default Strategist | Record exact mathematical content as a canonical delimiter-free LaTeX expression body; do not classify its implementation |
| Default Executor | Decide ordinary text versus inline native math versus block native math, then author the selected marker and SVG preview |
| Active Quick context | Perform both content and authoring responsibilities directly |
| SVG-to-PPTX exporter | Compile marker LaTeX to editable Office Math and replace only the registered preview |

| Content form | Authoring choice |
|---|---|
| Short variables, percentages, simple assignments, or notation such as `O(n log n)` | Ordinary editable SVG text |
| One-line structural math embedded in prose | Inline native marker |
| Matrix, `cases`, `aligned`, multiline derivation, or standalone high-structure expression | Block native marker |

The Strategist's `Mathematical content` field does not pre-decide this choice.
Formula handling is not a user-confirmed policy, image resource, manifest, or
`spec_lock.md images` entry.

---

## 2. Canonical Markers

### 2.1 Inline formula

```xml
<text x="120" y="240" font-size="28" fill="#173B57">
  The ratio <tspan data-pptx-inline-formula="\frac{a_i}{b_i}">aᵢ/bᵢ</tspan> remains stable.
</text>
```

**Hard rule — one leaf run**: Put non-empty LaTeX directly in
`data-pptx-inline-formula` on a leaf `<tspan>`. Canonical authoring omits outer
`$...$`, `$$...$$`, `\(...\)`, and `\[...\]` delimiters, though the compiler
accepts and removes one complete outer pair. Give that `<tspan>` one non-empty
direct preview string with no leading/trailing whitespace, no child element,
and no `x`, `y`, `dx`, `dy`, or paragraph-layout metadata; spacing belongs to
the surrounding text. The marker inherits its computed size and visible solid
fill; exported math uses the project text language and Cambria Math. Local
`\color` / `\textcolor` scopes override the marker fill on both selectable
formula runs and non-selectable structural controls. `\boldsymbol` / `\bm`
also applies its bold-italic style to structural control glyphs. Neither form
changes unrelated marker defaults.

**Hard rule — Slide-local ordinary text only**: Do not place an inline marker
inside a structured Layout placeholder, a Master/Layout layer, imported
preserved `txBody`, geometry transport subtree, another inline marker, or any
`data-pptx-replace-with` subtree. Export keeps the surrounding text runs in the
same `a:p` and replaces only the marker run with `a14:m > m:oMath`.

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

**Hard rule — block metadata is truth**: Write one direct
`<metadata type="application/json">` child with non-empty `latex`, `display:
block`, `font_size` in `(0, 400]`, a visible `color`, and `align:
left|center|right`. Use the same canonical delimiter-free form described above.
Give the group finite `data-pptx-x/y`, positive `data-pptx-width/height`, and
matching root-coordinate `data-pptx-bounds`. Export replaces the complete group
with `a14:m > m:oMathPara > m:oMath`.

**Hard rule — preview is SVG, never fallback**: Make every marker preview
semantically equivalent with ordinary SVG text/shapes/lines/paths. Do not use
`<image>`, `<foreignObject>`, visible raw LaTeX, or another runtime renderer.
The exporter discards the registered preview and emits no picture branch.

---

## 3. Source, Failure, and Validation

**Forward input profile**: The compiler implements every explicitly named
LaTeX-to-OMML input and behavior in Microsoft's documented
[Microsoft 365 LaTeX profile](https://learn.microsoft.com/en-us/office/math/latex)
(Windows 2606 / Mac 16.110) and
[mhchem profile](https://learn.microsoft.com/en-us/office/math/latex.mhchem)
(Windows 2605 / Mac 16.109). This includes outer delimiters, all listed symbols
and relations, fractions and binomials, roots, right and left scripts,
delimiters and `\middle`, accents, bars and group characters, limits, all 21
listed n-ary operators, standard/custom functions, matrices and equation-array
environments, CD diagrams, fonts and local colors, boxes and phantoms, spacing,
global 0–9 argument macros, and the documented `\ce` chemistry grammar. The
closed command tables in `scripts/svg_to_pptx/native_objects/formula_profile.py`
are the executable vocabulary; the public compiler facade and OMML structure
gate live in `scripts/svg_to_pptx/native_objects/formula_compiler.py` and
`scripts/svg_to_pptx/native_objects/formula_omml.py`. Microsoft's open-ended
“etc.” wording for additional relation aliases does not define undisclosed
names; only explicitly named commands and retained project aliases are
contractual.

**Native normalization**: `\dfrac` / `\tfrac`, `\dbinom` / `\tbinom`, and
continued-fraction alignment normalize to the corresponding OMML structure;
explicit big-delimiter grades become auto-sizing delimiters; `\mathscr`
normalizes to `\mathcal`; `smallmatrix` normalizes to `matrix`; PowerPoint array
columns become centered; style/size commands and equation tags are accepted but
not stored. Color is stored in generated formula runs and structural control
properties. No reverse OMML-to-LaTeX build-down is implemented by PPT Master.

**Fail-closed boundary**: Input containing unknown commands or environments,
Microsoft's explicitly unsupported commands, unsupported mhchem arrows,
unescaped `%` comments, invalid macros, or any resource-limit overflow blocks
conversion. This is stricter than Microsoft 365's literal-text passthrough and
macro-limit behavior: PPT Master never leaks unresolved LaTeX into a released
slide.

**Hard rule — repair LaTeX upstream**: Unsupported source or an invalid marker
blocks the page. Rewrite within the documented profile without changing the
planned mathematics; otherwise return it to the content owner. Never substitute
a PNG, flatten structural math into ordinary text, hand-write OMML, or leave raw
LaTeX visible.

**Compatibility boundary**: The generated package uses standard editable Office
Math and retains the PowerPoint 2010+ package target. The executable profile is
pinned to the Microsoft documentation versions above. Repository verification
covers compilation, OMML structure, and PPTX packaging; it is not a complete
Microsoft 365 UI rendering/editability certification. Earlier PowerPoint
versions are not the source-profile baseline. WPS, Keynote, LibreOffice, and
other clients receive no embedded formula fallback and are outside the
rendering/editability contract.

**Validation**: The first-page/final SVG checker validates every marker and
compiles its LaTeX before release; native export repeats validation.
