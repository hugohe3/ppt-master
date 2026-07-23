# 音频旁白与视频导出

[English](../audio-narration.md) | [Chinese](./audio-narration.md)

---

PPT Master 可以把演讲者备注转成逐页音频旁白（默认基于 [`edge-tts`](https://github.com/rany2/edge-tts) —— 微软 Edge 的在线神经网络语音；也可配置 ElevenLabs、MiniMax、Qwen TTS、CosyVoice 使用高质量或复刻音色）。Edge 路径还会从同一次 TTS 流中写出该页的 SRT；音频可继续嵌入 PPTX，供 PowerPoint 使用原生视频导出。

## 你会得到什么

- 每页一个音频文件，存放于 `<project_path>/audio/`，文件名与 SVG 对齐（`01_cover.mp3`、`02_market_landscape.mp3` …）。
- 使用 Edge 时，每页还有一个同名字幕文件，存放于 `<project_path>/notes/subtitles/`（`01_cover.srt`、`02_market_landscape.srt` …）。每个文件使用以 `00:00:00,000` 为原点的页内时间轴，时间来自 Edge 的词边界。
- 提供 SVG 到 SRT 的计时计划后，还会重建 `animations.json`：无点击入场动画会等待相关字幕 cue；同时生成与最终 PPTX 时间轴一致的 `<project_path>/notes/subtitles/total.srt`。PowerPoint 导出视频后，还可用同一命令根据视频音轨校准每页起点，得到帧级对齐的外挂字幕。
- 可选重新导出：在 `exports/` 生成新版 PPTX，每页对应的 `m4a` / `mp3` / `wav` 音频已嵌入到该页，且页面切换时间按音频长度自动设置——无人值守自动播放和视频导出都不用再手动调时间。
- 演讲者备注原样保留。

## 它是怎么做到的

1. **备注本身就是为 TTS 写的口播稿**。PPT Master 的 notes 规范刻意产出适合朗读的散文——没有 `[过渡]` / `[停顿]` 这种舞台标记，也没有 `要点：` / `时长：` 这种 meta 行——念出来的内容就是页面上的内容。
2. **AI 替你选音色**。当你提出生成旁白时，AI 根据 deck 的主语言（`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …）和所选 provider 拉取或解释可用音色，挑出候选并给每个写一句中文调性说明（如"稳重男声·适合财报"）。语速/风格也会基于 notes 信息密度给出推荐值。
3. **一次问完，一次回答**。AI 在一条消息里同时问三件事——生成模式、音色、是否把音频嵌入回 PPTX——每项都标了推荐值。回"好"接受全部默认，或者只说要改的部分（如"音色 2，语速 -5%"）。
4. **执行**。使用 Edge 时，脚本从同一次流中把每页 MP3 和 SRT 分别写到 `audio/` 与 `notes/subtitles/`；云端 provider 目前仍只写音频。对于 Generate PPTX，AI 将当前 SVG 内容组映射到编号后的 SRT cue，重建无点击动画，再导出带音频的 PPTX；最后从该 PPTX 读回实际计时并合并逐页 SRT。如果已有 PowerPoint 导出的视频，可再根据视频音轨测出每页旁白的真实起点，只修正分页偏移。不支持长音频导入或自动拆分。

字幕保持为外部 SRT 文件：PPT Master 不把字幕嵌入 PPTX，也不直接导出 MP4。请使用 PowerPoint 原生视频导出，并配套使用生成的 `total.srt`。

共享阶段见 [`workflows/stages/generate-audio.md`](../../skills/ppt-master/workflows/stages/generate-audio.md)。

## 两条嵌入路径

| 命令 | 用途 |
|---|---|
| `--recorded-narration audio` | 准备 PowerPoint 的"录制的计时和旁白"。要求每页都有音频，并写入页面自动推进时间。用于旁白视频导出。重导出文件保存为 `exports/<name>_<timestamp>_narrated.pptx`。 |
| `--narration-audio-dir audio` | 底层音频嵌入能力。只嵌入匹配到的文件，允许部分页面有音频。用于测试或后续手工整理。导出文件同样带 `_narrated` 后缀。 |

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

# 2A. 用 edge-tts 生成 MP3/SRT 对（默认，无需 API Key）
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice zh-CN-YunjianNeural --rate +0%

# 2B. 用 ElevenLabs 生成 MP3（需要 ELEVENLABS_API_KEY）
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs \
  --voice-id <elevenlabs-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 2C. 用 MiniMax 生成 MP3（支持系统音色或复刻 voice_id）
export MINIMAX_API_KEY="your-minimax-api-key"
# 默认使用国内地址；海外访问可设置 MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax \
  --voice-id <minimax-voice-id> \
  --minimax-model speech-2.8-hd

# 2D. 用 Qwen TTS 生成音频（系统音色或复刻音色）
export DASHSCOPE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen \
  --voice-id <qwen-voice> \
  --qwen-model qwen3-tts-flash \
  --qwen-language-type Chinese

# 2E. 用 CosyVoice 生成 MP3（系统音色或复刻/设计音色）
export COSYVOICE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice \
  --voice-id <cosyvoice-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 3. 输出整套 SRT 的指纹，再对照每页当前 SVG 内容组与 SRT cue，编写
#    <project_path>/narration_timing.json；没有对应口播的组不写 cue，
#    后续按正常动画顺序出现。
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>

# 4. 根据正式 SRT 重建无点击对象动画计时
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-padding 0.5 --force

# 5. 重新导出 PPTX 嵌入音频
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --no-merge --recorded-narration audio \
  --narration-padding 0.5

# 6. 按最终 PowerPoint 计时合并逐页 SRT
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 7. 可选：PowerPoint 创建视频后，根据导出音轨校准每页起点，
#    生成与视频同名的外挂 SRT
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --video <powerpoint_exported_video> \
  -o exports/<powerpoint_exported_video_stem>.srt --force
```

edge 模式下 `--voice` 是必填项，可用 `--list-voices --locale <locale>` 查看音色。

Edge 命令会从同一次流式请求中生成 `audio/<stem>.mp3` 与 `notes/subtitles/<stem>.srt`。句末标点必定结束一条字幕；单条超过默认 20 个可见字符时，优先在逗号、分号或冒号处拆分，仍然过长才在最近的词边界拆分。可用 `--subtitle-max-chars` 调整上限。每页 SRT 使用从零计时的页内时间基准，并保留 Edge `WordBoundary` 的实际时间（包括首条字幕前的静音）；云端 provider 命令目前只生成音频。

`narration_timing.json` 与 `animations.json` 刻意分离：前者记录整套有序 SRT 的 SHA-256、旁白 padding、有序 SVG 组 ID 和可选的 1-based cue 编号。`narration_sync.py animations` 会拒绝过期的 SRT 指纹，用当前 SVG 校验组 ID，并用 PowerPoint 支持的字段完整替换动画 sidecar。`narration_sync.py subtitles` 从最终 PPTX 读取真实页面关系顺序、毫秒级页面推进与转场时间，因此 `total.srt` 使用原生 PPTX 时间轴。相对 `--pptx` 路径按 `<project_path>` 解析。

PowerPoint 的视频编码器可能把每个页面 / 媒体段落量化到输出帧时钟；即使 PPTX 计时值正确，这些很小的分页误差仍可能逐页累积。把最终 `.mp4` / `.wmv` / `.mov` 通过 `--video` 传入后，脚本会用归一化音频相关性在视频音轨中定位每页原始旁白。它只改页级偏移，Edge 的字幕文本和页内 `WordBoundary` 时间保持不变。这是视频导出后的字幕校准步骤；PPT Master 仍不创建或改写视频。

最终带旁白的 SVG 导出固定使用 `--no-merge`。让每条 SVG 文本行保持独立文本框，可以保留作者坐标；合并段落会让 PowerPoint 重新计算多行文本几何，可能造成肉眼可见的偏移。

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

ElevenLabs 模式下 `--voice-id` 是必填项，可从账户中列出音色：

```bash
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py --provider elevenlabs --list-voices
```

MiniMax、Qwen 与 CosyVoice 使用 `--voice-id` 传入对应平台的系统音色或复刻音色 ID。声音复刻本身先在对应平台控制台 / API 中完成，`notes_to_audio.py` 使用得到的 voice ID 生成逐页旁白。

进入 PPTX 的旁白音频必须是 PowerPoint 可靠格式：`m4a`（AAC）、`mp3` 或 `wav`。内置生成路径默认使用 `mp3`；如果 provider 产出 `pcm`、`opus` 或 `flac`，需要先转码再嵌入。

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
- **Provider 保留策略** —— 只要该音色仍存在于你的 provider 账户中，就可以继续复用对应 `voice_id`；保留、删除与过期规则以各平台政策为准。

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

带旁白的 PPTX 在 `exports/` 里就绪后，PowerPoint 自带"创建视频"功能可以直接把它导出成 MP4——不需要任何第三方工具。嵌入的音频会作为每页旁白播放；页间切换时间已经由 PPT Master 在嵌入时按音频长度自动设好（用 `--recorded-narration audio` 重新导出时），所以视频节奏和旁白完全同步。`--recorded-narration` 会拒绝 `on-click` 对象动画，因为 PPT Master 不生成对象级点击计时。

**PowerPoint（Windows / Mac，Office 2016+）**：

1. 打开 `exports/` 里那份带旁白的 `.pptx`。
2. **文件 → 导出 → 创建视频**。
3. 选清晰度（4K / 全高清 / 高清 / 标准）以及"使用录制的计时和旁白"——PPT Master 已经替你录好了。
4. **创建视频** → 保存为 `.mp4`（Windows 也支持 `.wmv`）。
5. 若要让外挂字幕最贴合最终视频，再执行上面的 `narration_sync.py subtitles --video ...`，把生成的同名 SRT 与视频放在一起。

**Keynote（Mac）**：打开 deck → **文件 → 导出到 → 影片…** ——Keynote 同样会读取嵌入的音频和分页计时，输出 `.m4v` / `.mov`。

**经验值**：

- **不需要麦克风、不需要录制环节**——音频是合成的，重跑可重现。
- **动画保留**：PPT Master 的页间转场和无点击页内元素入场动画是真正的 OOXML 动画，导出视频后正常播放。详见 [转场与动画](./animations.md)。
- **单页改音频**：改对应 `notes/<page>.md`，再跑一遍 `notes_to_audio.py` + 嵌入步骤，再重新导出视频——单页迭代通常不到一分钟。
- **文件大小**：20 页全高清 deck 通常是 30–80 MB，取决于图片量。需要小文件分享时降到高清就行。
