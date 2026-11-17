#!/usr/bin/env python3
"""PPT Master - Local Template Migration Tests

Exercise additive legacy registrations and rollback through the updater CLI.

Usage:
    PYTHONPATH=skills/ppt-master/scripts python3 -m unittest tests.test_local_template_migration

Examples:
    PYTHONPATH=skills/ppt-master/scripts python3 -m unittest tests.test_local_template_migration

Dependencies:
    None (only uses standard library and Git)
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import update_repo


class LocalTemplateMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ppt-local-migration-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.templates = self.root / "skills" / "ppt-master" / "templates"
        self.builtin_dir = self.templates / "decks"
        self.builtin_index = self.builtin_dir / "decks_index.json"
        self.local_dir = self.templates / "local" / "decks"
        self.local_index = self.local_dir / "decks_index.json"
        self.official = {"official": {"summary": "Official deck", "page_count": 1}}
        self._write_json(self.builtin_index, self.official)
        (self.root / ".gitignore").write_text(
            "/skills/ppt-master/templates/local/\n", encoding="utf-8",
        )
        (self.root / "source.py").write_text("original\n", encoding="utf-8")
        self._git("init", "-q")
        self._git("add", ".")
        self._commit()
        self.original_official = self.builtin_index.read_bytes()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(update_repo, "REPO_ROOT", self.root).start()
        mock.patch.object(update_repo, "REQUIREMENTS_FILE", self.root / "requirements.txt").start()

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True,
            text=True, encoding="utf-8",
        ).stdout

    def _commit(self):
        tree = self._git("write-tree").strip()
        parent = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=self.root,
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        parents = ["-p", parent.stdout.strip()] if parent.returncode == 0 else []
        revision = self._git(
            "-c", "user.name=Template Test", "-c", "user.email=template@example.invalid",
            "commit-tree", tree, *parents, "-m", "Fixture",
        ).strip()
        self._git("update-ref", "HEAD", revision)

    def _write_json(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")

    def _legacy(self, template_id="legacy_user_deck"):
        root = self.builtin_dir / template_id
        (root / "templates").mkdir(parents=True)
        (root / "templates" / "design_spec.md").write_text("Legacy spec\n", encoding="utf-8")
        (root / "asset.bin").write_bytes(b"user asset\x00\xff")
        index = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        index[template_id] = {"summary": f"User deck {template_id}", "page_count": 1}
        self._write_json(self.builtin_index, index)
        return root

    def _update(self, *, checkout_error=False):
        output, errors = io.StringIO(), io.StringIO()
        original_run = update_repo.run_command
        commands = []

        def run(args, *, check=True):
            commands.append(args)
            if args == ["git", "pull", "--ff-only"]:
                return subprocess.CompletedProcess(args, 0, "Already up to date.\n", "")
            if checkout_error and args[:3] == ["git", "checkout", "--"]:
                raise subprocess.CalledProcessError(1, args, stderr="checkout failed")
            return original_run(args, check=check)

        with mock.patch.object(update_repo, "run_command", side_effect=run):
            with redirect_stdout(output), redirect_stderr(errors):
                result = update_repo.main(["--skip-pip"])
        self.assertEqual(output.getvalue(), "")
        return result, errors.getvalue(), commands

    def _assert_blocked(self):
        result, errors, commands = self._update()
        self.assertEqual(result, 1, errors)
        self.assertIn("Tracked local changes detected", errors)
        self.assertNotIn(["git", "pull", "--ff-only"], commands)
        return errors

    def test_additive_registration_migrates_and_allows_update(self) -> None:
        first = self._legacy("zeta")
        second = self._legacy("alpha")
        self._write_json(self.local_index, {"previous": {"summary": "Existing local deck"}})
        result, errors, commands = self._update()
        self.assertEqual(result, 0, errors)
        self.assertIn("Migrated 2 local template(s)", errors)
        self.assertIn(["git", "pull", "--ff-only"], commands)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertEqual((self.local_dir / "zeta" / "asset.bin").read_bytes(), b"user asset\x00\xff")
        self.assertEqual(self.builtin_index.read_bytes(), self.original_official)
        local = json.loads(self.local_index.read_text(encoding="utf-8"))
        self.assertEqual(list(local), ["alpha", "previous", "zeta"])
        self.assertEqual(
            self.local_index.read_text(encoding="utf-8"),
            json.dumps(local, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        self.assertEqual(self._git("status", "--porcelain", "--untracked-files=no"), "")

    def test_symlinked_repo_parent_allows_unicode_template_migration(self) -> None:
        legacy = self._legacy("中国电信")
        with tempfile.TemporaryDirectory(prefix="ppt-local-alias-") as alias_directory:
            parent_alias = Path(alias_directory) / "parent"
            parent_alias.symlink_to(self.root.parent, target_is_directory=True)
            with mock.patch.object(update_repo, "REPO_ROOT", parent_alias / self.root.name):
                result, errors, commands = self._update()
        self.assertEqual(result, 0, errors)
        self.assertIn("Migrated 1 local template(s)", errors)
        self.assertIn("skills/ppt-master/templates/local/decks/: 中国电信", errors)
        self.assertIn(["git", "pull", "--ff-only"], commands)
        self.assertFalse(legacy.exists())
        self.assertEqual((self.local_dir / "中国电信" / "asset.bin").read_bytes(), b"user asset\x00\xff")
        self.assertEqual(self.builtin_index.read_bytes(), self.original_official)
        self.assertIn("中国电信", json.loads(self.local_index.read_text(encoding="utf-8")))

    def test_changed_or_removed_official_entries_are_not_migrated(self) -> None:
        legacy = self._legacy()
        current = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        for replacement in ({"summary": "Changed"}, None, {"summary": "Official deck", "page_count": True}):
            with self.subTest(replacement=replacement):
                data = dict(current)
                if replacement is None:
                    del data["official"]
                else:
                    data["official"] = replacement
                self._write_json(self.builtin_index, data)
                self._assert_blocked()
                self.assertTrue(legacy.is_dir())
                self.assertFalse(self.local_index.exists())

    def test_all_four_template_kinds_migrate_independently(self) -> None:
        directories = ("brands", "styles", "layouts", "decks")
        for directory in directories[:-1]:
            index = self.templates / directory / f"{directory}_index.json"
            self._write_json(index, {})
            self._git("add", str(index))
        self._commit()
        for directory in directories:
            workspace = self.templates / directory / "personal" / "templates"
            workspace.mkdir(parents=True)
            (workspace / "design_spec.md").write_text("Personal spec\n", encoding="utf-8")
            index = self.templates / directory / f"{directory}_index.json"
            data = json.loads(index.read_text(encoding="utf-8"))
            self._write_json(index, {**data, "personal": {"summary": "Personal template"}})
        result, errors, _ = self._update()
        self.assertEqual(result, 0, errors)
        self.assertEqual(errors.count("Migrated 1 local template(s)"), 4)
        for directory in directories:
            self.assertTrue((self.templates / "local" / directory / "personal").is_dir())
            self.assertFalse((self.templates / directory / "personal").exists())
        self.assertEqual(self._git("status", "--porcelain", "--untracked-files=no"), "")

    def test_staged_index_is_not_migrated(self) -> None:
        legacy = self._legacy()
        self._git("add", str(self.builtin_index))
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertFalse(self.local_index.exists())
        self.builtin_index.write_text(self.builtin_index.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())

    def test_other_tracked_changes_still_block_pull_after_migration(self) -> None:
        self._legacy()
        source = self.root / "source.py"
        source.write_text("user edit\n", encoding="utf-8")
        self._assert_blocked()
        self.assertEqual(source.read_text(encoding="utf-8"), "user edit\n")
        self.assertTrue((self.local_dir / "legacy_user_deck").is_dir())

    def test_invalid_index_objects_are_not_migrated(self) -> None:
        legacy = self._legacy()
        for content in ("{", "[]", "null"):
            with self.subTest(content=content):
                self.builtin_index.write_text(content, encoding="utf-8")
                self._assert_blocked()
                self.assertTrue(legacy.is_dir())

    def test_invalid_head_object_is_not_migrated(self) -> None:
        self.builtin_index.write_text("[]\n", encoding="utf-8")
        self._git("add", str(self.builtin_index))
        self._commit()
        self._write_json(self.builtin_index, self.official)
        legacy = self._legacy()
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())

    def test_one_missing_workspace_prevents_the_entire_index_migration(self) -> None:
        legacy = self._legacy()
        current = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        current["missing"] = {"summary": "Missing workspace"}
        self._write_json(self.builtin_index, current)
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertFalse(self.local_index.exists())

    def test_tracked_workspace_is_not_migrated(self) -> None:
        legacy = self._legacy()
        self._git("add", str(legacy))
        self._commit()
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())

    def test_tracked_workspace_with_pathspec_characters_is_not_migrated(self) -> None:
        legacy = self._legacy("[legacy]")
        self._git("--literal-pathspecs", "add", str(legacy))
        self._commit()
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertFalse(self.local_index.exists())

    def test_unencodable_index_value_is_rejected_before_moving(self) -> None:
        legacy = self._legacy()
        current = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        current[legacy.name]["summary"] = "\ud800"
        self._write_json(self.builtin_index, current)
        original = self.builtin_index.read_bytes()
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertEqual(self.builtin_index.read_bytes(), original)
        self.assertFalse(self.local_index.exists())

    def test_unsafe_ids_are_not_migrated(self) -> None:
        legacy = self._legacy()
        base = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        for template_id in ("../outside", "a/b", "a\\b", ".", "C:outside", "has space", "trailing."):
            with self.subTest(template_id=template_id):
                self._write_json(self.builtin_index, {**base, template_id: {"summary": "Unsafe"}})
                self._assert_blocked()
                self.assertTrue(legacy.is_dir())

    def test_existing_target_is_never_overwritten(self) -> None:
        legacy = self._legacy()
        target = self.local_dir / legacy.name
        target.mkdir(parents=True)
        (target / "personal.txt").write_text("preserve\n", encoding="utf-8")
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertEqual((target / "personal.txt").read_text(encoding="utf-8"), "preserve\n")

    def test_conflicting_local_entry_is_not_overwritten(self) -> None:
        legacy = self._legacy()
        self._write_json(self.local_index, {legacy.name: {"summary": "Different local entry"}})
        original = self.local_index.read_bytes()
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertEqual(self.local_index.read_bytes(), original)

    def test_invalid_local_index_is_not_replaced(self) -> None:
        legacy = self._legacy()
        self.local_dir.mkdir(parents=True)
        for content in ("{", "[]", "null"):
            with self.subTest(content=content):
                self.local_index.write_text(content, encoding="utf-8")
                self._assert_blocked()
                self.assertTrue(legacy.is_dir())
                self.assertEqual(self.local_index.read_text(encoding="utf-8"), content)

    def test_matching_local_entry_without_workspace_can_be_migrated(self) -> None:
        legacy = self._legacy()
        data = json.loads(self.builtin_index.read_text(encoding="utf-8"))
        self._write_json(self.local_index, {legacy.name: data[legacy.name]})
        result, errors, _ = self._update()
        self.assertEqual(result, 0, errors)
        self.assertTrue((self.local_dir / legacy.name).is_dir())

    def test_local_symlink_escape_is_not_followed(self) -> None:
        legacy = self._legacy()
        outside = self.root / "outside"
        outside.mkdir()
        (self.templates / "local").symlink_to(outside, target_is_directory=True)
        self._assert_blocked()
        self.assertTrue(legacy.is_dir())
        self.assertEqual(list(outside.iterdir()), [])

    def test_failed_index_write_rolls_back_all_moved_workspaces(self) -> None:
        first, second = self._legacy("alpha"), self._legacy("beta")
        original = self.builtin_index.read_bytes()
        with mock.patch.object(update_repo, "_write_atomic", side_effect=OSError("disk full")):
            result, errors, commands = self._update()
        self.assertEqual(result, 1)
        self.assertIn("rolled back", errors)
        self.assertNotIn(["git", "pull", "--ff-only"], commands)
        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())
        self.assertEqual(self.builtin_index.read_bytes(), original)
        self.assertFalse(self.local_index.exists())

    def test_failed_second_move_rolls_back_the_first(self) -> None:
        first, second = self._legacy("alpha"), self._legacy("beta")
        original_rename = Path.rename

        def rename(path, target):
            if path == second:
                raise OSError("move failed")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", rename):
            result, errors, _ = self._update()
        self.assertEqual(result, 1)
        self.assertIn("rolled back", errors)
        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())
        self.assertFalse(self.local_index.exists())

    def test_failed_checkout_restores_both_indexes_and_workspace(self) -> None:
        legacy = self._legacy()
        self._write_json(self.local_index, {"existing": {"summary": "Preserve"}})
        original_local = self.local_index.read_bytes()
        original_builtin = self.builtin_index.read_bytes()
        result, errors, commands = self._update(checkout_error=True)
        self.assertEqual(result, 1)
        self.assertIn("rolled back", errors)
        self.assertNotIn(["git", "pull", "--ff-only"], commands)
        self.assertTrue(legacy.is_dir())
        self.assertEqual(self.local_index.read_bytes(), original_local)
        self.assertEqual(self.builtin_index.read_bytes(), original_builtin)

    def test_zip_upgrade_message_preserves_local_templates(self) -> None:
        self.assertIn("skills/ppt-master/templates/local/", update_repo.non_git_checkout_message())
        self.assertIn("if present", update_repo.non_git_checkout_message())
