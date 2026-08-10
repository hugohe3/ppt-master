# Video-delivery Design Reference Manual

Conditional design guidance for presentations whose intended use is a recorded,
self-running, or video delivery.

**Trigger**: load this reference when the effective delivery purpose is video,
recorded narration, or unattended playback. Also load its script rules for an
explicit final/literal narration input. Speaker notes, animation, or audio
requested for an otherwise ordinary deck do not activate it alone. Explicit
video/MP4 delivery does; Quick additionally activates §3's direct-delivery
contract.

**Ownership**: this is a conditional Generate reference, not a profile or a new
artifact route. Default keeps its Strategist and confirmation flow; Quick keeps
its one-pass active-context flow. Existing notes, animation, audio, and native
PowerPoint export stages retain their schemas and commands.
When Beautify is active, its wording/page/order invariants still bind; apply
this reference only inside the design and motion freedom that profile permits.

---

## 1. Intake and Script State

Classify supplied spoken material before planning:

| Material | Treatment |
|---|---|
| Ordinary source or rough transcript | Use as source material; edit, condense, and reorganize under the selected route's normal content-divergence contract |
| Explicit final/literal narration script | Preserve every spoken word and its order; segment only at semantic scene boundaries |
| SRT used to generate new TTS | Preserve cue text when it is explicitly final; use source timecodes only as pacing evidence because the new synthesis timing becomes authoritative |
| SRT bound to an existing recording | Preserve its text/audio timing authority; do not regenerate TTS or pretend that one long recording was split automatically |
| Already page-separated final script | Preserve the supplied page boundaries unless the user explicitly permits restructuring |
| Target platform, canvas, or duration | Use the existing canvas registry; resolve scene granularity, page count, and notes length together |

**Hard rule — final means explicit**: freeze wording only when the user identifies
the script as final, literal, or verbatim. Never promote ASR output, subtitles,
or a draft transcript into a literal contract by inference.

**Default — semantic segmentation (may override for a user-authored page
plan)**: one scene represents one coherent visual state or mental-map step, not
one sentence, subtitle cue, or effect. Several cues may share a scene; one scene
may contain several ordered reveals.

**Final-script production input**: after the page roster is final but before SVG
authoring, write the resolved per-slide script once to `notes/total.md`. Use
`# Slide <number>` headings and `---` separators so the file can exist before SVG
filenames do; preserve each body segment verbatim. It is a production input, not
a storyboard or substitute Design Spec. Run `total_md_split.py` only after the
SVG roster exists.

---

## 2. Scene and Page Planning

Judge quality by reduced audience understanding cost, not spectacle. Resolve the
spoken argument, visible evidence, mental map, and motion job together before
choosing effects.

| Narrative relationship | Page treatment |
|---|---|
| Several lines explain one idea | Keep one page/scene and reveal only the semantic units needed for that explanation |
| One process or system persists | Retain its main roles and relative positions as a stable visual anchor |
| New evidence expands one part of a known map | Keep the map, enlarge or emphasize the active region, and de-emphasize context only as needed |
| The same object changes position, scale, containment, or state | Author compatible adjacent endpoints and use the Morph contract when motion is active |
| The audience must adopt a genuinely new mental map | Start a new composition and make the transition explicit |

**Default — stable visual anchors (may override when the subject resets)**:
within one explanation, keep recurring roles, relative positions, and governing
structure stable. Prefer moving, enlarging, revealing, or dimming within that
map over replacing the entire layout at every beat.

**Default — one semantic focus change per beat (may override for one inseparable
idea)**: several elements may change together only when they communicate one
unit. Do not change unrelated title, diagram, annotation, and footer regions at
the same moment merely to make the frame busier.

**Default — scene chrome earns its place (may override for navigation, identity,
attribution, or fidelity)**: for newly authored recorded, self-running, or video
scenes, do not carry a report-style fixed header, footer, or page number merely
by deck convention. Let the semantic title participate in the scene composition,
and omit nonessential running chrome especially on cover, ending, and breathing
scenes. Retain source or template chrome when the active profile's fidelity
boundary requires it, and retain new chrome when it genuinely orients the
audience or carries required identity or attribution.

**Default — screen for orientation, notes for speech (may override for literal
on-screen copy)**: place keywords, structure, evidence, and relationships on the
slide; keep full explanation in notes. Do not duplicate the narration script as
body copy.

**Page-count rule**: derive page count from semantic scenes, visual-state
endpoints, and target duration. Never derive it from subtitle-cue or sentence
count.

---

## 3. Default and Quick Planning Handoff

**Default**: Stage 1 confirms the existing open-text `delivery_context`; it does
not ask a separate video question. When the confirmed value identifies
recorded/self-running/video delivery, load this reference before authoring the
three Stage-2 whole solutions. Apply its scene grammar to every direction; it
does not add a style catalog or confirmation field. Record delivery context and
afterlife in §I, visible states and optional motion jobs in §IX, and script/notes
policy plus target duration in §X. When the final-script branch is active,
create the frozen `notes/total.md` after the approved roster/lock is final and
before Step 5 or split-mode handoff.

