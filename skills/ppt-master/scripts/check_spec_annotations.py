#!/usr/bin/env python3
"""
PPT Master - Spec Annotation Checker

Print compact JSON to-dos and unread direct-edit summaries; acknowledge listed
edits or unchanged comments. See scripts/docs/spec_review.md.

Usage:
    python3 scripts/check_spec_annotations.py <project_path> [--applied ID | --ack-edits]

Examples:
    python3 scripts/check_spec_annotations.py projects/example
    python3 scripts/check_spec_annotations.py projects/example --applied abc123
    python3 scripts/check_spec_annotations.py projects/example --ack-edits

Dependencies:
    None (only uses the standard library and local project modules)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from spec_review.store import ReviewStore  # noqa: E402

configure_utf8_stdio()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_path")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--applied", metavar="ID")
    actions.add_argument("--ack-edits", action="store_true", help="Consume direct edits from the last CLI listing")
    args = parser.parse_args(argv)
    store = ReviewStore(Path(args.project_path))
    try:
        store.document()
        if args.applied:
            store.remove_annotation(args.applied, applied=True)
            result = {"applied": args.applied}
        elif args.ack_edits:
            result = {"edits_cursor": store.ack_edits()}
        else:
            result = store.list_todo()
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
