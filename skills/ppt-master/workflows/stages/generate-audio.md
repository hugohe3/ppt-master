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

# 2A. Generate PPTX caller with Edge SRT: rebuild click-free object timings
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-padding 0.5 --force

# 2B. Re-export with audio embedded
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --no-merge --recorded-narration audio --narration-padding 0.5

# 2C. Merge page-local SRT against timing values read from the final PPTX
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 2D. Optional after PowerPoint exports the video: calibrate page starts against
# the actual video audio and write a same-stem sidecar SRT
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --video <powerpoint_exported_video> \
  -o exports/<powerpoint_exported_video_stem>.srt --force
```

If `notes_to_audio.py` errors with a missing dependency or missing provider API key, fix the prerequisite and re-run — do NOT swallow the error.

The edge command writes each MP3 and its SRT from the same `edge-tts` stream. SRT cues use the stream's `WordBoundary` timing: sentence-ending punctuation always closes a cue; text over the default 20-character limit first splits at commas, semicolons, or colons, then at the nearest word boundary only when still too long. Each SRT uses a page-local timeline whose origin is `00:00:00,000`, including any leading silence before the first cue. Override the limit with `--subtitle-max-chars`. Cloud-provider commands currently write audio only.

**Generate PPTX narration timing plan**: before `narration_sync.py animations`, compare every current SVG content group with that page's SRT and write `<project_path>/narration_timing.json`. Pin the plan to the ordered page-local SRT set with `srt_sha256`, and record the same `narration_padding` that the later PPTX export will use. Each slide contains one ordered `groups` list. Set `cue` to the matching 1-based SRT cue number; omit `cue` when the group has no spoken counterpart. The list must cover every non-static content group exactly once. The sync command rejects a stale SRT fingerprint, then rebuilds `animations.json` from scratch with `after-previous` timing; it does not migrate legacy narration fields. Matched groups wait for their cue, while unmatched groups follow the preceding animation with the page rhythm's normal stagger.

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

After the narrated PPTX is exported, `narration_sync.py subtitles` reads the actual presentation relationship order plus integer `advTm` and transition duration from every slide, then writes `<project_path>/notes/subtitles/total.srt`. Relative `--pptx` paths are project-relative. This produces the deck-wide SRT on the native PPTX timeline, including page transitions and narration padding.

PowerPoint video export may quantize each slide/media segment to the video frame clock, creating small page-boundary differences that accumulate across a long deck. When the finished video exists, pass it with `--video`. The command correlates each original page narration with the exported audio track and replaces only the theoretical page offsets; it preserves every page-local cue and rejects weak matches. This optional post-export calibration does not create or rewrite MP4.

This stage keeps subtitles as external SRT files. It does not embed subtitles into PPTX or export MP4 directly.

**Caller integration**:

| Caller | After audio generation |
|---|---|
| Generate PPTX | With Edge SRT, rebuild animations, export with `--recorded-narration audio`, then merge `total.srt` from the final PPTX. If PowerPoint later exports a video, optionally rerun the merge with `--video` for exact sidecar alignment. |
| Enhance Native PPTX | Return to [`native-enhance-pptx`](../native-enhance-pptx.md) Step 9; its `apply` command owns audio relationships, timings, transitions, and the enhanced export |

For Generate PPTX, `--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide must have a matching supported audio file, every duration must be readable by `ffprobe`, and object animations must not use `--animation-trigger on-click`. Use `after-previous` or `with-previous` for narrated/video export. Narration changes the slide-advance layer only: the resolved page-transition effect remains unchanged, `-t none` remains visually transition-free, and narration advance disables click while using audio duration plus padding. The re-export is saved as `exports/<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports.

**Narrated SVG export**: keep `--no-merge` on the final synchronized export. Separate SVG line frames preserve authored coordinates; default paragraph merging can make PowerPoint recalculate multiline text geometry and introduce visible offsets.

---

## Step 5: Completion report

Output one summary block listing:

- Number of audio files generated and their location (`<project_path>/audio/*`).
- For edge, number of matching page-local SRT files and their location (`<project_path>/notes/subtitles/*`).
- For Generate PPTX with Edge SRT, rebuilt animation group count and merged SRT path (`<project_path>/notes/subtitles/total.srt`).
- When `--video` was used, the calibrated sidecar SRT path, page-offset adjustment range, and minimum audio-correlation score.
- The provider, voice, and rate/settings actually used.
- The caller-owned integration result: narrated SVG export path, enhanced native PPTX path, or “audio only”.
- For Generate PPTX when embedding was skipped, one-line hint: `python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio`.
