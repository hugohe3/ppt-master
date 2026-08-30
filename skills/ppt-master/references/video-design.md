# Video-delivery Design Reference Manual

Conditional design guidance for presentations whose intended use is recorded, self-running, or video delivery.

**Trigger**: load when the effective delivery purpose is video, recorded narration, or unattended playback, and load its script rules for an explicit final/literal narration input. Speaker notes, animation, or audio requested for an ordinary deck do not activate it alone; explicit video/MP4 delivery does, and Quick additionally activates §3's direct-delivery contract.

**Ownership**: a conditional Generate reference, not a profile or artifact route. Default keeps Strategist and confirmation; Quick keeps its one-pass flow; notes, animation, audio, and native export stages keep their schemas and commands. Under Beautify, its wording/page/order invariants still bind — apply this reference only inside the freedom that profile permits.

---

## 1. Intake and Script State

| Material | Treatment |
|---|---|
| Ordinary source or rough transcript | Source material: edit, condense, reorganize under the route's normal content-divergence contract |
| Explicit final/literal narration script | Preserve every spoken word and its order; segment only at semantic scene boundaries |
| SRT used to generate new TTS | Preserve cue text when explicitly final; source timecodes are pacing evidence only, the new synthesis timing is authoritative |
| SRT bound to an existing recording | Preserve its text/audio timing authority; do not regenerate TTS or pretend one long recording was split automatically |
| Already page-separated final script | Preserve supplied page boundaries unless the user permits restructuring |
| Target platform, canvas, or duration | Use the canvas registry; resolve scene granularity, page count, and notes length together |

**Hard rule — final means explicit**: freeze wording only when the user identifies the script as final, literal, or verbatim; never promote ASR output, subtitles, or a draft transcript into a literal contract by inference.

**Final-script production input**: after the page roster is final and before SVG authoring, write the resolved per-slide script once to `notes/total.md` with `# Slide <number>` headings and `---` separators, each body segment verbatim. It is a production input, not a storyboard or substitute Design Spec; run `total_md_split.py` only after the SVG roster exists.

**Default — semantic segmentation (may override for a user-authored page plan)**: one scene is one coherent visual state or mental-map step, not one sentence, cue, or effect; several cues may share a scene and one scene may hold several ordered reveals.

---

## 2. Scene and Page Planning

**Default — quality follows purpose (may override)**: explanation prioritizes understanding; promotion or brand work may prioritize emotion, recall, or impact. Give every change a communication job.

| Narrative relationship | Page treatment |
|---|---|
| Several lines explain one idea | One page/scene; reveal only the semantic units the explanation needs |
| One system persists | Derive states from the prior composition before roster/notes freeze; keep orienting cues, change the semantic delta |
| New evidence expands a known map | Retain orienting cues; adapt the active region and context |
| The same object changes position, scale, containment, or state | Consider compatible Morph endpoints when movement improves orientation |
| The audience must adopt a new mental map | Start a new composition and make the transition explicit |

**Defaults (each may override for the stated reason)**:

- *Stable anchors* — within one explanation preserve recognizable roles, relationships, or spatial cues; position, scale, and style may change while identity and orientation stay legible; reset for a new map.
- *One semantic focus change per beat* — change several elements together only for one inseparable communication unit; never alter unrelated regions for busyness.
- *Scene chrome earns its place* — newly authored scenes do not carry a report-style header, footer, or page number by convention; let the semantic title join the composition and drop running chrome on cover, ending, and breathing scenes. Keep chrome the active profile's fidelity boundary requires, or that genuinely orients, identifies, or attributes.
- *Screen for orientation, notes for speech* — keywords, structure, evidence, and relationships on the slide; full explanation in notes; never duplicate the narration as body copy, except literal on-screen copy.

**Page count**: derive page/notes boundaries from scenes, mental-map arcs, endpoints, and duration — not cues or sentences. Profile-fixed count/order/content (1:1/fidelity) permits only existing-neighbor evaluation; never alter those invariants for motion.

---

## 3. Default and Quick Planning Handoff

**Default**: Stage 1 confirms the existing open-text `delivery_context`, no separate video question. When the confirmed value identifies recorded/self-running/video delivery, load this reference before authoring the three Stage-2 solutions and apply its scene grammar to every direction; it adds no catalog or confirmation field. Record delivery context and afterlife in §I, visible states and optional motion jobs in §IX, script/notes policy plus target duration in §X. On the final-script branch, create the frozen `notes/total.md` after the approved roster/lock and before Step 5 or split-mode handoff. Reading mode leans `presentation`; choose `balanced` when close-reading afterlife materially outweighs video delivery.

**Quick**: no Stage 1 or video-purpose confirmation. Explicit video/recorded/self-running intent activates this reference after source sufficiency is known and before the one-pass roster, resource, and motion decisions; absent that intent, ordinary Quick behavior. Load the script rules alone when an explicit final/literal narration becomes notes/audio. A pre-SVG `notes/total.md` is an enabled production artifact; Quick still creates no Design Spec, lock, confirmation payload, or storyboard.

