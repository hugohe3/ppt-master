# Audio Narration & Video Export

[English](./audio-narration.md) | [Chinese](./zh/audio-narration.md)

---

PPT Master can turn the speaker notes into per-slide narration via [`edge-tts`](https://github.com/rany2/edge-tts) (Microsoft Edge's online neural voices) by default, or via ElevenLabs, MiniMax, Qwen TTS, and CosyVoice when you need higher-quality cloud narration or a cloned voice. The edge path also writes a page-local SRT from the same TTS stream. It can then embed the audio back into the PPTX for PowerPoint's native video export.

## What you get

- One audio file per slide under `<project_path>/audio/`, named to match the SVG (`01_cover.mp3`, `02_market_landscape.mp3`, …).
- With edge, one matching subtitle file per slide under `<project_path>/notes/subtitles/` (`01_cover.srt`, `02_market_landscape.srt`, …). Each file uses a page-local timeline with a `00:00:00,000` origin and edge's word-boundary timing.
- With an SVG-to-SRT timing plan, a rebuilt `animations.json` whose click-free entrance animations wait for the relevant subtitle cue, plus a deck-wide `<project_path>/notes/subtitles/total.srt` aligned to the final PPTX timeline. After PowerPoint exports a video, the same command can calibrate the page starts against its audio track for frame-accurate sidecar subtitles.
- Optional re-export: a new PPTX in `exports/` with each `m4a` / `mp3` / `wav` file embedded into the matching slide and slide auto-advance timings set to the audio length, so kiosk/auto-play and video export work without manual timing.
- Optional native video export on Windows: `powerpoint_video.py` delegates the final narrated PPTX to PowerPoint 2016+ and waits until its native MP4 encoder succeeds or fails.
- The original speaker notes are preserved.

## How it works

1. **Speaker notes are written as pure spoken narration.** PPT Master's notes spec deliberately produces TTS-friendly prose — no bracketed stage markers, no `Key points:` / `Duration:` meta-lines — so what is read aloud is exactly what's on the page.
2. **AI picks the voice for you.** When you ask for narration, the AI checks the deck's primary language (`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …), pulls the selected provider's voice catalog, and recommends 3–6 candidates with a one-line tone description for each (e.g. "steady male voice for financial reporting"). It also recommends a speaking rate or provider defaults based on notes density.
3. **One question, one answer.** You are asked once — provider, voice, rate, "embed audio back into PPTX", and "continue to video" — all with a recommended default. Reply "ok" to accept everything, or just call out the part you want to change.
4. **Generation runs.** With edge, the script writes each page's MP3 and SRT from the same stream to `audio/` and `notes/subtitles/`; cloud providers currently write audio only. For Generate PPTX, the AI maps current SVG content groups to numbered SRT cues, rebuilds click-free animations, and re-exports the deck with audio attached. It then merges the local SRT files using timing values read from that final PPTX. When automatic video export was selected and compatible Windows PowerPoint is available, it continues through PowerPoint's native encoder and waits for the MP4 before aligning the delivery SRT. Long-audio import and automatic long-audio splitting are not supported.

Subtitles remain external artifacts: PPT Master does not embed them into the PPTX or burn them into the MP4. Automatic video export delegates to installed Windows PowerPoint; it is not a separate renderer.

The shared stage is documented in [`workflows/stages/generate-audio.md`](../skills/ppt-master/workflows/stages/generate-audio.md).

## Two embedding paths

| Command | Purpose |
|---|---|
| `--recorded-narration audio` | Prepare PowerPoint's recorded timings and narrations. Requires complete per-slide audio and writes page auto-advance timings. Use this for narrated/video export. The re-export is saved as `exports/<name>_<timestamp>_narrated.pptx`. |
| `--narration-audio-dir audio` | Lower-level audio embedding. Embeds matched files and allows partial coverage. Use this for testing or manual PowerPoint finishing. Exports get the same `_narrated` name suffix. |

## Triggering it

Just say so in chat after the deck has been exported:

```
You: Generate narration audio for this deck
You: Generate narration for this deck and re-export with audio embedded.
You: Add Japanese voice narration; pick a calm female voice.
```

The AI handles the rest.

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

# 2B. Or generate MP3s with ElevenLabs (requires ELEVENLABS_API_KEY)
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs \
  --voice-id <elevenlabs-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 2C. Or generate MP3s with MiniMax (supports system and cloned voice_id)
export MINIMAX_API_KEY="your-minimax-api-key"
# Defaults to the China endpoint. For overseas access, set MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2.
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax \
  --voice-id <minimax-voice-id> \
  --minimax-model speech-2.8-hd

# 2D. Or generate audio with Qwen TTS (system voice or cloned voice)
export DASHSCOPE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen \
  --voice-id <qwen-voice> \
  --qwen-model qwen3-tts-flash \
  --qwen-language-type Chinese

# 2E. Or generate MP3s with CosyVoice (system voice or cloned/designed voice_id)
export COSYVOICE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice \
  --voice-id <cosyvoice-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 3. Print the SRT-set fingerprint, then author
#    <project_path>/narration_timing.json by comparing each current
#    SVG content group with the numbered cues in that page's SRT. A missing
#    cue means the group has no spoken counterpart and uses normal sequencing.
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>

# 4. Rebuild click-free object animation timing from the formal SRT
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-padding 0.5 --force

# 5. Re-export PPTX with audio embedded
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --no-merge --recorded-narration audio \
  --narration-padding 0.5

# 6. Merge page-local SRT using the final PowerPoint timings
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 7. Optional on Windows: export through PowerPoint and wait for completion
python3 skills/ppt-master/scripts/powerpoint_video.py --check
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o exports/<final_video>.mp4

# 8. Calibrate page starts against the exported audio track and write a
#    same-stem sidecar SRT
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --video <powerpoint_exported_video> \
  -o exports/<powerpoint_exported_video_stem>.srt --force
```

For edge, `--voice` is required. Use `--list-voices --locale <locale>` to see what's available.
Edge generates up to three slide-level audio/SRT pairs concurrently by default.
Use `--concurrency <N>` to tune it or `--concurrency 1` for serial
troubleshooting. Cloud providers remain serial.

The edge command creates `audio/<stem>.mp3` and `notes/subtitles/<stem>.srt` from the same streaming request. Sentence-ending punctuation closes a cue. A cue over 20 visible characters first splits at commas, semicolons, or colons, then at the nearest word boundary only if it is still too long. Use `--subtitle-max-chars` to change the limit. Adjacent timing overlap up to 100 ms is tolerated by moving the later cue start to the previous cue end; larger overlap fails. Each SRT uses a page-local timebase with a zero origin and preserves edge's `WordBoundary` timing, including any leading silence before the first cue. The cloud-provider commands currently create audio only.

`narration_timing.json` is deliberately separate from `animations.json`. It records the ordered SRT-set SHA-256, narration padding, ordered SVG group IDs, and optional 1-based cue numbers. `narration_sync.py animations` rejects a stale fingerprint, validates the group IDs against the current SVGs, and replaces the animation sidecar with only supported PowerPoint fields. `narration_sync.py subtitles` reads the final PPTX's actual presentation order plus millisecond slide-advance and transition values, so `total.srt` follows the native PPTX timeline. A relative `--pptx` path is resolved under `<project_path>`.

PowerPoint's video encoder can quantize each slide/media segment to its output frame clock. Those small per-page differences may accumulate even when the PPTX timing values are correct. Passing the finished `.mp4` / `.wmv` / `.mov` with `--video` uses normalized audio correlation to locate each original page narration in the exported audio track. It changes only the page-level offsets: edge's cue text and page-local `WordBoundary` timing remain untouched. This is a post-export subtitle calibration step and does not rewrite the video.

Use `--no-merge` for the final narrated SVG export. Keeping each SVG line in its own text frame preserves the authored coordinates; paragraph merging lets PowerPoint recalculate multiline text geometry and can introduce visible offsets.

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
- **Provider retention** — reuse the `voice_id` while that voice remains available in your provider account. Retention, deletion, and expiration policies are provider-specific.

## Dependency

```bash
python3 -m pip install edge-tts
```

Already listed in `skills/ppt-master/requirements.txt`. `edge-tts` calls Microsoft's online TTS service — an internet connection is required at generation time. The MP3s themselves are local files; nothing about playback or PowerPoint export depends on the network afterwards.

Cloud TTS providers do not require extra Python packages; they use HTTPS directly. Configure the relevant API key in the current shell or in `.env` based on `.env.example`.

Automatic MP4 export adds no Python package. It requires Windows PowerPoint 2016+ and Windows PowerShell; macOS and systems without compatible PowerPoint keep the narrated PPTX and use manual export.

## Tips

- **Pacing**: On the Generate PPTX route, speaker notes scale with the independent information groups in the final SVG; 2–5 sentences is a typical rhythm, not a cap. Start with `+0%`; for a dense, deliberately detailed script, try `-5%`.
- **Mid-deck regeneration**: change a single slide's `notes/<page>.md`, re-run `notes_to_audio.py` (it overwrites all MP3s, so re-run for the whole deck — the cost is small).
- **Mixed-language decks** (Chinese with English technical terms etc.): `edge-tts` neural voices handle the embedded foreign words reasonably well in most locales — pick the dominant language voice and try one slide first.

## Export as video

Once the narrated PPTX is in `exports/`, Windows PowerPoint 2016+ can export it automatically through:

```bash
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o <final_video.mp4>
```

The command uses recorded timings and narrations, defaults to 1080p/30 fps, and returns only after PowerPoint reports success or failure. The embedded audio plays as each slide's narration, while the per-slide auto-advance timings drive the video's pacing. `--recorded-narration` rejects `on-click` object animation because it does not generate object-level click timings.

**Manual PowerPoint fallback (Windows / Mac, Office 2016+)**:

1. Open the narrated `.pptx` from `exports/`.
2. **File → Export → Create a Video**.
3. Pick a quality and "Use Recorded Timings and Narrations".
4. Save as `.mp4` (`.wmv` is also available on Windows).
5. Run the optional subtitle calibration command above and place its same-stem SRT beside the video.

PowerPoint for Mac can export MP4/MOV manually, but Microsoft documents that
animation effects do not play in its movie export. Use the Windows automation
path when animation fidelity matters.

**Keynote (Mac)**: open the deck → **File → Export To → Movie…** — Keynote also honors embedded audio and per-slide timings, output `.m4v` / `.mov`.

**Tips**:

- **No mic, no recording session needed** — the audio is generated, not recorded, so re-runs are deterministic.
- **Animation fidelity on Windows** — PowerPoint's Windows video export preserves PPT Master's native page transitions and click-free object animation. Mac movie export has the limitation noted above. See [Animations & Transitions](./animations.md).
- **Want to tweak just one slide's audio?** Edit `notes/<page>.md`, re-run `notes_to_audio.py` and the embedding step, then re-export the video — total turnaround is usually under a minute per slide.
- **File size**: a 20-page deck at Full HD typically lands at 30–80 MB depending on imagery. Drop to HD if you need a smaller file for sharing.
