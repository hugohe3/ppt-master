#!/usr/bin/env python3
"""Validate dependency consistency across all three manifests.

Checks:
  1. Root pyproject.toml vs skill pyproject.toml — identical [project] dependencies
  2. Both pyproject.toml vs requirements.txt — same package names, compatible versions
  3. Both uv.lock files are byte-identical (same lock state)

Usage:
    uv run skills/ppt-master/scripts/check_deps_sync.py
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent

ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"
SKILL_PYPROJECT = SKILL_DIR / "pyproject.toml"
REQUIREMENTS_FILE = SKILL_DIR / "requirements.txt"
ROOT_UV_LOCK = REPO_ROOT / "uv.lock"
SKILL_UV_LOCK = SKILL_DIR / "uv.lock"


def parse_pyproject_deps(path: Path) -> dict[str, str]:
    """Extract {package_name: version_spec} from a pyproject.toml [project] dependencies list.

    Returns an empty dict if the file is missing.
    """
    if not path.exists():
        return {}

    with open(path, "rb") as f:
        data = tomllib.load(f)

    deps: dict[str, str] = {}
    for entry in data.get("project", {}).get("dependencies", []):
        # entry is a PEP 508 dependency string like "python-pptx>=0.6.21"
        match = re.match(r'^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*(.*)$', entry)
        if match:
            name = match.group(1).lower()
            constraint = match.group(2).strip()
            deps[name] = constraint
    return deps


def parse_requirements_txt(path: Path) -> dict[str, str]:
    """Extract {package_name: version_spec} from a requirements.txt file.

    Skips comments, blank lines, and option flags (--index-url etc.).
    Returns an empty dict if the file is missing.
    """
    if not path.exists():
        return {}

    deps: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        # "python-pptx>=0.6.21" or "python-pptx>=0.6.21  # comment"
        stripped = stripped.split("#")[0].strip()
        match = re.match(r'^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*(.*)$', stripped)
        if match:
            name = match.group(1).lower()
            constraint = match.group(2).strip()
            deps[name] = constraint
    return deps


def compare_pyproject_pair(
    root_deps: dict[str, str], skill_deps: dict[str, str]
) -> list[str]:
    """Compare two pyproject.toml dependency dicts. Returns list of error messages."""
    errors: list[str] = []

    root_names = set(root_deps)
    skill_names = set(skill_deps)

    if not root_deps:
        errors.append(f"  (file missing or has no dependencies: {ROOT_PYPROJECT})")
        return errors
    if not skill_deps:
        errors.append(f"  (file missing or has no dependencies: {SKILL_PYPROJECT})")
        return errors

    only_root = root_names - skill_names
    only_skill = skill_names - root_names

    for name in sorted(only_root):
        errors.append(
            f"  - {name}: present in root pyproject.toml, "
            f"missing from skills/ppt-master/pyproject.toml"
        )
    for name in sorted(only_skill):
        errors.append(
            f"  - {name}: present in skills/ppt-master/pyproject.toml, "
            f"missing from root pyproject.toml"
        )

    for name in sorted(root_names & skill_names):
        rv = root_deps[name]
        sv = skill_deps[name]
        if rv != sv:
            errors.append(
                f"  - {name}: version mismatch — "
                f'root has "{rv}", skill has "{sv}"'
            )

    return errors


def compare_req_vs_pyproject(
    req_deps: dict[str, str],
    pyproject_deps: dict[str, str],
    req_label: str,
    pyproject_label: str,
) -> list[str]:
    """Compare requirements.txt deps against a pyproject.toml. Returns error messages."""
    errors: list[str] = []

    req_names = set(req_deps)
    pp_names = set(pyproject_deps)

    if not req_deps:
        errors.append(f"  (file missing or has no dependencies: {req_label})")
        return errors
    if not pyproject_deps:
        errors.append(f"  (file missing or has no dependencies: {pyproject_label})")
        return errors

    only_req = req_names - pp_names
    only_pp = pp_names - req_names

    for name in sorted(only_req):
        errors.append(
            f"  - {name}: present in {req_label}, "
            f"missing from {pyproject_label}"
        )
    for name in sorted(only_pp):
        errors.append(
            f"  - {name}: present in {pyproject_label}, "
            f"missing from {req_label}"
        )

    for name in sorted(req_names & pp_names):
        rv = req_deps[name]
        pv = pyproject_deps[name]
        if rv != pv:
            errors.append(
                f'  - {name}: version mismatch — '
                f'{req_label} has "{rv}", {pyproject_label} has "{pv}"'
            )

    return errors


def check_lock_sync() -> list[str]:
    """Check that both uv.lock files are byte-identical."""
    errors: list[str] = []

    root_exists = ROOT_UV_LOCK.exists()
    skill_exists = SKILL_UV_LOCK.exists()

    if not root_exists and not skill_exists:
        errors.append("  Both uv.lock files are missing — run `uv lock` in each directory")
        return errors
    if not root_exists:
        errors.append(f"  {ROOT_UV_LOCK} is missing — run `uv lock` at repo root")
    if not skill_exists:
        errors.append(f"  {SKILL_UV_LOCK} is missing — run `uv lock` in skills/ppt-master/")

    if root_exists and skill_exists:
        root_bytes = ROOT_UV_LOCK.read_bytes()
        skill_bytes = SKILL_UV_LOCK.read_bytes()
        if root_bytes != skill_bytes:
            errors.append(
                "  uv.lock files differ byte-for-byte — run `uv lock` in both directories"
            )

    return errors


def main() -> int:
    exit_code = 0

    # --- Check 1: pyproject.toml pair ---
    print("=" * 60)
    print("1. root pyproject.toml  <->  skills/ppt-master/pyproject.toml")
    print("=" * 60)
    root_deps = parse_pyproject_deps(ROOT_PYPROJECT)
    skill_deps = parse_pyproject_deps(SKILL_PYPROJECT)
    errors = compare_pyproject_pair(root_deps, skill_deps)
    if errors:
        exit_code = 1
        print("FAIL — dependency mismatch:")
        for e in errors:
            print(e)
    else:
        print(f"OK   — {len(root_deps)} packages match")

    # --- Check 2: root pyproject.toml vs requirements.txt ---
    print()
    print("=" * 60)
    print("2. root pyproject.toml  <->  skills/ppt-master/requirements.txt")
    print("=" * 60)
    req_deps = parse_requirements_txt(REQUIREMENTS_FILE)
    errors = compare_req_vs_pyproject(
        req_deps, root_deps,
        req_label="requirements.txt",
        pyproject_label="root pyproject.toml",
    )
    if errors:
        exit_code = 1
        print("FAIL — dependency mismatch:")
        for e in errors:
            print(e)
    else:
        print(f"OK   — {len(req_deps)} packages match")

    # --- Check 3: skill pyproject.toml vs requirements.txt ---
    print()
    print("=" * 60)
    print("3. skills/ppt-master/pyproject.toml  <->  requirements.txt")
    print("=" * 60)
    errors = compare_req_vs_pyproject(
        req_deps, skill_deps,
        req_label="requirements.txt",
        pyproject_label="skills/ppt-master/pyproject.toml",
    )
    if errors:
        exit_code = 1
        print("FAIL — dependency mismatch:")
        for e in errors:
            print(e)
    else:
        print(f"OK   — {len(req_deps)} packages match")

    # --- Check 4: uv.lock byte-identity ---
    print()
    print("=" * 60)
    print("4. uv.lock  <->  skills/ppt-master/uv.lock")
    print("=" * 60)
    errors = check_lock_sync()
    if errors:
        exit_code = 1
        print("FAIL — lock drift:")
        for e in errors:
            print(e)
    else:
        root_size = ROOT_UV_LOCK.stat().st_size if ROOT_UV_LOCK.exists() else 0
        print(f"OK   — byte-identical ({root_size:,} bytes)")

    # --- Summary ---
    print()
    if exit_code == 0:
        print("All checks passed.")
    else:
        print("Fix the issues above, then run `uv lock` in both directories.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
