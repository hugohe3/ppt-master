#!/usr/bin/env python3
"""
PPT Master - Prompt Budget Audit Tool

Audits the repository's agent-facing documents without modifying them. Reports
exact o200k_base token counts, declared load-set budgets, Markdown references,
registry claims, schema-definition candidates, and cross-file duplication.

Usage:
    python3 scripts/prompt_audit.py
    python3 scripts/prompt_audit.py --json
    python3 scripts/prompt_audit.py --root /path/to/ppt-master

Examples:
    python3 skills/ppt-master/scripts/prompt_audit.py
    python3 skills/ppt-master/scripts/prompt_audit.py --json | python3 -m json.tool

Dependencies:
    tiktoken (o200k_base encoding)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
_WORD_RE = re.compile(r"[0-9A-Za-z_./<>:+-]+|[\u3400-\u9fff]")
_HEADING_RE = re.compile(r"^#{1,6}\s+")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_SCHEMA_HEADING_RE = re.compile(r"^##\s+([A-Za-z][A-Za-z0-9_.-]*)\s*$")
_REGISTRY_INDEX_ENTRY_RE = re.compile(
    r"^\|\s*\[`(?P<label>[A-Za-z0-9][A-Za-z0-9_-]*)`\]"
    r"\(\./(?P<target>[A-Za-z0-9][A-Za-z0-9_-]*)\.md(?:#[^)]*)?\)\s*\|",
    re.MULTILINE,
)
_AUTHORITY_TERMS_RE = re.compile(
    r"\b(authorit(?:y|ative)|owns?|owner|source of truth|wins for)\b|权威|唯一事实源",
    re.IGNORECASE,
)
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "data:", "javascript:")
_SEVERITY_ORDER = {"error": 0, "warning": 1}


class AuditError(RuntimeError):
    """Represent a user-actionable audit setup failure."""


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""
    line: int = 0
    related: list[str] = field(default_factory=list)


@dataclass
class Document:
    path: str
    absolute_path: Path
    text: str
    tokens: int


@dataclass
class Paragraph:
    path: str
    line: int
    text: str
    normalized: str
    words: tuple[str, ...]


@dataclass
class ReferenceEdge:
    source: str
    line: int
    target: str
    authority_candidate: bool = False


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"Cannot read UTF-8 file {path}: {exc}") from exc


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and validate the prompt-audit manifest."""
    try:
        raw = json.loads(_read_utf8(path))
    except json.JSONDecodeError as exc:
        raise AuditError(f"Invalid JSON manifest {path}: {exc}") from exc

    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise AuditError("Manifest must be an object with schema_version: 1")
    for key in (
        "audit_only",
        "runtime_consumed",
        "budget_policy",
        "encoding",
        "documents",
        "load_sets",
    ):
        if key not in raw:
            raise AuditError(f"Manifest is missing required key: {key}")
    if raw["audit_only"] is not True or raw["runtime_consumed"] is not False:
        raise AuditError("Manifest must remain audit-only and excluded from runtime loading")
    if raw["budget_policy"] != "current_growth_ceiling":
        raise AuditError("Manifest budget_policy must remain current_growth_ceiling")
    if raw["encoding"] != "o200k_base":
        raise AuditError("Manifest encoding must remain o200k_base")
    documents = raw["documents"]
    if not isinstance(documents, dict):
        raise AuditError("documents must be an object")
    if not isinstance(documents.get("max_tokens"), int) or documents["max_tokens"] < 1:
        raise AuditError("documents.max_tokens must be a positive integer")
    for key in ("load_sets", "file_budgets", "duplicates", "coverage"):
        if key in raw and not isinstance(raw[key], dict):
            raise AuditError(f"{key} must be an object")
    for key in ("authority_edges", "registries", "schema_grammars"):
        if key in raw and not isinstance(raw[key], list):
            raise AuditError(f"{key} must be an array")

    schema_configs = raw.get("schema_grammars", [])
    for index, config in enumerate(schema_configs):
        label = f"schema_grammars[{index}]"
        if not isinstance(config, dict):
            raise AuditError(f"{label} must be an object")
        source = config.get("source")
        if not isinstance(source, str) or not source.strip():
            raise AuditError(f"{label}.source must be a non-empty path")
        fields = config.get("fields")
        if fields is not None and (
            not isinstance(fields, list)
            or not fields
            or not all(isinstance(item, str) and item.strip() for item in fields)
            or len(set(fields)) != len(fields)
        ):
            raise AuditError(
                f"{label}.fields must be a non-empty array of unique field names"
            )
        scan = config.get("scan")
        if scan is not None and (
            not isinstance(scan, list)
            or not scan
            or not all(isinstance(item, str) and item.strip() for item in scan)
        ):
            raise AuditError(
                f"{label}.scan must be a non-empty array of path patterns"
            )

    exempt_entries = raw.get("coverage", {}).get("exempt", [])
    if not isinstance(exempt_entries, list):
        raise AuditError("coverage.exempt must be an array")
    for entry in exempt_entries:
        reason = entry.get("reason") if isinstance(entry, dict) else None
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("glob"), str)
            or not entry["glob"]
            or not isinstance(reason, str)
            or not reason.strip()
            or "\n" in reason
            or "\r" in reason
        ):
            raise AuditError(
                "coverage.exempt entries require a non-empty glob and one-line reason"
            )

    accepted_entries = raw.get("duplicates", {}).get("accepted", [])
    if not isinstance(accepted_entries, list):
        raise AuditError("duplicates.accepted must be an array")
    accepted_identities: set[tuple[str, str, tuple[str, ...]]] = set()
    for entry in accepted_entries:
        reason = entry.get("reason") if isinstance(entry, dict) else None
        paths = entry.get("paths") if isinstance(entry, dict) else None
        if (
            not isinstance(entry, dict)
            or entry.get("kind") not in {"exact", "near"}
            or not isinstance(entry.get("fingerprint"), str)
            or re.fullmatch(r"[0-9a-f]{12}", entry["fingerprint"]) is None
            or not isinstance(paths, list)
            or not paths
            or not all(isinstance(item, str) and item.strip() for item in paths)
            or len(set(paths)) != len(paths)
            or not isinstance(reason, str)
            or not reason.strip()
            or "\n" in reason
            or "\r" in reason
        ):
            raise AuditError(
                "duplicates.accepted entries require kind, 12-hex fingerprint, "
                "unique paths, and a one-line reason"
            )
        identity = (
            entry["kind"],
            entry["fingerprint"],
            tuple(sorted(paths)),
        )
        if identity in accepted_identities:
            raise AuditError(f"Duplicate duplicates.accepted identity: {identity}")
        accepted_identities.add(identity)
    return raw


