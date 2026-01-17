#!/usr/bin/env python3
"""
PPT Master - 项目管理工具

提供项目初始化、验证等功能。

用法:
    python3 tools/project_manager.py init <project_name> [--format ppt169|ppt43|wechat|...]
    python3 tools/project_manager.py validate <project_path>
    python3 tools/project_manager.py info <project_path>
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 导入公共工具模块（必须成功）
try:
    from project_utils import (
        CANVAS_FORMATS,
        get_project_info,
        validate_project_structure,
        validate_svg_viewbox
    )
except ImportError:
    # 如果直接运行，尝试从当前目录导入
    import os
    import sys
    # 将 tools 目录添加到路径
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        from project_utils import (
            CANVAS_FORMATS,
            get_project_info,
            validate_project_structure,
            validate_svg_viewbox
        )
    except ImportError as e:
        print(f"错误: 无法导入 project_utils 模块")
        print(f"请确保在 tools/ 目录下运行，或将 tools/ 添加到 PYTHONPATH")
        print(f"详细信息: {e}")
        sys.exit(1)


class ProjectManager:
    """项目管理器"""

    # 使用公共模块的画布格式定义（统一来源）
    CANVAS_FORMATS = CANVAS_FORMATS

    def __init__(self, base_dir: str = 'projects'):
        """初始化项目管理器

        Args:
            base_dir: 项目基础目录，默认为 projects
        """
        self.base_dir = Path(base_dir)

    def init_project(self, project_name: str, canvas_format: str = 'ppt169',
                     design_style: str = '通用灵活', base_dir: Optional[str] = None) -> str:
        """初始化新项目

        Args:
            project_name: 项目名称
            canvas_format: 画布格式 (ppt169, ppt43, wechat, 等)
            design_style: 设计风格 (通用灵活, 一般咨询, 顶级咨询)
            base_dir: 项目基础目录，默认使用实例的 base_dir

        Returns:
            创建的项目路径
        """
        if base_dir:
            base_path = Path(base_dir)
        else:
            base_path = self.base_dir

        # 创建项目目录名: {project_name}_{format}_{YYYYMMDD}
        date_str = datetime.now().strftime('%Y%m%d')
        project_dir_name = f"{project_name}_{canvas_format}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"项目目录已存在: {project_path}")

        # 创建目录结构
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / 'svg_output').mkdir(exist_ok=True)   # 原始版本（带占位符）
        (project_path / 'svg_final').mkdir(exist_ok=True)    # 最终版本（后处理完成）
        (project_path / 'images').mkdir(exist_ok=True)       # 图片资源
        (project_path / 'notes').mkdir(exist_ok=True)        # 演讲备注

        # 获取画布格式信息
        canvas_info = self.CANVAS_FORMATS.get(
            canvas_format, self.CANVAS_FORMATS['ppt169'])

        # 创建设计规范与内容大纲
        spec_content = f"""# {project_name} - 设计规范与内容大纲

## 一、项目信息

| 项目 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **画布格式** | {canvas_info['name']} ({canvas_info['dimensions']}) |
| **页数** | [待定] |
| **设计风格** | {design_style} |
| **目标受众** | [待填写] |
| **使用场景** | [待填写] |
| **创建日期** | {datetime.now().strftime('%Y-%m-%d')} |

---

## 二、画布规范

| 属性 | 值 |
|------|-----|
| **格式** | {canvas_info['name']} |
| **尺寸** | {canvas_info['dimensions']} |
| **viewBox** | `{canvas_info['viewbox']}` |
| **边距** | 左右 60px，上下 50px |
| **内容区域** | [根据画布计算] |

---

## 三、视觉主题

### 主题风格
- **风格**: {design_style}
- **主题**: [亮色主题 / 深色主题]
- **调性**: [待填写，如：科技、专业、现代、创新]

### 配色方案

