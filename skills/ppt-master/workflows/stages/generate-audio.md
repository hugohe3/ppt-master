---
description: Shared post-processing stage for narration audio, PPTX embedding, PowerPoint video delivery, and triggered sound mixing.
---

# Generate Audio Stage

> Shared narration stage, run after the owning route's notes step. Edge, ElevenLabs, MiniMax, and timestamp-capable CosyVoice produce per-slide audio/SRT pairs; Qwen is audio-only because its API exposes no timing. The caller owns final PPTX integration. Context-independent: it reads `notes/*.md` and the selected voice catalog, chooses no route, and patches no slide design. Tool behavior, prerequisites, keys, and every flag are documented in [`narration.md`](../../scripts/docs/narration.md).

**Trigger**: Generate PPTX — the effective `Narration Audio` outcome in `design_spec.md` §I is `enabled` (a later explicit request first updates that outcome and provenance); Quick — the request or active-context decision selects narration; Edit Native PPTX — the confirmed plan enables narration.

**Hard dependency — speaker notes**: audio requires complete per-slide notes: Generate additionally requires its effective `Speaker Notes` outcome enabled; Edit Native follows its confirmed plan (a note for every output page); Quick records the same dependency. Never enter audio generation with missing or incomplete notes — generate and validate them first. Missing notes recover through the owning route: Generate returns to its notes branch and runs `total_md_split.py <project_path>`; Edit Native returns to [`edit-native-pptx`](../edit-native-pptx.md) §6 and writes `notes/<svg-stem>.md` per output page; never run the Generate splitter on a round-trip workspace.

## When to Run

- Per-page notes exist at `notes/*.md` — split from `notes/total.md` in Generate Step 7.1, or `notes/<svg-stem>.md` keyed by output page in Edit Native (roster from `page_plan.json`, copies inherit source notes).
- The stage is page-level only: one note → one audio file (plus SRT on provider-timed paths). Never substitute one long track or automatic splitting; SRT bound to an authoritative existing recording does not enter TTS, and recorded narration requires page-level audio or an explicit page/time map.
- Final/literal script notes are synthesized verbatim; source SRT timecodes are pacing evidence only.
- The deck is in one dominant language (mixed decks: pick the one the audience hears most — judgment, not a heuristic).
- Optional native video export runs only through `powerpoint_video.py` on Windows PowerPoint 2016+; slideshow capture is an explicit manual Windows handoff, never an automatic fallback; direct MP4 delivery with resolved sound cues additionally needs `ffmpeg` plus `numpy`.

---

## Step 1: Determine the deck's language

The AI already knows it from writing the notes — no detection script. Identify `zh` / `en` / `ja` / `ko` / …; for Chinese choose `zh-CN` (default), `zh-TW`, or `zh-HK` from context — Default may ask when unclear, Quick chooses the best supported default.

---

## Step 2: Choose audio backend and pull the voice catalog

