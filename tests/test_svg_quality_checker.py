"""
svg_quality_checker 模块测试

测试 SVG 质量检查功能。
"""

import pytest
from pathlib import Path


class TestSVGQualityChecker:
    """SVG 质量检查器测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        """创建检查器实例"""
        return svg_quality_checker.SVGQualityChecker()
    
    def test_checker_initialization(self, checker):
        """测试检查器初始化"""
        assert checker.results == []
        assert checker.summary['total'] == 0
        assert checker.summary['passed'] == 0
        assert checker.summary['warnings'] == 0
        assert checker.summary['errors'] == 0
    
    def test_check_valid_svg(self, checker, temp_svg_file):
        """测试检查有效的 SVG 文件"""
        result = checker.check_file(str(temp_svg_file), 'ppt169')
        
        assert result['exists'] == True
        assert result['passed'] == True
        assert len(result['errors']) == 0
    
    def test_check_nonexistent_file(self, checker, temp_dir):
        """测试检查不存在的文件"""
        fake_path = temp_dir / 'nonexistent.svg'
        result = checker.check_file(str(fake_path))
        
        assert result['exists'] == False
        assert result['passed'] == False
        assert len(result['errors']) > 0
    
    def test_check_detects_foreign_object(self, checker, temp_invalid_svg_file):
        """测试检测 foreignObject 元素"""
        result = checker.check_file(str(temp_invalid_svg_file))
        
        assert result['passed'] == False
        assert any('foreignObject' in error for error in result['errors'])
    
    def test_check_detects_viewbox_mismatch(self, checker, temp_invalid_svg_file):
        """测试检测 viewBox 不匹配"""
        result = checker.check_file(str(temp_invalid_svg_file), 'ppt169')
        
        # viewBox 是 1920x1080，期望 ppt169 (1280x720)
        assert any('viewBox' in error or 'viewbox' in error.lower() for error in result['errors'])
    
    def test_summary_updates(self, checker, temp_svg_file, temp_invalid_svg_file):
        """测试摘要统计更新"""
        checker.check_file(str(temp_svg_file), 'ppt169')
        checker.check_file(str(temp_invalid_svg_file))
        
        assert checker.summary['total'] == 2
        assert checker.summary['passed'] + checker.summary['warnings'] + checker.summary['errors'] == 2


class TestViewBoxCheck:
    """viewBox 检查测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        return svg_quality_checker.SVGQualityChecker()
    
    def test_missing_viewbox(self, checker, temp_dir):
        """测试缺少 viewBox"""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><rect fill="red"/></svg>'
        svg_path = temp_dir / 'no_viewbox.svg'
        svg_path.write_text(svg_content)
        
        result = checker.check_file(str(svg_path))
        
        assert result['passed'] == False
        assert any('viewBox' in error for error in result['errors'])
    
    def test_viewbox_info_extracted(self, checker, temp_svg_file):
        """测试 viewBox 信息被提取"""
        result = checker.check_file(str(temp_svg_file))
        
        assert 'viewbox' in result['info']
        assert result['info']['viewbox'] == '0 0 1280 720'


class TestFontCheck:
    """字体检查测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        return svg_quality_checker.SVGQualityChecker()
    
    def test_system_font_ok(self, checker, temp_svg_file):
        """测试系统字体不产生警告"""
        result = checker.check_file(str(temp_svg_file))
        
        # 使用系统 UI 字体栈不应产生字体警告
        font_warnings = [w for w in result['warnings'] if '字体' in w or 'font' in w.lower()]
        assert len(font_warnings) == 0
    
    def test_custom_font_warning(self, checker, temp_dir):
        """测试自定义字体产生警告"""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
            <text font-family="Comic Sans MS" x="100" y="100">Test</text>
        </svg>'''
        svg_path = temp_dir / 'custom_font.svg'
        svg_path.write_text(svg_content)
        
        result = checker.check_file(str(svg_path))
        
        # 使用非系统字体应产生警告
        font_warnings = [w for w in result['warnings'] if '字体' in w or 'font' in w.lower()]
        assert len(font_warnings) > 0


class TestFileSizeCheck:
    """文件大小检查测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        return svg_quality_checker.SVGQualityChecker()
    
    def test_file_size_info(self, checker, temp_svg_file):
        """测试文件大小信息被提取"""
        result = checker.check_file(str(temp_svg_file))
        
        assert 'file_size' in result['info']
        assert 'KB' in result['info']['file_size']
    
    def test_large_file_warning(self, checker, temp_dir):
        """测试大文件产生警告"""
        # 创建一个大文件 (> 500KB)
        large_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">'
        large_content += '<rect width="100" height="100" fill="red"/>' * 50000  # 大量重复内容
        large_content += '</svg>'
        
        large_svg = temp_dir / 'large.svg'
        large_svg.write_text(large_content)
        
        result = checker.check_file(str(large_svg))
        
        # 检查是否有大小相关警告
        size_warnings = [w for w in result['warnings'] if '大' in w or 'size' in w.lower()]
        # 注意：如果文件不够大可能不会触发警告
        if large_svg.stat().st_size > 500 * 1024:
            assert len(size_warnings) > 0 or len(result['errors']) > 0


class TestDirectoryCheck:
    """目录检查测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        return svg_quality_checker.SVGQualityChecker()
    
    def test_check_directory(self, checker, temp_project, sample_svg_content):
        """测试检查目录"""
        svg_output = temp_project / 'svg_output'
        (svg_output / 'slide_01_cover.svg').write_text(sample_svg_content)
        (svg_output / 'slide_02_content.svg').write_text(sample_svg_content)
        
        results = checker.check_directory(str(temp_project))
        
        assert len(results) == 2
        assert all(r['passed'] for r in results)
    
    def test_check_empty_directory(self, checker, temp_dir, capsys):
        """测试检查空目录"""
        empty_dir = temp_dir / 'empty'
        empty_dir.mkdir()
        
        results = checker.check_directory(str(empty_dir))
        
        assert len(results) == 0


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def checker(self, svg_quality_checker):
        return svg_quality_checker.SVGQualityChecker()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_check_example_project(self, checker, example_project):
        """测试检查示例项目"""
        results = checker.check_directory(str(example_project))
        
        # 示例项目应该有一些 SVG 文件
        assert len(results) > 0
        
        # 大部分文件应该通过检查
        passed_count = sum(1 for r in results if r['passed'])
        pass_rate = passed_count / len(results)
        
        assert pass_rate >= 0.5, f"示例项目通过率过低: {pass_rate:.1%}"
    
    @pytest.mark.integration
    def test_check_chart_templates(self, checker, templates_dir):
        """测试检查图表模板"""
        charts_dir = templates_dir / 'charts'
        if not charts_dir.exists():
            pytest.skip("charts 目录不存在")
        
        svg_files = list(charts_dir.glob('*.svg'))
        if not svg_files:
            pytest.skip("没有找到图表模板")
        
        for svg_file in svg_files[:5]:  # 只检查前5个
            result = checker.check_file(str(svg_file), 'ppt169')
            
            # 模板应该通过基本检查
            assert result['exists'] == True
            # foreignObject 不应该出现在模板中
            assert not any('foreignObject' in error for error in result['errors']), \
                f"模板 {svg_file.name} 包含 foreignObject"

