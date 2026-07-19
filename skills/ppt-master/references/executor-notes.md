> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core.

# Executor Speaker-notes Branch

Conditional late-stage authority for generating the complete speaker-notes document.

**Trigger**: load only after all SVG pages pass the final quality check.

## 1. Speaker Notes Generation Framework

### 1.1 Generate Complete Speaker Notes Document

After all SVG pages are finalized, enter Logic Construction Phase and write the full notes to `notes/total.md`. Batch-writing (not per-page) lets transitions plan coherently.

**Pure spoken narration**: notes are read aloud verbatim by `notes_to_audio.py` (TTS). Write only what should be spoken. No visible markers, no labeled meta-lines, no enumerated key-point lists, no duration annotations — anything you write outside the heading will be vocalized.

**Per-page structure**: `# <number>_<page_title>` heading (the `#` heading line is the only thing stripped before TTS), pages separated by `---`. Body is 2–5 natural sentences carrying the page's core message. Page-to-page transitions live inside the opening sentence as natural prose ("接下来……" / "Having framed X, let's turn to Y") — no bracketed `[过渡]` / `[Transition]` tags.

**Reading-mode note burden**:

| `consumption_mode` | Notes emphasis |
|---|---|
| `text` | Add interpretation or transition without reading the already self-contained page aloud. |
| `balanced` | Connect the visible claim and evidence, explain the trade-off, and bridge to the next page. |
| `presentation` | Carry the reasoning, context, and supporting detail intentionally omitted from the sparse projected surface. |

**Concrete examples** — same shape applies to any language; just write naturally in that language.

中文 deck：

```
# 02_市场格局

在明确了行业背景之后，我们来看具体的市场格局。当前线上零售集中度持续上升，前三大平台合计份额已经达到百分之六十八，腰部玩家正在被快速挤压，留给新进入者的窗口期不超过十八个月。这意味着我们的策略必须聚焦，而不是铺开。
```

英文 deck：

```
# 02_market_landscape

Having framed the industry backdrop, let's look at the actual market landscape. Online retail concentration keeps rising — the top three platforms now hold sixty-eight percent of combined share, mid-tier players are being squeezed fast, and the window for new entrants is under eighteen months. This means our strategy has to focus, not spread.
```

> 日本語 / 한국어 / 其他语言：照搬同样的结构，用对应语言自然书写即可。

**Number readability**: TTS reads digits and symbols literally. Prefer fully-spelled forms in the language being spoken when literal pronunciation would be awkward (e.g. Chinese "百分之六十八" reads better than "68%"; "1-2分钟" reads as "一减二分钟"). Plain integers and percentages in English are fine as-is.

**Common mistakes to avoid**:
- Leaving any bracketed stage marker (`[过渡]` / `[Transition]` / `[Pause]` / `[Data]` / `[Scan Room]` / `[Interactive]` / `[Benchmark]` etc.) in the text — they will be read aloud literally.
- Adding `要点：① …` / `Key points: (1) …` / `时长：2分钟` / `Duration: 2 minutes` / `Flex: …` lines — TTS will speak "要点 一 …".
- Mixing languages within one deck's notes.

After `notes/total.md` is complete, return to Generate Step 7.1. The route authority owns the serial split command and its success criterion.
