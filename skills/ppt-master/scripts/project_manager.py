#!/usr/bin/env python3
"""PPT Master project management helpers.

Usage:
    python3 scripts/project_manager.py init <project_name> [--format ppt169] [--dir <path>]
    python3 scripts/project_manager.py import-sources <project_path> <source1> [<source2> ...] [--move | --copy]
    python3 scripts/project_manager.py validate <project_path>
    python3 scripts/project_manager.py info <project_path>
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from console_encoding import configure_utf8_stdio

try:
    from project_utils import (
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        normalize_canvas_format,
        validate_project_structure,
        validate_svg_viewbox,
    )
except ImportError:
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from project_utils import (  # type: ignore
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        normalize_canvas_format,
        validate_project_structure,
        validate_svg_viewbox,
    )

TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
SOURCE_TO_MD_TOOLS_DIR = TOOLS_DIR / "source_to_md"
if str(SOURCE_TO_MD_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_TO_MD_TOOLS_DIR))

from _dispatcher import (  # noqa: E402
    DOC_SUFFIXES,
    EXCEL_SUFFIXES,
    LEGACY_EXCEL_SUFFIXES,
    PDF_SUFFIXES,
    PRESENTATION_SUFFIXES,
    build_conversion_command,
)

SOURCE_DIRNAME = "sources"
TEXT_SOURCE_SUFFIXES = {".md", ".markdown", ".txt"}
TABLE_TEXT_SUFFIXES = {".csv", ".tsv"}
IMAGE_ASSET_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif",
    ".emf", ".wmf", ".svg",
}


configure_utf8_stdio()


def is_url(value: str) -> bool:
    """Return whether a string looks like an HTTP(S) URL."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sanitize_name(value: str) -> str:
    """Sanitize a user-facing name into a filesystem-safe token."""
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in value.strip())
    safe = safe.strip("._")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe[:120] or "source"


def derive_url_basename(url: str) -> str:
    """Derive a stable base filename from a URL."""
    parsed = urlparse(url)
    parts = [sanitize_name(parsed.netloc)]
    if parsed.path and parsed.path != "/":
        path_part = sanitize_name(parsed.path.strip("/").replace("/", "_"))
        if path_part:
            parts.append(path_part)
    return "_".join(part for part in parts if part) or "web_source"


