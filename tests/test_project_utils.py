"""
project_utils 模块测试

测试项目工具公共模块的功能。
"""

import pytest
from pathlib import Path


class TestCanvasFormats:
    """画布格式定义测试"""
    
    def test_canvas_formats_exist(self, canvas_formats):
        """测试画布格式定义存在"""
        assert canvas_formats is not None
        assert len(canvas_formats) > 0
    
    def test_ppt169_format(self, canvas_formats):
        """测试 PPT 16:9 格式定义"""
        assert 'ppt169' in canvas_formats
        ppt169 = canvas_formats['ppt169']
        
        assert ppt169['dimensions'] == '1280×720'
        assert ppt169['viewbox'] == '0 0 1280 720'
        assert ppt169['aspect_ratio'] == '16:9'
    
    def test_all_formats_have_required_fields(self, canvas_formats):
        """测试所有格式都有必需字段"""
        required_fields = ['name', 'dimensions', 'viewbox', 'aspect_ratio']
        
        for format_key, format_info in canvas_formats.items():
            for field in required_fields:
                assert field in format_info, f"格式 {format_key} 缺少字段 {field}"
    
    def test_viewbox_format_valid(self, canvas_formats):
        """测试 viewBox 格式有效"""
        import re
        viewbox_pattern = re.compile(r'^0 0 \d+ \d+$')
        
        for format_key, format_info in canvas_formats.items():
            viewbox = format_info['viewbox']
            assert viewbox_pattern.match(viewbox), \
                f"格式 {format_key} 的 viewBox '{viewbox}' 格式无效"


class TestParseProjectName:
    """项目名解析测试"""
    
    def test_parse_full_name(self, project_utils):
        """测试解析完整项目名"""
        result = project_utils.parse_project_name('test_project_ppt169_20251206')
        
        assert result['format'] == 'ppt169'
        assert result['date'] == '20251206'
        assert result['date_formatted'] == '2025-12-06'
    
    def test_parse_without_date(self, project_utils):
        """测试解析没有日期的项目名"""
        result = project_utils.parse_project_name('my_project_ppt169')
        
        assert result['format'] == 'ppt169'
        assert result['date'] == 'unknown'
    
    def test_parse_xiaohongshu_format(self, project_utils):
        """测试解析小红书格式"""
        result = project_utils.parse_project_name('content_xiaohongshu_20251201')
        
        assert result['format'] == 'xiaohongshu'
        assert result['format_name'] == '小红书'
    
    def test_parse_unknown_format(self, project_utils):
        """测试解析未知格式"""
        result = project_utils.parse_project_name('random_project')
        
        assert result['format'] == 'unknown'


class TestGetProjectInfo:
    """获取项目信息测试"""
    
    def test_get_info_for_nonexistent_project(self, project_utils, temp_dir):
        """测试获取不存在项目的信息"""
        fake_path = temp_dir / 'nonexistent_project'
        info = project_utils.get_project_info(str(fake_path))
        
        assert info['exists'] == False
        assert info['svg_count'] == 0
    
    def test_get_info_for_valid_project(self, project_utils, temp_project):
        """测试获取有效项目的信息"""
        info = project_utils.get_project_info(str(temp_project))
        
        assert info['exists'] == True
        assert info['has_readme'] == True
        assert info['has_spec'] == True
        assert info['format'] == 'ppt169'
    
    def test_get_info_counts_svg_files(self, project_utils, temp_project, sample_svg_content):
        """测试 SVG 文件计数"""
        svg_output = temp_project / 'svg_output'
        
        # 创建几个 SVG 文件
        (svg_output / 'slide_01_cover.svg').write_text(sample_svg_content)
        (svg_output / 'slide_02_content.svg').write_text(sample_svg_content)
        
        info = project_utils.get_project_info(str(temp_project))
        
        assert info['svg_count'] == 2
        assert 'slide_01_cover.svg' in info['svg_files']
        assert 'slide_02_content.svg' in info['svg_files']