| 角色 | 色值 | 用途 |
|------|------|------|
| **背景色** | `#FFFFFF` | 页面背景 |
| **次背景** | `#F8FAFC` | 卡片背景、区块背景 |
| **主导色** | `#[待定]` | 标题装饰、重点区块、图标 |
| **强调色** | `#[待定]` | 数据高亮、关键信息、链接 |
| **辅助强调** | `#[待定]` | 次要强调、渐变过渡 |
| **正文文字** | `#1F2937` | 主要正文 |
| **次要文字** | `#6B7280` | 说明文字、标注 |
| **弱文字** | `#9CA3AF` | 辅助信息、页脚 |
| **边框/分割** | `#E5E7EB` | 卡片边框、分割线 |
| **成功色** | `#10B981` | 正向指标 |
| **警示色** | `#EF4444` | 问题标注 |

### 渐变方案（如需要）

```
主标题渐变: linear-gradient(135deg, #[主导色], #[辅助强调])
强调渐变: linear-gradient(90deg, #[强调色], #[主导色])
背景装饰: radial-gradient(circle at 80% 20%, rgba(主导色, 0.15), transparent 50%)
```

---

## 四、排版体系

### 字体方案

> 推荐预设说明：P1=现代商务科技 | P2=政务公文 | P3=文化艺术 | P4=传统稳重 | P5=英文为主

| 角色 | 中文 | 英文 | 备选 |
|------|------|------|------|
| **标题** | 微软雅黑 | Arial | Helvetica |
| **正文** | 微软雅黑 | Calibri | Arial |
| **代码** | - | Consolas | Monaco |
| **强调** | 黑体 | Arial Black | Impact |

**字体栈**: `"PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif`

### 字号层级

> **px ↔ pt 转换**: 1 pt = 1.333 px | 1 px = 0.75 pt（96 DPI 标准）

| 层级 | px | pt | 字重 | 用途 |
|------|-----|-----|------|------|
| H1 | 48px | 36pt | Bold | 封面标题 |
| H2 | 36px | 27pt | Bold | 页面主标题 |
| H3 | 28px | 21pt | SemiBold | 章节标题 |
| H4 | 22px | 16.5pt | Medium | 卡片标题 |
| Body | 18px | 13.5pt | Regular | 正文内容 |
| Caption | 14px | 10.5pt | Regular | 说明、标注 |
| Code | 16px | 12pt | Regular | 代码片段 |

---

## 五、布局原则

### 页面结构
- **页眉区**: 顶部 50px，放置页码和章节标识
- **内容区**: 中部主要内容区域
- **页脚区**: 底部 50px，放置项目名称或装饰

### 常用布局模式

| 模式 | 适用场景 |
|------|----------|
| **单栏居中** | 封面、结语、重要观点 |
| **左右分栏 (5:5)** | 对比、双概念 |
| **左右分栏 (4:6)** | 图文混排 |
| **上下分栏** | 流程、时间线 |
| **三栏/四栏卡片** | 特性列表、角色介绍 |
| **矩阵网格** | 对比分析、分类展示 |

### 间距规范

| 元素 | 间距 |
|------|------|
| 卡片间距 | 24px |
| 内容块间距 | 32px |
| 卡片内边距 | 24px |
| 卡片圆角 | 12px |
| 图标与文字 | 12px |

---

## 六、图标使用规范

### 来源
- **内置图标库**: `templates/icons/` (640+ 图标)
- **使用方式**: 占位符格式 `{{{{icon:类别/图标名}}}}`

### 推荐图标清单（按需填写）

| 用途 | 图标路径 | 页面 |
|------|----------|------|
| [示例] | `{{{{icon:interface/check-circle}}}}` | Slide XX |

---

## 七、图片资源清单（如需要）

| 文件名 | 尺寸 | 比例 | 用途 | 状态 | 生成描述 |
|--------|------|------|------|------|----------|
| cover_bg.png | {canvas_info['dimensions']} | [比例] | 封面背景 | [待生成/已有/占位符] | [AI生成提示词] |

**状态说明**:
- **待生成** - 需要 AI 生成，提供详细描述
- **已有** - 用户已有图片，直接放入 `images/`
- **占位符** - 暂不处理，SVG 中用虚线框占位

---

## 八、内容大纲

### 第一部分：[章节名称]

#### Slide 01 - 封面
- **布局**: 全屏背景图 + 居中标题
- **标题**: [主标题]
- **副标题**: [副标题]
- **信息**: [作者/日期/单位]

