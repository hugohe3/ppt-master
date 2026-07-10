"""Theme-color contracts shared by SVG conversion and PPTX package assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .utils import parse_hex_color


DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_LOCK_ROW_RE = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")
_SRGB_PAIR_RE = re.compile(
    r"<a:srgbClr\b(?P<attrs>[^>]*?)(?<!/)>(?P<body>.*?)</a:srgbClr>",
    re.DOTALL,
)
_SRGB_EMPTY_RE = re.compile(r"<a:srgbClr\b(?P<attrs>[^>]*)/>")
_VAL_RE = re.compile(r'\bval="(?P<color>[0-9A-Fa-f]{6})"')

_OFFICE_DEFAULTS = {
    "dk1": "000000",
    "lt1": "FFFFFF",
    "dk2": "1F497D",
    "lt2": "EEECE1",
    "accent1": "4F81BD",
    "accent2": "C0504D",
    "accent3": "9BBB59",
    "accent4": "8064A2",
    "accent5": "4BACC6",
    "accent6": "F79646",
    "hlink": "0000FF",
    "folHlink": "800080",
}
_ROLE_SLOTS = {
    "bg": "lt1",
    "background": "lt1",
    "master_bg": "lt1",
    "secondary_bg": "lt2",
    "bg_secondary": "lt2",
    "text": "dk1",
    "body_text": "dk1",
    "text_secondary": "dk2",
    "primary": "accent1",
    "accent": "accent2",
    "secondary_accent": "accent3",
    "border": "accent4",
}
_USAGE_ROLE_ORDER = {
    "background": (
        "bg", "background", "master_bg", "secondary_bg", "bg_secondary",
        "primary", "accent", "secondary_accent",
    ),
    "fill": (
        "primary", "accent", "secondary_accent", "bg", "background",
        "master_bg", "secondary_bg", "bg_secondary", "text", "body_text",
        "text_secondary", "border",
    ),
    "text": (
        "text", "body_text", "text_secondary", "primary", "accent",
        "secondary_accent",
    ),
    "stroke": (
        "border", "primary", "accent", "secondary_accent", "text",
        "body_text", "text_secondary",
    ),
    "chart": ("primary", "accent", "secondary_accent"),
}
_BACKGROUND_ROLE_TOKENS = (
    "bg", "background", "surface", "paper", "card", "panel", "tint",
)
_TEXT_ROLE_TOKENS = ("text", "ink", "muted")
_STROKE_ROLE_TOKENS = ("border", "grid", "line", "stroke")
_BACKGROUND_USAGES = frozenset({"background", "fill"})
_TEXT_USAGES = frozenset({"text"})
_STROKE_USAGES = frozenset({"stroke", "fill"})
_SEMANTIC_USAGES = frozenset({"fill", "text", "stroke"})


class ThemeColorError(RuntimeError):
    """Raised when a project theme-color contract cannot be loaded or applied."""


@dataclass(frozen=True)
class ThemeColorSpec:
    """PowerPoint color scheme derived from one project's color lock."""

    slots: dict[str, str]
    roles: dict[str, str]
    role_slots: dict[str, str]
    extra_roles: tuple[str, ...] = ()

    def scheme_for(self, color: str, usage: str) -> str | None:
        """Resolve one concrete color to a safe scheme slot for its usage."""
        normalized = parse_hex_color(color)
        if normalized is None:
            return None
        for role in _USAGE_ROLE_ORDER.get(usage, ()):
            if self.roles.get(role) == normalized:
                slot = self.role_slots[role]
                if self.slots.get(slot) == normalized:
                    return slot
        for role in self.extra_roles:
            if usage in _extra_role_usages(role) and self.roles.get(role) == normalized:
                slot = self.role_slots[role]
                if self.slots.get(slot) == normalized:
                    return slot
        return None


def _extra_role_usages(role: str) -> frozenset[str]:
    """Limit extra theme slots to contexts implied by their lock role name."""
    normalized = role.lower()
    if any(token in normalized for token in _BACKGROUND_ROLE_TOKENS):
        return _BACKGROUND_USAGES
    if any(token in normalized for token in _TEXT_ROLE_TOKENS):
        return _TEXT_USAGES
    if any(token in normalized for token in _STROKE_ROLE_TOKENS):
        return _STROKE_USAGES
    return _SEMANTIC_USAGES


