#!/usr/bin/env python3
"""
PPT Master - Skill Attribution Guard

Fail closed when the distributed Skill attribution bundle or its execution
gates are missing or modified.

Usage:
    python3 "<absolute-skill-root>/scripts/attribution_guard.py"

Examples:
    python3 "/opt/agent-skills/ppt-master/scripts/attribution_guard.py"

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
from pathlib import Path


_ERROR_MESSAGE = (
    "PPT Master skill integrity check failed. Please use the complete official "
    "distribution without removing its attribution files."
)
_SKILL_DIR = Path(__file__).resolve().parent.parent
_EXACT_METADATA_VALUES = {
    "copyright": '"Copyright (c) 2025-2026 Hugo He"',
    "license": '"MIT"',
    "official_repository": '"https://github.com/hugohe3/ppt-master"',
}
_REQUIRED_METADATA_FIELDS = ("sponsors",)
_REQUIRED_ATTRIBUTION_FILES = ("LICENSE", "SPONSORS.md", "SPONSORS_CN.md")
_LICENSE_DIGEST = "80cefc234c1ec12a8cece4344f16300c634fa03df7891686fcf979e3828f0921"
_REQUIRED_GATE_FILES = (
    "scripts/console_encoding.py",
    "scripts/project_manager.py",
    "scripts/project_management/cli.py",
    "scripts/svg_quality_checker.py",
    "scripts/svg_quality/cli.py",
    "scripts/svg_to_pptx.py",
    "scripts/svg_to_pptx/pptx_package/cli.py",
    "scripts/register_template.py",
    "scripts/template_preview_pptx.py",
)
_SKILL_GATE_MARKER = 'python3 "${SKILL_DIR}/scripts/attribution_guard.py"'
_SECONDARY_GATE_FILE = "scripts/console_encoding.py"
_SECONDARY_GATE_NAME = "_require_official_distribution_identity"


def _normalized_bytes(path: Path) -> bytes:
    """Return UTF-8 text bytes with platform line endings normalized."""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _frontmatter(skill_text: str) -> str:
    """Return the opening YAML frontmatter or reject malformed input."""
    if not skill_text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = skill_text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    return skill_text[4:end]


def _metadata_is_valid() -> bool:
    """Require fixed identity values and each structural attribution field."""
    skill_text = _normalized_bytes(_SKILL_DIR / "SKILL.md").decode("utf-8")
    metadata = _frontmatter(skill_text)
    return (
        all(
            len(re.findall(
                rf"(?m)^  {re.escape(field)}\s*:\s*{re.escape(value)}\s*$",
                metadata,
            )) == 1
            for field, value in _EXACT_METADATA_VALUES.items()
        )
        and all(
            len(re.findall(rf"(?m)^  {re.escape(field)}\s*:", metadata)) == 1
            for field in _REQUIRED_METADATA_FIELDS
        )
        and skill_text.count(_SKILL_GATE_MARKER) == 1
    )


def _protected_files_are_valid() -> bool:
    """Require all attribution paths and the exact MIT license text."""
    for relative_path in _REQUIRED_ATTRIBUTION_FILES:
        path = _SKILL_DIR / relative_path
        if not path.is_file():
            return False
    license_digest = hashlib.sha256(_normalized_bytes(_SKILL_DIR / "LICENSE")).hexdigest()
    return license_digest == _LICENSE_DIGEST


def _is_zero_arg_call(node: ast.stmt, function_name: str) -> bool:
    """Return whether one statement directly invokes the named function."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == function_name
        and not node.value.args
        and not node.value.keywords
    )


def _is_gate_call(node: ast.stmt) -> bool:
    """Return whether one statement directly invokes the primary integrity gate."""
    return _is_zero_arg_call(node, "require_skill_integrity")


def _execution_gate_is_valid(path: Path) -> bool:
    """Require one live import and one live entry-point call."""
    tree = ast.parse(_normalized_bytes(path).decode("utf-8"), filename=str(path))
    has_import = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "attribution_guard"
        and any(alias.name == "require_skill_integrity" for alias in node.names)
        for node in tree.body
    )
    has_entry_call = False
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"configure_utf8_stdio", "main"}
        ):
            body = node.body[1:] if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ) else node.body
            has_entry_call = bool(body and _is_gate_call(body[0]))
        elif isinstance(node, ast.If) and any(_is_gate_call(statement) for statement in node.body):
            has_entry_call = True
    return has_import and has_entry_call


def _execution_gates_are_valid() -> bool:
    """Require every supported route to retain executable guard calls."""
    for relative_path in _REQUIRED_GATE_FILES:
        if not _execution_gate_is_valid(_SKILL_DIR / relative_path):
            return False
    return _secondary_execution_gate_is_valid(_SKILL_DIR / _SECONDARY_GATE_FILE)


def _secondary_execution_gate_is_valid(path: Path) -> bool:
    """Require the independent identity guard and its live bootstrap call."""
    tree = ast.parse(_normalized_bytes(path).decode("utf-8"), filename=str(path))
    has_guard = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == _SECONDARY_GATE_NAME
        for node in tree.body
    )
    for node in tree.body:
        if not (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "configure_utf8_stdio"
        ):
            continue
        body = node.body[1:] if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ) else node.body
        return (
            has_guard
            and len(body) >= 2
            and _is_gate_call(body[0])
            and _is_zero_arg_call(body[1], _SECONDARY_GATE_NAME)
        )
    return False


def _integrity_is_valid() -> bool:
    """Validate every local attribution and execution invariant."""
    return (
        _metadata_is_valid()
        and _protected_files_are_valid()
        and _execution_gates_are_valid()
    )


def require_skill_integrity() -> None:
    """Stop the active command with one generic message on any expected failure."""
    try:
        valid = _integrity_is_valid()
    except (OSError, SyntaxError, UnicodeError, ValueError):
        valid = False
    if valid:
        return
    print(_ERROR_MESSAGE, file=sys.stderr)
    raise SystemExit(78)


def build_parser() -> argparse.ArgumentParser:
    """Build the zero-argument integrity-check CLI parser."""
    return argparse.ArgumentParser(
        description="Validate the PPT Master Skill attribution and execution gates.",
    )


def main(argv: list[str] | None = None) -> int:
    """Run the fail-closed Skill integrity gate."""
    build_parser().parse_args(argv)
    require_skill_integrity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
