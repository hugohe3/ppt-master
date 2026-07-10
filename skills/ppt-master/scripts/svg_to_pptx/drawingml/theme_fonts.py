"""Theme-font contracts shared by SVG conversion and PPTX package assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .utils import parse_font_family


DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_LOCK_ROW_RE = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")
_CJK_THEME_SCRIPTS = frozenset({"Hans", "Hant", "Jpan", "Hang"})


class ThemeFontError(RuntimeError):
    """Raised when a project theme-font contract cannot be loaded or applied."""


@dataclass(frozen=True)
class ThemeFontFace:
    """Concrete Latin, East Asian, and complex-script theme faces."""

    latin: str
    ea: str
    cs: str

    def matches(self, fonts: dict[str, str]) -> bool:
        """Return whether resolved SVG fonts represent this theme face."""
        return fonts.get("latin") == self.latin and fonts.get("ea") == self.ea


@dataclass(frozen=True)
class ThemeFontSpec:
    """Major/minor theme fonts derived from one project's typography lock."""

    major: ThemeFontFace
    minor: ThemeFontFace
    major_family: str
    minor_family: str


def _font_face(font_family: str) -> ThemeFontFace:
    fonts = parse_font_family(font_family)
    return ThemeFontFace(
        latin=fonts["latin"],
        ea=fonts["ea"],
        cs=fonts["latin"],
    )


def _typography_rows(lock_path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    current_section: str | None = None
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ThemeFontError(f"Cannot read {lock_path}: {exc}") from exc

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if current_section != "typography":
            continue
        match = _LOCK_ROW_RE.fullmatch(line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


def load_theme_font_spec(project_path: Path) -> ThemeFontSpec | None:
    """Load major/minor theme fonts from ``spec_lock.md`` typography rows."""
    lock_path = project_path / "spec_lock.md"
    if not lock_path.is_file():
        return None
    rows = _typography_rows(lock_path)
    default_family = rows.get("font_family")
    major_family = rows.get("title_family") or default_family
    minor_family = rows.get("body_family") or default_family
    if not major_family or not minor_family:
        return None
    return ThemeFontSpec(
        major=_font_face(major_family),
        minor=_font_face(minor_family),
        major_family=major_family,
        minor_family=minor_family,
    )


def theme_font_tokens(
    fonts: dict[str, str],
    spec: ThemeFontSpec | None,
) -> dict[str, str] | None:
    """Return DrawingML major/minor tokens for a locked SVG font face."""
    if spec is None:
        return None
    major_match = spec.major.matches(fonts)
    minor_match = spec.minor.matches(fonts)
    if major_match and not minor_match:
        prefix = "+mj"
    elif minor_match:
        # When title/body use the same family, minor is the least surprising
        # default for ordinary text boxes. Template assembly forces semantic
        # title placeholders to the major role after SVG conversion.
        prefix = "+mn"
    else:
        return None
    return {
        "latin": f"{prefix}-lt",
        "ea": f"{prefix}-ea",
        "cs": f"{prefix}-cs",
    }


def _patch_font_collection(collection: ET.Element, face: ThemeFontFace) -> None:
    for tag, value in (("latin", face.latin), ("ea", face.ea), ("cs", face.cs)):
        elem = collection.find(f"{{{DML_NS}}}{tag}")
        if elem is None:
            elem = ET.SubElement(collection, f"{{{DML_NS}}}{tag}")
        elem.set("typeface", value)
    for supplemental in collection.findall(f"{{{DML_NS}}}font"):
        if supplemental.get("script") in _CJK_THEME_SCRIPTS:
            supplemental.set("typeface", face.ea)


def apply_theme_font_spec(extract_dir: Path, spec: ThemeFontSpec) -> None:
    """Install locked major/minor fonts into every existing PPTX theme part."""
    theme_dir = extract_dir / "ppt" / "theme"
    theme_paths = sorted(theme_dir.glob("theme*.xml"))
    if not theme_paths:
        raise ThemeFontError(f"PPTX package has no theme part under {theme_dir}")

    ET.register_namespace("a", DML_NS)
    for theme_path in theme_paths:
        try:
            tree = ET.parse(theme_path)
        except (OSError, ET.ParseError) as exc:
            raise ThemeFontError(f"Cannot parse {theme_path}: {exc}") from exc
        font_scheme = tree.getroot().find(f".//{{{DML_NS}}}fontScheme")
        if font_scheme is None:
            raise ThemeFontError(f"Theme has no fontScheme: {theme_path}")
        major = font_scheme.find(f"{{{DML_NS}}}majorFont")
        minor = font_scheme.find(f"{{{DML_NS}}}minorFont")
        if major is None or minor is None:
            raise ThemeFontError(f"Theme has no major/minor font collection: {theme_path}")
        font_scheme.set("name", "PPT Master")
        _patch_font_collection(major, spec.major)
        _patch_font_collection(minor, spec.minor)
        tree.write(theme_path, encoding="utf-8", xml_declaration=True)
