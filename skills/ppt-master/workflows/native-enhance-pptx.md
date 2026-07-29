---
description: Native enhancement platform for existing PPTX files, with delivery checks and scoped OOXML updates without SVG conversion
---

# Enhance Native PPTX Route

> Top-level route for enhancing an existing PowerPoint deck without regenerating it. The current write scope is speaker notes, narration audio, slide auto-advance timings, and global or per-slide page transitions; read-only delivery checks always run.

This route treats a `.pptx` as the artifact to preserve. It archives the source file into a lightweight project, uses `ppt_to_md.py` only to understand slide content, then patches the archived PPTX package directly through OOXML zip operations.

---

## 1. Platform Contract

| Rule | Contract |
|---|---|
| Source file | If already under `projects/`, move it into the enhancement project; otherwise copy it |
| Visible slides | Do not rewrite existing text, shapes, images, charts, tables, masters, or layouts |
| Route | Direct PPTX package patching; no SVG conversion |
| Output | A new `.pptx` under `<project>/exports/` |
| Project kind | `native_pptx_enhancement` |

**Hard rule**: Native enhancement is append-oriented. It may add notes, media, timings, transitions, relationships, and content-type records. It must not regenerate slides.

**Forbidden — SVG pipeline**:
- Do not run `pptx_template_import.py`
- Do not create `svg_output/`
- Do not run `finalize_svg.py`
- Do not run `svg_to_pptx.py`

**Hard rule — public entrypoint**: Route and document all new work through
`native_enhance_pptx.py`. The legacy `native_narration_pptx.py` command remains
only as a thin CLI compatibility shim; it is not a separate route. The core
continues to accept the legacy `native_narration_pptx_project.v1` project schema.

**OOXML execution model**:

```text
source.pptx
→ unzip to temporary work directory
→ patch only required package parts
→ rezip to exports/<source>_enhanced.pptx
```

---

## 2. Module Scope

| Module | V1 status | Behavior |
|---|---:|---|
| `narration.notes` | Enabled | Add or replace speaker notes generated from slide content |
| `narration.audio` | Enabled | Embed one audio file per slide |
| `narration.timings` | Enabled | Set narrated slides to auto-advance by audio duration |
| `narration.transitions` | Enabled | Add page-level transitions for narrated/selected slides |
| `delivery.check` | Enabled | Read-only package/font/media/hidden-slide/file-size and existing-motion audit |
| `media` | Planned | Background music, video, media compression |
| `presenter` | Planned | Q&A notes, speaker cues, rehearsal artifacts |
| `animation` | Planned | Explicit object-level animation only |
| `visible-stamp` | Planned | Watermark/footer/logo; requires explicit confirmation |

**Default — current write scope only**: Do not implement planned write modules inside this route yet. Keep mutations limited to notes, narration audio, timings, and page transitions.

**Object animation boundary**: `delivery.check` reports existing object-animation presence, and apply proves its fingerprint is unchanged. It does not author or edit object animations. The shared animation writer builds a complete timing tree for generated slides and is not safe to append to an arbitrary native slide.

---

## 3. When to Run

| Condition | Action |
|---|---|
| Existing `.pptx` + wants notes / narration / voiceover / auto-play / page transitions while keeping format stable | Run this route |
| Existing `.pptx` + asks to optimize it but says not to change existing content or layout | Run this route only for V1 narration enhancements; clarify any visible-slide request |
| Existing `.pptx` + asks to beautify or re-layout | Enter Generate PPTX with the [`beautify-pptx`](./profiles/beautify-pptx.md) profile |
| Existing `.pptx` + asks to fill new content into the design | Use [`template-fill-pptx`](./template-fill-pptx.md) |
| PPT Master generated project with `svg_output/` | Stay in Generate PPTX and run the shared [`generate-audio`](./stages/generate-audio.md) stage |

---

## 4. Create the Project and Draft Plan

🚧 **GATE**: User provided an existing `.pptx`.

