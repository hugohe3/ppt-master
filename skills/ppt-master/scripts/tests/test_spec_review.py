#!/usr/bin/env python3
"""Regression tests for lossless spec review, concurrent edits, and comment receipts."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_spec_annotations import main as check_main  # noqa: E402
from project_management.spec_blocks import replace_spec_block, split_spec_blocks  # noqa: E402
from project_specs import SCHEMA_DIR, validate_markdown_schema, validate_markdown_text  # noqa: E402
from spec_review.server import create_app, main as server_main  # noqa: E402
from spec_review.store import ReviewError, ReviewStore, sha256  # noqa: E402


SPEC = """<!-- ppt-master-schema: design-spec/v1 -->
# Complete 深度 - Design Spec

## I. Project Information
| Item | Value |
| --- | --- |
| Page Count | 2 |
| Design Spec Depth | complete |

## II. Canvas Specification
1280 × 720

## III. Visual Theme
### Theme Style
Long prose **with emphasis**.

## IV. Typography System
| Role | Font |
| --- | --- |
| Body | Arial |

## V. Layout Principles
Whitespace.

## VI. Icon Usage Specification
None.

## VIII. Image Resource List
None.

## IX. Content Outline
Introduction.
### Part 1 - Opening

#### Slide 01 - 开篇
- **Audience move**: Understand.
- **Relationships**: none
- A complete paragraph that can be changed.
  - A nested list.

| Region | Value |
| --- | --- |
| North | 12 |

### Part 2 - Closing

#### Slide 02 - Close
- **Audience move**: Decide.
- **Relationships**: none
- Closing paragraph.

## X. Speaker Notes Requirements
None.

