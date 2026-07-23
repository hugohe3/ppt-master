#!/usr/bin/env python3
"""
PPT Master - Chart Candidate Recall

Recalls a deterministic chart-template shortlist from page-shape semantic tags,
or validates selected chart keys against the live chart catalog.

Usage:
    python3 scripts/chart_recall.py recall --page P03 --tag "time series" --tag "three metrics" --tag "trend"
    python3 scripts/chart_recall.py validate line_chart column_chart

Examples:
    python3 scripts/chart_recall.py recall --page P07 --tag "named quadrants" \
        --tag "bullet lists" --tag "SWOT" --limit 6
    python3 scripts/chart_recall.py validate quadrant_text_bullets

Dependencies:
    None (only uses standard library)

See scripts/docs/chart-recall.md for the Strategist workflow and output contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

_SCRIPTS_DIR = Path(__file__).resolve().parent
_INDEX_PATH = _SCRIPTS_DIR.parent / "templates" / "charts" / "charts_index.json"
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PAGE_RE = re.compile(r"^P\d{2,}$")
_KEY_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
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


def load_catalog() -> dict[str, str]:
    """Load and validate the live chart catalog."""
    try:
        payload = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read chart catalog {_INDEX_PATH}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Chart catalog {_INDEX_PATH} root must be an object")
    raw_charts = payload.get("charts")
    if not isinstance(raw_charts, dict) or not raw_charts:
        raise RuntimeError(f"Chart catalog {_INDEX_PATH} has no non-empty 'charts' object")

    charts: dict[str, str] = {}
    for key, item in raw_charts.items():
        if (
            not isinstance(key, str)
            or _KEY_RE.fullmatch(key) is None
            or not isinstance(item, dict)
        ):
            raise RuntimeError(f"Chart catalog entry {key!r} is malformed")
        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError(f"Chart catalog entry {key!r} has no non-empty summary")
        charts[key] = summary.strip()
    return charts


def _score_candidate(key: str, summary: str, tags: list[str]) -> tuple[int, list[str]]:
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


def recall_candidates(
    page: str,
    tags: list[str],
    limit: int,
    *,
    force_semantic_fallback: bool = False,
) -> dict[str, object]:
    """Recall a deterministic shortlist for one page."""
    charts = load_catalog()
    scored: list[tuple[int, str, str, list[str]]] = []
    for key, summary in charts.items():
        score, matched_tags = _score_candidate(key, summary, tags)
        if score > 0 and matched_tags:
            scored.append((score, key, summary, matched_tags))
    scored.sort(key=lambda item: (-item[0], item[1]))

    candidates = []
    for score, key, summary, matched_tags in scored[:limit]:
        candidates.append(
            {
                "key": key,
                "path": f"templates/charts/{key}.svg",
                "summary": summary,
                "score": score,
                "matched_tags": matched_tags,
            }
        )

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
    if force_semantic_fallback:
        result["semantic_fallback"] = {
            "reason": "requested-after-bounded-review",
            "instruction": (
                "Semantically compare the page tags with every returned selection rule. "
                "Choose one exact catalog key or keep no-template-match; lexical overlap "
                "is not required in this review."
            ),
            "path_pattern": "templates/charts/{key}.svg",
            "catalog": charts,
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
        force_semantic_fallback=args.semantic_fallback,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    charts = load_catalog()
    selected = _dedupe(args.keys)
    invalid = sorted(key for key in selected if key not in charts)
    result = {
        "invalid": invalid,
        "valid": sorted(key for key in selected if key in charts),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if invalid:
        print(
            "Error: replace each invalid key with a key returned by the recall command, "
            "or keep no-template-match out of Section VII and page_charts while "
            "recording the custom fallback in the page's Section IX block.",
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recall chart-template candidates or validate selected keys.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    recall = subparsers.add_parser("recall", help="Recall candidates for one planned page.")
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
        help="Include the full catalog when bounded recall may have missed a semantic match.",
    )
    recall.set_defaults(handler=_run_recall)

    validate = subparsers.add_parser("validate", help="Validate selected catalog keys.")
    validate.add_argument("keys", nargs="+", help="One or more selected chart keys.")
    validate.set_defaults(handler=_run_validate)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