Run:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py init "<source.pptx>" --name "<project_slug>"
```

Project layout:

| Path | Purpose |
|---|---|
| `<project>/project.json` | Project schema, kind, enabled modules, source paths, defaults |
| `<project>/sources/<source>.pptx` | Archived source PPTX used for package patching |
| `<project>/sources/<source>.md` | `ppt_to_md.py` output for slide understanding |
| `<project>/analysis/slide_index.json` | Slide order and PPTX slide part mapping |
| `<project>/notes/` | Per-slide spoken notes, named `001.md`, `002.md`, ... |
| `<project>/audio/` | Per-slide narration media, named `001.mp3`, `002.mp3`, ... |
| `<project>/exports/` | Enhanced PPTX copies |
| `<project>/validation/` | Delivery checks, readiness reports, and read-back artifacts |

**Validation**: `project.json` contains `schema: native_pptx_enhancement_project.v1`, `kind: native_pptx_enhancement`, and `modules` containing `notes`, `audio`, `timings`, `transitions`, and `delivery.check`.

`init` records the archived source SHA-256 and ordered slide-part roster, then writes the intake audit to `<project>/validation/report.json`. Package-integrity, OPC part/content-type/relationship, XML, slide-inventory, transition, or object-animation errors stop before a project-local source is moved. The only retained historical structural baseline is the narrowly recognized legacy notes-slide relationship to a missing notes master; it remains visible in the report and apply may not add any new structural error.

**Source import rule**: When `<source.pptx>` is inside the repo's `projects/` tree, `init` moves it into `<project>/sources/`. When it is outside `projects/`, `init` copies it into `<project>/sources/`. The mode is recorded in `project.json` as `source_import.mode`.

The `init` command also writes:

```text
<project>/analysis/enhancement_plan.json
```

**Hard rule**: Treat this draft plan as the first user-facing artifact. Do not generate notes, list voices, generate audio, or apply package patches before the user confirms which enhancements to add.

---

## 5. Enhancement Plan Confirmation

🚧 **GATE**: Step 4 complete; `<project>/analysis/enhancement_plan.json` exists.

If the project already existed or notes/audio coverage changed, refresh the draft:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py plan "<project>"
```

Refresh preserves user-owned module enablement, timing padding, global transition settings, and `transitions.slides`; it recomputes file presence/coverage, resets the plan to `draft`, and requires confirmation again. Audio coverage in the plan is explicitly `decodability: unchecked`; `validate` owns the ffprobe gate. CLI flags override only fields explicitly supplied.

Present the plan to the user before generating notes or audio:

| Module | Recommended default | Confirmation question |
|---|---|---|
| `notes` | Enabled; required whenever audio is enabled | Add/replace speaker notes generated from slide content? |
| `audio` | Enabled when user wants narration/video/autoplay | After notes are complete, generate one narration audio file per slide? |
| `timings` | Enabled with audio | Set slide auto-advance from audio duration? |
| `transitions` | Enabled, `fade` 0.5s | Add page transitions? Which canonical native effect, Effect Options, and duration? |
| `delivery.check` | Always on, read-only | No confirmation required; review errors and advisories |

**⛔ BLOCKING**: Stop here and wait for explicit user confirmation. Do not generate notes, generate audio, or patch the PPTX until the user confirms the module plan.

**Hard dependency — notes before audio**: Confirming `audio.enabled: true`
also requires `notes.enabled: true`. If complete per-slide notes do not already
exist, run Step 6 and generate them before entering audio configuration or
audio generation. Never generate narration directly from slide text or bypass
the notes artifact.

**Transition/timing ownership**:

| Confirmed state | Enter transition | Slide advance |
|---|---|---|
| Transitions enabled with an effect | Replace with that exact effect and duration | Preserve unless timings is enabled |
| Transitions disabled with a non-`none` configured effect | Preserve the source effect, including unknown `AlternateContent` | Preserve unless timings is enabled |
| Explicit `none` | Remove the visual effect | Preserve, or write timing-only advance when timings is enabled |
| Timings enabled with audio | Keep the resolved enter policy | Use audio duration plus narration padding; click disabled |
| Timings disabled | Apply the confirmed enter policy only | Audio readiness may probe decodability; do not use duration or add/change `advTm` or `useTimings` |