"""
SCHEMA = SCHEMA_DIR / "design_spec.schema.json"


class SpecBlocksTests(unittest.TestCase):
    def test_lossless_round_trips(self):
        fenced = SPEC.replace("| Region | Value |", "```md\n## x\n#### Slide 99 - fake\n```\n\n| Region | Value |")
        tilde = SPEC.replace(
            "| Region | Value |", "~~~~md\n## x\n#### Slide 99 - fake\n~~~\n~~~~\n\n| Region | Value |",
        )
        for text in (SPEC, SPEC.replace("\n", "\r\n"), SPEC.rstrip("\n"), fenced, tilde, "preamble only"):
            with self.subTest(ending=repr(text[-8:]), fenced="fake" in text):
                layout = split_spec_blocks(text)
                joined = layout.preamble + "".join(text[block.start:block.end] for block in layout.blocks)
                self.assertEqual(joined.encode("utf-8"), text.encode("utf-8"))
                raw = text.encode("utf-8")
                for block in layout.blocks:
                    self.assertEqual(raw[block.byte_start:block.byte_end], text[block.start:block.end].encode("utf-8"))
                self.assertNotIn("slide:99", [block.key for block in layout.blocks])

    def test_block_order_and_part_ownership(self):
        layout = split_spec_blocks(SPEC)
        self.assertEqual([block.key for block in layout.blocks][-6:],
                         ["section:IX", "part:01", "slide:01", "part:02", "slide:02", "section:X"])
        parts = [block for block in layout.blocks if block.kind == "part"]
        self.assertEqual([SPEC[block.start:block.end] for block in parts],
                         ["### Part 1 - Opening\n\n", "### Part 2 - Closing\n\n"])
        slide = next(block for block in layout.blocks if block.key == "slide:01")
        self.assertNotIn("### Part 2", SPEC[slide.start:slide.end])
        self.assertEqual(slide.title, "#### Slide 01 - 开篇")

    def test_slide_headings_at_every_supported_level(self):
        for level in range(3, 7):
            with self.subTest(level=level):
                text = SPEC.replace("#### Slide 01", "#" * level + " Slide 01")
                layout = split_spec_blocks(text)
                slide = next(block for block in layout.blocks if block.key == "slide:01")
                self.assertEqual(slide.kind, "slide")
                self.assertEqual(len([block for block in layout.blocks if block.kind == "part"]), 2)
                self.assertEqual(layout.preamble + "".join(text[b.start:b.end] for b in layout.blocks), text)
                draft = text[slide.start:slide.end].replace("开篇", "New title")
                self.assertEqual(replace_spec_block(text, slide.key, draft), text.replace("开篇", "New title"))

    def test_non_slide_h3_is_part_regardless_of_title(self):
        text = SPEC.replace("### Part 1 - Opening", "### Introduction")
        block = next(block for block in split_spec_blocks(text).blocks if block.key == "part:01")
        self.assertEqual(block.kind, "part")
        self.assertEqual(text[block.start:block.end], "### Introduction\n\n")

    def test_replacement_changes_only_target_bytes(self):
        for text in (SPEC, SPEC.replace("\n", "\r\n"), SPEC.rstrip("\n")):
            with self.subTest(crlf="\r" in text):
                old = next(block for block in split_spec_blocks(text).blocks if block.key == "slide:01")
                draft = text[old.start:old.end].replace("开篇", "新的页名").replace("can be changed", "was changed")
                candidate = replace_spec_block(text, old.key, draft.replace("\r\n", "\n"))
                new = next(block for block in split_spec_blocks(candidate).blocks if block.key == old.key)
                self.assertEqual(text.encode()[:old.byte_start], candidate.encode()[:new.byte_start])
                self.assertEqual(text.encode()[old.byte_end:], candidate.encode()[new.byte_end:])
                if "\r" in text:
                    self.assertNotIn("\n", candidate.replace("\r\n", ""))

    def test_noop_preserves_mixed_endings_and_terminal_whitespace(self):
        text = SPEC.replace("Whitespace.\n", "Whitespace.\r\n")
        block = next(block for block in split_spec_blocks(text).blocks if block.key == "section:V")
        self.assertEqual(replace_spec_block(text, block.key, text[block.start:block.end].replace("\r\n", "\n")), text)
        for tail in ("", "\n", "\n\n", "\r\n \r\n"):
            text = SPEC.rstrip() + tail
            block = split_spec_blocks(text).blocks[-1]
            candidate = replace_spec_block(text, block.key, "## X. Speaker Notes Requirements\nChanged.\n\n\n")
            self.assertEqual(candidate[block.start:], "## X. Speaker Notes Requirements\nChanged." + tail)

    def test_structural_injection_and_heading_changes_rejected(self):
        block = next(block for block in split_spec_blocks(SPEC).blocks if block.key == "slide:02")
        original = SPEC[block.start:block.end]
        changes = [original + heading for heading in (
            "## Extra", "#### Slide 99 - Injected", "#### Slide 99  ", "### Part 3",
            "### Slide 99", "##### Slide 99 - Injected", "###### Slide 99 - Injected",
        )]
        changes += [original.replace("Slide 02", "Slide 03"), original.replace("#### Slide", "### Slide"),
                    "prefix\n" + original, original + "```\n"]
        for draft in changes:
            with self.subTest(draft=draft[-40:]), self.assertRaises(ValueError):
                replace_spec_block(SPEC, block.key, draft)

    def test_part_allows_only_title_text_edits(self):
        text = SPEC.replace("### Part 2 - Closing\n", "### Part 2 - Closing\nExisting part description.\n")
        for text in (text, text.replace("\n", "\r\n")):
            block = next(block for block in split_spec_blocks(text).blocks if block.key == "part:02")
            original = text[block.start:block.end]
            renamed = original.replace("Closing", "Final decisions").replace("\r\n", "\n")
            expected = text.replace("### Part 2 - Closing", "### Part 2 - Final decisions")
            self.assertEqual(replace_spec_block(text, block.key, renamed), expected)
            changes = [original + heading for heading in (
                "## Extra", "### Another part", "### Slide 99", "#### Slide 99", "New body text",
            )]
            changes += [
                original.replace("### Part", "#### Part"), original.replace("### Part 2 - Closing", "### Slide 99"),
                original.replace("Existing part description.", "Changed body."),
            ]
            for draft in changes:
                with self.subTest(draft=draft), self.assertRaises(ValueError):
                    replace_spec_block(text, block.key, draft)
        with self.assertRaisesRegex(ValueError, "section heading"):
            replace_spec_block(SPEC, "section:V", "## V. Renamed\nBody\n")

    def test_slide_injection_outside_ix_is_rejected(self):
        block = next(block for block in split_spec_blocks(SPEC).blocks if block.key == "section:V")
        for level in range(3, 7):
            with self.subTest(level=level), self.assertRaisesRegex(ValueError, "Structural heading"):
                replace_spec_block(SPEC, block.key, SPEC[block.start:block.end] + "#" * level + " Slide 99\n")

    def test_headings_inside_both_fences_can_be_edited(self):
        block = next(block for block in split_spec_blocks(SPEC).blocks if block.key == "slide:02")
        for fence in ("```", "~~~"):
            draft = SPEC[block.start:block.end] + (
                f"{fence}\n## x\n### Slide 99\n#### Slide 99 - fake\n### Part\n{fence}\n"
            )
            candidate = replace_spec_block(SPEC, block.key, draft)
            self.assertEqual(len(split_spec_blocks(candidate).blocks), len(split_spec_blocks(SPEC).blocks))


class ReviewServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "design_spec.md"
        self.path.write_bytes(SPEC.encode())
        self.app = create_app(str(self.root), idle_timeout=0)
        self.client = self.app.test_client()
        self.store = self.app.extensions["review_store"]

    def draft(self, key="slide:02", text=None):
        block = self.client.get(f"/api/blocks/{key}").get_json()
        response = self.client.put(f"/api/drafts/{key}", json={
            "sha256": block["sha256"], "text": text or block["text"].replace("Closing paragraph", "Edited paragraph"),
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def check(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = check_main([str(self.root), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_read_api_returns_raw_crlf_and_metadata(self):
        raw = SPEC.replace("\n", "\r\n").encode()
        self.path.write_bytes(raw)
        self.assertEqual(self.client.get("/api/health").get_json()["service"], "spec_review")
        document = self.client.get("/api/spec").get_json()
        self.assertEqual(document["text"].encode(), raw)
        self.assertEqual(document["sha256"], sha256(raw))
        blocks = self.client.get("/api/blocks").get_json()
        self.assertEqual(blocks["blocks"][-2]["key"], "slide:02")
        self.assertFalse(any(block["has_draft"] for block in blocks["blocks"]))

    def test_staging_and_discard_never_write_spec(self):
        before = self.path.read_bytes()
        draft = self.draft()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse((self.root / "spec_review" / "edits.jsonl").exists())
        result = self.client.delete("/api/drafts/slide:02", json={"version": draft["version"]})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(self.client.get("/api/blocks/slide:02").get_json()["draft"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_apply_crlf_and_history(self):
        self.path.write_bytes(SPEC.replace("\n", "\r\n").encode())
        block = self.client.get("/api/blocks/slide:02").get_json()
        draft = self.draft(text=block["text"].replace("Closing", "Edited").replace("\r\n", "\n"))
        result = self.client.post("/api/apply/slide:02", json=draft)
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual(result.get_json()["validation_errors"], [])
        self.assertNotIn(b"\n", self.path.read_bytes().replace(b"\r\n", b""))
        log = json.loads((self.root / "spec_review/edits.jsonl").read_text())
        self.assertEqual(log["before_sha256"], draft["sha256"])
        self.assertEqual(log["after_sha256"], sha256(self.path.read_bytes()))
        self.assertIn("Edited", log["after"])

    def test_apply_append_to_last_slide_of_part(self):
        block = self.client.get("/api/blocks/slide:01").get_json()
        self.assertNotIn("### Part 2", block["text"])
        draft = self.draft("slide:01", block["text"].rstrip() + "\nAdded at page end.\n\n")
        response = self.client.post("/api/apply/slide:01", json=draft)
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.path.read_bytes(),
                         SPEC.replace("| North | 12 |\n", "| North | 12 |\nAdded at page end.\n").encode())

    def test_sha_mismatch_is_409_and_draft_survives(self):
        draft = self.draft()
        self.path.write_bytes(self.path.read_bytes() + b"External change\n")
        before = self.path.read_bytes()
        result = self.client.post("/api/apply/slide:02", json=draft)
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.client.get("/api/blocks/slide:02").get_json()["draft"], draft)

    def test_external_block_removal_keeps_draft_accessible(self):
        draft = self.draft()
        block = next(block for block in split_spec_blocks(SPEC).blocks if block.key == "slide:02")
        self.path.write_bytes((SPEC[:block.start] + SPEC[block.end:]).encode())
        listing = self.client.get("/api/blocks").get_json()
        self.assertEqual(listing["orphan_drafts"][0]["key"], "slide:02")
        missing = self.client.get("/api/blocks/slide:02").get_json()
        self.assertTrue(missing["missing"])
        self.assertEqual(missing["draft"], draft)
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 409)
        discarded = self.client.delete("/api/drafts/slide:02", json={"version": draft["version"]})
        self.assertEqual(discarded.status_code, 200)

    def test_hold_is_423_and_resume_reports_revision(self):
        draft = self.draft()
        self.assertEqual(self.client.post("/api/hold", json={"hold": True}).status_code, 200)
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 423)
        released = self.client.post("/api/hold", json={"hold": False}).get_json()
        self.assertEqual(released["hold_revision"], 2)
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 200)

    def test_apply_rejects_structure_without_mutation(self):
        for heading in ("## Injected", "### Slide 99"):
            with self.subTest(heading=heading):
                draft = self.draft(text=f"#### Slide 02 - Close\n{heading}\nBody\n")
                before = self.path.read_bytes()
                result = self.client.post("/api/apply/slide:02", json=draft)
                self.assertEqual(result.status_code, 400)
                self.assertIn("Structural heading", result.get_json()["error"])
                self.assertEqual(self.path.read_bytes(), before)
                self.assertEqual(self.client.delete("/api/drafts/slide:02", json=draft).status_code, 200)

    def test_schema_errors_are_advisory_and_returned_unchanged(self):
        draft = self.draft(text="#### Slide 02 - Close\nMissing schema fields.\n")
        result = self.client.post("/api/apply/slide:02", json=draft)
        self.assertEqual(result.status_code, 200)
        errors = result.get_json()["validation_errors"]
        self.assertTrue(errors)
        self.assertEqual(errors, validate_markdown_schema(self.path, SCHEMA))
        self.assertIn(b"Missing schema fields.", self.path.read_bytes())
        self.assertFalse((self.root / "spec_lock.md").exists())

    def test_candidate_and_file_validation_match_without_reading_spec_lock(self):
        variants = (SPEC, SPEC.replace("\n", "\r\n"), "\ufeff" + SPEC,
                    "\ufeff\ufeff" + SPEC, SPEC.replace("design-spec/v1", "bad"))
        for text in variants:
            self.path.write_bytes(text.encode())
            disk = validate_markdown_schema(self.path, SCHEMA)
            if text.startswith("\ufeff\ufeff"):
                self.assertTrue(any("missing ppt-master-schema marker" in error for error in disk))
            read_text = Path.read_text

            def guarded(path, *args, **kwargs):
                self.assertNotIn(path.name, ("spec_lock.md", "design_spec.md"))
                return read_text(path, *args, **kwargs)

            with patch.object(Path, "read_text", guarded):
                self.assertEqual(validate_markdown_text(text, SCHEMA, markdown_path=self.path), disk)
        missing = self.root / "missing.schema.json"
        self.assertEqual(validate_markdown_text(text, missing, markdown_path=self.path),
                         validate_markdown_schema(self.path, missing))

    def test_comment_crud_is_sidecar_only(self):
        before = self.path.read_bytes()
        saved = self.client.post("/api/annotations", json={"key": "global", "body": "Full deck feedback"})
        self.assertEqual(saved.status_code, 201)
        item = saved.get_json()
        changed = self.client.put(
            f"/api/annotations/{item['id']}", json={"revision": item["revision"], "body": "New text"},
        )
        updated = changed.get_json()
        self.assertEqual(updated["spec_sha256"], sha256(before))
        self.assertNotEqual(updated["revision"], item["revision"])
        self.assertEqual(self.client.delete(f"/api/annotations/{item['id']}",
                                          json={"revision": item["revision"]}).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/annotations/{item['id']}",
                                          json={"revision": updated["revision"]}).status_code, 200)
        self.assertEqual(self.path.read_bytes(), before)
        events = [json.loads(line)["event"] for line in
                  (self.root / "spec_review/annotations.jsonl").read_text().splitlines()]
        self.assertEqual(events, ["saved", "updated", "removed"])

    def test_applied_unchanged_comment_is_removed_and_logged(self):
        item = self.store.save_annotation("slide:01", "Change the opening")
        self.assertEqual(self.check()[0], 0)
        self.assertEqual(self.check("--applied", item["id"])[0], 0)
        self.assertEqual(self.store.annotations(), [])
        self.assertIn('"event":"annotation_applied"', (self.root / "spec_review/annotations.jsonl").read_text())

    def test_applied_changed_comment_is_retained(self):
        item = self.store.save_annotation("slide:01", "Original")
        self.check()
        self.store.save_annotation("", "Updated", item["id"], item["revision"])
        code, output, errors = self.check("--applied", item["id"])
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("changed since it was listed", errors)
        self.assertEqual(self.store.annotations()[0]["body"], "Updated")

    def test_applied_unlisted_and_same_text_revisions_are_rejected(self):
        item = self.store.save_annotation("global", "Same text")
        self.assertEqual(self.check("--applied", item["id"])[0], 1)
        self.check()
        self.store.save_annotation("", item["body"], item["id"], item["revision"])
        self.assertEqual(self.check("--applied", item["id"])[0], 1)

    def test_applied_detects_manual_sidecar_change_without_revision_bump(self):
        item = self.store.save_annotation("global", "Original")
        self.check()
        path = self.root / "spec_review/annotations.json"
        data = json.loads(path.read_text())
        data["items"][0]["body"] = "Manually changed"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.check("--applied", item["id"])[0], 1)
        self.assertEqual(self.store.annotations()[0]["body"], "Manually changed")

    def test_todo_includes_hash_status_and_edit_summary_without_full_text(self):
        self.store.save_annotation("slide:02", "Review it")
        draft = self.draft()
        self.client.post("/api/apply/slide:02", json=draft)
        code, output, errors = self.check()
        self.assertEqual((code, errors), (0, ""))
        result = json.loads(output)
        self.assertTrue(result["annotations"][0]["block_changed"])
        self.assertFalse(result["annotations"][0]["block_missing"])
        self.assertEqual(set(result["edits"][0]), {"ts", "key", "title", "before_sha256", "after_sha256"})
        self.assertEqual(result["edits"][0]["before_sha256"], draft["sha256"][:12])
        self.assertEqual(result["edits"][0]["after_sha256"], sha256(self.path.read_bytes())[:12])
        self.assertNotIn("Edited paragraph", output)

    def test_ack_edits_consumes_only_last_listing_and_preserves_history(self):
        self.store.save_annotation("global", "Keep pending")
        draft = self.draft()
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 200)
        for _ in range(2):
            self.assertEqual(len(json.loads(self.check()[1])["edits"]), 1)
        # A new Apply after the listing must survive acknowledgement of that listing.
        draft = self.draft(text=self.store.block("slide:02")["text"].replace("Edited", "Edited again"))
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 200)
        log = self.root / "spec_review/edits.jsonl"
        history = log.read_bytes()
        self.assertEqual(self.check("--ack-edits")[0], 0)
        result = json.loads(self.check()[1])
        self.assertEqual(len(result["annotations"]), 1)
        self.assertEqual(len(result["edits"]), 1)
        self.assertEqual(result["edits"][0]["before_sha256"], draft["sha256"][:12])
        self.assertEqual(self.check("--ack-edits")[0], 0)
        self.assertEqual(json.loads(self.check()[1])["edits"], [])
        self.assertEqual(log.read_bytes(), history)
        self.assertEqual(ReviewStore(self.root).list_todo()["edits"], [])

    def test_ack_edits_requires_cli_listing(self):
        self.client.get("/api/annotations")
        code, output, errors = self.check("--ack-edits")
        self.assertEqual((code, output), (1, ""))
        self.assertIn("List direct edits before acknowledging", errors)

    def test_block_comment_baselines_ignore_edits_to_other_blocks(self):
        self.path.write_bytes(SPEC.replace("\n", "\r\n").encode())
        first = self.store.save_annotation("slide:01", "Opening feedback")
        second = self.store.save_annotation("slide:02", "Closing feedback")
        self.store.save_annotation("global", "Whole spec feedback")
        self.assertEqual(first["block_sha256"], sha256(self.store.block("slide:01")["text"].encode()))
        before = self.client.get("/api/annotations").get_json()["annotations"]
        self.assertFalse(before[0]["block_changed"])
        self.assertFalse(before[1]["block_changed"])
        self.assertTrue(before[2]["base_current"])
        draft = self.draft()
        self.assertEqual(self.client.post("/api/apply/slide:02", json=draft).status_code, 200)
        updated = self.store.save_annotation("", "Updated feedback", second["id"], second["revision"])
        self.assertEqual(updated["block_sha256"], second["block_sha256"])
        for items in (self.client.get("/api/annotations").get_json()["annotations"],
                      json.loads(self.check()[1])["annotations"]):
            self.assertFalse(items[0]["block_changed"])
            self.assertTrue(items[1]["block_changed"])
            self.assertFalse(items[0]["block_missing"])
            self.assertNotIn("base_current", items[0])
            self.assertFalse(items[2]["base_current"])
            self.assertNotIn("block_changed", items[2])

    def test_block_comment_unknown_and_missing_baselines(self):
        self.store.save_annotation("slide:01", "Legacy feedback")
        self.store.save_annotation("slide:02", "Missing block feedback")
        sidecar = self.root / "spec_review/annotations.json"
        data = json.loads(sidecar.read_text())
        del data["items"][0]["block_sha256"]
        sidecar.write_text(json.dumps(data), encoding="utf-8")
        block = next(block for block in split_spec_blocks(SPEC).blocks if block.key == "slide:02")
        self.path.write_bytes((SPEC[:block.start] + SPEC[block.end:]).encode())
        for items in (self.client.get("/api/annotations").get_json()["annotations"],
                      json.loads(self.check()[1])["annotations"]):
            self.assertIsNone(items[0]["block_changed"])
            self.assertFalse(items[0]["block_missing"])
            self.assertIsNone(items[1]["block_changed"])
            self.assertTrue(items[1]["block_missing"])

    def test_polling_and_health_do_not_refresh_activity(self):
        self.app.config["LAST_ACTIVITY"] = 10.0
        with patch("spec_review.server.time.monotonic", return_value=8000.0):
            for path in ("/api/state", "/api/state?poll=1", "/api/health"):
                for _ in range(2):
                    self.assertEqual(self.client.get(path).status_code, 200)
                    self.assertEqual(self.app.config["LAST_ACTIVITY"], 10.0)
            self.assertEqual(self.client.get("/api/blocks").status_code, 200)
            self.assertEqual(self.app.config["LAST_ACTIVITY"], 8000.0)
        with patch("spec_review.server.time.monotonic", return_value=9000.0):
            response = self.client.post("/api/annotations", json={"key": "global", "body": "Active"})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(self.app.config["LAST_ACTIVITY"], 9000.0)

    def test_shutdown_stops_service_without_applying_pending_draft(self):
        self.draft()
        before = self.path.read_bytes()
        response = self.client.post("/api/shutdown", json={})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.app.extensions["stop_event"].is_set())
        self.assertTrue(self.store.hold)
        self.assertEqual(self.path.read_bytes(), before)

    def test_two_applies_have_one_winner(self):
        draft = self.draft()

        def apply():
            try:
                self.store.apply("slide:02", draft["sha256"], draft["version"])
                return 200
            except ReviewError as exc:
                return exc.status

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: apply(), range(2)))
        self.assertEqual(sorted(results), [200, 409])
        self.assertEqual(len((self.root / "spec_review/edits.jsonl").read_text().splitlines()), 1)

    def test_other_block_draft_rebases_only_after_own_edit(self):
        first = self.draft("slide:01")
        second = self.draft("slide:02")
        result = self.client.post("/api/apply/slide:02", json=second).get_json()
        remaining = self.store.block("slide:01")["draft"]
        self.assertEqual(remaining["sha256"], result["sha256"])
        self.assertEqual(remaining["version"], first["version"])
        self.path.write_bytes(self.path.read_bytes() + b"external\n")
        self.assertNotEqual(self.store.block("slide:01")["sha256"], remaining["sha256"])

    def test_atomic_replace_failure_preserves_file_and_draft(self):
        draft = self.draft()
        before = self.path.read_bytes()
        with patch("spec_review.store.os.replace", side_effect=OSError("Replace failed")):
            response = self.client.post("/api/apply/slide:02", json=draft)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNotNone(self.store.block("slide:02")["draft"])
        self.assertEqual(list(self.root.glob(".design_spec.md.*")), [])

    def test_draft_versions_prevent_cross_tab_overwrite(self):
        draft = self.draft()
        response = self.client.put("/api/drafts/slide:02", json={"text": "lost", "sha256": draft["sha256"]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.store.block("slide:02")["draft"], draft)

    def test_host_origin_and_json_guards(self):
        for headers in ({"Host": "attacker.example"}, {"Origin": "null"}, {"Origin": "http://attacker.example"},
                        {"Origin": "http://localhost:7777"}):
            self.assertEqual(self.client.get("/api/state", headers=headers).status_code, 403)
        self.assertEqual(self.client.get("/api/state", headers={"Origin": "http://localhost"}).status_code, 200)
        self.assertEqual(self.client.post("/api/annotations", json=[]).status_code, 400)
        self.assertEqual(self.client.post("/api/hold", json={"hold": "on"}).status_code, 400)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("default-src 'none'", response.headers["Content-Security-Policy"])
        response.close()

    def test_cli_help_and_invalid_port_have_no_runtime_side_effect(self):
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            server_main(["--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(server_main([str(self.root), "--port", "0"]), 1)
        self.assertFalse((self.root / "spec_review").exists())

    def test_explicit_port_is_strict_and_foreground_releases_lock(self):
        httpd = Mock()
        with patch("spec_review.server._running", return_value=None), patch(
            "spec_review.server.make_server", return_value=httpd,
        ) as bind, patch("spec_review.server.find_free_port") as scan, patch(
            "spec_review.server.threading.Thread.start",
        ), patch("spec_review.server.signal.signal"), redirect_stdout(io.StringIO()):
            self.assertEqual(server_main([str(self.root), "--port", "6077", "--no-browser"]), 0)
        scan.assert_not_called()
        self.assertEqual(bind.call_args.args[:2], ("127.0.0.1", 6077))
        httpd.server_close.assert_called_once()
        self.assertFalse((self.root / "spec_review/lock.json").exists())

    def test_explicit_port_bind_failure_does_not_fall_back(self):
        with patch("spec_review.server._running", return_value=None), patch(
            "spec_review.server.make_server", side_effect=OSError("Address already in use"),
        ), patch("spec_review.server.find_free_port") as scan:
            self.assertEqual(server_main([str(self.root), "--port", "6077", "--no-browser"]), 1)
        scan.assert_not_called()
        self.assertFalse((self.root / "spec_review/lock.json").exists())

    def test_hold_cli_and_running_port_mismatch(self):
        with patch("spec_review.server._running", return_value={"pid": 1234, "port": 6077}), patch(
            "spec_review.server._call", return_value={"hold": True},
        ) as call, redirect_stdout(io.StringIO()):
            self.assertEqual(server_main([str(self.root), "--hold", "on"]), 0)
            call.assert_called_once_with(6077, "/api/hold", {"hold": True})
            self.assertEqual(server_main([str(self.root), "--port", "6088", "--no-browser"]), 1)
