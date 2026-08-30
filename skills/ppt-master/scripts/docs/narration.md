# Narration Tools

Tool behavior behind the [`generate-audio`](../../workflows/stages/generate-audio.md) stage: `notes_to_audio.py`, `narration_sync.py`, the narrated `svg_to_pptx.py` export, `powerpoint_video.py`, `video_sound_mix.py`, and `video_subtitles.py`. The stage owns when each runs and what the user confirms; this page owns what the tools do. Model and audio-parameter recommendations live in [`docs/audio-narration.md`](../../../../docs/audio-narration.md).

## Prerequisites

- `edge-tts` for the default backend (`python3 -m pip install edge-tts`); `ffprobe` for recorded-narration export (slide timings come from actual audio duration); `ffmpeg` plus `numpy` for post-export video calibration and the sound mix.
- Cloud keys: ElevenLabs `ELEVENLABS_API_KEY`; MiniMax `MINIMAX_API_KEY` (China endpoint by default; `MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2` for overseas); Qwen `QWEN_API_KEY` or `DASHSCOPE_API_KEY`; CosyVoice `COSYVOICE_API_KEY` or `DASHSCOPE_API_KEY`. Keys come from the process environment or the first `.env` found in: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`.
- Automatic video export requires Windows PowerPoint 2016+. macOS PowerPoint has no `CreateVideo` automation contract and its manual movie export drops animation effects; UI scripting is not a substitute.

## `notes_to_audio.py`

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale <locale>              # edge
python3 skills/ppt-master/scripts/notes_to_audio.py --provider <elevenlabs|minimax|qwen|cosyvoice> --list-voices
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --voice <ShortName> --rate <rate> [--concurrency <N>]
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider elevenlabs --voice-id <id> --elevenlabs-model eleven_multilingual_v2
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider minimax --voice-id <id> --minimax-model speech-2.8-hd
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider qwen --voice-id <voice> --qwen-model qwen3-tts-flash --qwen-language-type Chinese
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider cosyvoice --voice-id <voice> --cosyvoice-model cosyvoice-v3-flash [--cosyvoice-audio-only]
```

- **Roster preflight**: the notes roster comes from `svg_output/*.svg` on Generate projects or from `page_plan.json` / the identity roster on round-trip workspaces (copies inherit source notes). Every expected note must exist, be readable, and contain spoken text before any TTS request; exit code `2` returns the caller to notes generation. Narration text is read verbatim; only `# ...` heading lines are skipped.
- **Outputs**: one `audio/<stem>.<ext>` per note plus `audio/<stem>.srt` on provider-timed paths (edge, ElevenLabs, MiniMax, timestamp-capable CosyVoice); Qwen and explicit `--cosyvoice-audio-only` write audio only. The flat `audio/` directory is the single active set — no provider subdirectories unless the user asks to keep variants. Stale `audio/manifest.json` and `audio/total.srt` are removed before generation; a successful audio-only run also removes same-stem stale SRT; the manifest (provider/model, formats, voice settings, SHA-256 voice fingerprint — no per-slide inventory, hashes, or keys) is published atomically only after the complete roster succeeds.
- **Formats**: PowerPoint-reliable audio is `m4a` (AAC), `mp3`, or `wav`; edge defaults to `mp3`; provider `pcm` / `opus` / `flac` output must be transcoded before embedding.
- **Edge SRT**: MP3 and page SRT come from the same `edge-tts` stream using `WordBoundary` timing. Sentence-ending punctuation always closes a cue; text over the 20-visible-character default (`--subtitle-max-chars`) splits at commas, semicolons, or colons, then at the nearest word boundary. Adjacent overlap up to 100 ms moves the later cue start to the previous end; larger overlap fails. Each SRT uses a page-local timeline starting at `00:00:00,000` including leading silence. Default concurrency is three slide pairs (`--concurrency 1` for serial troubleshooting); cloud providers stay serial.
- **Provider timing**: MiniMax reads word timing from its synchronous subtitle file; ElevenLabs uses `/with-timestamps` with original-text character alignment; CosyVoice enables HTTP streaming plus `word_timestamp_enabled` and uses the final audio URL and word timing — unsupported model/voice pairs fail without replacing the prior pair unless `--cosyvoice-audio-only` was explicit (model and voice families must match; cloned voices need a supported v3.5/v3/v2 model or a timestamp-supported system voice); Qwen exposes no timing and never gets estimated SRT. Provider-timed paths share punctuation-first, `--subtitle-max-chars`-bounded regrouping, exact-text validation, and rollback-safe pair publication.

## `narration_sync.py`

```bash
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> --narration-start-floor 0.8 --narration-padding 0.5 --force
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> --pptx <final_narrated_pptx> --force
```

