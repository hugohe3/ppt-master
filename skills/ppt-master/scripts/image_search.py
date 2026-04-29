#!/usr/bin/env python3
import argparse
import importlib
import json
from datetime import datetime, timezone

from image_sources.provider_common import ensure_json_parent


PROVIDER_REGISTRY = {
    "openverse": "image_sources.provider_openverse",
    "wikimedia": "image_sources.provider_wikimedia",
    "pexels": "image_sources.provider_pexels",
    "pixabay": "image_sources.provider_pixabay",
}

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
        default="",
        help="Preferred local filename for the selected image.",
    )
    parser.add_argument(
        "--manifest",
        default="image_sources.json",
        help="Output path for the sources manifest JSON file.",
    )
    return parser


def load_provider(provider_name):
    module_name = PROVIDER_REGISTRY[provider_name]
    return importlib.import_module(module_name)


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


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    item = {
        "query": args.query,
        "provider": args.provider,
    }
    if args.filename:
        item["filename"] = args.filename

    write_sources_manifest(args.manifest, [item])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
