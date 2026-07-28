# PPTX Transition Core

The shared transition core owns page-transition vocabulary, slide-advance
semantics, OOXML mutation, MCE preservation, package timing enablement, and
read-back validation for every PPTX route.

## 1. Ownership

| Concern | Owner |
|---|---|
| Page transition registry | scripts/pptx_transitions.py |
| In-slide object animation | scripts/pptx_animations.py |
| Generated PPTX adapter | svg_to_pptx/pptx_package/builder.py |
| Template Fill adapter | template_fill_pptx/transitions.py |
| Native Enhance adapter | native_enhance_pptx_core.py |
| Public workflow | references/animations.md |

**Hard rule**: adapters resolve route policy, then call the shared core. They
must not build, replace, or patch a transition with route-local XML or regex.

---

## 2. Domain Model

| Layer | Meaning | OOXML |
|---|---|---|
| Enter | How the current slide appears from the preceding slide | Native effect, Effect Options, and duration |
| Advance | How the current slide leaves for the next slide | advClick and advTm |

Enter policy:

| Policy | Behavior |
|---|---|
| preserve | Keep the source visual transition, including unknown extensions |
| replace | Write the requested supported effect |
| none | Write no visual effect |

Advance mode:

| Mode | Behavior |
|---|---|
| preserve | Keep source advClick and advTm |
| click | Click advance only |
| after | Timed advance only |
| both | Click or timed advance, whichever occurs first |
| narration | Timed advance from audio duration plus padding; click disabled |

**Hard rule**: enter=none may coexist with a timed advance. The valid result is
a timing-only p:transition with no visual-effect child.

---

## 3. Compatibility Contract

The native registry covers the complete current PowerPoint transition gallery:
12 Subtle effects, 29 Exciting effects, and 7 Dynamic Content effects. New
selection, sidecars, plans, conversion traces, help, and writers use only these
48 native keys.

Eight established low-level names remain valid at input boundaries. They
normalize to one native effect plus native `effect_options`; they are not a
second transition registry:

| Compatibility input | Native request |
|---|---|
| `strips` | `wipe` with `direction: right` |
| `circle` | `shape` with `shape: circle` |
| `diamond` | `shape` with `shape: diamond` |
| `plus` | `shape` with `shape: plus` |
| `newsflash` | `flash` |
| `pull` | `uncover` |
| `wedge` | `clock` with `style: wedge` |
| `wheel` | `clock` with `style: clockwise` |

Standard PresentationML effects use a direct `p:transition` carrier:

| Effect | Required primary child and attributes |
|---|---|
| fade | p:fade |
| push | p:push dir=r |
| wipe | p:wipe dir=r |
| split | p:split |
| cut | p:cut |
| random_bars | p:randomBar dir=vert |
| shape | p:circle |
| uncover | p:pull dir=r |
| cover | p:cover dir=r |
| dissolve | p:dissolve |
| checkerboard | p:checker |
| blinds | p:blinds dir=vert |
| clock | p:wheel spokes=1 |
| random | p:random |
| box | p:zoom |
| comb | p:comb |

Office 2010 effects use a `p14` Choice with a `p:fade` Fallback:

| Effect | Required primary child and attributes |
|---|---|
| reveal | p14:reveal dir=r |
| flash | p14:flash |
| ripple | p14:ripple |
| honeycomb | p14:honeycomb |
| glitter | p14:glitter |
| vortex | p14:vortex dir=r |
| shred | p14:shred dir=out |
| switch | p14:switch dir=r |
| flip | p14:flip dir=r |
| gallery | p14:gallery dir=r |
| cube | p14:prism dir=r |
| doors | p14:doors dir=vert |
| zoom | p14:warp dir=in |
| pan | p14:pan dir=r |
| ferris_wheel | p14:ferris dir=r |
| conveyor | p14:conveyor dir=r |
| rotate | p14:prism dir=r isContent=1 |
| window | p14:window |
| orbit | p14:prism dir=r isContent=1 isInverted=1 |
| fly_through | p14:flythrough |