**Default — reading mode (may override for durable close reading)**: recorded
explanation leans `presentation`; choose `balanced` when close-reading afterlife
materially outweighs video delivery.

**Quick**: there is no Stage 1 or separate video-purpose confirmation. Explicit
video/recorded/self-running intent activates this reference after source
sufficiency is known and before the one-pass roster, resource, and motion
decisions; absent that intent, keep ordinary Quick behavior. Load the script
rules alone when an explicit final/literal narration will become notes/audio.
Keep the applicable scene grammar and final-script handling in active context.
A pre-SVG `notes/total.md` is an enabled production artifact, not a forbidden
planning checkpoint; Quick still creates no root Design Spec, lock,
confirmation payload, or storyboard.

**Hard rule — Quick direct video input**: when Quick must deliver a narrated
video or MP4 rather than only a deck for later recording, enable Speaker Notes,
Custom Animations, Narration Audio, and video export. Before P01, write the
complete per-scene narration to `notes/total.md` even when the agent authored
it. Treat it as page-design input; validate/finalize agent-authored wording after
the SVG roster and before audio. A supplied final/literal script remains
verbatim and requires visual repair instead.

**Production outcomes**:

| Need | Decision |
|---|---|
| Spoken delivery or a supplied final script | Enable Speaker Notes |
| User asks the workflow to synthesize narration | Enable Narration Audio; Speaker Notes is its dependency |
| Progressive reveal, continuing geometry, or timed emphasis materially aids explanation | Enable/load the appropriate animation capability |
| Quick directly delivers a narrated video or MP4 | Enable Speaker Notes, Custom Animations, Narration Audio, and video export; require timestamped page-local SRT |
| Video is manually narrated or static playback is sufficient | Keep Narration Audio and/or object animation off as applicable |

**Capability boundary**: a deck intended for later video use does not force
object animation or generated audio. Direct Quick narrated-video delivery uses
the mandatory row above. Explicit user instructions remain authoritative.

---

## 4. SVG, Notes, and Motion Realization

When §3 created `notes/total.md` before SVG, read it once before the first SVG
and design each page around its corresponding spoken segment. Give every
independently narrated or timed semantic unit a descriptive direct-root `<g
id>`; keep inseparable units grouped. Preserve a final/literal script exactly;
agent-authored direct-video narration may change only during its final-SVG
validation before audio.

**Hard rule — script/design consistency**: a final script is literal content.
If the finished visual page introduces an independent claim or relationship the
script does not explain, repair the page or return to planning; never rewrite or
pad the final script during the late notes pass. Conversely, every spoken idea
that requires visual orientation must have a visible state or deliberate
speech-only treatment.

**Motion readiness**: load `animations.md` before SVG authoring whenever the
plan needs compatible Morph endpoints or page/object-specific motion. Author
every required start/end state and real semantic group before the final checker;
post-processing cannot invent missing visual endpoints or target IDs.

**Motion restraint**: use transitions, reveals, emphasis, and Morph only for a
named communication job. There is no motion-coverage quota, and `effect: none`
remains valid. Auto-running narration uses `after-previous` / `with-previous`,
never `on-click`.

**Hard rule — Quick direct video synchronization**: load `animations.md` before
SVG authoring and create/validate canonical `animations.json` from real semantic
groups. After notes validation, export the base PPTX/report, use a
timestamp-capable provider to generate page audio/SRT, map each timed group in
`narration_timing.json`, derive `narration_animations.json`, re-export the
narrated PPTX, then export MP4. Author object identity, effect, and order before
audio; only narration-derived triggers/delays wait for SRT timing. An audio-only
provider cannot satisfy this branch.

**Sound effects**: add them only on explicit request and only from prepared,
project-local assets. Do not introduce sound search, trimming, or normalization
as an implicit video step.

**Production sequence**: after the final SVG check, validate any pre-SVG
narration against the visible pages; ordinary draft-source runs instead use the
final-SVG-grounded notes generation. Split notes, run triggered custom animation,
and export the canonical editable PPTX. Direct Quick video continues through
timestamped audio/SRT, narration synchronization, narrated PPTX, and MP4.

---

## 5. Delivery Boundary

**Canonical artifact**: the editable PPTX remains canonical. `generate-audio` owns provider/voice/rate
selection, page audio/SRT generation, semantic narration timing, narrated PPTX
export, and optional native PowerPoint video export.

**Conditional MP4**: run `powerpoint_video.py --check` only when MP4 delivery is
selected. If native Windows PowerPoint export is unavailable, keep the narrated
PPTX as the successful upstream artifact; do not substitute screenshots, HTML,
or a third-party renderer and call it equivalent.

**Current boundary**: importing and automatically splitting one long finished
recording is unsupported. Require page-level audio or an explicit page/time map;
otherwise deliver the designed deck and frozen notes without claiming audio
integration.
