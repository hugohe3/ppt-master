# SVG 图片嵌入指南

本文档介绍如何在 SVG 文件中添加图片。

---

## 完整工作流

### 图片资源清单格式

在《设计规范与内容大纲》中定义，每张图片标注**状态**：

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

4. 预览
   └── python3 -m http.server 8000

5. 导出（可选）
   └── python3 tools/embed_images.py *.svg
```

---

## 技术参考

### 外部引用 vs Base64 内嵌

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **外部引用** | 文件小、图片可单独更新 | 需要HTTP服务器 | 开发调试阶段 |
| **Base64 内嵌** | 完全独立、可离线查看 | 文件体积大 | 分享导出阶段 |

---

## 方式一：外部引用（开发阶段推荐）

### 语法

```xml
<image href="image.png" x="0" y="0" width="1280" height="720" 
       preserveAspectRatio="xMidYMid slice"/>
```

### 关键属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `href` | 图片路径（相对或绝对） | `"cover.png"` 或 `"./images/cover.png"` |
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

由于浏览器安全限制，直接双击打开 SVG 无法加载外部图片。需要通过 HTTP 服务器访问：

```bash
# 启动本地服务器
python3 -m http.server --directory <svg目录> 8000

# 访问
http://localhost:8000/your_file.svg
```

---

## 方式二：Base64 内嵌（分享导出推荐）

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

### 步骤 1：生成 Base64 编码

**macOS / Linux:**

```bash
# 将图片转换为 Base64 并保存到文件
base64 -i image.png -o image.b64

# 或直接输出到终端
base64 -i image.png
```

**Windows (PowerShell):**

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("image.png")) > image.b64
```

### 步骤 2：嵌入 SVG

**手动方式：**

1. 打开 `.b64` 文件，复制全部内容
2. 在 SVG 中替换 `href="image.png"` 为 `href="data:image/png;base64,<粘贴内容>"`

**自动化脚本（推荐）：**

```python
#!/usr/bin/env python3
"""
SVG 图片嵌入工具
将 SVG 中引用的外部图片转换为 Base64 内嵌格式
"""

import os
import base64
import re
import sys

def get_mime_type(filename):
    """根据文件扩展名返回 MIME 类型"""
    ext = filename.lower().split('.')[-1]
    mime_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
    }
    return mime_map.get(ext, 'application/octet-stream')

def embed_images_in_svg(svg_path):
    """将 SVG 文件中的外部图片转换为 Base64 内嵌"""
    svg_dir = os.path.dirname(svg_path)
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配 href="xxx.png" 或 href="xxx.jpg" 等
    pattern = r'href="([^"]+\.(png|jpg|jpeg|gif|webp))"'
    
    def replace_with_base64(match):
        img_path = match.group(1)
        full_path = os.path.join(svg_dir, img_path)
        
        if not os.path.exists(full_path):
            print(f"Warning: Image not found: {full_path}")
            return match.group(0)
        
        with open(full_path, 'rb') as img_file:
            b64_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        mime_type = get_mime_type(img_path)
        print(f"Embedded: {img_path} ({len(b64_data)} chars)")
        
        return f'href="data:{mime_type};base64,{b64_data}"'
    
    new_content = re.sub(pattern, replace_with_base64, content)
    
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated: {svg_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python embed_images.py <svg_file> [svg_file2] ...")
        sys.exit(1)
    
    for svg_file in sys.argv[1:]:
        if os.path.exists(svg_file):
            embed_images_in_svg(svg_file)
        else:
            print(f"File not found: {svg_file}")
```

### 步骤 3：使用脚本

```bash
# 保存上述脚本为 embed_images.py，然后运行：
python3 embed_images.py path/to/your_file.svg

# 批量处理多个文件
python3 embed_images.py *.svg
```

---

## 完整工作流示例

### 场景：制作包含图片的 PPT

```
1. 开发阶段
   ├── 创建 SVG 文件，使用外部引用
   │   <image href="cover.png" .../>
   │
   ├── 启动本地服务器预览
   │   python3 -m http.server 8000
   │
   └── 调试修改，快速迭代

2. 导出阶段
   ├── 运行嵌入脚本
   │   python3 embed_images.py *.svg
   │
   └── 得到独立的 SVG 文件，可直接分享
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
├── svg_output/
│   ├── 01_cover.svg          # 开发版（外部引用）
│   ├── cover_bg.png          # 图片资源
│   └── ...
└── svg_export/
    └── 01_cover_embedded.svg # 导出版（Base64 内嵌）
```

### 3. 圆角处理（禁止 clipPath）

由于 `clipPath` 在 PPT 中不兼容，**禁止**使用裁剪路径为图片加圆角。

推荐替代方案：

- 在生成图片时直接处理圆角（如导出为带圆角的 PNG）
- 或用同尺寸的圆角矩形覆盖边缘（视觉模拟）

---

## 常见问题

### Q: 直接打开 SVG 看不到图片？

A: 浏览器安全策略阻止了本地文件的跨域请求。解决方案：
- 使用 HTTP 服务器访问
- 或将图片转换为 Base64 内嵌

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