- `animations` deep-copies read-only `animations.json` to `narration_animations.json`, preserving transitions, effects, durations, order, and explicit `effect: none`, and changes only the derived trigger/delay values needed for click-free playback. `<project_path>/narration_timing.json` maps each animated content group (not each effect row) to the 1-based SRT `cue` that speaks about it; for `effects[]` the cue anchors the group's first active row and later rows keep global order and relative delay; an omitted `cue` keeps the group's canonical relative delay. The file is fingerprinted to the ordered SRT set (`srt_sha256`, from the `fingerprint` subcommand); reuse a complete current mapping when fingerprint and group semantics remain valid, rebuild only affected pages otherwise. Without a timing sidecar the command maps groups positionally (group N → cue N) and warns when later objects may reveal during an earlier topic — treat that warning as required repair. The command may read an affected SVG page to resolve structural group order for a sparse sidecar; it never edits SVG, notes, or `animations.json`.
- `subtitles` merges page-local SRT against timing read from the final PPTX and may write `audio/total.srt` as a PPTX-timeline diagnostic; it is not the delivery subtitle for a finished video.

```json
{
  "version": 1,
  "srt_sha256": "<sha256 of the ordered page-local SRT set>",
  "narration_start_floor": 0.8,
  "narration_padding": 0.5,
  "slides": {"01_title": {"groups": [{"id": "page-title", "cue": 1}, {"id": "supporting-visual"}]}}
}
```

## Narrated `svg_to_pptx.py` export

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio --narration-start-floor 0.8 --narration-padding 0.5 --inherit-motion-from "<base_postflight_report>"
#   [--animation-config animations.json]  canonical narration-independent motion
#   [--no-animations]                     explicit all-motion-off
#   [--quick-generate --with-notes]       Quick projects
#   [--conversion-trace <final_narrated_trace>]  native-export mix branch
```

- `--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide needs a matching supported audio file with an `ffprobe`-readable duration, and object animations may not use `--animation-trigger on-click` (use `after-previous` / `with-previous`). Narration changes only the slide-advance layer — the page-transition effect is unchanged, `-t none` stays transition-free, and advance disables click while using page-start lead-in + audio duration + page-tail padding. Output is `exports/<project_name>_<timestamp>_narrated.pptx`.
- **Pacing**: `narration_start_floor` (default `0.8` s) and `narration_padding` (default `0.5` s) are independent. For a destination-page transition of `T` seconds the post-transition lead-in is `max(0, narration_start_floor - T)` — narration never starts during the transition and a longer transition is not stretched; the same lead-in applies to embedded narration, cue-bound object animation, subtitle offsets, and slide advance; uncued title or decorative animation keeps canonical relative timing; a floor of `0` starts narration as soon as the transition completes.
- `--inherit-motion-from` preserves source-bound deck motion from the base export report: inherited `-a none` preserves explicit objects-off, while a final Stage-2 `false` does not; only explicit all-motion-off uses `--no-animations`; invalid reports block. Text uses the default flow mode (authored line breaks in one editable no-wrap frame).
- Edit Native PPTX exports with `--roundtrip --recorded-narration audio --use-narration-timings`.

## `powerpoint_video.py`

```bash
python3 skills/ppt-master/scripts/powerpoint_video.py --check
python3 skills/ppt-master/scripts/powerpoint_video.py <final_narrated_pptx> -o <raw_powerpoint_video.mp4>
```

Opens the final narrated PPTX in local Windows PowerPoint, requests the native encoder with recorded timings and narrations, and polls `CreateVideoStatus` until success, failure, or timeout — synchronous to its caller. It preserves the native visual-animation and narration path but does not reliably write transition or object-animation sounds into the MP4 audio track. A native-export failure leaves the narrated PPTX as a successful upstream artifact; do not regenerate audio or the PPTX unless their own validation failed.

## `video_sound_mix.py`

```bash
python3 skills/ppt-master/scripts/video_sound_mix.py <project_path> --pptx <final_narrated_pptx> --trace <final_narrated_trace> --video <raw_powerpoint_video.mp4> -o <final_mixed_video.mp4> --stem-output <final_sfx_stem.wav> --report-output <sound_mix_report.json> --force
```

Cross-checks the final narrated trace against the PPTX read-back, extracts the exact embedded sound relationships, calibrates every page against the raw video's narration, renders a float SFX stem, and mixes it with narration at unity gain — transition cues about 35%, object cues about 25%, no `amix` normalization or ducking, a -1 dBFS peak limiter after the mix. The receipt must prove a non-silent stem, preserved video-stream hash, changed and present final audio, duration parity, non-clipping true peak, and correlation between the added audio component and the stem; a valid `animations.json` or OOXML package alone is not MP4 audio acceptance. Audio-only narration can still calibrate from its complete per-page tracks. A slideshow capture must never enter this tool.

## `video_subtitles.py`

```bash
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> --video <final_delivery_video.mp4> --language <language> --force
```

Force-aligns the narration text frozen in the page SRT set against the finished video's audio track with `stable-ts` — the mixed MP4 when mixing ran, the accepted capture when slideshow recording ran, otherwise the raw PowerPoint MP4. Long cues may be split for display here. Writes a same-stem external SRT without changing the MP4, notes, page SRT, or animation files; subtitles are never burned in.
