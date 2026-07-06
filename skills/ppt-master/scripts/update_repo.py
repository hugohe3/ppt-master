#!/usr/bin/env python3
"""PPT Master - Repository Updater

Pull the latest Git checkout and sync Python dependencies when requirements
change.

Usage:
    uv run skills/ppt-master/scripts/update_repo.py
    uv run skills/ppt-master/scripts/update_repo.py --skip-deps

Examples:
    uv run skills/ppt-master/scripts/update_repo.py
    uv run skills/ppt-master/scripts/update_repo.py --skip-deps

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"
PYPROJECT_FILE = REPO_ROOT / "pyproject.toml"


def non_git_checkout_message() -> str:
    return f"""This copy of PPT Master is not a Git checkout, so it cannot be updated automatically.

Repository path:
  {REPO_ROOT}

If you installed with Download ZIP:
  1. Download the latest ZIP from GitHub or AtomGit.
  2. Unzip it into a new folder.
  3. Copy your old .env and projects/ folder into the new folder.
  4. Run: pip install -r requirements.txt

If you want one-command updates next time, install with Git clone:
  git clone https://github.com/hugohe3/ppt-master.git

If you installed through a skill marketplace, update or reinstall through the
same marketplace / skills tool."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pull the latest repository changes and sync Python dependencies "
            "only when requirements.txt changes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip Python dependency sync even if requirements.txt changed.",
    )
    return parser.parse_args(argv)


def print_status(message: str = "") -> None:
    """Print progress/status messages to stderr."""
    print(message, file=sys.stderr)


def run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_git_available() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("Missing executable: git")


def ensure_git_checkout() -> None:
    if not (REPO_ROOT / ".git").exists():
        raise RuntimeError(non_git_checkout_message())


def ensure_uv_available() -> None:
    if shutil.which("uv") is None:
        raise RuntimeError("Missing executable: uv — install from https://docs.astral.sh/uv/getting-started/installation/")


def ensure_git_checkout() -> None:
    if not (REPO_ROOT / ".git").exists():
        raise RuntimeError(non_git_checkout_message())


def ensure_clean_tracked_worktree() -> None:
    status = run_command(["git", "status", "--porcelain", "--untracked-files=no"], check=False)
    if status.returncode != 0:
        details = (status.stderr or status.stdout or "").strip()
        raise RuntimeError(details or "Unable to inspect git status.")

    if status.stdout.strip():
        raise RuntimeError(
            "Tracked local changes detected. Please commit or stash them before running the update command."
        )


def get_head_revision() -> str:
    result = run_command(["git", "rev-parse", "HEAD"])
    return result.stdout.strip()


def sync_python_dependencies() -> None:
    if not REQUIREMENTS_FILE.exists() and not PYPROJECT_FILE.exists():
        print("Neither requirements.txt nor pyproject.toml found; skipping Python dependency sync.")
        return

    print("Dependency files changed. Syncing Python dependencies with uv...")
    result = run_command(["uv", "sync"])
    if result.stdout.strip():
        print_status(result.stdout.strip())
    if result.stderr.strip():
        print_status(result.stderr.strip())


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        ensure_git_checkout()
        ensure_git_available()
        ensure_uv_available()
        ensure_clean_tracked_worktree()

        before_head = get_head_revision()
        before_requirements = file_digest(REQUIREMENTS_FILE)
        before_pyproject = file_digest(PYPROJECT_FILE)

        print_status(f"Repository: {REPO_ROOT}")
        pull_result = run_command(["git", "pull", "--ff-only"])
        if pull_result.stdout.strip():
            print_status(pull_result.stdout.strip())
        if pull_result.stderr.strip():
            print_status(pull_result.stderr.strip())

        after_head = get_head_revision()
        after_requirements = file_digest(REQUIREMENTS_FILE)
        after_pyproject = file_digest(PYPROJECT_FILE)

        if before_head == after_head:
            print_status("Repository is already up to date.")
        else:
            print_status(f"Updated from {before_head[:7]} to {after_head[:7]}.")

        if args.skip_deps:
            print("Skipped Python dependency sync (--skip-deps).")
        elif before_requirements != after_requirements or before_pyproject != after_pyproject:
            sync_python_dependencies()
        else:
            print("Dependency files unchanged. Skipping Python dependency sync.")

        print_status(
            "Note: system dependencies such as Node.js and Pandoc still need "
            "to be installed manually."
        )
        return 0
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        print(details or "Command failed.", file=sys.stderr)
        return exc.returncode or 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
