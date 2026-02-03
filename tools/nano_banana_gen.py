#!/usr/bin/env python3
"""
Nano Banana Image Generator (Gemini Nano)
通过 Google GenAI API (Gemini Nano) 生成高质量图片的工具。

支持功能:
- 高达 4K 分辨率的图像生成
- 自定义宽高比 (16:9, 4:3, 1:1, 9:16 等)
- 负面提示词支持 (通过 Prompt 工程实现)
- 自动保存为 PNG 格式
- 环境变量配置 (安全优先)

依赖:
  pip install google-genai
"""

import os
import json
import base64
import argparse
import mimetypes
from google import genai
from google.genai import types

# Predefined configuration presets
VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", 
    "4:5", "5:4", "9:16", "16:9", "21:9"
]
VALID_IMAGE_SIZES = ["1K", "2K", "4K"]


def save_binary_file(file_name: str, data: bytes):
    """保存二进制数据到文件"""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


def generate(prompt: str, negative_prompt: str = None, 
             aspect_ratio: str = "1:1", image_size: str = "4K", 
             output_dir: str = None):
    """
    调用 Gemini API 生成图像
    
    Args:
        prompt: 正向提示词
        negative_prompt: 负面提示词 (可选)
        aspect_ratio: 图片宽高比 (默认 1:1)
        image_size: 图片尺寸 (1K, 2K, 4K)
        output_dir: 输出目录 (可选，默认为当前目录)
    """
    # Load configuration
    # Priority: Environment Variables > Config File
    
    api_key = os.environ.get("GEMINI_API_KEY")
    base_url = os.environ.get("GEMINI_BASE_URL")
    
    config_path = os.path.join(os.path.dirname(__file__), "nano_banana_config.json")
    
    # If config file exists, load it directly to supplement missing env vars or as fallback
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                if not api_key:
                    api_key = config.get("api_key")
                if not base_url:
                    base_url = config.get("base_url")
        except Exception as e:
            print(f"Warning: Error reading configuration file: {e}")

    if not api_key:
        print("Error: API Key not found. Please set GEMINI_API_KEY env var or valid config file.")
        return

    # Validate aspect_ratio
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        print(f"Error: Invalid aspect ratio '{aspect_ratio}'. Valid options: {VALID_ASPECT_RATIOS}")
        return

    # Validate image_size
    size_upper = str(image_size).upper()
    if size_upper not in VALID_IMAGE_SIZES:
        print(f"Error: Invalid image size '{image_size}'. Valid options: {VALID_IMAGE_SIZES}")
        return

    client = genai.Client(
        api_key=api_key,
        http_options={
            'base_url': base_url
        }
    )

    base_model = "gemini-3-pro-image-preview"
    model = base_model

    # Handle image size model selection (2K or 4K adds suffix, 1K is default/no suffix)
    if size_upper in ["2K", "4K"]:
        model += f"-{size_upper.lower()}"

    # Handle Aspect Ratio in model name (e.g. -16x9)
    # This assumes the backend routes specific model names to specific aspect ratio pipelines
    if aspect_ratio:
        ratio_suffix = aspect_ratio.replace(":", "x")
        model += f"-{ratio_suffix}"

    # Append aspect ratio to prompt for models that support prompt-based config
    prompt_with_config = f"{prompt} --ar {aspect_ratio}"
    
    # Structure the prompt to include negative prompt if provided
    # Note: While some APIs have a dedicated negative_prompt field, putting it in the text 
    # is a robust fallback for this specific client wrapper if the field isn't exposed.
    # We will try to pass it clearly in the text.
    final_prompt_text = prompt_with_config
    if negative_prompt:
        # Common convention for text-to-image prompts
        final_prompt_text += f"\n\nNegative prompt: {negative_prompt}"
    
    print(f"Generating image with prompt: '{final_prompt_text}'")
    print(f"Using Model: {model}")
    print(f"Configuration: Aspect Ratio={aspect_ratio}, Size={image_size}")
    
    parts = [types.Part.from_text(text=final_prompt_text)]
    
    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
        ],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            output_mime_type="image/png",
        ),
    )

    file_index = 0
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            part = chunk.candidates[0].content.parts[0]
            if part.inline_data and part.inline_data.data:
                # Use a descriptive filename based on prompt (sanitized) or default
                # We use the ORIGINAL prompt for naming, not the one with flags
                safe_prompt = "".join([c for c in prompt if c.isalnum() or c in (' ', '_')]).rstrip()
                safe_prompt = safe_prompt.replace(" ", "_").lower()[:30] # Increased length
                if not safe_prompt:
                    safe_prompt = "generated_image"
                
                file_name = f"{safe_prompt}_{file_index}"
                file_index += 1
                inline_data = part.inline_data
                data_buffer = inline_data.data
                
                # specific handling for requested mime type, though guess_extension is usually good
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                # Clean up extension (mimetypes can return .jpe for jpeg)
                if file_extension in ['.jpe', '.jpeg']:
                     file_extension = '.jpg'
                
                file_name_with_ext = f"{file_name}{file_extension}"
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    full_path = os.path.join(output_dir, file_name_with_ext)
                else:
                    full_path = file_name_with_ext
                save_binary_file(full_path, data_buffer)
            else:
                pass # Text content or other non-image content
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate images using Gemini Nano Banana.")
    parser.add_argument("prompt", nargs="?", default="Nano Banana", help="The text prompt for image generation.")
    parser.add_argument(
        "--negative_prompt", "-n",
        default=None,
        help="Negative prompt to specify what to avoid in the image."
    )
    parser.add_argument(
        "--aspect_ratio", 
        default="1:1", 
        choices=VALID_ASPECT_RATIOS,
        help=f"Aspect ratio of the generated image. Choices: {VALID_ASPECT_RATIOS}. Default is '1:1'."
    )
    parser.add_argument(
        "--image_size", 
        default="4K", 
        choices=VALID_IMAGE_SIZES,
        help=f"Size of the generated image. Choices: {VALID_IMAGE_SIZES}. Default is '4K'."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for generated images. If not specified, saves to current directory."
    )

    args = parser.parse_args()
    
    generate(args.prompt, args.negative_prompt, args.aspect_ratio, args.image_size, args.output)
