#!/usr/bin/env python3
"""
PPT Master - Visualization Candidate Recall

Recall a deterministic chart or table shortlist from semantic tags, or validate
selected references against the live family catalogs.

Usage:
    python3 scripts/visualization_recall.py recall --page P03 --tag "time series" --tag "three metrics" --tag "trend"
    python3 scripts/visualization_recall.py validate chart/line_chart table/record_table

Examples:
    python3 scripts/visualization_recall.py recall --page P07 --family table \
        --tag "option comparison" --tag "shared criteria" \
        --tag "cell values" --limit 6
    python3 scripts/visualization_recall.py validate table/record_table
    python3 scripts/visualization_recall.py validate --legacy-bare process_flow

Dependencies:
    None (only uses the standard library)

See scripts/docs/visualization-recall.md for the planning workflow and output contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Optional

from console_encoding import configure_utf8_stdio
from visualization_catalog import (
    LEGACY_STRUCTURE_INTENT_KIND,
    VISUALIZATION_SVG_KIND,
    VisualizationCatalogError,
    VisualizationEntry,
    load_visualization_entries,
    resolve_visualization_reference,
    visualization_families,
)

configure_utf8_stdio()

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PAGE_RE = re.compile(r"^P\d{2,}$")
_SKIP_RE = re.compile(r"\bskip\s+(?:if|for)\b", re.IGNORECASE)
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "if",
    "in",
    "into",
    "of",
    "on",
    "or",
    "per",
    "the",
    "to",
    "use",
    "with",
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("_", " ")
    return " ".join(_TOKEN_RE.findall(normalized))


def _stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokens(text: str) -> set[str]:
    return {
        _stem(token)
        for token in _TOKEN_RE.findall(_normalize(text))
        if token not in _STOP_WORDS
    }


def _selected_families(family: str) -> tuple[str, ...]:
    return visualization_families() if family == "all" else (family,)


def load_catalog(family: str = "all") -> dict[str, VisualizationEntry]:
    """Load the selected live family catalogs."""
    return load_visualization_entries(
        _selected_families(family),
    )


def _score_candidate(
    key: str,
    summary: str,
    tags: list[str],
) -> tuple[int, list[str]]:
    skip_match = _SKIP_RE.search(summary)
    if skip_match is None:
        pick_clause, skip_clause = summary, ""
    else:
        pick_clause = summary[:skip_match.start()]
        skip_clause = summary[skip_match.start():]
    key_text = _normalize(key)
    pick_text = _normalize(pick_clause)
    skip_text = _normalize(skip_clause)
    key_tokens = _tokens(key)
    pick_tokens = _tokens(pick_clause)
    skip_tokens = _tokens(skip_clause)
    score = 0
    matched_tags: list[str] = []

    for tag in tags:
        tag_text = _normalize(tag)
        tag_tokens = _tokens(tag)
        positive_score = 0
        negative_score = 0
        if tag_text and tag_text in key_text:
            positive_score += 20
        elif tag_text and tag_text in pick_text:
            positive_score += 14
        if tag_text and tag_text in skip_text:
            negative_score += 12

        for token in tag_tokens:
            if token in key_tokens:
                positive_score += 9
            elif token in pick_tokens:
                positive_score += 5
            if token in skip_tokens:
                negative_score += 6

        if positive_score:
            matched_tags.append(tag)
        score += positive_score - negative_score

    return score, matched_tags


def _candidate_payload(
    entry: VisualizationEntry,
    score: int,
    matched_tags: list[str],
    *,
    legacy_output: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "key": entry.key,
        "path": entry.display_path,
        "summary": entry.summary,
        "score": score,
        "matched_tags": matched_tags,
    }
    if not legacy_output:
        payload.update(
            {
                "family": entry.family,
                "reference": entry.reference,
            }
        )
    return payload


def _validation_payload(entry: VisualizationEntry) -> dict[str, object]:
    """Describe one resolution without inventing an asset for intent-only keys."""
    payload: dict[str, object] = {
        "family": entry.family,
        "key": entry.key,
        "kind": entry.kind,
    }
    if entry.kind == VISUALIZATION_SVG_KIND:
        payload.update(
            {
                "path": entry.display_path,
                "reference": entry.reference,
            }
        )
    elif entry.kind != LEGACY_STRUCTURE_INTENT_KIND:
        raise VisualizationCatalogError(
            f"{entry.key!r} resolves to unsupported kind {entry.kind!r}"
        )
    return payload


def recall_candidates(
    page: str,
    tags: list[str],
    limit: int,
    *,
    family: str = "all",
    force_semantic_fallback: bool = False,
    legacy_output: bool = False,
) -> dict[str, object]:
    """Recall a deterministic shortlist for one page."""
    entries = load_catalog(family)
    scored: list[tuple[int, VisualizationEntry, list[str]]] = []
    for entry in entries.values():
        score, matched_tags = _score_candidate(entry.key, entry.summary, tags)
        if score > 0 and matched_tags:
            scored.append((score, entry, matched_tags))
    scored.sort(key=lambda item: (-item[0], item[1].family, item[1].key))

    candidates = [
        _candidate_payload(
            entry,
            score,
            matched_tags,
            legacy_output=legacy_output,
        )
        for score, entry, matched_tags in scored[:limit]
    ]

    top_score = candidates[0]["score"] if candidates else 0
    if top_score >= 35:
        confidence = "high"
    elif top_score >= 15:
        confidence = "medium"
    elif top_score > 0:
        confidence = "low"
    else:
        confidence = "none"

    fallback_required_before_no_match = (
        confidence in {"low", "none"} and not force_semantic_fallback
    )
    if fallback_required_before_no_match:
        no_match_instruction = (
            f"Lexical confidence is {confidence}. Select a bounded candidate when one "
            "fits; otherwise rerun the same recall with --semantic-fallback before "
            "keeping no-template-match. Keep the final negative result out of Design "
            "Spec Section VII and describe the chosen fallback in the page's Section "
            "IX block."
        )
    else:
        no_match_instruction = (
            "Use when none of the reviewed candidates fits the page structure. Keep "
            "this result out of Design Spec Section VII and describe the chosen fallback "
            "in the page's Section IX block."
        )

    result: dict[str, object] = {
        "page": page,
        "semantic_tags": tags,
        "confidence": confidence,
        "candidates": candidates,
        "no_template_match": {
            "allowed": not fallback_required_before_no_match,
            "key": "no-template-match",
            "instruction": no_match_instruction,
        },
    }
    if not legacy_output:
        result["family_filter"] = family
    if force_semantic_fallback:
        if legacy_output:
            catalog: object = {
                entry.key: entry.summary
                for entry in sorted(entries.values(), key=lambda item: item.key)
            }
        else:
            catalog = {
                entry.reference: {
                    "family": entry.family,
                    "key": entry.key,
                    "path": entry.display_path,
                    "summary": entry.summary,
                }
                for entry in sorted(
                    entries.values(),
                    key=lambda item: (item.family, item.key),
                )
            }
        result["semantic_fallback"] = {
            "reason": "requested-after-bounded-review",
            "instruction": (
                "Semantically compare the page tags with every returned selection rule. "
                "Choose one exact catalog reference or keep no-template-match; lexical "
                "overlap is not required in this review."
            ),
            "reference_pattern": "family/key",
            "catalog": catalog,
        }
    return result


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        normalized = _normalize(stripped)
        if not stripped or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(stripped)
    return result


def _run_recall(args: argparse.Namespace) -> int:
    page = args.page.upper()
    if not _PAGE_RE.fullmatch(page):
        print("Error: --page must match P<NN>, for example P03.", file=sys.stderr)
        return 2

    tags = _dedupe(args.tag)
    if not 3 <= len(tags) <= 8:
        print("Error: recall requires 3-8 distinct non-empty --tag values.", file=sys.stderr)
        return 2

    result = recall_candidates(
        page,
        tags,
        args.limit,
        family=args.family,
        force_semantic_fallback=args.semantic_fallback,
        legacy_output=args.legacy_output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _resolve_validation_value(
    raw: str,
    family: str,
    *,
    allow_legacy_bare: bool,
) -> VisualizationEntry:
    if "/" in raw:
        return resolve_visualization_reference(raw)
    if family != "all":
        return resolve_visualization_reference(f"{family}/{raw}")
    return resolve_visualization_reference(
        raw,
        allow_legacy_bare=allow_legacy_bare,
    )


def _run_validate(args: argparse.Namespace) -> int:
    selected = _dedupe(args.keys)
    invalid: list[str] = []
    valid_entries: list[tuple[str, VisualizationEntry]] = []
    for value in selected:
        try:
            valid_entries.append(
                (
                    value,
                    _resolve_validation_value(
                        value,
                        args.family,
                        allow_legacy_bare=args.legacy_bare,
                    ),
                )
            )
        except VisualizationCatalogError:
            invalid.append(value)

    if args.legacy_output:
        valid: object = sorted(raw for raw, _entry in valid_entries)
    else:
        valid = [
            _validation_payload(entry)
            for _raw, entry in sorted(
                valid_entries,
                key=lambda item: (item[1].kind, item[1].family, item[1].key),
            )
        ]
    result: dict[str, object] = {"invalid": sorted(invalid), "valid": valid}
    if args.legacy_output:
        result["resolved"] = [
            {"input": raw, **_validation_payload(entry)}
            for raw, entry in sorted(valid_entries, key=lambda item: item[0])
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if invalid:
        mapping_name = (
            "page_charts"
            if args.legacy_output or args.legacy_bare
            else "page_visualizations"
        )
        print(
            "Error: replace each invalid reference with one returned by recall, or "
            f"keep no-template-match out of Section VII and {mapping_name} while "
            "recording the custom fallback in the page's Section IX block.",
            file=sys.stderr,
        )
        return 1
    return 0


def _add_family_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--family",
        choices=("all",) + visualization_families(),
        default="all",
        help="Limit candidates to one family (default: all).",
    )


def build_parser(*, legacy_output: bool = False) -> argparse.ArgumentParser:
    description = (
        "Recall legacy chart-catalog candidates or validate selected keys."
        if legacy_output
        else "Recall visualization candidates or validate selected references."
    )
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.set_defaults(legacy_output=legacy_output)
    subparsers = parser.add_subparsers(dest="command", required=True)

    recall = subparsers.add_parser("recall", help="Recall candidates for one page.")
    recall.add_argument("--page", required=True, help="Planned page key, for example P03.")
    recall.add_argument(
        "--tag",
        action="append",
        required=True,
        help="English semantic content-shape tag; repeat 3-8 times.",
    )
    recall.add_argument(
        "--limit",
        type=int,
        choices=range(3, 9),
        default=6,
        metavar="3..8",
        help="Candidate count (default: 6).",
    )
    recall.add_argument(
        "--semantic-fallback",
        action="store_true",
        help="Include the selected live catalogs after a low-confidence review.",
    )
    _add_family_argument(recall)
    recall.set_defaults(handler=_run_recall)

    validate = subparsers.add_parser("validate", help="Validate selected references.")
    validate.add_argument("keys", nargs="+", help="One or more keys or family/key references.")
    validate.add_argument(
        "--legacy-bare",
        action="store_true",
        default=legacy_output,
        help=(
            argparse.SUPPRESS
            if legacy_output
            else "Allow unqualified keys from an existing legacy page_charts mapping."
        ),
    )
    _add_family_argument(validate)
    validate.set_defaults(handler=_run_validate)
    return parser


def main(
    argv: Optional[list[str]] = None,
    *,
    legacy_output: bool = False,
) -> int:
    parser = build_parser(legacy_output=legacy_output)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except VisualizationCatalogError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
