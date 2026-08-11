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

**Default — quality follows purpose (may override)**: explanation prioritizes
understanding; promotion or brand work may prioritize emotion, recall, or
impact. Give every change a communication job.

| Narrative relationship | Page treatment |
|---|---|
| Several lines explain one idea | Keep one page/scene and reveal only the semantic units needed for that explanation |
| One system persists | Before roster/notes freeze, derive states from the prior composition; keep orienting cues and change the semantic delta |
| New evidence expands a known map | Retain orienting cues; adapt the active region and context as needed |
| The same object changes position, scale, containment, or state | Consider compatible Morph endpoints when movement improves orientation |
| The audience must adopt a genuinely new mental map | Start a new composition and make the transition explicit |

**Default — stable visual anchors (may override when the mental map resets)**:
within one explanation, preserve recognizable roles, relationships, or spatial
cues. Position, scale, and style may change while identity and orientation
remain legible; reset for a new map.

**Default — one semantic focus change per beat (may override for one inseparable
idea)**: change several elements together only for one communication unit. Do
not alter unrelated regions merely for busyness.

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

**Page-count rule**: derive page/notes boundaries from scenes, mental-map arcs,
endpoints, and duration—not cues or sentences. Profile-fixed count/order/content,
including 1:1/fidelity, permits only existing-neighbor evaluation; never alter
those invariants for motion.

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

**Hard rule — Quick video Custom Animations**: when Quick generates a PPTX for
recorded, self-running, or video delivery, enable Custom Animations before SVG
authoring and complete the custom-animation stage before base export. Use
semantic groups and page-specific choreography; deck-wide `-a auto` and page
transitions do not satisfy this requirement. Individual pages or groups may
remain static, so this is not an animation-coverage quota. A validated
`animations.json` is required unless the user explicitly requests static or
page-transition-only playback.

**Mandatory — Quick direct video input**: when Quick must deliver a narrated
video or MP4 rather than only a deck for later recording, enable Speaker Notes,
Narration Audio, and video export; write the complete per-scene narration to
`notes/total.md` before P01 and use it as page-design input. After the SVG
roster, only agent-authored wording may be finalized; final/literal input remains
verbatim. Before audio, complete the required Custom Animations configuration
and decide whether narration governs any group timing.

**Production outcomes**:

| Need | Decision |
|---|---|
| Spoken delivery or a supplied final script | Enable Speaker Notes |
| User asks the workflow to synthesize narration | Enable Narration Audio; Speaker Notes is its dependency |
| Progressive reveal, continuing geometry, or timed emphasis materially aids explanation | Enable/load the appropriate animation capability |
| Quick generates a PPTX for recorded, self-running, or video delivery | Enable Custom Animations before SVG authoring and validate `animations.json` before base export |
| Quick directly delivers a narrated video or MP4 | Also enable Speaker Notes, Narration Audio, and video export; resolve narration-governed timing before audio, requiring timestamped page-local SRT for cue sync or subtitle delivery |
| The user explicitly requests static playback or disables object motion | Keep object animation off; retain the remaining notes/audio/video outcomes as requested |

**Capability boundary**: Default generation does not force object animation or
generated audio merely because a deck may later be recorded. Quick with an
effective recorded/self-running/video delivery purpose does require Custom
Animations, while explicit user instructions for static or
page-transition-only playback remain authoritative. This requirement selects
the capability, not motion coverage or one effect for every page.

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

**Mandatory when narration governs object motion**: before SVG authoring, load
`animations.md` and preserve real semantic groups; before audio, create and
validate canonical `animations.json`. After the base PPTX/report and timestamped
page audio/SRT, map timed groups in `narration_timing.json`, derive
`narration_animations.json`, and export the narrated PPTX/MP4. Only derived
triggers/delays wait for SRT; object identity, effect, and order do not. `-a
auto` or inherited fixed stagger is not semantic synchronization. For an
explicit user-selected static/page-transition-only Quick exception, or for
ordinary Default narration-independent deck-wide motion, omit these sidecars
and the object-sync claim.

**Sound effects**: exclude them from this pass and planning artifacts. After
final SVG/motion, animation post-processing owns on-demand selection and native
PPTX configuration; otherwise remain silent. For direct narrated MP4 delivery,
`generate-audio` additionally owns the triggered post-export mix when the final
resolved motion contains sound cues. Video gain and limiting never enter
`animations.json`.

**Production sequence**: after the final SVG check, validate any pre-SVG
narration against the visible pages; ordinary draft-source runs instead use the
final-SVG-grounded notes generation. Split notes, execute the resolved motion
path, and export the editable PPTX. Direct Quick video continues
through audio and, when required, timestamped SRT. Custom Animations use the
narrated-sidecar flow when narration governs group timing;
narration-independent custom motion exports its canonical timing without an
object-sync claim before the narrated PPTX and MP4.

---

## 5. Delivery Boundary

**Canonical artifact**: the editable PPTX remains canonical. `generate-audio`
owns provider/voice/rate selection, page audio/SRT generation, semantic
narration timing, narrated PPTX export, optional native PowerPoint video export,
and the triggered sound-effects mix for direct MP4 delivery.

**Conditional MP4**: run `powerpoint_video.py --check` only when MP4 delivery is
selected. If native Windows PowerPoint export is unavailable, keep the narrated
PPTX as the successful upstream artifact; do not substitute screenshots, HTML,
or a third-party renderer and call it equivalent.

**Hard rule — native MP4 sound boundary**: PowerPoint's native encoder is the
visual-animation and narration source, but it does not reliably include
transition or object-animation sounds in the MP4 audio track. When the final
narrated trace and PPTX contain sound cues, treat that native MP4 as a raw
intermediate and run `video_sound_mix.py`; only its verified mixed MP4 is the
sound-enabled video deliverable. Keep the native cue configuration in the
canonical PPTX.

**Current boundary**: importing and automatically splitting one long finished
recording is unsupported. Require page-level audio or an explicit page/time map;
otherwise deliver the designed deck and frozen notes without claiming audio
integration.
