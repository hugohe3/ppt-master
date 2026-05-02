# Audio Narration & Video Export

PPT Master can turn the speaker notes into per-slide narration via [`edge-tts`](https://github.com/rany2/edge-tts) (Microsoft Edge's online neural voices) by default, or via ElevenLabs, MiniMax, Qwen TTS, and CosyVoice when you need higher-quality cloud narration or a cloned voice. It can then embed the audio back into the PPTX and let PowerPoint export the deck as an MP4 video — with synced narration and slide transitions, no extra tools.

## What you get

- One audio file per slide under `<project_path>/audio/`, named to match the SVG (`01_cover.mp3`, `02_market_landscape.mp3`, …).
- Optional re-export: a new PPTX in `exports/` with each MP3 embedded into the matching slide and slide auto-advance timings set to the audio length, so kiosk/auto-play and video export work without manual timing.
- The original speaker notes are preserved.

## How it works

1. **Speaker notes are written as pure spoken narration.** PPT Master's notes spec deliberately produces TTS-friendly prose — no bracketed stage markers, no `Key points:` / `Duration:` meta-lines — so what is read aloud is exactly what's on the page.
2. **AI picks the voice for you.** When you ask for narration, the AI checks the deck's primary language (`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …), pulls the selected provider's voice catalog, and recommends 3–6 candidates with a one-line tone description for each (e.g. "稳重男声，适合财报"). It also recommends a speaking rate or provider defaults based on notes density.
3. **One question, one answer.** You are asked once — voice, rate, and "embed audio back into PPTX (yes/no)" — all with a recommended default. Reply "ok" to accept everything, or just call out the part you want to change.
4. **Generation runs.** The script writes MP3s to `audio/`, then (if you kept embedding) re-exports the deck with audio attached.

The full step-by-step is in [`workflows/generate-audio.md`](../skills/ppt-master/workflows/generate-audio.md).

## Triggering it

Just say so in chat after the deck has been exported:

```
You: 给这个 PPT 生成音频
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

# 2A. Generate MP3s with edge-tts (default, no API key)
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

# 3. (Optional) Re-export PPTX with audio embedded
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final \
  --recorded-narration audio
```

For edge, `--voice` is required. Use `--list-voices --locale <locale>` to see what's available.

For ElevenLabs, `--voice-id` is required. List voices from your ElevenLabs account with:

```bash
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py --provider elevenlabs --list-voices
```

For MiniMax, Qwen, and CosyVoice, pass the provider-specific system voice or cloned voice ID/name with `--voice-id`. Voice cloning itself is performed in the provider's console/API first; `notes_to_audio.py` uses the resulting voice ID to generate per-slide narration.

## Use a cloned voice

Four cloud providers — **ElevenLabs**, **MiniMax**, **Qwen**, **CosyVoice** — let you clone a voice from a short sample and then synthesize new speech in that voice. PPT Master narrates the entire deck in your cloned voice as long as you can hand it a `voice_id`. (`edge` does not support cloning.)

**The split of responsibilities**: voice cloning itself happens in the provider's console or API — you upload a sample (typically 10 s – a few minutes of clean audio) and the provider returns a `voice_id`. PPT Master is on the *consumption* side: it takes that `voice_id` and reads every slide's notes in that voice. PPT Master never uploads your sample anywhere.

| Provider | Where to clone | Sample length |
|---|---|---|
| ElevenLabs | [elevenlabs.io](https://elevenlabs.io) → Voices → Add Voice → Instant / Professional Voice Cloning | 1 min (Instant) / 30 min+ (Professional) |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → 语音克隆 (Voice Clone) | ~10 s – 5 min |
| Qwen TTS | [DashScope console](https://dashscope.console.aliyun.com) → 语音合成 → 声音复刻 | ~10 s – 5 min |
| CosyVoice | [DashScope console](https://dashscope.console.aliyun.com) → 语音合成 → 音色复刻 | ~10 s – 5 min |

**How to use it after cloning** — in chat, just say so. The AI will skip the voice-recommendation step and use your `voice_id` directly:

```
You: 用 MiniMax 我克隆的音色生成旁白，voice_id 是 xxxxxxx
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
- **One-time setup, reusable forever** — the `voice_id` doesn't expire. Clone once, narrate any number of decks.

## Dependency

```bash
python3 -m pip install edge-tts
```

Already listed in `skills/ppt-master/requirements.txt`. `edge-tts` calls Microsoft's online TTS service — an internet connection is required at generation time. The MP3s themselves are local files; nothing about playback or PowerPoint export depends on the network afterwards.

Cloud TTS providers do not require extra Python packages; they use HTTPS directly. Configure the relevant API key in the current shell or in `.env` based on `.env.example`.

## Tips

- **Pacing**: PPT Master's default speaker-notes are 2–5 sentences per slide; `+0%` rate sounds natural. If a deck is very dense (long technical paragraphs), try `-5%`.
- **Mid-deck regeneration**: change a single slide's `notes/<page>.md`, re-run `notes_to_audio.py` (it overwrites all MP3s, so re-run for the whole deck — the cost is small).
- **Mixed-language decks** (Chinese with English technical terms etc.): `edge-tts` neural voices handle the embedded foreign words reasonably well in most locales — pick the dominant language voice and try one slide first.

## Export as video

Once the narrated PPTX is in `exports/`, PowerPoint exports it as a video natively — no third-party tool needed. The embedded audio plays as each slide's narration, and the per-slide auto-advance timings (set from audio length when you let the AI re-export with `--recorded-narration audio`) drive the video's pacing.

**PowerPoint (Windows / Mac, Office 2016+)**:

1. Open the narrated `.pptx` from `exports/`.
2. **File → Export → Create a Video**.
3. Pick a quality (4K / Full HD / HD / Standard) and "Use Recorded Timings and Narrations" — PPT Master has already set both for you.
4. **Create Video** → save as `.mp4` (or `.wmv` on Windows).

**Keynote (Mac)**: open the deck → **File → Export To → Movie…** — Keynote also honors embedded audio and per-slide timings, output `.m4v` / `.mov`.

**Tips**:

- **No mic, no recording session needed** — the audio is generated, not recorded, so re-runs are deterministic.
- **Animations are preserved** — page transitions and per-element entrance animations from PPT Master are real OOXML and play correctly in the exported video. See [Animations & Transitions](../skills/ppt-master/references/animations.md).
- **Want to tweak just one slide's audio?** Edit `notes/<page>.md`, re-run `notes_to_audio.py` and the embedding step, then re-export the video — total turnaround is usually under a minute per slide.
- **File size**: a 20-page deck at Full HD typically lands at 30–80 MB depending on imagery. Drop to HD if you need a smaller file for sharing.
