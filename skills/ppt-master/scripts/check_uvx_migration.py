"""Check that changed files in a merge don't introduce old-style command calls.

Scans the diff between the merge commit's parents for any file that adds or
contains ``python3 scripts/``, ``python scripts/``, ``python3 skills/``, or
``python skills/`` patterns.  These should all be ``uvx ppt-master <cmd>``
after the uvx migration (v0.1.4+).

Exit codes:
    0 — clean (no old-style commands in changed files)
    1 — violations found
    2 — not a merge commit, skipped
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

OLD_PATTERNS = [
    (re.compile(r"python3\s+scripts/"), "python3 scripts/"),
    (re.compile(r"python\s+scripts/"), "python scripts/"),
    (re.compile(r"python3\s+skills/"), "python3 skills/"),
    (re.compile(r"python\s+skills/"), "python skills/"),
]

ALLOWED_FILES = {
    "skills/ppt-master/scripts/check_uvx_migration.py",
    "skills/ppt-master/scripts/check_cli_sync.py",
    ".github/workflows/check-uvx-migration.yml",
}

ALLOWED_DIRS = {
    "docs/superpowers/",
    "docs/zh/upstream-sync.md",
}

CHECK_EXTENSIONS = {".md", ".py", ".yml", ".yaml", ".toml", ".txt", ".rst", ".sh", ".ps1", ".cfg"}


def is_merge_commit(sha: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-p", sha],
        capture_output=True, text=True,
    )
    parents = [line for line in result.stdout.splitlines() if line.startswith("parent ")]
    return len(parents) >= 2


def get_changed_files(sha: str) -> list[str]:
    """Return list of files changed by merge commit *sha* (diff against first parent)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{sha}^1..{sha}"],
        capture_output=True, text=True,
    )
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def check_file(filepath: str) -> list[tuple[int, str, str]]:
    """Scan *filepath* for old-style command patterns.

    Returns list of (line_number, pattern_label, matched_line).
    """
    violations: list[tuple[int, str, str]] = []
    if not os.path.exists(filepath):
        return violations
    try:
        with open(filepath, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                for regex, label in OLD_PATTERNS:
                    if regex.search(line):
                        violations.append((lineno, label, line.rstrip("\n")))
    except (OSError, UnicodeDecodeError):
        pass
    return violations


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv

    sha = argv[1] if len(argv) > 1 else "HEAD"

    if not is_merge_commit(sha):
        print(f"[SKIP] {sha} is not a merge commit — nothing to check.")
        return 2

    changed = get_changed_files(sha)
    if not changed:
        print("[OK] No files changed in merge.")
        return 0

    checkable = [
        f for f in changed
        if os.path.splitext(f)[1].lower() in CHECK_EXTENSIONS
        and f not in ALLOWED_FILES
        and not any(f == ad or f.startswith(ad) for ad in ALLOWED_DIRS)
    ]

    if not checkable:
        print("[OK] No checkable files changed in merge.")
        return 0

    total_violations = 0
    for filepath in sorted(checkable):
        violations = check_file(filepath)
        if violations:
            total_violations += len(violations)
            print(f"\n[FAIL] {filepath}:")
            for lineno, label, line in violations:
                print(f"  L{lineno}: [{label}] {line}")

    if total_violations:
        print(f"\n[SUMMARY] {total_violations} old-style command(s) found in {len(changed)} changed file(s).")
        print("Replace with 'uvx ppt-master <subcommand>' (see cli.py COMMANDS dict).")
        return 1

    print(f"[OK] All {len(checkable)} changed file(s) clean — no old-style commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
