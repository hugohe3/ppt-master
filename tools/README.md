# PPT Master 工具集

本目录包含用于项目管理、验证和文件处理的实用工具。

## 工具列表

### 1. project_utils.py — 项目工具公共模块

提供项目信息解析、验证等公共功能，供其他工具复用。

**功能**:

- 画布格式定义和管理
- 项目信息解析（从目录名提取格式、日期等）
- 项目结构验证
- SVG viewBox 验证
- 项目查找和统计

**用法**:

```bash
# 作为模块被其他工具导入
from project_utils import get_project_info, validate_project_structure

# 也可以直接运行测试
python3 tools/project_utils.py <project_path>
```

---

### 2. project_manager.py — 项目管理工具

项目初始化、验证和管理的一站式工具。

**功能**:

- 初始化新项目（创建标准目录结构）
- 验证项目完整性
- 查看项目信息

**用法**:

```bash
# 初始化新项目
python3 tools/project_manager.py init <project_name> --format ppt169

# 验证项目结构
python3 tools/project_manager.py validate <project_path>

# 查看项目信息
python3 tools/project_manager.py info <project_path>
```

**支持的画布格式**:

- `ppt169` - PPT 16:9 (1280×720)
- `ppt43` - PPT 4:3 (1024×768)
- `wechat` - 微信公众号头图 (900×383)
- `xiaohongshu` - 小红书 3:4 (1242×1660)
- `moments` - 朋友圈/Instagram 1:1 (1080×1080)
- `story` - Story/竖版 9:16 (1080×1920)
- `banner` - 横版 Banner 16:9 (1920×1080)
- `a4` - A4 打印 (1240×1754)

**示例**:

```bash
# 创建一个新的 PPT 16:9 项目
python3 tools/project_manager.py init my_presentation --format ppt169

# 验证项目
python3 tools/project_manager.py validate projects/my_presentation_ppt169_20251116

# 查看项目信息
python3 tools/project_manager.py info projects/my_presentation_ppt169_20251116
```

---

### 3. flatten_tspan.py — 文本扁平化（去 `<tspan>`）

将含有多行 `<tspan>` 的 `<text>` 结构扁平化为多条独立的 `<text>` 元素，便于部分渲染器兼容或文本抽取。

**注意**: 生成端仍应使用 `<tspan>` 手动换行（禁止 `<foreignObject>`）。此工具仅用于后处理。

**用法**:

```bash
# 交互模式
python3 tools/flatten_tspan.py
python3 tools/flatten_tspan.py -i

# 扁平化整个输出目录（默认输出到同级 svg_output_flattext）
python3 tools/flatten_tspan.py examples/<project_name>_<format>_<YYYYMMDD>/svg_output

# 指定输出目录
python3 tools/flatten_tspan.py examples/<project>/svg_output examples/<project>/svg_output_flattext

# 处理单个 SVG（自定义输出路径）
python3 tools/flatten_tspan.py path/to/input.svg path/to/output.svg
```

**行为说明**:

- 逐个 `<tspan>` 计算绝对位置（综合 `x`/`y` 与 `dx`/`dy`），合并父/子样式，输出为独立 `<text>`
- 复制父 `<text>` 的通用文本属性和 `style`，子级覆盖优先
- 保留或合并 `transform`
- 输出采用 UTF-8 编码，无 XML 声明，保持与仓库示例风格一致

**建议校验**:

- 目标目录为 `svg_output_flattext`，不应含 `<tspan>`
- 抽检字号、字重、颜色、对齐和坐标是否与原文件一致
- 若发现偏差，优先在生成端修正 `<tspan>` 的 `x`/`dy` 或父 `<text>` 的样式后重跑

**已知限制**:

- 仅处理 `<text>`/`<tspan>` 结构；其他子元素不做转换
- 复杂嵌套或特殊布局请先在生成端简化为规范的逐行 `<tspan>`

---

### 4. batch_validate.py — 批量项目验证工具

一次性检查多个项目的结构完整性和规范性。

**功能**:

- 批量验证项目结构
- 检查必需文件（README、设计规范、SVG 等）
- 验证 SVG viewBox 设置
- 生成验证报告
- 提供修复建议

**用法**:

```bash
# 验证单个目录
python3 tools/batch_validate.py examples

# 验证多个目录
python3 tools/batch_validate.py examples projects

# 验证所有
python3 tools/batch_validate.py --all

# 导出报告
python3 tools/batch_validate.py examples --export
```

**示例输出**:

```
✅ google_annual_report_ppt169_20251116
   路径: examples/google_annual_report_ppt169_20251116
   格式: PPT 16:9 | SVG: 10 个 | 日期: 2025-11-16

⚠️  某项目名称
   路径: examples/某项目名称
   格式: PPT 16:9 | SVG: 8 个 | 日期: 2025-10-15
   ⚠️  警告 (1):
      - SVG 文件命名不规范: old_name.svg
```

