#!/usr/bin/env python3
import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

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


def build_parser():
    parser = argparse.ArgumentParser(
        description="Search external image providers and write a source manifest."
    )
    parser.add_argument("query", help="Search query for the external image provider.")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDER_REGISTRY),
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
    except ModuleNotFoundError:
        manifest_item = build_manifest_item(args)
    manifest_path = args.manifest or default_manifest_path(args.output)
    write_sources_manifest(manifest_path, [manifest_item])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