class TestValidateProjectStructure:
    """项目结构验证测试"""
    
    def test_validate_valid_project(self, project_utils, temp_project, sample_svg_content):
        """测试验证有效项目"""
        # 添加 SVG 文件
        svg_output = temp_project / 'svg_output'
        (svg_output / 'slide_01_cover.svg').write_text(sample_svg_content)
        
        is_valid, errors, warnings = project_utils.validate_project_structure(str(temp_project))
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_missing_readme(self, project_utils, temp_project):
        """测试缺少 README 的项目"""
        (temp_project / 'README.md').unlink()
        
        is_valid, errors, warnings = project_utils.validate_project_structure(str(temp_project))
        
        assert is_valid == False
        assert any('README.md' in error for error in errors)
    
    def test_validate_missing_svg_output(self, project_utils, temp_dir):
        """测试缺少 svg_output 的项目"""
        project_path = temp_dir / 'incomplete_project'
        project_path.mkdir()
        (project_path / 'README.md').write_text('# Test')
        
        is_valid, errors, warnings = project_utils.validate_project_structure(str(project_path))
        
        assert is_valid == False
        assert any('svg_output' in error for error in errors)
    
    def test_validate_empty_svg_output(self, project_utils, temp_project):
        """测试空的 svg_output 目录"""
        is_valid, errors, warnings = project_utils.validate_project_structure(str(temp_project))
        
        # 空目录应该产生警告而非错误
        assert any('空' in warning for warning in warnings)


class TestValidateSvgViewbox:
    """SVG viewBox 验证测试"""
    
    def test_validate_correct_viewbox(self, project_utils, temp_dir, sample_svg_content):
        """测试正确的 viewBox"""
        svg_path = temp_dir / 'test.svg'
        svg_path.write_text(sample_svg_content)
        
        warnings = project_utils.validate_svg_viewbox([svg_path], 'ppt169')
        
        assert len(warnings) == 0
    
    def test_validate_wrong_viewbox(self, project_utils, temp_dir, invalid_svg_content):
        """测试错误的 viewBox"""
        svg_path = temp_dir / 'test.svg'
        svg_path.write_text(invalid_svg_content)
        
        warnings = project_utils.validate_svg_viewbox([svg_path], 'ppt169')
        
        # 应该检测到 viewBox 不匹配
        assert len(warnings) > 0
        assert any('viewBox' in w or 'viewbox' in w.lower() for w in warnings)


class TestFindAllProjects:
    """查找所有项目测试"""
    
    def test_find_projects_in_examples(self, project_utils, examples_dir):
        """测试在 examples 目录中查找项目"""
        if not examples_dir.exists():
            pytest.skip("examples 目录不存在")
        
        projects = project_utils.find_all_projects(str(examples_dir))
        
        assert len(projects) > 0
        assert all(isinstance(p, Path) for p in projects)
    
    def test_find_projects_in_empty_dir(self, project_utils, temp_dir):
        """测试在空目录中查找项目"""
        projects = project_utils.find_all_projects(str(temp_dir))
        
        assert len(projects) == 0


class TestFormatFileSize:
    """文件大小格式化测试"""
    
    def test_format_bytes(self, project_utils):
        """测试字节格式化"""
        assert project_utils.format_file_size(500) == '500.0 B'
    
    def test_format_kilobytes(self, project_utils):
        """测试 KB 格式化"""
        result = project_utils.format_file_size(2048)
        assert 'KB' in result
    
    def test_format_megabytes(self, project_utils):
        """测试 MB 格式化"""
        result = project_utils.format_file_size(2 * 1024 * 1024)
        assert 'MB' in result


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.integration
    def test_example_project_is_valid(self, project_utils, example_project):
        """测试示例项目结构有效"""
        is_valid, errors, warnings = project_utils.validate_project_structure(str(example_project))
        
        # 示例项目应该基本有效（可能有警告但不应有错误）
        assert is_valid == True, f"示例项目验证失败: {errors}"
    
    @pytest.mark.integration
    def test_example_project_has_svg_files(self, project_utils, example_project):
        """测试示例项目包含 SVG 文件"""
        info = project_utils.get_project_info(str(example_project))
        
        assert info['svg_count'] > 0, "示例项目应该包含 SVG 文件"

