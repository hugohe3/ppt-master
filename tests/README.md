# PPT Master 测试套件

本目录包含项目的自动化测试用例，使用 pytest 框架。

## 快速开始

### 安装依赖

```bash
pip install pytest pytest-cov
```

### 运行所有测试

```bash
# 在项目根目录执行
pytest tests/

# 显示详细输出
pytest tests/ -v

# 显示更详细的输出（包括 print 语句）
pytest tests/ -v -s
```

### 运行特定测试

```bash
# 运行单个测试文件
pytest tests/test_project_utils.py

# 运行特定测试类
pytest tests/test_project_utils.py::TestCanvasFormats

# 运行特定测试方法
pytest tests/test_project_utils.py::TestCanvasFormats::test_ppt169_format

# 使用关键字过滤
pytest tests/ -k "viewbox"
```

### 跳过慢速测试

```bash
# 跳过标记为 slow 的测试
pytest tests/ -m "not slow"

# 只运行集成测试
pytest tests/ -m "integration"
```

### 生成覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/ --cov=tools --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest 配置和公共 fixtures
├── test_project_utils.py    # project_utils 模块测试
├── test_svg_quality_checker.py  # SVG 质量检查器测试
└── README.md                # 本文件
```

## 测试分类

### 单元测试

测试单个函数或方法的功能：

- `TestCanvasFormats` - 画布格式定义测试
- `TestParseProjectName` - 项目名解析测试
- `TestViewBoxCheck` - viewBox 检查测试
- `TestFontCheck` - 字体检查测试

### 集成测试

测试多个组件协同工作：

- `TestIntegration` - 使用实际示例项目进行测试

集成测试使用 `@pytest.mark.integration` 标记。

### 慢速测试

需要较长时间运行的测试使用 `@pytest.mark.slow` 标记。

## Fixtures 说明

### 路径相关

| Fixture | 说明 |
|---------|------|
| `project_root` | 项目根目录 |
| `tools_dir` | tools 目录 |
| `examples_dir` | examples 目录 |
| `templates_dir` | templates 目录 |

### 临时文件

| Fixture | 说明 |
|---------|------|
| `temp_dir` | 临时目录（自动清理）|
| `temp_project` | 临时项目目录（含基本结构）|
| `temp_svg_file` | 临时有效 SVG 文件 |
| `temp_invalid_svg_file` | 临时无效 SVG 文件 |

### 模块导入

| Fixture | 说明 |
|---------|------|
| `project_utils` | project_utils 模块 |
| `svg_quality_checker` | svg_quality_checker 模块 |
| `canvas_formats` | 画布格式定义字典 |

### 示例数据

| Fixture | 说明 |
|---------|------|
| `sample_svg_content` | 有效的 SVG 内容字符串 |
| `invalid_svg_content` | 包含问题的 SVG 内容 |
| `example_project` | 实际存在的示例项目路径 |

## 编写新测试

### 基本模板

```python
import pytest

class TestMyFeature:
    """功能测试类"""
    
    def test_basic_case(self, some_fixture):
        """测试基本情况"""
        result = some_function(some_fixture)
        assert result == expected_value
    
    def test_edge_case(self, some_fixture):
        """测试边界情况"""
        with pytest.raises(SomeException):
            some_function(invalid_input)
    
    @pytest.mark.slow
    def test_slow_operation(self, some_fixture):
        """慢速测试"""
        # 耗时操作
        pass
```

### 使用临时文件

```python
def test_with_temp_file(self, temp_dir):
    """使用临时文件测试"""
    test_file = temp_dir / 'test.txt'
    test_file.write_text('content')
    
    result = process_file(str(test_file))
    assert result == expected
    # temp_dir 会在测试结束后自动清理
```

### 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ('ppt169', '1280×720'),
    ('ppt43', '1024×768'),
    ('xiaohongshu', '1242×1660'),
])
def test_dimensions(self, canvas_formats, input, expected):
    """参数化测试"""
    assert canvas_formats[input]['dimensions'] == expected
```

## 常见问题

### Q: 测试找不到模块？

确保在项目根目录运行测试：

```bash
cd /path/to/ppt-master
pytest tests/
```

### Q: 如何调试测试？

使用 `-s` 参数显示 print 输出：

```bash
pytest tests/ -v -s
```

或在测试中设置断点：

```python
def test_debug(self):
    import pdb; pdb.set_trace()  # 设置断点
    # 或使用
    breakpoint()
```

### Q: 如何只运行失败的测试？

```bash
# 只运行上次失败的测试
pytest tests/ --lf

# 先运行失败的测试
pytest tests/ --ff
```

## 贡献指南

1. 新功能应有对应的测试用例
2. 测试应覆盖正常情况和边界情况
3. 使用有意义的测试名称
4. 保持测试独立，不依赖执行顺序
5. 慢速测试需添加 `@pytest.mark.slow` 标记

---

**维护者**: PPT Master Team  
**最后更新**: 2025-12-06