def _color_rows(lock_path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    current_section: str | None = None
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ThemeColorError(f"Cannot read {lock_path}: {exc}") from exc
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if current_section != "colors":
            continue
        match = _LOCK_ROW_RE.fullmatch(line)
        if not match:
            continue
        color = parse_hex_color(match.group(2))
        if color is not None:
            rows[match.group(1)] = color
    return rows


def _first_color(roles: dict[str, str], *keys: str, default: str) -> str:
    return next((roles[key] for key in keys if key in roles), default)


def load_theme_color_spec(project_path: Path) -> ThemeColorSpec | None:
    """Load a PowerPoint color scheme from ``spec_lock.md`` color rows."""
    lock_path = project_path / "spec_lock.md"
    if not lock_path.is_file():
        return None
    roles = _color_rows(lock_path)
    if not roles:
        return None

    extra_roles = tuple(
        key
        for key, color in roles.items()
        if key not in _ROLE_SLOTS and color not in {"000000", "FFFFFF"}
    )[:2]
    extra_slots = dict(zip(extra_roles, ("accent5", "accent6")))
    role_slots = {**_ROLE_SLOTS, **extra_slots}

    slots = dict(_OFFICE_DEFAULTS)
    slots.update({
        "lt1": _first_color(
            roles,
            "bg", "background", "master_bg",
            default=slots["lt1"],
        ),
        "dk1": _first_color(
            roles,
            "text", "body_text", "primary",
            default=slots["dk1"],
        ),
        "lt2": _first_color(
            roles,
            "secondary_bg", "bg_secondary", "bg", "background", "master_bg",
            default=slots["lt2"],
        ),
        "dk2": _first_color(roles, "text_secondary", "text", default=slots["dk2"]),
        "accent1": _first_color(roles, "primary", "accent", default=slots["accent1"]),
        "accent2": _first_color(
            roles,
            "accent", "secondary_accent", "primary",
            default=slots["accent2"],
        ),
        "accent3": _first_color(roles, "secondary_accent", "accent", default=slots["accent3"]),
        "accent4": _first_color(roles, "border", "primary", default=slots["accent4"]),
        "hlink": _first_color(roles, "accent", "primary", default=slots["hlink"]),
        "folHlink": _first_color(roles, "secondary_accent", "accent", default=slots["folHlink"]),
    })
    for role, slot in extra_slots.items():
        slots[slot] = roles[role]
    return ThemeColorSpec(
        slots=slots,
        roles=roles,
        role_slots=role_slots,
        extra_roles=extra_roles,
    )


def color_node_xml(
    color: str,
    spec: ThemeColorSpec | None,
    usage: str,
    inner_xml: str = "",
) -> str:
    """Build an srgbClr or schemeClr node while preserving child transforms."""
    normalized = parse_hex_color(color) or color.strip().lstrip("#").upper()
    scheme = spec.scheme_for(normalized, usage) if spec is not None else None
    if scheme:
        return f'<a:schemeClr val="{scheme}">{inner_xml}</a:schemeClr>'
    return f'<a:srgbClr val="{normalized}">{inner_xml}</a:srgbClr>'


def _set_scheme_color(parent: ET.Element, slot: str, color: str) -> None:
    target = parent.find(f"{{{DML_NS}}}{slot}")
    if target is None:
        target = ET.SubElement(parent, f"{{{DML_NS}}}{slot}")
    for child in list(target):
        target.remove(child)
    ET.SubElement(target, f"{{{DML_NS}}}srgbClr", {"val": color})


def apply_theme_color_spec(extract_dir: Path, spec: ThemeColorSpec) -> None:
    """Install the locked color scheme into every existing PPTX theme part."""
    theme_dir = extract_dir / "ppt" / "theme"
    theme_paths = sorted(theme_dir.glob("theme*.xml"))
    if not theme_paths:
        raise ThemeColorError(f"PPTX package has no theme part under {theme_dir}")

    ET.register_namespace("a", DML_NS)
    for theme_path in theme_paths:
        try:
            tree = ET.parse(theme_path)
        except (OSError, ET.ParseError) as exc:
            raise ThemeColorError(f"Cannot parse {theme_path}: {exc}") from exc
        color_scheme = tree.getroot().find(f".//{{{DML_NS}}}clrScheme")
        if color_scheme is None:
            raise ThemeColorError(f"Theme has no clrScheme: {theme_path}")
        color_scheme.set("name", "PPT Master")
        for slot, color in spec.slots.items():
            _set_scheme_color(color_scheme, slot, color)
        tree.write(theme_path, encoding="utf-8", xml_declaration=True)


def rewrite_chart_accent_colors(data: bytes, spec: ThemeColorSpec | None) -> bytes:
    """Promote exact locked accent colors inside native chart XML."""
    if spec is None or b"<a:srgbClr" not in data:
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data

    def replacement(match: re.Match[str], *, paired: bool) -> str:
        attrs = match.group("attrs")
        value_match = _VAL_RE.search(attrs)
        if value_match is None:
            return match.group(0)
        scheme = spec.scheme_for(value_match.group("color"), "chart")
        if scheme is None:
            return match.group(0)
        new_attrs = _VAL_RE.sub(f'val="{scheme}"', attrs, count=1)
        if paired:
            return f'<a:schemeClr{new_attrs}>{match.group("body")}</a:schemeClr>'
        return f'<a:schemeClr{new_attrs}/>'

    text = _SRGB_PAIR_RE.sub(lambda match: replacement(match, paired=True), text)
    text = _SRGB_EMPTY_RE.sub(lambda match: replacement(match, paired=False), text)
    return text.encode("utf-8")
