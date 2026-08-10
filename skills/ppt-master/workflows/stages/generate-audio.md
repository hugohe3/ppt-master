---
description: Shared post-processing stage for narration audio, PPTX embedding, and optional native video export.
---

# Generate Audio Stage

> Shared narration stage. Run after the owning route's notes step. Edge, ElevenLabs, MiniMax, and timestamp-capable CosyVoice produce per-slide audio/SRT from synthesis timing. Qwen is audio-only because its TTS API exposes no timing. The caller owns final PPTX integration.

This stage is **context-independent**: it reads `notes/*.md` and queries the selected TTS voice catalog, so either owning route may invoke it in a fresh session. It does not choose the top-level route and does not patch slide design.

**Trigger**: In Generate PPTX, run when the effective `Narration Audio` outcome
in `design_spec.md` §I is `enabled`; a later explicit request first updates that
outcome and its provenance. Quick Generate instead runs when the request or
current agent's active-context decision selects narration. In Enhance Native
PPTX, run when its confirmed enhancement plan has `audio.enabled: true`.

**Hard dependency — speaker notes**: Audio requires complete per-slide speaker
notes. Generate PPTX additionally requires its effective `Speaker Notes`
outcome to be enabled; Enhance Native PPTX follows its confirmed notes/audio
plan, where enabling audio also enables notes. Quick records the same dependency
in active context. Do not enter audio generation while the owning route's notes
are missing or incomplete; generate and validate those notes first, then resume
this stage.

## When to Run

- Per-page narration files exist at `notes/*.md`. In Generate PPTX, split `notes/total.md` during Step 7.1. In Enhance Native PPTX, the notes module writes numeric files such as `001.md`.
- Default mode: `edge-tts` is installed (`python3 -m pip install edge-tts`).
- The stage is page-level only: one note becomes `audio/<stem>.<audio-ext>` plus `audio/<stem>.srt` on provider-timed paths, or one audio file with Qwen / explicit CosyVoice audio-only mode. Never substitute one long track or automatic splitting.
- Final/literal script notes are synthesized verbatim. Source SRT timecodes are pacing evidence only; new provider timing owns the generated audio/SRT set.
- SRT bound to an authoritative existing recording does not enter TTS. Recorded narration requires page-level audio or an explicit page/time map; automatic long-track splitting is unsupported.
- A fully successful run writes a compact `audio/manifest.json` with only provider/model, audio/subtitle format, relevant voice settings, and a SHA-256 fingerprint instead of the raw cloud voice ID. It has no per-slide inventory, artifact hashes, or API keys and is not a normal generation input. The flat `audio/` directory is the single active narration set; do not create provider subdirectories unless the user explicitly asks to preserve multiple variants.
- PPT narration assets must be PowerPoint-reliable audio: `m4a` (AAC), `mp3`, or `wav`. The built-in TTS path defaults to `mp3`; provider formats such as `pcm`, `opus`, or `flac` must be transcoded before embedding.
- PowerPoint recorded narration export requires `ffprobe` so slide timings can be written from actual audio duration.
- Optional automatic video export requires Windows PowerPoint 2016+ and runs
  through `powerpoint_video.py`; the command waits for PowerPoint's native
  encoder to finish before returning.
- macOS PowerPoint may export MP4/MOV manually, but it has no equivalent
  `CreateVideo` automation contract and its movie export does not preserve
  animation effects. Do not replace the missing API with UI scripting.
