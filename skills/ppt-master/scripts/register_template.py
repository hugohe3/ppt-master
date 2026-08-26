#!/usr/bin/env python3
"""Register a brand / style / layout / deck template in the global index.

Four kinds, four workspace roots, four index files. The shared model lives
in ``templates/README.md``; each kind's schema lives in its directory README:

| --kind  | Workspace roots         | Index file                    |
|---------|-------------------------|-------------------------------|
| brand   | ``templates/brands/``   | ``brands_index.json``         |
| style   | ``templates/styles/``   | ``styles_index.json``         |
| layout  | ``templates/layouts/``  | ``layouts_index.json``        |
| deck    | ``templates/decks/``    | ``decks_index.json``          |

Current workspaces keep ``design_spec.md`` and any SVG roster under
``<workspace>/templates/``. Assets live in optional ``images/`` / ``icons/``
directories. Explicitly generated review artifacts go to the optional, ignored
``exports/`` directory. Every kind uses this nested workspace contract.

Index entry schemas (the JSON file is the single source of truth — README
files describe the kind and usage in prose but do **not** enumerate templates;
discovery happens exclusively against the index file):

- brand:  ``{ summary, primary_color }``
- style:  ``{ summary, keywords[] }``
- layout: ``{ summary, canvas_format, page_count, page_types[] }``
- deck:   ``{ summary, canvas_format, page_count, primary_color }``

Usage::

    python3 scripts/register_template.py <id> --kind deck     # default kind=deck
    python3 scripts/register_template.py <id> --kind layout
    python3 scripts/register_template.py <id> --kind brand
    python3 scripts/register_template.py <id> --kind style
    python3 scripts/register_template.py --rebuild-all --kind deck
    python3 scripts/register_template.py <id> --dry-run

``--rebuild-all`` rebuilds every entry from scratch within the chosen kind;
recommended for repairing index drift across many templates at once.

Project-scoped Brand and Style workspaces are validated, not registered,
through ``svg_quality_checker.py <workspace>/templates --template-mode``. That
entry reuses :func:`validate_brand_workspace` or
:func:`validate_style_workspace`, so each schema has one authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

from attribution_guard import require_skill_integrity
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
    "style": {
        "dir": TEMPLATES_DIR / "styles",
        "index": TEMPLATES_DIR / "styles" / "styles_index.json",
        "id_key": "style_id",
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
_STYLE_REQUIRED_SECTIONS = (
    ("I", "Style Overview"),
    ("II", "Communication Method"),
    ("III", "Page Role Vocabulary"),
    ("IV", "Evidence & Data Expression"),
    ("V", "Visual System Defaults"),
    ("VI", "Image & Icon Direction"),
    ("VII", "Review Focus"),
)
_STYLE_FORBIDDEN_SECTIONS = (
    "Brand Overview",
    "Template Overview",
    "Color Scheme",
    "Typography",
    "Logo",
    "Voice & Tone",
    "Icon Style",
    "Assets",
    "Signature Design Elements",
    "Page Roster",
    "Placeholder Overrides",
)
_STYLE_REQUIRED_FIELDS = {
    "I. Style Overview": (
        "Style Name",
        "Best Fit",
        "Reusable Intent",
        "Sources",
    ),
    "II. Communication Method": (
        "Argument Flow",
        "Page Message Discipline",
        "Claim Discipline",
    ),
    "IV. Evidence & Data Expression": (
        "Argument Trace",
        "Charts",
        "Tables",
        "Sources",
        "Native Editability",
    ),
    "V. Visual System Defaults": (
        "Composition",
        "Density",
        "Decoration",
        "Color Behavior",
        "Typography Character",
    ),
    "VI. Image & Icon Direction": (
        "Image Usage",
        "Image Treatment",
        "Icon Treatment",
    ),
}
_STYLE_CUSTOM_FIELDS = (
    (
        "II. Communication Method",
        "Preferred Mode",
        "Mode Behavior",
        "Mode References",
        SKILL_DIR / "references" / "modes",
    ),
    (
        "V. Visual System Defaults",
        "Preferred Visual Style",
        "Visual Style Behavior",
        "Visual Style References",
        SKILL_DIR / "references" / "visual-styles",
    ),
    (
        "VI. Image & Icon Direction",
        "Preferred Image Rendering",
        "Image Rendering Behavior",
        "Image Rendering References",
        SKILL_DIR / "references" / "image-renderings",
    ),
)
_STYLE_FORBIDDEN_FIELDS = (
    "Brand Overview",
    "Template Overview",
    "Color Scheme",
    "Typography",
    "Signature Design Elements",
    "Page Roster",
    "Placeholder Overrides",
    "Target Audience",
    "Communication Objective",
    "Desired Outcome",
    "Core Message",
    "Delivery Context",
    "Artifact Afterlife",
    "Application Context",
    "Content Outline",
    "Page Count",
    "Page Types",
    "Page Order",
    "Page Sequence",
    "Canvas Format",
    "Canvas Width",
    "Canvas Height",
    "Canvas ViewBox",
    "Replication Mode",
    "Native Structure Mode",
    "Master",
    "Layout",
    "Placeholders",
    "Page Assignment",
    "Icon Inventory",
    "Image Resources",
    "Primary Color",
    "Logo",
    "Voice & Tone",
    "Icon Style",
    "Assets",
)
_STYLE_ALLOWED_FRONTMATTER_FIELDS = frozenset({
    "style_id",
    "kind",
    "summary",
    "keywords",
})
_STYLE_REVIEW_TRIGGER_MARKER = "<!-- visual-review-trigger: explicit-user-only -->"
_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_PORTABLE_STYLE_ID_RE = re.compile(r"^\w[\w.-]*$")


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


_SPEC_NAME_RE = re.compile(
    r"design_spec\.(?P<kind>brand|style|layout|deck)\.(?P<id>[^/\\]+)\.md"
)


def _has_kind_qualified_spec(directory: Path) -> bool:
    """Report whether a directory holds any ``design_spec.<kind>.<id>.md``."""
    if not directory.is_dir():
        return False
    return any(
        _SPEC_NAME_RE.fullmatch(path.name)
        for path in directory.glob("design_spec.*.md")
    )


def _qualified_template_specs(directory: Path) -> list[tuple[Path, str]]:
    """Return kind-qualified specs and their filename-declared kinds."""
    if not directory.is_dir():
        return []
    specs = []
    for path in sorted(directory.glob("design_spec.*.md")):
        match = _SPEC_NAME_RE.fullmatch(path.name)
        if match is not None:
            specs.append((path, match.group("kind")))
    return specs


def validate_qualified_spec_identity(
    spec_path: str | Path,
) -> tuple[str, str, dict, str]:
    """Match one qualified filename's kind and id to its frontmatter."""
    path = Path(spec_path)
    match = _SPEC_NAME_RE.fullmatch(path.name)
    if match is None:
        raise SpecParseError(
            "qualified Design Spec must be named "
            "design_spec.<kind>.<id>.md: "
            f"{path.name}"
        )

    filename_kind = match.group("kind")
    filename_id = match.group("id")
    frontmatter, body = _read_spec(path)
    fm = frontmatter or {}
    declared_kind = str(fm.get("kind") or "").strip()
    id_key = KIND_CONFIG[filename_kind]["id_key"]
    declared_id = str(fm.get(id_key) or "").strip()
    errors: list[str] = []
    if declared_kind != filename_kind:
        errors.append(
            f"filename kind {filename_kind!r} must match frontmatter kind "
            f"{declared_kind!r}"
        )
    if declared_id != filename_id:
        errors.append(
            f"filename id {filename_id!r} must match frontmatter {id_key} "
            f"{declared_id!r}"
        )
    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise SpecParseError(
            f"invalid qualified Design Spec identity ({path.name}):\n{details}"
        )
    return filename_kind, filename_id, fm, body