Default to **edge** unless the user asks for a cloud provider, higher-quality cloud narration, or a cloned voice.

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale <locale>
python3 skills/ppt-master/scripts/notes_to_audio.py --provider <elevenlabs|minimax|qwen|cosyvoice> --list-voices
```

From the flat list, pick **3–6 candidates**: cover both genders when the locale has them; for edge prefer the curated `COMMON_VOICES` set; for ElevenLabs prefer voices already in the user's account and never override a user-supplied `voice_id`; for MiniMax / Qwen / CosyVoice use a supplied cloned `voice_id` directly and never attempt cloning here; for CosyVoice subtitles use a timestamp-capable model/voice pair, and `--cosyvoice-audio-only` only when the user accepts no page-local SRT. Match the deck's tone — a Chinese consultant / financial deck leans a steady male (`zh-CN-YunjianNeural`) or clear female (`zh-CN-XiaoxiaoNeural`) voice; teaching / product decks a bright female or young male (`zh-CN-XiaoyiNeural` / `zh-CN-YunxiNeural`); launch / broadcast decks `zh-CN-YunyangNeural`; English consultant decks `en-US-GuyNeural` or `en-US-JennyNeural`; Japanese / Korean from `ja-JP-*` / `ko-KR-*` with gender + tone noted. Describe each candidate in one line in the user's chat language (gender · tone · best-fit scenario), with the exact name/ID to pass to `--voice-id` for cloud providers.

---

## Step 3: Resolve generation settings

**Quick exception**: do not pause. Apply explicit user values, resolve the rest from the recommended-value rules, keep video off unless the caller selected direct video (then embed the narrated PPTX and continue to native video only when `powerpoint_video.py --check` succeeds); with resolved sound cues continue automatically through the post-export mix. An explicit slideshow-capture request stops at the capture-ready narrated PPTX until the user supplies the recorded MP4 — never silently switching to native export. Require a timestamp-capable provider only when cue sync or subtitle delivery needs page-local SRT.

**Default / Edit Native — one-shot interaction (mandatory)**: send one message that resolves all five decisions with a recommended value each; never split into rounds. Run `powerpoint_video.py --check` before offering automatic video export (an explicit slideshow-capture choice skips the check and uses the manual handoff). **Cloned-voice fast path**: when the user mentioned a cloned voice / 克隆音色 / 复刻音色 / "my own voice" with a `voice_id`, skip the recommendation list, pin the named provider and `voice_id`, and confirm only rate + embed + video. "Embed" means SVG re-export for Generate or `svg_to_pptx.py --roundtrip --recorded-narration audio` for Edit Native.

**Message template** (Chinese; translate to the user's chat language):

> 检测到 notes 主语言为 **<语言>**（locale: `<locale>`）。基于 deck 调性（<风格>），我推荐以下配置：
>
> **生成模式**：⭐ 推荐 `<edge|elevenlabs|minimax|qwen|cosyvoice>`（理由：<一句话>）。
>
> **音色**：
> - **[1] <ShortName>** — <性别·调性·适用场景> ⭐ **推荐**
> - [2] <ShortName> — <性别·调性·适用场景>
> - [3] <ShortName> — <性别·调性·适用场景>
> - 也可直接输入清单中的其他 ShortName。
>
> **语速/风格参数**：⭐ 推荐 `<rate or provider defaults>`（理由：<一句话>）。
>
> **生成完是否重新导出嵌入音频的 PPTX**：⭐ 推荐 **是**（一次到位，自动按音频时长设页面停留）。
>
> **带音频 PPTX 完成后是否继续导出视频**：⭐ 推荐 **原生编码**（本机 Windows PowerPoint 2016+ 可用时）。需要录下实际放映声音时可选 **实时放映录制**。
>
> 直接回"好"用全部推荐值，或告诉我想改的部分（如"音色 2，语速 -5%"或"用 MiniMax 的 voice_id xxx"）。

**Recommended-value rules**: mode — `edge` by default, the user's named provider/voice otherwise; never recommend Qwen when page-local SRT, subtitle animation, or video subtitles are needed, and if the user insists state that only audio is delivered. Voice — the Step 2 candidate that best fits the tone. Rate — edge `+0%`; `-5%` for dense notes (>4 long sentences per page), `+5%` for short tight notes, anything beyond needs a stated reason; cloud providers keep defaults unless asked. Embed — yes unless the user has a customized PPTX they do not want overwritten. Video — native encoding when `--check` succeeds; slideshow capture only on explicit choice; when automation is unavailable, deliver the narrated PPTX and never switch to screen recording or a third-party renderer.

---

## Step 4: Execute (no further interaction)

`notes_to_audio.py` runs a blocking notes preflight (every expected note exists, is readable, and contains spoken text); exit `2` returns the caller to notes generation — never continue with partial audio. Run sequentially, never bundled; if a dependency or API key is missing, fix it and re-run, never swallow the error.

```bash
# 1. Generate audio (one provider form; flags in narration.md)
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --voice <ShortName> --rate <rate>
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider <elevenlabs|minimax|qwen|cosyvoice> --voice-id <id> [provider model flag]

# 2A. Only when narration-cue sync is selected and page SRT + animations.json exist
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> --narration-start-floor 0.8 --narration-padding 0.5 --force

# 2B. Re-export with audio embedded (Quick adds --quick-generate --with-notes; the native-export
#     mix branch also passes --conversion-trace <final_narrated_trace>)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio --narration-start-floor 0.8 --narration-padding 0.5 --inherit-motion-from "<base_postflight_report>"
#     narration-independent custom motion: add --animation-config animations.json; all-motion-off: --no-animations instead of --inherit-motion-from

# 2C. Only when page-local SRT exists
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> --pptx <final_narrated_pptx> --force

# 2D. Optional native video through installed Windows PowerPoint
python3 skills/ppt-master/scripts/powerpoint_video.py <final_narrated_pptx> -o <raw_powerpoint_video.mp4>