**Production outcomes**:

| Need | Decision |
|---|---|
| Spoken delivery or a supplied final script | Enable Speaker Notes |
| User asks the workflow to synthesize narration | Enable Narration Audio (Speaker Notes is its dependency) |
| Progressive reveal, continuing geometry, or timed emphasis materially aids explanation | Enable/load the appropriate animation capability |
| Quick generates a PPTX for recorded, self-running, or video delivery | **Hard rule**: enable Custom Animations before SVG authoring, use semantic groups and page-specific choreography, and complete the stage with a validated `animations.json` before base export; deck-wide `-a auto` and page transitions do not satisfy it; pages or groups may stay static — no coverage quota |
| Quick directly delivers a narrated video or MP4 | **Mandatory**: also enable Speaker Notes, Narration Audio, and video export; write the complete per-scene narration to `notes/total.md` before P01 as page-design input (agent-authored wording may be finalized after the roster, final/literal input stays verbatim); resolve narration-governed timing before audio, requiring timestamped page-local SRT for cue sync or subtitle delivery |
| The user explicitly requests static or page-transition-only playback | Keep object animation off; retain the remaining notes/audio/video outcomes |

Default never forces object animation or audio merely because a deck may later be recorded; the Quick requirement selects the capability, not motion coverage.

---

## 4. SVG, Notes, and Motion Realization

When §3 created `notes/total.md` before SVG, read it once before the first SVG and design each page around its spoken segment. Give every independently narrated or timed semantic unit a descriptive direct-root `<g id>`; keep inseparable units grouped. Preserve a final/literal script exactly; agent-authored direct-video narration changes only during final-SVG validation before audio.

**Hard rule — script/design consistency**: a final script is literal content. If a finished page introduces a claim or relationship the script does not explain, repair the page or return to planning — never rewrite or pad the script in the late notes pass. Every spoken idea needing visual orientation has a visible state or a deliberate speech-only treatment.

**Motion**: load `animations.md` before SVG authoring whenever the plan needs Morph endpoints or page/object-specific motion, and author every required start/end state and semantic group before the final checker — post-processing cannot invent endpoints or target IDs. Use transitions, reveals, emphasis, and Morph only for a named communication job; `effect: none` remains valid. Auto-running narration uses `after-previous` / `with-previous`, never `on-click`.

**Mandatory when narration governs object motion**: before SVG, load `animations.md` and preserve semantic groups; before audio, create and validate canonical `animations.json`. After the base PPTX/report and timestamped page audio/SRT, map timed groups in `narration_timing.json`, derive `narration_animations.json`, and export the narrated PPTX/MP4. Only derived triggers/delays wait for SRT; identity, effect, and order do not. `-a auto` or inherited fixed stagger is not semantic synchronization. For a user-selected static/page-transition-only Quick exception, or ordinary Default narration-independent deck-wide motion, omit these sidecars and the object-sync claim.

**Sound effects**: excluded from this pass and planning artifacts. After final SVG/motion, animation post-processing owns on-demand selection and native configuration. For direct narrated MP4, `generate-audio` owns the sound-delivery branch (§5); gain and limiting never enter `animations.json`.

**Production sequence**: after the final SVG check, validate pre-SVG narration against the visible pages (draft-source runs use final-SVG-grounded notes generation instead); split notes, execute the resolved motion path, export the editable PPTX; direct Quick video continues through audio and, when required, timestamped SRT. Narration-governed Custom Animations use the narrated-sidecar flow; narration-independent custom motion exports its canonical timing without an object-sync claim before the narrated PPTX and MP4.

---

## 5. Delivery Boundary

**Canonical artifact**: the editable PPTX. `generate-audio` owns provider/voice/rate selection, page audio/SRT, semantic narration timing, narrated PPTX export, optional native PowerPoint video export, the slideshow-capture handoff, and the triggered sound-effects mix.

**Conditional MP4**: run `powerpoint_video.py --check` only for the native-export branch. Without native Windows PowerPoint export, the narrated PPTX is the successful upstream artifact; an explicit slideshow-capture choice hands it to a user-operated PowerPoint recorder and is complete only when the capture is returned and accepted. Never substitute screenshots, HTML, or a third-party renderer.

**Hard rule — choose one PowerPoint video sound boundary**:

| Delivery branch | Sound contract |
|---|---|
| Native encoder | PowerPoint supplies visual animation and narration but may omit transition/object sounds; with resolved cues its MP4 is raw and requires the verified `video_sound_mix.py` output |
| Real-time slideshow capture | PowerPoint renders and plays audio; a recorder captures the full-screen Slide Show and exactly one application/system-audio source; the accepted capture contains narration and every cue once and never enters `video_sound_mix.py` |

The branches are mutually exclusive because mixing a capture would duplicate its cues. Keep the native cue configuration in the canonical PPTX; capture is explicit and human-audited, never an automatic fallback.

**Current boundary**: importing and automatically splitting one long finished recording is unsupported. Require page-level audio or an explicit page/time map; otherwise deliver the deck and frozen notes without claiming audio integration.
