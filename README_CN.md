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

**[在线预览](https://hugohe3.github.io/ppt-master/)** · [`examples/`](./examples/) — 15 个项目，229 页

| | 项目 | 页数 | 风格 |
|---|------|:----:|------|
| 🏢 | [心理治疗中的依恋](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E5%BF%83%E7%90%86%E6%B2%BB%E7%96%97%E4%B8%AD%E7%9A%84%E4%BE%9D%E6%81%8B) | 32 | 顶级咨询 |
| 🎨 | [Debug 六步法](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%80%9A%E7%94%A8%E7%81%B5%E6%B4%BB%2B%E4%BB%A3%E7%A0%81_debug%E5%85%AD%E6%AD%A5%E6%B3%95) | 10 | 深色科技 |
| ✨ | [地山谦卦深度研究](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E6%98%93%E7%90%86%E9%A3%8E_%E5%9C%B0%E5%B1%B1%E8%B0%A6%E5%8D%A6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6) | 20 | 易经美学 |

---

## 快速开始

### 1. 安装

**必需：** Python 3.8+ · **可选：** [Node.js](https://nodejs.org/) 18+（微信公众号转换）· [Pandoc](https://pandoc.org/)（DOCX/EPUB 转换）

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

1. Fork → 分支 → 提交 → PR

**方向：** 🎨 模板 · 📊 图表 · 📝 文档 · 🐛 Bug · 💡 建议

## 开源协议

[MIT](LICENSE)

## 致谢

[SVG Repo](https://www.svgrepo.com/) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author))（CRAP 设计原则）· 麦肯锡、BCG、贝恩

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

## 赞助

如果这个项目帮你省了时间，欢迎请我喝杯咖啡！

**支付宝**

<img src="docs/assets/alipay-qr.jpg" alt="支付宝收款码" width="250" />

---

Made with ❤️ by Hugo He

[⬆ 回到顶部](#ppt-master--ai-生成原生可编辑-pptx支持任意文档输入)
