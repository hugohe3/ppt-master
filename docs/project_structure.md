# 项目结构规范

本文档定义了 PPT Master 项目的标准目录结构和文件组织规范。

## 目录结构

### 标准项目结构

```
{project_name}_{format}_{YYYYMMDD}/
├── README.md                           # 项目说明（必需）
├── 设计规范与内容大纲.md                 # 设计规范（必需）
├── 来源文档.md                          # 来源文档（可选）
├── preview.html                        # 预览页面（自动生成）
├── svg_output/                         # SVG 输出目录（必需）
│   ├── slide_01_cover.svg
│   ├── slide_02_xxx.svg
│   └── ...
└── svg_output_flattext/                # 扁平化输出（可选）
    ├── slide_01_cover.svg
    └── ...
```

### 项目命名规范

**格式**: `{project_name}_{format}_{YYYYMMDD}`

**组成部分**:
- `project_name`: 项目名称，使用下划线分隔单词
- `format`: 画布格式标识（见下表）
- `YYYYMMDD`: 创建日期，8位数字

**画布格式标识**:

| 标识 | 全称 | 尺寸 | viewBox |
|------|------|------|---------|
| `ppt169` | PPT 16:9 | 1280×720 | 0 0 1280 720 |
| `ppt43` | PPT 4:3 | 1024×768 | 0 0 1024 768 |
| `wechat` | 微信公众号头图 | 900×383 | 0 0 900 383 |
| `xiaohongshu` | 小红书 3:4 | 1242×1660 | 0 0 1242 1660 |
| `moments` | 朋友圈/Instagram 1:1 | 1080×1080 | 0 0 1080 1080 |
| `story` | Story/竖版 9:16 | 1080×1920 | 0 0 1080 1920 |
| `banner` | 横版 Banner 16:9 | 1920×1080 | 0 0 1920 1080 |
| `a4` | A4 打印 | 1240×1754 | 0 0 1240 1754 |

**示例**:
```
gemini_marketing_guide_ppt169_20251110
洪九果品案例分析_ppt169_20251101
写给大家看的设计书_wechat_20251015
```

## 必需文件

### 1. README.md

项目说明文件，包含以下内容：

```markdown
# {项目名称}

## 项目信息

- **创建日期**: YYYY-MM-DD
- **画布格式**: 格式名称 (尺寸)
- **设计风格**: 通用灵活/高端咨询
- **状态**: 进行中/已完成

## 项目说明

[项目描述和背景]

## 内容概览

[内容结构和要点]

## 使用说明

### 预览 SVG 文件

[预览方法]

## 文件说明

[文件清单和说明]
```

### 2. 设计规范与内容大纲.md

设计规范文件，可使用以下文件名之一：
- `设计规范与内容大纲.md` (推荐)
- `design_specification.md`
- `设计规范.md`

必须包含：
- 项目基本信息
- 设计规范（颜色、字体、布局）
- 内容大纲
- 页面详细规划

### 3. svg_output/

SVG 文件输出目录，必须存在且包含至少一个 SVG 文件。

**SVG 文件命名规范**:
- 格式: `slide_{序号}_{名称}.svg`
- 序号: 两位数字，从 01 开始
- 名称: 英文或拼音，使用下划线分隔

**示例**:
```
slide_01_cover.svg
slide_02_overview.svg
slide_03_key_points.svg
```

## 可选文件

### 1. 来源文档.md

原始内容文档，用于记录来源材料。

### 2. preview.html

预览页面，由 `generate_preview.py` 自动生成。

**不建议手动编辑**，应使用工具重新生成。

### 3. svg_output_flattext/

扁平化 SVG 输出目录，由 `flatten_tspan.py` 生成。

用于将 `<tspan>` 转换为独立 `<text>` 元素的版本。

### 4. logs/

日志目录，用于记录迭代过程（可选）。

## 项目生命周期

### 1. 初始化

使用项目管理工具创建标准结构：

```bash
python3 tools/project_manager.py init <project_name> --format ppt169
```

### 2. 开发

1. 编辑 `设计规范与内容大纲.md`
2. 使用 AI 角色（Strategist → Executor → Optimizer）生成 SVG
3. 将 SVG 文件保存到 `svg_output/`

### 3. 预览

生成预览页面：

```bash
python3 tools/generate_preview.py <project_path>
```

### 4. 验证

验证项目完整性：

```bash
python3 tools/project_manager.py validate <project_path>
```

### 5. 发布

1. 确保所有文件完整
2. 生成预览页面
3. （可选）生成扁平化版本
4. 移动到 `examples/` 目录

## 目录组织

### projects/ - 进行中的项目

存放正在开发的项目，使用完整的项目结构。

