# SVG 图片嵌入指南

本文档介绍如何在 SVG 文件中添加图片，并说明当前项目中的推荐工作流。

---

## 完整工作流

### 图片资源清单格式

在《设计规范与内容大纲》中定义，每张图片标注**状态**。若图片方案包含「B) 用户提供」，需在 Strategist 阶段完成八项确认后立即运行 `analyze_images.py`，并在输出设计规范前完成清单填充。

```markdown
## 图片资源清单

| 文件名 | 尺寸 | 用途 | 状态 | 生成描述 |
|--------|------|------|------|----------|
| cover_bg.png | 1280×720 | 封面背景 | 待生成 | 现代科技感抽象背景，深蓝渐变 |
| product.png | 600×400 | 第3页 | 已有 | - |
| team.png | 600×400 | 第5页 | 占位符 | 团队协作场景（后期补充） |
```

### 三种状态的处理

| 状态 | 含义 | Executor 处理方式 |
|------|------|-------------------|
| **待生成** | 需 AI 生成，有描述 | 先生成图片放入 `images/`，再用 `<image>` 引用 |
| **已有** | 用户已有图片 | 放入 `images/`，用 `<image>` 引用 |
| **占位符** | 暂不处理 | 用虚线框占位，后期替换 |

### 工作流程

```
1. Strategist 定义图片需求
   └── 添加「图片资源清单」，标注每张图片状态

2. 图片准备（状态：待生成/已有）
   ├── 待生成：AI 工具生成 或 手动去平台生成
   └── 已有：用户直接提供
   └── 放入 项目/images/ 目录

3. Executor 生成 SVG（SVG 在 svg_output/ 目录中）
   ├── 已有/待生成 → <image href="../images/xxx.png" .../>
   └── 占位符 → 虚线框 + 描述文本

4. 预览原始版本
   └── python3 -m http.server -d <项目路径> 8000
      然后访问 /svg_output/<文件名>.svg

5. 后处理与导出（推荐）
   ├── python3 tools/finalize_svg.py <项目路径>
   └── python3 tools/svg_to_pptx.py <项目路径> -s final
```

> 推荐做法：生成阶段在 `svg_output/` 中保留外部引用，后处理阶段通过 `finalize_svg.py` 自动把图片嵌入到 `svg_final/`，再从 `svg_final/` 导出 PPTX。

---

## 技术参考

### 外部引用 vs Base64 内嵌

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **外部引用** | 文件小、迭代快、便于替换素材 | 预览时需从项目根目录起 HTTP 服务 | `svg_output/` 开发调试阶段 |
| **Base64 内嵌** | 文件独立、导出稳定、适合 PPTX | 文件体积更大 | `svg_final/` 导出与交付阶段 |

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
| `href` | 图片路径（相对或绝对） | `"../images/cover.png"` 或 `"../sources/article_files/image_1.png"` |
| `x`, `y` | 图片左上角位置 | `x="0" y="0"` |
| `width`, `height` | 图片显示尺寸 | `width="1280" height="720"` |
| `preserveAspectRatio` | 缩放方式 | `"xMidYMid slice"` 居中裁剪 |

### preserveAspectRatio 常用值

| 值 | 效果 |
|----|------|
| `xMidYMid slice` | 居中显示，裁剪溢出部分（类似 CSS `cover`） |
| `xMidYMid meet` | 居中显示，完整显示（类似 CSS `contain`） |
| `none` | 拉伸填满，不保持比例 |

### 预览方式

由于浏览器安全限制，直接双击打开 SVG 无法加载外部图片。项目中的图片通常位于 `images/` 或 `sources/*_files/`，因此应从**项目根目录**启动 HTTP 服务器：

```bash
# 启动本地服务器
python3 -m http.server -d <项目路径> 8000

# 访问
http://localhost:8000/svg_output/your_file.svg
```

---

## 方式二：Base64 内嵌（交付阶段推荐）

