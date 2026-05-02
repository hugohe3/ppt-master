# 音频旁白与视频导出

PPT Master 可以把演讲者备注转成逐页音频旁白（默认基于 [`edge-tts`](https://github.com/rany2/edge-tts) —— 微软 Edge 的在线神经网络语音；也可配置 ElevenLabs、MiniMax、Qwen TTS、CosyVoice 使用高质量或复刻音色），再把音频嵌入回 PPTX，由 PowerPoint 自带的"导出视频"一键产出带旁白和转场的 MP4，全程无需第三方工具。

## 你会得到什么

- 每页一个音频文件，存放于 `<project_path>/audio/`，文件名与 SVG 对齐（`01_cover.mp3`、`02_market_landscape.mp3` …）。
- 可选重新导出：在 `exports/` 生成新版 PPTX，每页对应的音频已嵌入到该页，且页面切换时间按音频长度自动设置——无人值守自动播放和视频导出都不用再手动调时间。
- 演讲者备注原样保留。

## 它是怎么做到的

1. **备注本身就是为 TTS 写的口播稿**。PPT Master 的 notes 规范刻意产出适合朗读的散文——没有 `[过渡]` / `[停顿]` 这种舞台标记，也没有 `要点：` / `时长：` 这种 meta 行——念出来的内容就是页面上的内容。
2. **AI 替你选音色**。当你提出生成旁白时，AI 根据 deck 的主语言（`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …）和所选 provider 拉取或解释可用音色，挑出候选并给每个写一句中文调性说明（如"稳重男声·适合财报"）。语速/风格也会基于 notes 信息密度给出推荐值。
3. **一次问完，一次回答**。AI 在一条消息里同时问三件事——生成模式、音色、是否把音频嵌入回 PPTX——每项都标了推荐值。回"好"接受全部默认，或者只说要改的部分（如"音色 2，语速 -5%"）。
4. **执行**。脚本写出音频到 `audio/`，再（如果你保留嵌入）重新导出带音频的 PPTX。

完整流程见 [`workflows/generate-audio.md`](../../skills/ppt-master/workflows/generate-audio.md)。

## 怎么触发

deck 导出后，在聊天里直接说就行：

```
你: 给这个 PPT 生成音频
你: 帮我用日语给这个 deck 配一个温柔女声的旁白
你: Generate narration for this deck and re-export with audio embedded.
```

剩下的 AI 全包。

## 支持的语言

凡是 `edge-tts` 支持的 locale 都行——大约 90 个，覆盖中文全部主要变体（`zh-CN` 普通话 / `zh-TW` 台湾普通话 / `zh-HK` 粤语）、英文（美/英/澳/印）、日语、韩语、法语、德语、西班牙语、葡萄牙语、俄语、阿拉伯语等。任何 locale 的全量音色清单都可以这样查：

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale ja-JP
```

## 进阶：手动调用脚本

如果你想跳过 AI 流程直接跑命令：

```bash
# 1. 确保备注已切分（后处理 Step 7.1）
python3 skills/ppt-master/scripts/total_md_split.py <project_path>

# 2A. 用 edge-tts 生成 MP3（默认，无需 API Key）
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice zh-CN-YunjianNeural --rate +0%

# 2B. 用 MiniMax 生成 MP3（支持系统音色或复刻 voice_id）
export MINIMAX_API_KEY="your-minimax-api-key"
# 默认使用国内地址；海外访问可设置 MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax \
  --voice-id <minimax-voice-id> \
  --minimax-model speech-2.8-hd

# 2C. 用 Qwen TTS 生成音频（系统音色或复刻音色）
export DASHSCOPE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen \
  --voice-id <qwen-voice> \
  --qwen-model qwen3-tts-flash \
  --qwen-language-type Chinese

# 2D. 用 CosyVoice 生成 MP3（系统音色或复刻/设计音色）
export COSYVOICE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice \
  --voice-id <cosyvoice-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 3.（可选）重新导出 PPTX 嵌入音频
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final \
  --recorded-narration audio
```

edge 模式下 `--voice` 是必填项。云端 provider 使用 `--voice-id` 传入对应平台的系统音色或复刻音色 ID。声音复刻本身先在对应平台控制台/API 中完成，`notes_to_audio.py` 使用得到的 voice ID 生成逐页旁白。

## 使用复刻音色

四个云端 provider —— **ElevenLabs**、**MiniMax**、**Qwen**、**CosyVoice** —— 都支持用一段较短的音频样本复刻一个新音色，再用这个音色合成新语音。只要你能拿到 `voice_id`，PPT Master 就能用这个音色把整份 deck 念出来。（`edge` 不支持复刻。）

**职责切分**：声音复刻本身在 provider 的控制台或 API 完成——你上传一段样本（一般 10 秒到几分钟的干净录音），平台给你返回一个 `voice_id`。PPT Master 在*消费*侧：拿到 `voice_id` 后用这个音色逐页朗读备注。PPT Master 不会把你的样本上传到任何地方。

| Provider | 复刻入口 | 样本时长 |
|---|---|---|
| ElevenLabs | [elevenlabs.io](https://elevenlabs.io) → Voices → Add Voice → Instant / Professional Voice Cloning | 1 分钟（Instant）/ 30 分钟以上（Professional） |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → 语音克隆 | 10 秒 – 5 分钟 |
| Qwen TTS | [DashScope 控制台](https://dashscope.console.aliyun.com) → 语音合成 → 声音复刻 | 10 秒 – 5 分钟 |
| CosyVoice | [DashScope 控制台](https://dashscope.console.aliyun.com) → 语音合成 → 音色复刻 | 10 秒 – 5 分钟 |

**复刻完之后怎么用** —— 在聊天里告诉 AI 即可，AI 会跳过音色推荐环节直接用你的 `voice_id`：

```
你: 用 MiniMax 我克隆的音色生成旁白，voice_id 是 xxxxxxx
你: 用我在 ElevenLabs 复刻的 voice id abc123 生成
```

也可以直接跑脚本：

```bash
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax --voice-id <你的复刻 voice id> \
  --minimax-model speech-2.8-hd
```

把 `--provider minimax` 换成 `elevenlabs` / `qwen` / `cosyvoice` 就能切到对应平台；`--voice-id` 接收复刻音色和接收系统音色的方式完全一样。

**注意**：

- **授权** —— 只复刻你自己拥有的、或拿到了明确授权的声音。每个 provider 的服务条款都禁止冒用他人声音。
- **语言覆盖** —— 复刻出来的音色会继承说话人的口音。对中英混合等多语 deck，建议挑一个对你样本语言组合处理较好的 provider；ElevenLabs `eleven_multilingual_v2` 和 CosyVoice 通常最宽容。
- **一次复刻、长期复用** —— `voice_id` 不过期。复刻一次，可以给任意多份 deck 配旁白。

## 依赖

```bash
python3 -m pip install edge-tts
```

已写入 `skills/ppt-master/requirements.txt`。`edge-tts` 调用微软的在线 TTS 服务，**生成时**需要联网；生成后的音频是本地文件，PowerPoint 播放和视频导出都不依赖网络。云端 TTS provider 不需要额外 Python 包，直接通过 HTTPS 调用；按 `.env.example` 配置对应 API Key 即可。

## 经验值

- **语速**：PPT Master 默认每页 2–5 句备注，`+0%` 听感最自然。如果某页特别密集（长技术段落），可以试 `-5%`。
- **改某一页**：改对应的 `notes/<page>.md`，再跑一次 `notes_to_audio.py`（脚本会重新生成全量 MP3，整套 deck 跑一遍成本很低）。
- **混合语言 deck**（中文里夹英文术语等）：主流 locale 的神经语音对嵌入的外语词处理得不错——按主语言挑音色，先用一页试听再批量。

---

## 导出为视频

带旁白的 PPTX 在 `exports/` 里就绪后，PowerPoint 自带"创建视频"功能可以直接把它导出成 MP4——不需要任何第三方工具。嵌入的音频会作为每页旁白播放；页间切换时间已经由 PPT Master 在嵌入时按音频长度自动设好（用 `--recorded-narration audio` 重新导出时），所以视频节奏和旁白完全同步。

**PowerPoint（Windows / Mac，Office 2016+）**：

1. 打开 `exports/` 里那份带旁白的 `.pptx`。
2. **文件 → 导出 → 创建视频**。
3. 选清晰度（4K / 全高清 / 高清 / 标准）以及"使用录制的计时和旁白"——PPT Master 已经替你录好了。
4. **创建视频** → 保存为 `.mp4`（Windows 也支持 `.wmv`）。

**Keynote（Mac）**：打开 deck → **文件 → 导出到 → 影片…** ——Keynote 同样会读取嵌入的音频和分页计时，输出 `.m4v` / `.mov`。

**经验值**：

- **不需要麦克风、不需要录制环节**——音频是合成的，重跑可重现。
- **动画保留**：PPT Master 的页间转场和页内元素入场动画是真正的 OOXML 动画，导出视频后正常播放。详见 [转场与动画](./animations.md)。
- **单页改音频**：改对应 `notes/<page>.md`，再跑一遍 `notes_to_audio.py` + 嵌入步骤，再重新导出视频——单页迭代通常不到一分钟。
- **文件大小**：20 页全高清 deck 通常是 30–80 MB，取决于图片量。需要小文件分享时降到高清就行。
