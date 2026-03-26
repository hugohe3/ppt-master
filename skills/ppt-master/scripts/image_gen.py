#!/usr/bin/env python3
"""
Unified Image Generation Tool

Dispatches to the appropriate backend (Gemini or OpenAI) based on configuration.

Backend selection (IMAGE_BACKEND env var):
  IMAGE_BACKEND=gemini  -> Gemini backend (google-genai SDK)
  IMAGE_BACKEND=openai  -> OpenAI-compatible backend (openai SDK)
  (not set)             -> Auto-detect: use Gemini if GEMINI_API_KEY is present

Environment variables:
  IMAGE_BACKEND    (optional) "gemini" or "openai"
  IMAGE_API_KEY    (required) API key for the selected backend
  IMAGE_BASE_URL   (optional) Custom API endpoint
  IMAGE_MODEL      (optional) Model name override

  Legacy support (Gemini only):
    GEMINI_API_KEY / GEMINI_BASE_URL still work when IMAGE_BACKEND is not set.

Usage:
  python3 image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o images/
"""

import os
import sys
import argparse
from pathlib import Path

# Load .env from project root (if python-dotenv is installed)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

# All aspect ratios accepted by the unified CLI
# (each backend validates its own subset internally)
ALL_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8",
    "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
]

ALL_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]


def _resolve_backend():
    """
    Determine which backend to use based on environment variables.

    Returns:
        A backend module with a generate() function.
    """
    backend_name = os.environ.get("IMAGE_BACKEND", "").strip().lower()

    if backend_name == "gemini":
        import backend_gemini
        return backend_gemini, "gemini"

    if backend_name == "openai":
        import backend_openai
        return backend_openai, "openai"

    if backend_name and backend_name not in ("gemini", "openai"):
        print(f"Error: Unknown IMAGE_BACKEND='{backend_name}'. Supported: gemini, openai")
        sys.exit(1)

    # Auto-detect: IMAGE_BACKEND not set
    # Check for IMAGE_API_KEY first, then legacy keys
    if os.environ.get("IMAGE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        import backend_gemini
        return backend_gemini, "gemini"

    if os.environ.get("OPENAI_API_KEY"):
        import backend_openai
        return backend_openai, "openai"

    print(
        "Error: No image backend configured.\n"
        "\n"
        "Set environment variables:\n"
        "  IMAGE_BACKEND=gemini    # or openai\n"
        "  IMAGE_API_KEY=your-key\n"
        "\n"
        "Or for legacy Gemini usage:\n"
        "  GEMINI_API_KEY=your-key\n"
    )
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using AI (Gemini or OpenAI backend)."
    )
    parser.add_argument(
        "prompt", nargs="?", default="a beautiful landscape",
        help="The text prompt for image generation."
    )
    parser.add_argument(
        "--negative_prompt", "-n", default=None,
        help="Negative prompt to specify what to avoid."
    )
    parser.add_argument(
        "--aspect_ratio", default="1:1", choices=ALL_ASPECT_RATIOS,
        help=f"Aspect ratio. Default: 1:1."
    )
    parser.add_argument(
        "--image_size", default="1K",
        help=f"Image size. Choices: {ALL_IMAGE_SIZES}. Default: 1K. (case-insensitive)"
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
        "--model", "-m", default=None,
        help="Model name. Default depends on backend."
    )
    parser.add_argument(
        "--backend", "-b", default=None, choices=["gemini", "openai"],
        help="Override IMAGE_BACKEND env var."
    )

    args = parser.parse_args()

    # CLI --backend overrides env var
    if args.backend:
        os.environ["IMAGE_BACKEND"] = args.backend

    backend, backend_name = _resolve_backend()
    print(f"Using backend: {backend_name}\n")

    try:
        backend.generate(
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            output_dir=args.output,
            filename=args.filename,
            model=args.model,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
