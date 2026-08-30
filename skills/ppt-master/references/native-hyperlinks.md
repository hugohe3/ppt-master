# Native Hyperlink Specification

Authoring contract for PowerPoint-native click hyperlinks on complete objects and inline text runs.

## 1. Trigger and Ownership

**Trigger**: a user instruction, source fact, or page plan requires an external destination or a jump to another slide in the same deck.

| Layer | Ownership |
|---|---|
| Default Strategist | Record the linked text/object intent and exact target in the §IX page block; never invent or normalize an unknown destination |
| Default Executor | Choose the whole-object or inline carrier and author the canonical SVG anchor |
| Active Quick context | Both responsibilities directly |
| SVG-to-PPTX exporter | Validate the target, create the native relationship, and attach the click action |

**Hard rule — page content only**: hyperlinks are not a confirmation field, resource, manifest, or `spec_lock.md` entry. Missing or ambiguous targets return upstream; never substitute a search result or guessed URL.

---

## 2. Canonical SVG

| Intent | Canonical form |
|---|---|
| Whole object, image, button, or group | `<a href="https://example.com"><g>...</g></a>` |
| Inline text | `<text>Read <a href="https://example.com"><tspan>the guide</tspan></a>.</text>` |
| Same-deck jump | `href="#slide-3"` using the 1-based final slide roster |
| Imported shape-plus-run conflict | Importer-only `data-pptx-shape-hyperlink="..."` on the logical `<g>`, with standard inline anchors retained inside |

**Hard rule — one target syntax**: author SVG 2 `href` (import may read legacy `xlink:href`; generated SVG never writes both). Same-deck destinations use the exact `#slide-N` form inside the final roster. External destinations are absolute URIs with an explicit scheme and percent-encoded spaces; relative paths, arbitrary fragments, filesystem paths, and `data:` / `file:` / `javascript:` / `vbscript:` fail closed.

**Hard rule — inline run**: visible text sits in one or more `<tspan>` children inside the anchor; the anchor and its descendants own no `x`, `y`, `dx`, or `dy` — line positioning belongs to the enclosing line `<tspan>`. A linked inline formula is one leaf formula `<tspan>` inside the anchor and keeps its native math contract.

**Hard rule — whole-object hit area**: wrap at least one visible SVG element; no direct text or bare `<tspan>` in a shape anchor. A multi-object anchor links each exported leaf object; include an explicit background shape when gaps inside a button or card must also be clickable. Ordinary animation may target an outer top-level `<g>`, but a hyperlink-bearing group cannot also be an interactive `trigger_shape` — one click has one owner.

**Forbidden**: nested `<a>`; an anchor inside `defs`, metadata, geometry-detail, or a native-replacement subtree (a complete block formula or Chart/Table marker may be wrapped as one whole object, but its preview may not contain another anchor); authored `data-pptx-shape-hyperlink`, which PPTX import writes only when one source shape has both a whole-shape click and descendant run links, and which checker/export accept only on that logical group with at least one real inline `<a>` descendant.

---

## 3. Native Result and Preservation

Inline links become `a:rPr/a:hlinkClick`, whole-object links `p:cNvPr/a:hlinkClick` on each clickable leaf, each with an external hyperlink relationship; slide jumps add an internal slide relationship and `ppaction://hlinksldjump`. Supported PPTX import reconstructs the same canonical `<a href>` form.

**Hard rule — Edit Native PPTX preservation**: unchanged round-trip pages keep their hyperlink XML and relationships byte-for-byte; external links are preserved. With a `page_plan.json`, a same-deck jump is retargeted only when its source target maps unambiguously to one output page — omitted or repeated targets make `svg_to_pptx.py --roundtrip` fail rather than link to an orphan or wrong slide. New links on an edited page use this contract.

---

## 4. Exclusions and Validation

**Forbidden — unsupported action settings**: mouse-over links, custom shows, first/last/next/previous navigation, program or macro execution, OLE or file actions, and arbitrary `ppaction://` or relationship injection. An `actionButton*` preset stays visual geometry until wrapped in a supported anchor.

**Validation**: the final SVG checker validates carrier structure, target syntax, and slide range; export validates relationship type/mode and final roster membership. Unsupported PPTX click actions produce an import diagnostic; strict import fails rather than fabricating an SVG link.
