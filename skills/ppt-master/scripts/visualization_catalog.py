#!/usr/bin/env python3
"""
PPT Master - Visualization Catalog Resolver

Resolve chart and table references from their live family indexes.

Historical ``page_charts`` structure keys remain readable as intent-only
compatibility values. They do not resolve to SVG assets and are never part of
the live recall catalog.

Usage:
    Import load_visualization_entries() or resolve_visualization_reference().

Examples:
    from visualization_catalog import resolve_visualization_reference

Dependencies:
    None (only uses the standard library)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_SCRIPTS_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _SCRIPTS_DIR.parent / "templates"
_KEY_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_FAMILY_SPECS = {
    "chart": ("charts", "charts_index.json", "charts"),
    "table": ("tables", "tables_index.json", "tables"),
}
VISUALIZATION_SVG_KIND = "visualization-svg"
LEGACY_STRUCTURE_INTENT_KIND = "legacy-structure-intent"

# Frozen from the 36 Structure entries published in origin/main's historical
# broad charts catalog. Keep this exact allowlist: later split-only aliases and
# generated Structure keys were never part of that public compatibility input.
_LEGACY_STRUCTURE_INTENT_KEYS = frozenset(
    {
        "agenda_list",
        "arc_anchored_list",
        "chevron_chain_with_tail",
        "chevron_process",
        "circular_stages",
        "client_server_flow",
        "comparison_columns",
        "concentric_circles",
        "fishbone_diagram",
        "hub_inward_arrows",
        "hub_spoke",
        "icon_grid",
        "isometric_stairs",
        "journey_map",
        "kpi_cards",
        "labeled_card",
        "layered_architecture",
        "mind_map",
        "module_composition",
        "numbered_steps",
        "pipeline_with_stages",
        "process_flow",
        "pros_cons_chart",
        "pyramid_chart",
        "pyramid_isometric",
        "quadrant_bubble_scatter",
        "quadrant_text_bullets",
        "roadmap_vertical",
        "segmented_wheel",
        "snake_flow",
        "team_roster",
        "timeline",
        "top_down_tree",
        "venn_diagram",
        "vertical_list",
        "vertical_pillars",
    }
)


class VisualizationCatalogError(RuntimeError):
    """Reject an unreadable, malformed, missing, or ambiguous reference."""


@dataclass(frozen=True)
class VisualizationEntry:
    """One live SVG entry or one frozen legacy Structure intent."""

    family: str
    key: str
    summary: str
    path: Path | None
    kind: str = VISUALIZATION_SVG_KIND

    @property
    def reference(self) -> str:
        """Return the canonical live ``family/key`` reference."""
        if self.kind != VISUALIZATION_SVG_KIND:
            raise VisualizationCatalogError(
                f"legacy Structure intent {self.key!r} has no canonical reference"
            )
        return f"{self.family}/{self.key}"

    @property
    def display_path(self) -> str:
        """Return the Skill-relative SVG path."""
        if self.path is None:
            raise VisualizationCatalogError(
                f"{self.key!r} is a legacy Structure intent without an SVG path"
            )
        return self.path.relative_to(_SCRIPTS_DIR.parent).as_posix()


@dataclass(frozen=True)
class VisualizationCatalog:
    """Canonical entries plus family-local compatibility aliases."""

    entries: dict[str, VisualizationEntry]
    aliases: dict[str, str]


def visualization_families() -> tuple[str, ...]:
    """Return the stable live visualization family order."""
    return tuple(_FAMILY_SPECS)


def legacy_structure_intent_keys() -> tuple[str, ...]:
    """Return the frozen legacy ``page_charts`` Structure bare keys."""
    return tuple(sorted(_LEGACY_STRUCTURE_INTENT_KEYS))


def _normalize_families(families: Iterable[str] | None) -> tuple[str, ...]:
    requested = visualization_families() if families is None else tuple(families)
    normalized: list[str] = []
    for raw_family in requested:
        family = str(raw_family).strip().casefold()
        if family not in _FAMILY_SPECS:
            allowed = ", ".join(visualization_families())
            raise VisualizationCatalogError(
                f"unknown visualization family {raw_family!r}; expected one of {allowed}"
            )
        if family not in normalized:
            normalized.append(family)
    if not normalized:
        raise VisualizationCatalogError("at least one visualization family is required")
    return tuple(normalized)


def _load_family(family: str) -> tuple[dict[str, VisualizationEntry], dict[str, str]]:
    directory_name, index_name, object_key = _FAMILY_SPECS[family]
    family_dir = _TEMPLATES_DIR / directory_name
    index_path = family_dir / index_name
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualizationCatalogError(
            f"cannot read {family} catalog {index_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise VisualizationCatalogError(f"{family} catalog root must be an object")
    raw_entries = payload.get(object_key)
    if not isinstance(raw_entries, dict):
        raise VisualizationCatalogError(
            f"{family} catalog {index_path} has no '{object_key}' object"
        )

    entries: dict[str, VisualizationEntry] = {}
    for raw_key, raw_item in raw_entries.items():
        if (
            not isinstance(raw_key, str)
            or _KEY_RE.fullmatch(raw_key) is None
            or not isinstance(raw_item, dict)
        ):
            raise VisualizationCatalogError(
                f"{family} catalog entry {raw_key!r} is malformed"
            )
        summary = raw_item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise VisualizationCatalogError(
                f"{family} catalog entry {raw_key!r} has no non-empty summary"
            )
        entry = VisualizationEntry(
            family=family,
            key=raw_key,
            summary=summary.strip(),
            path=(family_dir / f"{raw_key}.svg").resolve(),
        )
        entries[entry.reference] = entry

    raw_aliases = payload.get("aliases", {})
    if not isinstance(raw_aliases, dict):
        raise VisualizationCatalogError(f"{family} catalog aliases must be an object")
    aliases: dict[str, str] = {}
    for raw_alias, raw_target in raw_aliases.items():
        if (
            not isinstance(raw_alias, str)
            or _KEY_RE.fullmatch(raw_alias) is None
            or not isinstance(raw_target, str)
            or _KEY_RE.fullmatch(raw_target) is None
        ):
            raise VisualizationCatalogError(
                f"{family} catalog alias {raw_alias!r} is malformed"
            )
        target_reference = f"{family}/{raw_target}"
        if raw_alias in raw_entries:
            raise VisualizationCatalogError(
                f"{family} alias {raw_alias!r} collides with a canonical key"
            )
        if target_reference not in entries:
            raise VisualizationCatalogError(
                f"{family} alias {raw_alias!r} targets missing key {raw_target!r}"
            )
        aliases[f"{family}/{raw_alias}"] = target_reference
    return entries, aliases


def load_visualization_catalog(
    families: Iterable[str] | None = None,
) -> VisualizationCatalog:
    """Load selected live family registries."""
    selected = _normalize_families(families)
    entries: dict[str, VisualizationEntry] = {}
    aliases: dict[str, str] = {}
    for family in selected:
        family_entries, family_aliases = _load_family(family)
        entries.update(family_entries)
        aliases.update(family_aliases)
    if not entries:
        shown = ", ".join(selected)
        raise VisualizationCatalogError(
            f"no visualization entries are available for family selection {shown}"
        )
    return VisualizationCatalog(entries=entries, aliases=aliases)


def load_visualization_entries(
    families: Iterable[str] | None = None,
) -> dict[str, VisualizationEntry]:
    """Return canonical entries keyed by ``family/key``."""
    return load_visualization_catalog(families).entries


def _require_svg(entry: VisualizationEntry) -> VisualizationEntry:
    if entry.kind != VISUALIZATION_SVG_KIND:
        raise VisualizationCatalogError(
            f"{entry.family}/{entry.key} has unsupported kind {entry.kind!r}"
        )
    if entry.path is None:
        raise VisualizationCatalogError(f"{entry.reference!r} has no SVG asset path")
    if entry.path.suffix.casefold() != ".svg" or not entry.path.is_file():
        raise VisualizationCatalogError(
            f"{entry.reference!r} has no SVG asset at {entry.path}"
        )
    return entry


def resolve_visualization_reference(
    value: str,
    *,
    allow_legacy_bare: bool = False,
) -> VisualizationEntry:
    """Resolve one live ``family/key`` or supported legacy bare key.

    Legacy Structure intents are accepted only when ``allow_legacy_bare`` is
    true. A qualified ``structure/<key>`` is never a live reference.
    """
    normalized = str(value).strip().casefold()
    if not normalized:
        raise VisualizationCatalogError("visualization reference must not be empty")

    catalog = load_visualization_catalog()
    if "/" in normalized:
        family, separator, key = normalized.partition("/")
        if (
            not separator
            or family not in _FAMILY_SPECS
            or _KEY_RE.fullmatch(key) is None
            or "/" in key
        ):
            raise VisualizationCatalogError(
                f"invalid canonical visualization reference {value!r}"
            )
        reference = f"{family}/{key}"
        entry = catalog.entries.get(reference)
        if entry is None:
            if reference in catalog.aliases:
                raise VisualizationCatalogError(
                    f"{value!r} is a legacy alias; use {catalog.aliases[reference]!r}"
                )
            raise VisualizationCatalogError(
                f"canonical visualization reference {value!r} is not registered"
            )
        return _require_svg(entry)

    if not allow_legacy_bare:
        raise VisualizationCatalogError(
            f"{value!r} must use canonical family/key grammar"
        )
    if _KEY_RE.fullmatch(normalized) is None:
        raise VisualizationCatalogError(f"invalid legacy visualization key {value!r}")

    matches = [
        entry
        for entry in catalog.entries.values()
        if entry.key == normalized
    ]
    for alias_reference, target_reference in catalog.aliases.items():
        _, alias = alias_reference.split("/", 1)
        if alias == normalized:
            matches.append(catalog.entries[target_reference])
    if normalized in _LEGACY_STRUCTURE_INTENT_KEYS:
        matches.append(
            VisualizationEntry(
                family="structure",
                key=normalized,
                summary=(
                    "Frozen legacy page_charts Structure intent; author the "
                    "page structure from its semantic relationships."
                ),
                path=None,
                kind=LEGACY_STRUCTURE_INTENT_KIND,
            )
        )
    unique_matches = {
        (entry.kind, entry.family, entry.key): entry
        for entry in matches
    }
    if not unique_matches:
        raise VisualizationCatalogError(
            f"legacy visualization key {value!r} is not registered"
        )
    if len(unique_matches) > 1:
        candidates = ", ".join(
            f"{family}/{key} ({kind})"
            for kind, family, key in sorted(unique_matches)
        )
        raise VisualizationCatalogError(
            f"legacy visualization key {value!r} is ambiguous across {candidates}"
        )
    resolved = next(iter(unique_matches.values()))
    if resolved.kind == LEGACY_STRUCTURE_INTENT_KIND:
        if resolved.path is not None:
            raise VisualizationCatalogError(
                f"legacy Structure intent {resolved.key!r} must not have an asset path"
            )
        return resolved
    return _require_svg(resolved)


if __name__ == "__main__" and any(
    arg in {"-h", "--help", "help"} for arg in sys.argv[1:]
):
    print(__doc__)
    raise SystemExit(0)


if __name__ == "__main__":
    from console_encoding import configure_utf8_stdio

    configure_utf8_stdio()
    print(
        "Use visualization_catalog via visualization_recall.py or project_manager.py.",
        file=sys.stderr,
    )
    raise SystemExit(2)
