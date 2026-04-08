# PPT Master — AI 生成原生可编辑 PPTX，支持任意文档输入

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)

[English](./README.md) | 中文

丢进一份 PDF、DOCX、网址或 Markdown，拿回一份**原生可编辑的 PowerPoint**——真正的形状、真正的文本框、真正的图表，不是图片。点击任何元素即可编辑。

**核心特点：**

- 每个元素都是真正的 PowerPoint 对象（DrawingML）——无需"转换为形状"
- 支持 Claude Code、Cursor、VS Code Copilot 等主流 AI 编辑器
- 10+ 种输出格式：PPT 16:9、小红书、朋友圈、营销海报等
- 低成本——VS Code Copilot 下最低 **$0.08/份**；非 Opus 模型也能生成不错的结果

**[在线预览 →](https://hugohe3.github.io/ppt-master/)** · [`examples/`](./examples/) — 15 个项目，229 页

## 效果展示

<table>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_magazine_garden.png" alt="杂志风 — 打造小院指南" /><br/><sub><b>杂志风</b> — 暖色调，大图排版，生活方式感</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_academic_medical.png" alt="学术风 — 医学图像分割研究" /><br/><sub><b>学术风</b> — 严谨结构，数据图表，论文答辩场景</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_dark_art_mv.png" alt="暗色艺术风 — MV 深度解析" /><br/><sub><b>暗色艺术风</b> — 电影感深色背景，美术馆陈列感</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_nature_wildlife.png" alt="自然风 — 湿地野生动物纪录" /><br/><sub><b>自然纪录风</b> — 沉浸式摄影，简洁信息层级</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_tech_claude_plans.png" alt="科技风 — Claude AI 订阅方案" /><br/><sub><b>科技 / SaaS 风</b> — 白底卡片，定价表格，产品说明书</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_launch_xiaomi.png" alt="发布会风 — 小米春季新品" /><br/><sub><b>发布会风</b> — 高对比度，参数突出，苹果/小米发布会感</sub></td>
  </tr>
</table>

---

## 快速开始

### 1. 安装

**必需：** [Python](https://www.python.org/downloads/) 3.10+ · **可选：** [Node.js](https://nodejs.org/) 18+（微信公众号转换）· [Pandoc](https://pandoc.org/)（DOCX/EPUB 转换）

```bash
# macOS
brew install python
brew install node                # 可选——用于微信公众号等网页转换
brew install pandoc              # 可选——用于 DOCX/EPUB 转换

# Ubuntu/Debian
sudo apt install python3 python3-pip
sudo apt install nodejs npm      # 可选
sudo apt install pandoc          # 可选

# Windows — 从 python.org、nodejs.org、pandoc.org 下载安装
```

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

日常更新：`python3 skills/ppt-master/scripts/update_repo.py`

### 2. 选择 AI 编辑器

| 工具 | 推荐度 | 说明 |
|------|:------:|------|
| **[Claude Code](https://claude.ai/)** | ⭐⭐⭐ | 效果最佳——原生 Opus，上下文最充裕 |
| [Cursor](https://cursor.sh/) / [VS Code + Copilot](https://code.visualstudio.com/) | ⭐⭐ | 不错的替代方案 |
| Codebuddy IDE | ⭐⭐ | 国产模型最佳选择（Kimi 2.5、MiniMax 2.7） |

### 3. 开始创作

打开 AI 聊天面板，描述你想要的内容：

```
你：我有一份 Q3 季度业绩报告，需要制作成 PPT

AI：好的，先确认设计规范：
   [模板] B) 不使用模板
   [格式] PPT 16:9
   [页数] 8-10 页
   ...
```

AI 全程处理——内容分析、视觉设计、SVG 生成、PPTX 导出。

> **输出说明：** `.pptx` 文件包含原生形状，可直接编辑。同时生成 `_svg.pptx` 参考版（在 PowerPoint 中使用"转换为形状"编辑）。需要 Office 2016+。

> **AI 迷失上下文？** 让它先读 `skills/ppt-master/SKILL.md`。

### 4. AI 生图配置（可选）

```bash
cp .env.example .env    # 然后填入你的 API Key
```

```env
IMAGE_BACKEND=gemini                        # 必填——必须显式指定
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

支持的后端：`gemini` · `openai` · `qwen` · `zhipu` · `volcengine` · `stability` · `bfl` · `ideogram` · `siliconflow` · `fal` · `replicate`

运行 `python3 skills/ppt-master/scripts/image_gen.py --list-backends` 查看分级。环境变量优先于 `.env`。使用各家独立的 Key（`GEMINI_API_KEY`、`OPENAI_API_KEY` 等）——不支持全局 `IMAGE_API_KEY`。

> **建议：** 高质量图片推荐在 [Gemini](https://gemini.google.com/) 中生成并选择 **Download full size**。去水印可用 `scripts/gemini_watermark_remover.py`。

---

## 文档导航

| | 文档 | 说明 |
|---|------|------|
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | 核心流程与规则 |
| 📐 | [画布格式](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9、小红书、朋友圈等 10+ 种格式 |
| 🛠️ | [脚本与工具](./skills/ppt-master/scripts/README.md) | 所有脚本和命令 |
| 💼 | [示例](./examples/README.md) | 15 个项目，229 页 |
| 🏗️ | [技术路线](./docs/zh/technical-design.md) | 架构、设计哲学、为什么选 SVG |
| ❓ | [常见问题](./docs/zh/faq.md) | 费用、编辑、自定义模板 |

---

## 贡献

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 开源协议

[MIT](LICENSE)

## 致谢

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author))（CRAP 设计原则）· 麦肯锡、BCG、贝恩

## 联系

[GitHub Issues](https://github.com/hugohe3/ppt-master/issues) · [@hugohe3](https://github.com/hugohe3)

---

## Star History

如果这个项目对你有帮助，请给一个 ⭐！

<a href="https://star-history.com/#hugohe3/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
 </picture>
</a>

---

## DigitalOcean Support

<p>本项目获得 DigitalOcean Open Source Credits Program 支持：</p>
<p>
  <a href="https://m.do.co/c/547f129aabe1">
    <img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" width="201" />
  </a>
</p>

---

## 赞助

如果这个项目帮你省了时间，欢迎请我喝杯咖啡！

**支付宝**

<img src="docs/assets/alipay-qr.jpg" alt="支付宝收款码" width="250" />

---

Made with ❤️ by Hugo He

[⬆ 回到顶部](#ppt-master--ai-生成原生可编辑-pptx支持任意文档输入)