### 语法

```xml
<image href="data:image/png;base64,iVBORw0KGgo..." x="0" y="0" width="1280" height="720"/>
```

### 格式说明

```
data:<MIME类型>;base64,<Base64编码数据>
```

| MIME 类型 | 文件格式 |
|-----------|----------|
| `image/png` | PNG |
| `image/jpeg` | JPG/JPEG |
| `image/gif` | GIF |
| `image/webp` | WebP |
| `image/svg+xml` | SVG |

---

## 转换流程

### 推荐方式：统一走 `finalize_svg.py`

```bash
# 从 svg_output 复制到 svg_final，并自动处理图标、图片、文本与圆角
python3 tools/finalize_svg.py <项目路径>

# 从最终版本导出 PPTX
python3 tools/svg_to_pptx.py <项目路径> -s final
```

### 独立使用 `embed_images.py`（高级用法）

当你只想单独处理某几个 SVG，而不想跑完整个后处理流程时，可直接使用：

```bash
# 处理单个 SVG
python3 tools/embed_images.py <svg文件>

# 批量处理多个 SVG
python3 tools/embed_images.py <项目路径>/svg_output/*.svg

# 仅预览，不实际写回
python3 tools/embed_images.py --dry-run <项目路径>/svg_output/*.svg
```

---

## 完整工作流示例

### 场景：制作包含图片的 PPT

```
1. 开发阶段
   ├── 创建 SVG 文件，使用外部引用
   │   <image href="../images/cover.png" .../>
   │
   ├── 启动本地服务器预览
   │   python3 -m http.server -d <项目路径> 8000
   │
   └── 调试修改，快速迭代

2. 导出阶段
   ├── 运行后处理
   │   python3 tools/finalize_svg.py <项目路径>
   │
   └── 从 svg_final/ 导出 PPTX
       python3 tools/svg_to_pptx.py <项目路径> -s final
```

---

## 最佳实践

### 1. 图片优化

在嵌入前优化图片大小，减少 SVG 文件体积：

```bash
# 使用 ImageMagick 压缩 PNG
convert input.png -quality 85 -resize 1920x1080\> output.png

# 使用 pngquant 压缩（推荐）
pngquant --quality=65-80 input.png -o output.png
```

### 2. 文件组织

```
project/
├── images/
│   ├── cover_bg.png
│   └── ...
├── sources/
│   ├── article.md
│   └── article_files/
│       └── image_1.png
├── svg_output/
│   ├── 01_cover.svg          # 原始版本（外部引用）
│   └── ...
└── svg_final/
    ├── 01_cover.svg          # 最终版本（已嵌入图片）
    └── ...
```

### 3. 圆角处理（禁止 clipPath）

由于 `clipPath` 在 PPT 中不兼容，**禁止**使用裁剪路径为图片加圆角。

推荐替代方案：

- 在生成图片时直接处理圆角（如导出为带圆角的 PNG）
- 或用同尺寸的圆角矩形覆盖边缘（视觉模拟）

---

## 常见问题

### Q: 直接打开 SVG 看不到图片？

A: 浏览器安全策略阻止了本地文件的跨目录请求。解决方案：
- 从项目根目录启动 HTTP 服务器，再访问 `/svg_output/*.svg`
- 或先运行 `python3 tools/finalize_svg.py <项目路径>`，再查看 `svg_final/`

### Q: Base64 文件太大怎么办？

A: 
1. 压缩原始图片
2. 使用 JPEG 格式（比 PNG 更小）
3. 降低图片分辨率（匹配实际显示尺寸即可）

### Q: 如何反向提取 Base64 图片？

A: 
```bash
# 从 Base64 还原图片
base64 -d image.b64 > image.png
```

---

## 相关资源

- [MDN: SVG image 元素](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/image)
- [MDN: Data URLs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs)
- [SVG preserveAspectRatio 详解](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/preserveAspectRatio)