```
projects/
├── project_a_ppt169_20251116/
├── project_b_wechat_20251115/
└── ...
```

### examples/ - 完成的示例项目

存放已完成的示例项目，供参考和展示。

```
examples/
├── gemini_marketing_guide_ppt169_20251110/
├── 洪九果品案例分析_ppt169_20251101/
└── ...
```

## 文件编码和格式

### 编码

所有文本文件使用 **UTF-8** 编码。

### Markdown 文件

- 使用标准 Markdown 语法
- 中英文之间添加空格（可选，但推荐）
- 代码块指定语言

### SVG 文件

- UTF-8 编码
- 无 XML 声明（或使用标准声明）
- 遵循 SVG 1.1 规范
- 禁止使用 `<foreignObject>`
- 文本换行使用 `<tspan>`

## 版本控制

### Git 忽略规则

建议在 `.gitignore` 中添加：

```gitignore
# 临时文件
*.tmp
*.bak
*~

# 系统文件
.DS_Store
Thumbs.db

# 编辑器文件
.vscode/
.idea/

# 可选的扁平化输出（如果不需要版本控制）
# svg_output_flattext/
```

### 提交规范

- 每个项目作为独立目录提交
- 提交信息格式: `[项目名] 描述`
- 示例: `[gemini_guide] 添加封面和目录页`

## 最佳实践

### 1. 命名一致性

- 项目名使用英文或拼音
- 文件名使用小写字母和下划线
- 避免使用特殊字符和空格

### 2. 文档完整性

- README.md 必须包含完整的项目信息
- 设计规范必须详细且可执行
- 每个 SVG 文件都应有对应的规划说明

### 3. 目录整洁

- 不要在项目根目录放置临时文件
- 使用 svg_output/ 存放所有 SVG
- 日志和草稿放在 logs/ 目录

### 4. 预览及时更新

- 每次修改 SVG 后重新生成预览
- 确保预览页面与实际文件同步

### 5. 验证后发布

- 发布前运行 validate 检查
- 确保没有错误和重要警告
- 测试预览页面是否正常工作

## 工具使用

### 项目管理工具

```bash
# 初始化项目
python3 tools/project_manager.py init <name> --format ppt169

# 验证项目
python3 tools/project_manager.py validate <path>

# 查看项目信息
python3 tools/project_manager.py info <path>

# 生成预览
python3 tools/project_manager.py preview <path>
```

### 预览生成工具

```bash
# 为单个项目生成
python3 tools/generate_preview.py <project_path>

# 为所有项目生成
python3 tools/generate_preview.py --all

# 批量生成
python3 tools/generate_preview.py --batch <path1> <path2> ...

# 交互模式
python3 tools/generate_preview.py
```

### 文本扁平化工具

```bash
# 扁平化整个目录
python3 tools/flatten_tspan.py <project>/svg_output

# 扁平化单个文件
python3 tools/flatten_tspan.py <input.svg> <output.svg>
```

## 迁移指南

### 从旧格式迁移

如果你有使用旧格式的项目，可以按以下步骤迁移：

1. **重命名目录**（如需要）
   ```bash
   mv old_name new_name_format_YYYYMMDD
   ```

2. **创建缺失的文件**
   - 添加 README.md
   - 统一设计规范文件名

3. **整理 SVG 文件**
   - 移动到 svg_output/ 目录
   - 统一文件命名

4. **生成预览文件**
   ```bash
   python3 tools/generate_preview.py <project_path>
   ```

5. **验证**
   ```bash
   python3 tools/project_manager.py validate <project_path>
   ```

## 常见问题

### Q: 项目名称可以使用中文吗？

A: 可以，但建议使用英文或拼音，以避免跨平台兼容性问题。

### Q: 必须使用指定的文件名吗？

A: 核心文件（README.md、svg_output/）必须使用标准名称。设计规范文件可以使用几个备选名称之一。

### Q: 可以添加额外的文件和目录吗？

A: 可以，但建议遵循以下原则：
- 不要在根目录添加过多文件
- 使用有意义的目录名
- 在 README.md 中说明额外文件的用途

### Q: preview.html 可以手动编辑吗？

A: 不建议。应该修改模板或配置，然后重新生成。

### Q: 如何处理大型项目？

A: 对于超过 20 页的项目，可以考虑：
- 使用子目录组织 SVG（但保持 svg_output/ 作为主目录）
- 在设计规范中使用更详细的分组
- 创建多个预览页面（按章节）

## 相关文档

- [快速开始](../README.md)
- [工作流详解](workflow_tutorial.md)
- [设计规范](design_guidelines.md)
- [画布格式](canvas_formats.md)
- [工具说明](../tools/README.md)

---

*最后更新: 2025-11-16*

