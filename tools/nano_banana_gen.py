#!/usr/bin/env python3
"""
Nano Banana Image Generator (Gemini Nano)
通过 Google GenAI API (Gemini) 生成高质量图片的工具。

连接方式:
  - 无 GEMINI_BASE_URL → 直连 Google 官方 API
  - 有 GEMINI_BASE_URL → 通过代理 API (使用相同的 Official 协议)

依赖:
  pip install google-genai Pillow
"""

import os
import sys
import time
import argparse
from google import genai
from google.genai import types

# 可选依赖: PIL (用于报告图片分辨率)
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Constants                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# Gemini 3.1 Flash Image 支持的全部宽高比 (含新增的 1:4, 4:1, 1:8, 8:1)
VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8",
    "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
]

# 官方文档: "512px", "1K", "2K", "4K" (必须大写 K)
VALID_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

# 默认模型
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"

# 重试配置
MAX_RETRIES = 3          # 最大重试次数
RETRY_BASE_DELAY = 10    # 首次重试等待 (秒)
RETRY_BACKOFF = 2        # 指数退避倍数


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Utilities                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

def save_binary_file(file_name: str, data: bytes):
    """保存二进制数据到文件"""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


def _resolve_output_path(prompt: str, output_dir: str = None,
                         filename: str = None, ext: str = ".png") -> str:
    """根据参数计算最终的输出文件路径"""
    if filename:
        file_name = os.path.splitext(filename)[0]
    else:
        safe = "".join(c for c in prompt if c.isalnum() or c in (' ', '_')).rstrip()
        safe = safe.replace(" ", "_").lower()[:30]
        file_name = safe or "generated_image"

    full_name = f"{file_name}{ext}"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, full_name)
    return full_name


def _normalize_image_size(image_size: str) -> str:
    """
    大小写容错: 将用户输入规范化为 API 接受的格式。
    例: "2k" → "2K", "4k" → "4K", "512PX" → "512px"
    """
    s = image_size.strip()
    upper = s.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return s


def _report_resolution(path: str):
    """尝试用 PIL 报告图片分辨率"""
    if HAS_PIL:
        try:
            img = PILImage.open(path)
            print(f"  Resolution:   {img.size[0]}x{img.size[1]}")
        except Exception:
            pass


def _is_rate_limit_error(e: Exception) -> bool:
    """判断异常是否为速率限制 (429) 错误"""
    err_str = str(e).lower()
    return "429" in err_str or "rate" in err_str or "quota" in err_str or "resource_exhausted" in err_str


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Image Generation — 统一生成逻辑 (Official / Proxy)              ║
# ╚══════════════════════════════════════════════════════════════════╝

