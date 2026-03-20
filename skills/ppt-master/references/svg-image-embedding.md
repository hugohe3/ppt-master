> 📎 公共技术约束见 shared-standards.md

# SVG 图片嵌入指南

在 SVG 文件中添加图片的技术规范和推荐工作流。

---

## 图片资源清单格式

在《设计规范与内容大纲》中定义，每张图片标注状态。若图片方案包含「B) 用户提供」，需在 Strategist 阶段完成八项确认后立即运行 `analyze_images.py`，并在输出设计规范前完成清单填充。

```markdown
| 文件名 | 尺寸 | 用途 | 状态 | 生成描述 |
|--------|------|------|------|----------|
| cover_bg.png | 1280x720 | 封面背景 | 待生成 | 现代科技感抽象背景，深蓝渐变 |
| product.png | 600x400 | 第3页 | 已有 | - |
| team.png | 600x400 | 第5页 | 占位符 | 团队协作场景（后期补充） |
```

### 三种状态的处理

| 状态 | 含义 | Executor 处理方式 |
|------|------|-------------------|
| **待生成** | 需 AI 生成，有描述 | 先生成图片放入 `images/`，再用 `<image>` 引用 |
| **已有** | 用户已有图片 | 放入 `images/`，用 `<image>` 引用 |
| **占位符** | 暂不处理 | 用虚线框占位，后期替换 |

---

## 工作流程

```
1. Strategist 定义图片需求 → 添加图片资源清单，标注每张状态
2. 图片准备（待生成/已有）→ 放入 项目/images/
3. Executor 生成 SVG（svg_output/）
   ├── 已有/待生成 → <image href="../images/xxx.png" .../>
   └── 占位符 → 虚线框 + 描述文本
4. 预览：python3 -m http.server -d <项目路径> 8000 → /svg_output/<文件名>.svg
5. 后处理与导出
   ├── python3 scripts/finalize_svg.py <项目路径>
   └── python3 scripts/svg_to_pptx.py <项目路径> -s final
```

> 推荐：生成阶段在 `svg_output/` 保留外部引用，后处理通过 `finalize_svg.py` 自动嵌入图片到 `svg_final/`，再从 `svg_final/` 导出 PPTX。

---

## 外部引用 vs Base64 内嵌

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **外部引用** | 文件小、迭代快、便于替换 | 预览需从项目根起 HTTP 服务 | `svg_output/` 开发阶段 |
| **Base64 内嵌** | 文件独立、导出稳定 | 文件体积大 | `svg_final/` 交付阶段 |

---

## 方式一：外部引用（生成阶段推荐）

### 语法

```xml
<image href="../images/image.png" x="0" y="0" width="1280" height="720"
       preserveAspectRatio="xMidYMid slice"/>
```

### 关键属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `href` | 图片路径（相对或绝对） | `"../images/cover.png"` |
| `x`, `y` | 图片左上角位置 | `x="0" y="0"` |
| `width`, `height` | 图片显示尺寸 | `width="1280" height="720"` |
| `preserveAspectRatio` | 缩放方式 | `"xMidYMid slice"` |

### preserveAspectRatio 常用值

| 值 | 效果 |
|----|------|
| `xMidYMid slice` | 居中裁剪（类似 CSS `cover`） |
| `xMidYMid meet` | 完整显示（类似 CSS `contain`） |
| `none` | 拉伸填满，不保持比例 |

### 预览方式

浏览器安全限制下，直接双击 SVG 无法加载外部图片。从项目根目录启动 HTTP 服务器：

```bash
python3 -m http.server -d <项目路径> 8000
# 访问 http://localhost:8000/svg_output/your_file.svg
```

---

## 方式二：Base64 内嵌（交付阶段推荐）

### 语法

```xml
<image href="data:image/png;base64,iVBORw0KGgo..." x="0" y="0" width="1280" height="720"/>
```

### MIME 类型

| MIME 类型 | 文件格式 |
|-----------|----------|
| `image/png` | PNG |
| `image/jpeg` | JPG/JPEG |
| `image/gif` | GIF |
| `image/webp` | WebP |
| `image/svg+xml` | SVG |

---

## 转换流程

### 推荐：统一走 finalize_svg.py

```bash
python3 scripts/finalize_svg.py <项目路径>        # 图标、图片、文本、圆角一次处理
python3 scripts/svg_to_pptx.py <项目路径> -s final # 从最终版本导出 PPTX
```

### 独立使用 embed_images.py（高级用法）

仅处理特定 SVG 而不跑完整后处理时：

```bash
python3 scripts/embed_images.py <svg文件>                        # 单个
python3 scripts/embed_images.py <项目路径>/svg_output/*.svg      # 批量
python3 scripts/embed_images.py --dry-run <项目路径>/svg_output/*.svg  # 预览
```

---

## 最佳实践

### 图片优化

嵌入前压缩图片以减少文件体积：

```bash
convert input.png -quality 85 -resize 1920x1080\> output.png  # ImageMagick
pngquant --quality=65-80 input.png -o output.png               # pngquant（推荐）
```

### 文件组织

```
project/
├── images/            # 图片资源
├── sources/           # 源文件及其附带图片
│   └── article_files/
├── svg_output/        # 原始版本（外部引用）
└── svg_final/         # 最终版本（已嵌入图片）
```

### 圆角处理（禁止 clipPath）

由于 `clipPath` 在 PPT 中不兼容，禁止使用裁剪路径为图片加圆角。替代方案：
- 生成图片时直接处理圆角（导出为带圆角的 PNG）
- 或用同尺寸圆角矩形覆盖边缘（视觉模拟）

---

## 常见问题

**Q: 直接打开 SVG 看不到图片？**
浏览器安全策略阻止跨目录请求。从项目根目录启动 HTTP 服务器，或先运行 `finalize_svg.py` 再查看 `svg_final/`。

**Q: Base64 文件太大？**
压缩原始图片、使用 JPEG 格式、降低分辨率（匹配实际显示尺寸即可）。

**Q: 如何反向提取 Base64 图片？**
```bash
base64 -d image.b64 > image.png
```
