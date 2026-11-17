#!/usr/bin/env python3
"""PPT Master - Repository Updater

Pull the latest Git checkout and sync Python dependencies when the effective
requirements include tree changes.

Usage:
    python3 skills/ppt-master/scripts/update_repo.py
    python3 skills/ppt-master/scripts/update_repo.py --skip-pip

Examples:
    python3 skills/ppt-master/scripts/update_repo.py
    python3 skills/ppt-master/scripts/update_repo.py --skip-pip

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio
from register_template import KIND_CONFIG, get_library_paths, is_safe_template_id

configure_utf8_stdio()


TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"


def non_git_checkout_message() -> str:
    return f"""This copy of PPT Master is not a Git checkout, so it cannot be updated automatically.

Repository path:
  {REPO_ROOT}

If you installed with Download ZIP:
  1. Download the latest ZIP from GitHub or AtomGit.
  2. Unzip it into a new folder.
  3. Copy your old .env, projects/, and skills/ppt-master/templates/local/
     (if present) into the new folder.
  4. Run: pip install -r requirements.txt

If you want one-command updates next time, install with Git clone:
  git clone https://github.com/hugohe3/ppt-master.git

If you installed through a skill marketplace, update or reinstall through the
same marketplace / skills tool."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pull the latest repository changes and sync Python dependencies "
            "only when the requirements include tree changes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-pip",
        action="store_true",
        help="Skip Python dependency sync even if the requirements include tree changed.",
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


def _requirement_includes(path: Path, content: str) -> list[Path]:
    """Resolve local -r/--requirement includes relative to their owning file."""
    includes: list[Path] = []
    for raw_line in content.splitlines():
        try:
            tokens = shlex.split(raw_line, comments=True, posix=True)
        except ValueError:
            continue
        if not tokens:
            continue

        option = tokens[0]
        include_value: str | None = None
        if option in {"-r", "--requirement"}:
            if len(tokens) >= 2:
                include_value = tokens[1]
        elif option.startswith("--requirement="):
            include_value = option.partition("=")[2]
        elif option.startswith("-r") and len(option) > 2:
            include_value = option[2:].lstrip("=")

        if not include_value:
            continue
        include_path = Path(include_value)
        if not include_path.is_absolute():
            include_path = path.parent / include_path
        includes.append(include_path)
    return includes


def requirements_digest(path: Path) -> str | None:
    """Hash one requirements file and its recursive local include closure."""
    if not path.exists():
        return None

    digest = hashlib.sha256()
    visited: set[Path] = set()

    def visit(current: Path) -> None:
        try:
            resolved = current.resolve()
        except OSError as exc:
            raise RuntimeError(
                f"Unable to resolve requirements file {current}: {exc}"
            ) from exc
        if resolved in visited:
            digest.update(b"repeat\0")
            return
        visited.add(resolved)

        if not resolved.is_file():
            digest.update(b"missing\0")
            return
        try:
            content = resolved.read_bytes()
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read requirements file {resolved}: {exc}"
            ) from exc
        digest.update(b"file\0")
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        for included in _requirement_includes(
            resolved,
            content.decode("utf-8", errors="replace"),
        ):
            visit(included)

    visit(path)
    return digest.hexdigest()


def ensure_git_available() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("Missing executable: git")


def ensure_git_checkout() -> None:
    if not (REPO_ROOT / ".git").exists():
        raise RuntimeError(non_git_checkout_message())


def _read_json_object(content: str | bytes) -> dict:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Template index must be a JSON object")
    return data