def _validate_spec_shape(template_dir: Path) -> list[tuple[Path, str]]:
    """Reject ambiguous project-spec naming and duplicate kind ownership."""
    exact = template_dir / "design_spec.md"
    qualified = _qualified_template_specs(template_dir)
    if exact.is_file() and qualified:
        raise SpecParseError(
            "design_spec.md and design_spec.<kind>.<id>.md cannot share "
            f"{template_dir}; rename the bare spec to its kind-qualified name"
        )
    kinds = [kind for _path, kind in qualified]
    duplicate_kinds = sorted({
        kind for kind in kinds if kinds.count(kind) > 1
    })
    if duplicate_kinds:
        raise SpecParseError(
            f"{template_dir} declares the same kind more than once: "
            + ", ".join(duplicate_kinds)
        )
    for path, _kind in qualified:
        validate_qualified_spec_identity(path)
    return qualified


def _has_qualified_roster_spec(template_dir: Path) -> bool:
    """Return whether a project directory declares a structural kind."""
    return any(
        kind in {"layout", "deck"}
        for _path, kind in _qualified_template_specs(template_dir)
    )


def _template_content_dir(template_root: Path) -> Path:
    """Resolve the only canonical template source directory."""
    nested = template_root / "templates"
    if (nested / "design_spec.md").is_file() or _has_kind_qualified_spec(nested):
        return nested
    raise SpecParseError(
        "missing templates/design_spec.md or "
        f"templates/design_spec.<kind>.<id>.md in {template_root}"
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


def _markdown_subsection(body: str, title: str) -> str | None:
    match = re.search(
        rf"^###\s+{re.escape(title)}\s*$.*?(?=^#{{2,3}}\s+|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(0) if match else None


def _markdown_table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _style_value_is_substantive(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = _clean_field_value(value)
    if not cleaned or re.fullmatch(r"<[^>]+>", cleaned):
        return False
    return cleaned.casefold() not in {"tbd", "todo", "n/a", "none", "-", "—"}


def _style_field_is_declared(body: str, label: str) -> bool:
    escaped = re.escape(label)
    return bool(
        re.search(
            rf"^\s*(?:>\s*)?(?:[-*]\s*)?"
            rf"\*{{0,2}}{escaped}\*{{0,2}}\s*[:：]",
            body,
            re.MULTILINE | re.IGNORECASE,
        )
        or re.search(
            rf"^\|\s*\*{{0,2}}{escaped}\*{{0,2}}\s*\|",
            body,
            re.MULTILINE | re.IGNORECASE,
        )
    )


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

    # Project pages are valid only when one sibling Layout or Deck owns them.
    if pages and not _has_qualified_roster_spec(template_dir):
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


def _validate_style_spec(
    expected_template_id: str | None,
    template_root: Path,
    template_dir: Path,
    frontmatter: dict,
    body: str,
    pages: list[str],
) -> None:
    """Reject Style workspaces outside the roster-free method contract."""
    errors: list[str] = []

    raw_style_id = frontmatter.get("style_id")
    declared_id = raw_style_id.strip() if isinstance(raw_style_id, str) else ""
    if not declared_id:
        errors.append("frontmatter style_id must be a non-empty string")
    else:
        if (
            _PORTABLE_STYLE_ID_RE.fullmatch(declared_id) is None
            or declared_id in {".", ".."}
            or declared_id.endswith(".")
        ):
            errors.append(
                "frontmatter style_id must be a filesystem-safe portable slug"
            )
        if (
            expected_template_id is not None
            and declared_id != expected_template_id
        ):
            errors.append(
                "frontmatter style_id must match directory "
                f"{expected_template_id!r}, got {declared_id!r}"
            )

    raw_kind = frontmatter.get("kind")
    declared_kind = raw_kind.strip() if isinstance(raw_kind, str) else ""
    if declared_kind != "style":
        errors.append(
            "frontmatter kind must be 'style', "
            f"got {declared_kind!r}"
        )

    raw_summary = frontmatter.get("summary")
    if not isinstance(raw_summary, str) or not _style_value_is_substantive(
        raw_summary
    ):
        errors.append("frontmatter summary must be a non-empty string")

    non_string_fields = [key for key in frontmatter if not isinstance(key, str)]
    if non_string_fields:
        errors.append("style frontmatter field names must be strings")
    unexpected_fields = sorted(
        key
        for key in frontmatter
        if isinstance(key, str) and key not in _STYLE_ALLOWED_FRONTMATTER_FIELDS
    )
    if unexpected_fields:
        errors.append(
            "style frontmatter contains unsupported field(s): "
            + ", ".join(unexpected_fields)
        )

    keywords = frontmatter.get("keywords")
    if (
        not isinstance(keywords, list)
        or not 3 <= len(keywords) <= 5
        or not all(
            isinstance(item, str) and _style_value_is_substantive(item)
            for item in keywords
        )
    ):
        errors.append(
            "frontmatter keywords must contain 3-5 non-empty strings"
        )
    elif len({item.strip().casefold() for item in keywords}) != len(keywords):
        errors.append("frontmatter keywords must be unique")

    if pages and not _has_qualified_roster_spec(template_dir):
        errors.append(
            "style workspaces must not contain page SVGs without a sibling "
            "Layout or Deck owner: "
            + ", ".join(f"{page}.svg" for page in pages)
        )

    # The one-file packaging rule describes a workspace whose templates/ Style
    # owns alone. A project root shares that directory with other kinds, so the
    # rule there is only that Style itself contributes nothing but its spec.
    if (template_dir / "design_spec.md").is_file():
        unexpected_source_entries = sorted(
            path.relative_to(template_dir).as_posix()
            + ("/" if path.is_dir() else "")
            for path in template_dir.rglob("*")
            if path.relative_to(template_dir).as_posix() != "design_spec.md"
        )
        if unexpected_source_entries:
            errors.append(
                "style workspaces must contain only templates/design_spec.md; "
                "unexpected template entry(s): "
                + ", ".join(unexpected_source_entries)
            )

    if expected_template_id is not None:
        unexpected_workspace_entries = sorted(
            path.relative_to(template_root).as_posix()
            + ("/" if path.is_dir() else "")
            for path in template_root.rglob("*")
            if path.relative_to(template_root).as_posix()
            not in {"templates", "templates/design_spec.md"}
        )
        if unexpected_workspace_entries:
            errors.append(
                "library Style workspaces must contain only "
                "templates/design_spec.md; unexpected workspace entry(s): "
                + ", ".join(unexpected_workspace_entries)
            )

    h1_headings = re.findall(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    if len(h1_headings) != 1:
        errors.append(
            "style body must contain exactly one document-title H1; got "
            f"{len(h1_headings)}"
        )

    expected_headings = [
        f"{numeral}. {title}" for numeral, title in _STYLE_REQUIRED_SECTIONS
    ]
    actual_headings = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    if actual_headings != expected_headings:
        errors.append(
            "style body must contain exactly the required I-VII sections in "
            "order; got: " + (", ".join(actual_headings) or "none")
        )

    nested_headings = re.findall(
        r"^(#{3,6})\s+(.+?)\s*$",
        body,
        re.MULTILINE,
    )
    unexpected_nested_headings = [
        f"{marks} {title}"
        for marks, title in nested_headings
        if len(marks) != 3
        or title not in {"Fallback Color Scheme", "Fallback Typography"}
    ]
    if unexpected_nested_headings:
        errors.append(
            "style body contains unsupported nested heading(s): "
            + ", ".join(unexpected_nested_headings)
        )
    allowed_h3 = [title for marks, title in nested_headings if len(marks) == 3]
    if len(allowed_h3) != len(set(allowed_h3)):
        errors.append("style fallback subsections must not be repeated")

    for title in _STYLE_FORBIDDEN_SECTIONS:
        if re.search(
            rf"^#{{1,6}}\s+(?:[IVX]+\.\s+)?{re.escape(title)}\s*$",
            body,
            re.MULTILINE,
        ):
            errors.append(f"style scope must not declare section: {title}")

    for section_title, labels in _STYLE_REQUIRED_FIELDS.items():
        section_name = section_title.split(". ", 1)[1]
        if _numbered_section(body, section_name) is None:
            continue
        for label in labels:
            value = _extract_section_field(body, section_title, [label])
            if not _style_value_is_substantive(value):
                errors.append(
                    f"{section_title} must declare a non-empty {label} field"
                )

    role_section = _numbered_section(body, "Page Role Vocabulary") or ""
    role_rows = [
        row
        for row in _markdown_table_rows(role_section)
        if row and row[0].casefold() != "role"
    ]
    if not any(
        len(row) >= 4
        and all(_style_value_is_substantive(cell) for cell in row[:4])
        for row in role_rows
    ):
        errors.append(
            "III. Page Role Vocabulary must contain at least one complete "
            "four-column role row"
        )

    for (
        section_title,
        preferred_label,
        behavior_label,
        references_label,
        catalog_dir,
    ) in _STYLE_CUSTOM_FIELDS:
        preferred = _extract_section_field(
            body,
            section_title,
            [preferred_label],
        )
        behavior = _extract_section_field(
            body,
            section_title,
            [behavior_label],
        )
        references = _extract_section_field(
            body,
            section_title,
            [references_label],
        )
        preferred_text = _clean_field_value(preferred or "")
        catalog_ids = {
            path.stem
            for path in catalog_dir.glob("*.md")
            if not path.stem.startswith("_")
        }
        is_custom = bool(
            re.match(r"^custom(?:\b|\s*[:—-])", preferred_text, re.IGNORECASE)
        )
        if is_custom and not _style_value_is_substantive(behavior):
            errors.append(
                f"{behavior_label} is required when {preferred_label} is custom"
            )
        if not is_custom and _style_value_is_substantive(behavior):
            errors.append(
                f"{behavior_label} is allowed only when {preferred_label} is custom"
            )
        if not is_custom and _style_value_is_substantive(references):
            errors.append(
                f"{references_label} is allowed only when "
                f"{preferred_label} is custom"
            )
        if (
            _style_value_is_substantive(preferred)
            and not is_custom
            and preferred_text not in catalog_ids
        ):
            errors.append(
                f"{preferred_label} references unknown catalog id "
                f"{preferred_text!r}"
            )
        if is_custom and _style_value_is_substantive(references):
            catalog_references = [
                _clean_field_value(item)
                for item in (references or "").split(",")
            ]
            if any(not item for item in catalog_references):
                errors.append(
                    f"{references_label} must be a comma-separated list of "
                    "catalog ids"
                )
            duplicates = sorted(
                item
                for item in set(catalog_references)
                if catalog_references.count(item) > 1
            )
            if duplicates:
                errors.append(
                    f"{references_label} repeats catalog id(s): "
                    + ", ".join(duplicates)
                )
            unknown_references = sorted(
                item
                for item in set(catalog_references)
                if item == "custom" or item not in catalog_ids
            )
            if unknown_references:
                errors.append(
                    f"{references_label} references unknown catalog id(s): "
                    + ", ".join(unknown_references)
                )

    visual_section = _numbered_section(body, "Visual System Defaults") or ""
    fallback_colors = _markdown_subsection(body, "Fallback Color Scheme")
    if fallback_colors is not None:
        if "### Fallback Color Scheme" not in visual_section:
            errors.append("Fallback Color Scheme must appear under section V")
        color_rows = [
            row
            for row in _markdown_table_rows(fallback_colors)
            if row and row[0].casefold() != "role"
        ]
        if not color_rows:
            errors.append("Fallback Color Scheme must contain at least one row")
        for row in color_rows:
            if (
                len(row) < 3
                or not _style_value_is_substantive(row[0])
                or _HEX_COLOR_RE.fullmatch(row[1].strip("` ")) is None
                or not _style_value_is_substantive(row[2])
            ):
                errors.append(
                    "Fallback Color Scheme rows must be Role | #RRGGBB | Purpose"
                )
                break

    fallback_typography = _markdown_subsection(body, "Fallback Typography")
    if fallback_typography is not None:
        if "### Fallback Typography" not in visual_section:
            errors.append("Fallback Typography must appear under section V")
        typography_rows = [
            row
            for row in _markdown_table_rows(fallback_typography)
            if row and row[0].casefold() != "role"
        ]
        if not any(
            len(row) >= 4
            and all(_style_value_is_substantive(cell) for cell in row[:4])
            for row in typography_rows
        ):
            errors.append(
                "Fallback Typography must contain at least one complete "
                "four-column row"
            )

    review_section = _numbered_section(body, "Review Focus") or ""
    if review_section.count(_STYLE_REVIEW_TRIGGER_MARKER) != 1:
        errors.append(
            "VII. Review Focus must contain exactly one "
            f"{_STYLE_REVIEW_TRIGGER_MARKER} marker"
        )
    review_items = re.findall(r"^[-*]\s+(.+?)\s*$", review_section, re.MULTILINE)
    if not any(_style_value_is_substantive(item) for item in review_items):
        errors.append("VII. Review Focus must contain at least one check")

    for label in _STYLE_FORBIDDEN_FIELDS:
        if _style_field_is_declared(body, label):
            errors.append(f"style scope must not declare field: {label}")

    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise SpecParseError(f"invalid style specification:\n{details}")


def _validate_svg_template_spec(
    kind: str,
    template_id: str,
    template_dir: Path,
    frontmatter: dict,
    pages: list[str],
    *,
    validate_payload: bool = True,
) -> None:
    """Validate Layout/Deck metadata and, when active, its SVG payload."""
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
    if validate_payload and canvas is not None:
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

    if validate_payload and svg_paths:
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


def validate_shadowed_deck_spec(
    spec_path: str | Path,
    declared_pages: list[str],
) -> None:
    """Validate a Deck spec whose SVG roster is overridden by Layout."""
    path = Path(spec_path)
    match = _SPEC_NAME_RE.fullmatch(path.name)
    if match is None or match.group("kind") != "deck":
        raise SpecParseError(
            "shadowed Deck validation requires design_spec.deck.<id>.md"
        )
    _kind, filename_id, frontmatter, _body = validate_qualified_spec_identity(
        path
    )
    _validate_svg_template_spec(
        "deck",
        filename_id,
        path.parent,
        frontmatter,
        declared_pages,
        validate_payload=False,
    )


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
    if template_id is not None:
        exact_spec = template_dir / "design_spec.md"
        if not exact_spec.is_file():
            raise SpecParseError(
                "library workspaces require templates/design_spec.md; "
                "kind-qualified specs belong only to shared project roots"
            )
    spec_path = _resolve_spec_path(template_dir, kind)

    frontmatter, body = _read_spec(spec_path)
    fm = frontmatter or {}

    declared_kind = fm.get("kind")
    if declared_kind not in (None, kind):
        raise SpecParseError(
            f"design_spec.md frontmatter declares kind={declared_kind!r}; "
            f"expected kind={kind!r} — use --kind {declared_kind} instead"
        )

    raw_summary = fm.get("summary")
    summary = raw_summary.strip() if isinstance(raw_summary, str) else ""
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
    elif kind == "style":
        _validate_style_spec(
            template_id,
            template_root,
            template_dir,
            fm,
            body,
            pages,
        )
        entry = OrderedDict(
            summary=summary,
            keywords=[item.strip() for item in fm["keywords"]],
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
        page_prefix="templates/",
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


def _resolve_spec_path(template_dir: Path, kind: str) -> Path:
    """Return the Design Spec one kind owns inside a template source directory.

    A library workspace keeps the exact ``design_spec.md`` because
    ``<kind_dir>/<template_id>/`` already names its kind and id. A project
    workspace root has no such parent, so it keeps
    ``design_spec.<kind>.<id>.md`` and may hold one spec per kind side by side.
    """
    qualified = _validate_spec_shape(template_dir)
    exact = template_dir / "design_spec.md"
    if exact.is_file():
        return exact
    matches = sorted(
        path for path, declared_kind in qualified if declared_kind == kind
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SpecParseError(
            f"missing design_spec.md or design_spec.{kind}.<id>.md in {template_dir}"
        )
    raise SpecParseError(
        f"{template_dir} declares kind {kind!r} more than once: "
        + ", ".join(path.name for path in matches)
    )


def validate_brand_workspace(template_root: str | Path) -> dict:
    """Validate a portable Brand workspace without registering it.

    This is the project-scope entry used by ``svg_quality_checker.py
    --template-mode``. Library registration calls the same extraction path with
    an expected directory id, so both scopes share one Brand schema authority.
    """
    return _extract_entry("brand", None, Path(template_root))


def validate_style_workspace(template_root: str | Path) -> dict:
    """Validate a portable Style workspace without registering it.

    Global library roots also enforce directory identity and the one-file
    package boundary. Project roots keep their unrelated initialized-project
    scaffolding out of the Style contract.
    """
    root = Path(template_root)
    expected_id = (
        root.name
        if root.resolve().parent == KIND_CONFIG["style"]["dir"].resolve()
        else None
    )
    return _extract_entry("style", expected_id, root)


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
        and (p / "templates" / "design_spec.md").is_file()
    )


def _print_completion_card(kind: str, template_id: str, entry: dict, extras: dict) -> None:
    pretty_kind = {
        "layout": "Layout",
        "deck": "Deck",
        "brand": "Brand",
        "style": "Style",
    }[kind]
    dir_name = {
        "layout": "layouts",
        "deck": "decks",
        "brand": "brands",
        "style": "styles",
    }[kind]
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
    if KIND_CONFIG[kind]["needs_svg_roster"]:
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
    require_skill_integrity()
    parser = argparse.ArgumentParser(
        description=(
            "Register / refresh templates (brand / style / layout / deck) "
            "in the index."
        )
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
