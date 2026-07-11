---
description: Native enhancement platform for existing PPTX files, starting with notes/audio/timings/transitions without SVG conversion
---

# Native Enhance PPTX Workflow

> Standalone workflow for enhancing an existing PowerPoint deck without regenerating it. V1 implements the `narration` module: speaker notes, narration audio, slide auto-advance timings, and page transitions.

This workflow treats a `.pptx` as the artifact to preserve. It archives the source file into a lightweight project, uses `ppt_to_md.py` only to understand slide content, then patches the archived PPTX package directly through OOXML zip operations.

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
| `delivery.check` | Planned | Font/media/hidden-slide/file-size validation |
| `media` | Planned | Background music, video, media compression |
| `presenter` | Planned | Q&A notes, speaker cues, rehearsal artifacts |
| `animation` | Planned | Explicit object-level animation only |
| `visible-stamp` | Planned | Watermark/footer/logo; requires explicit confirmation |

**Default — V1 only**: Do not implement planned modules inside this workflow yet. Keep V1 focused on the narration module.

**Object animation boundary**: Object-level animation is not part of V1. If the user asks for it, treat it as a future module or a separate explicitly confirmed task.

---

## 3. When to Run

| Condition | Action |
|---|---|
| Existing `.pptx` + wants notes / narration / voiceover / auto-play / page transitions while keeping format stable | Run this workflow |
| Existing `.pptx` + asks to optimize it but says not to change existing content or layout | Run this workflow only for V1 narration enhancements; clarify any visible-slide request |
| Existing `.pptx` + asks to beautify or re-layout | Use [`beautify-pptx`](./beautify-pptx.md) |
| Existing `.pptx` + asks to fill new content into the design | Use [`template-fill-pptx`](./template-fill-pptx.md) |
| PPT Master generated project with `svg_output/` | Use [`generate-audio`](./generate-audio.md) for narration |

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
| `<project>/validation/` | Coverage reports and read-back artifacts |

**Validation**: `project.json` contains `schema: native_pptx_enhancement_project.v1`, `kind: native_pptx_enhancement`, and `modules` containing `notes`, `audio`, `timings`, `transitions`.

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

Present the plan to the user before generating notes or audio:

| Module | Recommended default | Confirmation question |
|---|---|---|
| `notes` | Enabled | Add/replace speaker notes generated from slide content? |
| `audio` | Enabled when user wants narration/video/autoplay | Generate one narration audio file per slide? |
| `timings` | Enabled with audio | Set slide auto-advance from audio duration? |
| `transitions` | Enabled, `fade` 0.5s | Add page transitions? Which effect/duration? |

**⛔ BLOCKING**: Stop here and wait for explicit user confirmation. Do not generate notes, generate audio, or patch the PPTX until the user confirms the module plan.

**Transition/timing ownership**:

| Confirmed state | Enter transition | Slide advance |
|---|---|---|
| Transitions enabled with an effect | Replace with that exact effect and duration | Preserve unless timings is enabled |
| Transitions disabled with a non-`none` configured effect | Preserve the source effect, including unknown `AlternateContent` | Preserve unless timings is enabled |
| Explicit `none` | Remove the visual effect | Preserve, or write timing-only advance when timings is enabled |
| Timings enabled with audio | Keep the resolved enter policy | Use audio duration plus narration padding; click disabled |
| Timings disabled | Apply the confirmed enter policy only | Do not run `ffprobe`; do not add/change `advTm` or `useTimings` |

**Hard rule — no silent downgrade**: a requested supported effect must be written with its established direction/variant attributes. Unknown requested effects fail; unknown source effects are preserved when the transition module is disabled.

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

> Note: before audio generation, missing audio returns exit code `2` only when `audio.enabled` is true. Missing notes are not acceptable once this step is complete.

---

## 7. Audio Voice Confirmation

🚧 **GATE**: Step 6 complete; `audio.enabled` is true.

Follow the same one-shot interaction standard as [`generate-audio`](./generate-audio.md):

1. Determine the notes' primary language.
2. List available voices for the selected backend.
3. Recommend backend, voice, rate/settings, and whether to embed audio back into the PPTX.
4. Ask the user to accept all recommendations or override any field.

For edge voices:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale <locale>
```

**⛔ BLOCKING**: Stop here and wait for explicit user confirmation of audio backend, voice, rate/settings, and embedding. Do not run `notes_to_audio.py` before this confirmation.

Record the confirmed audio config into `project.json`:

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

## 8. Generate Audio

🚧 **GATE**: Step 7 confirmed; notes files exist under `<project>/notes/`.

Run with the confirmed values:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py "<project>" \
  --voice <chosen-ShortName> --rate <chosen-rate>
```

**Default — edge (may override)**: Use `edge` unless the user requests a cloud provider or supplies a cloned voice ID.

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

Without `--apply-transition-without-audio` (or the matching confirmed-plan
field), the resolved enter policy is applied while processing slides with
audio; slides without audio keep their source transition.

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

```markdown
## ✅ Native PPTX Enhancement V1 Complete

- [x] Project initialized at `<project>`
- [x] Source PPTX archived into `<project>/sources/`
- [x] V1 narration module applied
- [x] Enhanced PPTX exported to `<project>/exports/<file>.pptx`
- [x] Read-back validation written to `<project>/validation/readback.md`
```