def is_within_path(path: Path, parent: Path) -> bool:
    """Return whether `path` resolves inside `parent`."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


class ProjectManager:
    """Create, inspect, validate, and populate project folders."""

    CANVAS_FORMATS = CANVAS_FORMATS

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else Path.cwd() / "projects"

    def init_project(
        self,
        project_name: str,
        canvas_format: str = "ppt169",
        base_dir: str | None = None,
    ) -> str:
        base_path = Path(base_dir) if base_dir else self.base_dir

        normalized_format = normalize_canvas_format(canvas_format)
        if normalized_format not in self.CANVAS_FORMATS:
            available = ", ".join(sorted(self.CANVAS_FORMATS.keys()))
            raise ValueError(
                f"Unsupported canvas format: {canvas_format} "
                f"(available: {available}; common alias: xhs -> xiaohongshu)"
            )

        date_str = datetime.now().strftime("%Y%m%d")
        # A name already carrying a `_<format>_<YYYYMMDD>` suffix (e.g. a full
        # project dir name pasted back into init) is used as-is — re-appending
        # would produce `name_ppt169_20260101_ppt169_20260102`.
        if re.search(rf"_{re.escape(normalized_format)}_\d{{8}}$", project_name):
            project_dir_name = project_name
        else:
            project_dir_name = f"{project_name}_{normalized_format}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")

        for rel_path in (
            "svg_output",
            "svg_final",
            "images",
            "icons",
            "notes",
            "templates",
            "live_preview",
            SOURCE_DIRNAME,
            "analysis",
            "exports",
        ):
            (project_path / rel_path).mkdir(parents=True, exist_ok=True)

        canvas_info = self.CANVAS_FORMATS[normalized_format]
        readme_path = project_path / "README.md"
        readme_path.write_text(
            (
                f"# {project_name}\n\n"
                f"- Canvas format: {normalized_format}\n"
                f"- Created: {date_str}\n\n"
                "## Directories\n\n"
                "- `svg_output/`: raw SVG output\n"
                "- `svg_final/`: finalized SVG output\n"
                "- `images/`: runtime image pool; converter assets keep their original short filenames when possible\n"
                "- `icons/`: project icon set — selected library icons copied in (via icon_sync.py) plus any custom icons you add; embedded from here at export\n"
                "- `notes/`: speaker notes\n"
                "- `templates/`: project templates\n"
                "- `live_preview/`: browser preview runtime files and history (lock.json, server.log, edits.jsonl, annotations.jsonl)\n"
                "- `sources/`: source materials and normalized markdown\n"
                "- `analysis/`: machine-extracted intermediate analysis (PPTX intake, image_analysis.csv) — the pipeline's canonical must-read source/asset facts\n"
                "- `exports/`: main native pptx (timestamped); `_svg.pptx` sibling added with `--svg-snapshot`, `_native_charts.pptx` name with `--native-objects`, `_narrated.pptx` name when narration audio is embedded\n"
                "- `backup/<timestamp>/`: svg_output/ archive (always written in default-flow mode; safe to delete old timestamps)\n"
            ),
            encoding="utf-8",
        )

        print(f"Project created: {project_path}")
        print(f"Canvas: {canvas_info['name']} ({canvas_info['dimensions']})")
        return str(project_path)

    def _source_dir(self, project_path: Path) -> Path:
        sources_dir = project_path / SOURCE_DIRNAME
        sources_dir.mkdir(parents=True, exist_ok=True)
        return sources_dir

    def _analysis_dir(self, project_path: Path) -> Path:
        analysis_dir = project_path / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        return analysis_dir

    def _ensure_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        suffix = path.suffix
        stem = path.stem
        counter = 2
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _copy_or_move_file(self, source: Path, destination: Path, move: bool) -> Path:
        try:
            if source.resolve() == destination.resolve():
                return destination
        except FileNotFoundError:
            pass

        destination = self._ensure_unique_path(destination)
        if move:
            shutil.move(str(source), str(destination))
        else:
            shutil.copy2(source, destination)
        return destination

    def _copy_or_move_tree(self, source: Path, destination: Path, move: bool) -> Path:
        try:
            if source.resolve() == destination.resolve():
                return destination
        except FileNotFoundError:
            pass

        destination = self._ensure_unique_path(destination)
        if move:
            shutil.move(str(source), str(destination))
        else:
            shutil.copytree(source, destination)
        return destination

    def _run_tool(self, args: list[str]) -> None:
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env["PYTHONIOENCODING"] = "utf-8:replace"
        try:
            result = subprocess.run(
                args,
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"Missing executable: {args[0]}") from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(details or "tool execution failed") from exc

        if result.stdout.strip():
            print(result.stdout.strip())

    def _import_pdf(self, pdf_path: Path, markdown_path: Path) -> None:
        route = build_conversion_command(
            str(pdf_path),
            markdown_path,
            forced_type="pdf",
        )
        self._run_tool(route.command)

    def _import_doc(self, doc_path: Path, markdown_path: Path) -> None:
        route = build_conversion_command(
            str(doc_path),
            markdown_path,
            forced_type="doc",
        )
        self._run_tool(route.command)

    def _import_presentation(self, presentation_path: Path, markdown_path: Path) -> None:
        route = build_conversion_command(
            str(presentation_path),
            markdown_path,
            forced_type="pptx",
        )
        self._run_tool(route.command)

    def _import_pptx_intake(self, presentation_path: Path, project_dir: Path) -> Path:
        # Multi-deck intake: each PPTX writes its own `<stem>.identity.json` /
        # `<stem>.slide_library.json` and is merged into the single multi-deck
        # index `analysis/source_profile.json` (one entry per source deck).
        analysis_dir = self._analysis_dir(project_dir)
        self._run_tool(
            [
                sys.executable,
                str(TOOLS_DIR / "pptx_intake.py"),
                str(presentation_path),
                "-o",
                str(analysis_dir),
            ]
        )
        return analysis_dir

    def _import_excel(self, excel_path: Path, markdown_path: Path) -> None:
        route = build_conversion_command(
            str(excel_path),
            markdown_path,
            forced_type="excel",
        )
        self._run_tool(route.command)

    def _import_url(self, url: str, markdown_path: Path) -> None:
        route = build_conversion_command(
            url,
            markdown_path,
            forced_type="web",
        )
        self._run_tool(route.command)

    def _is_valid_imported_url_markdown(self, markdown_path: Path) -> bool:
        """Return whether web_to_md produced a usable Markdown source."""
        if not markdown_path.is_file():
            return False
        content = markdown_path.read_text(encoding="utf-8", errors="replace")
        if "[Failed URLs]:" in content:
            return False
        return bool(content.strip())

    def _archive_url_record(self, sources_dir: Path, url: str) -> Path:
        file_path = self._ensure_unique_path(sources_dir / f"{derive_url_basename(url)}.url.txt")
        file_path.write_text(
            f"URL: {url}\nImported: {datetime.now().isoformat(timespec='seconds')}\n",
            encoding="utf-8",
        )
        return file_path

    def _normalize_text_source(self, source_path: Path, sources_dir: Path) -> Path:
        target = self._ensure_unique_path(sources_dir / f"{source_path.stem}.md")
        content = source_path.read_text(encoding="utf-8", errors="replace")
        target.write_text(content, encoding="utf-8")
        return target

    def _canonicalize_markdown_content(self, content: str) -> str:
        canonical = content.replace("\r\n", "\n")
        canonical = re.sub(r"(?m)^(\s*Crawled:\s+).*$", r"\1__IGNORED__", canonical)
        canonical = re.sub(r"(?m)^(\s*Imported:\s+).*$", r"\1__IGNORED__", canonical)
        canonical = re.sub(r"([^\s\]()/]+_files)/", "__ASSET_DIR__/", canonical)
        return canonical.strip()

    def _find_equivalent_markdown(self, source_path: Path, sources_dir: Path) -> Path | None:
        source_content = source_path.read_text(encoding="utf-8", errors="replace")
        canonical_source = self._canonicalize_markdown_content(source_content)

        for existing in sorted(sources_dir.iterdir()):
            if existing.suffix.lower() not in {".md", ".markdown"}:
                continue
            try:
                if existing.resolve() == source_path.resolve():
                    continue
            except FileNotFoundError:
                pass

            existing_content = existing.read_text(encoding="utf-8", errors="replace")
            if self._canonicalize_markdown_content(existing_content) == canonical_source:
                return existing

        return None

    def _companion_asset_dir(self, source_path: Path) -> Path | None:
        candidate = source_path.with_name(f"{source_path.stem}_files")
        if candidate.exists() and candidate.is_dir():
            return candidate
        return None

    def _rewrite_markdown_asset_refs(
        self,
        markdown_path: Path,
        original_asset_dirname: str,
        imported_asset_dirname: str,
    ) -> None:
        if original_asset_dirname == imported_asset_dirname:
            return

        content = markdown_path.read_text(encoding="utf-8", errors="replace")
        updated = content.replace(f"{original_asset_dirname}/", f"{imported_asset_dirname}/")
        if updated != content:
            markdown_path.write_text(updated, encoding="utf-8")

    def _merge_image_manifest(self, source_items: list[dict], destination_manifest: Path) -> None:
        """Merge per-source manifest items into the project-level manifest, keyed by filename."""
        existing_data: list[object] = []
        if destination_manifest.is_file():
            try:
                loaded = json.loads(destination_manifest.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    existing_data = loaded
                else:
                    print(f"[WARN] Replacing non-list image manifest: {destination_manifest}")
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[WARN] Replacing unreadable image manifest {destination_manifest}: {exc}")

        new_by_filename: dict[str, dict] = {}
        new_order: list[str] = []
        for item in source_items:
            filename = item.get("filename")
            if not isinstance(filename, str):
                continue
            if filename not in new_by_filename:
                new_order.append(filename)
            new_by_filename[filename] = item

        merged: list[dict] = []
        seen: set[str] = set()
        for item in existing_data:
            if not isinstance(item, dict):
                continue
            filename = item.get("filename")
            if not isinstance(filename, str):
                continue
            if filename in new_by_filename:
                merged.append(new_by_filename[filename])
            else:
                merged.append(item)
            seen.add(filename)

        for filename in new_order:
            if filename not in seen:
                merged.append(new_by_filename[filename])

        destination_manifest.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _namespace_from_asset_dir(asset_dir: Path) -> str:
        """Derive a per-source namespace from a `<stem>_files` companion directory name."""
        name = asset_dir.name
        suffix = "_files"
        return name[:-len(suffix)] if name.endswith(suffix) else name

    def _image_destination_name(
        self,
        images_dir: Path,
        source_file: Path,
        namespace: str,
        existing_manifest: dict[str, dict],
    ) -> str:
        """Return a short unique image filename for the runtime image pool."""
        candidate = images_dir / source_file.name
        if not candidate.exists():
            return source_file.name
        try:
            meta = existing_manifest.get(candidate.name, {})
            if (
                meta.get("source_namespace") == namespace
                and candidate.is_file()
                and filecmp.cmp(source_file, candidate, shallow=False)
            ):
                return candidate.name
        except OSError:
            pass

        stem = source_file.stem
        suffix = source_file.suffix
        counter = 2
        while True:
            candidate = images_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate.name
            try:
                meta = existing_manifest.get(candidate.name, {})
                if (
                    meta.get("source_namespace") == namespace
                    and candidate.is_file()
                    and filecmp.cmp(source_file, candidate, shallow=False)
                ):
                    return candidate.name
            except OSError:
                pass
            counter += 1

    def _propagate_image_assets(self, asset_dir: Path, project_dir: Path) -> None:
        """Copy converter-generated image assets and manifest into project images/.

        Filenames are preserved when possible because source Markdown commonly
        uses short names that are meaningful in context. Only real collisions
        receive a compact numeric suffix.
        """
        manifest_path = asset_dir / "image_manifest.json"
        if not manifest_path.is_file():
            return

        try:
            source_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[WARN] Cannot read image manifest {manifest_path}: {exc}")
            return
        if not isinstance(source_data, list):
            print(f"[WARN] Ignoring non-list image manifest: {manifest_path}")
            return

        images_dir = project_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        namespace = self._namespace_from_asset_dir(asset_dir)
        existing_manifest: dict[str, dict] = {}
        destination_manifest = images_dir / "image_manifest.json"
        if destination_manifest.is_file():
            try:
                data = json.loads(destination_manifest.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    existing_manifest = {
                        item["filename"]: item
                        for item in data
                        if isinstance(item, dict) and isinstance(item.get("filename"), str)
                    }
            except (OSError, json.JSONDecodeError):
                existing_manifest = {}
        rename_map: dict[str, str] = {}

        copied_count = 0
        for source_file in sorted(asset_dir.iterdir()):
            if not source_file.is_file():
                continue
            if source_file.suffix.lower() not in IMAGE_ASSET_SUFFIXES:
                continue
            new_name = self._image_destination_name(
                images_dir,
                source_file,
                namespace,
                existing_manifest,
            )
            destination = images_dir / new_name
            if source_file.resolve() != destination.resolve():
                shutil.copy2(source_file, destination)
            rename_map[source_file.name] = new_name
            copied_count += 1

        rebased_items: list[dict] = []
        for item in source_data:
            if not isinstance(item, dict):
                continue
            original = item.get("filename")
            if not isinstance(original, str):
                continue
            new_item = dict(item)
            new_item["filename"] = rename_map.get(original, original)
            new_item["source_namespace"] = namespace
            rebased_items.append(new_item)

        self._merge_image_manifest(rebased_items, images_dir / "image_manifest.json")
        print(
            f"Propagated {copied_count} image asset(s) + manifest "
            f"from {asset_dir} → images/ (namespace: {namespace})"
        )

    def _propagate_companion_image_assets(self, markdown_path: Path, project_dir: Path) -> None:
        asset_dir = markdown_path.with_name(f"{markdown_path.stem}_files")
        if asset_dir.is_dir():
            self._propagate_image_assets(asset_dir, project_dir)

    def _import_markdown_with_assets(
        self,
        source_path: Path,
        sources_dir: Path,
        move: bool,
    ) -> tuple[Path, Path | None, str | None]:
        archived_markdown = self._copy_or_move_file(
            source_path,
            sources_dir / source_path.name,
            move=move,
        )

        profile_src = source_path.with_name(f"{source_path.stem}.conversion_profile.json")
        if profile_src.is_file():
            self._copy_or_move_file(
                profile_src,
                sources_dir / f"{archived_markdown.stem}.conversion_profile.json",
                move=move,
            )

        asset_dir = self._companion_asset_dir(source_path)
        if asset_dir is None:
            return archived_markdown, None, None

        imported_asset_dir = self._copy_or_move_tree(
            asset_dir,
            sources_dir / f"{archived_markdown.stem}_files",
            move=move,
        )
        self._rewrite_markdown_asset_refs(
            archived_markdown,
            original_asset_dirname=asset_dir.name,
            imported_asset_dirname=imported_asset_dir.name,
        )

        note = None
        if archived_markdown.stem != source_path.stem:
            note = (
                f"{source_path}: renamed imported markdown to {archived_markdown.name} "
                f"and rewrote asset references to {imported_asset_dir.name}/"
            )
        return archived_markdown, imported_asset_dir, note

    def import_sources(
        self,
        project_path: str,
        source_items: list[str],
        move: bool = False,
        copy: bool = False,
    ) -> dict[str, list[str]]:
        if move and copy:
            raise ValueError("--move and --copy are mutually exclusive")
        project_dir = Path(project_path)
        if not project_dir.exists() or not project_dir.is_dir():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")
        if not source_items:
            raise ValueError("At least one source path or URL is required")

        sources_dir = self._source_dir(project_dir)
        summary: dict[str, list[str]] = {
            "archived": [],
            "markdown": [],
            "assets": [],
            "analysis": [],
            "notes": [],
            "skipped": [],
        }

        expanded_items: list[str] = []
        for item in source_items:
            if is_url(item):
                expanded_items.append(item)
                continue
            item_path = Path(item)
            if item_path.is_dir():
                directory_files = sorted(
                    path for path in item_path.iterdir() if path.is_file()
                )
                if directory_files:
                    expanded_items.extend(str(path) for path in directory_files)
                    summary["notes"].append(
                        f"{item}: expanded directory into {len(directory_files)} file(s)"
                    )
                else:
                    summary["skipped"].append(f"{item}: directory contains no files")
                continue
            expanded_items.append(item)

        explicit_markdown_stems = {
            Path(item).stem
            for item in expanded_items
            if not is_url(item)
            and Path(item).exists()
            and Path(item).is_file()
            and Path(item).suffix.lower() in {".md", ".markdown"}
        }

        for item in expanded_items:
            if is_url(item):
                markdown_path = self._ensure_unique_path(
                    sources_dir / f"{derive_url_basename(item)}.md"
                )
                try:
                    self._import_url(item, markdown_path)
                except Exception as exc:  # pragma: no cover - summary path
                    archived = self._archive_url_record(sources_dir, item)
                    summary["archived"].append(str(archived))
                    summary["skipped"].append(f"{item}: {exc}")
                    continue

                if not self._is_valid_imported_url_markdown(markdown_path):
                    markdown_path.unlink(missing_ok=True)
                    archived = self._archive_url_record(sources_dir, item)
                    summary["archived"].append(str(archived))
                    summary["skipped"].append(f"{item}: URL conversion produced no usable Markdown")
                    continue

                summary["markdown"].append(str(markdown_path))
                self._propagate_companion_image_assets(markdown_path, project_dir)
                continue

            source_path = Path(item)
            if not source_path.exists():
                summary["skipped"].append(f"{item}: path not found")
                continue
            if source_path.is_dir():
                summary["skipped"].append(f"{item}: directories are not supported")
                continue

            if copy:
                effective_move = False
            elif move:
                effective_move = True
            elif is_within_path(source_path, REPO_ROOT):
                effective_move = True
                print(
                    f"note: {source_path} is inside the ppt-master repo; moved "
                    f"(not copied) to avoid accidental commit. Pass --copy to override.",
                    file=sys.stderr,
                )
            else:
                effective_move = False
            suffix = source_path.suffix.lower()

            if suffix in {".md", ".markdown"}:
                duplicate_markdown = self._find_equivalent_markdown(source_path, sources_dir)
                if duplicate_markdown is not None:
                    summary["markdown"].append(str(duplicate_markdown))
                    self._propagate_companion_image_assets(duplicate_markdown, project_dir)
                    summary["notes"].append(
                        f"{item}: skipped duplicate markdown import because equivalent content already exists as {duplicate_markdown.name}"
                    )
                    continue

                archived_markdown, asset_dir, note = self._import_markdown_with_assets(
                    source_path,
                    sources_dir,
                    move=effective_move,
                )
                summary["archived"].append(str(archived_markdown))
                summary["markdown"].append(str(archived_markdown))
                if asset_dir is not None:
                    summary["assets"].append(str(asset_dir))
                    self._propagate_image_assets(asset_dir, project_dir)
                if note:
                    summary["notes"].append(note)
                continue

            archived_path = self._copy_or_move_file(
                source_path,
                sources_dir / source_path.name,
                move=effective_move,
            )
            summary["archived"].append(str(archived_path))

            if suffix in PDF_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped PDF auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    self._propagate_companion_image_assets(canonical_markdown_path, project_dir)
                    summary["notes"].append(
                        f"{item}: skipped PDF auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_pdf(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                    self._propagate_companion_image_assets(markdown_path, project_dir)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: PDF conversion failed ({exc})")
            elif suffix in PRESENTATION_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                try:
                    intake_dir = self._import_pptx_intake(archived_path, project_dir)
                    intake_str = str(intake_dir)
                    if intake_str not in summary["analysis"]:
                        summary["analysis"].append(intake_str)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["notes"].append(f"{item}: PPTX intake analysis failed ({exc})")
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped presentation auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    self._propagate_companion_image_assets(canonical_markdown_path, project_dir)
                    summary["notes"].append(
                        f"{item}: skipped presentation auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_presentation(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                    self._propagate_companion_image_assets(markdown_path, project_dir)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: presentation conversion failed ({exc})")
            elif suffix in EXCEL_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped Excel auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    self._propagate_companion_image_assets(canonical_markdown_path, project_dir)
                    summary["notes"].append(
                        f"{item}: skipped Excel auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_excel(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                    self._propagate_companion_image_assets(markdown_path, project_dir)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: Excel conversion failed ({exc})")
            elif suffix in LEGACY_EXCEL_SUFFIXES:
                summary["notes"].append(
                    f"{item}: archived only; legacy .xls is not converted automatically. "
                    "Resave as .xlsx to generate Markdown."
                )
            elif suffix in TABLE_TEXT_SUFFIXES:
                summary["notes"].append(
                    f"{item}: archived as a plain-text table source; no Markdown conversion needed"
                )
            elif suffix in DOC_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped document auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    self._propagate_companion_image_assets(canonical_markdown_path, project_dir)
                    summary["notes"].append(
                        f"{item}: skipped document auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_doc(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                    self._propagate_companion_image_assets(markdown_path, project_dir)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: document conversion failed ({exc})")
            elif suffix == ".txt":
                markdown_path = self._normalize_text_source(archived_path, sources_dir)
                summary["markdown"].append(str(markdown_path))
            else:
                summary["notes"].append(f"{item}: archived only, no automatic conversion")

        return summary

    def validate_project(self, project_path: str) -> tuple[bool, list[str], list[str]]:
        project_path_obj = Path(project_path)
        is_valid, errors, warnings = validate_project_structure(str(project_path_obj))

        if project_path_obj.exists() and project_path_obj.is_dir():
            info = get_project_info_common(str(project_path_obj))
            if info.get("svg_files"):
                svg_files = [project_path_obj / "svg_output" / name for name in info["svg_files"]]
                expected_format = info.get("format")
                if expected_format == "unknown":
                    expected_format = None
                warnings.extend(validate_svg_viewbox(svg_files, expected_format))

        return is_valid, errors, warnings

    def get_project_info(self, project_path: str) -> dict[str, object]:
        shared = get_project_info_common(project_path)
        return {
            "name": shared.get("name", Path(project_path).name),
            "path": shared.get("path", str(project_path)),
            "exists": shared.get("exists", False),
            "svg_count": shared.get("svg_count", 0),
            "has_spec": shared.get("has_spec", False),
            "has_source": shared.get("has_source", False),
            "source_count": shared.get("source_count", 0),
            "canvas_format": shared.get("format_name", "Unknown"),
            "create_date": shared.get("date_formatted", "Unknown"),
        }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="PPT Master project management helpers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 scripts/project_manager.py init demo --format ppt169
  python3 scripts/project_manager.py import-sources projects/demo file.md --move
  python3 scripts/project_manager.py validate projects/demo
  python3 scripts/project_manager.py info projects/demo
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a project directory")
    init.add_argument("project_name", help="Project name")
    init.add_argument("--format", default="ppt169", help="Canvas format (default: ppt169)")
    init.add_argument("--dir", default=None, help="Base directory for the project")

    import_sources = subparsers.add_parser(
        "import-sources",
        help="Import source files or URLs into a project",
    )
    import_sources.add_argument("project_path", help="Project directory")
    import_sources.add_argument("sources", nargs="+", help="Source files, directories, or URLs")
    mode = import_sources.add_mutually_exclusive_group()
    mode.add_argument("--move", action="store_true", help="Move local source files")
    mode.add_argument("--copy", action="store_true", help="Copy local source files")

    validate = subparsers.add_parser("validate", help="Validate a project directory")
    validate.add_argument("project_path", help="Project directory")

    info = subparsers.add_parser("info", help="Print project metadata")
    info.add_argument("project_path", help="Project directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    manager = ProjectManager()

    try:
        if args.command == "init":
            project_path = manager.init_project(
                args.project_name,
                args.format,
                base_dir=args.dir,
            )
            print(f"[OK] Project initialized: {project_path}")
            print("Next:")
            print("1. Put source files into sources/ (or use import-sources)")
            print("2. Save your design spec to the project root")
            print("3. Generate SVG files into svg_output/")
            return 0

        if args.command == "import-sources":
            summary = manager.import_sources(
                args.project_path,
                args.sources,
                move=args.move,
                copy=args.copy,
            )
            print(f"[OK] Imported sources into: {args.project_path}")
            if summary["archived"]:
                print("\nArchived originals / URL records:")
                for item in summary["archived"]:
                    print(f"  - {item}")
            if summary["markdown"]:
                print("\nNormalized markdown:")
                for item in summary["markdown"]:
                    print(f"  - {item}")
            if summary["assets"]:
                print("\nImported asset directories:")
                for item in summary["assets"]:
                    print(f"  - {item}")
            if summary["analysis"]:
                print("\nAnalysis artifacts:")
                for item in summary["analysis"]:
                    print(f"  - {item}")
            if summary["notes"]:
                print("\nNotes:")
                for item in summary["notes"]:
                    print(f"  - {item}")
            if summary["skipped"]:
                print("\nSkipped:")
                for item in summary["skipped"]:
                    print(f"  - {item}")
            return 0

        if args.command == "validate":
            project_path = args.project_path
            is_valid, errors, warnings = manager.validate_project(project_path)

            print(f"\nProject validation: {project_path}")
            print("=" * 60)

            if errors:
                print("\n[ERROR]")
                for error in errors:
                    print(f"  - {error}")

            if warnings:
                print("\n[WARN]")
                for warning in warnings:
                    print(f"  - {warning}")

            if is_valid and not warnings:
                print("\n[OK] Project structure is complete.")
            elif is_valid:
                print("\n[OK] Project structure is valid, with warnings.")
            else:
                print("\n[ERROR] Project structure is invalid.")
                return 1
            return 0

        if args.command == "info":
            project_path = args.project_path
            info = manager.get_project_info(project_path)

            print(f"\nProject info: {info['name']}")
            print("=" * 60)
            print(f"Path: {info['path']}")
            print(f"Exists: {'Yes' if info['exists'] else 'No'}")
            print(f"SVG files: {info['svg_count']}")
            print(f"Design spec: {'Yes' if info['has_spec'] else 'No'}")
            print(f"Source materials: {'Yes' if info['has_source'] else 'No'}")
            print(f"Source count: {info['source_count']}")
            print(f"Canvas format: {info['canvas_format']}")
            print(f"Created: {info['create_date']}")
            return 0

        parser.error(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
