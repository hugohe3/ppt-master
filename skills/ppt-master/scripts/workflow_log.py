#!/usr/bin/env python3
"""
PPT Master - Workflow Log

Append one manually selected important event to a project's cold audit log.

Usage:
    python3 scripts/workflow_log.py <project_path> <message>

Examples:
    python3 scripts/workflow_log.py projects/demo "Strategist handoff complete"
    python3 scripts/workflow_log.py projects/demo "Reworked P07 after source-label mismatch"

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

WORKFLOW_LOG_RELATIVE_PATH = Path("validation/workflow.log")


def _utc_timestamp() -> str:
    """Return a compact UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def workflow_log_path(project_path: str | Path) -> Path:
    """Return the canonical workflow-log path for a project."""
    return Path(project_path) / WORKFLOW_LOG_RELATIVE_PATH


def append_note(project_path: str | Path, message: str) -> Path:
    """Append one important event without interpreting workflow state."""
    log_path = workflow_log_path(project_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = (
        f"\n=== {_utc_timestamp()} NOTE id={uuid.uuid4().hex[:12]} ===\n"
        f"{message.rstrip()}\n"
    )
    with log_path.open(
        "a",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as handle:
        handle.write(record)
        handle.flush()
    return log_path


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Append one important event to validation/workflow.log.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Existing project directory")
    parser.add_argument("message", help="Concise important event")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = Path(args.project_path)
    if not project_path.is_dir():
        parser.error(f"project path does not exist: {project_path}")

    message = args.message.strip()
    if not message:
        parser.error("message must not be empty")
    try:
        log_path = append_note(project_path, message)
    except OSError as exc:
        print(
            f"[ERROR] Could not append workflow event to "
            f"{workflow_log_path(project_path)}: {exc}",
            file=sys.stderr,
        )
        return 1
    print(f"[OK] Workflow event appended: {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