The confirmed `modules.transitions` object may include `effect_options` beside
an explicit canonical `effect`. Use
`pptx_animations.py --describe-transition <effect>` for its exact fields.
Old names remain accepted only when reading compatibility input; a newly
written plan stores the canonical effect and any implied options.

For explicit page selection or page-specific settings, add `slides` keyed by
the 1-based `index` in `analysis/slide_index.json`:

```json
{
  "modules": {
    "transitions": {
      "enabled": false,
      "effect": "fade",
      "duration": 0.5,
      "apply_without_audio": false,
      "slides": {
        "2": {},
        "3": {"duration": 0.8},
        "4": {
          "effect": "push",
          "effect_options": {"direction": "left"}
        },
        "5": {"effect": "none"},
        "6": {"effect": "preserve"}
      }
    }
  }
}
```

| Per-slide entry | Behavior |
|---|---|
| `{}` | Select the page and inherit the global effect/options/duration |
| Partial object | Inherit omitted global fields; a new explicit effect uses its own default options |
| `effect: none` | Remove the visual transition; timings remain independently owned |
| `effect: preserve` | Preserve the source visual transition; narration timing may still update advance |

A `slides` entry always selects that page. Without audio, enabled global effects
and explicit global `none` apply deck-wide; `apply_without_audio` is ignored.
With audio, the flag extends the global policy from narrated to all pages.
Disabled non-`none` effects preserve unlisted pages. Morph uses PowerPoint
automatic matching; this route does not rename native objects for deterministic
pairs.

**Hard rule — no silent downgrade**: a requested native effect must be written with its complete validated Effect Options. Unknown effects or inapplicable options fail; unknown source effects are preserved when the transition module is disabled.

After confirmation, update `<project>/analysis/enhancement_plan.json`:

```json
{
  "status": "confirmed"
}
```

Also set each confirmed module's `enabled` value. Disabled modules must stay in the file with `enabled: false`, not be deleted.

---

## 6. Generate Notes From Existing Slides

🚧 **GATE**: Step 5 confirmed; `notes.enabled` is true; `<project>/sources/<source>.md` exists.

Read:

| File | Use |
|---|---|
| `<project>/sources/<source>.md` | Visible slide text, tables, extracted notes, image references |
| `<project>/analysis/slide_index.json` | Exact slide count and target note filenames |

Write:

```text
<project>/notes/001.md
<project>/notes/002.md
...
```

**Hard rule**: Notes are spoken narration only. Do not include stage directions, implementation comments, timing labels, markdown tables, or visible-slide rewrite instructions.

**Hard rule**: Notes must be faithful to the slide. They may explain visible content, but must not add unsupported facts.

| Slide type | Notes length |
|---|---|
| Cover / section divider | 1-2 short sentences |
| Dense content page | 2-4 sentences |
| Chart / table page | Explain the reading path, then state the takeaway |
| Ending page | One concise close |

Run coverage check:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate "<project>"
```

> Note: missing, empty, unreadable, or undecodable requested material returns exit code `2`. Package, source-drift, plan/module, or duplicate native-enhance narration-carrier errors return `1`.

---

## 7. Shared Audio Configuration

🚧 **GATE**: Step 6 complete; `audio.enabled` is true.

Run [`generate-audio`](./stages/generate-audio.md) Steps 1–3. That shared stage exclusively owns language selection, provider/voice catalog lookup, recommendation rules, and the one-shot confirmation. Do not repeat or fork those rules here.

Record the confirmed config into `project.json`:

```json
{
  "audio": {
    "provider": "edge",
    "voice": "zh-CN-YunjianNeural",
    "rate": "+0%"
  }
}
```

---

## 8. Run the Shared Audio Stage

🚧 **GATE**: Step 7 confirmed; complete non-empty notes files exist under
`<project>/notes/` for every slide.

Run [`generate-audio`](./stages/generate-audio.md) Step 4 with `<project>` and the confirmed values. Stop after audio generation; do not run its Generate-PPTX-only `svg_to_pptx.py --recorded-narration` integration. This route integrates audio through Step 9 instead.

**Naming contract**: Audio stems match note stems: `001.md` → `001.mp3`.

Validate:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate "<project>"
```

