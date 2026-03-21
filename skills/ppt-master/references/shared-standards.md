# Shared Technical Standards

PPT Master 公共技术约束，消除跨角色文件重复。

---

## 1. SVG 禁用功能黑名单

以下功能在生成 SVG 时**绝对禁止**使用，否则 PPT 导出将出错：

| 禁止功能 | 说明 |
|----------|------|
| `clipPath` | 裁剪路径 |
| `mask` | 遮罩 |
| `<style>` | 内嵌样式表 |
| `class` | CSS 选择器属性（`<defs>` 内 `id` 为合法引用，不在此列） |
| 外部 CSS | 外部样式表链接 |
| `<foreignObject>` | 嵌入外部内容 |
| `<symbol>` + `<use>` | 符号引用复用 |
| `textPath` | 沿路径排列文本 |
| `@font-face` | 自定义字体声明 |
| `<animate*>` / `<set>` | SVG 动画 |
| `<script>` / 事件属性 | 脚本与交互 |
| `marker` / `marker-end` | 线段端点标记 |
| `<iframe>` | 内嵌框架 |

---

## 2. PPT 兼容性替代方案

| 禁止写法 | 正确替代 |
|----------|---------|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">...</g>` | 每个子元素单独设置 `fill-opacity` / `stroke-opacity` |
| `<image opacity="0.3"/>` | 图片后叠加 `<rect fill="背景色" opacity="0.7"/>` 遮罩层 |
| `marker-end` 箭头 | 用 `<polygon>` 绘制三角形箭头 |

**记忆口诀**：PPT 不认 rgba、不认组透明、不认图片透明、不认 marker。

---

## 3. 画布格式速查

### 演示文稿

| 格式 | viewBox | 尺寸 | 比例 |
|------|---------|------|------|
| PPT 16:9 | `0 0 1280 720` | 1280x720 | 16:9 |
| PPT 4:3 | `0 0 1024 768` | 1024x768 | 4:3 |

### 社交媒体

| 格式 | viewBox | 尺寸 | 比例 |
|------|---------|------|------|
| 小红书 | `0 0 1242 1660` | 1242x1660 | 3:4 |
| 朋友圈 / Instagram Post | `0 0 1080 1080` | 1080x1080 | 1:1 |
| Story / 抖音竖屏 | `0 0 1080 1920` | 1080x1920 | 9:16 |

### 营销物料

| 格式 | viewBox | 尺寸 | 比例 |
|------|---------|------|------|
| 微信公众号头图 | `0 0 900 383` | 900x383 | 2.35:1 |
| 横版 Banner | `0 0 1920 1080` | 1920x1080 | 16:9 |
| 竖版海报 | `0 0 1080 1920` | 1080x1920 | 9:16 |
| A4 打印 (150dpi) | `0 0 1240 1754` | 1240x1754 | 1:1.414 |

---

## 4. 基础 SVG 规则

- **viewBox** 必须与画布尺寸一致（`width`/`height` 与 `viewBox` 匹配）
- **背景**：用 `<rect>` 定义页面背景色
- **换行**：用 `<tspan>` 手动换行，禁止 `<foreignObject>`
- **字体**：仅使用系统字体（微软雅黑、Arial、Calibri 等），禁止 `@font-face`
- **样式**：仅使用内联样式（`fill="..."` `font-size="..."`），禁止 `<style>` / `class`（`<defs>` 内 `id` 合法）
- **颜色**：使用 HEX 值，透明度用 `fill-opacity` / `stroke-opacity`
- **图片引用**：`<image href="../images/xxx.png" preserveAspectRatio="xMidYMid slice"/>`
- **图标占位**：`<use data-icon="icon-name" x="" y="" width="48" height="48" fill="#HEX"/>`（后处理自动嵌入）

---

## 5. 后处理三步命令

必须按顺序执行，不可跳过或添加额外参数：

```bash
# 1. 拆分讲稿到各页备注文件
python3 scripts/total_md_split.py <项目路径>

# 2. SVG 后处理（图标嵌入、图片裁剪/嵌入、文本扁平化、圆角矩形转 Path）
python3 scripts/finalize_svg.py <项目路径>

# 3. 导出 PPTX（从 svg_final/ 导出，默认嵌入演讲备注）
python3 scripts/svg_to_pptx.py <项目路径> -s final
```

**禁止事项**：
- 禁止用 `cp` 替代 `finalize_svg.py`
- 禁止从 `svg_output/` 直接导出，必须从 `svg_final/`（`-s final`）导出
- 禁止添加 `--only` 等额外参数
- Optimizer 优化后需重新执行全部三步

---

## 6. 项目目录结构

```
project/
├── svg_output/    # 原始 SVG（Executor 输出，含占位符）
├── svg_final/     # 后处理完成的最终 SVG（finalize_svg.py 输出）
├── images/        # 图片资源（用户提供 + AI 生成）
├── notes/         # 演讲备注（与 SVG 同名的 .md 文件）
│   └── total.md   # 完整演讲备注文稿（拆分前）
├── templates/     # 项目使用的模板（如有）
└── *.pptx         # 导出的 PPT 文件
```
