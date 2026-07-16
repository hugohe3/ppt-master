#!/usr/bin/env python3
"""Register a brand / layout / deck template into the global template index.

Three kinds, three workspace roots, three index files. The shared model lives
in ``templates/README.md``; each kind's schema lives in its directory README:

| --kind  | Workspace roots         | Index file                    |
|---------|-------------------------|-------------------------------|
| brand   | ``templates/brands/``   | ``brands_index.json``         |
| layout  | ``templates/layouts/``  | ``layouts_index.json``        |
| deck    | ``templates/decks/``    | ``decks_index.json``          |

Current workspaces keep ``design_spec.md`` and any SVG roster under
``<workspace>/templates/``. Assets live in optional ``images/`` / ``icons/``
directories. Explicitly generated review artifacts go to the optional, ignored
``exports/`` directory. Legacy flat roots remain readable.

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

Project-scoped Brand workspaces are validated, not registered, through
``svg_quality_checker.py <workspace>/templates --template-mode``. That entry
reuses :func:`validate_brand_workspace`, so the Brand schema has one authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from config import CANVAS_FORMATS

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

_BRAND_REQUIRED_SECTIONS = (
    ("I", "Brand Overview"),
    ("II", "Color Scheme"),
    ("III", "Typography"),
    ("IV", "Logo"),
    ("V", "Voice & Tone"),
    ("VI", "Icon Style"),
)
_BRAND_FORBIDDEN_SECTIONS = (
    "Page Roster",
    "Signature Design Elements",
)
_BRAND_ALLOWED_FRONTMATTER_FIELDS = frozenset({
    "brand_id",
    "kind",
    "summary",
    "primary_color",
})
_BRAND_PROVENANCE_VALUES = {"fact", "approx", "user"}
_BRAND_ASSET_REF_RE = re.compile(
    r"`((?:\.\./)+(?:images|icons)/[^`]+)`"
)
_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")


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


def _numbered_section(body: str, title: str) -> str | None:
    match = re.search(
        rf"^##\s+[IVX]+\.\s+{re.escape(title)}\s*$.*?(?=^##\s+|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(0) if match else None


def _validate_brand_spec(
    expected_template_id: str | None,
    template_root: Path,
    template_dir: Path,
    frontmatter: dict,
    body: str,
    pages: list[str],
) -> None:
    """Reject brand workspaces that cannot be locked as portable identity truth.

    Args:
        expected_template_id: Registry key to match in library scope. Project
            workspaces pass ``None`` because their root name is the project id,
            not the portable brand id.
        template_root: Brand workspace root containing assets and templates.
        template_dir: Directory containing ``design_spec.md`` and any page SVGs.
        frontmatter: Parsed design-spec frontmatter.
        body: Markdown content after the frontmatter block.
        pages: SVG page stems discovered beside the design spec.
    """
    errors: list[str] = []

    declared_id = str(frontmatter.get("brand_id") or "").strip()
    if not declared_id:
        errors.append("frontmatter brand_id must be non-empty")
    elif expected_template_id is not None and declared_id != expected_template_id:
        errors.append(
            "frontmatter brand_id must match directory "
            f"{expected_template_id!r}, "
            f"got {declared_id!r}"
        )

    declared_kind = str(frontmatter.get("kind") or "").strip()
    if declared_kind != "brand":
        errors.append(
            "frontmatter kind must be 'brand', "
            f"got {declared_kind!r}"
        )

    if not str(frontmatter.get("summary") or "").strip():
        errors.append("frontmatter summary must be non-empty")

    unexpected_fields = sorted(
        set(frontmatter) - _BRAND_ALLOWED_FRONTMATTER_FIELDS
    )
    if unexpected_fields:
        errors.append(
            "brand frontmatter contains non-identity field(s): "
            + ", ".join(unexpected_fields)
        )

    if pages:
        errors.append(
            "brand workspaces must not contain page SVGs under templates/: "
            + ", ".join(f"{page}.svg" for page in pages)
        )

    for numeral, title in _BRAND_REQUIRED_SECTIONS:
        if re.search(
            rf"^##\s+{numeral}\.\s+{re.escape(title)}\s*$",
            body,
            re.MULTILINE,
        ) is None:
            errors.append(f"missing required section: {numeral}. {title}")

    for title in _BRAND_FORBIDDEN_SECTIONS:
        if re.search(
            rf"^##\s+(?:[IVX]+\.\s+)?{re.escape(title)}\s*$",
            body,
            re.MULTILINE,
        ):
            errors.append(f"brand scope must not declare section: {title}")

    declared_primary = str(frontmatter.get("primary_color") or "").strip()
    if _HEX_COLOR_RE.fullmatch(declared_primary) is None:
        errors.append(
            "frontmatter primary_color must use #RRGGBB, "
            f"got {declared_primary!r}"
        )

    color_section = _numbered_section(body, "Color Scheme") or ""
    primary_rows: list[str] = []
    for line in color_section.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        role = cells[0].strip("` ")
        raw_color = cells[1].strip("` ")
        if role.lower() == "role" or re.fullmatch(r":?-+:?", role):
            continue
        if _HEX_COLOR_RE.fullmatch(raw_color) is None:
            errors.append(
                f"color row {role!r} must use #RRGGBB, "
                f"got {raw_color!r}"
            )
            continue
        if role.lower() == "primary":
            primary_rows.append(raw_color.upper())
        provenance = cells[2].strip("` ").lower()
        if provenance not in _BRAND_PROVENANCE_VALUES:
            errors.append(
                f"color {raw_color} must declare provenance as "
                "fact, approx, or user"
            )

    if not primary_rows:
        errors.append("Color Scheme must declare one primary color row")
    elif len(primary_rows) > 1:
        errors.append("Color Scheme must declare only one primary color row")
    elif (
        _HEX_COLOR_RE.fullmatch(declared_primary)
        and primary_rows[0] != declared_primary.upper()
    ):
        errors.append(
            "Color Scheme primary must match frontmatter primary_color: "
            f"{primary_rows[0]} != {declared_primary.upper()}"
        )

    root = template_root.resolve()
    for raw_ref in sorted(set(_BRAND_ASSET_REF_RE.findall(body))):
        asset = (template_dir / raw_ref).resolve()
        try:
            asset.relative_to(root)
        except ValueError:
            errors.append(f"asset reference escapes brand workspace: {raw_ref}")
            continue
        if not asset.is_file():
            errors.append(f"referenced brand asset does not exist: {raw_ref}")

    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise SpecParseError(f"invalid brand specification:\n{details}")


def _validate_svg_template_spec(
    kind: str,
    template_id: str,
    template_dir: Path,
    frontmatter: dict,
    pages: list[str],
) -> None:
    """Reject Layout/Deck workspaces whose registry facts drift from SVGs."""
    errors: list[str] = []
    id_key = KIND_CONFIG[kind]["id_key"]
    declared_id = str(frontmatter.get(id_key) or "").strip()
    if declared_id != template_id:
        errors.append(
            f"frontmatter {id_key} must match directory {template_id!r}, "
            f"got {declared_id!r}"
        )
    declared_kind = str(frontmatter.get("kind") or "").strip()
    if declared_kind != kind:
        errors.append(
            f"frontmatter kind must be {kind!r}, got {declared_kind!r}"
        )
    if not str(frontmatter.get("summary") or "").strip():
        errors.append("frontmatter summary must be non-empty")
    if not pages:
        errors.append(f"{kind} workspace must contain at least one template SVG")

    raw_page_count = frontmatter.get("page_count")
    if isinstance(raw_page_count, bool) or not isinstance(raw_page_count, int):
        errors.append("frontmatter page_count must be an integer")
    elif raw_page_count != len(pages):
        errors.append(
            f"frontmatter page_count is {raw_page_count}, but templates/ "
            f"contains {len(pages)} SVG files"
        )

    canvas_format = str(frontmatter.get("canvas_format") or "").strip()
    canvas = CANVAS_FORMATS.get(canvas_format)
    if canvas is None:
        errors.append(
            "frontmatter canvas_format must be one of: "
            + ", ".join(sorted(CANVAS_FORMATS))
        )
    else:
        expected_canvas_fields = {
            "canvas_width": canvas["width"],
            "canvas_height": canvas["height"],
            "canvas_viewbox": canvas["viewbox"],
        }
        for field, expected in expected_canvas_fields.items():
            actual = frontmatter.get(field)
            if str(actual) != str(expected):
                errors.append(
                    f"frontmatter {field} must be {expected!r} for "
                    f"{canvas_format}, got {actual!r}"
                )

    if frontmatter.get("native_structure_mode") != "structured":
        errors.append(
            "frontmatter native_structure_mode must be 'structured'"
        )
    if frontmatter.get("replication_mode") not in {
        "standard",
        "fidelity",
        "mirror",
    }:
        errors.append(
            "frontmatter replication_mode must be standard, fidelity, or mirror"
        )

    if kind == "layout":
        raw_page_types = frontmatter.get("page_types")
        expected_page_types = _derive_page_types(pages)
        if not isinstance(raw_page_types, list) or not all(
            isinstance(item, str) and item.strip()
            for item in raw_page_types
        ):
            errors.append("frontmatter page_types must be a non-empty string list")
        elif raw_page_types != expected_page_types:
            errors.append(
                "frontmatter page_types must exactly match the SVG filename "
                f"roster: expected {expected_page_types!r}, got {raw_page_types!r}"
            )
    else:
        primary_color = str(frontmatter.get("primary_color") or "").strip()
        if _HEX_COLOR_RE.fullmatch(primary_color) is None:
            errors.append(
                "frontmatter primary_color must use #RRGGBB, "
                f"got {primary_color!r}"
            )

    svg_paths = [template_dir / f"{page}.svg" for page in pages]
    if canvas is not None:
        expected_viewbox = str(canvas["viewbox"])
        for svg_path in svg_paths:
            try:
                root = ET.parse(svg_path).getroot()
            except (OSError, ET.ParseError) as exc:
                errors.append(f"{svg_path.name} is not valid SVG XML: {exc}")
                continue
            actual_canvas = (
                root.get("width"),
                root.get("height"),
                root.get("viewBox"),
            )
            expected_canvas = (
                str(canvas["width"]),
                str(canvas["height"]),
                expected_viewbox,
            )
            if actual_canvas != expected_canvas:
                errors.append(
                    f"{svg_path.name} canvas is {actual_canvas!r}, expected "
                    f"{expected_canvas!r}"
                )

    if svg_paths:
        try:
            from svg_to_pptx.pptx_package.template_structure import (
                TemplateStructureError,
                parse_template_slides,
            )
        except ImportError as exc:
            errors.append(f"structured SVG roster is invalid: {exc}")
        else:
            try:
                parse_template_slides(svg_paths)
            except TemplateStructureError as exc:
                errors.append(f"structured SVG roster is invalid: {exc}")

    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise SpecParseError(f"invalid {kind} specification:\n{details}")


# ---------------------------------------------------------------------------
# Per-kind extraction
# ---------------------------------------------------------------------------

def _extract_entry(
    kind: str,
    template_id: str | None,
    template_dir: Path,
) -> dict:
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
    resolved_template_id = (
        template_id
        or str(fm.get(KIND_CONFIG[kind]["id_key"]) or "").strip()
        or template_root.name
    )

    if kind == "brand":
        _validate_brand_spec(
            template_id,
            template_root,
            template_dir,
            fm,
            body,
            pages,
        )
        entry = OrderedDict(
            summary=summary,
            primary_color=str(primary_color),
        )
    elif kind == "layout":
        if template_id is None:
            raise SpecParseError("layout validation requires an expected layout_id")
        _validate_svg_template_spec(
            kind,
            template_id,
            template_dir,
            fm,
            pages,
        )
        page_types = fm["page_types"]
        entry = OrderedDict(
            summary=summary,
            canvas_format=str(fm["canvas_format"]),
            page_count=int(fm["page_count"]),
            page_types=list(page_types),
        )
    elif kind == "deck":
        if template_id is None:
            raise SpecParseError("deck validation requires an expected deck_id")
        _validate_svg_template_spec(
            kind,
            template_id,
            template_dir,
            fm,
            pages,
        )
        entry = OrderedDict(
            summary=summary,
            canvas_format=str(fm["canvas_format"]),
            page_count=int(fm["page_count"]),
            primary_color=str(primary_color),
        )
    else:
        raise SpecParseError(f"unknown kind {kind!r}")

    extras = OrderedDict(
        pages=pages,
        primary_color=str(primary_color),
        page_prefix="templates/" if template_dir != template_root else "",
        preview=(
            f"exports/{resolved_template_id}_template_preview.pptx"
            if (
                template_root
                / "exports"
                / f"{resolved_template_id}_template_preview.pptx"
            ).is_file()
            else ""
        ),
    )
    return {"entry": entry, "extras": extras}


def validate_brand_workspace(template_root: str | Path) -> dict:
    """Validate a portable Brand workspace without registering it.

    This is the project-scope entry used by ``svg_quality_checker.py
    --template-mode``. Library registration calls the same extraction path with
    an expected directory id, so both scopes share one Brand schema authority.
    """
    return _extract_entry("brand", None, Path(template_root))


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
