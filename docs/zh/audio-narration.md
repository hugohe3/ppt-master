# 音频旁白与视频导出

[English](../audio-narration.md) | [Chinese](./audio-narration.md)

---

PPT Master 可以把演讲者备注转成逐页音频旁白（默认基于 [`edge-tts`](https://github.com/rany2/edge-tts) —— 微软 Edge 的在线神经网络语音；也可配置 ElevenLabs、MiniMax、Qwen TTS、CosyVoice 使用高质量或复刻音色）。Edge、ElevenLabs、MiniMax，以及支持时间戳的 CosyVoice 音色，都会从同一次合成返回的 provider 计时生成逐页 SRT。Qwen 当前 TTS API 不返回时间戳，因此仍只生成音频。音频可继续嵌入 PPTX，供 PowerPoint 使用原生视频导出。

## 你会得到什么

- 每页一个音频文件，存放于 `<project_path>/audio/`，文件名与 SVG 对齐（`01_cover.mp3`、`02_market_landscape.mp3` …）。
- 使用 provider 原生计时字幕时，每页还有一个同名字幕文件，与音频一起存放于 `<project_path>/audio/`（`01_cover.srt`、`02_market_landscape.srt` …）。每个文件使用以 `00:00:00,000` 为原点的页内时间轴；provider 的词级或字符级时间戳都会重组为同一套紧凑 cue。
- 完整生成成功后写出精简的 `<project_path>/audio/manifest.json`，只记录 provider、模型、音频/字幕格式、相关音色参数，以及代替云端 voice ID 原文的 SHA-256 指纹；不包含逐页清单、产物哈希或 API Key，正常生成过程也不会读取它。
- 选择旁白 cue 同步时，规范的 `animations.json` 与逐页 SRT 会派生 `narration_animations.json`，让无点击对象动画等待相关字幕 cue；与旁白无关的自定义动画则保留规范配置中的原始计时。两个动画 sidecar 都不存在时，旁白导出不会创建 sidecar，而是继承基础导出的已解析 motion。存在逐页 SRT 时，这些路径都可以生成与最终 PPTX 时间轴一致的 `<project_path>/audio/total.srt`；PowerPoint 导出视频后，`video_subtitles.py` 可把冻结的旁白文本与实际视频音轨对齐，生成交付用外挂字幕。
- 可选重新导出：在 `exports/` 生成新版 PPTX，每页对应的 `m4a` / `mp3` / `wav` 音频已嵌入到该页，且页面推进时间根据可配置的页前起始下限、音频长度和页尾停留自动设置——无人值守自动播放和视频导出都不用再手动调时间。旁白不会早于页面转场结束时启动。
- Windows 下可选原生视频导出：`powerpoint_video.py` 把最终带旁白 PPTX 交给 PowerPoint 2016+，并等待其原生 MP4 编码成功或失败。该 raw MP4 保留视觉动画与旁白路径，但 PowerPoint 不保证把原生转场音效或对象动画音效写入视频音轨。
- 原生导出路径直接交付 MP4 且存在已解析动画音效时，`video_sound_mix.py` 会生成独立的 float SFX WAV、最终混音 MP4 和 JSON 回执，证明 stem 已进入实际成片音轨，同时视频流保持不变。
- 也可以显式选择人工实时录制：用桌面版 Windows PowerPoint 全屏播放最终带旁白 deck，再由录屏器捕获放映画面和唯一一路应用 / 系统音频。它会录下 PowerPoint 实际播放的旁白与原生 cue，因此不能再运行 `video_sound_mix.py`。
- 演讲者备注原样保留。

## 它是怎么做到的

1. **备注本身就是为 TTS 写的口播稿**。PPT Master 的 notes 规范刻意产出适合朗读的散文——没有 `[过渡]` / `[停顿]` 这种舞台标记，也没有 `要点：` / `时长：` 这种 meta 行——念出来的内容就是页面上的内容。
2. **AI 替你选音色**。当你提出生成旁白时，AI 根据 deck 的主语言（`zh-CN` / `en-US` / `ja-JP` / `ko-KR` / …）和所选 provider 拉取或解释可用音色，挑出候选并给每个写一句中文调性说明（如"稳重男声·适合财报"）。语速/风格也会基于 notes 信息密度给出推荐值。
3. **配置一次确定**。Default Generate 和 Enhance Native 会一次确认 provider、音色、语速、是否嵌入 PPTX，以及是否继续导出视频。Quick 直接采用明确值，并自动补齐未指定的 provider、音色、语速和嵌入方式；只有明确要求直接交付视频时才开启视频导出。
4. **执行**。Edge、ElevenLabs、MiniMax，以及支持时间戳的 CosyVoice 音色，会依据同一次合成返回的 provider 计时，把每页音频和 SRT 一起写入 `audio/`；Qwen 和显式 CosyVoice 纯音频模式只写音频。完整生成成功后会原子写入 `audio/manifest.json` 记录来源。对于选择旁白 cue 同步的 Generate PPTX，逐页 SRT 与规范自定义动画会让 AI 将当前 SVG 内容组映射到编号后的 SRT cue，并派生无点击的 `narration_animations.json`；与旁白无关的自定义动画保留规范计时，没有动画 sidecar 时则继承基础导出的已解析 motion。随后再导出带音频的 PPTX；存在逐页 SRT 时，才从该 PPTX 读回实际计时并合并。自动视频交付继续调用 PowerPoint 原生编码器，存在 cue 时再完成验收后的混音；显式选择实时放映录制时，则捕获 PowerPoint 实际全屏画面与系统音频、跳过混音，并将交付字幕对齐到验收后的录屏。不支持长音频导入或自动拆分。

字幕保持为外部 SRT 文件：PPT Master 不把字幕嵌入 PPTX，也不烧录进 MP4。自动视频导出委托给本机 Windows PowerPoint，并不是另一套渲染器。

共享阶段见 [`workflows/stages/generate-audio.md`](../../skills/ppt-master/workflows/stages/generate-audio.md)。

## 两条嵌入路径

| 命令 | 用途 |
|---|---|
| `--recorded-narration audio` | 准备 PowerPoint 的"录制的计时和旁白"。要求每页都有音频，并写入页面自动推进时间。用于旁白视频导出。重导出文件保存为 `exports/<name>_<timestamp>_narrated.pptx`。 |
| `--narration-audio-dir audio` | 底层音频嵌入能力。只嵌入匹配到的文件，允许部分页面有音频。用于测试或后续手工整理。导出文件同样带 `_narrated` 后缀。 |
| `--narration-start-floor 0.8` | 可选的页前参数：从目标页转场开始计，到旁白启动的最短秒数。默认 `0.8`；设为 `0` 表示转场结束后立即开始。 |
| `--narration-padding 0.5` | 可选的页尾参数：旁白结束后、页面推进前的静默停留秒数。默认 `0.5`。 |

两个计时参数都可以省略，也可以独立覆盖。转场结束后的实际静默时间为 `max(0, narration_start_floor - transition_duration)`；调整起始下限不会拉长转场本身。

## 怎么触发

deck 导出后，在聊天里直接说就行：

```
你: 给这个 PPT 生成音频
你: 帮我用日语给这个 deck 配一个温柔女声的旁白
你: Generate narration for this deck and re-export with audio embedded.
```

Generate 路线在最终 Stage 2 把 Narration Audio 的有效结果解析为开启时，
也会主动运行该阶段；后续明确指令仍优先于主动默认值。剩下的 AI 全包。

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

# 2B. 用 ElevenLabs 生成 MP3/SRT 对（需要 ELEVENLABS_API_KEY）
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs \
  --voice-id <elevenlabs-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 2C. 用 MiniMax 生成 MP3/SRT 对（支持系统音色或复刻 voice_id）
export MINIMAX_API_KEY="your-minimax-api-key"
# 默认使用国内地址；海外访问可设置 MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax \
  --voice-id <minimax-voice-id> \
  --minimax-model speech-2.8-hd

# 2D. 用 Qwen TTS 仅生成音频（系统音色或复刻音色）
export DASHSCOPE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen \
  --voice-id <qwen-voice> \
  --qwen-model qwen3-tts-flash \
  --qwen-language-type Chinese

# 2E. 用支持时间戳的 CosyVoice 音色生成 MP3/SRT 对
export COSYVOICE_API_KEY="your-dashscope-api-key"
python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice \
  --voice-id <cosyvoice-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 3-4. 仅当选择旁白 cue 同步，且逐页 SRT 与规范 animations.json 都存在时，
#    输出整套 SRT 的指纹，
#    再对照每页当前 SVG 内容组与 SRT cue，编写
#    <project_path>/narration_timing.json；没有对应口播的组不写 cue，
#    后续按正常动画顺序出现。旁白无关的自定义动画或无 sidecar 时直接跳到第 5 步。
python3 skills/ppt-master/scripts/narration_sync.py fingerprint <project_path>

# 4. 从规范 animations.json 派生无点击的 narration_animations.json
python3 skills/ppt-master/scripts/narration_sync.py animations <project_path> \
  --narration-start-floor 0.8 --narration-padding 0.5 --force

# 5A. 与旁白 cue 同步的自定义动画：使用派生 sidecar
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --animation-config narration_animations.json \
  --inherit-motion-from "<base_postflight_report>"

# 5B. 与旁白无关的自定义动画：使用规范计时
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --animation-config animations.json \
  --inherit-motion-from "<base_postflight_report>"

# 5C. 没有动画 sidecar：继承基础导出的 motion，包括 -a auto
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  -o <final_narrated_pptx> --recorded-narration audio \
  --narration-start-floor 0.8 --narration-padding 0.5 \
  --inherit-motion-from "<base_postflight_report>"

# Quick Generate 在所选命令后追加 --quick-generate --with-notes。
# 原生导出混音分支存在已解析音效 cue 时，还需在所选导出命令中追加
# --conversion-trace <final_narrated_trace>；实时放映录制不依赖该 trace 交付声音。

# 6. 存在逐页 SRT 时，按最终 PowerPoint 计时合并
python3 skills/ppt-master/scripts/narration_sync.py subtitles <project_path> \
  --pptx <final_narrated_pptx> --force

# 7. Windows 可选：通过 PowerPoint 导出 raw 视频并等待完成
python3 skills/ppt-master/scripts/powerpoint_video.py --check
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o exports/<raw_powerpoint_video>.mp4

# 8. 原生导出分支的最终 motion 存在音效 cue 时，生成独立 SFX stem 与
#    验收后的混音成片。默认：转场音约 35%，对象音约 25%，最终限幅 -1 dBFS。
python3 skills/ppt-master/scripts/video_sound_mix.py <project_path> \
  --pptx <final_narrated_pptx> \
  --trace <final_narrated_trace> \
  --video exports/<raw_powerpoint_video>.mp4 \
  -o exports/<final_mixed_video>.mp4 --force

# 9. 存在逐页 SRT 时，把冻结的旁白文本与最终视频音轨对齐；
#    第 8 步执行过就使用 mixed，选择录屏则使用验收后的 capture，否则使用 raw。
python3 skills/ppt-master/scripts/video_subtitles.py <project_path> \
  --video "<final_delivery_video>" --language <language> --force
```

发送任何 TTS 请求前，`notes_to_audio.py` 会确认每个 Generate SVG 页面或
Native Enhance 页面都有可读且非空的逐页备注。缺失或空备注会返回退出码
`2`；必须先生成这些备注，再重新运行音频生成。

edge 模式下 `--voice` 是必填项，可用 `--list-voices --locale <locale>` 查看音色。
Edge 默认同时生成最多 3 页音频/SRT。可用 `--concurrency <N>` 调整；
排查连接问题时可设为 `--concurrency 1`。云端 provider 仍保持串行。

Edge 命令会从同一次流式请求中生成 `audio/<stem>.mp3` 与 `audio/<stem>.srt`。句末标点必定结束一条字幕；单条超过默认 20 个可见字符时，优先在逗号、分号或冒号处拆分，仍然过长才在最近的词边界拆分。可用 `--subtitle-max-chars` 调整上限。相邻字幕最多允许 100 毫秒的计时重叠：后一句起点会移到前一句终点；超过该范围则报错。每页 SRT 使用从零计时的页内时间基准，并保留 Edge `WordBoundary` 的实际时间（包括首条字幕前的静音）。

MiniMax 会在同一次非流式 T2A 请求中获取词级字幕并下载返回的 JSON 时间戳。ElevenLabs 使用 `/with-timestamps` 接口，从同一 JSON 响应读取音频和原文字符级对齐。CosyVoice 开启 HTTP 流式响应与 `word_timestamp_enabled`，再使用同次合成返回的完整音频 URL 和词级时间戳。四条 provider 原生计时路径统一使用标点优先、受 `--subtitle-max-chars` 约束的重组逻辑，并原子发布通过校验的音频/SRT 对；整理后的紧凑 cue 用于语义动画映射。

CosyVoice 的时间戳能力取决于模型和音色组合：`cosyvoice-v3.5-plus`、`cosyvoice-v3.5-flash`、`cosyvoice-v3-plus`、`cosyvoice-v3-flash`、`cosyvoice-v2` 的复刻音色支持，[CosyVoice 音色清单](https://help.aliyun.com/zh/model-studio/cosyvoice-voice-list)里明确标记支持时间戳的系统音色也支持。模型与音色家族必须匹配。如果所选音色不能返回计时，而且明确只需要音频，可传入 `--cosyvoice-audio-only`。

Qwen 当前 TTS 的 HTTP 与实时响应都只返回音频，不含词级或字符级对齐。PPT Master 因此保留 Qwen 纯音频路径，不用理论时长估算 SRT。需要逐页字幕时，请选择 Edge、ElevenLabs、MiniMax 或支持时间戳的 CosyVoice 音色。

### Provider 能力与参数选择

| Provider | 逐页 SRT | 原始计时 | 当前默认裁决 |
|---|---|---|---|
| Edge | 支持 | 词级 | 保留所选神经网络音色与 `+0%`；只有 notes 密度确实需要时才小幅调速。 |
| ElevenLabs | 支持 | 原文字符级对齐 | 保留 `eleven_multilingual_v2` 与 `mp3_44100_128`，适合稳定长文旁白。显式调速使用 `--elevenlabs-speed 0.7-1.2`；`eleven_v3` 表现力更强但波动更大，Flash v2.5 更偏延迟与成本。 |
| MiniMax | 支持 | 词级 | 保留现有 `speech-2.8-hd`、32 kHz 单声道 MP3 默认值，除非所选音色或交付目标另有要求。 |
| Qwen | 不支持 | 当前 TTS 响应无计时 | 保留稳定版 `qwen3-tts-flash`；单语 deck 明确指定 `--qwen-language-type`。当前接口固定返回 WAV，不提供格式、采样率或数值语速控制；Instruct 模型仍可通过指令控制表达。不为了不存在的时间戳盲目换模型。 |
| CosyVoice | 有条件支持 | 词级 | 保留兼容系统音色的 `cosyvoice-v3-flash` 与 24 kHz MP3 默认值。复刻/设计音色使用其所属模型；v3.5 音色必须显式选择匹配的 v3.5 模型。 |

CLI 会在发送请求前拒绝超出范围的 ElevenLabs stability/similarity/style、`0.7-1.2` 以外的 ElevenLabs 语速，以及不符合 provider 官方范围的 CosyVoice 音量、语速、音高或采样率。

以上裁决依据当前 [ElevenLabs 带时间戳语音接口](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)、[ElevenLabs 模型指南](https://elevenlabs.io/docs/overview/capabilities/text-to-speech)、[Qwen TTS API](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api) 与 [Qwen-Audio-TTS/CosyVoice HTTP API](https://help.aliyun.com/en/model-studio/cosyvoice-tts-http-api)。阿里云目前建议 CosyVoice HTTP 使用北京地域的 workspace 专属域名；有该域名时通过 `--cosyvoice-base-url` 传入，旧域名仍可用。

阿里云当前的 [TTS 模型选型指南](https://www.alibabacloud.com/help/en/model-studio/tts-model/)建议新建的预置/复刻音色工作流优先考虑 Qwen-Audio 3.0。但这些模型使用 Qwen-Audio-TTS/CosyVoice API 和另一套音色契约，仍不返回时间戳。因此 PPT Master 不会静默替换兼容的 `qwen3-tts-flash` 默认值；只有确实为了音质迁移时，才显式更换模型及其匹配音色，而不是为了字幕能力盲目迁移。

`audio/` 是唯一的当前旁白集，来源由 manifest 记录，因此默认不创建 provider 子目录。重新生成前，脚本会移除过期的 `manifest.json` 与 `total.srt`；仅生成音频的 provider 还会移除同名旧逐页 SRT。只有明确需要保留另一套 provider 结果时，才使用单独的显式输出目录。

选择旁白 cue 同步且存在规范自定义动画时，`narration_timing.json` 与只读的 `animations.json` 刻意分离：前者记录整套有序 SRT 的 SHA-256、可选的旁白起始下限、页尾 padding、有序 SVG 组 ID 和可选的 1-based cue 编号。`narration_sync.py animations` 会拒绝过期的 SRT 指纹，用当前 SVG 校验组 ID，并把 PowerPoint 支持的字段写入派生的 `narration_animations.json`。与 cue 绑定的动画使用和嵌入音频相同的页前起始下限；未绑定 cue 的标题或装饰动画保留规范相对时间。包含 `effects[]` 的分组仍只映射一条 cue：第一条有效动画行锚定该 cue，后续动画行保留相对延迟。与旁白无关的自定义动画直接使用规范 `animations.json`；没有 sidecar 时继承基础报告的已解析 motion。`narration_sync.py subtitles` 从最终 PPTX 读取真实页面关系顺序、毫秒级转场、旁白延迟与页面推进时间，因此 `total.srt` 使用原生 PPTX 时间轴。相对 `--pptx` 路径按 `<project_path>` 解析。

PowerPoint 的视频编码器可能把每个页面 / 媒体段落量化到输出帧时钟；即使 PPTX 计时值正确，这些很小的分页误差仍可能逐页累积。`video_sound_mix.py` 复用逐页旁白相关性，把每个转场 / 对象音效从理论 PPTX 时钟映射到 raw MP4 时钟，而不是直接叠加两套独立时间轴。`video_subtitles.py` 再使用 `stable-ts`，把冻结的旁白原文与最终 `.mp4` / `.wmv` / `.mov` 音轨强制对齐；交付时可为显示效果拆分过长 cue，并生成与视频同名的 SRT，不会改写视频、备注或逐页字幕。

最终带旁白的 SVG 导出使用默认文本流模式即可：在一个禁用自动换行的可编辑文本框中保留作者断行；旁白不要求每一行拆成独立文本框。

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
- **字幕能力** —— ElevenLabs 复刻音色和受支持的 CosyVoice 复刻音色可以生成 provider 原生计时 SRT；Qwen 复刻音色在当前 API 下仍只生成音频。
- **Provider 保留策略** —— 只要该音色仍存在于你的 provider 账户中，就可以继续复用对应 `voice_id`；保留、删除与过期规则以各平台政策为准。

## 依赖

```bash
python3 -m pip install edge-tts
```

已写入 `skills/ppt-master/requirements.txt`。`edge-tts` 调用微软的在线 TTS 服务，**生成时**需要联网；生成后的音频是本地文件，PowerPoint 播放和视频导出都不依赖网络。云端 TTS provider 不需要额外 Python 包，直接通过 HTTPS 调用；按 `.env.example` 配置对应 API Key 即可。

自动 MP4 导出不增加 Python 依赖，但要求 Windows PowerPoint 2016+ 与 Windows PowerShell；macOS 或没有兼容 PowerPoint 的机器保留带旁白 PPTX，改用手动导出。

实时放映录制不增加 PPT Master 依赖，但需要桌面版 Windows PowerPoint 和能
捕获放映画面及应用 / 系统音频的录屏器。[OBS Studio](https://obsproject.com/kb/quick-start-guide)
和 [Windows Game Bar](https://support.microsoft.com/en-us/accessibility/windows/use-a-screen-reader-to-record-your-screen-with-xbox-game-bar)
只是可选工具示例，不是项目依赖。

导出后混入动画音效需要系统 `PATH` 中可用的 `ffmpeg` / `ffprobe` 以及
`numpy`；最终视频字幕对齐另需 `stable-ts`：

```bash
python3 -m pip install numpy stable-ts
```

## 经验值

- **语速**：在 Generate PPTX 路线上，PPT Master 会根据最终 SVG 中的独立信息组调整讲稿长度；每页 2–5 句只是常见节奏，并非上限。可先使用 `+0%`，较密且刻意保留细节的讲稿可尝试 `-5%`。
- **改某一页**：改对应的 `notes/<page>.md`，再跑一次 `notes_to_audio.py`（脚本会重新生成全量 MP3，整套 deck 跑一遍成本很低）。
- **混合语言 deck**（中文里夹英文术语等）：主流 locale 的神经语音对嵌入的外语词处理得不错——按主语言挑音色，先用一页试听再批量。

---

## 导出为视频

只选择一条交付路径：

| 路径 | 适用情况 | 声音结果 |
|---|---|---|
| 原生 `CreateVideo` | 需要自动、可重复的流程 | 原生包含旁白；存在已解析转场 / 对象 cue 时必须运行 `video_sound_mix.py`。 |
| PowerPoint 实时放映录制 | 明确希望成片包含 PowerPoint 实际播放的全部声音 | 录屏已经包含旁白和原生 cue，不能再运行 `video_sound_mix.py`。 |
| 手工执行“创建视频” | 自动化不可用，但可以接受 PowerPoint 编码器 | 声音边界与原生 `CreateVideo` 相同；这不是录屏。 |

带旁白的 PPTX 在 `exports/` 里就绪后，Windows PowerPoint 2016+ 可通过下面的接口自动导出：

```bash
python3 skills/ppt-master/scripts/powerpoint_video.py \
  <final_narrated_pptx> -o <raw_powerpoint_video.mp4>
```

命令使用录制的计时和旁白，默认输出 1080p/30fps，并在 PowerPoint 明确成功或失败后才返回。嵌入音频作为逐页旁白播放，页面自动推进时间控制视频节奏。`--recorded-narration` 会拒绝 `on-click` 对象动画，因为 PPT Master 不生成对象级点击计时。

即使 `animations.json` 和 PPTX package 校验通过，PowerPoint 的 raw MP4
也不保证包含附着在转场或 Animation Pane 行上的声音。Generate 项目的最终
narrated trace 含这些 cue 时，按上面的命令运行 `video_sound_mix.py`：原生声音
仍保留在可编辑 PPTX 中，视觉视频流原样复制，旁白保持 unity，提示音先降增益再
与旁白混合，最终经过峰值限幅，并输出独立 SFX stem 与机器可读验收回执。字幕应
基于 mixed MP4 对齐，而不是 raw 中间产物。

### 录制 PowerPoint 实时放映

这是显式选择的实时采集路径。PowerPoint 仍是渲染器和音频播放器，录屏器只负责
捕获其输出。

1. 用桌面版 Windows PowerPoint 打开最终带旁白 PPTX，从第一页开始全屏放映。使用 deck 已有的自动翻页和无点击对象计时，不录编辑界面或演讲者视图。
2. 只捕获与 deck 宽高比一致的全屏放映画面，关闭通知，并让鼠标指针离开画面。常规目标为 1920×1080、稳定 30fps。
3. 只开启一路应用 / 系统音频捕获；除非明确需要现场讲话，否则关闭麦克风。不能同时捕获桌面音频和应用音频，否则会产生回声。48kHz 是推荐录制设置，不是硬要求。
4. 第一页开始前提前录制，最终声音拖尾结束后再停止。保留原始录屏，然后只裁去首尾缓冲。
5. 验收最终文件确实包含视频流和音频流，旁白清楚，所有已配置 cue 各出现一次，动画与转场完整，并且没有掉帧、通知或桌面 UI。
6. 存在逐页 SRT 时，对最终裁切后的录屏运行 `video_subtitles.py`，把冻结旁白文本对齐到真实录制音轨。

当前录屏验收依赖人工检查，PPT Master 不会声称它具有机器化 cue 回执。如果 cue
盖住旁白或发生削波，应调整 PPTX / cue 素材后重新录制，或改用带确定性增益和限幅
的原生导出加混音路径。Linux 可以准备完整的带旁白 PPTX、音频、计时和字幕，但
这一步仍需要真实的桌面版 Windows PowerPoint 播放端。

### 手工“创建视频”回退（Windows / Mac，Office 2016+）

1. 打开 `exports/` 里那份带旁白的 `.pptx`。
2. **文件 → 导出 → 创建视频**。
3. 选清晰度以及"使用录制的计时和旁白"。
4. **创建视频** → 保存为 `.mp4`（Windows 也支持 `.wmv`）。
5. 若已配置原生转场 / 对象动画音效，先运行上面的声音混合命令；否则 PowerPoint 导出即为最终视频。
6. 再对最终视频运行可选的 `video_subtitles.py` 对齐命令；它会把同名 SRT 写在视频旁边。

PowerPoint for Mac 可以手动导出 MP4/MOV，但微软明确说明其影片导出不会播放动画效果。需要动画保真时，应使用 Windows 自动导出路径。

**Keynote（Mac）**：打开 deck → **文件 → 导出到 → 影片…** ——Keynote 可以读取嵌入的旁白和分页计时，输出 `.m4v` / `.mov`；这不构成 PowerPoint 动画音效已进入成片的保证。

**经验值**：

- **生成旁白不需要麦克风**：原生导出也不需要录制环节；实时放映录制捕获应用 / 系统音频，并关闭麦克风。重跑会复用同一份 notes 与参数，但云端模型仍可能出现轻微的非确定性差异。
- **Windows 动画保真**：PowerPoint 的 Windows 视频导出会保留 PPT Master 的原生视觉页间转场和无点击对象动画；动画音效采用验收后的导出后混音，或与其互斥的实时放映录制。Mac 影片导出存在上面的限制。详见 [转场与动画](./animations.md)。
- **单页改音频**：改对应 `notes/<page>.md`，再跑一遍 `notes_to_audio.py` + 嵌入步骤，再重新导出视频——单页迭代通常不到一分钟。
- **文件大小**：20 页全高清 deck 通常是 30–80 MB，取决于图片量。需要小文件分享时降到高清就行。
