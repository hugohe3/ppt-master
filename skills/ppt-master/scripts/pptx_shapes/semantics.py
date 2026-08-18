#!/usr/bin/env python3
"""
PPT Master - DrawingML Preset Shape Semantics

Load and validate the bundled Office-category and authoring-use catalog for
DrawingML preset shapes.

Usage:
    Import get_preset_shape_semantics from pptx_shapes.semantics.

Examples:
    catalog = get_preset_shape_semantics()
    arrow = catalog.describe("rightArrow")

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from .errors import PresetShapeDataError, UnknownPresetShapeError
from .registry import get_preset_registry


BUNDLED_SEMANTICS_PATH = (
    Path(__file__).resolve().parent / "data" / "presetShapeSemantics.json"
)

SEMANTIC_ROLES = (
    "field",
    "carrier",
    "node",
    "edge",
    "spine",
    "boundary",
    "callout",
    "label",
    "symbol",
    "control",
    "accent",
)
SEMANTIC_RELATIONSHIPS = (
    "none",
    "membership",
    "order",
    "link",
    "hierarchy",
    "contrast",
    "convergence",
    "cycle",
    "overlap",
    "annotation",
    "flow",
    "literal",
    "navigation",
)
SEMANTIC_DIRECTIONALITY = (
    "none",
    "horizontal",
    "vertical",
    "diagonal",
    "bidirectional",
    "multidirectional",
    "bent",
    "curved",
    "radial",
    "callout",
)
SEMANTIC_ASPECTS = (
    "flexible",
    "wide",
    "tall",
    "square",
    "linear",
)
SEMANTIC_TEXT_CAPACITIES = ("none", "short", "medium", "high")
SEMANTIC_VISUAL_WEIGHTS = ("quiet", "moderate", "strong", "emblematic")
SEMANTIC_SCOPES = ("general", "literal", "flowchart", "navigation")

_TEXT_CAPACITY_RANK = {
    value: index for index, value in enumerate(SEMANTIC_TEXT_CAPACITIES)
}
_QUERY_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_QUERY_STOP_WORDS = frozenset({
    "a",
    "an",
    "and",
    "for",
    "of",
    "or",
    "the",
    "to",
    "with",
})


class PresetShapeSemantics:
    """Read-only semantic catalog aligned exactly with the preset registry."""

    def __init__(self, payload: object, expected_names: Sequence[str]) -> None:
        root = _require_dict(payload, "catalog")
        self.schema = _require_string(root.get("schema"), "catalog.schema")
        self.sources = tuple(
            _require_dict(item, f"catalog.sources[{index}]")
            for index, item in enumerate(
                _require_list(root.get("sources"), "catalog.sources")
            )
        )

        categories = _require_list(
            root.get("office_categories"),
            "catalog.office_categories",
        )
        self._categories: list[dict[str, object]] = []
        self._category_by_id: dict[str, dict[str, object]] = {}
        for index, raw_category in enumerate(categories):
            label = f"catalog.office_categories[{index}]"
            category = _require_dict(raw_category, label)
            _reject_unknown_fields(category, label, {"id", "label", "summary"})
            category_id = _require_string(category.get("id"), f"{label}.id")
            if category_id in self._category_by_id:
                raise PresetShapeDataError(
                    f"Duplicate Office shape category: {category_id!r}"
                )
            normalized = {
                "id": category_id,
                "label": _require_string(category.get("label"), f"{label}.label"),
                "summary": _require_string(
                    category.get("summary"),
                    f"{label}.summary",
                ),
            }
            self._categories.append(normalized)
            self._category_by_id[category_id] = normalized

        groups = _require_list(root.get("groups"), "catalog.groups")
        self._groups: list[dict[str, object]] = []
        self._preset_semantics: dict[str, dict[str, object]] = {}
        self._group_order: dict[str, int] = {}
        self._preset_order = {
            name: index for index, name in enumerate(expected_names)
        }
        for index, raw_group in enumerate(groups):
            group = self._normalize_group(raw_group, index)
            group_id = str(group["id"])
            if group_id in self._group_order:
                raise PresetShapeDataError(
                    f"Duplicate preset semantic group: {group_id!r}"
                )
            self._group_order[group_id] = index
            self._groups.append(group)
            presets = group["presets"]
            assert isinstance(presets, dict)
            for preset_name, preset_details in presets.items():
                if preset_name in self._preset_semantics:
                    raise PresetShapeDataError(
                        f"Preset appears in multiple semantic groups: {preset_name!r}"
                    )
                details = dict(group)
                details.pop("presets")
                details["preset"] = preset_name
                details.update(preset_details)
                details["recommended_for"] = _merge_strings(
                    group["recommended_for"],
                    preset_details.get("recommended_for", ()),
                )
                details["avoid_for"] = _merge_strings(
                    group["avoid_for"],
                    preset_details.get("avoid_for", ()),
                )
                self._preset_semantics[preset_name] = details

        expected = set(expected_names)
        actual = set(self._preset_semantics)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            raise PresetShapeDataError(
                "Preset semantic catalog differs from ShapeTypeValues: "
                f"missing={missing}, extra={extra}"
            )

    @classmethod
    def bundled(cls) -> PresetShapeSemantics:
        """Load the semantic catalog shipped with PPT Master."""

        try:
            payload = json.loads(BUNDLED_SEMANTICS_PATH.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PresetShapeDataError(
                f"Cannot read preset semantic catalog: {exc}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise PresetShapeDataError(
                "Invalid preset semantic JSON at "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc
        return cls(payload, get_preset_registry().names)

    @property
    def preset_count(self) -> int:
        """Return the number of catalogued presets."""

        return len(self._preset_semantics)

    def describe(self, preset: str) -> dict[str, object]:
        """Return the resolved semantic record for one preset."""

        try:
            return dict(self._preset_semantics[preset])
        except KeyError as exc:
            raise UnknownPresetShapeError(
                f"Unknown DrawingML preset shape: {preset!r}"
            ) from exc

    def grouped(self, search: str = "") -> dict[str, object]:
        """Return a compact Office/group index and matching preset names."""

        query_tokens = _query_tokens(search)
        category_payloads: list[dict[str, object]] = []
        for category in self._categories:
            group_payloads: list[dict[str, object]] = []
            for group in self._groups:
                if group["office_category"] != category["id"]:
                    continue
                presets = group["presets"]
                assert isinstance(presets, dict)
                matching_presets = []
                group_matches = _matches_query(
                    {
                        key: value
                        for key, value in group.items()
                        if key != "presets"
                    },
                    query_tokens,
                )
                for name, details in presets.items():
                    if query_tokens and not group_matches and not _matches_query(
                        {"preset": name, **details},
                        query_tokens,
                    ):
                        continue
                    matching_presets.append(name)
                if not matching_presets:
                    continue
                recommended_for = group["recommended_for"]
                assert isinstance(recommended_for, tuple)
                group_payload = {
                    "id": group["id"],
                    "label": group["label"],
                    "scope": group["scope"],
                    "intent": recommended_for[0],
                    "presets": matching_presets,
                }
                group_payloads.append(group_payload)
            if group_payloads:
                category_payloads.append({**category, "groups": group_payloads})
        return {
            "schema": self.schema,
            "sources": [dict(source) for source in self.sources],
            "preset_count": sum(
                len(group["presets"])
                for category in category_payloads
                for group in category["groups"]
            ),
            "search": search,
            "office_categories": category_payloads,
        }

    def recommend(
        self,
        *,
        roles: Sequence[str],
        scope: str = "general",
        relationships: Sequence[str] = (),
        directionality: str | None = None,
        aspect: str | None = None,
        text_capacity: str | None = None,
        visual_weight: str | None = None,
        query: str = "",
        limit: int = 12,
    ) -> dict[str, object]:
        """Return a diverse, semantics-matched candidate recall set."""

        query_tokens = _query_tokens(query)
        candidates: list[dict[str, object]] = []
        for details in self._preset_semantics.values():
            if scope != "all" and details["scope"] != scope:
                continue

            role_matches = [role for role in roles if role in details["roles"]]
            if not role_matches:
                continue
            relationship_matches = [
                relationship
                for relationship in relationships
                if relationship in details["relationships"]
            ]
            if relationships and not relationship_matches:
                continue
            if directionality and directionality not in details["directionality"]:
                continue
            if aspect and not _aspect_matches(details["aspects"], aspect):
                continue
            if text_capacity and not _capacity_matches(
                str(details["text_capacity"]),
                text_capacity,
            ):
                continue
            if visual_weight and details["visual_weight"] != visual_weight:
                continue

            query_score = _query_score(details, query_tokens, query)
            if query_tokens and query_score == 0:
                continue
            score = (
                len(role_matches) * 20
                + len(relationship_matches) * 12
                + (5 if directionality else 0)
                + (4 if aspect else 0)
                + (3 if text_capacity else 0)
                + (2 if visual_weight else 0)
                + query_score
            )
            why = [f"role={value}" for value in role_matches]
            why.extend(
                f"relationship={value}" for value in relationship_matches
            )
            if directionality:
                why.append(f"directionality={directionality}")
            if aspect:
                why.append(f"aspect={aspect}")
            if text_capacity:
                why.append(f"text_capacity>={text_capacity}")
            if visual_weight:
                why.append(f"visual_weight={visual_weight}")
            if query_tokens:
                why.append(f"query={query}")
            candidates.append({
                "score": score,
                "preset": details["preset"],
                "office_category": {
                    "id": details["office_category"],
                    "label": details["office_category_label"],
                },
                "group": details["id"],
                "scope": details["scope"],
                "intent": details["intent"],
                "why": why,
                "recommended_for": details["recommended_for"],
                "avoid_for": details["avoid_for"],
                "literal_only": details["literal_only"],
            })

        ordered = self._diverse_order(candidates)
        return {
            "criteria": {
                "roles": list(roles),
                "scope": scope,
                "relationships": list(relationships),
                "directionality": directionality,
                "aspect": aspect,
                "text_capacity": text_capacity,
                "visual_weight": visual_weight,
                "query": query,
            },
            "candidate_count": len(candidates),
            "returned_count": min(len(ordered), limit),
            "selection_note": (
                "Candidate recall only. Compare contour, content fit, and avoid_for "
                "before choosing; this is neither a whitelist nor an automatic choice."
                if ordered
                else "No candidates matched. This is a valid recall result; relax or "
                "change the criteria before selecting a contour."
            ),
            "candidates": ordered[:limit],
        }

    def _normalize_group(
        self,
        raw_group: object,
        index: int,
    ) -> dict[str, object]:
        label = f"catalog.groups[{index}]"
        group = _require_dict(raw_group, label)
        _reject_unknown_fields(
            group,
            label,
            {
                "id",
                "label",
                "office_category",
                "scope",
                "roles",
                "relationships",
                "directionality",
                "aspects",
                "text_capacity",
                "visual_weight",
                "literal_only",
                "recommended_for",
                "avoid_for",
                "presets",
            },
        )
        category_id = _require_string(
            group.get("office_category"),
            f"{label}.office_category",
        )
        if category_id not in self._category_by_id:
            raise PresetShapeDataError(
                f"{label} references unknown Office category {category_id!r}"
            )
        scope = _require_choice(group.get("scope"), f"{label}.scope", SEMANTIC_SCOPES)
        roles = _require_choices(group.get("roles"), f"{label}.roles", SEMANTIC_ROLES)
        relationships = _require_choices(
            group.get("relationships"),
            f"{label}.relationships",
            SEMANTIC_RELATIONSHIPS,
        )
        directionality = _require_choices(
            group.get("directionality"),
            f"{label}.directionality",
            SEMANTIC_DIRECTIONALITY,
        )
        aspects = _require_choices(
            group.get("aspects"),
            f"{label}.aspects",
            SEMANTIC_ASPECTS,
        )
        presets = _require_dict(group.get("presets"), f"{label}.presets")
        if not presets:
            raise PresetShapeDataError(f"{label}.presets must not be empty")
        normalized_presets: dict[str, dict[str, object]] = {}
        for preset_name, raw_details in presets.items():
            preset_label = f"{label}.presets[{preset_name!r}]"
            details = _require_dict(raw_details, preset_label)
            _reject_unknown_fields(
                details,
                preset_label,
                {
                    "intent",
                    "scope",
                    "roles",
                    "relationships",
                    "directionality",
                    "aspects",
                    "text_capacity",
                    "visual_weight",
                    "literal_only",
                    "recommended_for",
                    "avoid_for",
                },
            )
            normalized_details: dict[str, object] = {
                "intent": _require_string(
                    details.get("intent"),
                    f"{preset_label}.intent",
                )
            }
            repeated_choices = {
                "roles": SEMANTIC_ROLES,
                "relationships": SEMANTIC_RELATIONSHIPS,
                "directionality": SEMANTIC_DIRECTIONALITY,
                "aspects": SEMANTIC_ASPECTS,
            }
            for field, choices in repeated_choices.items():
                if field in details:
                    normalized_details[field] = _require_choices(
                        details[field],
                        f"{preset_label}.{field}",
                        choices,
                    )
            single_choices = {
                "scope": SEMANTIC_SCOPES,
                "text_capacity": SEMANTIC_TEXT_CAPACITIES,
                "visual_weight": SEMANTIC_VISUAL_WEIGHTS,
            }
            for field, choices in single_choices.items():
                if field in details:
                    normalized_details[field] = _require_choice(
                        details[field],
                        f"{preset_label}.{field}",
                        choices,
                    )
            if "literal_only" in details:
                normalized_details["literal_only"] = _require_bool(
                    details["literal_only"],
                    f"{preset_label}.literal_only",
                )
            for field in ("recommended_for", "avoid_for"):
                if field in details:
                    normalized_details[field] = _require_string_list(
                        details[field],
                        f"{preset_label}.{field}",
                    )
            normalized_presets[preset_name] = normalized_details
        recommended_for = _require_string_list(
            group.get("recommended_for"),
            f"{label}.recommended_for",
        )
        avoid_for = _require_string_list(
            group.get("avoid_for"),
            f"{label}.avoid_for",
        )
        if not recommended_for or not avoid_for:
            raise PresetShapeDataError(
                f"{label}.recommended_for and avoid_for must not be empty"
            )
        return {
            "id": _require_string(group.get("id"), f"{label}.id"),
            "label": _require_string(group.get("label"), f"{label}.label"),
            "office_category": category_id,
            "office_category_label": self._category_by_id[category_id]["label"],
            "scope": scope,
            "roles": roles,
            "relationships": relationships,
            "directionality": directionality,
            "aspects": aspects,
            "text_capacity": _require_choice(
                group.get("text_capacity"),
                f"{label}.text_capacity",
                SEMANTIC_TEXT_CAPACITIES,
            ),
            "visual_weight": _require_choice(
                group.get("visual_weight"),
                f"{label}.visual_weight",
                SEMANTIC_VISUAL_WEIGHTS,
            ),
            "literal_only": _require_bool(
                group.get("literal_only"),
                f"{label}.literal_only",
            ),
            "recommended_for": recommended_for,
            "avoid_for": avoid_for,
            "presets": normalized_presets,
        }

    def _diverse_order(
        self,
        candidates: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        candidates.sort(
            key=lambda item: (
                -int(item["score"]),
                self._group_order[str(item["group"])],
                self._preset_order[str(item["preset"])],
            )
        )
        ordered: list[dict[str, object]] = []
        scores = sorted({int(item["score"]) for item in candidates}, reverse=True)
        for score in scores:
            score_items = [item for item in candidates if item["score"] == score]
            first_by_group: list[dict[str, object]] = []
            remaining: list[dict[str, object]] = []
            seen_groups: set[str] = set()
            for item in score_items:
                group_id = str(item["group"])
                target = first_by_group if group_id not in seen_groups else remaining
                target.append(item)
                seen_groups.add(group_id)
            ordered.extend(first_by_group)
            ordered.extend(remaining)
        return ordered


@lru_cache(maxsize=1)
def get_preset_shape_semantics() -> PresetShapeSemantics:
    """Return the process-wide, lazily loaded bundled semantic catalog."""

    return PresetShapeSemantics.bundled()


def _require_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PresetShapeDataError(f"{label} must be a JSON object")
    return value


def _reject_unknown_fields(
    value: dict[str, object],
    label: str,
    allowed: set[str],
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise PresetShapeDataError(
            f"{label} contains unsupported fields: {', '.join(unknown)}"
        )


def _require_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise PresetShapeDataError(f"{label} must be a JSON array")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PresetShapeDataError(f"{label} must be a non-empty string")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise PresetShapeDataError(f"{label} must be a boolean")
    return value


def _require_choice(value: object, label: str, choices: Sequence[str]) -> str:
    text = _require_string(value, label)
    if text not in choices:
        raise PresetShapeDataError(
            f"{label} must be one of {', '.join(choices)}; got {text!r}"
        )
    return text


def _require_choices(
    value: object,
    label: str,
    choices: Sequence[str],
) -> tuple[str, ...]:
    values = _require_string_list(value, label)
    if not values:
        raise PresetShapeDataError(f"{label} must not be empty")
    unknown = sorted(set(values) - set(choices))
    if unknown:
        raise PresetShapeDataError(
            f"{label} contains unsupported values: {', '.join(unknown)}"
        )
    return values


def _require_string_list(value: object, label: str) -> tuple[str, ...]:
    items = _require_list(value, label)
    values = tuple(
        _require_string(item, f"{label}[{index}]")
        for index, item in enumerate(items)
    )
    if len(values) != len(set(values)):
        raise PresetShapeDataError(f"{label} contains duplicate values")
    return values


def _merge_strings(first: object, second: object) -> tuple[str, ...]:
    merged: list[str] = []
    for values in (first, second):
        assert isinstance(values, tuple)
        for value in values:
            if value not in merged:
                merged.append(value)
    return tuple(merged)


def _query_tokens(query: str) -> tuple[str, ...]:
    normalized = _CAMEL_BOUNDARY_RE.sub(" ", query).casefold()
    return tuple(
        token
        for token in _QUERY_TOKEN_RE.findall(normalized)
        if token not in _QUERY_STOP_WORDS
    )


def _search_text(value: object) -> str:
    if isinstance(value, str):
        return _CAMEL_BOUNDARY_RE.sub(" ", value).casefold()
    if isinstance(value, (list, tuple)):
        return " ".join(_search_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_search_text(item) for item in value.values())
    return ""


def _matches_query(details: dict[str, object], query_tokens: Sequence[str]) -> bool:
    if not query_tokens:
        return True
    haystack = _search_text(details)
    return all(token in haystack for token in query_tokens)


def _query_score(
    details: dict[str, object],
    query_tokens: Sequence[str],
    query: str,
) -> int:
    if not query_tokens:
        return 0
    haystack = _search_text(details)
    matches = sum(1 for token in query_tokens if token in haystack)
    if matches == 0:
        return 0
    score = matches * 4
    normalized_query = " ".join(_query_tokens(query))
    if normalized_query and normalized_query in haystack:
        score += 10
    preset = str(details["preset"])
    if query.casefold() == preset.casefold():
        score += 20
    return score


def _aspect_matches(values: object, requested: str) -> bool:
    assert isinstance(values, tuple)
    return requested in values or "flexible" in values


def _capacity_matches(actual: str, requested: str) -> bool:
    return _TEXT_CAPACITY_RANK[actual] >= _TEXT_CAPACITY_RANK[requested]
