#!/usr/bin/env python3
"""Install selected Brand / Style / Layout / Deck workspaces into a project.

Runs the install half of ``workflows/stages/apply-template-workspace.md`` §4
as one command: validate every root, map each spec to its kind-qualified
project name, resolve the structural owner (Layout over Deck), copy the owner's
roster and every root's ``images/`` / ``icons/`` once, refuse destination
collisions and duplicate kinds before writing anything, prepend one provenance
line under each copied spec's H1, and print the §5.3 completion receipt.

Usage::

    python3 scripts/apply_template.py <project_path> --root <workspace_root> [--root ...] [--dry-run]

A root is a workspace directory exposing ``templates/design_spec.md`` (library
shape) or one ``templates/design_spec.<kind>.<id>.md`` per kind (project
shape). A root that resolves to the target project is consumed in place. The
tool selects nothing: which roots to pass is the Stage-1 / Quick decision.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from attribution_guard import require_skill_integrity  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402
from register_template import (  # noqa: E402
    KIND_CONFIG,
    SpecParseError,
    _read_spec,
    _validate_spec_shape,
    validate_qualified_spec_identity,
)

configure_utf8_stdio()

SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
CHECKER = SCRIPT_DIR / "svg_quality_checker.py"
KINDS = ("brand", "style", "layout", "deck")
STRUCTURAL_KINDS = ("layout", "deck")
ASSET_DIRS = ("images", "icons")
BITMAP_SUFFIXES = {
    ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp",
}


class ApplyTemplateError(Exception):
    """A contract violation that blocks installation."""


@dataclass
class SpecRecord:
    kind: str
    template_id: str
    path: Path
    frontmatter: dict


@dataclass
class RootRecord:
    supplied: str
    root: Path
    source: str  # library | explicit
    specs: list[SpecRecord]
    in_place: bool = False

    @property
    def kinds(self) -> list[str]:
        return [spec.kind for spec in self.specs]

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    @property
    def display(self) -> str:
        if self.source == "library":
            kind = self.specs[0].kind
            kind_dir = KIND_CONFIG[kind]["dir"].name
            return f"skills/ppt-master/templates/{kind_dir}/{self.specs[0].template_id}/"
        return f"{self.root}/"


@dataclass
class Mapping:
    src: Path
    dst: Path
    content: bytes | None = None  # rewritten specs carry their bytes
    status: str = "copy"  # copy | identical | in-place


@dataclass
class InstallPlan:
    project: Path
    roots: list[RootRecord]
    owner: RootRecord | None
    owner_kind: str | None
    mappings: list[Mapping] = field(default_factory=list)
    removals: list[Path] = field(default_factory=list)

    @property
    def installed_specs(self) -> list[str]:
        return [
            f"design_spec.{spec.kind}.{spec.template_id}.md"
            for root in self.roots
            for spec in root.specs
        ]


# ---------------------------------------------------------------------------
# Discovery and validation
# ---------------------------------------------------------------------------


def _frontmatter_identity(spec_path: Path) -> tuple[str, str, dict]:
    frontmatter, _body = _read_spec(spec_path)
    fm = frontmatter or {}
    kind = str(fm.get("kind") or "").strip()
    if kind not in KINDS:
        raise ApplyTemplateError(
            f"{spec_path} declares no kind in its frontmatter; a legacy or "
            "semantic-only package needs a new workspace from Create Template"
        )
    template_id = str(fm.get(KIND_CONFIG[kind]["id_key"]) or "").strip()
    if not template_id:
        raise ApplyTemplateError(
            f"{spec_path} declares kind {kind!r} without {KIND_CONFIG[kind]['id_key']}"
        )
    return kind, template_id, fm


def _discover_specs(templates_dir: Path) -> list[SpecRecord]:
    bare = templates_dir / "design_spec.md"
    try:
        qualified = _validate_spec_shape(templates_dir)
    except SpecParseError as exc:
        raise ApplyTemplateError(str(exc)) from exc
    if bare.is_file():
        kind, template_id, fm = _frontmatter_identity(bare)
        return [SpecRecord(kind, template_id, bare, fm)]
    specs: list[SpecRecord] = []
    for path, _kind in qualified:
        try:
            kind, template_id, fm, _body = validate_qualified_spec_identity(path)
        except SpecParseError as exc:
            raise ApplyTemplateError(str(exc)) from exc
        specs.append(SpecRecord(kind, template_id, path, fm))
    if not specs:
        raise ApplyTemplateError(
            f"{templates_dir} holds neither design_spec.md nor "
            "design_spec.<kind>.<id>.md"
        )
    return specs


def _source_label(root: Path, specs: list[SpecRecord]) -> str:
    if len(specs) != 1:
        return "explicit"
    spec = specs[0]
    config = KIND_CONFIG[spec.kind]
    library_root = (config["dir"] / spec.template_id).resolve()
    if root.resolve() != library_root:
        return "explicit"
    index_path = config["index"]
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "explicit"
    return "library" if spec.template_id in index else "explicit"


def _load_root(supplied: str, project: Path) -> RootRecord:
    root = Path(supplied).expanduser()
    if not root.is_dir():
        raise ApplyTemplateError(f"workspace root is not a directory: {supplied}")
    if root.name == "templates" and (root / "design_spec.md").is_file():
        raise ApplyTemplateError(
            f"{supplied} is an inner templates/ directory; pass its workspace "
            "root so sibling images/ and icons/ install with it"
        )
    root = root.resolve()
    templates_dir = root / "templates"
    if not templates_dir.is_dir():
        raise ApplyTemplateError(f"{supplied} has no templates/ directory")
    specs = _discover_specs(templates_dir)
    in_place = root == project.resolve()
    if in_place and any(spec.path.name == "design_spec.md" for spec in specs):
        raise ApplyTemplateError(
            "an in-place project root must already hold kind-qualified specs "
            "(design_spec.<kind>.<id>.md); templates/design_spec.md is a "
            "library shape"
        )
    record = RootRecord(
        supplied=supplied,
        root=root,
        source="explicit" if in_place else _source_label(root, specs),
        specs=specs,
        in_place=in_place,
    )
    if record.source == "library" and specs[0].kind == "style":
        for extra in (*ASSET_DIRS, "exports"):
            if (root / extra).exists():
                raise ApplyTemplateError(
                    f"Style-only library package {record.display} carries "
                    f"{extra}/; a Style contributes only its spec"
                )
    return record


def _validate_root(record: RootRecord) -> None:
    command = [
        sys.executable,
        str(CHECKER),
        str(record.templates_dir),
        "--template-mode",
        "--canonical-authoring",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        tail = "\n".join(
            line for line in (result.stdout + result.stderr).splitlines()[-25:]
        )
        raise ApplyTemplateError(
            f"template validation failed for {record.display} "
            f"(exit {result.returncode}):\n{tail}"
        )


def _check_kind_cardinality(roots: list[RootRecord]) -> None:
    seen: dict[str, str] = {}
    for record in roots:
        for kind in record.kinds:
            if kind in seen:
                raise ApplyTemplateError(
                    f"kind {kind!r} is contributed by both {seen[kind]} and "
                    f"{record.display}; select one root per kind"
                )
            seen[kind] = record.display


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def _provenance_line(record: RootRecord) -> str:
    return f"> **Installed from**: `{record.display}` ({record.source})"


def _spec_with_provenance(spec_path: Path, record: RootRecord) -> bytes:
    text = spec_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    body_start = 0
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                body_start = idx + 1
                break
    h1 = next(
        (idx for idx in range(body_start, len(lines)) if lines[idx].startswith("# ")),
        None,
    )
    if h1 is None:
        raise ApplyTemplateError(f"{spec_path} has no H1 to anchor the provenance line")
    rewritten = lines[: h1 + 1] + ["", _provenance_line(record)] + lines[h1 + 1 :]
    return "\n".join(rewritten).encode("utf-8")


def _iter_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file())


def _is_spec_file(path: Path) -> bool:
    return path.name == "design_spec.md" or (
        path.name.startswith("design_spec.") and path.suffix == ".md"
    )


def _structural_files(record: RootRecord) -> list[Path]:
    return [
        path
        for path in _iter_files(record.templates_dir)
        if not _is_spec_file(path) and path.suffix.lower() not in BITMAP_SUFFIXES
    ]


def _plan(project: Path, roots: list[RootRecord]) -> InstallPlan:
    owner = next((r for r in roots if "layout" in r.kinds), None)
    owner_kind = "layout" if owner else None
    if owner is None:
        owner = next((r for r in roots if "deck" in r.kinds), None)
        owner_kind = "deck" if owner else None
    plan = InstallPlan(project=project, roots=roots, owner=owner, owner_kind=owner_kind)
    project_templates = project / "templates"

    for record in roots:
        if record.in_place:
            continue
        for spec in record.specs:
            plan.mappings.append(
                Mapping(
                    src=spec.path,
                    dst=project_templates / f"design_spec.{spec.kind}.{spec.template_id}.md",
                    content=_spec_with_provenance(spec.path, record),
                )
            )
        for asset_dir in ASSET_DIRS:
            source_dir = record.root / asset_dir
            if not source_dir.is_dir():
                continue
            for path in _iter_files(source_dir):
                plan.mappings.append(
                    Mapping(src=path, dst=project / asset_dir / path.relative_to(source_dir))
                )
    if owner is not None and not owner.in_place:
        for path in _structural_files(owner):
            plan.mappings.append(
                Mapping(src=path, dst=project_templates / path.relative_to(owner.templates_dir))
            )
        in_place_deck = next(
            (r for r in roots if r.in_place and "deck" in r.kinds), None
        )
        if owner_kind == "layout" and in_place_deck is not None:
            plan.removals.extend(_structural_files(in_place_deck))
    return plan


def _preflight(plan: InstallPlan) -> None:
    by_dst: dict[Path, Mapping] = {}
    for mapping in plan.mappings:
        if mapping.dst in by_dst:
            raise ApplyTemplateError(
                f"two selected files map to {mapping.dst}: "
                f"{by_dst[mapping.dst].src} and {mapping.src}"
            )
        by_dst[mapping.dst] = mapping
    removals = set(plan.removals)
    collisions: list[str] = []
    for mapping in plan.mappings:
        if mapping.dst in removals or not mapping.dst.exists():
            continue
        if mapping.content is not None:
            identical = mapping.dst.read_bytes() == mapping.content
        else:
            identical = filecmp.cmp(mapping.src, mapping.dst, shallow=False)
        if identical:
            mapping.status = "identical"
        else:
            collisions.append(f"{mapping.dst} (from {mapping.src})")
    if collisions:
        raise ApplyTemplateError(
            "destination collision; remove or rename before installing:\n  "
            + "\n  ".join(collisions)
        )


# ---------------------------------------------------------------------------
# Writing and receipt
# ---------------------------------------------------------------------------


def _write(plan: InstallPlan) -> None:
    for path in plan.removals:
        path.unlink()
    for mapping in plan.mappings:
        if mapping.status == "identical":
            continue
        mapping.dst.parent.mkdir(parents=True, exist_ok=True)
        if mapping.content is not None:
            mapping.dst.write_bytes(mapping.content)
        else:
            shutil.copy2(mapping.src, mapping.dst)


def _receipt(plan: InstallPlan) -> str:
    kinds_present = {kind for root in plan.roots for kind in root.kinds}
    identity = (
        "brand" if "brand" in kinds_present
        else "deck" if "deck" in kinds_present
        else "current-project"
    )
    structure = plan.owner_kind or "free-design"
    application = "deck" if "deck" in kinds_present else "none"
    direction = "style" if "style" in kinds_present else "unresolved"
    active_roster = (
        f"{plan.owner_kind}:{plan.owner.display}" if plan.owner else "none"
    )
    install = "in-place" if all(root.in_place for root in plan.roots) else "copied"
    return (
        "roots=" + ";".join(root.display for root in plan.roots)
        + "; sources=" + ";".join(root.source for root in plan.roots)
        + "; kinds=" + ";".join(",".join(root.kinds) for root in plan.roots)
        + f"; segments=identity:{identity},structure:{structure},"
        f"application_context:{application},direction:{direction}"
        + f"; active_roster={active_roster}"
        + f"; install={install}"
        + "; installed_specs=" + ",".join(plan.installed_specs)
    )


def apply_templates(
    project_path: str | Path,
    root_args: list[str],
    *,
    dry_run: bool = False,
    validate: bool = True,
) -> InstallPlan:
    """Plan, preflight, and (unless ``dry_run``) install the selected roots."""
    project = Path(project_path).expanduser().resolve()
    if not project.is_dir():
        raise ApplyTemplateError(f"project path is not a directory: {project_path}")
    if not root_args:
        raise ApplyTemplateError("pass at least one --root workspace")
    roots = [_load_root(arg, project) for arg in root_args]
    unique = {record.root for record in roots}
    if len(unique) != len(roots):
        raise ApplyTemplateError("the same workspace root was passed more than once")
    _check_kind_cardinality(roots)
    if validate:
        for record in roots:
            _validate_root(record)
    plan = _plan(project, roots)
    _preflight(plan)
    if not dry_run:
        _write(plan)
    return plan


def main(argv: list[str] | None = None) -> int:
    require_skill_integrity()
    parser = argparse.ArgumentParser(
        description=(
            "Install selected Brand/Style/Layout/Deck workspaces into a "
            "project's templates/, images/, and icons/ (apply-template-workspace §4)."
        ),
    )
    parser.add_argument("project_path", help="Initialized project root")
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="WORKSPACE_ROOT",
        help="Workspace root to install; repeat for several kinds (one root per kind)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate, plan, and print the mapping and receipt without writing",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip the per-root svg_quality_checker --template-mode run (already validated in this turn)",
    )
    args = parser.parse_args(argv)
    try:
        plan = apply_templates(
            args.project_path,
            args.root,
            dry_run=args.dry_run,
            validate=not args.skip_validation,
        )
    except ApplyTemplateError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    verb = "would install" if args.dry_run else "installed"
    for path in plan.removals:
        print(f"[remove] {path}")
    same = 0
    for mapping in plan.mappings:
        if mapping.status == "identical":
            same += 1
        label = "[same]" if mapping.status == "identical" else "[copy]"
        print(f"{label} {mapping.dst}")
    copied = len(plan.mappings) - same
    note = f", {same} already present" if same else ""
    print(f"[OK] {verb} {copied} file(s) into {plan.project}{note}")
    print(_receipt(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
