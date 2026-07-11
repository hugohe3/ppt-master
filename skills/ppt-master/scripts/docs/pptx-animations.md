# PPTX Animation Core

The shared animation core owns the entrance-effect vocabulary, trigger
semantics, OOXML timing writer, semantic read-back, and package validation for
PowerPoint OOXML. Per-element animation remains opt-in: generated PPTX export
defaults to `none`, exactly as before this validation upgrade.

## 1. Ownership

| Concern | Owner |
|---|---|
| Effect registry, timing writer, and read-back | `scripts/pptx_animations.py` |
| Sidecar parsing and SVG target discovery | `svg_to_pptx/animation_config.py` |
| SVG group-to-shape mapping | `svg_to_pptx/drawingml/converter.py` |
| Generated PPTX resolution and validation | `svg_to_pptx/pptx_package/builder.py` |
| Narration timing merge | `svg_to_pptx/pptx_package/narration.py` |
| Public authoring contract | `references/animations.md` |
| Customization workflow | `workflows/customize-animations.md` |

**Hard rule**: only the generated SVG-to-PPTX route writes object entrance
animations. Direct-PPTX routes preserve source animations and run structural
package validation; they do not resolve or author animation effects.

---

## 2. Domain Model

One resolved animation-pane row contains these fields:

| Field | Meaning |
|---|---|
| Target | Positive PowerPoint shape id written to `p:spTgt@spid` |
| Effect | One exact registry tuple: filter, `presetID`, and `presetSubtype` |
| Trigger | `on-click`, `with-previous`, or `after-previous` |
| Duration | Finite positive schedule duration; filter effects serialize it as behavior duration |
| Delay | Finite non-negative offset used by `after-previous` |
| Order | Positive integer sidecar order; ties retain stable SVG order |

Modes resolve before XML writing:

| Mode | Resolution |
|---|---|
| `auto` | Deterministic semantic mapping from the SVG group id |
| `mixed` | Deterministic legacy cycle |
| `random` | Stable seeded choice from the legacy pool |
| `none` | No entrance sequence |

The same effective input produces the same `random` choices. When enabled,
`--conversion-trace` records each resolved row and effect, so a generated deck
can be audited without replaying the resolver.

---

## 3. Compatibility Contract

The registry preserves these established 22 tuples exactly:

| Key | `p:animEffect@filter` | `presetID` | `presetSubtype` |
|---|---|---:|---:|
| `appear` | none | 1 | 0 |
| `fade` | `fade` | 10 | 0 |
| `fly` | `slide(fromBottom)` | 2 | 4 |
| `cut` | `slide(fromLeft)` | 42 | 8 |
| `zoom` | `image` | 23 | 0 |
| `wipe` | `wipe(left)` | 22 | 1 |
| `split` | `barn(inVertical)` | 16 | 21 |
| `blinds` | `blinds(horizontal)` | 3 | 10 |
| `checkerboard` | `checkerboard(across)` | 5 | 6 |
| `dissolve` | `dissolve` | 9 | 0 |
| `random_bars` | `randombar(horizontal)` | 14 | 10 |
| `peek` | `wipe(down)` | 12 | 4 |
| `wheel` | `wheel(4)` | 21 | 0 |
| `box` | `box(in)` | 4 | 0 |
| `circle` | `circle(in)` | 6 | 0 |
| `diamond` | `diamond(in)` | 8 | 0 |
| `plus` | `plus(in)` | 13 | 0 |
| `strips` | `strips(downRight)` | 18 | 12 |
| `wedge` | `wedge` | 20 | 0 |
| `stretch` | `stretch(across)` | 17 | 0 |
| `expand` | `stretch(across)` | 50 | 0 |
| `swivel` | `wheel(1)` | 19 | 0 |

`cut` is a legacy public key. Compatibility promises the tuple above; it does
not infer a different semantic name from external preset-id tables.

**Hard rule — no downgrade**:

- Keep the 22 established tuples byte-for-byte equivalent in meaning.
- Reject an unknown effect, mode, or trigger; never substitute another value.
- Reject booleans and non-finite, out-of-range, or invalidly ordered values.
- Reject a missing slide, missing group, or structural-layer target.
- Keep the generated-route default at `none`; validation does not opt a deck in.