def _expand_globs(
    root: Path,
    patterns: Iterable[str],
    *,
    require_match: bool,
) -> set[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        matches = {path for path in root.glob(pattern) if path.is_file()}
        if require_match and not matches:
            raise AuditError(f"Document include pattern matched no files: {pattern}")
        paths.update(matches)
    return paths


def discover_documents(root: Path, config: dict[str, Any]) -> list[Path]:
    """Resolve the manifest's document corpus into a stable file list."""
    include = config.get("include", [])
    exclude = config.get("exclude", [])
    if not isinstance(include, list) or not all(isinstance(item, str) for item in include):
        raise AuditError("documents.include must be a list of path patterns")
    if not isinstance(exclude, list) or not all(isinstance(item, str) for item in exclude):
        raise AuditError("documents.exclude must be a list of path patterns")

    paths = _expand_globs(root, include, require_match=True)
    excluded = _expand_globs(root, exclude, require_match=False) if exclude else set()
    return sorted(paths - excluded, key=lambda item: _relative_path(root, item))


def _load_encoder(name: str) -> Any:
    try:
        import tiktoken
    except ImportError as exc:
        raise AuditError(
            "tiktoken is required for exact prompt counts. "
            "Install it with: pip install 'tiktoken>=0.7.0'"
        ) from exc

    try:
        return tiktoken.get_encoding(name)
    except (KeyError, ValueError) as exc:
        raise AuditError(f"tiktoken does not provide the required encoding: {name}") from exc


def count_documents(root: Path, paths: list[Path], encoding_name: str) -> list[Document]:
    """Read corpus files and count exact tokenizer units."""
    encoder = _load_encoder(encoding_name)
    documents: list[Document] = []
    for path in paths:
        text = _read_utf8(path)
        documents.append(
            Document(
                path=_relative_path(root, path),
                absolute_path=path,
                text=text,
                tokens=len(encoder.encode(text, disallowed_special=())),
            )
        )
    return documents


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    candidate = PurePosixPath(path)
    return any(candidate.match(pattern) for pattern in patterns)


def _load_entry_paths(root: Path, entry: Any) -> tuple[list[Path], int | None, str]:
    if isinstance(entry, str):
        path = root / entry
        if not path.is_file():
            raise AuditError(f"Load-set file does not exist: {entry}")
        return [path], None, entry

    if not isinstance(entry, dict) or not isinstance(entry.get("glob"), str):
        raise AuditError("Each load-set file entry must be a path or an object with glob")

    pattern = entry["glob"]
    paths = sorted(root.glob(pattern))
    paths = [path for path in paths if path.is_file()]
    excludes = entry.get("exclude", [])
    if excludes:
        paths = [
            path
            for path in paths
            if not _matches_any(_relative_path(root, path), excludes)
        ]
    if not paths:
        raise AuditError(f"Load-set selector matched no files: {pattern}")

    select = entry.get("select")
    if not isinstance(select, int) or select < 1 or select > len(paths):
        raise AuditError(
            f"Load-set selector {pattern} has invalid select={select}; "
            f"expected 1..{len(paths)}"
        )
    return paths, select, pattern


def audit_load_sets(
    root: Path,
    config: dict[str, Any],
    token_counts: dict[str, int],
    manifest_label: str,
    registry_members: dict[str, set[Any]],
) -> tuple[list[dict[str, Any]], list[Finding], set[str]]:
    """Resolve declared load scenarios and enforce their maximum budgets."""
    findings: list[Finding] = []
    results: list[dict[str, Any]] = []
    resolved_cache: dict[str, list[Any]] = {}
    covered_paths: set[str] = set()

    def entry_key(entry: Any) -> str:
        if isinstance(entry, dict):
            return json.dumps(entry, sort_keys=True)
        return f"path:{entry}"

    def resolve_entries(name: str, stack: tuple[str, ...] = ()) -> list[Any]:
        if name in resolved_cache:
            return resolved_cache[name]
        if name not in config:
            raise AuditError(f"Load set includes unknown set: {name}")
        if name in stack:
            cycle = " -> ".join((*stack, name))
            raise AuditError(f"Load-set include cycle: {cycle}")
        load_set = config[name]
        if not isinstance(load_set, dict):
            raise AuditError(f"load_sets.{name} must be an object")
        includes = load_set.get("include", [])
        entries = load_set.get("files", [])
        if not isinstance(includes, list) or not all(isinstance(item, str) for item in includes):
            raise AuditError(f"load_sets.{name}.include must be a list of set names")
        if not isinstance(entries, list):
            raise AuditError(f"load_sets.{name}.files must be a list")

        resolved: list[Any] = []
        seen: set[str] = set()
        for included in includes:
            for entry in resolve_entries(included, (*stack, name)):
                key = entry_key(entry)
                if key not in seen:
                    seen.add(key)
                    resolved.append(entry)
        for entry in entries:
            key = entry_key(entry)
            if key not in seen:
                seen.add(key)
                resolved.append(entry)
        resolved_cache[name] = resolved
        return resolved

    for name, load_set in sorted(config.items()):
        if not isinstance(load_set, dict):
            raise AuditError(f"load_sets.{name} must be an object")
        entries = resolve_entries(name)
        budget = load_set.get("max_tokens")
        if not isinstance(budget, int) or budget < 1:
            raise AuditError(f"load_sets.{name} requires a positive max_tokens")

        fixed: set[str] = set()
        selectors: list[dict[str, Any]] = []
        claimed_options: set[str] = set()
        for entry in entries:
            paths, select, label = _load_entry_paths(root, entry)
            relative = [_relative_path(root, path) for path in paths]
            covered_paths.update(relative)
            missing_counts = [path for path in relative if path not in token_counts]
            if missing_counts:
                raise AuditError(
                    f"Load set {name} references files outside documents.include: "
                    + ", ".join(missing_counts)
                )

            if select is None:
                overlap = (fixed | claimed_options).intersection(relative)
                if overlap:
                    raise AuditError(
                        f"Load set {name} repeats fixed files: {', '.join(sorted(overlap))}"
                    )
                fixed.update(relative)
                continue

            registry_name = entry.get("registry") if isinstance(entry, dict) else None
            if registry_name is not None:
                if registry_name not in registry_members:
                    raise AuditError(
                        f"Load set {name} selector references unknown registry: {registry_name}"
                    )
                candidate_ids = {Path(path).stem for path in relative}
                expected_ids = {str(item) for item in registry_members[registry_name]}
                if candidate_ids != expected_ids:
                    missing = sorted(expected_ids - candidate_ids)
                    extra = sorted(candidate_ids - expected_ids)
                    raise AuditError(
                        f"Load set {name} selector does not match registry {registry_name}; "
                        f"missing={missing}, extra={extra}"
                    )

            overlap = claimed_options.intersection(relative) | fixed.intersection(relative)
            allow_repeat = isinstance(entry, dict) and entry.get("allow_repeat") is True
            load_event = str(entry.get("load_event", ""))
            if allow_repeat and not load_event:
                raise AuditError(
                    f"Load set {name} uses allow_repeat without a named load_event: {label}"
                )
            if overlap and not allow_repeat:
                raise AuditError(
                    f"Load set {name} has overlapping selector files: "
                    + ", ".join(sorted(overlap))
                )
            claimed_options.update(relative)
            counts = sorted(token_counts[path] for path in relative)
            selectors.append(
                {
                    "glob": label,
                    "load_event": load_event,
                    "registry": str(registry_name or ""),
                    "select": select,
                    "candidates": len(relative),
                    "min_tokens": sum(counts[:select]),
                    "typical_tokens": round(statistics.mean(counts) * select),
                    "max_tokens": sum(counts[-select:]),
                }
            )

        fixed_tokens = sum(token_counts[path] for path in fixed)
        minimum = fixed_tokens + sum(item["min_tokens"] for item in selectors)
        typical = fixed_tokens + sum(item["typical_tokens"] for item in selectors)
        maximum = fixed_tokens + sum(item["max_tokens"] for item in selectors)
        status = "pass" if maximum <= budget else "fail"
        if status == "fail":
            findings.append(
                Finding(
                    severity="error",
                    code="BUDGET_LOAD_SET",
                    message=f"{name} maximum {maximum} exceeds budget {budget}",
                    path=manifest_label,
                )
            )
        results.append(
            {
                "name": name,
                "description": str(load_set.get("description", "")),
                "scope": str(load_set.get("scope", "incremental")),
                "includes": list(load_set.get("include", [])),
                "fixed_files": sorted(fixed),
                "selectors": selectors,
                "tokens": {"min": minimum, "typical": typical, "max": maximum},
                "max_tokens": budget,
                "status": status,
            }
        )
    return results, findings, covered_paths


def audit_load_coverage(
    document_paths: Iterable[str],
    covered_paths: set[str],
    config: dict[str, Any],
    manifest_label: str,
) -> tuple[dict[str, Any], list[Finding]]:
    """Force every corpus document into a load set or an explicit exemption."""
    findings: list[Finding] = []
    exempt_entries = config.get("exempt", [])
    all_paths = sorted(document_paths)
    exempt_paths: set[str] = set()
    exempt_owner: dict[str, str] = {}

    for entry in exempt_entries:
        glob = entry["glob"]
        matches = {
            path for path in all_paths if PurePosixPath(path).match(glob)
        }
        if not matches:
            findings.append(
                Finding(
                    severity="error",
                    code="COVERAGE_EXEMPT_STALE",
                    message=f"coverage.exempt glob matches no corpus file: {glob}",
                    path=manifest_label,
                )
            )
            continue
        duplicate_exemptions = sorted(path for path in matches if path in exempt_owner)
        if duplicate_exemptions:
            details = ", ".join(
                f"{path} (already matched by {exempt_owner[path]})"
                for path in duplicate_exemptions
            )
            findings.append(
                Finding(
                    severity="error",
                    code="COVERAGE_EXEMPT_DUPLICATE",
                    message=f"coverage.exempt glob {glob} overlaps: {details}",
                    path=manifest_label,
                )
            )
        overlap = sorted(matches & covered_paths)
        if overlap:
            findings.append(
                Finding(
                    severity="error",
                    code="COVERAGE_EXEMPT_OVERLAP",
                    message=(
                        f"coverage.exempt glob {glob} matches load-set files: "
                        + ", ".join(overlap)
                    ),
                    path=manifest_label,
                )
            )
        for path in matches:
            exempt_owner.setdefault(path, glob)
        exempt_paths.update(matches)

    uncovered = sorted(set(all_paths) - covered_paths - exempt_paths)
    for path in uncovered:
        findings.append(
            Finding(
                severity="error",
                code="LOAD_COVERAGE_GAP",
                message=(
                    "Document is in no load set and has no coverage.exempt entry; "
                    "add it to a load set or exempt it with a reason"
                ),
                path=path,
            )
        )
    return (
        {
            "documents": len(all_paths),
            "covered": len(set(all_paths) & covered_paths),
            "exempt": len(exempt_paths - covered_paths),
            "uncovered": uncovered,
        },
        findings,
    )


def audit_file_budgets(
    budgets: dict[str, Any],
    token_counts: dict[str, int],
) -> list[Finding]:
    """Check explicit per-file growth ceilings."""
    findings: list[Finding] = []
    for path, budget in sorted(budgets.items()):
        if path not in token_counts:
            raise AuditError(f"File budget references a file outside the corpus: {path}")
        if not isinstance(budget, int) or budget < 1:
            raise AuditError(f"File budget for {path} must be a positive integer")
        actual = token_counts[path]
        if actual > budget:
            findings.append(
                Finding(
                    severity="error",
                    code="BUDGET_FILE",
                    message=f"File has {actual} tokens; budget is {budget}",
                    path=path,
                )
            )
    return findings


def _duplicate_fingerprint(*texts: str) -> str:
    joined = "\n\x00\n".join(sorted(texts))
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


def _accepted_identity(
    kind: str,
    fingerprint: str,
    paths: Iterable[str],
) -> tuple[str, str, tuple[str, ...]]:
    return kind, fingerprint, tuple(sorted(paths))


def _partition_accepted(
    entries: list[dict[str, Any]],
    kind: str,
    accepted: list[dict[str, Any]],
    used: set[tuple[str, str, tuple[str, ...]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split duplicate findings into open ones and manifest-accepted ones."""
    lookup = {
        _accepted_identity(item["kind"], item["fingerprint"], item["paths"]): item
        for item in accepted
        if item["kind"] == kind
    }
    open_entries: list[dict[str, Any]] = []
    accepted_entries: list[dict[str, Any]] = []
    for entry in entries:
        identity = _accepted_identity(kind, entry["fingerprint"], entry["paths"])
        match = lookup.get(identity)
        if match is not None:
            used.add(identity)
            accepted_entries.append({**entry, "reason": match["reason"]})
        else:
            open_entries.append(entry)
    return open_entries, accepted_entries


def _normalize_paragraph(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def extract_paragraphs(
    documents: list[Document],
    config: dict[str, Any],
) -> list[Paragraph]:
    """Extract prose blocks for duplicate and registry analysis."""
    minimum = int(config.get("min_chars", 100))
    paragraphs: list[Paragraph] = []

    for document in documents:
        if not document.path.endswith(".md"):
            continue
        block: list[str] = []
        block_line = 1
        in_fence = False

        def flush() -> None:
            nonlocal block
            text = "\n".join(block).strip()
            block = []
            if len(text) < minimum:
                return
            normalized = _normalize_paragraph(text)
            words = tuple(_WORD_RE.findall(normalized))
            if not normalized or not words:
                return
            paragraphs.append(
                Paragraph(
                    path=document.path,
                    line=block_line,
                    text=text,
                    normalized=normalized,
                    words=words,
                )
            )

        for line_number, line in enumerate(document.text.splitlines(), start=1):
            if _FENCE_RE.match(line):
                flush()
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if not line.strip() or _HEADING_RE.match(line) or line.strip() == "---":
                flush()
                continue
            if not block:
                block_line = line_number
            block.append(line)
        flush()

    return paragraphs


def extract_registry_blocks(documents: list[Document]) -> list[Paragraph]:
    """Extract unfiltered Markdown blocks, including headings and fenced examples."""
    blocks: list[Paragraph] = []
    for document in documents:
        if not document.path.endswith(".md"):
            continue
        lines: list[str] = []
        block_line = 1

        def flush() -> None:
            nonlocal lines
            text = "\n".join(lines).strip()
            lines = []
            if not text:
                return
            normalized = _normalize_paragraph(text)
            blocks.append(
                Paragraph(
                    path=document.path,
                    line=block_line,
                    text=text,
                    normalized=normalized,
                    words=tuple(_WORD_RE.findall(normalized)),
                )
            )

        for line_number, line in enumerate(document.text.splitlines(), start=1):
            if not line.strip():
                flush()
                continue
            if not lines:
                block_line = line_number
            lines.append(line)
        flush()
    return blocks


def find_exact_duplicates(
    paragraphs: list[Paragraph],
) -> tuple[list[dict[str, Any]], int]:
    """Find normalized prose blocks copied across files."""
    groups: dict[str, list[Paragraph]] = defaultdict(list)
    for paragraph in paragraphs:
        groups[paragraph.normalized].append(paragraph)

    duplicates: list[dict[str, Any]] = []
    for normalized, items in groups.items():
        if len({item.path for item in items}) < 2:
            continue
        paths = sorted({item.path for item in items})
        locations = sorted(
            ({"path": item.path, "line": item.line} for item in items),
            key=lambda item: (item["path"], item["line"]),
        )
        duplicates.append(
            {
                "kind": "exact",
                "fingerprint": _duplicate_fingerprint(*(item.text for item in items)),
                "paths": paths,
                "chars": len(normalized),
                "preview": normalized[:180],
                "locations": locations,
            }
        )
    duplicates.sort(key=lambda item: (-item["chars"], item["locations"][0]["path"]))
    return duplicates, len(duplicates)


def find_near_duplicates(
    paragraphs: list[Paragraph],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Find heuristic near-duplicate paragraph candidates using word shingles."""
    shingle_size = int(config.get("shingle_words", 4))
    minimum_words = int(config.get("min_words", 20))
    minimum_hits = int(config.get("min_shared_shingles", 3))
    max_frequency = int(config.get("max_shingle_frequency", 24))
    threshold = float(config.get("near_similarity", 0.82))

    eligible = [item for item in paragraphs if len(item.words) >= minimum_words]
    shingle_sets: list[set[tuple[str, ...]]] = []
    inverted: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, paragraph in enumerate(eligible):
        shingles = {
            paragraph.words[offset : offset + shingle_size]
            for offset in range(len(paragraph.words) - shingle_size + 1)
        }
        shingle_sets.append(shingles)
        for shingle in shingles:
            inverted[shingle].append(index)

    hits: Counter[tuple[int, int]] = Counter()
    for indices in inverted.values():
        if len(indices) > max_frequency:
            continue
        for left_offset, left in enumerate(indices):
            for right in indices[left_offset + 1 :]:
                if eligible[left].path != eligible[right].path:
                    hits[(left, right)] += 1

    candidates: list[dict[str, Any]] = []
    for (left, right), shared in hits.items():
        if shared < minimum_hits:
            continue
        first = eligible[left]
        second = eligible[right]
        if first.normalized == second.normalized:
            continue
        union = shingle_sets[left] | shingle_sets[right]
        if not union or shared / len(union) < 0.18:
            continue
        similarity = SequenceMatcher(
            None,
            first.normalized,
            second.normalized,
            autojunk=False,
        ).ratio()
        if similarity < threshold:
            continue
        candidates.append(
            {
                "kind": "near",
                "fingerprint": _duplicate_fingerprint(first.text, second.text),
                "paths": sorted((first.path, second.path)),
                "similarity": round(similarity, 4),
                "left": {"path": first.path, "line": first.line},
                "right": {"path": second.path, "line": second.line},
                "preview": first.normalized[:180],
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["similarity"],
            item["left"]["path"],
            item["left"]["line"],
            item["right"]["path"],
            item["right"]["line"],
        )
    )
    return candidates, len(candidates)


def _clean_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(" ", 1)[0]
    return unquote(target.strip())


def extract_references(
    root: Path,
    documents: list[Document],
) -> tuple[list[ReferenceEdge], list[Finding]]:
    """Extract local Markdown links and report missing targets."""
    edges: list[ReferenceEdge] = []
    findings: list[Finding] = []

    for document in documents:
        if not document.path.endswith(".md"):
            continue
        in_fence = False
        for line_number, line in enumerate(document.text.splitlines(), start=1):
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in _MARKDOWN_LINK_RE.finditer(line):
                raw_target = _clean_link_target(match.group(1))
                if (
                    not raw_target
                    or raw_target.startswith("#")
                    or raw_target.startswith(_EXTERNAL_SCHEMES)
                    or "${" in raw_target
                    or "<" in raw_target
                ):
                    continue
                target_without_anchor = raw_target.split("#", 1)[0].split("?", 1)[0]
                if not target_without_anchor:
                    continue
                target_path = (document.absolute_path.parent / target_without_anchor).resolve()
                try:
                    target_relative = _relative_path(root, target_path)
                except ValueError:
                    findings.append(
                        Finding(
                            severity="error",
                            code="REFERENCE_OUTSIDE_ROOT",
                            message=f"Local link escapes repository root: {raw_target}",
                            path=document.path,
                            line=line_number,
                        )
                    )
                    continue
                if not target_path.exists():
                    findings.append(
                        Finding(
                            severity="error",
                            code="REFERENCE_MISSING",
                            message=f"Markdown target does not exist: {raw_target}",
                            path=document.path,
                            line=line_number,
                        )
                    )
                    continue
                edges.append(
                    ReferenceEdge(
                        source=document.path,
                        line=line_number,
                        target=target_relative,
                        authority_candidate=bool(_AUTHORITY_TERMS_RE.search(line)),
                    )
                )
    edges.sort(key=lambda edge: (edge.source, edge.line, edge.target))
    return edges, findings


def _strongly_connected_components(edges: Iterable[tuple[str, str]]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for source, target in edges:
        graph[source].add(target)
        nodes.update((source, target))

    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    low_links: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(graph.get(node, set())):
            if neighbor not in indices:
                visit(neighbor)
                low_links[node] = min(low_links[node], low_links[neighbor])
            elif neighbor in on_stack:
                low_links[node] = min(low_links[node], indices[neighbor])

        if low_links[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1 or node in graph.get(node, set()):
            components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda item: (len(item), item))


def audit_authority_graph(
    root: Path,
    edges_config: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], list[list[str]], list[Finding]]:
    """Validate the explicit concern-level authority DAG."""
    findings: list[Finding] = []
    normalized: list[dict[str, str]] = []
    by_concern: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for edge in edges_config:
        if not isinstance(edge, dict):
            raise AuditError("authority_edges entries must be objects")
        source = edge.get("from")
        target = edge.get("to")
        concern = edge.get("concern")
        if not all(isinstance(value, str) and value for value in (source, target, concern)):
            raise AuditError("authority_edges require non-empty from, to, and concern")
        for path in (source, target):
            if not (root / path).is_file():
                raise AuditError(f"Authority edge references missing file: {path}")
        normalized.append({"from": source, "to": target, "concern": concern})
        by_concern[concern].append((source, target))

    cycles: list[list[str]] = []
    for concern, concern_edges in sorted(by_concern.items()):
        for component in _strongly_connected_components(concern_edges):
            labeled = [f"{concern}:{path}" for path in component]
            cycles.append(labeled)
            findings.append(
                Finding(
                    severity="error",
                    code="AUTHORITY_CYCLE",
                    message=f"Authority cycle for concern {concern}: " + " -> ".join(component),
                )
            )
    normalized.sort(key=lambda item: (item["concern"], item["from"], item["to"]))
    return normalized, cycles, findings


def _registry_ids(root: Path, config: dict[str, Any]) -> tuple[set[Any], str, list[Any]]:
    kind = config.get("kind")
    source = config.get("source")
    if not isinstance(source, str) or not (root / source).is_file():
        raise AuditError(f"Registry has missing source: {source}")

    if kind == "numbered_markdown":
        pattern = config.get("entry_pattern")
        if not isinstance(pattern, str):
            raise AuditError(f"Registry {config.get('name')} needs entry_pattern")
        try:
            regex = re.compile(pattern, re.MULTILINE)
        except re.error as exc:
            raise AuditError(f"Invalid registry entry_pattern: {exc}") from exc
        matched_ids = [
            int(match.group("id"))
            for match in regex.finditer(_read_utf8(root / source))
        ]
        duplicates = sorted(
            item for item, count in Counter(matched_ids).items() if count > 1
        )
        return set(matched_ids), source, duplicates

    if kind == "directory":
        pattern = config.get("glob")
        excludes = config.get("exclude", [])
        if not isinstance(pattern, str):
            raise AuditError(f"Registry {config.get('name')} needs glob")
        paths = [path for path in root.glob(pattern) if path.is_file()]
        ids = {
            path.stem
            for path in paths
            if not _matches_any(_relative_path(root, path), excludes)
        }
        return ids, source, []

    if kind == "json_collection":
        key = config.get("key")
        if not isinstance(key, str):
            raise AuditError(f"Registry {config.get('name')} needs key")
        try:
            value: Any = json.loads(_read_utf8(root / source))
        except json.JSONDecodeError as exc:
            raise AuditError(f"Registry source is invalid JSON: {source}: {exc}") from exc
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                raise AuditError(f"Registry key {key} is missing in {source}")
            value = value[part]
        if isinstance(value, dict):
            return set(value), source, []
        if isinstance(value, list):
            return set(range(len(value))), source, []
        raise AuditError(f"Registry key {key} in {source} is not a collection")

    raise AuditError(f"Unsupported registry kind: {kind}")


def _registry_count_claims(paragraph: Paragraph, nouns: list[str]) -> list[int]:
    noun_pattern = "|".join(re.escape(noun) for noun in nouns)
    patterns = (
        rf"\bcatalog\s*\(\s*(\d+)\s+(?:{noun_pattern})\s*\)",
        rf"\bcatalog\s+read\s*:?\s*(\d+)\s+(?:{noun_pattern})\b",
        rf"\(\s*(\d+)\s+(?:{noun_pattern})\s*\)",
        rf"\b(?:all|every|the|total(?:\s+of)?|contains?|currently(?:\s+has)?|read(?:\s+all)?)\s+"
        rf"(\d+)\s+(?:{noun_pattern})\b",
    )
    claims: list[int] = []
    for pattern in patterns:
        matches = re.finditer(pattern, paragraph.normalized, re.I)
        claims.extend(int(match.group(1)) for match in matches)
    return claims


def audit_registries(
    root: Path,
    configs: list[dict[str, Any]],
    paragraphs: list[Paragraph],
    documents: list[Document],
) -> tuple[list[dict[str, Any]], list[Finding]]:
    """Compare live registry membership with numeric documentation claims."""
    findings: list[Finding] = []
    reports: list[dict[str, Any]] = []

    for config in configs:
        name = config.get("name")
        if not isinstance(name, str) or not name:
            raise AuditError("Every registry requires a name")
        ids, source, duplicate_ids = _registry_ids(root, config)
        if not ids:
            raise AuditError(f"Registry {name} has no entries")
        for duplicate_id in duplicate_ids:
            findings.append(
                Finding(
                    severity="error",
                    code="REGISTRY_ID_DUPLICATE",
                    message=f"{name} defines id {duplicate_id!r} more than once",
                    path=source,
                )
            )
        index_labels: list[str] | None = None
        index_targets: list[str] | None = None
        if config.get("validate_index_links") is True:
            if config.get("kind") != "directory":
                raise AuditError(
                    f"Registry {name} enables validate_index_links but is not a directory"
                )
            index_matches = list(
                _REGISTRY_INDEX_ENTRY_RE.finditer(_read_utf8(root / source))
            )
            index_labels = [match.group("label") for match in index_matches]
            index_targets = [match.group("target") for match in index_matches]
            for label, target in zip(index_labels, index_targets):
                if label != target:
                    findings.append(
                        Finding(
                            severity="error",
                            code="REGISTRY_INDEX_LABEL_TARGET_MISMATCH",
                            message=(
                                f"{name} index label {label!r} points to {target!r}"
                            ),
                            path=source,
                        )
                    )
            for field_name, values in (
                ("label", index_labels),
                ("target", index_targets),
            ):
                duplicates = sorted(
                    value for value, count in Counter(values).items() if count > 1
                )
                if duplicates:
                    findings.append(
                        Finding(
                            severity="error",
                            code="REGISTRY_INDEX_DUPLICATE",
                            message=(
                                f"{name} index repeats {field_name}(s): "
                                + ", ".join(duplicates)
                            ),
                            path=source,
                        )
                    )
                index_ids = set(values)
                if index_ids != ids:
                    missing = sorted(str(item) for item in ids - index_ids)
                    extra = sorted(str(item) for item in index_ids - ids)
                    findings.append(
                        Finding(
                            severity="error",
                            code="REGISTRY_INDEX_MISMATCH",
                            message=(
                                f"{name} index {field_name}s differ from registry files; "
                                f"missing={missing}, extra={extra}"
                            ),
                            path=source,
                        )
                    )
        terms = [_normalize_paragraph(str(item)) for item in config.get("reference_terms", [])]
        source_name = Path(source).name
        if not source_name.startswith("_"):
            terms.append(_normalize_paragraph(source_name))
        nouns = [str(item).lower() for item in config.get("claim_nouns", [])]
        claims: list[dict[str, Any]] = []
        seen_claims: set[tuple[str, int, int]] = set()
        line_claim_keys: set[tuple[str, int]] = set()

        def record_count_claim(path: str, line: int, count: int) -> None:
            key = (path, line, count)
            if key in seen_claims:
                return
            seen_claims.add(key)
            claims.append({"path": path, "line": line, "count": count})
            if count != len(ids):
                findings.append(
                    Finding(
                        severity="error",
                        code="REGISTRY_COUNT_MISMATCH",
                        message=f"{name} claims {count} entries; registry contains {len(ids)}",
                        path=path,
                        line=line,
                    )
                )

        for document in documents:
            if not document.path.endswith(".md"):
                continue
            for line_number, line in enumerate(document.text.splitlines(), start=1):
                normalized = _normalize_paragraph(line)
                if document.path != source and not any(term in normalized for term in terms):
                    continue
                claim_line = Paragraph(
                    path=document.path,
                    line=line_number,
                    text=line,
                    normalized=normalized,
                    words=tuple(_WORD_RE.findall(normalized)),
                )
                for count in _registry_count_claims(claim_line, nouns):
                    line_claim_keys.add((document.path, count))
                    record_count_claim(document.path, line_number, count)

        for paragraph in paragraphs:
            if paragraph.path != source and not any(term in paragraph.normalized for term in terms):
                continue
            for count in _registry_count_claims(paragraph, nouns):
                if (paragraph.path, count) not in line_claim_keys:
                    record_count_claim(paragraph.path, paragraph.line, count)
            if config.get("kind") != "numbered_markdown":
                continue
            numeric_ids = {int(item) for item in ids}
            id_pattern = re.compile(r"#([1-9]\d*)\b")
            range_pattern = re.compile(r"#([1-9]\d*)\s*[-–]\s*#?([1-9]\d*)\b")
            for match in id_pattern.finditer(paragraph.text):
                claimed_id = int(match.group(1))
                if claimed_id not in numeric_ids:
                    findings.append(
                        Finding(
                            severity="error",
                            code="REGISTRY_ID_MISSING",
                            message=f"{name} references missing id #{claimed_id}",
                            path=paragraph.path,
                            line=paragraph.line,
                        )
                    )

            ranges = sorted(
                tuple(sorted((int(match.group(1)), int(match.group(2)))))
                for match in range_pattern.finditer(paragraph.text)
            )
            comprehensive = re.search(
                r"\b(all|every|entire|full|file is split)\b",
                paragraph.normalized,
            )
            if ranges and comprehensive:
                merged: list[list[int]] = []
                for start, end in ranges:
                    if not merged or start > merged[-1][1] + 1:
                        merged.append([start, end])
                    else:
                        merged[-1][1] = max(merged[-1][1], end)
                declared_count = sum(end - start + 1 for start, end in merged)
                covers_ids = all(
                    any(start <= item <= end for start, end in merged)
                    for item in numeric_ids
                )
                if declared_count != len(numeric_ids) or not covers_ids:
                    findings.append(
                        Finding(
                            severity="error",
                            code="REGISTRY_RANGE_MISMATCH",
                            message=(
                                f"{name} comprehensive ranges cover {declared_count} ids; "
                                f"registry contains {len(numeric_ids)}"
                            ),
                            path=paragraph.path,
                            line=paragraph.line,
                        )
                    )

        reports.append(
            {
                "name": name,
                "source": source,
                "entries": len(ids),
                "duplicate_ids": duplicate_ids,
                "minimum_id": min(ids) if all(isinstance(item, int) for item in ids) else None,
                "maximum_id": max(ids) if all(isinstance(item, int) for item in ids) else None,
                "index_labels": index_labels,
                "index_targets": index_targets,
                "claims": sorted(claims, key=lambda item: (item["path"], item["line"])),
            }
        )
    return sorted(reports, key=lambda item: item["name"]), findings


def _has_schema_grammar_signal(line: str, schema_field: str) -> bool:
    heading = _SCHEMA_HEADING_RE.match(line)
    return bool(
        (heading and heading.group(1) == schema_field)
        or re.search(r"\b(formats?|grammars?|schemas?|syntaxes?|keys?|values?)\b", line, re.I)
        or re.search(r"P<NN>\s*:", line)
        or re.search(rf"{re.escape(schema_field)}\s*[:=]", line)
        or (" | " in line and re.search(r"<[^>]+>", line))
    )


def audit_schema_grammars(
    root: Path,
    configs: list[dict[str, Any]],
    documents: list[Document],
) -> tuple[list[dict[str, Any]], list[Finding]]:
    """Surface fields with grammar-like definitions in multiple non-owner files."""
    findings: list[Finding] = []
    results: list[dict[str, Any]] = []
    document_map = {document.path: document for document in documents}

    for config in configs:
        source = config.get("source")
        if not isinstance(source, str) or not (root / source).is_file():
            raise AuditError(f"Schema source does not exist: {source}")
        source_text = _read_utf8(root / source)
        configured_fields = config.get("fields")
        if configured_fields is None:
            fields = sorted(set(_SCHEMA_HEADING_RE.findall(source_text)))
        elif isinstance(configured_fields, list):
            fields = sorted(str(item) for item in configured_fields)
        else:
            raise AuditError("schema_grammars fields must be a list when present")
        scan_patterns = config.get("scan", ["skills/ppt-master/**/*.md"])

        for schema_field in fields:
            owner_defines_field = any(
                re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(schema_field)}(?![A-Za-z0-9_])",
                    line,
                )
                and _has_schema_grammar_signal(line, schema_field)
                for line in source_text.splitlines()
            )
            if not owner_defines_field:
                raise AuditError(
                    f"Schema owner {source} does not define configured field {schema_field}"
                )
            sites: list[dict[str, Any]] = []
            field_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(schema_field)}(?![A-Za-z0-9_])")
            for path, document in sorted(document_map.items()):
                if path == source or not _matches_any(path, scan_patterns):
                    continue
                in_fence = False
                for line_number, line in enumerate(document.text.splitlines(), start=1):
                    if _FENCE_RE.match(line):
                        in_fence = not in_fence
                        continue
                    if in_fence or not field_re.search(line):
                        continue
                    if not _has_schema_grammar_signal(line, schema_field):
                        continue
                    sites.append(
                        {
                            "path": path,
                            "line": line_number,
                            "excerpt": line.strip()[:240],
                        }
                    )

            unique_files = sorted({site["path"] for site in sites})
            if not unique_files:
                continue
            results.append(
                {
                    "field": schema_field,
                    "owner": source,
                    "definition_candidates": sites,
                }
            )
            findings.append(
                Finding(
                    severity="warning",
                    code="SCHEMA_MULTIDEF_CANDIDATE",
                    message=(
                        f"owns {schema_field}, but {len(unique_files)} non-owner "
                        "files carry grammar-like text for it"
                    ),
                    path=source,
                    related=unique_files,
                )
            )
    results.sort(key=lambda item: item["field"])
    return results, findings


def _finding_key(finding: Finding) -> tuple[Any, ...]:
    return (
        _SEVERITY_ORDER.get(finding.severity, 9),
        finding.code,
        finding.path,
        finding.line,
        finding.message,
    )


def run_audit(
    root: Path,
    manifest_path: Path,
    *,
    include_near_duplicates: bool = True,
) -> dict[str, Any]:
    """Run the complete read-only prompt audit and return a stable report."""
    root = root.resolve()
    manifest = load_manifest(manifest_path)
    encoding_name = str(manifest["encoding"])
    paths = discover_documents(root, manifest["documents"])
    documents = count_documents(root, paths, encoding_name)
    token_counts = {document.path: document.tokens for document in documents}
    findings: list[Finding] = []
    try:
        manifest_label = _relative_path(root, manifest_path)
    except ValueError:
        manifest_label = str(manifest_path.resolve())

    corpus_budget = manifest["documents"].get("max_tokens")
    corpus_tokens = sum(token_counts.values())
    if isinstance(corpus_budget, int) and corpus_tokens > corpus_budget:
        findings.append(
            Finding(
                severity="error",
                code="BUDGET_CORPUS",
                message=f"Corpus has {corpus_tokens} tokens; budget is {corpus_budget}",
            )
        )

    findings.extend(audit_file_budgets(manifest.get("file_budgets", {}), token_counts))
    registry_configs = manifest.get("registries", [])
    registry_members: dict[str, set[Any]] = {}
    for registry_config in registry_configs:
        registry_name = registry_config.get("name")
        if not isinstance(registry_name, str) or not registry_name:
            raise AuditError("Every registry requires a name")
        if registry_name in registry_members:
            raise AuditError(f"Duplicate registry name: {registry_name}")
        members, _, _ = _registry_ids(root, registry_config)
        registry_members[registry_name] = members

    load_sets, load_findings, covered_paths = audit_load_sets(
        root,
        manifest["load_sets"],
        token_counts,
        manifest_label,
        registry_members,
    )
    findings.extend(load_findings)

    coverage, coverage_findings = audit_load_coverage(
        token_counts.keys(),
        covered_paths,
        manifest.get("coverage", {}),
        manifest_label,
    )
    findings.extend(coverage_findings)

    duplicate_config = manifest.get("duplicates", {})
    accepted_config = duplicate_config.get("accepted", [])
    accepted_used: set[tuple[str, str, tuple[str, ...]]] = set()
    paragraphs = extract_paragraphs(documents, duplicate_config)
    registry_blocks = extract_registry_blocks(documents)
    exact, _ = find_exact_duplicates(paragraphs)
    exact, exact_accepted = _partition_accepted(
        exact,
        "exact",
        accepted_config,
        accepted_used,
    )
    exact_total = len(exact)
    exact = exact[: int(duplicate_config.get("max_exact_results", 100))]
    if include_near_duplicates:
        near, _ = find_near_duplicates(paragraphs, duplicate_config)
        near, near_accepted = _partition_accepted(
            near,
            "near",
            accepted_config,
            accepted_used,
        )
        near_total = len(near)
        near = near[: int(duplicate_config.get("max_near_results", 100))]
    else:
        near, near_total, near_accepted = [], None, []

    scanned_duplicate_kinds = {"exact"}
    if include_near_duplicates:
        scanned_duplicate_kinds.add("near")
    for entry in accepted_config:
        identity = _accepted_identity(
            entry["kind"],
            entry["fingerprint"],
            entry["paths"],
        )
        if entry["kind"] in scanned_duplicate_kinds and identity not in accepted_used:
            findings.append(
                Finding(
                    severity="error",
                    code="DUPLICATE_ACCEPTED_STALE",
                    message=(
                        "duplicates.accepted entry matches no current duplicate; "
                        f"remove or update {entry['kind']} {entry['fingerprint']} "
                        f"for {entry['paths']}"
                    ),
                    path=manifest_label,
                )
            )

    if exact_total:
        findings.append(
            Finding(
                severity="warning",
                code="DUPLICATE_EXACT_CANDIDATES",
                message=f"Found {exact_total} cross-file exact paragraph groups",
            )
        )
    if near_total:
        findings.append(
            Finding(
                severity="warning",
                code="DUPLICATE_NEAR_CANDIDATES",
                message=f"Found {near_total} cross-file near-duplicate paragraph pairs",
            )
        )

    references, reference_findings = extract_references(root, documents)
    findings.extend(reference_findings)
    reference_cycles = _strongly_connected_components(
        (edge.source, edge.target)
        for edge in references
        if edge.source.endswith(".md") and edge.target.endswith(".md")
    )
    authority_candidates = [edge for edge in references if edge.authority_candidate]
    authority_candidate_cycles = _strongly_connected_components(
        (edge.source, edge.target) for edge in authority_candidates
    )
    authority_edges, authority_cycles, authority_findings = audit_authority_graph(
        root,
        manifest.get("authority_edges", []),
    )
    findings.extend(authority_findings)
    reference_pairs = {(edge.source, edge.target) for edge in references}
    for edge in authority_edges:
        if (edge["from"], edge["to"]) not in reference_pairs:
            findings.append(
                Finding(
                    severity="error",
                    code="AUTHORITY_EDGE_UNREFERENCED",
                    message=(
                        f"Declared authority edge has no Markdown reference: "
                        f"{edge['from']} -> {edge['to']}"
                    ),
                    path=manifest_label,
                )
            )

    registries, registry_findings = audit_registries(
        root,
        registry_configs,
        registry_blocks,
        documents,
    )
    findings.extend(registry_findings)
    schema_grammars, schema_findings = audit_schema_grammars(
        root,
        manifest.get("schema_grammars", []),
        documents,
    )
    findings.extend(schema_findings)

    findings.sort(key=_finding_key)
    serialized_findings = [asdict(finding) for finding in findings]
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)

    return {
        "schema_version": 1,
        "encoding": encoding_name,
        "manifest": {
            "audit_only": manifest["audit_only"],
            "runtime_consumed": manifest["runtime_consumed"],
            "budget_policy": manifest["budget_policy"],
        },
        "summary": {
            "files": len(documents),
            "tokens": corpus_tokens,
            "max_tokens": corpus_budget,
            "errors": errors,
            "warnings": warnings,
        },
        "files": [
            {"path": path, "tokens": tokens}
            for path, tokens in sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "load_sets": load_sets,
        "coverage": coverage,
        "duplicates": {
            "exact_total": exact_total,
            "exact": exact,
            "exact_accepted": exact_accepted,
            "near_scanned": include_near_duplicates,
            "near_total": near_total,
            "near": near,
            "near_accepted": near_accepted,
        },
        "references": {
            "edges": [asdict(edge) for edge in references],
            "cycles": reference_cycles,
            "authority_candidates": [asdict(edge) for edge in authority_candidates],
            "authority_candidate_cycles": authority_candidate_cycles,
            "declared_authority_edges": authority_edges,
            "declared_authority_cycles": authority_cycles,
        },
        "registries": registries,
        "schema_grammars": schema_grammars,
        "findings": serialized_findings,
    }


def render_text(report: dict[str, Any]) -> str:
    """Render the stable JSON report as a maintainer-oriented text summary."""
    summary = report["summary"]
    lines = [
        "PPT Master Prompt Audit",
        "=======================",
        "Manifest: audit-only | runtime loading: disabled | budgets: current growth ceilings",
        (
            f"Corpus: {summary['files']} files | {summary['tokens']} tokens "
            f"(budget {summary['max_tokens']})"
        ),
        (
            f"Coverage: {report['coverage']['covered']} in load sets | "
            f"{report['coverage']['exempt']} exempt | "
            f"{len(report['coverage']['uncovered'])} uncovered"
        ),
        f"Findings: {summary['errors']} error(s) | {summary['warnings']} warning(s)",
        "",
        "Load sets (min / typical / max <= budget):",
    ]
    for item in report["load_sets"]:
        tokens = item["tokens"]
        lines.append(
            f"  {item['status'].upper():4} {item['name']}: "
            f"{tokens['min']} / {tokens['typical']} / {tokens['max']} <= {item['max_tokens']}"
        )

    lines.extend(["", "Registries:"])
    for item in report["registries"]:
        bounds = ""
        if item["minimum_id"] is not None:
            bounds = f" | ids {item['minimum_id']}..{item['maximum_id']}"
        lines.append(f"  {item['name']}: {item['entries']} entries{bounds}")

    references = report["references"]
    duplicates = report["duplicates"]
    near_summary = (
        (
            f"{duplicates['near_total']} near pair(s) + "
            f"{len(duplicates['near_accepted'])} accepted"
        )
        if duplicates["near_scanned"]
        else "near scan skipped"
    )
    lines.extend(
        [
            "",
            "Candidates:",
            (
                f"  duplicate paragraphs: {duplicates['exact_total']} exact group(s) + "
                f"{len(duplicates['exact_accepted'])} accepted, "
                f"{near_summary}"
            ),
            (
                f"  reference graph: {len(references['edges'])} edge(s), "
                f"{len(references['cycles'])} cyclic component(s)"
            ),
            (
                f"  authority candidates: {len(references['authority_candidates'])} edge(s), "
                f"{len(references['authority_candidate_cycles'])} candidate cycle(s)"
            ),
            f"  schema multi-definition candidates: {len(report['schema_grammars'])}",
        ]
    )
    if duplicates["exact"]:
        lines.append("  exact examples:")
        for item in duplicates["exact"][:5]:
            locations = item["locations"][:2]
            lines.append(
                "    " + " <-> ".join(f"{site['path']}:{site['line']}" for site in locations)
            )
    if duplicates["near_scanned"] and duplicates["near"]:
        lines.append("  near examples:")
        for item in duplicates["near"][:5]:
            left = item["left"]
            right = item["right"]
            lines.append(
                f"    {left['path']}:{left['line']} <-> {right['path']}:{right['line']} "
                f"({item['similarity']:.2f})"
            )
    lines.extend(["", "Per-file tokens:"])
    for item in report["files"]:
        lines.append(f"  {item['tokens']:7d}  {item['path']}")

    lines.extend(["", "Findings:"])
    if not report["findings"]:
        lines.append("  none")
    else:
        for finding in report["findings"]:
            location = finding["path"]
            if location and finding["line"]:
                location += f":{finding['line']}"
            prefix = f" {location}" if location else ""
            lines.append(
                f"  [{finding['severity'].upper()} {finding['code']}]{prefix} "
                f"{finding['message']}"
            )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit PPT Master's prompt budget and governance metadata without writes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    default_root = Path(__file__).resolve().parents[3]
    default_manifest = Path(__file__).with_name("prompt_audit_manifest.json")
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root,
        help=f"Repository root (default: {default_root})",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=default_manifest,
        help=f"Audit manifest (default: {default_manifest})",
    )
    parser.add_argument("--json", action="store_true", help="Emit the complete report as JSON")
    parser.add_argument(
        "--skip-near-duplicates",
        action="store_true",
        help="Skip the slower heuristic near-duplicate pass",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        report = run_audit(
            root,
            manifest_path,
            include_near_duplicates=not args.skip_near_duplicates,
        )
    except AuditError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "error": {
                            "code": "AUDIT_SETUP_ERROR",
                            "message": str(exc),
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False))
    else:
        print(render_text(report), end="")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
