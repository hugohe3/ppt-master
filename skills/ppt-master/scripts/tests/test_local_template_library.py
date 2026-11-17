#!/usr/bin/env python3
"""PPT Master - Local Template Registration and Installation Tests

Exercise both library scopes without writing into the distributed library.

Usage:
    python3 -m unittest tests.test_local_template_library

Examples:
    PYTHONPATH=skills/ppt-master/scripts python3 -m unittest tests.test_local_template_library

Dependencies:
    Standard library and the script runtime dependencies.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import apply_template  # noqa: E402
import register_template as register  # noqa: E402


class LocalTemplateLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.templates = self.root / "skill" / "templates"
        config = {
            kind: {
                **original,
                "dir": self.templates / original["dir"].name,
                "index": self.templates / original["dir"].name / original["index"].name,
            }
            for kind, original in register.KIND_CONFIG.items()
        }
        patched_config = patch.dict(register.KIND_CONFIG, config, clear=True)
        patched_config.start()
        self.addCleanup(patched_config.stop)
        for original in config.values():
            original["dir"].mkdir(parents=True)
            original["index"].write_text("{}\n", encoding="utf-8")

    def _style(self, template_id: str, scope: str = "local") -> Path:
        parent = self.templates / "styles"
        if scope == "local":
            parent = self.templates / "local" / "styles"
        workspace = parent / template_id
        shutil.copytree(
            SCRIPTS_DIR.parent / "templates" / "styles" / "incident-postmortem",
            workspace,
        )
        spec = workspace / "templates" / "design_spec.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("incident-postmortem", template_id),
            encoding="utf-8",
        )
        return workspace

    def _register(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["register_template.py", *args]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = register.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_default_local_and_explicit_builtin_keep_indexes_separate(self) -> None:
        for template_id, scope, flags in (
            ("personal", "local", []),
            ("official", "builtin", ["--builtin"]),
        ):
            with self.subTest(scope=scope):
                workspace = self._style(template_id, scope)
                code, stdout, stderr = self._register(template_id, "--kind", "style", *flags)
                self.assertEqual(code, 0, stderr)
                index = workspace.parent / "styles_index.json"
                self.assertIn(template_id, json.loads(index.read_text(encoding="utf-8")))
                prefix = "local/" if scope == "local" else ""
                self.assertIn(f"`templates/{prefix}styles/{template_id}/`", stdout)
        official = json.loads((self.templates / "styles/styles_index.json").read_text(encoding="utf-8"))
        self.assertEqual(set(official), {"official"})

    def test_safe_ids_preserve_unicode_and_reject_invalid_registration(self) -> None:
        for template_id in ("中国电信", "personal-v2.1", "a..b", "_draft"):
            with self.subTest(template_id=template_id):
                self.assertTrue(register.is_safe_template_id(template_id))
        for template_id in (None, 42, "", ".", "..", "has space", "trailing.", "a/b", "a\\b", "[id]"):
            with self.subTest(template_id=template_id):
                self.assertFalse(register.is_safe_template_id(template_id))
                if isinstance(template_id, str):
                    with self.assertRaises(SystemExit) as error:
                        self._register(template_id, "--kind", "style")
                    self.assertEqual(error.exception.code, 2)
        workspace = self._style("中国电信")
        code, _stdout, stderr = self._register("中国电信", "--kind", "style")
        self.assertEqual(code, 0, stderr)
        self.assertIn("中国电信", json.loads((workspace.parent / "styles_index.json").read_text(encoding="utf-8")))

    def test_rebuild_rejects_unsafe_directory_id_without_writing_index(self) -> None:
        workspace = self._style("has space")
        code, _stdout, stderr = self._register("--rebuild-all", "--kind", "style")
        self.assertEqual(code, 1)
        self.assertIn("unsafe template id", stderr)
        self.assertFalse((workspace.parent / "styles_index.json").exists())

    def test_collisions_refuse_single_registration_and_rebuild_in_both_directions(self) -> None:
        local = self._style("shared")
        official = self._style("shared", "builtin")
        for scope, index, flags in (
            ("local", official.parent / "styles_index.json", []),
            ("builtin", local.parent / "styles_index.json", ["--builtin"]),
        ):
            with self.subTest(scope=scope):
                for path in (official.parent / "styles_index.json", local.parent / "styles_index.json"):
                    path.write_text("{}\n", encoding="utf-8")
                index.write_text('{"shared": {"summary": "existing"}}\n', encoding="utf-8")
                for selection in (["shared"], ["--rebuild-all"]):
                    before = {path: path.read_bytes() for path in self.templates.rglob("*_index.json")}
                    code, _stdout, stderr = self._register(*selection, "--kind", "style", *flags)
                    self.assertEqual(code, 1)
                    self.assertIn("shared", stderr)
                    self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_old_location_error_explains_both_choices(self) -> None:
        self._style("old_location", "builtin")
        code, _stdout, stderr = self._register("old_location", "--kind", "style")
        self.assertEqual(code, 1)
        self.assertIn("--builtin", stderr)
        self.assertIn("templates/local/styles/old_location", stderr)

    def test_local_style_enforces_id_and_single_file_boundary(self) -> None:
        workspace = self._style("personal")
        register.validate_style_workspace(workspace)
        spec = workspace / "templates/design_spec.md"
        original = spec.read_text(encoding="utf-8")
        spec.write_text(original.replace("style_id: personal", "style_id: different"), encoding="utf-8")
        with self.assertRaises(register.SpecParseError):
            register.validate_style_workspace(workspace)
        spec.write_text(original, encoding="utf-8")
        (workspace / "images").mkdir()
        with self.assertRaises(register.SpecParseError):
            register.validate_style_workspace(workspace)

    def test_local_install_is_library_and_preserves_real_provenance(self) -> None:
        workspace = self._style("personal")
        code, _stdout, stderr = self._register("personal", "--kind", "style")
        self.assertEqual(code, 0, stderr)
        project = self.root / "project"
        (project / "templates").mkdir(parents=True)
        plan = apply_template.apply_templates(project, [str(workspace)], validate=False)
        self.assertEqual(plan.roots[0].source, "library")
        self.assertEqual(plan.roots[0].display, "skills/ppt-master/templates/local/styles/personal/")
        spec = project / "templates/design_spec.style.personal.md"
        self.assertIn(
            "> **Installed from**: `skills/ppt-master/templates/local/styles/personal/` (library)",
            spec.read_text(encoding="utf-8"),
        )

    def test_unregistered_local_workspace_is_explicit(self) -> None:
        workspace = self._style("personal")
        project = self.root / "project"
        (project / "templates").mkdir(parents=True)
        plan = apply_template.apply_templates(project, [str(workspace)], validate=False)
        self.assertEqual(plan.roots[0].source, "explicit")