# 2E. Only when final resolved motion has sound cues and direct MP4 delivery is selected
python3 skills/ppt-master/scripts/video_sound_mix.py <project_path> --pptx <final_narrated_pptx> --trace <final_narrated_trace> --video <raw_powerpoint_video.mp4> -o <final_mixed_video.mp4> --stem-output <final_sfx_stem.wav> --report-output <sound_mix_report.json> --force

# 2F. Only when page-local SRT exists: align against the final delivery video (mixed, captured, or raw)
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> --video <final_delivery_video.mp4> --language <language> --force
```

**Mandatory when narration-cue sync is selected — semantic animation context**: before writing or refreshing `narration_timing.json`, confirm the active context holds the current top-level SVG group IDs and visible group-content semantics for every affected page; reuse it without rereading when complete and still matching `svg_output/`, otherwise read only the missing or stale pages read-only. Combine those semantics with the page SRT topics/timestamps and `animations.json` — group order alone is not a semantic mapping, and the positional fallback's warning is required repair. Preserve the title reveal decision from the custom-animation pass: assign a title group a `cue` only when the user or the motion plan explicitly chose `narration-cued`; never infer it because notes mention the title.

| Sidecar state | Narrated export |
|---|---|
| `narration_animations.json` exists and cue sync is selected | Use it |
| Only canonical `animations.json` exists and cue sync is selected | Block until synchronization creates the derived sidecar |
| Canonical `animations.json` exists and motion is narration-independent | `--animation-config animations.json`; claim no object sync |
| Both absent | No sidecar; inherit the base report's deck motion |

Pacing defaults are `narration_start_floor=0.8` s and `narration_padding=0.5` s without a confirmation question unless the user supplies values. For Qwen or explicit CosyVoice audio-only mode, embed/export normally but skip `narration_timing.json`, `narration_sync.py animations`, SRT merge, and final-video subtitle alignment; pass canonical narration-independent motion explicitly when present; a native-export sound mix may still run from page audio. Never present missing subtitle artifacts or object sync as generated.

**Explicit slideshow capture**: desktop Windows PowerPoint plays the final narrated PPTX full-screen from the beginning with automatic timing; capture only the deck frame and one application/system-audio source with mic, UI, pointer, and notifications absent; trim short head/tail handles; human-check streams, narration, every cue once, complete motion, and no dropped frames. The capture has no machine cue receipt and never enters `video_sound_mix.py`. If the host cannot capture, report only the capture-ready PPTX handoff; align page SRT against an accepted capture and append one compact `workflow_log.py` note. If native video export fails, keep the narrated PPTX as the successful upstream artifact and report the video failure separately. Subtitles stay external SRT and are never burned in.

| Caller | After audio generation |
|---|---|
| Generate PPTX | Derive narration-cued motion when selected; otherwise pass canonical motion, inherit base motion, or use explicit all-motion-off. Export with `--recorded-narration audio` (Quick also `--quick-generate --with-notes`). Native video uses conversion trace plus raw export and cue mix as required; explicit capture returns the narrated PPTX for the handoff, skips trace-only sound work and mixing, then aligns subtitles against the accepted capture |
| Edit Native PPTX | Return to [`edit-native-pptx`](../edit-native-pptx.md) §7 and export with `--roundtrip --recorded-narration audio --use-narration-timings`; native video passes the final PPTX to `powerpoint_video.py`; explicit capture uses the same handoff and skips mixing |

---

## Step 5: Completion report

One summary block: audio file count and location (`<project_path>/audio/*`); page-local SRT count and location, or "no page-local SRT" for Qwen / CosyVoice audio-only; provider/model plus the `audio/manifest.json` path; for narrated object animation, whether SVG semantics were reused or which pages were reread, plus mapping coverage and fallback count; for Generate, the derived narration animation coverage/path, the canonical config path for narration-independent motion, or the inherited/all-motion-off state; the raw PowerPoint MP4 path/status when native export was selected, and with sound mixing the final mixed MP4, SFX stem, cue count, and `video_sound_mix.py` receipt (otherwise the raw MP4 is final); for slideshow capture, the capture-ready PPTX handoff or accepted MP4 plus system-audio and human picture/narration/all-cue status, never a mix receipt; the PPTX-timeline `audio/total.srt` path when merged; the aligned delivery SRT path and its source video when alignment ran; provider, voice, and rate/settings used; the caller-owned integration result (narrated export path, enhanced native PPTX path, or "audio only"); and, when Generate embedding was skipped, the one-line hint `python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio`.