---

## 9. Apply V1 Enhancements

🚧 **GATE**: Enhancement plan is confirmed; notes are ready if requested; audio is ready if requested.

Run:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply "<project>"
```

Optional:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply "<project>" \
  --transition fade \
  --transition-duration 0.5 \
  --narration-padding 0.4 \
  --apply-transition-without-audio \
  --overwrite
```

`--apply-transition-without-audio` matters only with audio enabled: it extends
the global enter policy from narrated slides to all slides. Explicit slide
entries always opt in. Without audio, enabled transitions apply to every slide.

`apply` reruns the same source/readiness/plan checks as `validate`. Enabling
audio always requires every selected file to be decodable by ffprobe; enabling
timings additionally consumes that duration for `advTm`. It refuses
partial requested material, a changed source hash/slide roster, or a source
that already contains a `native_enhance_audio_*` carrier. New audio/poster
parts use collision-free names; an existing poster is reused only when its
bytes match the tool marker exactly. Output must be a new `.pptx` under
`exports/` or an external location; apply never overwrites either source or
writes into project control directories. Every apply attempt invalidates the
previous validation receipt, and a failed preflight records its current errors
instead of leaving stale passed evidence.

Patch scope:

| Package area | Append/update |
|---|---|
| `ppt/notesSlides/` | Notes slide parts |
| `ppt/notesMasters/` | Notes master only when needed |
| `ppt/slides/_rels/slideN.xml.rels` | Relationships for notes/audio/media/poster |
| `ppt/media/` | Narration audio and transparent poster |
| `ppt/slides/slideN.xml` | Hidden autoplay audio shape and page timing |
| `ppt/presProps.xml` | `showPr useTimings=1` only when this run writes automatic slide advance |
| `[Content_Types].xml` | Required content types |

**Hard rule**: Do not modify existing slide shapes, text bodies, images, chart data, master/layout parts, or existing non-target relationships.

Before publishing the candidate, apply validates transitions, timing/object
animation structure, ZIP integrity, unique parts, internal relationships,
slide count, and hidden-slide state. The narrowly allowed legacy missing
notes-master finding may remain exactly equivalent, but the candidate must not
introduce any structural error. Apply then writes both audits and the
introduced-error delta to `<project>/validation/report.json`.

---

## 10. Validate Output

Run read-back:

```bash
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py \
  "<project>/exports/<source>_enhanced.pptx" \
  -o "<project>/validation/readback.md"
```

Check:

| Check | Expected |
|---|---|
| Slide count | Same as source |
| Visible content | No intentional changes |
| Notes | Present on intended slides |
| Audio media | Present under `ppt/media/` when generated |
| Auto-play | Narrated slides advance by audio duration |
| Transition | Requested effect remains exact; preserved `AlternateContent` keeps its primary and fallback branches |
| Timings disabled | Source `advTm` and package `useTimings` are not changed |
| Delivery check | No newly introduced structural errors; source baseline and font/media/hidden-slide advisories reviewed |

```markdown
## ✅ Native PPTX Enhancement V1 Complete

- [x] Project initialized at `<project>`
- [x] Source PPTX archived into `<project>/sources/`
- [x] Confirmed native enhancement modules applied
- [x] Enhanced PPTX exported to `<project>/exports/<file>.pptx`
- [x] Delivery postflight written to `<project>/validation/report.json`
- [x] Read-back validation written to `<project>/validation/readback.md`
```
