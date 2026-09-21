#!/usr/bin/env python3
"""
PPT Master - Spec Review Storage

Serialize annotation transactions and stage lossless edits of one Design Spec.
See scripts/docs/spec_review.md for the sidecars and HTTP contract.

Usage:
    Import ReviewStore from this module.

Examples:
    store = ReviewStore(project_path)

Dependencies:
    None (only uses the standard library and local project modules)
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from project_management.project_specs import SCHEMA_DIR, validate_markdown_text
from project_management.spec_blocks import replace_spec_block, split_spec_blocks


class ReviewError(ValueError):
    """Report an actionable HTTP/CLI conflict without losing pending work."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def sha256(data: bytes) -> str:
    """Hash exactly the bytes on disk."""
    return hashlib.sha256(data).hexdigest()


def timestamp() -> str:
    """Return an unambiguous UTC event time."""
    return datetime.now(timezone.utc).isoformat()


def _annotation_fingerprint(item: dict) -> str:
    return sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode("utf-8"))


@contextmanager
def file_mutex(path: Path) -> Iterator[None]:
    """Hold a cross-process lock, released by the OS even after a crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_write(path: Path, data: bytes) -> None:
    """Flush a sibling temporary file and atomically replace its destination."""
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class ReviewStore:
    """Keep drafts in memory and comments in one process-safe sidecar."""

    def __init__(self, project: Path):
        self.project = project.resolve()
        self.path = self.project / "design_spec.md"
        self.runtime = self.project / "spec_review"
        self.mutex = threading.RLock()
        self.drafts: dict[str, dict] = {}
        self.hold = False
        self.hold_revision = 0

    def _read(self) -> tuple[bytes, str, str]:
        raw = self.path.read_bytes()
        return raw, raw.decode("utf-8"), sha256(raw)

    def _append(self, filename: str, record: dict) -> None:
        self.runtime.mkdir(parents=True, exist_ok=True)
        with (self.runtime / filename).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @contextmanager
    def _annotations(self) -> Iterator[dict]:
        with self.mutex, file_mutex(self.runtime / "storage.guard"):
            path = self.runtime / "annotations.json"
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"items": [], "listed": {}}
            if not isinstance(data, dict) or not isinstance(data.get("items"), list) or not isinstance(
                data.get("listed"), dict
            ):
                raise ValueError("Invalid annotations.json; repair the sidecar before continuing.")
            yield data

    def _save_annotations(self, data: dict) -> None:
        atomic_write(
            self.runtime / "annotations.json",
            (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )

    def state(self) -> dict:
        """Return the current disk hash and handoff state."""
        with self.mutex:
            _, _, digest = self._read()
            return {"sha256": digest, "hold": self.hold, "hold_revision": self.hold_revision}

    def snapshot(self) -> dict:
        """Return ordered block metadata and per-block pending status."""
        with self.mutex, self._annotations() as data:
            _, text, digest = self._read()
            pending = {item["key"] for item in data["items"]}
            blocks = [
                {**asdict(block), "has_annotations": block.key in pending, "has_draft": block.key in self.drafts}
                for block in split_spec_blocks(text).blocks
            ]
            live_keys = {block["key"] for block in blocks}
            orphans = [
                {"key": key, "title": draft["title"], "kind": "missing", "has_draft": True,
                 "has_annotations": key in pending}
                for key, draft in self.drafts.items() if key not in live_keys
            ]
            return {
                "sha256": digest, "hold": self.hold, "hold_revision": self.hold_revision,
                "blocks": blocks, "global_annotations": "global" in pending,
                "draft_keys": list(self.drafts),
                "orphan_drafts": orphans,
            }

    def document(self) -> dict:
        """Read the full raw spec without universal-newline translation."""
        with self.mutex:
            _, text, digest = self._read()
            return {"text": text, "sha256": digest}

    def block(self, key: str) -> dict:
        """Return original block text and its separate in-memory draft."""
        with self.mutex:
            _, text, digest = self._read()
            block = next((block for block in split_spec_blocks(text).blocks if block.key == key), None)
            if block is None:
                if key in self.drafts:
                    draft = self.drafts[key]
                    return {"key": key, "title": draft["title"], "text": "", "sha256": digest,
                            "draft": draft, "missing": True}
                raise ReviewError("Block no longer exists; reload the spec.", 404)
            return {**asdict(block), "text": text[block.start:block.end], "sha256": digest,
                    "draft": self.drafts.get(key)}

    def stage(self, key: str, text: str, base: str, version: str | None) -> dict:
        """Stage text without touching the spec; preserve stale drafts for review."""
        with self.mutex:
            block = self.block(key)
            current = self.drafts.get(key)
            if (current or {}).get("version") != version:
                raise ReviewError("Another tab changed this draft; reload before editing it.", 409)
            if base != block["sha256"] and (not current or current["sha256"] != base):
                raise ReviewError("The spec changed on disk; reload. Your local draft is retained.", 409)
            draft = {"text": text, "sha256": base, "version": uuid.uuid4().hex, "title": block["title"]}
            self.drafts[key] = draft
            return draft

    def discard(self, key: str, version: str | None) -> None:
        """Discard only the draft version the browser actually saw."""
        with self.mutex:
            if (self.drafts.get(key) or {}).get("version") != version:
                raise ReviewError("Another tab changed this draft; reload before discarding it.", 409)
            self.drafts.pop(key, None)

    def set_hold(self, enabled: bool) -> dict:
        """Wait for any active Apply, then switch the write handoff state."""
        with self.mutex:
            if self.hold != enabled:
                self.hold_revision += 1
            self.hold = enabled
            return self.state()

    def apply(self, key: str, base: str, version: str) -> dict:
        """Compare, validate, and atomically replace one byte range under a lock."""
        with self.mutex, file_mutex(self.runtime / "storage.guard"):
            if self.hold:
                raise ReviewError("AI is editing; Apply is paused until hold is off.", 423)
            raw, text, digest = self._read()
            draft = self.drafts.get(key)
            if base != digest or (draft and draft["sha256"] != digest):
                raise ReviewError("The spec changed on disk; reload. The draft is retained.", 409)
            if not draft or draft["version"] != version:
                raise ReviewError("The staged draft changed; reload before applying it.", 409)
            try:
                candidate = replace_spec_block(text, key, draft["text"])
            except ValueError as exc:
                raise ReviewError(str(exc)) from exc
            blocks = split_spec_blocks(text).blocks
            before = next(block for block in blocks if block.key == key)
            after = next(block for block in split_spec_blocks(candidate).blocks if block.key == key)
            new_text = candidate[after.start:after.end]
            payload = raw[:before.byte_start] + new_text.encode("utf-8") + raw[before.byte_end:]
            errors = validate_markdown_text(candidate, SCHEMA_DIR / "design_spec.schema.json", markdown_path=self.path)
            if sha256(self.path.read_bytes()) != digest:
                raise ReviewError("The spec changed during validation; reload. The draft is retained.", 409)
            new_digest = sha256(payload)
            if payload != raw:
                atomic_write(self.path, payload)
                self._append("edits.jsonl", {
                    "ts": timestamp(), "key": key, "title": after.title,
                    "before": text[before.start:before.end], "after": new_text,
                    "before_sha256": digest, "after_sha256": new_digest,
                })
            del self.drafts[key]
            # Other blocks were byte-identical; our own successful edit does not
            # invalidate their drafts. External edits never take this path.
            for remaining in self.drafts.values():
                if remaining["sha256"] == digest:
                    remaining["sha256"] = new_digest
            return {"sha256": new_digest, "validation_errors": errors, "saved": True}

    def annotations(self) -> list[dict]:
        """Read comments without acknowledging them on behalf of an agent."""
        with self._annotations() as data:
            _, text, digest = self._read()
            return self._current_annotations(data, text, digest)

    def _current_annotations(self, data: dict, text: str, digest: str) -> list[dict]:
        block_hashes = {
            block.key: sha256(text[block.start:block.end].encode("utf-8"))
            for block in split_spec_blocks(text).blocks
        }
        items = []
        for item in data["items"]:
            if item["key"] == "global":
                status = {"base_current": item["spec_sha256"] == digest}
            else:
                current = block_hashes.get(item["key"])
                base = item.get("block_sha256")
                status = {"block_missing": current is None,
                          "block_changed": current != base if current is not None and base else None}
            items.append({**item, **status})
        return items

    def save_annotation(self, key: str, body: str, item_id: str | None = None, revision: str | None = None) -> dict:
        """Create or update a comment, keeping its creation-time fingerprints."""
        if not body.strip():
            raise ReviewError("Enter an annotation before saving.")
        with self._annotations() as data:
            if item_id:
                item = next((item for item in data["items"] if item["id"] == item_id), None)
                if item is None or item["revision"] != revision:
                    raise ReviewError("The annotation changed or was removed; reload it.", 409)
                event = "updated"
            else:
                block = self.block(key) if key != "global" else {"title": "Global", **self.document()}
                item = {"id": uuid.uuid4().hex, "key": key, "title": block["title"],
                        "spec_sha256": block["sha256"], "created_at": timestamp()}
                if key != "global" and not block.get("missing"):
                    item["block_sha256"] = sha256(block["text"].encode("utf-8"))
                data["items"].append(item)
                event = "saved"
            item.update(body=body, updated_at=timestamp(), revision=uuid.uuid4().hex)
            self._save_annotations(data)
            self._append("annotations.jsonl", {"event": event, "ts": timestamp(), **item})
            return item

    def remove_annotation(self, item_id: str, revision: str | None = None, *, applied: bool = False) -> None:
        """Clear a comment only if its browser/listed version still matches."""
        with self._annotations() as data:
            item = next((item for item in data["items"] if item["id"] == item_id), None)
            expected = data["listed"].get(item_id) if applied else revision
            actual = _annotation_fingerprint(item) if applied and item is not None else (item or {}).get("revision")
            if item is None or actual != expected:
                raise ReviewError(
                    "Annotation changed since it was listed, or was not listed; retained. List again.", 409,
                )
            data["items"].remove(item)
            data["listed"].pop(item_id, None)
            self._save_annotations(data)
            self._append("annotations.jsonl", {
                "event": "annotation_applied" if applied else "removed", "ts": timestamp(), **item,
            })

    def list_todo(self) -> dict:
        """Record listed comment revisions and the last unread edit's byte offset."""
        with self._annotations() as data:
            _, text, digest = self._read()
            fields = ("id", "key", "title", "body", "spec_sha256", "block_sha256",
                      "base_current", "block_changed", "block_missing")
            items = [{key: item[key] for key in fields if key in item}
                     for item in self._current_annotations(data, text, digest)]
            edits_path = self.runtime / "edits.jsonl"
            edits = []
            cursor = data.get("edits_cursor", 0)
            if edits_path.exists():
                with edits_path.open("rb") as handle:
                    handle.seek(cursor)
                    for line in handle:
                        event = json.loads(line)
                        edits.append({**{key: event[key] for key in ("ts", "key", "title")},
                                      **{key: event[key][:12] for key in ("before_sha256", "after_sha256")}})
                    cursor = handle.tell()
            data["listed"] = {item["id"]: _annotation_fingerprint(item) for item in data["items"]}
            data["listed_edits_cursor"] = cursor
            self._save_annotations(data)
            return {"sha256": digest, "annotations": items, "edits": edits}

    def ack_edits(self) -> int:
        """Consume only edits included in the last CLI listing, preserving the log."""
        with self._annotations() as data:
            if "listed_edits_cursor" not in data:
                raise ReviewError("List direct edits before acknowledging them.", 409)
            data["edits_cursor"] = data["listed_edits_cursor"]
            self._save_annotations(data)
            return data["edits_cursor"]
