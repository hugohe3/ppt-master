#!/usr/bin/env python3
"""
PPT Master - Dry-Run Prompt Export

Parses image_prompts.md and exports each image prompt to an individual
.txt file optimized for feeding directly to AI image generators
(ChatGPT, Midjourney, etc.).

Part of Path C in the image acquisition pipeline.
See references/image-generator.md §3.2 for the full workflow.

Usage:
    python3 scripts/dry_run_export.py <project_path>
    python3 scripts/dry_run_export.py <project_path> --output-dir custom-dir

Examples:
    python3 scripts/dry_run_export.py projects/my-ppt
    python3 scripts/dry_run_export.py projects/my-ppt --output-dir /tmp/prompts

Dependencies:
    None (only uses standard library)
"""

import argparse
import re
import sys
from pathlib import Path


def _sanitize_filename(filename: str) -> str:
    """Strip extension, replace spaces/unsafe chars with underscores, collapse, lowercase."""
    name = Path(filename).stem
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = name.strip("_").lower()
    return re.sub(r"_+", "_", name)


def _parse_image_blocks(text: str) -> list[dict]:
    """Parse all image blocks from image_prompts.md content."""
    blocks = []
    # Split on ### Image N: headings
    pattern = re.compile(
        r"###\s+Image\s+(\d+):\s*(.+?)(?=\n)",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))

    for match in matches:
        image_num = int(match.group(1))
        filename = match.group(2).strip()
        # Get the block text (from this heading to the next ### or end)
        start = match.end()
        end = matches[matches.index(match) + 1].start() if matches.index(match) + 1 < len(matches) else len(text)
        block_text = text[start:end]

        result = {
            "num": image_num,
            "filename": filename,
        }

        # Extract Purpose from table row
        purpose_match = re.search(r"\|\s*Purpose\s*\|\s*(.+?)\s*\|", block_text)
        result["purpose"] = purpose_match.group(1).strip() if purpose_match else ""

        # Extract Type from table row
        type_match = re.search(r"\|\s*Type\s*\|\s*(.+?)\s*\|", block_text)
        result["type"] = type_match.group(1).strip() if type_match else ""

        # Extract Prompt: everything between **Prompt**: and **Alt Text**:
        prompt_match = re.search(
            r"\*\*Prompt\*\*\s*:\s*\n(.*?)(?=\n\*\*Alt Text\*\*|\Z)",
            block_text,
            re.DOTALL,
        )
        result["prompt"] = prompt_match.group(1).strip() if prompt_match else ""

        # Extract Alt Text: the line(s) after **Alt Text**: that start with >
        alt_match = re.search(
            r"\*\*Alt Text\*\*\s*:\s*\n>\s*(.*?)(?=\n\n|\n###|\Z)",
            block_text,
            re.DOTALL,
        )
        result["alt_text"] = alt_match.group(1).strip() if alt_match else ""

        blocks.append(result)

    return blocks


def _format_txt(block: dict) -> str:
    """Format a single image prompt block as a .txt file for AI generators."""
    purpose = block.get("purpose", "")
    type_ = block.get("type", "")
    prompt = block.get("prompt", "")
    alt_text = block.get("alt_text", "")

    lines = [
        f"请生成一张图片，用于PPT的{purpose}。",
        "",
        f"Purpose: {purpose}",
        f"Type: {type_}",
        "",
        "Prompt:",
        prompt,
    ]
    if alt_text:
        lines.extend(["", "Alt Text:", alt_text])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Export image_prompts.md blocks to individual .txt files for AI image generators.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to the PPT project directory (must contain images/image_prompts.md)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Custom output directory (default: <project_path>/images/dry-run/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    prompts_path = args.project_path / "images" / "image_prompts.md"
    if not prompts_path.exists():
        print(f"Error: {prompts_path} not found", file=sys.stderr)
        return 1

    text = prompts_path.read_text(encoding="utf-8")
    blocks = _parse_image_blocks(text)

    if not blocks:
        print("Warning: no parseable image blocks found in image_prompts.md", file=sys.stderr)
        return 1

    out_dir = args.output_dir if args.output_dir else args.project_path / "images" / "dry-run"
    out_dir.mkdir(parents=True, exist_ok=True)

    exported = 0
    for block in blocks:
        try:
            sanitized = _sanitize_filename(block["filename"])
            padded = f"{block['num']:02d}_{sanitized}.txt"
            out_file = out_dir / padded
            out_file.write_text(_format_txt(block), encoding="utf-8")
            exported += 1
        except Exception as exc:
            print(f"Warning: skipping image {block['num']}: {exc}", file=sys.stderr)

    print(f"Exported {exported} prompt file(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