- Optional post-export video calibration requires `ffmpeg` plus `numpy`; it runs only after a finished PowerPoint video is supplied or created.
- High-quality cloud mode: provider API key is set before use:
  - ElevenLabs: `ELEVENLABS_API_KEY`
  - MiniMax: `MINIMAX_API_KEY`
  - Qwen: `QWEN_API_KEY` or `DASHSCOPE_API_KEY`
  - CosyVoice: `COSYVOICE_API_KEY` or `DASHSCOPE_API_KEY`
  - Keys may live in the current process environment or the first `.env` found in this order: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`
- The deck is in a single dominant language (mixed-language decks: pick the dominant one — the AI uses judgment, not a heuristic).

If per-slide notes are missing, recover through the owning route. Generate
PPTX returns to its enabled notes branch and then runs
`total_md_split.py <project_path>`; Enhance Native PPTX returns to
`native-enhance-pptx` Step 6 and writes numeric notes directly. Never run the
Generate splitter against a Native Enhance project.

---

## Step 1: Determine the deck's language

The AI already knows the deck's language from writing the notes. No detection script needed.

- Identify the primary language from the notes content: `zh` / `en` / `ja` / `ko` / etc.
- For mixed-language decks (e.g. Chinese with English technical terms), pick the language the audience will hear most of.
- For Chinese specifically: pick the locale based on context — `zh-CN` (mainland mandarin, default), `zh-TW` (Taiwanese mandarin), or `zh-HK` (Cantonese). Default Generate may ask when context is unclear; Quick chooses the best supported default and continues.

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
- **For CosyVoice subtitles**: use a cloned voice from a supported v3.5/v3/v2 model or a system voice marked timestamp-supported. Model and voice families must match. Use `--cosyvoice-audio-only` only when the user accepts no page-local SRT.
- **Match the deck's tone** — pick the strongest recommendation based on style:
  - Consultant / data-driven / 财报 → 稳重男声（如 `zh-CN-YunjianNeural`）or 清晰女声（如 `zh-CN-XiaoxiaoNeural`）
  - General / 教学 / 产品介绍 → 明亮女声 / 年轻男声（如 `zh-CN-XiaoyiNeural` / `zh-CN-YunxiNeural`）
  - 发布会 / 播报 → 播报感男声（如 `zh-CN-YunyangNeural`）
  - English consultant deck → `en-US-GuyNeural` (steady) or `en-US-JennyNeural` (clear)
  - Japanese / Korean → pick from `ja-JP-*` / `ko-KR-*` neural voices, mark gender + tone

For each candidate, write a **one-line Chinese description** covering: 性别 · 调性 · 适用场景。For cloud providers, include the voice name/ID exactly as it must be passed to `--voice-id`.

---

## Step 3: One-shot user interaction (mandatory)

Send a single message to the user that resolves all five configuration decisions at once and provides a recommended value for each. Before offering automatic video export, run `python3 skills/ppt-master/scripts/powerpoint_video.py --check`; do not present an unavailable local capability as executable. Do NOT split into multiple rounds.

**Cloned-voice fast path**: if the user mentioned a cloned voice / 克隆音色 / 复刻音色 / "my own voice" along with a `voice_id`, skip the voice-recommendation list — set the provider to whichever the user named (`elevenlabs` / `minimax` / `qwen` / `cosyvoice`), pin the `voice_id` they gave you, and only confirm rate + embed + video.

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
> **带音频 PPTX 完成后是否继续导出视频**：⭐ 推荐 **是**（仅在本机 Windows PowerPoint 2016+ 可用时；将等待原生视频导出完成）。
>
> 直接回"好"用全部推荐值，或告诉我想改的部分（如"音色 2，语速 -5%"或"用 MiniMax 的 voice_id xxx"）。

**Recommended-value rules**:
- 生成模式：默认 `edge`；用户指定 cloud provider / voice ID 时按其选择。需要逐页 SRT、字幕动画或视频字幕时不推荐 Qwen；用户坚持时，说明仅交付音频并跳过 SRT 步骤。
- 音色：从 Step 2 候选里挑最贴合 deck 调性的那一个。
- 语速：edge 默认 `+0%`；notes 字数密集（页均 >4 句长句）建议 `-5%`；notes 简短紧凑建议 `+5%`；超出此范围需说明理由。Cloud providers 默认用 provider defaults，除非用户明确要调速或改风格。
- 嵌入：默认推荐"是"；除非用户已有定制 PPTX 不希望覆盖。
- 视频：`powerpoint_video.py --check` 成功时默认推荐"是"；不可用时说明只能交付带音频 PPTX，不自动改用第三方渲染器。

---

## Step 4: Execute (no further interaction)

**Blocking notes preflight**: `notes_to_audio.py` resolves the complete notes
roster from `svg_output/*.svg` on Generate projects or
`analysis/slide_index.json` on Native Enhance projects. Before any TTS request,
every expected note must exist, be readable, and contain spoken text. Exit code
`2` returns the caller to its notes-generation step; never continue with partial
audio generation.

Run sequentially — do NOT bundle:

```bash
# 1A. Generate audio with edge (default)
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice <chosen-ShortName> --rate <chosen-rate>

# 1B. Or generate audio/SRT pairs with ElevenLabs
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs --voice-id <chosen-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 1C. Or generate audio with MiniMax
# Defaults to the China endpoint; set MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2 for overseas access.
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax --voice-id <chosen-voice-id> \
  --minimax-model speech-2.8-hd

# 1D. Or generate audio only with Qwen TTS (the API returns no timestamps)
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen --voice-id <chosen-voice> \
  --qwen-model qwen3-tts-flash --qwen-language-type Chinese

# 1E. Or generate audio/SRT pairs with a timestamp-capable CosyVoice voice
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice --voice-id <chosen-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 2A. Only when page-local SRT exists and animations.json is active, author or
#     refresh narration_timing.json
#     by matching SVG group semantics to SRT topics, then derive the narrated
#     sidecar. Reuse current SVG semantics when complete; otherwise read only
#     the missing or stale svg_output pages.
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-start-floor 0.8 --narration-padding 0.5 --force

# 2B. Re-export with audio embedded
#     Use the base export's [REPORT] path to preserve source-bound deck motion.
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --inherit-motion-from "<base_postflight_report>"

# Optional: use the canonical presentation animation instead
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --animation-config animations.json \
  --inherit-motion-from "<base_postflight_report>"

# Optional: export narration with no object or page-transition animation
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --no-animations

# 2C. Only when page-local SRT exists, merge it against timing values read
#     from the final PPTX
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 2D. Optional: export through installed Windows PowerPoint and wait for completion
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o <final_video.mp4>

# 2E. Only when page-local SRT exists, align the frozen narration text against
#     the finished video's audio track
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> \
  --video <final_video.mp4> --language <language> --force
```

**Default — bounded Edge concurrency (may override)**: Generate up to three
slide-level audio/SRT pairs concurrently. Use `--concurrency <N>` to tune the
Edge path or `--concurrency 1` for serial troubleshooting. Cloud providers
remain serial.

If `notes_to_audio.py` errors with a missing dependency or missing provider API key, fix the prerequisite and re-run — do NOT swallow the error.

The edge command writes each MP3 and its internal page SRT from the same `edge-tts` stream. SRT cues use the service's `WordBoundary` timing: sentence-ending punctuation always closes a cue; text over the default 20-visible-character limit first splits at commas, semicolons, or colons, then at the nearest word boundary. Override the limit with `--subtitle-max-chars`. Adjacent timing overlap up to 100 ms is tolerated by moving the later cue start to the previous cue end; larger overlap fails instead of silently distorting timing. Each SRT uses a page-local timeline whose origin is `00:00:00,000`, including any leading silence before the first cue.

MiniMax reads word timing from its synchronous subtitle file. ElevenLabs uses `/with-timestamps` and original-text character alignment. CosyVoice enables HTTP streaming plus `word_timestamp_enabled`, then uses the final audio URL and word timing from that synthesis; unsupported model/voice pairs fail without replacing the prior pair unless `--cosyvoice-audio-only` was explicit. Qwen exposes no timing, so it remains audio-only and this stage never estimates SRT timing.

Provider-timed paths share punctuation-first, `--subtitle-max-chars`-bounded regrouping, exact-text validation, and rollback-safe pair publication. See [`docs/audio-narration.md`](../../../../docs/audio-narration.md) for current model and audio-parameter recommendations.

Before generation starts, `notes_to_audio.py` removes stale `audio/manifest.json` and `audio/total.srt`; an incomplete run therefore cannot claim the previous set's provenance or merged timeline. A successful audio-only provider run also removes same-stem stale SRT files. The new manifest is published atomically only after the complete page roster succeeds.

**Mandatory when `animations.json` is consumed — semantic animation context**: Before writing or refreshing `<project_path>/narration_timing.json`, determine whether the active context already contains the current top-level SVG group IDs and visible group-content semantics for every affected page. Reuse that context without rereading SVG when it is complete and still matches the current `svg_output/`. If any page is missing, stale, or represented only by group IDs/order without content meaning, read only that page's SVG as a read-only source and extract the missing group semantics. Always combine those semantics with the page SRT topics/timestamps and `animations.json`; group order alone is not a semantic narration mapping.

> Active `animations.json` requires `narration_timing.json`; explicit `--no-animations` bypasses both. Without a sidecar, `narration_sync.py animations` maps groups **positionally** (group N → cue N) and warns when later objects may reveal during an earlier topic. Treat that warning as required repair: author the semantic plan and re-derive.

**Narration animation ownership**: When `animations.json` is consumed, it remains read-only. The audio stage deep-copies it to `narration_animations.json`, preserves transitions, effects, durations, order, and explicit `effect: none`, then changes only the derived trigger/delay values needed for click-free narration playback. The authored `narration_timing.json` maps each animated content group—not each effect row—to the SRT cue that speaks about that content. For `effects[]`, the cue anchors the group's first active row; later rows keep global order and their relative delay. The command may still read an affected SVG page to resolve structural group order when a sparse sidecar cannot identify every effective group; this structural fallback does not replace the semantic-context step and never edits SVG, notes, or `animations.json`. Unmatched groups keep their canonical relative delay.

**Title timing handoff when canonical animation exists**: preserve the title reveal decision already made by the custom-animation pass. Assign a title group to an SRT cue only when the user's request or the active motion plan explicitly chose `narration-cued`; otherwise leave its `cue` omitted in `narration_timing.json` so it keeps the canonical relative delay from `animations.json`. Do not infer `narration-cued` merely because speaker notes mention the title.

**Narrated export animation selection**:

| Sidecar state | Behavior |
|---|---|
| `narration_animations.json` exists | Use it by default |
| Only canonical `animations.json` exists | Block until narration synchronization creates the derived sidecar |
| Both are absent | Create no sidecar; inherit the base report's deck motion |

Generate passes the base report through `--inherit-motion-from`: inherited
`-a none` preserves explicit objects-off, while final Stage-2 `false` does not.
Only explicit all-motion-off uses `--no-animations`. Invalid reports block;
page-start lead-in, audio duration, and page-tail padding own final advance.

**Narration pacing controls**: page-front and page-tail timing are independent,
optional parameters. Unless the user supplies values, use
`narration_start_floor=0.8` seconds and `narration_padding=0.5` seconds without
adding a confirmation question. For a destination-page transition of `T`
seconds, the post-transition lead-in is
`max(0, narration_start_floor - T)`: narration never begins during the
transition, while a longer transition is not stretched. Apply the same
lead-in to embedded narration, cue-bound object animation, subtitle offsets,
and slide advance. Uncued title or decorative animation keeps its canonical
relative timing. Setting the start floor to `0` means narration begins as soon
as the transition completes; it does not bypass the transition.

When canonical custom animation is synchronized,
`<project_path>/narration_timing.json` is the explicit semantic mapping for
narrated object animation. It is fingerprinted to the ordered SRT set; `cue`
is the 1-based subtitle cue, and omitted `cue` keeps that group's canonical
relative delay. Reuse a complete current mapping when its fingerprint and SVG
group semantics remain valid; rebuild only affected pages when either input
changed.

Get the exact fingerprint value with:

```bash
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>
```

```json
{
  "version": 1,
  "srt_sha256": "<sha256 of the ordered page-local SRT set>",
  "narration_start_floor": 0.8,
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

`narration_sync.py subtitles` may still write `<project_path>/audio/total.srt` as a PPTX-timeline diagnostic. It is not the delivery subtitle for a finished video.

When video export was selected, `powerpoint_video.py` opens the final narrated PPTX through local Windows PowerPoint, requests its native video encoder with recorded timings and narrations enabled, and polls `CreateVideoStatus` until the MP4 succeeds, fails, or times out. The interface is synchronous to its caller even though PowerPoint performs encoding asynchronously. It preserves PowerPoint's own animation and media behavior rather than re-rendering the deck.

If native video export fails, keep the narrated PPTX as a successful upstream
artifact and report the video failure separately. Do not regenerate audio or
the PPTX unless their own validation failed.

After the MP4 exists, `video_subtitles.py` takes the exact narration text frozen in the page SRT set and force-aligns it against the finished video's actual audio track with `stable-ts`. Long delivery cues may be split for display at this final stage. This writes a same-stem external SRT without changing the MP4, notes, page SRT, or animation files.

This stage keeps subtitles as external SRT files. It does not burn subtitles into the video. Automatic MP4 export is an optional Windows PowerPoint integration, not an independent renderer; when PowerPoint automation is unavailable, stop after the narrated PPTX instead of claiming a downgraded video.

**Caller integration**:

| Caller | After audio generation |
|---|---|
| Generate PPTX | With page-local SRT from Edge, ElevenLabs, MiniMax, or timestamp-capable CosyVoice and an existing `animations.json`, derive `narration_animations.json`; with no sidecar, inherit the base report's resolved motion, while explicit all-motion-off uses `--no-animations`. Export with `--recorded-narration audio`, optionally continue through `powerpoint_video.py`, then generate the delivery SRT from the finished video. |
| Enhance Native PPTX | Return to [`native-enhance-pptx`](../native-enhance-pptx.md) Step 9; its `apply` command owns audio relationships, timings, transitions, and the enhanced export. If video was selected, pass that final PPTX to `powerpoint_video.py`. |

For Qwen or explicit CosyVoice audio-only mode, embed/export the audio normally but skip `narration_timing.json`, `narration_sync.py animations`, SRT merge, and final-video subtitle alignment. Never present those missing subtitle artifacts as generated.

For Generate PPTX, `--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide must have a matching supported audio file, every duration must be readable by `ffprobe`, and object animations must not use `--animation-trigger on-click`. Use `after-previous` or `with-previous` for narrated/video export. Narration changes the slide-advance layer only: the resolved page-transition effect remains unchanged, `-t none` remains visually transition-free, and narration advance disables click while using page-start lead-in plus audio duration plus page-tail padding. The re-export is saved as `exports/<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports.

**Narrated SVG export**: use the default text-flow mode. It keeps authored line breaks in one editable, no-wrap text frame; narration does not require per-line text frames.

---

## Step 5: Completion report

Output one summary block listing:

- Number of audio files generated and their location (`<project_path>/audio/*`).
- For provider-timed subtitles, number of matching page-local SRT files and their location (`<project_path>/audio/*`); for Qwen or explicit CosyVoice audio-only mode, report that no page-local SRT was generated.
- Narration provider/model plus the `<project_path>/audio/manifest.json` provenance path.
- For narrated object animation, whether current SVG semantics were reused or which missing/stale pages were reread, plus semantic mapping coverage and fallback count.
- For Generate PPTX with page-local SRT and canonical custom animation, derived narration animation group count and `narration_animations.json` path; otherwise report inherited base motion or explicit all-motion-off.
- When video export was selected, the final MP4 path and native PowerPoint export status.
- When a finished video exists, the final aligned sidecar SRT path.
- The provider, voice, and rate/settings actually used.
- The caller-owned integration result: narrated SVG export path, enhanced native PPTX path, or “audio only”.
- For Generate PPTX when embedding was skipped, one-line hint: `python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio`.
