"""
pytest 配置和公共 fixtures

本文件定义了测试用的公共 fixtures 和配置。
"""

import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# 将 tools 目录添加到 Python 路径
TOOLS_DIR = Path(__file__).parent.parent / 'tools'
sys.path.insert(0, str(TOOLS_DIR))


# ============================================================
# 路径相关 fixtures
# ============================================================

@pytest.fixture
def project_root():
    """返回项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def tools_dir(project_root):
    """返回 tools 目录"""
    return project_root / 'tools'


@pytest.fixture
def examples_dir(project_root):
    """返回 examples 目录"""
    return project_root / 'examples'


@pytest.fixture
def templates_dir(project_root):
    """返回 templates 目录"""
    return project_root / 'templates'


# ============================================================
# 临时文件/目录 fixtures
# ============================================================

@pytest.fixture
def temp_dir():
    """创建临时目录，测试结束后自动清理"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_project(temp_dir):
    """
    创建一个临时的项目目录结构
    
    返回包含基本结构的项目路径
    """
    project_path = temp_dir / 'test_project_ppt169_20251206'
    project_path.mkdir()
    
    # 创建 README.md
    (project_path / 'README.md').write_text('# Test Project\n\nThis is a test project.')
    
    # 创建 设计规范与内容大纲.md
    (project_path / '设计规范与内容大纲.md').write_text('# 设计规范\n\n## 配色方案\n')
    
    # 创建 svg_output 目录
    svg_output = project_path / 'svg_output'
    svg_output.mkdir()
    
    return project_path


@pytest.fixture
def sample_svg_content():
    """返回一个有效的 SVG 内容"""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
    <rect width="1280" height="720" fill="#FFFFFF"/>
    <text x="640" y="360" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" 
          font-size="48" font-weight="bold" fill="#2C3E50" text-anchor="middle">
        <tspan>测试标题</tspan>
    </text>
</svg>'''


@pytest.fixture
def invalid_svg_content():
    """返回一个包含问题的 SVG 内容"""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
    <rect width="1920" height="1080" fill="#FFFFFF"/>
    <foreignObject x="100" y="100" width="400" height="200">
        <div xmlns="http://www.w3.org/1999/xhtml">
            <p>This should not be used!</p>
        </div>
    </foreignObject>
</svg>'''


@pytest.fixture
def temp_svg_file(temp_dir, sample_svg_content):
    """创建一个临时的有效 SVG 文件"""
    svg_path = temp_dir / 'slide_01_test.svg'
    svg_path.write_text(sample_svg_content)
    return svg_path


@pytest.fixture
def temp_invalid_svg_file(temp_dir, invalid_svg_content):
    """创建一个临时的无效 SVG 文件"""
    svg_path = temp_dir / 'slide_02_invalid.svg'
    svg_path.write_text(invalid_svg_content)
    return svg_path


# ============================================================
# 模块导入 fixtures
# ============================================================

@pytest.fixture
def project_utils():
    """导入 project_utils 模块"""
    import project_utils
    return project_utils


@pytest.fixture
def svg_quality_checker():
    """导入 svg_quality_checker 模块"""
    import svg_quality_checker
    return svg_quality_checker


@pytest.fixture
def canvas_formats(project_utils):
    """返回画布格式定义"""
    return project_utils.CANVAS_FORMATS


# ============================================================
# 示例项目 fixtures
# ============================================================

@pytest.fixture
def example_project(examples_dir):
    """
    返回一个实际存在的示例项目路径
    
    优先选择文件较少的项目以加快测试速度
    """
    # 尝试找一个小项目
    small_projects = [
        'ppt169_数据型_甘孜经济分析',
        'wechat_手绘风格_学习方法伪勤奋陷阱',
        'ppt169_常规风_医疗器械注册调研报告'
    ]
    
    for project_name in small_projects:
        project_path = examples_dir / project_name
        if project_path.exists():
            return project_path
    
    # 如果都不存在，返回第一个找到的项目
    for item in examples_dir.iterdir():
        if item.is_dir() and (item / 'svg_output').exists():
            return item
    
    pytest.skip("没有找到可用的示例项目")


# ============================================================
# pytest 配置
# ============================================================

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

