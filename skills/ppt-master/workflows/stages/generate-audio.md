---
description: Shared post-processing stage for per-slide narration audio and optional embedding.
---

# Generate Audio Stage

> Shared narration stage. Run from the Generate PPTX route after notes/export readiness, or from the Enhance Native PPTX narration module after its notes step. By default, `edge-tts` produces one audio/SRT pair per slide from the same streaming request. Cloud TTS providers (`elevenlabs` / `minimax` / `qwen` / `cosyvoice`) currently produce audio only. The caller owns final PPTX integration.

This stage is **context-independent**: it reads `notes/*.md` and queries the selected TTS voice catalog, so either owning route may invoke it in a fresh session. It does not choose the top-level route and does not patch slide design.

## When to Run

- Per-page narration files exist at `notes/*.md`. In Generate PPTX, split `notes/total.md` during Step 7.1. In Enhance Native PPTX, the notes module writes numeric files such as `001.md`.
- Default mode: `edge-tts` is installed (`python3 -m pip install edge-tts`).
- The stage is page-level only: with edge, one notes file becomes `audio/<stem>.mp3` plus `notes/subtitles/<stem>.srt`; with a cloud provider, it becomes one audio file. Do not use a single long audio track or attempt automatic long-audio splitting.
- PPT narration assets must be PowerPoint-reliable audio: `m4a` (AAC), `mp3`, or `wav`. The built-in TTS path defaults to `mp3`; provider formats such as `pcm`, `opus`, or `flac` must be transcoded before embedding.
- PowerPoint recorded narration export requires `ffprobe` so slide timings can be written from actual audio duration.
- Optional post-export video calibration requires `ffmpeg` plus `numpy`; it runs only when the caller supplies the finished PowerPoint video.
- High-quality cloud mode: provider API key is set before use:
  - ElevenLabs: `ELEVENLABS_API_KEY`
  - MiniMax: `MINIMAX_API_KEY`
  - Qwen: `QWEN_API_KEY` or `DASHSCOPE_API_KEY`
  - CosyVoice: `COSYVOICE_API_KEY` or `DASHSCOPE_API_KEY`
  - Keys may live in the current process environment or the first `.env` found in this order: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`
- The deck is in a single dominant language (mixed-language decks: pick the dominant one — the AI uses judgment, not a heuristic).

If `notes/*.md` are missing, run `total_md_split.py <project_path>` first.

---

## Step 1: Determine the deck's language

The AI already knows the deck's language from writing the notes. No detection script needed.

- Identify the primary language from the notes content: `zh` / `en` / `ja` / `ko` / etc.
- For mixed-language decks (e.g. Chinese with English technical terms), pick the language the audience will hear most of.
- For Chinese specifically: pick the locale based on context — `zh-CN` (mainland mandarin, default), `zh-TW` (Taiwanese mandarin), or `zh-HK` (Cantonese). Ask the user only if the project context doesn't make it clear.

---

## Step 2: Choose audio backend and pull the voice catalog

Default to **edge** unless the user explicitly asks for a cloud provider / higher-quality cloud narration / a cloned voice.

**edge backend**:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale <locale>
```

**ElevenLabs backend**:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --provider elevenlabs --list-voices
```

**Cloud providers using explicit voice IDs/names**:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --provider minimax --list-voices
python3 skills/ppt-master/scripts/notes_to_audio.py --provider qwen --list-voices
python3 skills/ppt-master/scripts/notes_to_audio.py --provider cosyvoice --list-voices
```

The output is a flat list of all available voices for the selected provider. From this list, the AI picks **3–6 candidates** to recommend, applying these rules:

- **Cover both genders** when both exist for the locale.
- **For edge**: prefer `COMMON_VOICES`-listed voices (curated set inside `notes_to_audio.py`) when the locale has them — they are battle-tested.
- **For ElevenLabs**: prefer voices already present in the user's account; if the user provides a specific `voice_id`, do not override it.
- **For MiniMax / Qwen / CosyVoice**: if the user provides a cloned `voice_id`, use it directly. Do not attempt voice cloning inside this narration stage.
- **Match the deck's tone** — pick the strongest recommendation based on style:
  - Consultant / data-driven / 财报 → 稳重男声（如 `zh-CN-YunjianNeural`）or 清晰女声（如 `zh-CN-XiaoxiaoNeural`）
  - General / 教学 / 产品介绍 → 明亮女声 / 年轻男声（如 `zh-CN-XiaoyiNeural` / `zh-CN-YunxiNeural`）
  - 发布会 / 播报 → 播报感男声（如 `zh-CN-YunyangNeural`）
  - English consultant deck → `en-US-GuyNeural` (steady) or `en-US-JennyNeural` (clear)
  - Japanese / Korean → pick from `ja-JP-*` / `ko-KR-*` neural voices, mark gender + tone

For each candidate, write a **one-line Chinese description** covering: 性别 · 调性 · 适用场景。For cloud providers, include the voice name/ID exactly as it must be passed to `--voice-id`.

---

## Step 3: One-shot user interaction (mandatory)

Send a single message to the user that asks all three questions at once and provides a recommended value for each. Do NOT split into multiple rounds.

**Cloned-voice fast path**: if the user mentioned a cloned voice / 克隆音色 / 复刻音色 / "my own voice" along with a `voice_id`, skip the voice-recommendation list — set the provider to whichever the user named (`elevenlabs` / `minimax` / `qwen` / `cosyvoice`), pin the `voice_id` they gave you, and only confirm rate + embed-or-not.

**Message template** (Chinese; translate to user's chat language if different). “Embed” means caller-specific integration: SVG re-export for Generate PPTX, or native OOXML application for Enhance Native PPTX.

> 检测到 notes 主语言为 **<语言>**（locale: `<locale>`）。基于 deck 调性（<风格>），我推荐以下配置：
>
> **生成模式**：⭐ 推荐 `<edge|elevenlabs|minimax|qwen|cosyvoice>`（理由：<一句话，如"无需配置，稳定生成"或"用户要求高质量云端音色">）。
>
> **音色**：
> - **[1] <ShortName>** — <性别·调性·适用场景> ⭐ **推荐**
> - [2] <ShortName> — <性别·调性·适用场景>
> - [3] <ShortName> — <性别·调性·适用场景>
> - [4] <ShortName> — <性别·调性·适用场景>
> - [5] <ShortName> — <性别·调性·适用场景>
> - 也可直接输入清单中的其他 ShortName。
>
> **语速/风格参数**：⭐ 推荐 `<rate or provider defaults>`（理由：<一句话，如"页均 2–3 句，正常语速听感最稳"或"ElevenLabs 默认 voice settings 保留音色原始表现最稳">）。
>
> **生成完是否重新导出嵌入音频的 PPTX**：⭐ 推荐 **是**（一次到位，自动按音频时长设页面停留）。
>
> 直接回"好"用全部推荐值，或告诉我想改的部分（如"音色 2，语速 -5%"或"用 MiniMax 的 voice_id xxx"）。

**Recommended-value rules**:
- 生成模式：默认 `edge`；当用户明确追求高质量云端音色或提供 cloud voice ID 时，按用户指定选 `elevenlabs` / `minimax` / `qwen` / `cosyvoice`。
- 音色：从 Step 2 候选里挑最贴合 deck 调性的那一个。
- 语速：edge 默认 `+0%`；notes 字数密集（页均 >4 句长句）建议 `-5%`；notes 简短紧凑建议 `+5%`；超出此范围需说明理由。Cloud providers 默认用 provider defaults，除非用户明确要调速或改风格。
- 嵌入：默认推荐"是"；除非用户已有定制 PPTX 不希望覆盖。

---

## Step 4: Execute (no further interaction)

Run sequentially — do NOT bundle:

```bash
# 1A. Generate audio with edge (default)
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice <chosen-ShortName> --rate <chosen-rate>

# 1B. Or generate audio with ElevenLabs
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs --voice-id <chosen-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 1C. Or generate audio with MiniMax
# Defaults to the China endpoint; set MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2 for overseas access.
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax --voice-id <chosen-voice-id> \
  --minimax-model speech-2.8-hd

# 1D. Or generate audio with Qwen TTS
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen --voice-id <chosen-voice> \
  --qwen-model qwen3-tts-flash --qwen-language-type Chinese

# 1E. Or generate audio with CosyVoice
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice --voice-id <chosen-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 2A. Derive click-free narration timings from the existing custom animation
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-padding 0.5 --force

# 2B. Re-export with audio embedded
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --no-merge --recorded-narration audio --narration-padding 0.5

# Optional: use the canonical presentation animation instead
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --no-merge --recorded-narration audio --narration-padding 0.5 \
  --animation-config animations.json

# Optional: export narration with no object or page-transition animation
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --no-merge --recorded-narration audio --narration-padding 0.5 \
  --no-animations

# 2C. Merge page-local SRT against timing values read from the final PPTX
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 2D. After PowerPoint exports the video, align the frozen narration text
# against the finished video's actual audio track
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> \
  --video <powerpoint_exported_video> --language <language> --force
```

If `notes_to_audio.py` errors with a missing dependency or missing provider API key, fix the prerequisite and re-run — do NOT swallow the error.

The edge command writes each MP3 and its internal page SRT from the same `edge-tts` stream. Every cue is the service's native `SentenceBoundary` text, offset, and duration; the audio stage does not re-segment it or edit the notes. Each SRT uses a page-local timeline whose origin is `00:00:00,000`, including any leading silence before the first cue. Cloud-provider commands currently write audio only.

**Narration animation ownership**: `animations.json` must already exist and remains read-only. The audio stage deep-copies it to `narration_animations.json`, preserves transitions, effects, durations, order, and explicit `effect: none`, then changes only the derived trigger/delay values needed for click-free narration playback. It first resolves the sequence from `animations.json` and page SRT. When a sparse sidecar cannot identify every effective group, it reads only the affected SVG page as a read-only fallback; it never edits SVG, notes, or `animations.json`. Without a timing plan, ordered animated groups map to ordered sentence cues and unmatched groups keep their canonical relative delay.

**Narrated export animation selection**: `--recorded-narration` defaults to `<project_path>/narration_animations.json` and fails with a repair hint when that file is missing. Pass `--animation-config animations.json` to keep the canonical presentation animation, or `--no-animations` to disable both object animations and page-transition motion while preserving narration audio and recorded slide-advance timings. Non-narrated export keeps its existing optional `<project_path>/animations.json` default.

An existing `<project_path>/narration_timing.json` remains an optional explicit mapping for ambiguous pages. It is fingerprinted to the ordered SRT set; `cue` is the 1-based sentence cue, and omitted `cue` keeps that group's canonical relative delay.

Get the exact fingerprint value with:

```bash
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>
```

```json
{
  "version": 1,
  "srt_sha256": "<sha256 of the ordered page-local SRT set>",
  "narration_padding": 0.5,
  "slides": {
    "01_title": {
      "groups": [
        { "id": "page-title", "cue": 1 },
        { "id": "supporting-visual" }
      ]
    }
  }
}
```

`narration_sync.py subtitles` may still write `<project_path>/notes/subtitles/total.srt` as a PPTX-timeline diagnostic. It is not the delivery subtitle for a finished video.

After PowerPoint exports the video, `video_subtitles.py` takes the exact narration text frozen in the page SRT set and force-aligns it against the finished video's actual audio track with `stable-ts`. Long delivery cues may be split for display at this final stage. This writes a same-stem external SRT without changing the MP4, notes, page SRT, or animation files.

This stage keeps subtitles as external SRT files. It does not embed subtitles into PPTX or export MP4 directly.

**Caller integration**:

| Caller | After audio generation |
|---|---|
| Generate PPTX | With Edge SRT and an existing `animations.json`, derive `narration_animations.json`, export with `--recorded-narration audio` (derived animation by default; canonical or no-animation modes remain explicit), and generate the delivery SRT only after PowerPoint exports the video. |
| Enhance Native PPTX | Return to [`native-enhance-pptx`](../native-enhance-pptx.md) Step 9; its `apply` command owns audio relationships, timings, transitions, and the enhanced export |

For Generate PPTX, `--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide must have a matching supported audio file, every duration must be readable by `ffprobe`, and object animations must not use `--animation-trigger on-click`. Use `after-previous` or `with-previous` for narrated/video export. Narration changes the slide-advance layer only: the resolved page-transition effect remains unchanged, `-t none` remains visually transition-free, and narration advance disables click while using audio duration plus padding. The re-export is saved as `exports/<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports.

**Narrated SVG export**: keep `--no-merge` on the final synchronized export. Separate SVG line frames preserve authored coordinates; default paragraph merging can make PowerPoint recalculate multiline text geometry and introduce visible offsets.

---

## Step 5: Completion report

Output one summary block listing:

- Number of audio files generated and their location (`<project_path>/audio/*`).
- For edge, number of matching page-local SRT files and their location (`<project_path>/notes/subtitles/*`).
- For Generate PPTX with Edge SRT, derived narration animation group count and `narration_animations.json` path.
- When a finished video was supplied, the final aligned sidecar SRT path.
- The provider, voice, and rate/settings actually used.
- The caller-owned integration result: narrated SVG export path, enhanced native PPTX path, or “audio only”.
- For Generate PPTX when embedding was skipped, one-line hint: `python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio`.
