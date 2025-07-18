#!/usr/bin/env python3
"""
生成基本的应用程序图标

这个脚本会生成 Tauri 应用程序所需的基本图标文件。
在实际部署中，应该使用专业的图标设计。
"""

import os

from PIL import Image, ImageDraw


def create_simple_icon(size, output_path):
    """创建简单的图标"""
    # 创建图像
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 绘制简单的图标 - 一个带边框的圆形
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(52, 152, 219, 255),
        outline=(41, 128, 185, 255),
        width=2,
    )

    # 在中心绘制 "MCP" 文字
    try:
        # 尝试使用系统字体
        from PIL import ImageFont

        font_size = size // 4
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()
    except ImportError:
        font = None

    text = "MCP"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * (size // 8)
        text_height = size // 6

    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    # 保存图像
    img.save(output_path)
    print(f"已生成图标: {output_path}")


def main():
    """主函数"""
    icons_dir = "icons"
    os.makedirs(icons_dir, exist_ok=True)

    # 生成不同尺寸的 PNG 图标
    sizes = [32, 128, 256]
    for size in sizes:
        if size == 128:
            # 生成普通和 2x 版本
            create_simple_icon(size, f"{icons_dir}/{size}x{size}.png")
            create_simple_icon(size * 2, f"{icons_dir}/{size}x{size}@2x.png")
        else:
            create_simple_icon(size, f"{icons_dir}/{size}x{size}.png")

    # 为 Windows 创建 ICO 文件
    try:
        img_256 = Image.open(f"{icons_dir}/256x256.png")
        img_256.save(
            f"{icons_dir}/icon.ico",
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
        )
        print(f"已生成 Windows 图标: {icons_dir}/icon.ico")
    except Exception as e:
        print(f"生成 ICO 文件失败: {e}")

    # 为 macOS 创建 ICNS 文件（需要额外工具）
    print("注意：macOS ICNS 文件需要使用专门的工具生成")
    print("可以使用在线工具或 iconutil 命令将 PNG 转换为 ICNS")

    print("图标生成完成！")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("错误：需要安装 Pillow 库")
        print("请运行：pip install Pillow")
    except Exception as e:
        print(f"生成图标时发生错误: {e}")