#### Slide 02 - [页面名称]
- **布局**: [选择布局模式]
- **标题**: [页面标题]
- **内容**:
  - [要点1]
  - [要点2]
  - [要点3]

---

[继续添加更多页面...]

---

## 九、演讲备注要求

每页生成对应的演讲备注文件，保存到 `notes/` 目录：
- **文件命名**: 与 SVG 同名，如 `01_封面.md`
- **内容包含**: 讲稿要点、时间提示、过渡语

---

## 十、技术约束提醒

### SVG 生成必须遵守：
1. viewBox: `{canvas_info['viewbox']}`
2. 背景使用 `<rect>` 元素
3. 文本换行使用 `<tspan>`
4. 透明度使用 `fill-opacity` / `stroke-opacity`，禁止 rgba()
5. 禁止使用：clipPath、mask、filter、style、class、foreignObject

### PPT 兼容性规则：
- 禁止组透明度 `<g opacity="...">`
- 图片透明度使用遮罩层替代
- 仅使用内联样式

---

## 十一、设计检查清单

### 生成前
- [ ] 内容符合页面容量
- [ ] 布局模式选择正确
- [ ] 颜色使用符合语义

### 生成后
- [ ] viewBox = `{canvas_info['viewbox']}`
- [ ] 无 `<foreignObject>` 元素
- [ ] 所有文本可读（≥14px）
- [ ] 内容在安全区域内
- [ ] 所有元素对齐到网格
- [ ] 相同元素保持一致样式
- [ ] 颜色符合规范
- [ ] CRAP 四原则检查通过

---

## 十二、下一步

1. ✅ 设计规范已完成
2. **下一步**: [根据图片方式选择]
   - 无 AI 图片 → 调用 **Executor** 角色生成 SVG
   - 有 AI 图片 → 调用 **Image_Generator** 角色，完成后再调用 Executor

---