def _generate_image(api_key: str, prompt: str, negative_prompt: str = None,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = None) -> str:
    """
    统一图像生成函数 (流式)。

    根据 base_url 是否存在自动选择连接方式:
      - 无 base_url → 直连 Google 官方 API
      - 有 base_url → 通过代理 API (使用相同的 Official 协议)

    使用 generate_content_stream 实现流式接收，提供实时进度反馈：
      - 显示已等待时长
      - 收到 chunk 时显示编号和数据大小
      - 保留最后一个 image chunk（最高质量）

    Returns:
        保存的图片文件路径

    Raises:
        RuntimeError: 生成失败时
    """
    # 根据是否有 base_url 创建 client
    if base_url:
        client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
    else:
        client = genai.Client(api_key=api_key)

    # Build prompt
    final_prompt = prompt
    if negative_prompt:
        final_prompt += f"\n\nNegative prompt: {negative_prompt}"

    config_kwargs = {
        "response_modalities": ["IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    }
    # ThinkingConfig 仅 flash 系列模型支持
    if "flash" in model.lower():
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_level="MINIMAL",
        )
    config = types.GenerateContentConfig(**config_kwargs)

    mode_label = "Proxy Mode" if base_url else "Official Mode"
    print(f"[{mode_label}]")
    if base_url:
        print(f"  Base URL:     {base_url}")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {final_prompt[:120]}{'...' if len(final_prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Image Size:   {image_size}")
    print()

    # Stream response for real-time progress feedback
    start_time = time.time()
    print(f"  ⏳ Generating...", end="", flush=True)

    # Heartbeat thread: print elapsed time every 5s while waiting
    import threading
    heartbeat_stop = threading.Event()

    def _heartbeat():
        while not heartbeat_stop.is_set():
            heartbeat_stop.wait(5)
            if not heartbeat_stop.is_set():
                elapsed = time.time() - start_time
                print(f" {elapsed:.0f}s...", end="", flush=True)

    hb_thread = threading.Thread(target=_heartbeat, daemon=True)
    hb_thread.start()

    last_image_data = None  # (PIL.Image or bytes, mime_type)
    chunk_count = 0
    total_bytes = 0

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=[final_prompt],
        config=config,
    ):
        elapsed = time.time() - start_time

        if chunk.parts is None:
            continue

        for part in chunk.parts:
            if part.text is not None:
                print(f"\n  Model says: {part.text}", end="", flush=True)
            elif part.inline_data is not None:
                chunk_count += 1
                data_size = len(part.inline_data.data) if part.inline_data.data else 0
                total_bytes += data_size
                size_str = f"{data_size / 1024:.0f}KB" if data_size < 1048576 else f"{data_size / 1048576:.1f}MB"
                print(f"\n  📦 Chunk #{chunk_count} received ({size_str}, {elapsed:.1f}s)", end="", flush=True)
                last_image_data = part

    # Stop heartbeat
    heartbeat_stop.set()
    hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  ✅ Stream complete ({elapsed:.1f}s, {chunk_count} chunk(s), {total_bytes / 1024:.0f}KB total)")

    if last_image_data is not None and last_image_data.inline_data is not None:
        if chunk_count > 1:
            print(f"  Keeping the final chunk (highest quality).")
        image = last_image_data.as_image()
        path = _resolve_output_path(prompt, output_dir, filename, ".png")
        image.save(path)
        print(f"File saved to: {path}")
        _report_resolution(path)
        return path

    raise RuntimeError("No image was generated. The server may have refused the request.")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Entry Point                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

def generate(prompt: str, negative_prompt: str = None,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = DEFAULT_MODEL,
             max_retries: int = MAX_RETRIES) -> str:
    """
    图像生成入口函数（带自动重试）。

    根据环境变量 GEMINI_BASE_URL 是否存在，自动选择连接方式:
      - 无 GEMINI_BASE_URL → 直连 Google 官方 API
      - 有 GEMINI_BASE_URL → 通过代理 API (使用相同的 Official 协议)

    遇到 429 Rate Limit 错误时自动指数退避重试。

    Args:
        prompt: 正向提示词
        negative_prompt: 负面提示词
        aspect_ratio: 宽高比
        image_size: 图片尺寸 ("512px", "1K", "2K", "4K", 大小写不敏感)
        output_dir: 输出目录
        filename: 输出文件名 (不含扩展名)
        model: 模型名称 (默认 gemini-3.1-flash-image-preview)
        max_retries: 最大重试次数

    Returns:
        保存的图片文件路径

    Raises:
        ValueError: 参数不合法时
        RuntimeError: 生成失败且重试耗尽时
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    base_url = os.environ.get("GEMINI_BASE_URL")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # 大小写容错
    image_size = _normalize_image_size(image_size)

    # Validate inputs
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect ratio '{aspect_ratio}'. Valid: {VALID_ASPECT_RATIOS}")

    if image_size not in VALID_IMAGE_SIZES:
        raise ValueError(f"Invalid image size '{image_size}'. Valid: {VALID_IMAGE_SIZES}")

    # ── Retry loop ──
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(api_key, prompt, negative_prompt,
                                   aspect_ratio, image_size, output_dir,
                                   filename, model, base_url)
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_rate_limit_error(e):
                delay = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                print(f"\n  ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                      f"Waiting {delay}s before retry...")
                time.sleep(delay)
            elif attempt < max_retries:
                delay = 5
                print(f"\n  ⚠️  Error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                      f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                break

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini Nano Banana."
    )
    parser.add_argument(
        "prompt", nargs="?", default="Nano Banana",
        help="The text prompt for image generation."
    )
    parser.add_argument(
        "--negative_prompt", "-n", default=None,
        help="Negative prompt to specify what to avoid."
    )
    parser.add_argument(
        "--aspect_ratio", default="1:1", choices=VALID_ASPECT_RATIOS,
        help=f"Aspect ratio. Choices: {VALID_ASPECT_RATIOS}. Default: 1:1."
    )
    parser.add_argument(
        "--image_size", default="1K",
        help=f"Image size. Choices: {VALID_IMAGE_SIZES}. Default: 1K. (case-insensitive)"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output directory. Default: current directory."
    )
    parser.add_argument(
        "--filename", "-f", default=None,
        help="Output filename (without extension). Overrides auto-naming."
    )
    parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL,
        help=f"Model name. Default: {DEFAULT_MODEL}."
    )

    args = parser.parse_args()

    try:
        generate(args.prompt, args.negative_prompt, args.aspect_ratio,
                 args.image_size, args.output, args.filename, args.model)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