def _same_json_value(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def _has_symlink_below(path: Path, repo_root: Path) -> bool:
    """Check only repository-internal segments, not system parent aliases."""
    current = repo_root
    for part in path.relative_to(repo_root).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _write_atomic(path: Path, content: bytes) -> None:
    """Replace one file only after its complete replacement is on disk."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _migrate_template_index(
    builtin_index: Path, local_dir: Path, local_index: Path, *, repo_root: Path,
) -> None:
    relative_index = builtin_index.relative_to(repo_root).as_posix()
    head = run_command(["git", "show", f"HEAD:{relative_index}"], check=False)
    if head.returncode:
        return
    try:
        if _has_symlink_below(builtin_index, repo_root) or _has_symlink_below(local_index, repo_root):
            return
        original_index = builtin_index.read_bytes()
        official = _read_json_object(head.stdout)
        current = _read_json_object(original_index)
        if any(
            key not in current or not _same_json_value(value, current[key])
            for key, value in official.items()
        ):
            return
        additions = {key: value for key, value in current.items() if key not in official}
        if not additions:
            return
        original_local = local_index.read_bytes() if local_index.exists() else None
        local = _read_json_object(original_local) if original_local is not None else {}
        moves = []
        for template_id, entry in additions.items():
            if not is_safe_template_id(template_id):
                return
            source = builtin_index.parent / template_id
            target = local_dir / template_id
            if (
                not source.is_dir()
                or source.is_symlink()
                or not (source / "templates" / "design_spec.md").is_file()
                or target.exists()
                or target.is_symlink()
                or (template_id in local and not _same_json_value(local[template_id], entry))
            ):
                return
            tracked = run_command(
                ["git", "--literal-pathspecs", "ls-files", "--", source.relative_to(repo_root).as_posix()],
                check=False,
            )
            if tracked.returncode or tracked.stdout.strip():
                return
            moves.append((source, target))
        local.update(additions)
        content = (json.dumps(local, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    except (OSError, UnicodeError, ValueError):
        return

    moved = []
    local_written = False
    checkout_started = False
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
        for source, target in moves:
            source.rename(target)
            moved.append((source, target))
        _write_atomic(local_index, content)
        local_written = True
        checkout_started = True
        run_command(["git", "checkout", "--", relative_index])
    except (OSError, subprocess.CalledProcessError) as exc:
        rollback_errors = []
        if checkout_started:
            try:
                _write_atomic(builtin_index, original_index)
            except OSError as rollback_exc:
                rollback_errors.append(f"restore {builtin_index}: {rollback_exc}")
        if local_written:
            try:
                if original_local is None:
                    local_index.unlink()
                else:
                    _write_atomic(local_index, original_local)
            except OSError as rollback_exc:
                rollback_errors.append(f"restore {local_index}: {rollback_exc}")
        for source, target in reversed(moved):
            try:
                target.rename(source)
            except OSError as rollback_exc:
                rollback_errors.append(f"restore {source} from {target}: {rollback_exc}")
        detail = "; ".join(rollback_errors)
        suffix = f" Rollback needs manual attention: {detail}." if detail else " Changes were rolled back."
        raise RuntimeError(
            f"Unable to migrate local templates from {relative_index}: {exc}.{suffix} "
            "Check the listed paths before retrying the update."
        ) from exc
    print_status(
        f"Migrated {len(moved)} local template(s) from {relative_index} to "
        f"{local_dir.relative_to(repo_root).as_posix()}/: {', '.join(sorted(additions))}"
    )


def migrate_legacy_local_templates() -> None:
    """Move only additive, unstaged user registrations out of official indexes."""
    status = run_command(["git", "status", "--porcelain", "--untracked-files=no"], check=False)
    if status.returncode:
        details = (status.stderr or status.stdout or "").strip()
        raise RuntimeError(details or "Unable to inspect git status.")
    unstaged = {line[3:] for line in status.stdout.splitlines() if line[:3] == " M "}
    repo_root = REPO_ROOT.resolve()
    templates_dir = repo_root / "skills" / "ppt-master" / "templates"
    for kind in KIND_CONFIG:
        _, builtin_index = get_library_paths(kind, "builtin", templates_dir=templates_dir)
        if builtin_index.relative_to(repo_root).as_posix() not in unstaged:
            continue
        local_dir, local_index = get_library_paths(kind, "local", templates_dir=templates_dir)
        _migrate_template_index(builtin_index, local_dir, local_index, repo_root=repo_root)


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
    if not REQUIREMENTS_FILE.exists():
        print_status("requirements.txt not found; skipping Python dependency sync.")
        return

    print_status("Requirements include tree changed. Syncing Python dependencies...")
    result = run_command([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    if result.stdout.strip():
        print_status(result.stdout.strip())
    if result.stderr.strip():
        print_status(result.stderr.strip())


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        ensure_git_checkout()
        ensure_git_available()
        migrate_legacy_local_templates()
        ensure_clean_tracked_worktree()

        before_head = get_head_revision()
        before_requirements = requirements_digest(REQUIREMENTS_FILE)

        print_status(f"Repository: {REPO_ROOT}")
        pull_result = run_command(["git", "pull", "--ff-only"])
        if pull_result.stdout.strip():
            print_status(pull_result.stdout.strip())
        if pull_result.stderr.strip():
            print_status(pull_result.stderr.strip())

        after_head = get_head_revision()
        after_requirements = requirements_digest(REQUIREMENTS_FILE)

        if before_head == after_head:
            print_status("Repository is already up to date.")
        else:
            print_status(f"Updated from {before_head[:7]} to {after_head[:7]}.")

        if args.skip_pip:
            print_status("Skipped Python dependency sync (--skip-pip).")
        elif before_requirements != after_requirements:
            sync_python_dependencies()
        else:
            print_status(
                "Requirements include tree unchanged. Skipping Python dependency sync."
            )

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
