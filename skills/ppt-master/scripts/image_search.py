#!/usr/bin/env python3
import argparse
import importlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from image_sources.notes_writer import append_image_credits
from image_sources.provider_common import ensure_json_parent


PROVIDER_REGISTRY = {
    "openverse": "image_sources.provider_openverse",
    "wikimedia": "image_sources.provider_wikimedia",
    "pexels": "image_sources.provider_pexels",
    "pixabay": "image_sources.provider_pixabay",
}

ORIENTATION_CHOICES = ("any", "landscape", "portrait", "square")

LICENSE_VERIFICATION_NOTE = (
    "provider metadata used; manual review recommended for external delivery"
)


def available_providers():
    return tuple(PROVIDER_REGISTRY)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Search external image providers and write a source manifest."
    )
    parser.add_argument("query", help="Search query for the external image provider.")
    parser.add_argument(
        "--provider",
        choices=available_providers(),
        default="openverse",
        help="Provider to use for the search.",
    )
    parser.add_argument(
        "--filename",
        required=True,
        help="Deterministic local filename for the selected image.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory for acquired images and the default manifest path.",
    )
    parser.add_argument(
        "--slide",
        default="",
        help="Slide identifier associated with the requested image.",
    )
    parser.add_argument(
        "--purpose",
        default="",
        help="Usage purpose for the requested image.",
    )
    parser.add_argument(
        "--orientation",
        choices=ORIENTATION_CHOICES,
        default="any",
        help="Preferred image orientation.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Optional explicit output path for the sources manifest JSON file.",
    )
    return parser


def load_provider(provider_name):
    module_name = PROVIDER_REGISTRY[provider_name]
    return importlib.import_module(module_name)


def _print_cli_error(message):
    print(message, file=sys.stderr)


def default_manifest_path(output_dir):
    return Path(output_dir) / "image_sources.json"


def write_sources_manifest(path, items):
    manifest_path = ensure_json_parent(path)
    payload = {
        "license_verification": LICENSE_VERIFICATION_NOTE,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": list(items),
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def infer_project_root(output_dir):
    output_path = Path(output_dir)
    if output_path.name == "images":
        return output_path.parent
    return None


def note_path_for_slide(project_root, slide):
    slide_name = Path(str(slide)).name
    slide_stem = Path(slide_name).stem
    if re.fullmatch(r"\d+", slide_stem):
        slide_name = f"slide{int(slide_stem):02d}.md"
    elif not slide_name.endswith(".md"):
        slide_name = f"{slide_name}.md"
    return Path(project_root) / "notes" / slide_name


def write_note_attribution(output_dir, slide, attribution_text):
    if not slide or not attribution_text:
        return None
    project_root = infer_project_root(output_dir)
    if project_root is None:
        _print_cli_error(
            "Skipping note attribution: --output must point to the project's "
            f"'images' directory, got {output_dir!r}"
        )
        return None
    note_path = note_path_for_slide(project_root, slide)
    return append_image_credits(note_path, [attribution_text])


def build_manifest_item(args):
    return {
        "filename": args.filename,
        "provider": args.provider,
        "search_query": args.query,
        "slide": args.slide,
        "purpose": args.purpose,
        "orientation": args.orientation,
        "source_page_url": "",
        "download_url": "",
        "author": "",
        "license_name": "",
        "license_url": "",
        "attribution_required": False,
        "attribution_text": "",
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        provider = load_provider(args.provider)
        manifest_item = provider.search_and_download(
            query=args.query,
            output_dir=args.output,
            filename=args.filename,
            slide=args.slide,
            purpose=args.purpose,
            orientation=args.orientation,
        )
    except ModuleNotFoundError as exc:
        _print_cli_error(f"Provider '{args.provider}' is unavailable: {exc}")
        return 1
    except RuntimeError as exc:
        _print_cli_error(f"Image search failed for provider '{args.provider}': {exc}")
        return 1

    manifest_path = args.manifest or default_manifest_path(args.output)
    write_sources_manifest(manifest_path, [manifest_item])
    write_note_attribution(
        output_dir=args.output,
        slide=args.slide,
        attribution_text=manifest_item.get("attribution_text", ""),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
