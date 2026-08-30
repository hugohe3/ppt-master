#!/usr/bin/env python3
"""Focused tests for spec-lock forbidden-row provenance."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_management.project_specs import (  # noqa: E402
    SCHEMA_DIR,
    default_spec_lock_forbidden,
    validate_markdown_schema,
    validate_project_artifacts,
)


_SPEC_LOCK_V1_MARKER = "<!-- ppt-master-schema: spec-lock/v1 -->"


def _spec_lock_text(
    extra_forbidden: tuple[str, ...] = (),
    *,
    marker: str | None = _SPEC_LOCK_V1_MARKER,
) -> str:
    forbidden = "\n".join(
        f"- {row}"
        for row in sorted(default_spec_lock_forbidden()) + list(extra_forbidden)
    )
    marker_line = f"{marker}\n" if marker is not None else ""
    return f"""{marker_line}# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: Engineers
- objective: Explain the validator contract
- core_message: User prohibitions retain provenance
- consumption_mode: presentation

## mode
- mode: briefing

## visual_style
- visual_style: editorial

## colors
- bg: #FFFFFF

## typography
- font_family: Arial
- body: 24
- title: 36

## icons
- library: none
- inventory: none

## page_rhythm
- P01: anchor

## pptx_structure
- mode: flat
- template_reuse_scope: style

## forbidden
{forbidden}
"""


class SpecLockForbiddenTests(unittest.TestCase):
    def _validate(
        self,
        extra_forbidden: tuple[str, ...] = (),
        *,
        marker: str | None = _SPEC_LOCK_V1_MARKER,
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "fixture_ppt169_20260830"
            project.mkdir()
            lock_path = project / "spec_lock.md"
            lock_path.write_text(
                _spec_lock_text(extra_forbidden, marker=marker),
                encoding="utf-8",
            )
            return validate_markdown_schema(
                lock_path,
                SCHEMA_DIR / "spec_lock.schema.json",
            )

    def test_baseline_only_lock_passes(self) -> None:
        self.assertEqual(self._validate(), [])

    def test_user_tagged_extra_row_passes(self) -> None:
        self.assertEqual(
            self._validate(("不要用任何阴影和发光 (user)",)),
            [],
        )

    def test_versioned_legacy_baseline_anchors_pass(self) -> None:
        rows = (
            "Legacy `<style>` baseline wording",
            "Legacy `<foreignObject>` baseline wording",
            "Legacy HTML named entities baseline wording",
            "Legacy Mixing icon libraries baseline wording",
            "Legacy rgba() baseline wording",
            "Legacy <g opacity baseline wording",
        )
        for row in rows:
            with self.subTest(row=row):
                self.assertEqual(self._validate((row,)), [])

    def test_versioned_untagged_extra_row_fails(self) -> None:
        row = "不要用任何阴影和发光"
        expected = (
            "spec_lock.md forbidden: row "
            f"{len(default_spec_lock_forbidden()) + 1} is not a baseline rule "
            f"and lacks the (user) tag: {row}"
        )

        self.assertEqual(
            self._validate((row,), marker=_SPEC_LOCK_V1_MARKER),
            [expected],
        )

    def test_legacy_untagged_extra_row_has_no_forbidden_error(self) -> None:
        row = "不要用任何阴影和发光"
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "fixture_ppt169_20260830"
            project.mkdir()
            (project / "spec_lock.md").write_text(
                _spec_lock_text((row,), marker=None),
                encoding="utf-8",
            )

            errors, warnings = validate_project_artifacts(
                project,
                project_info={"format": "ppt169"},
                include_design=False,
            )

        self.assertFalse(
            any(error.startswith("spec_lock.md forbidden:") for error in errors)
        )
        self.assertTrue(
            any("legacy artifact has no ppt-master-schema marker" in warning
                for warning in warnings)
        )


if __name__ == "__main__":
    unittest.main()
