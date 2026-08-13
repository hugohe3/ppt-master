# Native Hyperlink Specification

Shared authoring contract for PowerPoint-native click hyperlinks on complete
objects and inline text runs.

## 1. Trigger and Ownership

**Trigger**: A user instruction, source fact, or page plan requires an external
destination or a jump to another slide in the same deck.

| Layer | Ownership |
|---|---|
| Default Strategist | Record the linked text/object intent and exact target in the applicable §IX page block; never invent or normalize an unknown destination |
| Default Executor | Choose the whole-object or inline carrier and author the canonical SVG anchor |
| Active Quick context | Perform both content and authoring responsibilities directly |
| SVG-to-PPTX exporter | Validate the target, create the native relationship, and attach the click action |

**Hard rule — page content only**: Hyperlinks are not a confirmation field,
resource, manifest, or `spec_lock.md` entry. Missing or ambiguous targets return
upstream; do not substitute a search result or guessed URL.

---

## 2. Canonical SVG

| Intent | Canonical form |
|---|---|
| Whole object, image, button, or group | `<a href="https://example.com"><g>...</g></a>` |
| Inline text | `<text>Read <a href="https://example.com"><tspan>the guide</tspan></a>.</text>` |
| Same-deck jump | `href="#slide-3"` using the 1-based final slide roster |
| Imported shape-plus-run conflict | Importer-only `data-pptx-shape-hyperlink="..."` on the logical `<g>`, with standard inline anchors retained inside |

**Hard rule — one target syntax**: Author SVG 2 `href`. Import may read legacy
`xlink:href`, but generated SVG never writes both. Same-deck destinations use
the exact `#slide-N` form and must resolve inside the final roster. External
destinations are absolute URIs with an explicit scheme; percent-encode spaces.
Relative paths, arbitrary fragments, filesystem paths, and `data:`, `file:`,
`javascript:`, or `vbscript:` destinations fail closed.

**Hard rule — inline run**: Put visible text in one or more `<tspan>` children
inside the anchor. The anchor and its descendants own no `x`, `y`, `dx`, or
`dy`; line positioning belongs to the enclosing line `<tspan>`. A linked inline
formula uses one leaf formula `<tspan>` inside the anchor and retains its native
math contract.

**Hard rule — whole-object hit area**: Wrap at least one visible SVG element;
do not put direct text or a bare `<tspan>` in a shape anchor. A multi-object
anchor links each exported leaf object. Include an explicit background shape
when gaps inside a button or card must also be clickable.

Ordinary entrance, emphasis, motion-path, exit, and Morph animation may target
an outer top-level `<g>`. A hyperlink-bearing group cannot also serve as an
interactive `trigger_shape`; use a separate trigger so one click has one owner.

**Forbidden — ambiguous ownership**: Do not nest `<a>` elements or place an
anchor inside `defs`, metadata, geometry-detail, or a native-replacement
subtree. A complete block formula or native Chart/Table marker may be wrapped
as one whole object; its preview descendants may not contain another anchor.

**Forbidden — authored transport metadata**: Never author
`data-pptx-shape-hyperlink`. PPTX import uses it only when one source shape has
both a whole-shape click and descendant run links, because standard SVG cannot
nest their two anchors. Checker/export accept it only on that logical group
with at least one real inline `<a>` descendant, then restore both native click
levels. Every ordinary whole-object link uses the standard outer `<a href>`.

---

## 3. Native Result and Preservation

| Carrier / target | Native result |
|---|---|
| Inline external link | `a:rPr/a:hlinkClick` plus an external hyperlink relationship |
| Whole-object external link | `p:cNvPr/a:hlinkClick` on each clickable leaf plus one shared external relationship |
| Inline or whole-object slide jump | The same click carrier plus an internal slide relationship and `ppaction://hlinksldjump` |
| Supported PPTX import | Reconstruct the same canonical SVG `<a href>` form |

**Hard rule — Fill Native preservation**: Preserve external links. Retarget a
same-deck jump only when its source target maps unambiguously to one output
slide; omitted or duplicated targets fail closed instead of linking to an
orphan or wrong slide.

**Hard rule — Enhance Native preservation**: Preserve existing hyperlink XML
and relationships unchanged. This route does not use the SVG authoring contract
to add new links.

---

## 4. Exclusions and Validation

**Forbidden — unsupported action settings**: Mouse-over links, custom shows,
first/last/next/previous navigation actions, program or macro execution, OLE or
file actions, and arbitrary `ppaction://` or relationship injection are outside
this contract. An `actionButton*` preset remains visual geometry until wrapped
in an ordinary supported hyperlink anchor.

**Validation**: The final SVG checker validates carrier structure, target
syntax, and slide range. Export validates relationship type/mode and final
presentation-roster membership. Unsupported PPTX click actions produce an
import diagnostic; strict import fails rather than fabricating an SVG link.
