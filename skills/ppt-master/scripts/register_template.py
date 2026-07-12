#!/usr/bin/env python3
"""Register a brand / layout / deck template into the global template index.

Three kinds, three workspace roots, three index files (see
``docs/zh/templates-architecture.md`` for the data model):

| --kind  | Workspace roots         | Index file                    |
|---------|-------------------------|-------------------------------|
| brand   | ``templates/brands/``   | ``brands_index.json``         |
| layout  | ``templates/layouts/``  | ``layouts_index.json``        |
| deck    | ``templates/decks/``    | ``decks_index.json``          |

Current layout/deck workspaces keep the source roster under
``<workspace>/templates/`` and the review PPTX under ``<workspace>/exports/``.
Legacy flat roots remain readable. Brand packaging is unchanged.

Index entry schemas (the JSON file is the single source of truth — README
files describe the kind and usage in prose but do **not** enumerate templates;
discovery happens exclusively against the index file):

- brand:  ``{ summary, primary_color }``
- layout: ``{ summary, canvas_format, page_count, page_types[] }``
- deck:   ``{ summary, canvas_format, page_count, primary_color }``

Usage::

    python3 scripts/register_template.py <id> --kind deck     # default kind=deck
    python3 scripts/register_template.py <id> --kind layout
    python3 scripts/register_template.py <id> --kind brand
    python3 scripts/register_template.py --rebuild-all --kind deck
    python3 scripts/register_template.py <id> --dry-run

``--rebuild-all`` rebuilds every entry from scratch within the chosen kind;
recommended for repairing index drift across many templates at once.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

from console_encoding import configure_utf8_stdio

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


configure_utf8_stdio()


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"

KIND_CONFIG = {
    "brand": {
        "dir": TEMPLATES_DIR / "brands",
        "index": TEMPLATES_DIR / "brands" / "brands_index.json",
        "id_key": "brand_id",
        "needs_svg_roster": False,
    },
    "layout": {
        "dir": TEMPLATES_DIR / "layouts",
        "index": TEMPLATES_DIR / "layouts" / "layouts_index.json",
        "id_key": "layout_id",
        "needs_svg_roster": True,
    },
    "deck": {
        "dir": TEMPLATES_DIR / "decks",
        "index": TEMPLATES_DIR / "decks" / "decks_index.json",
        "id_key": "deck_id",
        "needs_svg_roster": True,
    },
}


# ---------------------------------------------------------------------------
# design_spec.md parsing
# ---------------------------------------------------------------------------

class SpecParseError(RuntimeError):
    """Raised when a design_spec.md cannot be turned into an index entry."""


def _read_spec(spec_path: Path) -> tuple[dict | None, str]:
    """Split YAML frontmatter from the body. Returns ``(frontmatter, body)``."""
    text = spec_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fm_block = text[4:end]
    body = text[end + 5:]
    if yaml is None:
        raise SpecParseError(
            "design_spec.md has YAML frontmatter but PyYAML is not installed; "
            "install pyyaml or remove the frontmatter."
        )
    try:
        data = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError as exc:
        raise SpecParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecParseError("YAML frontmatter must be a mapping")
    return data, body


def _extract_section_field(body: str, section_title: str, labels: list[str]) -> str | None:
    section_re = re.compile(
        rf"^##\s+{re.escape(section_title)}\b.*?(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    section_match = section_re.search(body)
    if section_match is None:
        return None
    section = section_match.group(0)

    for label in labels:
        row = re.search(
            rf"^\|\s*\*?\*?{re.escape(label)}\*?\*?\s*\|\s*(.+?)\s*\|",
            section, re.MULTILINE | re.IGNORECASE,
        )
        if row:
            return _clean_field_value(row.group(1))

        bullet = re.search(
            rf"^[-*]\s*\*?\*?{re.escape(label)}\*?\*?\s*[:：]\s*(.+?)\s*$",
            section, re.MULTILINE | re.IGNORECASE,
        )
        if bullet:
            return _clean_field_value(bullet.group(1))
    return None


def _clean_field_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[`*_]+", "", value)
    value = re.sub(r"[`*_]+$", "", value)
    return value.strip()


def _find_first_color(section: str) -> str | None:
    match = re.search(r"`(#[0-9A-Fa-f]{3,8})`", section)
    return match.group(1).upper() if match else None


def _extract_primary_color(body: str) -> str | None:
    section_match = re.search(
        r"^##\s+[IVX]+\.\s+Color Scheme\b.*?(?=^##\s+|\Z)",
        body, re.MULTILINE | re.DOTALL,
    )
    if section_match is None:
        return None
    return _find_first_color(section_match.group(0))


def _summary_from_use_cases(use_cases: str | None) -> str | None:
    if not use_cases:
        return None
    cleaned = use_cases.strip().rstrip(".")
    if not cleaned:
        return None
    return f"{cleaned}."


def _template_content_dir(template_root: Path) -> Path:
    """Resolve the canonical source directory, with legacy-flat compatibility."""
    nested = template_root / "templates"
    if (nested / "design_spec.md").is_file():
        return nested
    if (template_root / "design_spec.md").is_file():
        return template_root
    raise SpecParseError(
        f"missing templates/design_spec.md or legacy design_spec.md in {template_root}"
    )


def _list_pages(template_dir: Path) -> list[str]:
    return sorted(p.stem for p in template_dir.glob("*.svg"))


def _derive_page_types(pages: list[str]) -> list[str]:
    """Derive canonical page-type list from SVG filenames (strips leading 'NN_')."""
    types: list[str] = []
    seen: set[str] = set()
    for p in pages:
        m = re.match(r"^\d+[a-z]?_(.+)$", p)
        role = m.group(1) if m else p
        if role not in seen:
            seen.add(role)
            types.append(role)
    return types


# ---------------------------------------------------------------------------
# Per-kind extraction
# ---------------------------------------------------------------------------

def _extract_entry(kind: str, template_id: str, template_dir: Path) -> dict:
    """Build the index entry + extras for a single template."""
    template_root = template_dir
    template_dir = _template_content_dir(template_root)
    spec_path = template_dir / "design_spec.md"

    frontmatter, body = _read_spec(spec_path)
    fm = frontmatter or {}

    declared_kind = fm.get("kind")
    if declared_kind not in (None, kind):
        raise SpecParseError(
            f"design_spec.md frontmatter declares kind={declared_kind!r}; "
            f"expected kind={kind!r} — use --kind {declared_kind} instead"
        )

    summary = (fm.get("summary") or "").strip()
    if not summary:
        section_title = (
            "I. Brand Overview" if kind == "brand" else "I. Template Overview"
        )
        summary = (_summary_from_use_cases(
            _extract_section_field(body, section_title, ["Use Cases", "Use cases"])
        ) or "").strip()

    pages = _list_pages(template_dir)
    primary_color = fm.get("primary_color") or _extract_primary_color(body) or ""

    if kind == "brand":
        entry = OrderedDict(
            summary=summary,
            primary_color=str(primary_color),
        )
    elif kind == "layout":
        page_types = fm.get("page_types") or _derive_page_types(pages)
        if isinstance(page_types, str):
            page_types = [t.strip() for t in re.split(r"[,，]", page_types) if t.strip()]
        entry = OrderedDict(
            summary=summary,
            canvas_format=str(fm.get("canvas_format", "ppt169")),
            page_count=int(fm.get("page_count", len(pages))),
            page_types=list(page_types),
        )
    elif kind == "deck":
        entry = OrderedDict(
            summary=summary,
            canvas_format=str(fm.get("canvas_format", "ppt169")),
            page_count=int(fm.get("page_count", len(pages))),
            primary_color=str(primary_color),
        )
    else:
        raise SpecParseError(f"unknown kind {kind!r}")

    extras = OrderedDict(
        pages=pages,
        primary_color=str(primary_color),
        page_prefix="templates/" if template_dir != template_root else "",
        preview=(
            f"exports/{template_id}_template_preview.pptx"
            if (template_root / "exports" / f"{template_id}_template_preview.pptx").is_file()
            else ""
        ),
    )
    return {"entry": entry, "extras": extras}


# ---------------------------------------------------------------------------
# Index / README writers
# ---------------------------------------------------------------------------

def _load_index(path: Path) -> "OrderedDict[str, dict]":
    if not path.exists():
        return OrderedDict()
    raw_text = path.read_text(encoding="utf-8").strip() or "{}"
    raw = json.loads(raw_text)
    return OrderedDict(sorted(raw.items()))


def _write_index(path: Path, data: "OrderedDict[str, dict]", *, dry_run: bool) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        print(f"--- {path.name} (dry-run) ---")
        print(payload)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _enumerate_ids(kind: str) -> list[str]:
    base = KIND_CONFIG[kind]["dir"]
    if not base.exists():
        return []
    return sorted(
        p.name for p in base.iterdir()
        if p.is_dir()
        and (
            (p / "templates" / "design_spec.md").is_file()
            or (p / "design_spec.md").is_file()
        )
    )


def _print_completion_card(kind: str, template_id: str, entry: dict, extras: dict) -> None:
    pretty_kind = {"layout": "Layout", "deck": "Deck", "brand": "Brand"}[kind]
    dir_name = {"layout": "layouts", "deck": "decks", "brand": "brands"}[kind]
    print()
    print(f"## {pretty_kind} Registration Complete")
    print()
    print(f"**{pretty_kind} ID**: {template_id}")
    print(f"**Path**: `templates/{dir_name}/{template_id}/`")
    if kind in ("brand", "deck"):
        primary = entry.get("primary_color") or "—"
        print(f"**Primary Color**: {primary}")
    if kind in ("layout", "deck"):
        canvas = entry.get("canvas_format") or "—"
        pc = entry.get("page_count") or "—"
        print(f"**Canvas**: {canvas}")
        print(f"**Pages**: {pc}")
    print(f"**Summary**: {entry.get('summary') or '—'}")
    print("**Index Registration**: Done")
    print()
    if kind != "brand":
        pages = extras.get("pages") or []
        page_prefix = extras.get("page_prefix") or ""
        preview = extras.get("preview") or ""
        if preview:
            print(f"**Review PPTX**: `{preview}`")
            print()
        if pages:
            print("### Files Included")
            print()
            print("| File | Status |")
            print("|------|--------|")
            for page in pages:
                print(f"| `{page_prefix}{page}.svg` | Done |")
            if preview:
                print(f"| `{preview}` | Verified |")
            print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register / refresh templates (brand / layout / deck) in the index."
    )
    parser.add_argument(
        "template_id", nargs="?",
        help="Template directory id (under templates/<kind_dir>/). Omit with --rebuild-all.",
    )
    parser.add_argument(
        "--kind", choices=list(KIND_CONFIG.keys()), default="deck",
        help="Template kind (default: deck).",
    )
    parser.add_argument("--rebuild-all", action="store_true",
                        help="Rebuild every index entry within the chosen kind.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be written without modifying any files.")
    args = parser.parse_args()

    if not args.template_id and not args.rebuild_all:
        parser.error("provide a template_id or use --rebuild-all")

    cfg = KIND_CONFIG[args.kind]
    base = cfg["dir"]

    if args.rebuild_all:
        ids = _enumerate_ids(args.kind)
        if not ids:
            print(f"[OK] No {args.kind} directories found; index left empty.")
            _write_index(cfg["index"], OrderedDict(), dry_run=args.dry_run)
            return 0
    else:
        ids = [args.template_id]
        spec_dir = base / args.template_id
        if not spec_dir.is_dir():
            print(f"Error: {args.kind} directory not found: {spec_dir}", file=sys.stderr)
            return 1

    extracted: dict[str, dict] = {}
    for tid in ids:
        try:
            extracted[tid] = _extract_entry(args.kind, tid, base / tid)
        except SpecParseError as exc:
            print(f"Error: {tid}: {exc}", file=sys.stderr)
            return 1

    if args.rebuild_all:
        index = OrderedDict((tid, extracted[tid]["entry"]) for tid in sorted(extracted))
    else:
        index = _load_index(cfg["index"])
        for tid, payload in extracted.items():
            index[tid] = payload["entry"]
        index = OrderedDict(sorted(index.items()))

    _write_index(cfg["index"], index, dry_run=args.dry_run)

    if not args.dry_run and not args.rebuild_all:
        tid = args.template_id
        _print_completion_card(
            args.kind, tid, extracted[tid]["entry"], extracted[tid]["extras"]
        )
        return 0

    print()
    print(
        f"[OK] {'Dry-run preview' if args.dry_run else 'Updated'}: "
        f"{len(extracted)} {args.kind}(s) processed; index now lists {len(index)} entries."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
