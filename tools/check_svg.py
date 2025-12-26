import xml.etree.ElementTree as ET
import os

# 遍历所有SVG文件
svg_dir = 'svg_output'
svg_files = [f for f in os.listdir(svg_dir) if f.endswith('.svg')]

print("检查SVG文件语法...")
print("=" * 50)

error_count = 0

for svg_file in svg_files:
    file_path = os.path.join(svg_dir, svg_file)
    try:
        # 解析SVG文件
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"✅ {svg_file}: 语法正确")
    except Exception as e:
        error_count += 1
        print(f"❌ {svg_file}: 语法错误 - {e}")

print("=" * 50)
print(f"检查完成！共检查 {len(svg_files)} 个文件，发现 {error_count} 个错误")
