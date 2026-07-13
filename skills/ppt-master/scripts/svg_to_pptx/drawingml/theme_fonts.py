"""Theme typography contracts shared by SVG conversion and PPTX assembly."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .utils import FONT_PX_TO_HUNDREDTHS_PT, font_px_to_hpt, parse_font_family


DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_LOCK_ROW_RE = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")
_CJK_THEME_SCRIPTS = frozenset({"Hans", "Hant", "Jpan", "Hang"})
_TEXT_FONT_SIZE_MIN = 100
_TEXT_FONT_SIZE_MAX = 400_000


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


@dataclass(frozen=True)
class MasterTextStyleSpec:
    """Title/body defaults written to one generated slide master's txStyles."""

    title_hpt: int
    body_hpt: int

    @property
    def body_levels_hpt(self) -> tuple[int, ...]:
        """Return a deterministic nine-level PowerPoint body-size hierarchy."""
        factors = (16, 15, 14, 13, 12, 11, 10, 9, 8)
        minimum = min(self.body_hpt, 800)
        sizes = []
        for factor in factors:
            scaled = round((self.body_hpt * factor / 16) / 50) * 50
            sizes.append(max(minimum, scaled))
        return tuple(sizes)


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


def _font_size_hpt(raw: str, field: str) -> int:
    try:
        px = float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ThemeFontError(
            f"spec_lock.md typography {field} must be a numeric px value: {raw!r}"
        ) from exc
    scaled = px * FONT_PX_TO_HUNDREDTHS_PT
    if not math.isfinite(scaled):
        raise ThemeFontError(
            f"spec_lock.md typography {field} must be finite: {raw!r}"
        )
    size = font_px_to_hpt(px)
    if not _TEXT_FONT_SIZE_MIN <= size <= _TEXT_FONT_SIZE_MAX:
        raise ThemeFontError(
            f"spec_lock.md typography {field} is outside the PowerPoint "
            f"font-size range: {raw!r}"
        )
    return size


def load_master_text_style_spec(project_path: Path) -> MasterTextStyleSpec:
    """Load required title/body defaults for generated Master text styles."""
    lock_path = project_path / "spec_lock.md"
    if not lock_path.is_file():
        raise ThemeFontError(
            "Master export requires spec_lock.md typography title and body rows"
        )
    rows = _typography_rows(lock_path)
    missing = [field for field in ("title", "body") if field not in rows]
    if missing:
        raise ThemeFontError(
            "Master export requires spec_lock.md typography rows: "
            + ", ".join(missing)
        )
    return MasterTextStyleSpec(
        title_hpt=_font_size_hpt(rows["title"], "title"),
        body_hpt=_font_size_hpt(rows["body"], "body"),
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


def _style_run_properties(style: ET.Element, label: str) -> list[ET.Element]:
    run_properties = list(style.iter(f"{{{DML_NS}}}defRPr"))
    if not run_properties:
        raise ThemeFontError(f"slide master {label} has no a:defRPr entries")
    return run_properties


def _style_level_run_properties(
    style: ET.Element,
    label: str,
) -> tuple[ET.Element, ...]:
    """Return direct level 1-9 defaults from one Master text style."""
    levels: list[ET.Element] = []
    for level in range(1, 10):
        run_properties = style.find(
            f"{{{DML_NS}}}lvl{level}pPr/{{{DML_NS}}}defRPr"
        )
        if run_properties is None:
            raise ThemeFontError(
                f"slide master {label} has no level-{level} a:defRPr"
            )
        levels.append(run_properties)
    return tuple(levels)


def apply_master_text_style_spec(
    extract_dir: Path,
    spec: MasterTextStyleSpec,
) -> int:
    """Install locked title/body sizes into generated slide-master txStyles."""
    master_dir = extract_dir / "ppt" / "slideMasters"
    master_paths = sorted(master_dir.glob("slideMaster*.xml"))
    if not master_paths:
        raise ThemeFontError(f"PPTX package has no slide master under {master_dir}")

    ET.register_namespace("a", DML_NS)
    ET.register_namespace("p", PML_NS)
    for master_path in master_paths:
        try:
            tree = ET.parse(master_path)
        except (OSError, ET.ParseError) as exc:
            raise ThemeFontError(f"Cannot parse {master_path}: {exc}") from exc
        text_styles = tree.getroot().find(f"{{{PML_NS}}}txStyles")
        if text_styles is None:
            raise ThemeFontError(f"Slide master has no p:txStyles: {master_path}")

        title_style = text_styles.find(f"{{{PML_NS}}}titleStyle")
        if title_style is None:
            raise ThemeFontError(
                f"Slide master has no p:titleStyle: {master_path}"
            )
        for run_properties in _style_run_properties(
            title_style,
            "p:titleStyle",
        ):
            run_properties.set("sz", str(spec.title_hpt))

        body_levels = spec.body_levels_hpt
        for style_name in ("bodyStyle", "otherStyle"):
            style = text_styles.find(f"{{{PML_NS}}}{style_name}")
            if style is None:
                raise ThemeFontError(
                    f"Slide master has no p:{style_name}: {master_path}"
                )
            for run_properties, size in zip(
                _style_level_run_properties(
                    style,
                    f"p:{style_name}",
                ),
                body_levels,
            ):
                run_properties.set("sz", str(size))

        style_sizes = (
            ("titleStyle", (spec.title_hpt,)),
            ("bodyStyle", body_levels),
            ("otherStyle", body_levels),
        )

        tree.write(master_path, encoding="utf-8", xml_declaration=True)

        try:
            read_back = ET.parse(master_path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise ThemeFontError(
                f"Cannot read back slide master {master_path}: {exc}"
            ) from exc
        read_back_styles = read_back.find(f"{{{PML_NS}}}txStyles")
        if read_back_styles is None:
            raise ThemeFontError(
                f"Slide master lost p:txStyles after update: {master_path}"
            )
        for style_name, expected_sizes in style_sizes:
            style = read_back_styles.find(f"{{{PML_NS}}}{style_name}")
            if style is None:
                actual_sizes: tuple[str | None, ...] = ()
            elif style_name == "titleStyle":
                actual_sizes = tuple(
                    item.get("sz")
                    for item in _style_run_properties(
                        style,
                        f"p:{style_name}",
                    )
                )
            else:
                actual_sizes = tuple(
                    item.get("sz")
                    for item in _style_level_run_properties(
                        style,
                        f"p:{style_name}",
                    )
                )
            if actual_sizes != tuple(str(size) for size in expected_sizes):
                raise ThemeFontError(
                    f"Slide master p:{style_name} size read-back failed: "
                    f"{master_path}"
                )
    return len(master_paths)
