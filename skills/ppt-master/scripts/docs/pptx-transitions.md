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
| Enter | How the current slide appears from the preceding slide | Transition effect child plus duration |
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

The Phase 1 registry preserves the established seven effects:

| Effect | Required child and attributes |
|---|---|
| fade | p:fade |
| push | p:push dir=r |
| wipe | p:wipe dir=r |
| split | p:split orient=horz dir=out |
| strips | p:strips dir=rd |
| cover | p:cover dir=r |
| random | p:random |

**Hard rule — no downgrade**:

- Never rename or remove an established effect.
- Never omit its established direction or split attributes.
- Reject an unknown requested effect; never substitute fade.
- Preserve an unknown source effect when the route selects preserve.
- A future PowerPoint extension counts as successful only when the primary
  Choice contains the requested effect. A fallback alone is not success.

---

## 4. Route Mapping

| Route | Default enter | Default advance | Compatibility note |
|---|---|---|---|
| Generated PPTX CLI | fade, 0.4s | click | auto-advance maps to both |
| Recorded narration | Preserve resolved enter | narration | none remains visually none |
| Template Fill v1 | fade, 0.5s | click | keep preserves source; legacy advance_after maps to both |
| Native Enhance v1 | Confirmed plan effect | Confirmed timing module | Disabled transitions preserve unless the v1 plan explicitly selected none |

Template Fill and Native Enhance keep their v1 route defaults in Phase 1.
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
- non-finite values, including NaN and Infinity;
- duration less than or equal to zero;
- negative advance or narration padding;
- booleans passed as numeric API values;
- multiple logical transition carriers;
- unresolved MCE Requires or Ignorable prefixes.

Read-back must report the primary Choice effect separately from the fallback.
It must also report carrier type, duration, click mode, and automatic advance
time. Package validation must run after writing, not only before mutation.

Use inline smoke commands and gitignored projects/_smoke_* artifacts. Do not
add a tests directory or test_*.py files.