---

## 4. Target Resolution

Generated object animation targets top-level SVG content groups. Explicit SVG
semantics are authoritative; the group-id chrome heuristic is only a fallback
for marker-free legacy SVGs.

| Target state | Behavior |
|---|---|
| Ordinary content group | Animatable |
| Legacy chrome-like id | Skipped unless explicitly named in `animations.json` |
| Explicit sidecar group override | May override only the legacy chrome-name heuristic |
| `data-pptx-layer` or explicit static role/placeholder | Structural and never animatable |

An explicit sidecar entry cannot turn a Master/Layout/Slide structural layer or
an explicitly marked static page-frame role/placeholder into an animation
target. This boundary preserves PPTX structure even when a legacy id resembles
content.

---

## 5. OOXML Rules

The writer emits one root-level `p:timing` after `p:transition` and before
`p:extLst`. Its animation tree contains a `tmRoot`, one `mainSeq`, unique
`p:cTn@id` values, and `p:spTgt` references to shapes on the same slide.

Trigger mapping:

| Public trigger | Entrance `p:cTn@nodeType` |
|---|---|
| `on-click` | `clickEffect` |
| `with-previous` | `withEffect` |
| `after-previous` | `afterEffect` |

The writer does not emit `p:bldP` for grouped content or pictures. Microsoft
defines `p:bldP@spid` for a text-bearing `p:sp`; using it for `p:grpSp` or
`p:pic` creates an invalid build reference. Package validation still accepts a
valid source `p:bldP` that targets a text-bearing shape.

Direct-PPTX preserve mode also tolerates an unchanged legacy `p:bldP` that
targets an existing group/picture. Earlier PPT Master exports wrote this form;
the direct routes fingerprint and preserve it instead of blocking those decks.
New generated output never writes it, and generated-package validation remains
strict.

`appear` is the visibility-flip exception: its `p:set` behavior is always 1ms.
The configured positive duration remains the row's scheduling span used when
computing the next `after-previous` offset; read-back verifies the 1ms behavior
and the resulting timeline offset separately.

---

## 6. Validation and Read-Back

Generated export reads every slide back before packaging and compares each
requested row with the serialized result:

- row count and row order;
- trigger and shape target;
- resolved effect key, filter, `presetID`, and `presetSubtype`;
- serialized behavior duration and computed timeline offset (`appear` uses the
  1ms exception above).

After packaging, validation scans every slide part for root timing placement,
duplicate or malformed `p:cTn` ids, missing `p:spTgt` shapes, invalid build
targets, and unsupported generated effect tuples. A mismatch fails export
before the requested output file replaces an existing deck.

Narration injection parses and merges the slide DOM. It adds audio timing under
the existing `tmRoot` child list, allocates fresh time-node ids, and preserves
the object entrance sequence. It does not replace an existing `p:timing` tree.
The merge accepts only a direct `p:sld/p:timing` source tree; a timing tree
wrapped in `mc:AlternateContent` or another non-root container fails safely
instead of being rewritten or duplicated.

Direct-PPTX routes run the structural package validator with generated-effect
enforcement disabled. This permits preservation of source/extension effects and
legacy group build rows while still rejecting corrupt timing IDs or missing
targets. Template fill and native enhancement fingerprint the source
object-animation tree before and after their allowed edits; any semantic change
fails. These routes have no object-animation write ownership.

---

## 7. Compatibility Scope

The compatibility contract covers PowerPoint OOXML and PowerPoint read-back.
Other presentation applications may interpret timing trees or filter values
differently; the exporter does not make an unconditional Keynote guarantee.

Official references:

- [Microsoft animation-filter implementation notes](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/a96dab70-2e72-4319-928d-0eb4b275ce58)
- [Microsoft `p:bldP` implementation restrictions](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/40d17b6d-30c0-4c10-b042-b2597824a820)
- [Open XML SDK time-node values](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.timenodevalues?view=openxml-3.0.1)
- [Open XML SDK shape target](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.shapetarget?view=openxml-3.0.1)

See [`pptx-transitions.md`](./pptx-transitions.md) for the symmetric page-motion
core, MCE handling, and slide-advance contract.