*最后更新: {datetime.now().strftime('%Y-%m-%d')}*
"""

        with open(project_path / '设计规范与内容大纲.md', 'w', encoding='utf-8') as f:
            f.write(spec_content)

        return str(project_path)

    def validate_project(self, project_path: str) -> Tuple[bool, List[str], List[str]]:
        """验证项目完整性

        Args:
            project_path: 项目目录路径

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        project_path = Path(project_path)
        errors = []
        warnings = []

        # 检查目录是否存在
        if not project_path.exists():
            errors.append(f"项目目录不存在: {project_path}")
            return False, errors, warnings

        if not project_path.is_dir():
            errors.append(f"不是有效的目录: {project_path}")
            return False, errors, warnings

        # 检查设计规范文件（核心必需文件）
        spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
        has_spec = any((project_path / f).exists() for f in spec_files)
        if not has_spec:
            errors.append("缺少设计规范文件（建议文件名: 设计规范与内容大纲.md）")

        # 检查 svg_output 目录
        svg_output = project_path / 'svg_output'
        if not svg_output.exists():
            errors.append("缺少 svg_output 目录")
        else:
            # 检查 SVG 文件
            svg_files = list(svg_output.glob('*.svg'))
            if len(svg_files) == 0:
                warnings.append("svg_output 目录为空")
            else:
                # 验证 SVG 文件命名
                for svg_file in svg_files:
                    if not re.match(r'^slide_\d+_\w+\.svg$', svg_file.name):
                        warnings.append(
                            f"SVG 文件命名不规范: {svg_file.name} (建议: slide_XX_name.svg)")

                # 检查 viewBox
                self._validate_svg_viewbox(svg_files, warnings)

        # 检查项目命名格式
        dir_name = project_path.name
        if not re.match(r'^.+_(ppt169|ppt43|wechat|xiaohongshu|story|moments|banner|a4)_\d{8}$', dir_name, re.IGNORECASE):
            warnings.append(
                f"项目目录命名不规范: {dir_name} (建议: name_format_YYYYMMDD)")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def _validate_svg_viewbox(self, svg_files: List[Path], warnings: List[str]):
        """验证 SVG 文件的 viewBox 设置

        Args:
            svg_files: SVG 文件列表
            warnings: 警告列表（会被修改）
        """
        viewbox_pattern = re.compile(r'viewBox="([^"]+)"')
        viewboxes = set()

        for svg_file in svg_files[:5]:  # 只检查前5个文件
            try:
                with open(svg_file, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 只读取前1000字符
                    match = viewbox_pattern.search(content)
                    if match:
                        viewboxes.add(match.group(1))
                    else:
                        warnings.append(f"{svg_file.name}: 未找到 viewBox 属性")
            except Exception as e:
                warnings.append(f"{svg_file.name}: 读取失败 - {e}")

        if len(viewboxes) > 1:
            warnings.append(f"检测到多个不同的 viewBox 设置: {viewboxes}")

    def get_project_info(self, project_path: str) -> Dict:
        """获取项目信息

        Args:
            project_path: 项目目录路径

        Returns:
            项目信息字典
        """
        project_path = Path(project_path)
        info = {
            'name': project_path.name,
            'path': str(project_path),
            'exists': project_path.exists(),
            'svg_count': 0,
            'has_spec': False,
            'canvas_format': 'unknown',
            'create_date': 'unknown'
        }

        if not project_path.exists():
            return info

        # 统计 SVG 文件
        svg_output = project_path / 'svg_output'
        if svg_output.exists():
            info['svg_count'] = len(list(svg_output.glob('*.svg')))

        # 检查设计规范
        spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
        info['has_spec'] = any((project_path / f).exists() for f in spec_files)

        # 从目录名提取信息
        dir_name = project_path.name

        # 提取画布格式
        for fmt in self.CANVAS_FORMATS.keys():
            if fmt in dir_name.lower():
                info['canvas_format'] = self.CANVAS_FORMATS[fmt]['name']
                break

        # 提取日期
        date_match = re.search(r'_(\d{8})$', dir_name)
        if date_match:
            date_str = date_match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                info['create_date'] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass

        return info


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    manager = ProjectManager()

    if command == 'init':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目名称")
            print(
                "用法: python3 tools/project_manager.py init <project_name> [--format ppt169]")
            sys.exit(1)

        project_name = sys.argv[2]
        canvas_format = 'ppt169'
        base_dir = 'projects'

        # 解析可选参数
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--format' and i + 1 < len(sys.argv):
                canvas_format = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--dir' and i + 1 < len(sys.argv):
                base_dir = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        try:
            project_path = manager.init_project(
                project_name, canvas_format, base_dir=base_dir)
            print(f"[OK] 项目已创建: {project_path}")
            print("\n下一步:")
            print("1. 编辑 设计规范与内容大纲.md")
            print("2. 将 SVG 文件放入 svg_output/ 目录")
        except Exception as e:
            print(f"[ERROR] 创建失败: {e}")
            sys.exit(1)

    elif command == 'validate':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目路径")
            print("用法: python3 tools/project_manager.py validate <project_path>")
            sys.exit(1)

        project_path = sys.argv[2]
        is_valid, errors, warnings = manager.validate_project(project_path)

        print(f"\n项目验证: {project_path}")
        print("=" * 60)

        if errors:
            print("\n[ERROR] 错误:")
            for error in errors:
                print(f"  - {error}")

        if warnings:
            print("\n[WARN] 警告:")
            for warning in warnings:
                print(f"  - {warning}")

        if is_valid and not warnings:
            print("\n[OK] 项目结构完整，没有问题")
        elif is_valid:
            print("\n[OK] 项目结构有效，但有一些建议")
        else:
            print("\n[ERROR] 项目结构无效，请修复错误")
            sys.exit(1)

    elif command == 'info':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目路径")
            print("用法: python3 tools/project_manager.py info <project_path>")
            sys.exit(1)

        project_path = sys.argv[2]
        info = manager.get_project_info(project_path)

        print(f"\n项目信息: {info['name']}")
        print("=" * 60)
        print(f"路径: {info['path']}")
        print(f"存在: {'是' if info['exists'] else '否'}")
        print(f"SVG 文件数: {info['svg_count']}")
        print(f"设计规范: {'存在' if info['has_spec'] else '缺失'}")
        print(f"画布格式: {info['canvas_format']}")
        print(f"创建日期: {info['create_date']}")

    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
