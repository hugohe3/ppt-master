#!/usr/bin/env python3
"""
PPT Master - Gemini 水印去除工具

去除 Gemini 生成图片右下角的水印 Logo。
使用逆向混合算法还原原始像素。

用法:
    python3 tools/gemini_watermark_remover.py <图片路径>
    python3 tools/gemini_watermark_remover.py <图片路径> -o 输出路径.png

示例:
    python3 tools/gemini_watermark_remover.py projects/demo/images/bg_01.png
    python3 tools/gemini_watermark_remover.py image.jpg -o image_clean.jpg

依赖:
    pip install Pillow numpy

注意:
    - 支持 PNG、JPG、JPEG 格式
    - 自动检测水印尺寸（48px 或 96px）
    - 输出文件默认添加 _unwatermarked 后缀
"""

import sys
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

# 导入同目录模块
sys.path.insert(0, str(Path(__file__).parent))

# 算法参数
ALPHA_THRESHOLD = 0.002  # Alpha 阈值，低于此值不处理
MAX_ALPHA = 0.99  # 最大 Alpha 值，防止除零
LOGO_VALUE = 255  # Logo 像素值（白色）

# 水印背景图路径
SCRIPT_DIR = Path(__file__).parent
BG_48_PATH = SCRIPT_DIR / "assets" / "bg_48.png"
BG_96_PATH = SCRIPT_DIR / "assets" / "bg_96.png"


def detect_watermark_config(width: int, height: int) -> dict:
    """
    根据图片尺寸检测水印配置
    
    Args:
        width: 图片宽度
        height: 图片高度
    
    Returns:
        配置字典，包含 logo_size、margin_right、margin_bottom
    """
    if width > 1024 and height > 1024:
        return {"logo_size": 96, "margin_right": 64, "margin_bottom": 64}
    return {"logo_size": 48, "margin_right": 32, "margin_bottom": 32}


def calculate_watermark_position(width: int, height: int, config: dict) -> dict:
    """
    计算水印位置
    
    Args:
        width: 图片宽度
        height: 图片高度
        config: 水印配置
    
    Returns:
        位置字典，包含 x、y、width、height
    """
    logo_size = config["logo_size"]
    return {
        "x": width - config["margin_right"] - logo_size,
        "y": height - config["margin_bottom"] - logo_size,
        "width": logo_size,
        "height": logo_size,
    }


def calculate_alpha_map(bg_image: Image.Image) -> np.ndarray:
    """
    从水印背景图计算 Alpha 通道映射
    
    Args:
        bg_image: 水印背景 PNG 图片
    
    Returns:
        Alpha 映射数组（0-1 范围）
    """
    bg_array = np.array(bg_image.convert("RGB"), dtype=np.float32)
    max_channel = np.max(bg_array, axis=2)
    return max_channel / 255.0


def remove_watermark(image: Image.Image, alpha_map: np.ndarray, position: dict) -> Image.Image:
    """
    使用逆向混合算法去除水印
    
    Args:
        image: 原始图片
        alpha_map: Alpha 映射数组
        position: 水印位置
    
    Returns:
        去除水印后的图片
    """
    img_array = np.array(image.convert("RGBA"), dtype=np.float32)
    x, y, w, h = position["x"], position["y"], position["width"], position["height"]

    for row in range(h):
        for col in range(w):
            alpha = alpha_map[row, col]
            if alpha < ALPHA_THRESHOLD:
                continue
            alpha = min(alpha, MAX_ALPHA)
            one_minus_alpha = 1.0 - alpha

            img_y, img_x = y + row, x + col
            for c in range(3):
                watermarked = img_array[img_y, img_x, c]
                original = (watermarked - alpha * LOGO_VALUE) / one_minus_alpha
                img_array[img_y, img_x, c] = np.clip(original, 0, 255)

    return Image.fromarray(img_array.astype(np.uint8))


def process_image(input_path: Path, output_path: Path | None = None, verbose: bool = True) -> Path:
    """
    处理单张图片，去除水印
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径（可选）
        verbose: 是否输出详细信息
    
    Returns:
        输出文件路径
    """
    image = Image.open(input_path)
    width, height = image.size

    config = detect_watermark_config(width, height)
    position = calculate_watermark_position(width, height, config)

    if verbose:
        print(f"  图片尺寸: {width} x {height}")
        print(f"  水印尺寸: {config['logo_size']} x {config['logo_size']}")
        print(f"  水印位置: ({position['x']}, {position['y']})")

    bg_path = BG_96_PATH if config["logo_size"] == 96 else BG_48_PATH
    
    if not bg_path.exists():
        print(f"错误: 水印背景图不存在: {bg_path}")
        sys.exit(1)
    
    bg_image = Image.open(bg_path)
    alpha_map = calculate_alpha_map(bg_image)

    result = remove_watermark(image, alpha_map, position)

    if output_path is None:
        stem = input_path.stem
        suffix = input_path.suffix or ".png"
        output_path = input_path.parent / f"{stem}_unwatermarked{suffix}"

    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        result = result.convert("RGB")

    result.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master - Gemini 水印去除工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    %(prog)s projects/demo/images/bg_01.png
    %(prog)s image.jpg -o image_clean.jpg

说明:
    - 自动检测水印尺寸（大图 96px，小图 48px）
    - 支持 PNG、JPG、JPEG 格式
    - 默认输出文件添加 _unwatermarked 后缀
'''
    )
    
    parser.add_argument('input', type=Path, help='输入图片路径')
    parser.add_argument('-o', '--output', type=Path, default=None, help='输出图片路径')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')
    
    args = parser.parse_args()

    if not args.input.exists():
        print(f"错误: 文件不存在: {args.input}")
        sys.exit(1)

    verbose = not args.quiet
    if verbose:
        print("PPT Master - Gemini 水印去除工具")
        print("=" * 40)
        print(f"  输入文件: {args.input}")

    output = process_image(args.input, args.output, verbose=verbose)
    
    if verbose:
        print()
        print(f"[完成] 已保存: {output}")


if __name__ == "__main__":
    main()
