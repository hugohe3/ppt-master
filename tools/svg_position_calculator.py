#!/usr/bin/env python3
"""
PPT Master - SVG 位置计算与验证工具

提供图表坐标的事前计算和事后验证功能，输出清晰的坐标表格。

======================================================================
常用命令 (可直接复制使用)
======================================================================

1. 分析 SVG 文件中的所有坐标:
   python tools/svg_position_calculator.py analyze <svg文件>

2. 交互式计算模式:
   python tools/svg_position_calculator.py interactive

3. 从 JSON 配置文件计算:
   python tools/svg_position_calculator.py from-json <config.json>

4. 快速计算:
   python tools/svg_position_calculator.py calc bar --data "华东:185,华南:142"
   python tools/svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
   python tools/svg_position_calculator.py calc line --data "0:50,10:80,20:120"
   python tools/svg_position_calculator.py calc grid --rows 2 --cols 3

======================================================================
"""

import sys
import re
import math
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# 修复 Windows 下中文输出乱码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 导入画布格式配置
try:
    from project_utils import CANVAS_FORMATS
except ImportError:
    # 如果导入失败，使用内置定义
    CANVAS_FORMATS = {
        'ppt169': {'name': 'PPT 16:9', 'dimensions': '1280×720', 'viewbox': '0 0 1280 720'},
        'ppt43': {'name': 'PPT 4:3', 'dimensions': '1024×768', 'viewbox': '0 0 1024 768'},
        'xiaohongshu': {'name': '小红书', 'dimensions': '1242×1660', 'viewbox': '0 0 1242 1660'},
        'moments': {'name': '朋友圈', 'dimensions': '1080×1080', 'viewbox': '0 0 1080 1080'},
    }


# =============================================================================
# 坐标系统基础类
# =============================================================================