---

### 5. generate_examples_index.py — Examples 索引生成工具

自动扫描 examples 目录并生成 README.md 索引文件。

**功能**:

- 自动发现所有示例项目
- 按格式分类整理
- 生成统计信息
- 创建预览链接
- 更新使用说明

**用法**:

```bash
# 生成 examples/README.md
python3 tools/generate_examples_index.py

# 指定目录
python3 tools/generate_examples_index.py examples
```

**特性**:

- 自动检测项目信息（名称、格式、日期、SVG 数量）
- 按画布格式分组
- 显示最近更新的项目
- 包含使用说明和贡献指南

---

### 6. error_helper.py — 错误消息助手

提供友好的错误消息和具体的修复建议。

**功能**:

- 标准化错误类型定义
- 提供具体的解决方案
- 支持上下文定制
- 格式化输出

**用法**:

```bash
# 查看所有错误类型
python3 tools/error_helper.py

# 查看特定错误的解决方案
python3 tools/error_helper.py missing_readme

# 带上下文
python3 tools/error_helper.py missing_readme project_path=my_project
```

**支持的错误类型**:

- `missing_readme` - 缺少 README.md
- `missing_spec` - 缺少设计规范
- `missing_svg_output` - 缺少 svg_output 目录
- `viewbox_mismatch` - viewBox 不匹配
- `foreignobject_detected` - 检测到禁用元素
- 等等...

---

### 7. svg_quality_checker.py — SVG 质量检查工具

检查 SVG 文件是否符合项目技术规范。

**功能**:

- 验证 viewBox 属性
- 检测禁用元素（foreignObject）
- 检查字体使用
- 验证 width/height 与 viewBox 一致性
- 检查文本换行方式
- 分析文件大小

**用法**:

```bash
# 检查单个文件
python3 tools/svg_quality_checker.py examples/project/svg_output/slide_01.svg

# 检查整个目录
python3 tools/svg_quality_checker.py examples/project/svg_output

# 检查项目（自动查找 svg_output）
python3 tools/svg_quality_checker.py examples/project

# 指定期望格式
python3 tools/svg_quality_checker.py examples/project --format ppt169

# 检查所有项目
python3 tools/svg_quality_checker.py --all examples

# 导出报告
python3 tools/svg_quality_checker.py examples/project --export
```

**检查项目**:

- ✅ viewBox 属性存在且格式正确
- ✅ 无 `<foreignObject>` 元素
- ✅ 使用系统 UI 字体栈
- ✅ width/height 与 viewBox 一致
- ✅ 文本使用 `<tspan>` 换行
- ✅ 文件大小合理（< 500KB）

---

## 工作流集成

### 典型工作流程

1. **创建新项目**

   ```bash
   python3 tools/project_manager.py init my_project --format ppt169
   ```

2. **编辑设计规范**
   编辑生成的 `设计规范与内容大纲.md` 文件

3. **生成 SVG 文件**
   使用 AI 角色（Strategist → Executor → Optimizer）生成 SVG 并保存到 `svg_output/`

4. **质量检查**

   ```bash
   # 检查 SVG 质量
   python3 tools/svg_quality_checker.py projects/my_project_ppt169_20251116
   ```

5. **验证项目**

   ```bash
   python3 tools/project_manager.py validate projects/my_project_ppt169_20251116
   ```

6. **（可选）扁平化文本**

   ```bash
   python3 tools/flatten_tspan.py projects/my_project_ppt169_20251116/svg_output
   ```

7. **更新索引**（如果是 examples 目录）
   ```bash
   python3 tools/generate_examples_index.py
   ```

### 批量操作

**批量验证项目**:

```bash
# 验证所有示例项目
python3 tools/batch_validate.py examples

# 验证并导出报告
python3 tools/batch_validate.py examples --export
```

**批量检查 SVG 质量**:

```bash
# 检查所有示例项目的 SVG
python3 tools/svg_quality_checker.py --all examples

# 导出质量报告
python3 tools/svg_quality_checker.py --all examples --export
```

## 依赖要求

所有工具均使用 Python 3 标准库，无需额外依赖。

**最低 Python 版本**: Python 3.6+

## 故障排除

### 问题：项目验证失败

**解决方案**:

1. 运行 `python3 tools/project_manager.py validate <path>` 查看详细错误
2. 根据错误提示修复缺失的文件或目录
3. 参考 `projects/README.md` 了解标准结构

### 问题：SVG 预览显示不正常

**解决方案**:

1. 确保 SVG 文件路径正确
2. 检查 SVG 文件命名是否符合规范（`slide_XX_name.svg`）
3. 使用本地服务器预览：`python3 -m http.server --directory <svg_output_path> 8000`

## 相关文档

- [工作流教程](../docs/workflow_tutorial.md)
- [快速参考](../docs/quick_reference.md)
- [AGENTS 指南](../AGENTS.md)

---

_最后更新: 2025-11-16_
