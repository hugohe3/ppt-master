# Audio Narration & Video Export

[English](./audio-narration.md) | [Chinese](./zh/audio-narration.md)

---

PPT Master can turn the speaker notes into per-slide narration via [`edge-tts`](https://github.com/rany2/edge-tts) (Microsoft Edge's online neural voices) by default, or via ElevenLabs, MiniMax, Qwen TTS, and CosyVoice when you need higher-quality cloud narration or a cloned voice. Edge, ElevenLabs, MiniMax, and timestamp-capable CosyVoice voices generate page-local SRT from provider timing returned with the same synthesis. Qwen remains audio-only because its current TTS API exposes no timestamps. The audio can then be embedded back into the PPTX for PowerPoint's native video export.

## What you get

- One audio file per slide under `<project_path>/audio/`, named to match the SVG (`01_cover.mp3`, `02_market_landscape.mp3`, …).
- With provider-timed subtitles, one matching subtitle file per slide in the same `<project_path>/audio/` directory (`01_cover.srt`, `02_market_landscape.srt`, …). Each file uses a page-local timeline with a `00:00:00,000` origin. Provider word/character timings are regrouped into the same compact cue format.
- One compact `<project_path>/audio/manifest.json` after a complete successful run. It records only provider/model, audio/subtitle format, relevant voice settings, and a SHA-256 fingerprint instead of a raw cloud voice ID. It contains no per-slide inventory, artifact hashes, or API keys and is not loaded during normal generation.
- When narration-cue synchronization is selected, canonical `animations.json` and page-local SRT derive `narration_animations.json`, whose click-free object animations wait for the relevant subtitle cue. Narration-independent custom motion keeps canonical timing instead. When neither animation sidecar exists, narrated export creates no sidecar and inherits the base export's resolved motion. With page-local SRT, these paths can produce a deck-wide `<project_path>/audio/total.srt` aligned to the final PPTX timeline; after PowerPoint exports a video, `video_subtitles.py` can align the frozen narration text against its actual audio track for a delivery sidecar SRT.
- Optional re-export: a new PPTX in `exports/` with each `m4a` / `mp3` / `wav` file embedded into the matching slide and slide auto-advance timings set from the configurable page-start floor, audio length, and page-tail padding, so kiosk/auto-play and video export work without manual timing. Narration never starts before the page transition finishes.
- Optional native video export on Windows: `powerpoint_video.py` delegates the final narrated PPTX to PowerPoint 2016+ and waits until its native MP4 encoder succeeds or fails. This raw MP4 preserves the visual animation/narration path, but PowerPoint does not reliably include native transition or object-animation sounds in its audio track.
- On the native-export path, when direct MP4 delivery has resolved animation sound cues, `video_sound_mix.py` produces an independent float SFX WAV, a final mixed MP4, and a JSON receipt proving the stem reached the actual final audio while the video stream stayed unchanged.
- As an explicit manual alternative, desktop Windows PowerPoint can play the final narrated deck full-screen while a recorder captures the presentation picture and one application/system-audio source. This records the narration and native cues PowerPoint actually plays, so it must not be followed by `video_sound_mix.py`.
- The original speaker notes are preserved.

## How it works

1. **Speaker notes are written as pure spoken narration.** PPT Master's notes spec deliberately produces TTS-friendly prose — no bracketed stage markers, no `Key points:` / `Duration:` meta-lines — so what is read aloud is exactly what's on the page.
2. **AI picks the voice for you.** When you ask for narration, the AI checks the deck's primary language (`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …), pulls the selected provider's voice catalog, and recommends 3–6 candidates with a one-line tone description for each (e.g. "steady male voice for financial reporting"). It also recommends a speaking rate or provider defaults based on notes density.
3. **Settings resolve once.** Default Generate and Enhance Native ask once for provider, voice, rate, embedding, and optional video export. Quick uses explicit values and automatically resolves unspecified provider, voice, rate, and embedding choices; video remains off unless direct video delivery was requested.
4. **Generation runs.** Edge, ElevenLabs, MiniMax, and timestamp-capable CosyVoice voices write each page's audio and SRT from provider timing returned by the same synthesis; Qwen and explicit CosyVoice audio-only mode write audio only. A complete run atomically writes `audio/manifest.json` for provenance. For Generate PPTX with narration-cue synchronization, page-local SRT and canonical custom animation let the AI map current SVG content groups to numbered SRT cues and derive click-free `narration_animations.json`; narration-independent custom motion keeps canonical timing, while no animation sidecar inherits the base export's resolved motion. It then re-exports the deck with audio attached and, when page-local SRT exists, merges it using timing values read from that final PPTX. Automatic video delivery continues through PowerPoint's native encoder and, when cues exist, the verified sound mix. An explicitly selected slideshow capture instead records PowerPoint's real-time full-screen picture and system audio, skips that mixer, and aligns any delivery SRT against the accepted capture. Long-audio import and automatic long-audio splitting are not supported.

Subtitles remain external artifacts: PPT Master does not embed them into the PPTX or burn them into the MP4. Automatic video export delegates to installed Windows PowerPoint; it is not a separate renderer.

The shared stage is documented in [`workflows/stages/generate-audio.md`](../skills/ppt-master/workflows/stages/generate-audio.md).

## Two embedding paths

| Command | Purpose |
|---|---|
| `--recorded-narration audio` | Prepare PowerPoint's recorded timings and narrations. Requires complete per-slide audio and writes page auto-advance timings. Use this for narrated/video export. The re-export is saved as `exports/<name>_<timestamp>_narrated.pptx`. |
| `--narration-audio-dir audio` | Lower-level audio embedding. Embeds matched files and allows partial coverage. Use this for testing or manual PowerPoint finishing. Exports get the same `_narrated` name suffix. |
| `--narration-start-floor 0.8` | Optional minimum seconds from the start of the destination-page transition to narration. The default is `0.8`; `0` means start as soon as the transition completes. |
| `--narration-padding 0.5` | Optional silent hold after narration finishes and before the slide advances. The default is `0.5`. |

Both timing options may be omitted or overridden independently. The actual silence after a transition is `max(0, narration_start_floor - transition_duration)`; changing the floor never stretches the transition itself.

## Triggering it

Just say so in chat after the deck has been exported:

```
You: Generate narration audio for this deck
You: Generate narration for this deck and re-export with audio embedded.
You: Add Japanese voice narration; pick a calm female voice.
```

The Generate route also runs this stage when final Stage 2 resolves effective
Narration Audio to enabled. A later explicit request still wins over the
proactive default. The AI handles the rest.

## Languages

Anything `edge-tts` supports — roughly 90 locales including all major Chinese variants (`zh-CN` / `zh-TW` / `zh-HK` Cantonese), English (US/UK/AU/IN), Japanese, Korean, French, German, Spanish, Portuguese, Russian, Arabic, etc. List voices for any locale yourself with:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale ja-JP
```

## Manual usage (advanced)

If you want to skip the AI flow and call the script directly:

```bash
# 1. Make sure speaker notes are split (post-processing Step 7.1):
python3 skills/ppt-master/scripts/total_md_split.py <project_path>

# 2A. Generate MP3/SRT pairs with edge-tts (default, no API key)
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice zh-CN-YunjianNeural --rate +0%

# 2B. Or generate MP3/SRT pairs with ElevenLabs (requires ELEVENLABS_API_KEY)
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs \
  --voice-id <elevenlabs-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 2C. Or generate MP3/SRT pairs with MiniMax (supports system and cloned voice_id)
export MINIMAX_API_KEY="your-minimax-api-key"
# Defaults to the China endpoint. For overseas access, set MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2.
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax \
  --voice-id <minimax-voice-id> \
  --minimax-model speech-2.8-hd

# 2D. Or generate audio only with Qwen TTS (system voice or cloned voice)
export DASHSCOPE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen \
  --voice-id <qwen-voice> \
  --qwen-model qwen3-tts-flash \
  --qwen-language-type Chinese

# 2E. Or generate MP3/SRT pairs with a timestamp-capable CosyVoice voice
export COSYVOICE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice \
  --voice-id <cosyvoice-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 3-4. Only when narration-cue sync is selected and page-local SRT plus canonical
#    animations.json exist, print the SRT-set fingerprint, then author
#    <project_path>/narration_timing.json by comparing each current
#    SVG content group with the numbered cues in that page's SRT. A missing
#    cue means the group has no spoken counterpart and uses normal sequencing.
#    For narration-independent custom motion or no sidecar, skip to step 5.
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>

# 4. Derive click-free narration_animations.json from canonical animations.json
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-start-floor 0.8 --narration-padding 0.5 --force

# 5A. Cue-synchronized custom motion: use the derived sidecar
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --animation-config narration_animations.json \
  --inherit-motion-from "<base_postflight_report>"

# 5B. Narration-independent custom motion: use canonical timing
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --animation-config animations.json \
  --inherit-motion-from "<base_postflight_report>"

# 5C. No animation sidecar: inherit resolved base motion, including -a auto
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --inherit-motion-from "<base_postflight_report>"

# Quick Generate appends --quick-generate --with-notes to the selected command.
# For the native-export mix branch with resolved sound cues, also append
# --conversion-trace <final_narrated_trace>. Slideshow capture does not need
# that trace for sound delivery.

# 6. When page-local SRT exists, merge it using the final PowerPoint timings
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 7. Optional on Windows: export the raw video through PowerPoint and wait
#    for completion
python3 skills/ppt-master/scripts/powerpoint_video.py --check
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o exports/<raw_powerpoint_video>.mp4

# 8. On the native-export branch, when final resolved motion has sound cues,
#    build the independent SFX stem and verified mixed video. Defaults:
#    transitions about 35%, object cues about 25%, final limiter -1 dBFS.
python3 skills/ppt-master/scripts/video_sound_mix.py <project_path> \
  --pptx <final_narrated_pptx> \
  --trace <final_narrated_trace> \
  --video exports/<raw_powerpoint_video>.mp4 \
  -o exports/<final_mixed_video>.mp4 --force

# 9. When page-local SRT exists, align the frozen narration text against the
#    final video's audio track: mixed when step 8 ran, accepted capture when
#    slideshow recording was selected, otherwise raw.
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> \
  --video "<final_delivery_video>" --language <language> --force
```

Before sending any TTS request, `notes_to_audio.py` verifies that every
Generate SVG page or Native Enhance slide has a readable, non-empty per-slide
note. Missing or empty notes return exit code `2`; generate those notes first,
then rerun audio generation.

For edge, `--voice` is required. Use `--list-voices --locale <locale>` to see what's available.
Edge generates up to three slide-level audio/SRT pairs concurrently by default.
Use `--concurrency <N>` to tune it or `--concurrency 1` for serial
troubleshooting. Cloud providers remain serial.

The edge command creates `audio/<stem>.mp3` and `audio/<stem>.srt` from the same streaming request. Sentence-ending punctuation closes a cue. A cue over 20 visible characters first splits at commas, semicolons, or colons, then at the nearest word boundary only if it is still too long. Use `--subtitle-max-chars` to change the limit. Adjacent timing overlap up to 100 ms is tolerated by moving the later cue start to the previous cue end; larger overlap fails. Each SRT uses a page-local timebase with a zero origin and preserves edge's `WordBoundary` timing, including any leading silence before the first cue.

MiniMax requests word-level subtitles on the same non-streaming T2A request and downloads the returned JSON timing file. ElevenLabs uses its `/with-timestamps` endpoint and reads original-text character alignment from the same JSON response. CosyVoice enables HTTP streaming plus `word_timestamp_enabled`, then uses the complete audio URL and word timings returned by that synthesis. All four provider-timed paths apply the same punctuation-first, `--subtitle-max-chars`-bounded regrouping and atomically publish a validated audio/SRT pair. Their compact cues are the semantic animation-mapping units.

CosyVoice timestamp support is model/voice-specific: cloned voices from `cosyvoice-v3.5-plus`, `cosyvoice-v3.5-flash`, `cosyvoice-v3-plus`, `cosyvoice-v3-flash`, and `cosyvoice-v2` are supported, as are system voices explicitly marked timestamp-capable in the [CosyVoice voice list](https://help.aliyun.com/en/model-studio/cosyvoice-voice-list). The model and voice family must match. If a selected voice cannot return timing and audio-only output is intentional, pass `--cosyvoice-audio-only`.

Qwen's current TTS HTTP and realtime responses return audio but no word or character alignment. PPT Master therefore keeps Qwen audio-only instead of estimating SRT timing. Choose Edge, ElevenLabs, MiniMax, or a timestamp-capable CosyVoice voice when page-local subtitles are required.

### Provider capability and parameter choices

| Provider | Page-local SRT | Provider timing | Current default decision |
|---|---|---|---|
| Edge | Yes | Word | Keep the selected neural voice and `+0%` unless notes density calls for a small rate adjustment. |
| ElevenLabs | Yes | Original-text character alignment | Keep `eleven_multilingual_v2` and `mp3_44100_128` for stable long-form narration. Use `--elevenlabs-speed 0.7-1.2` for an explicit pace override; `eleven_v3` is more expressive but more variable, while Flash v2.5 favors latency/cost. |
| MiniMax | Yes | Word | Keep the existing `speech-2.8-hd`, 32 kHz mono MP3 defaults unless the selected voice or delivery target requires otherwise. |
| Qwen | No | None in the current TTS response | Keep stable `qwen3-tts-flash`; specify the exact `--qwen-language-type` for a single-language deck. The current endpoint owns WAV output and exposes no format/sample-rate/numeric speed controls; an Instruct model can still control delivery through instructions. Do not switch models merely to claim unavailable timestamps. |
| CosyVoice | Conditional | Word | Keep `cosyvoice-v3-flash` plus 24 kHz MP3 as the system-voice-compatible default. Select the model that owns a cloned/designed voice; v3.5 voices require an explicit matching v3.5 model. |

The CLI rejects out-of-range ElevenLabs stability/similarity/style values, ElevenLabs speed outside `0.7-1.2`, and CosyVoice volume/rate/pitch or sample rates outside the provider's documented ranges before any request is sent.

These decisions follow the current [ElevenLabs speech-with-timing API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps), [ElevenLabs model guide](https://elevenlabs.io/docs/overview/capabilities/text-to-speech), [Qwen TTS API](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api), and [Qwen-Audio-TTS/CosyVoice HTTP API](https://help.aliyun.com/en/model-studio/cosyvoice-tts-http-api). Alibaba Cloud now recommends a workspace-specific Beijing domain for the CosyVoice HTTP endpoint; pass it through `--cosyvoice-base-url` when available. The legacy domain remains functional.

Alibaba Cloud's current [TTS model guide](https://www.alibabacloud.com/help/en/model-studio/tts-model/) recommends Qwen-Audio 3.0 for new preset/cloned-voice workflows. Those model IDs use the Qwen-Audio-TTS/CosyVoice API and a different voice contract, and still do not provide timestamps. PPT Master therefore does not silently replace the compatible `qwen3-tts-flash` default; migrate the model and its matching voice explicitly when audio quality is the reason, not subtitle parity.

`audio/` is the single active narration set. The manifest records its source, so provider subdirectories are not created by default. Before regeneration, the script removes stale `manifest.json` and `total.srt`; audio-only providers also remove same-stem stale page SRT files. Use a separate explicit output directory only when you intentionally need to preserve an alternate provider run.

When narration-cue synchronization is selected with canonical custom animation, `narration_timing.json` remains deliberately separate from read-only `animations.json`. It records the ordered SRT-set SHA-256, optional narration start floor, narration padding, ordered SVG group IDs, and optional 1-based cue numbers. `narration_sync.py animations` rejects a stale fingerprint, validates the group IDs against the current SVGs, and writes the derived `narration_animations.json` with only supported PowerPoint fields. Cue-bound animation starts use the same page-start floor as the embedded audio; uncued title or decorative animation keeps its canonical relative timing. A group with `effects[]` still maps to one cue: its first active row is anchored to that cue, while later rows retain their relative delay. Narration-independent custom motion passes canonical `animations.json` directly; with no sidecar, inherit the base report's resolved motion. `narration_sync.py subtitles` reads the final PPTX's actual presentation order plus millisecond transition, narration-delay, and slide-advance values, so `total.srt` follows the native PPTX timeline. A relative `--pptx` path is resolved under `<project_path>`.

PowerPoint's video encoder can quantize each slide/media segment to its output frame clock. Those small per-page differences may accumulate even when the PPTX timing values are correct. `video_sound_mix.py` reuses page-level narration correlation to move every transition/object cue from the theoretical PPTX clock to the raw MP4 clock; it does not directly add two independent timelines. `video_subtitles.py` then uses `stable-ts` to force-align the exact frozen narration text against the finished `.mp4` / `.wmv` / `.mov` audio track. It may split long delivery cues for display, writes a same-stem SRT, and does not rewrite the video, notes, or page-local subtitles.

Use the default text-flow mode for the final narrated SVG export. It keeps authored line breaks in one editable, no-wrap text frame; narration does not require per-line text frames.

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

For ElevenLabs, `--voice-id` is required. List voices from your ElevenLabs account with:

```bash
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py --provider elevenlabs --list-voices
```

For MiniMax, Qwen, and CosyVoice, pass the provider-specific system voice or cloned voice ID/name with `--voice-id`. Voice cloning itself is performed in the provider's console/API first; `notes_to_audio.py` uses the resulting voice ID to generate per-slide narration.

Audio embedded into PPTX must use a PowerPoint-reliable format: `m4a` (AAC), `mp3`, or `wav`. Built-in generation defaults to `mp3`; transcode provider output such as `pcm`, `opus`, or `flac` before embedding.

## Use a cloned voice

Four cloud providers — **ElevenLabs**, **MiniMax**, **Qwen**, **CosyVoice** — let you clone a voice from a short sample and then synthesize new speech in that voice. PPT Master narrates the entire deck in your cloned voice as long as you can hand it a `voice_id`. (`edge` does not support cloning.)

**The split of responsibilities**: voice cloning itself happens in the provider's console or API — you upload a sample (typically 10 s – a few minutes of clean audio) and the provider returns a `voice_id`. PPT Master is on the *consumption* side: it takes that `voice_id` and reads every slide's notes in that voice. PPT Master never uploads your sample anywhere.

| Provider | Where to clone | Sample length |
|---|---|---|
| ElevenLabs | [elevenlabs.io](https://elevenlabs.io) → Voices → Add Voice → Instant / Professional Voice Cloning | 1 min (Instant) / 30 min+ (Professional) |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → Voice Clone | ~10 s – 5 min |
| Qwen TTS | [DashScope console](https://dashscope.console.aliyun.com) → Speech Synthesis → Voice Replica | ~10 s – 5 min |
| CosyVoice | [DashScope console](https://dashscope.console.aliyun.com) → Speech Synthesis → Voice Replica | ~10 s – 5 min |

**How to use it after cloning** — in chat, just say so. The AI will skip the voice-recommendation step and use your `voice_id` directly:

```
You: Generate narration with my cloned MiniMax voice; voice_id is xxxxxxx
You: Generate the narration with my cloned ElevenLabs voice id abc123
```

Or call the script directly:

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax --voice-id <your-cloned-voice-id> \
  --minimax-model speech-2.8-hd
```

Replace `--provider minimax` with `elevenlabs` / `qwen` / `cosyvoice` as needed; `--voice-id` accepts the cloned voice the same way it accepts a system voice.

**Notes**:

- **Authorization** — only clone voices you own or have explicit permission to use. Each provider's terms forbid impersonation.
- **Language coverage** — the cloned voice inherits the speaker's accent. For multilingual decks (e.g. Chinese with English terms), pick a provider whose model handles your sample's language mix; ElevenLabs `eleven_multilingual_v2` and CosyVoice tend to be the most forgiving.
- **Subtitle capability** — cloned ElevenLabs and supported CosyVoice voices can produce provider-timed SRT; cloned Qwen voices remain audio-only under the current API.
- **Provider retention** — reuse the `voice_id` while that voice remains available in your provider account. Retention, deletion, and expiration policies are provider-specific.

## Dependency

```bash
python3 -m pip install edge-tts
```

Already listed in `skills/ppt-master/requirements.txt`. `edge-tts` calls Microsoft's online TTS service — an internet connection is required at generation time. The MP3s themselves are local files; nothing about playback or PowerPoint export depends on the network afterwards.

Cloud TTS providers do not require extra Python packages; they use HTTPS directly. Configure the relevant API key in the current shell or in `.env` based on `.env.example`.

Automatic MP4 export adds no Python package. It requires Windows PowerPoint 2016+ and Windows PowerShell; macOS and systems without compatible PowerPoint keep the narrated PPTX and use manual export.

Real-time slideshow capture adds no PPT Master package. It requires desktop
Windows PowerPoint plus a recorder that can capture the presentation picture
and application/system audio. [OBS Studio](https://obsproject.com/kb/quick-start-guide)
and [Windows Game Bar](https://support.microsoft.com/en-us/accessibility/windows/use-a-screen-reader-to-record-your-screen-with-xbox-game-bar)
are examples, not project dependencies.

Post-export animation-sound mixing requires `ffmpeg` / `ffprobe` on `PATH` and
`numpy`. Final-video subtitle alignment separately requires `stable-ts`:

```bash
python3 -m pip install numpy stable-ts
```

## Tips

- **Pacing**: On the Generate PPTX route, speaker notes scale with the independent information groups in the final SVG; 2–5 sentences is a typical rhythm, not a cap. Start with `+0%`; for a dense, deliberately detailed script, try `-5%`.
- **Mid-deck regeneration**: change a single slide's `notes/<page>.md`, re-run `notes_to_audio.py` (it overwrites all MP3s, so re-run for the whole deck — the cost is small).
- **Mixed-language decks** (Chinese with English technical terms etc.): `edge-tts` neural voices handle the embedded foreign words reasonably well in most locales — pick the dominant language voice and try one slide first.

## Export as video

Choose one delivery path:

| Path | Use it when | Sound result |
|---|---|---|
| Native `CreateVideo` | You want the automated, reproducible path | Narration is native; resolved transition/object cues require `video_sound_mix.py`. |
| Real-time PowerPoint slideshow capture | You explicitly want the video to contain exactly what PowerPoint plays | The capture already contains narration and native cues; never run `video_sound_mix.py` on it. |
| Manual **Create a Video** UI | Automation is unavailable but PowerPoint's encoder is acceptable | Same sound boundary as native `CreateVideo`; this is not screen recording. |

Once the narrated PPTX is in `exports/`, Windows PowerPoint 2016+ can export it automatically through:

```bash
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o <raw_powerpoint_video.mp4>
```

The command uses recorded timings and narrations, defaults to 1080p/30 fps, and returns only after PowerPoint reports success or failure. The embedded audio plays as each slide's narration, while the per-slide auto-advance timings drive the video's pacing. `--recorded-narration` rejects `on-click` object animation because it does not generate object-level click timings.

PowerPoint's raw MP4 does not reliably contain sounds attached to transitions
or Animation Pane rows, even when `animations.json` and the PPTX package are
valid. For Generate projects whose final narrated trace contains those cues,
run `video_sound_mix.py` as shown above. It keeps the native sounds in the
editable PPTX, copies the visual video stream unchanged, mixes narration at
unity with reduced cue levels, applies a peak limiter, and publishes an
independent SFX stem plus a machine-readable verification receipt. Align
subtitles against the mixed MP4, not the raw intermediate.

### Record the live PowerPoint slideshow

This is an explicit real-time capture path. PowerPoint remains the renderer and
audio player; the recorder only captures its output.

1. Open the final narrated PPTX in desktop Windows PowerPoint and start Slide Show from the beginning. Use the deck's automatic slide and click-free object timings; do not capture edit or Presenter View.
2. Capture only the full-screen presentation at the deck aspect ratio. Hide notifications and keep the pointer out of frame. The normal target is 1920x1080 at a stable 30 fps.
3. Enable exactly one application/system-audio capture source and disable the microphone unless live speech was explicitly requested. Do not capture both desktop and application audio, which creates echo; 48 kHz is a preferred recorder setting, not a requirement.
4. Start before the first slide and stop after the final sound tail. Preserve that raw capture, then trim only the leading and trailing handles.
5. Confirm that the final file has video and audio streams, narration is intelligible, every configured cue is audible exactly once, animations/transitions completed, and no dropped frames or desktop UI are visible.
6. When page-local SRT exists, run `video_subtitles.py` against the final trimmed capture. It aligns the frozen narration text to the actual recorded audio.

The current capture acceptance is human-audited; PPT Master does not claim a
machine cue receipt for it. If cue levels mask narration or clip, repair the
PPTX/cue assets and record again, or use native export plus the deterministic
gain/limiter mix. A Linux host can prepare the complete narrated PPTX, audio,
timings, and subtitles, but this capture step still needs a real desktop
Windows PowerPoint playback endpoint.

### Manual Create a Video fallback (Windows / Mac, Office 2016+)

1. Open the narrated `.pptx` from `exports/`.
2. **File → Export → Create a Video**.
3. Pick a quality and "Use Recorded Timings and Narrations".
4. Save as `.mp4` (`.wmv` is also available on Windows).
5. If native transition/object sounds are configured, run the sound-mix command above; otherwise the PowerPoint export is the final video.
6. Run the optional `video_subtitles.py` alignment command against the final video; it writes the same-stem SRT beside it.

PowerPoint for Mac can export MP4/MOV manually, but Microsoft documents that
animation effects do not play in its movie export. Use the Windows automation
path when animation fidelity matters.

**Keynote (Mac)**: open the deck → **File → Export To → Movie…** — Keynote can honor embedded narration and per-slide timings, output `.m4v` / `.mov`; this is not a guarantee that PowerPoint animation sounds are present.

**Tips**:

- **Generated narration does not need a microphone** — native export needs no recording session. Real-time slideshow capture records application/system audio with the microphone disabled. Re-runs reuse the same notes and settings, but cloud models may still produce small nondeterministic differences.
- **Animation fidelity on Windows** — PowerPoint's Windows video export preserves PPT Master's native visual page transitions and click-free object animation. Animation sound uses either the verified post-export mix or the mutually exclusive real-time slideshow capture above. Mac movie export has the limitation noted above. See [Animations & Transitions](./animations.md).
- **Want to tweak just one slide's audio?** Edit `notes/<page>.md`, re-run `notes_to_audio.py` and the embedding step, then re-export the video — total turnaround is usually under a minute per slide.
- **File size**: a 20-page deck at Full HD typically lands at 30–80 MB depending on imagery. Drop to HD if you need a smaller file for sharing.