@dataclass
class ChartArea:
    """图表区域定义"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    
    @property
    def width(self) -> float:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        return self.y_max - self.y_min
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)


class CoordinateSystem:
    """坐标系统 - 负责数据域到 SVG 画布坐标的映射"""
    
    def __init__(self, canvas_format: str = 'ppt169', chart_area: Optional[ChartArea] = None):
        """
        初始化坐标系统
        
        Args:
            canvas_format: 画布格式 (ppt169, ppt43, xiaohongshu, moments 等)
            chart_area: 图表区域，如果不指定则使用默认值
        """
        self.canvas_format = canvas_format
        
        # 解析画布尺寸
        if canvas_format in CANVAS_FORMATS:
            viewbox = CANVAS_FORMATS[canvas_format]['viewbox']
            parts = viewbox.split()
            self.canvas_width = int(parts[2])
            self.canvas_height = int(parts[3])
        else:
            self.canvas_width = 1280
            self.canvas_height = 720
        
        # 设置图表区域（默认留出边距）
        if chart_area:
            self.chart_area = chart_area
        else:
            # 默认图表区域：左右边距 140px，上下边距 150px
            self.chart_area = ChartArea(
                x_min=140,
                y_min=150,
                x_max=self.canvas_width - 120,
                y_max=self.canvas_height - 120
            )
    
    def data_to_svg_x(self, data_x: float, x_range: Tuple[float, float]) -> float:
        """
        将数据 X 值映射为 SVG X 坐标
        
        Args:
            data_x: 数据 X 值
            x_range: X 轴数据范围 (min, max)
        """
        x_min, x_max = x_range
        if x_max == x_min:
            return self.chart_area.x_min
        
        ratio = (data_x - x_min) / (x_max - x_min)
        return self.chart_area.x_min + ratio * self.chart_area.width
    
    def data_to_svg_y(self, data_y: float, y_range: Tuple[float, float]) -> float:
        """
        将数据 Y 值映射为 SVG Y 坐标（注意 SVG Y 轴向下为正）
        
        Args:
            data_y: 数据 Y 值
            y_range: Y 轴数据范围 (min, max)
        """
        y_min, y_max = y_range
        if y_max == y_min:
            return self.chart_area.y_max
        
        ratio = (data_y - y_min) / (y_max - y_min)
        # SVG Y 轴向下，所以要反转
        return self.chart_area.y_max - ratio * self.chart_area.height
    
    def data_to_svg(self, data_x: float, data_y: float, 
                    x_range: Tuple[float, float], y_range: Tuple[float, float]) -> Tuple[float, float]:
        """将数据点映射为 SVG 坐标"""
        return (self.data_to_svg_x(data_x, x_range), self.data_to_svg_y(data_y, y_range))


# =============================================================================
# 柱状图计算器
# =============================================================================

@dataclass
class BarPosition:
    """柱子位置信息"""
    index: int
    label: str
    value: float
    x: float
    y: float
    width: float
    height: float
    label_x: float  # 标签 X 位置
    label_y: float  # 标签 Y 位置（柱子下方）
    value_x: float  # 数值 X 位置
    value_y: float  # 数值 Y 位置（柱子上方）


class BarChartCalculator:
    """柱状图坐标计算器"""
    
    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system
    
    def calculate(self, data: Dict[str, float], 
                  bar_width: float = 50, 
                  gap_ratio: float = 0.3,
                  y_min: float = 0,
                  y_max: Optional[float] = None,
                  horizontal: bool = False) -> List[BarPosition]:
        """
        计算柱状图位置
        
        Args:
            data: 数据字典 {标签: 值}
            bar_width: 柱子宽度（如果为 None 则自动计算）
            gap_ratio: 柱子间隔比例（相对于柱宽）
            y_min: Y 轴最小值
            y_max: Y 轴最大值（如果为 None 则使用数据最大值）
            horizontal: 是否为水平柱状图
        """
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        
        if n == 0:
            return []
        
        # 计算 Y 轴范围
        if y_max is None:
            y_max = max(values) * 1.1  # 留 10% 空间
        
        area = self.coord.chart_area
        
        if horizontal:
            # 水平柱状图
            return self._calculate_horizontal(labels, values, bar_width, gap_ratio, y_min, y_max)
        
        # 计算柱子布局
        total_width = area.width
        if bar_width is None:
            # 自动计算柱宽：总宽度 / (柱数 * (1 + 间隔比例))
            bar_width = total_width / (n * (1 + gap_ratio))
        
        gap = bar_width * gap_ratio
        total_bars_width = n * bar_width + (n - 1) * gap
        start_x = area.x_min + (area.width - total_bars_width) / 2
        
        results = []
        for i, (label, value) in enumerate(zip(labels, values)):
            # 柱子 X 位置
            x = start_x + i * (bar_width + gap)
            
            # 柱子高度和 Y 位置
            ratio = (value - y_min) / (y_max - y_min) if y_max > y_min else 0
            height = ratio * area.height
            y = area.y_max - height  # SVG Y 轴向下
            
            # 标签和数值位置
            center_x = x + bar_width / 2
            
            results.append(BarPosition(
                index=i + 1,
                label=label,
                value=value,
                x=round(x, 1),
                y=round(y, 1),
                width=round(bar_width, 1),
                height=round(height, 1),
                label_x=round(center_x, 1),
                label_y=round(area.y_max + 30, 1),
                value_x=round(center_x, 1),
                value_y=round(y - 15, 1)
            ))
        
        return results
    
    def _calculate_horizontal(self, labels: List[str], values: List[float],
                              bar_height: float, gap_ratio: float,
                              x_min: float, x_max: float) -> List[BarPosition]:
        """计算水平柱状图"""
        n = len(labels)
        area = self.coord.chart_area
        
        if bar_height is None:
            bar_height = area.height / (n * (1 + gap_ratio))
        
        gap = bar_height * gap_ratio
        total_bars_height = n * bar_height + (n - 1) * gap
        start_y = area.y_min + (area.height - total_bars_height) / 2
        
        results = []
        for i, (label, value) in enumerate(zip(labels, values)):
            y = start_y + i * (bar_height + gap)
            
            ratio = (value - x_min) / (x_max - x_min) if x_max > x_min else 0
            width = ratio * area.width
            x = area.x_min
            
            center_y = y + bar_height / 2
            
            results.append(BarPosition(
                index=i + 1,
                label=label,
                value=value,
                x=round(x, 1),
                y=round(y, 1),
                width=round(width, 1),
                height=round(bar_height, 1),
                label_x=round(area.x_min - 10, 1),
                label_y=round(center_y, 1),
                value_x=round(x + width + 10, 1),
                value_y=round(center_y, 1)
            ))
        
        return results
    
    def format_table(self, positions: List[BarPosition]) -> str:
        """格式化为表格输出"""
        lines = []
        lines.append("序号  标签          数值      X        Y        宽度     高度")
        lines.append("----  ----------  --------  -------  -------  -------  -------")
        
        for p in positions:
            lines.append(f"{p.index:4d}  {p.label:<10s}  {p.value:>8.1f}  {p.x:>7.1f}  {p.y:>7.1f}  {p.width:>7.1f}  {p.height:>7.1f}")
        
        return "\n".join(lines)


# =============================================================================
# 饼图/环形图计算器
# =============================================================================

@dataclass
class PieSlice:
    """饼图扇区信息"""
    index: int
    label: str
    value: float
    percentage: float
    start_angle: float  # 起始角度（度）
    end_angle: float    # 终止角度（度）
    path_d: str         # SVG path d 属性
    label_x: float      # 标签 X 位置
    label_y: float      # 标签 Y 位置
    # 弧线端点坐标（相对于圆心）
    start_x: float
    start_y: float
    end_x: float
    end_y: float


class PieChartCalculator:
    """饼图/环形图计算器"""
    
    def __init__(self, center: Tuple[float, float] = (420, 400), radius: float = 200):
        self.cx, self.cy = center
        self.radius = radius
    
    def calculate(self, data: Dict[str, float], 
                  start_angle: float = -90,
                  inner_radius: float = 0) -> List[PieSlice]:
        """
        计算饼图扇区
        
        Args:
            data: 数据字典 {标签: 值}
            start_angle: 起始角度（度，-90 表示从 12 点方向开始）
            inner_radius: 内半径（0 表示饼图，> 0 表示环形图）
        """
        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)
        
        if total == 0:
            return []
        
        results = []
        current_angle = start_angle
        
        for i, (label, value) in enumerate(zip(labels, values)):
            percentage = value / total * 100
            angle_span = value / total * 360
            end_angle = current_angle + angle_span
            
            # 计算弧线端点
            start_rad = math.radians(current_angle)
            end_rad = math.radians(end_angle)
            
            start_x = self.radius * math.cos(start_rad)
            start_y = self.radius * math.sin(start_rad)
            end_x = self.radius * math.cos(end_rad)
            end_y = self.radius * math.sin(end_rad)
            
            # 生成 path
            large_arc = 1 if angle_span > 180 else 0
            
            if inner_radius > 0:
                # 环形图
                inner_start_x = inner_radius * math.cos(start_rad)
                inner_start_y = inner_radius * math.sin(start_rad)
                inner_end_x = inner_radius * math.cos(end_rad)
                inner_end_y = inner_radius * math.sin(end_rad)
                
                path_d = (
                    f"M {inner_start_x:.2f},{inner_start_y:.2f} "
                    f"L {start_x:.2f},{start_y:.2f} "
                    f"A {self.radius},{self.radius} 0 {large_arc},1 {end_x:.2f},{end_y:.2f} "
                    f"L {inner_end_x:.2f},{inner_end_y:.2f} "
                    f"A {inner_radius},{inner_radius} 0 {large_arc},0 {inner_start_x:.2f},{inner_start_y:.2f} Z"
                )
            else:
                # 饼图
                path_d = (
                    f"M 0,0 "
                    f"L {start_x:.2f},{start_y:.2f} "
                    f"A {self.radius},{self.radius} 0 {large_arc},1 {end_x:.2f},{end_y:.2f} Z"
                )
            
            # 标签位置（扇区中心方向，距离圆心的 70% 处）
            mid_angle = (current_angle + end_angle) / 2
            mid_rad = math.radians(mid_angle)
            label_distance = self.radius * 0.7
            label_x = self.cx + label_distance * math.cos(mid_rad)
            label_y = self.cy + label_distance * math.sin(mid_rad)
            
            results.append(PieSlice(
                index=i + 1,
                label=label,
                value=value,
                percentage=round(percentage, 1),
                start_angle=round(current_angle, 1),
                end_angle=round(end_angle, 1),
                path_d=path_d,
                label_x=round(label_x, 1),
                label_y=round(label_y, 1),
                start_x=round(start_x, 2),
                start_y=round(start_y, 2),
                end_x=round(end_x, 2),
                end_y=round(end_y, 2)
            ))
            
            current_angle = end_angle
        
        return results
    
    def format_table(self, slices: List[PieSlice]) -> str:
        """格式化为表格输出"""
        lines = []
        lines.append(f"圆心: ({self.cx}, {self.cy}) | 半径: {self.radius}")
        lines.append("")
        lines.append("序号  标签          百分比    起始角    终止角    标签X    标签Y")
        lines.append("----  ----------  --------  --------  --------  -------  -------")
        
        for s in slices:
            lines.append(
                f"{s.index:4d}  {s.label:<10s}  {s.percentage:>6.1f}%  {s.start_angle:>8.1f}  "
                f"{s.end_angle:>8.1f}  {s.label_x:>7.1f}  {s.label_y:>7.1f}"
            )
        
        lines.append("")
        lines.append("=== 弧线端点坐标（相对于圆心）===")
        lines.append("序号  起点X      起点Y      终点X      终点Y")
        lines.append("----  ---------  ---------  ---------  ---------")
        
        for s in slices:
            lines.append(
                f"{s.index:4d}  {s.start_x:>9.2f}  {s.start_y:>9.2f}  {s.end_x:>9.2f}  {s.end_y:>9.2f}"
            )
        
        lines.append("")
        lines.append("=== Path d 属性 ===")
        for s in slices:
            lines.append(f"{s.index}. {s.label}: {s.path_d}")
        
        return "\n".join(lines)


# =============================================================================
# 雷达图计算器
# =============================================================================

@dataclass
class RadarPoint:
    """雷达图数据点"""
    index: int
    label: str
    value: float
    percentage: float  # 相对于最大值的百分比
    angle: float       # 角度（度）
    x: float           # 相对于圆心的 X
    y: float           # 相对于圆心的 Y
    abs_x: float       # 绝对 X 坐标
    abs_y: float       # 绝对 Y 坐标
    label_x: float     # 标签 X 位置
    label_y: float     # 标签 Y 位置


class RadarChartCalculator:
    """雷达图计算器"""
    
    def __init__(self, center: Tuple[float, float] = (640, 400), radius: float = 200):
        self.cx, self.cy = center
        self.radius = radius
    
    def calculate(self, data: Dict[str, float], 
                  max_value: Optional[float] = None,
                  start_angle: float = -90) -> List[RadarPoint]:
        """
        计算雷达图顶点坐标
        
        Args:
            data: 数据字典 {维度名: 值}
            max_value: 最大值（用于归一化），如果为 None 则使用数据最大值
            start_angle: 起始角度（度，-90 表示从 12 点方向开始）
        """
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        
        if n == 0:
            return []
        
        if max_value is None:
            max_value = max(values)
        
        angle_step = 360 / n
        results = []
        
        for i, (label, value) in enumerate(zip(labels, values)):
            angle = start_angle + i * angle_step
            rad = math.radians(angle)
            
            # 计算归一化后的半径
            percentage = (value / max_value * 100) if max_value > 0 else 0
            point_radius = self.radius * (value / max_value) if max_value > 0 else 0
            
            # 计算坐标
            x = point_radius * math.cos(rad)
            y = point_radius * math.sin(rad)
            
            # 标签位置（在最外圈外侧）
            label_distance = self.radius + 30
            label_x = self.cx + label_distance * math.cos(rad)
            label_y = self.cy + label_distance * math.sin(rad)
            
            results.append(RadarPoint(
                index=i + 1,
                label=label,
                value=value,
                percentage=round(percentage, 1),
                angle=round(angle, 1),
                x=round(x, 2),
                y=round(y, 2),
                abs_x=round(self.cx + x, 2),
                abs_y=round(self.cy + y, 2),
                label_x=round(label_x, 1),
                label_y=round(label_y, 1)
            ))
        
        return results
    
    def calculate_grid(self, levels: int = 5) -> List[List[Tuple[float, float]]]:
        """计算网格层坐标（用于绘制背景多边形）"""
        n = 6  # 假设 6 个维度
        grids = []
        
        for level in range(1, levels + 1):
            level_radius = self.radius * level / levels
            points = []
            
            angle_step = 360 / n
            for i in range(n):
                angle = -90 + i * angle_step
                rad = math.radians(angle)
                x = level_radius * math.cos(rad)
                y = level_radius * math.sin(rad)
                points.append((round(x, 2), round(y, 2)))
            
            grids.append(points)
        
        return grids
    
    def format_table(self, points: List[RadarPoint]) -> str:
        """格式化为表格输出"""
        lines = []
        lines.append(f"圆心: ({self.cx}, {self.cy}) | 半径: {self.radius}")
        lines.append("")
        lines.append("序号  维度          数值    百分比    角度      X        Y        绝对X    绝对Y")
        lines.append("----  ----------  ------  --------  ------  -------  -------  -------  -------")
        
        for p in points:
            lines.append(
                f"{p.index:4d}  {p.label:<10s}  {p.value:>6.1f}  {p.percentage:>6.1f}%  "
                f"{p.angle:>6.1f}  {p.x:>7.2f}  {p.y:>7.2f}  {p.abs_x:>7.1f}  {p.abs_y:>7.1f}"
            )
        
        # 生成 polygon points 属性
        lines.append("")
        lines.append("=== SVG Polygon Points ===")
        points_str = " ".join([f"{p.x},{p.y}" for p in points])
        lines.append(f'points="{points_str}"')
        
        return "\n".join(lines)


# =============================================================================
# 折线图/散点图计算器
# =============================================================================

@dataclass
class DataPoint:
    """数据点"""
    index: int
    x_value: float
    y_value: float
    svg_x: float
    svg_y: float
    label: Optional[str] = None


class LineChartCalculator:
    """折线图/散点图计算器"""
    
    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system
    
    def calculate(self, data: List[Tuple[float, float]],
                  x_range: Optional[Tuple[float, float]] = None,
                  y_range: Optional[Tuple[float, float]] = None,
                  labels: Optional[List[str]] = None) -> List[DataPoint]:
        """
        计算数据点坐标
        
        Args:
            data: 数据点列表 [(x1, y1), (x2, y2), ...]
            x_range: X 轴范围，如果为 None 则自动计算
            y_range: Y 轴范围，如果为 None 则自动计算
            labels: 点标签列表
        """
        if not data:
            return []
        
        x_values = [p[0] for p in data]
        y_values = [p[1] for p in data]
        
        if x_range is None:
            x_range = (min(x_values), max(x_values))
        if y_range is None:
            y_min = 0
            y_max = max(y_values) * 1.1
            y_range = (y_min, y_max)
        
        results = []
        for i, (x, y) in enumerate(data):
            svg_x, svg_y = self.coord.data_to_svg(x, y, x_range, y_range)
            
            results.append(DataPoint(
                index=i + 1,
                x_value=x,
                y_value=y,
                svg_x=round(svg_x, 1),
                svg_y=round(svg_y, 1),
                label=labels[i] if labels and i < len(labels) else None
            ))
        
        return results
    
    def generate_path(self, points: List[DataPoint], closed: bool = False) -> str:
        """生成 SVG path d 属性"""
        if not points:
            return ""
        
        parts = [f"M {points[0].svg_x},{points[0].svg_y}"]
        for p in points[1:]:
            parts.append(f"L {p.svg_x},{p.svg_y}")
        
        if closed:
            parts.append("Z")
        
        return " ".join(parts)
    
    def format_table(self, points: List[DataPoint]) -> str:
        """格式化为表格输出"""
        lines = []
        area = self.coord.chart_area
        lines.append(f"图表区域: ({area.x_min}, {area.y_min}) - ({area.x_max}, {area.y_max})")
        lines.append("")
        lines.append("序号  X值        Y值        SVG_X     SVG_Y")
        lines.append("----  ---------  ---------  --------  --------")
        
        for p in points:
            label_part = f"  ({p.label})" if p.label else ""
            lines.append(
                f"{p.index:4d}  {p.x_value:>9.2f}  {p.y_value:>9.2f}  {p.svg_x:>8.1f}  {p.svg_y:>8.1f}{label_part}"
            )
        
        lines.append("")
        lines.append("=== SVG Path ===")
        lines.append(self.generate_path(points))
        
        return "\n".join(lines)


# =============================================================================
# 网格布局计算器
# =============================================================================

@dataclass
class GridCell:
    """网格单元格"""
    row: int
    col: int
    index: int  # 从 1 开始的索引
    x: float
    y: float
    width: float
    height: float
    center_x: float
    center_y: float


class GridLayoutCalculator:
    """网格布局计算器"""
    
    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system
    
    def calculate(self, rows: int, cols: int,
                  padding: float = 20,
                  gap: float = 20) -> List[GridCell]:
        """
        计算网格布局
        
        Args:
            rows: 行数
            cols: 列数
            padding: 图表区域内边距
            gap: 单元格间距
        """
        area = self.coord.chart_area
        
        # 计算可用区域
        available_width = area.width - 2 * padding - (cols - 1) * gap
        available_height = area.height - 2 * padding - (rows - 1) * gap
        
        cell_width = available_width / cols
        cell_height = available_height / rows
        
        results = []
        index = 1
        
        for row in range(rows):
            for col in range(cols):
                x = area.x_min + padding + col * (cell_width + gap)
                y = area.y_min + padding + row * (cell_height + gap)
                
                results.append(GridCell(
                    row=row + 1,
                    col=col + 1,
                    index=index,
                    x=round(x, 1),
                    y=round(y, 1),
                    width=round(cell_width, 1),
                    height=round(cell_height, 1),
                    center_x=round(x + cell_width / 2, 1),
                    center_y=round(y + cell_height / 2, 1)
                ))
                index += 1
        
        return results
    
    def format_table(self, cells: List[GridCell]) -> str:
        """格式化为表格输出"""
        lines = []
        area = self.coord.chart_area
        lines.append(f"图表区域: ({area.x_min}, {area.y_min}) - ({area.x_max}, {area.y_max})")
        lines.append("")
        lines.append("序号  行    列    X        Y        宽度     高度     中心X    中心Y")
        lines.append("----  ----  ----  -------  -------  -------  -------  -------  -------")
        
        for c in cells:
            lines.append(
                f"{c.index:4d}  {c.row:4d}  {c.col:4d}  {c.x:>7.1f}  {c.y:>7.1f}  "
                f"{c.width:>7.1f}  {c.height:>7.1f}  {c.center_x:>7.1f}  {c.center_y:>7.1f}"
            )
        
        return "\n".join(lines)


# =============================================================================
# SVG 验证器
# =============================================================================

@dataclass
class ValidationResult:
    """验证结果"""
    element_type: str
    element_id: str
    attribute: str
    expected: float
    actual: float
    deviation: float
    passed: bool


class SVGPositionValidator:
    """SVG 位置验证器"""
    
    def __init__(self, tolerance: float = 1.0):
        """
        初始化验证器
        
        Args:
            tolerance: 允许的误差范围（像素）
        """
        self.tolerance = tolerance
    
    def validate_from_file(self, svg_file: str, 
                           expected_coords: Dict[str, Dict[str, float]]) -> List[ValidationResult]:
        """
        从文件验证坐标
        
        Args:
            svg_file: SVG 文件路径
            expected_coords: 期望的坐标 {元素ID: {属性: 值}}
        """
        svg_path = Path(svg_file)
        if not svg_path.exists():
            raise FileNotFoundError(f"SVG 文件不存在: {svg_file}")
        
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.validate_content(content, expected_coords)
    
    def validate_content(self, svg_content: str,
                        expected_coords: Dict[str, Dict[str, float]]) -> List[ValidationResult]:
        """验证 SVG 内容中的坐标"""
        results = []
        
        for element_id, attrs in expected_coords.items():
            for attr, expected in attrs.items():
                actual = self._extract_attribute(svg_content, element_id, attr)
                
                if actual is not None:
                    deviation = abs(actual - expected)
                    passed = deviation <= self.tolerance
                    
                    results.append(ValidationResult(
                        element_type=self._guess_element_type(element_id),
                        element_id=element_id,
                        attribute=attr,
                        expected=expected,
                        actual=actual,
                        deviation=round(deviation, 2),
                        passed=passed
                    ))
                else:
                    results.append(ValidationResult(
                        element_type=self._guess_element_type(element_id),
                        element_id=element_id,
                        attribute=attr,
                        expected=expected,
                        actual=float('nan'),
                        deviation=float('inf'),
                        passed=False
                    ))
        
        return results
    
    def _extract_attribute(self, content: str, element_id: str, attr: str) -> Optional[float]:
        """从 SVG 内容中提取属性值"""
        # 查找包含该 ID 的元素
        pattern = rf'id="{element_id}"[^>]*{attr}="([^"]+)"'
        match = re.search(pattern, content)
        
        if not match:
            # 尝试反向顺序
            pattern = rf'{attr}="([^"]+)"[^>]*id="{element_id}"'
            match = re.search(pattern, content)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def _guess_element_type(self, element_id: str) -> str:
        """根据 ID 猜测元素类型"""
        id_lower = element_id.lower()
        if 'bar' in id_lower or 'rect' in id_lower:
            return 'rect'
        elif 'circle' in id_lower or 'dot' in id_lower:
            return 'circle'
        elif 'path' in id_lower or 'slice' in id_lower:
            return 'path'
        elif 'line' in id_lower:
            return 'line'
        elif 'text' in id_lower or 'label' in id_lower:
            return 'text'
        return 'unknown'
    
    def extract_all_positions(self, svg_content: str) -> Dict[str, Dict[str, float]]:
        """提取 SVG 中所有元素的位置信息"""
        positions = {}
        
        # 提取 rect 元素
        rect_pattern = r'<rect[^>]*(?:id="([^"]*)")?[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*(?:width="([^"]*)")?[^>]*(?:height="([^"]*)")?'
        for match in re.finditer(rect_pattern, svg_content):
            id_val = match.group(1) or f"rect_{len(positions)}"
            positions[id_val] = {
                'x': float(match.group(2)) if match.group(2) else 0,
                'y': float(match.group(3)) if match.group(3) else 0,
            }
            if match.group(4):
                positions[id_val]['width'] = float(match.group(4))
            if match.group(5):
                positions[id_val]['height'] = float(match.group(5))
        
        # 提取 circle 元素
        circle_pattern = r'<circle[^>]*(?:id="([^"]*)")?[^>]*cx="([^"]*)"[^>]*cy="([^"]*)"'
        for match in re.finditer(circle_pattern, svg_content):
            id_val = match.group(1) or f"circle_{len(positions)}"
            positions[id_val] = {
                'cx': float(match.group(2)),
                'cy': float(match.group(3)),
            }
        
        return positions
    
    def format_results(self, results: List[ValidationResult]) -> str:
        """格式化验证结果"""
        lines = []
        lines.append("=== SVG 位置验证结果 ===")
        lines.append(f"容差: {self.tolerance}px")
        lines.append("")
        lines.append("状态  元素ID          属性     期望值    实际值    偏差")
        lines.append("----  --------------  ------  --------  --------  ------")
        
        passed_count = 0
        for r in results:
            status = "[OK]" if r.passed else "[X]"
            if r.passed:
                passed_count += 1
            
            actual_str = f"{r.actual:.1f}" if not math.isnan(r.actual) else "N/A"
            deviation_str = f"{r.deviation:.2f}" if not math.isinf(r.deviation) else "N/A"
            
            lines.append(
                f"{status}    {r.element_id:<14s}  {r.attribute:<6s}  "
                f"{r.expected:>8.1f}  {actual_str:>8s}  {deviation_str:>6s}"
            )
        
        lines.append("")
        lines.append(f"通过: {passed_count}/{len(results)} ({passed_count/len(results)*100:.1f}%)")
        
        return "\n".join(lines)


# =============================================================================
# 命令行接口
# =============================================================================

def parse_data_string(data_str: str) -> Dict[str, float]:
    """解析数据字符串 '标签1:值1,标签2:值2' 格式"""
    result = {}
    for item in data_str.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            label, value = item.split(':', 1)
            try:
                result[label.strip()] = float(value.strip())
            except ValueError:
                print(f"[警告] 无法解析数值: '{value.strip()}', 已跳过")
        else:
            print(f"[警告] 格式错误 (应为 '标签:值'): '{item}'")
    return result


def parse_xy_data_string(data_str: str) -> List[Tuple[float, float]]:
    """解析 XY 数据字符串 'x1:y1,x2:y2' 格式"""
    result = []
    for item in data_str.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            x, y = item.split(':', 1)
            try:
                result.append((float(x.strip()), float(y.strip())))
            except ValueError:
                print(f"[警告] 无法解析坐标: '{item}', 已跳过")
        else:
            print(f"[警告] 格式错误 (应为 'x:y'): '{item}'")
    return result


def parse_tuple(s: str) -> Tuple[float, ...]:
    """解析逗号分隔的数字元组"""
    return tuple(float(x.strip()) for x in s.split(','))


def extract_attr(element: str, attr_name: str) -> Optional[str]:
    """从元素字符串中提取属性值（属性顺序无关）"""
    pattern = rf'{attr_name}="([^"]*)"'
    match = re.search(pattern, element)
    return match.group(1) if match else None


def analyze_svg_file(svg_file: str) -> None:
    """分析 SVG 文件中的所有图表元素"""
    svg_path = Path(svg_file)
    if not svg_path.exists():
        print(f"[错误] 文件不存在: {svg_file}")
        return
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n{'='*70}")
    print(f"SVG 文件分析: {svg_path.name}")
    print(f"{'='*70}")
    
    # 提取 viewBox
    viewbox_match = re.search(r'viewBox="([^"]+)"', content)
    if viewbox_match:
        print(f"画布 viewBox: {viewbox_match.group(1)}")
    
    # 使用更健壮的方式提取元素（属性顺序无关）
    # 提取所有 rect 元素
    rect_elements = re.findall(r'<rect[^>]*/?>', content)
    rects = []
    for elem in rect_elements:
        x = extract_attr(elem, 'x')
        y = extract_attr(elem, 'y')
        w = extract_attr(elem, 'width')
        h = extract_attr(elem, 'height')
        if x is not None and y is not None:
            rects.append((x, y, w, h))
    
    # 提取所有 circle 元素
    circle_elements = re.findall(r'<circle[^>]*/?>', content)
    circles = []
    for elem in circle_elements:
        cx = extract_attr(elem, 'cx')
        cy = extract_attr(elem, 'cy')
        r = extract_attr(elem, 'r')
        if cx is not None and cy is not None:
            circles.append((cx, cy, r))
    
    # 提取所有 polyline/polygon 元素
    polylines = re.findall(r'<(?:polyline|polygon)[^>]*points="([^"]*)"', content)
    
    # 提取 path 元素
    paths = re.findall(r'<path[^>]*d="([^"]*)"', content)
    
    print(f"\n元素统计:")
    print(f"  - rect 矩形: {len(rects)} 个")
    print(f"  - circle 圆形: {len(circles)} 个")
    print(f"  - polyline/polygon: {len(polylines)} 个")
    print(f"  - path 路径: {len(paths)} 个")
    
    # 详细列出 rect 元素
    if rects:
        print(f"\n=== 矩形元素 (rect) ===")
        print(f"{'序号':<4}  {'X':<8}  {'Y':<8}  {'宽度':<8}  {'高度':<8}")
        print("-" * 45)
        for i, (x, y, w, h) in enumerate(rects[:20], 1):  # 只显示前20个
            w_str = w if w else '-'
            h_str = h if h else '-'
            print(f"{i:<4}  {x:<8}  {y:<8}  {w_str:<8}  {h_str:<8}")
        if len(rects) > 20:
            print(f"... 还有 {len(rects) - 20} 个矩形")
    
    # 详细列出 circle 元素
    if circles:
        print(f"\n=== 圆形元素 (circle) ===")
        print(f"{'序号':<4}  {'CX':<10}  {'CY':<10}  {'半径':<8}")
        print("-" * 40)
        for i, (cx, cy, r) in enumerate(circles[:20], 1):
            r_str = r if r else '-'
            print(f"{i:<4}  {cx:<10}  {cy:<10}  {r_str:<8}")
        if len(circles) > 20:
            print(f"... 还有 {len(circles) - 20} 个圆形")
    
    # 列出 polyline points
    if polylines:
        print(f"\n=== 折线/多边形 (polyline/polygon) ===")
        for i, points in enumerate(polylines, 1):
            point_list = points.strip().split()
            print(f"\n折线 {i} ({len(point_list)} 个点):")
            # 解析并显示前几个点
            parsed_points = []
            for p in point_list[:5]:
                if ',' in p:
                    x, y = p.split(',')
                    parsed_points.append(f"({x},{y})")
            print(f"  起始点: {' → '.join(parsed_points)}")
            if len(point_list) > 5:
                print(f"  ... 共 {len(point_list)} 个点")
    
    print(f"\n{'='*70}")


def interactive_mode() -> None:
    """交互式计算模式"""
    print("\n" + "="*60)
    print("SVG 位置计算器 - 交互模式")
    print("="*60)
    print("\n选择图表类型:")
    print("  1. 柱状图 (bar)")
    print("  2. 饼图 (pie)")
    print("  3. 雷达图 (radar)")
    print("  4. 折线图 (line)")
    print("  5. 网格布局 (grid)")
    print("  6. 自定义折线 (custom)")
    print("  0. 退出")
    
    while True:
        try:
            choice = input("\n请选择 [1-6, 0退出]: ").strip()
            
            if choice == '0':
                print("退出交互模式")
                break
            
            elif choice == '1':
                print("\n=== 柱状图计算 ===")
                data_str = input("输入数据 (格式: 标签1:值1,标签2:值2): ").strip()
                if not data_str:
                    print("示例: 华东:185,华南:142,华北:128")
                    continue
                
                canvas = input("画布格式 [ppt169]: ").strip() or 'ppt169'
                coord = CoordinateSystem(canvas)
                calc = BarChartCalculator(coord)
                data = parse_data_string(data_str)
                positions = calc.calculate(data)
                print()
                print(calc.format_table(positions))
            
            elif choice == '2':
                print("\n=== 饼图计算 ===")
                data_str = input("输入数据 (格式: 标签1:值1,标签2:值2): ").strip()
                if not data_str:
                    print("示例: A:35,B:25,C:20,D:12,Other:8")
                    continue
                
                center_str = input("圆心坐标 [420,400]: ").strip() or '420,400'
                radius = float(input("半径 [200]: ").strip() or '200')
                
                center = parse_tuple(center_str)
                calc = PieChartCalculator(center, radius)
                data = parse_data_string(data_str)
                slices = calc.calculate(data)
                print()
                print(calc.format_table(slices))
            
            elif choice == '3':
                print("\n=== 雷达图计算 ===")
                data_str = input("输入数据 (格式: 维度1:值1,维度2:值2): ").strip()
                if not data_str:
                    print("示例: 性能:90,安全:85,易用:75,价格:70")
                    continue
                
                center_str = input("圆心坐标 [640,400]: ").strip() or '640,400'
                radius = float(input("半径 [200]: ").strip() or '200')
                
                center = parse_tuple(center_str)
                calc = RadarChartCalculator(center, radius)
                data = parse_data_string(data_str)
                points = calc.calculate(data)
                print()
                print(calc.format_table(points))
            
            elif choice == '4':
                print("\n=== 折线图计算 ===")
                data_str = input("输入数据 (格式: x1:y1,x2:y2): ").strip()
                if not data_str:
                    print("示例: 0:50,10:80,20:120,30:95")
                    continue
                
                canvas = input("画布格式 [ppt169]: ").strip() or 'ppt169'
                coord = CoordinateSystem(canvas)
                calc = LineChartCalculator(coord)
                data = parse_xy_data_string(data_str)
                points = calc.calculate(data)
                print()
                print(calc.format_table(points))
            
            elif choice == '5':
                print("\n=== 网格布局计算 ===")
                rows = int(input("行数: ").strip() or '2')
                cols = int(input("列数: ").strip() or '3')
                canvas = input("画布格式 [ppt169]: ").strip() or 'ppt169'
                
                coord = CoordinateSystem(canvas)
                calc = GridLayoutCalculator(coord)
                cells = calc.calculate(rows, cols)
                print()
                print(calc.format_table(cells))
            
            elif choice == '6':
                print("\n=== 自定义折线计算 ===")
                print("适用于自定义公式的折线图，如价格指数图")
                
                base_x = float(input("X起始值 [170]: ").strip() or '170')
                step_x = float(input("X步长 [40]: ").strip() or '40')
                base_y = float(input("Y基准值 [595]: ").strip() or '595')
                scale_y = float(input("Y缩放系数 [20]: ").strip() or '20')
                ref_value = float(input("参考基准值 [100]: ").strip() or '100')
                
                print(f"\n公式: X = {base_x} + 序号 × {step_x}")
                print(f"      Y = {base_y} - (数值 - {ref_value}) × {scale_y}")
                
                data_str = input("\n输入数据 (逗号分隔的数值): ").strip()
                if data_str:
                    values = [float(v.strip()) for v in data_str.split(',')]
                    print(f"\n{'序号':<4}  {'数值':<10}  {'X':<8}  {'Y':<8}")
                    print("-" * 35)
                    for i, v in enumerate(values, 1):
                        x = base_x + i * step_x
                        y = base_y - (v - ref_value) * scale_y
                        print(f"{i:<4}  {v:<10.1f}  {x:<8.0f}  {y:<8.0f}")
                    
                    # 生成 polyline points
                    points_list = []
                    for i, v in enumerate(values, 1):
                        x = base_x + i * step_x
                        y = base_y - (v - ref_value) * scale_y
                        points_list.append(f"{int(x)},{int(y)}")
                    print(f"\npolyline points:")
                    print(" ".join(points_list))
            
            else:
                print("无效选择，请输入 1-6 或 0")
                
        except KeyboardInterrupt:
            print("\n退出交互模式")
            break
        except Exception as e:
            print(f"错误: {e}")


def from_json_config(config_file: str) -> None:
    """从 JSON 配置文件读取并计算"""
    import json
    
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"[错误] 配置文件不存在: {config_file}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    chart_type = config.get('type', 'bar')
    data = config.get('data', {})
    
    print(f"\n从配置文件加载: {config_path.name}")
    print(f"图表类型: {chart_type}")
    
    if chart_type == 'bar':
        canvas = config.get('canvas', 'ppt169')
        coord = CoordinateSystem(canvas)
        calc = BarChartCalculator(coord)
        positions = calc.calculate(data)
        print(calc.format_table(positions))
    
    elif chart_type == 'pie':
        center = tuple(config.get('center', [420, 400]))
        radius = config.get('radius', 200)
        calc = PieChartCalculator(center, radius)
        slices = calc.calculate(data)
        print(calc.format_table(slices))
    
    elif chart_type == 'line':
        canvas = config.get('canvas', 'ppt169')
        coord = CoordinateSystem(canvas)
        calc = LineChartCalculator(coord)
        # data should be list of [x, y] pairs
        points_data = [(p[0], p[1]) for p in data]
        points = calc.calculate(points_data)
        print(calc.format_table(points))
    
    elif chart_type == 'custom_line':
        # 自定义折线图
        base_x = config.get('base_x', 170)
        step_x = config.get('step_x', 40)
        base_y = config.get('base_y', 595)
        scale_y = config.get('scale_y', 20)
        ref_value = config.get('ref_value', 100)
        values = config.get('values', [])
        
        print(f"\n公式: X = {base_x} + 序号 × {step_x}")
        print(f"      Y = {base_y} - (数值 - {ref_value}) × {scale_y}")
        print(f"\n{'序号':<4}  {'数值':<10}  {'X':<8}  {'Y':<8}")
        print("-" * 35)
        
        points_list = []
        for i, v in enumerate(values, 1):
            x = base_x + i * step_x
            y = base_y - (v - ref_value) * scale_y
            print(f"{i:<4}  {v:<10.1f}  {x:<8.0f}  {y:<8.0f}")
            points_list.append(f"{int(x)},{int(y)}")
        
        print(f"\npolyline points:")
        print(" ".join(points_list))


def main():
    parser = argparse.ArgumentParser(
        description='SVG 位置计算与验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
常用命令:
  # 分析 SVG 文件
  python svg_position_calculator.py analyze example.svg
  
  # 交互式模式
  python svg_position_calculator.py interactive
  
  # 从 JSON 配置计算
  python svg_position_calculator.py from-json config.json
  
  # 快速计算
  python svg_position_calculator.py calc bar --data "华东:185,华南:142"
  python svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
  python svg_position_calculator.py calc line --data "0:50,10:80,20:120"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # calc 子命令
    calc_parser = subparsers.add_parser('calc', help='计算坐标')
    calc_subparsers = calc_parser.add_subparsers(dest='chart_type', help='图表类型')
    
    # 柱状图
    bar_parser = calc_subparsers.add_parser('bar', help='柱状图')
    bar_parser.add_argument('--data', required=True, help='数据 "标签1:值1,标签2:值2"')
    bar_parser.add_argument('--canvas', default='ppt169', help='画布格式')
    bar_parser.add_argument('--area', help='图表区域 "x_min,y_min,x_max,y_max"')
    bar_parser.add_argument('--bar-width', type=float, default=50, help='柱宽')
    bar_parser.add_argument('--horizontal', action='store_true', help='水平柱状图')
    
    # 饼图
    pie_parser = calc_subparsers.add_parser('pie', help='饼图/环形图')
    pie_parser.add_argument('--data', required=True, help='数据 "标签1:值1,标签2:值2"')
    pie_parser.add_argument('--center', default='420,400', help='圆心 "x,y"')
    pie_parser.add_argument('--radius', type=float, default=200, help='半径')
    pie_parser.add_argument('--inner-radius', type=float, default=0, help='内半径（环形图）')
    pie_parser.add_argument('--start-angle', type=float, default=-90, help='起始角度')
    
    # 雷达图
    radar_parser = calc_subparsers.add_parser('radar', help='雷达图')
    radar_parser.add_argument('--data', required=True, help='数据 "维度1:值1,维度2:值2"')
    radar_parser.add_argument('--center', default='640,400', help='圆心 "x,y"')
    radar_parser.add_argument('--radius', type=float, default=200, help='半径')
    radar_parser.add_argument('--max-value', type=float, help='最大值')
    
    # 折线图/散点图
    line_parser = calc_subparsers.add_parser('line', help='折线图/散点图')
    line_parser.add_argument('--data', required=True, help='数据 "x1:y1,x2:y2"')
    line_parser.add_argument('--canvas', default='ppt169', help='画布格式')
    line_parser.add_argument('--area', help='图表区域 "x_min,y_min,x_max,y_max"')
    line_parser.add_argument('--x-range', help='X 轴范围 "min,max"')
    line_parser.add_argument('--y-range', help='Y 轴范围 "min,max"')
    
    # 网格布局
    grid_parser = calc_subparsers.add_parser('grid', help='网格布局')
    grid_parser.add_argument('--rows', type=int, required=True, help='行数')
    grid_parser.add_argument('--cols', type=int, required=True, help='列数')
    grid_parser.add_argument('--canvas', default='ppt169', help='画布格式')
    grid_parser.add_argument('--area', help='图表区域 "x_min,y_min,x_max,y_max"')
    grid_parser.add_argument('--padding', type=float, default=20, help='内边距')
    grid_parser.add_argument('--gap', type=float, default=20, help='间距')
    
    # validate 子命令
    validate_parser = subparsers.add_parser('validate', help='验证 SVG')
    validate_parser.add_argument('svg_file', help='SVG 文件路径')
    validate_parser.add_argument('--extract', action='store_true', help='提取所有位置信息')
    validate_parser.add_argument('--tolerance', type=float, default=1.0, help='容差（像素）')
    
    # analyze 子命令 - 分析 SVG 文件
    analyze_parser = subparsers.add_parser('analyze', help='分析 SVG 文件中的图表元素')
    analyze_parser.add_argument('svg_file', help='SVG 文件路径')
    
    # interactive 子命令 - 交互模式
    subparsers.add_parser('interactive', help='交互式计算模式')
    
    # from-json 子命令 - 从配置文件读取
    json_parser = subparsers.add_parser('from-json', help='从 JSON 配置文件计算')
    json_parser.add_argument('config_file', help='JSON 配置文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'calc':
        # 解析图表区域
        chart_area = None
        if hasattr(args, 'area') and args.area:
            parts = parse_tuple(args.area)
            chart_area = ChartArea(parts[0], parts[1], parts[2], parts[3])
        
        if args.chart_type == 'bar':
            canvas = args.canvas if hasattr(args, 'canvas') else 'ppt169'
            coord = CoordinateSystem(canvas, chart_area)
            calc = BarChartCalculator(coord)
            data = parse_data_string(args.data)
            positions = calc.calculate(data, bar_width=args.bar_width, horizontal=args.horizontal)
            
            print(f"\n=== 柱状图坐标计算 ===")
            print(f"画布: {CANVAS_FORMATS.get(canvas, {}).get('dimensions', canvas)}")
            print(f"图表区域: ({coord.chart_area.x_min}, {coord.chart_area.y_min}) - "
                  f"({coord.chart_area.x_max}, {coord.chart_area.y_max})")
            print()
            print(calc.format_table(positions))
            
        elif args.chart_type == 'pie':
            center = parse_tuple(args.center)
            calc = PieChartCalculator(center, args.radius)
            data = parse_data_string(args.data)
            slices = calc.calculate(data, start_angle=args.start_angle, inner_radius=args.inner_radius)
            
            print(f"\n=== 饼图扇区计算 ===")
            print(calc.format_table(slices))
            
        elif args.chart_type == 'radar':
            center = parse_tuple(args.center)
            calc = RadarChartCalculator(center, args.radius)
            data = parse_data_string(args.data)
            points = calc.calculate(data, max_value=args.max_value)
            
            print(f"\n=== 雷达图顶点计算 ===")
            print(calc.format_table(points))
            
        elif args.chart_type == 'line':
            canvas = args.canvas if hasattr(args, 'canvas') else 'ppt169'
            coord = CoordinateSystem(canvas, chart_area)
            calc = LineChartCalculator(coord)
            data = parse_xy_data_string(args.data)
            
            x_range = parse_tuple(args.x_range) if args.x_range else None
            y_range = parse_tuple(args.y_range) if args.y_range else None
            
            points = calc.calculate(data, x_range, y_range)
            
            print(f"\n=== 折线图/散点图坐标计算 ===")
            print(f"画布: {CANVAS_FORMATS.get(canvas, {}).get('dimensions', canvas)}")
            print(calc.format_table(points))
            
        elif args.chart_type == 'grid':
            canvas = args.canvas if hasattr(args, 'canvas') else 'ppt169'
            coord = CoordinateSystem(canvas, chart_area)
            calc = GridLayoutCalculator(coord)
            cells = calc.calculate(args.rows, args.cols, args.padding, args.gap)
            
            print(f"\n=== 网格布局计算 ({args.rows}×{args.cols}) ===")
            print(f"画布: {CANVAS_FORMATS.get(canvas, {}).get('dimensions', canvas)}")
            print(calc.format_table(cells))
            
        else:
            parser.print_help()
    
    elif args.command == 'validate':
        validator = SVGPositionValidator(tolerance=args.tolerance)
        
        if args.extract:
            # 提取模式
            with open(args.svg_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            positions = validator.extract_all_positions(content)
            
            print(f"\n=== 提取的元素位置 ===")
            print(f"文件: {args.svg_file}")
            print()
            
            for element_id, attrs in positions.items():
                print(f"{element_id}:")
                for attr, value in attrs.items():
                    print(f"  {attr}: {value}")
        else:
            print("验证模式需要提供期望坐标文件，请使用 --extract 先提取坐标")
    
    elif args.command == 'analyze':
        analyze_svg_file(args.svg_file)
    
    elif args.command == 'interactive':
        interactive_mode()
    
    elif args.command == 'from-json':
        from_json_config(args.config_file)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