Office 2012 effects use a `p15` Choice with a `p:fade` Fallback:

| Effect | Required primary child and attributes |
|---|---|
| fall_over | p15:prstTrans prst=fallOver invX=1 |
| drape | p15:prstTrans prst=drape invX=1 |
| curtains | p15:prstTrans prst=curtains |
| wind | p15:prstTrans prst=wind |
| prestige | p15:prstTrans prst=prestige |
| fracture | p15:prstTrans prst=fracture |
| crush | p15:prstTrans prst=crush |
| peel_off | p15:prstTrans prst=peelOff invX=1 |
| page_curl | p15:prstTrans prst=pageCurlSingle invX=1 |
| airplane | p15:prstTrans prst=airplane |
| origami | p15:prstTrans prst=origami |

`morph` uses `p159:morph option=byObject` in an Office 2015 Choice with a
`p:fade` Fallback. `none` is the explicit no-visual-effect input and therefore
is not a registry entry.

### 3.1 Native Effect Options

Use `effect_options` only with an explicit native `effect`. Omitted options use
the PowerPoint-authored `default` reported by `--describe-transition`:

| Effect | Supported options |
|---|---|
| `morph` | `morph_by`: `object`, `word`, `character` |
| `fade` | `style`: `smoothly`, `through_black` |
| `push`, `wipe`, `vortex`, `cube`, `pan`, `rotate`, `orbit` | `direction`: `left`, `right`, `up`, `down` |
| `split` | `orientation`: `horizontal`, `vertical`; `direction`: `out`, `in` |
| `reveal` | `direction`: `right`, `left`; `through_black`: boolean |
| `cut` | `through_black`: boolean |
| `random_bars`, `blinds`, `doors` | `orientation`: `vertical`, `horizontal` |
| `checkerboard` | `direction`: `across`, `down` |
| `comb`, `window` | `orientation`: `horizontal`, `vertical` |
| `shape` | `shape`: `circle`, `diamond`, `plus` |
| `uncover`, `cover` | `direction`: `left`, `right`, `up`, `down`, `up_left`, `up_right`, `down_left`, `down_right` |
| `fall_over`, `drape`, `wind`, `peel_off`, `airplane`, `origami` | `direction`: `right`, `left` |
| `page_curl` | `direction`: `right`, `left`; `pages`: `single`, `double` |
| `clock` | `style`: `clockwise`, `counterclockwise`, `wedge` |
| `ripple` | `origin`: `center`, `up_left`, `up_right`, `down_left`, `down_right` |
| `glitter` | `shape`: `diamond`, `hexagon`; `direction`: `right`, `left`, `up`, `down` |
| `shred` | `pattern`: `strips`, `rectangle`; `direction`: `out`, `in` |
| `switch`, `flip`, `gallery`, `ferris_wheel`, `conveyor` | `direction`: `right`, `left` |
| `box`, `zoom` | `direction`: `out`, `in` |
| `fly_through` | `direction`: `in`, `out`; `bounce`: boolean |
| All other native effects | No Effect Options |

Example:

~~~json
{
  "transition": {
    "effect": "page_curl",
    "effect_options": {
      "direction": "left",
      "pages": "double"
    },
    "duration": 0.6
  }
}
~~~

Inspect the exact contract, including compatibility desugaring:

~~~bash
python3 skills/ppt-master/scripts/pptx_animations.py --describe-transition page_curl
python3 skills/ppt-master/scripts/pptx_animations.py --describe-transition diamond
~~~

Read-back reports the canonical native effect, its complete effective options,
the raw OOXML child, and raw attributes. This makes option loss a validation
failure rather than a silent downgrade.

**Hard rule — no downgrade**:

- Never rename or remove an established effect.
- Never omit its established direction or split attributes.
- Reject an unknown requested effect; never substitute fade.
- Preserve an unknown source effect when the route selects preserve.
- An extension counts as successful only when the primary Choice contains the
  requested effect. A fallback alone is not success.

### 3.2 Deterministic Morph Identity

The generated route may add an explicit `slides.<destination>.morph` block to
bind direct-root SVG groups across adjacent slides. The sidecar stable key is
lowered to the same top-level `p:cNvPr@name="!!<key>"` on both final
Slide-local objects. This does not create an Animation Pane row and does not
change either object's numeric shape id.

The full plan is resolved before any SVG conversion so a source group named by
the following slide remains a stable top-level target. Names are written only
after flat/structured/preserve processing has finished; structured slide-shape
roster expectations are then refreshed. Package read-back requires:

- the declared source to be the immediately preceding public slide;
- exactly one `!!<key>` object on each side;
- the same OOXML object container type on both sides;
- Morph by object on the destination; and
- no structural target, same-slide name collision, group/key conflict, or
  undeclared shared `!!` name on a Morph edge.

Morph without an explicit pair block retains PowerPoint's automatic matching
behavior. Explicit pairing is generated-route authoring; direct-PPTX routes
continue to preserve existing object names and transition XML.

---

## 4. Route Mapping

| Route | Default enter | Default advance | Compatibility note |
|---|---|---|---|
| Generated PPTX CLI | fade, 0.4s | click | auto-advance maps to both |
| Recorded narration | Preserve resolved enter | narration | none remains visually none |
| Template Fill v1 | fade, 0.5s | click | keep preserves source; legacy advance_after maps to both |
| Native Enhance v1 | Confirmed plan effect | Confirmed timing module | Disabled transitions preserve unless the v1 plan explicitly selected none |

Template Fill and Native Enhance keep their v1 route defaults.
The public `create_pptx_with_native_svg` Python API also retains its legacy
0.5s default; the CLI explicitly passes 0.4s. Changing a default policy is a
separate migration decision.

---

## 5. OOXML Rules

**Slide child order**:

~~~text
p:cSld
p:clrMapOvr
p:transition or transition mc:AlternateContent
p:timing
p:extLst
~~~

One slide may contain at most one logical transition carrier:

- one direct p:transition; or
- one root-level mc:AlternateContent whose Choice/Fallback branches contain
  p:transition.

Mutation rules:

| Operation | Direct transition | AlternateContent |
|---|---|---|
| preserve | Leave unchanged | Leave wrapper and branches unchanged |
| advance-only | Patch direct attributes | Patch Choice and Fallback identically |
| replace | Replace the direct carrier | Remove the whole wrapper, then write one carrier |
| none | Remove visual carrier; retain timing-only carrier when needed | Remove the whole wrapper; retain timing-only carrier when needed |

**MCE prefix rule**: Requires and Ignorable values contain textual prefix
names. Serialization must retain bindings for those exact names. Renaming an
effect prefix without updating these attributes corrupts compatibility.

**Package timing rule**: when a route writes advTm, set
ppt/presProps.xml p:presentationPr/p:showPr useTimings=1. Do not write showPr
into ppt/presentation.xml.

---

## 6. Validation and Read-Back

Reject:

- unknown effect names;
- options without an explicit native effect;
- unknown option fields or values for the selected effect;
- non-finite values, including NaN and Infinity;
- duration less than or equal to zero;
- negative advance or narration padding;
- booleans passed as numeric API values;
- multiple logical transition carriers;
- unresolved MCE Requires or Ignorable prefixes.
- invalid forced-Morph adjacency, identity uniqueness, object type, or
  destination effect.

Read-back must report the canonical native effect and complete effective
options, while keeping the primary Choice child separate from the fallback. It
must also report raw effect attributes, carrier type, duration, click mode, and
automatic advance time. Package validation must run after writing, not only
before mutation.

Use inline smoke commands and gitignored projects/_smoke_* artifacts. Do not
add a tests directory or test_*.py files.
