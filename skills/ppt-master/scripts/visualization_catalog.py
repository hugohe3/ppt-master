#!/usr/bin/env python3
"""
PPT Master - Visualization Catalog Resolver

Resolve chart, structure, and table references from their live family indexes.

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
    "structure": ("structures", "structures_index.json", "structures"),
    "table": ("tables", "tables_index.json", "tables"),
}


class VisualizationCatalogError(RuntimeError):
    """Reject an unreadable, malformed, missing, or ambiguous reference."""


@dataclass(frozen=True)
class VisualizationEntry:
    """One canonical family catalog entry and its SVG asset."""

    family: str
    key: str
    summary: str
    path: Path

    @property
    def kind(self) -> str:
        """Return the page-context reference kind."""
        return "visualization-svg"

    @property
    def reference(self) -> str:
        """Return the canonical ``family/key`` reference."""
        return f"{self.family}/{self.key}"

    @property
    def display_path(self) -> str:
        """Return the Skill-relative SVG path."""
        return self.path.relative_to(_SCRIPTS_DIR.parent).as_posix()


@dataclass(frozen=True)
class VisualizationCatalog:
    """Canonical entries plus family-local compatibility aliases."""

    entries: dict[str, VisualizationEntry]
    aliases: dict[str, str]


def visualization_families() -> tuple[str, ...]:
    """Return the stable visualization family order."""
    return tuple(_FAMILY_SPECS)


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
    """Resolve one canonical ``family/key`` or supported legacy bare key."""
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
    unique_matches = {entry.reference: entry for entry in matches}
    if not unique_matches:
        raise VisualizationCatalogError(
            f"legacy visualization key {value!r} is not registered"
        )
    if len(unique_matches) > 1:
        candidates = ", ".join(sorted(unique_matches))
        raise VisualizationCatalogError(
            f"legacy visualization key {value!r} is ambiguous across {candidates}"
        )
    return _require_svg(next(iter(unique_matches.values())))


if __name__ == "__main__":
    from console_encoding import configure_utf8_stdio

    configure_utf8_stdio()
    print(
        "Use visualization_catalog via visualization_recall.py or project_manager.py.",
        file=sys.stderr,
    )
    raise SystemExit(2)
