---
description: Generate profile for agent-decided source and resource preparation, direct SVG authoring, and final PPTX delivery without Strategist or confirmation artifacts.
---

# Quick Generate Profile

> Generate-PPTX profile, not a top-level route. It removes the separate
> Strategist and confirmation phase; it does not remove the facts, resources,
> or export capabilities needed to build the final deck.

**Trigger**: the user explicitly requests quick/fast generation, asks to skip
strategy/confirmation, or directs the agent to proceed to SVG and export.
Page count alone never activates or blocks this profile.

---

## 1. Profile Boundary

| Concern | Quick Generate contract |
|---|---|
| Interaction | The current main agent decides content, design, resources, and implementation without Strategist, Confirm UI, or approval stops |
| Inputs | Any supported Generate input; convert/import sources and run bounded factual research when the input requires them |
| Resources | Prepare every project-local image, icon, formula, and required provenance/manifest artifact before the referencing SVG is authored |
| Planning artifacts | Do not create `design_spec.md`, `spec_lock.md`, confirmation payloads, or a second persisted strategy |
| Delivery | Hand-author the resolved SVG roster, run one lockless final checker, skip `finalize_svg.py`, and export the final native PPTX through `--quick-generate` |

**Hard rule — speed removes interaction, not material**: all ordinary source,
research, resource-preparation, analysis, and export capabilities remain
available when needed; the missing planning contract relaxes design constraints
only.

Explicit user facts, wording, choices, exclusions, and permission boundaries
still win. For every unspecified routine choice, decide directly and continue;
do not ask the user to approve a strategy or implementation detail.

After entry, continue through selected work, the final checker, and export.
Pause only for user interruption or an unresolved hard prerequisite.

**Default — optional production behavior (may override when useful)**: Speaker
notes, custom object animations, and narration start off. The current agent may
enable any ordinary capability when the request or deck benefits; use its
normal inputs, flags, and prerequisites without asking for approval. Quick
never creates or reads a Design Spec or lock to enable it.

**Mandatory — discover motion before deciding whether to load it**: scan this
compact gate once; do not load the full execution reference when the defaults
already fit.

| Signal | Action |
|---|---|
| The same semantic object or scene continues across adjacent pages | Load [`animations.md`](../../references/animations.md) before SVG authoring; prepare both visible endpoints and use its Morph contract |
| Page- or object-specific reveal, renewed emphasis, meaningful movement, or same-page removal clarifies the message | Load [`animations.md`](../../references/animations.md) before SVG authoring; preserve the required units/states, then run [`customize-animations`](../stages/customize-animations.md) after the final checker |
| One deck-wide entrance policy supplies all required staged reveal | Load [`animations.md`](../../references/animations.md) before export and use an exporter flag such as `-a auto`; do not run the custom stage |
| A directional/section boundary benefits from a non-default transition | Load [`animations.md`](../../references/animations.md) before export and select from its §3 playbook |
| No earlier signal applies | Keep `fade` transitions and object animation `none`; do not load the motion reference |

This gate activates capability discovery, not motion coverage. Keep the
defaults when no row supplies a concrete communication job. When several
signals apply, perform every required action and use the earliest required load
point; a before-authoring signal always overrides a before-export-only timing.

---

## 2. Source and Resource Preparation

Run [`generate-pptx.md`](../generate-pptx.md) Step 1 when applicable. Initialize
the minimal workspace with:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> \
  --format <format> --quick-generate
```

It creates only `svg_output/` and no root README. Add capability inputs only
when triggered; checker/exporter create `validation/`, `exports/`, and the
default-path `backup/`. With source files, continue with Step 2
`import-sources`; it creates the triggered input directories. Never scaffold a
Design Spec or lock. Use a new path, or verify that an existing path's
`svg_output/` is empty; Quick ignores any existing `design_spec.md` or
`spec_lock.md`.

Before writing P01, resolve in active context:

- the slide roster, canvas, visual direction, palette, typography, and wording;
- when useful, one transient deck-level visual motif with an identity or
  communication job, a recognizable invariant, and planned variation across
  applicable page roles; omit it when restraint serves the deck better;
- a transient resource roster with page, filename, purpose, visual intent,
  acquisition path, crop behavior, and status. For an image/formula, include
  its page relationship plus any subject position, focus, quiet region, or
  overlay-safety cue that must exist before SVG authoring;
- the implementation path for each resource. An explicit user path wins;
  otherwise choose the registered automatic/default path without another
  interaction.

Prepare only the resource paths that the roster triggers:

| Resource | Required preparation |
|---|---|
| Supplied/extracted image | Copy the selected file into `images/`; preserve its factual/provenance context and use the measured file rather than an invented substitute |
| Bundled/custom icon | Follow the [icon library contract](../../templates/icons/README.md), resolve the selected SVG under project `icons/`, and use `icon_sync.py` for bundled icons |
| Formula | Follow the [`latex_render.py` contract](../../scripts/docs/image.md), write `images/formula_manifest.json`, run the renderer, and keep the rendered PNG under `images/` |
| AI image | Follow `image-base.md` + `image-generator.md`; keep `image_prompts.json` and its human-readable sidecar |
| Web image | Follow `image-base.md` + `image-searcher.md`; keep query/status data and `image_sources.json`, including any required on-slide attribution |
| Illustration slice | Generate or obtain the parent sheet, run `slice_images.py`, and place only the resulting element files |

After image resources change, run `analyze_images.py` so
`analysis/image_analysis.csv` reflects the files that SVG authoring will use.
Operational manifests and provenance are resource truth, not a hidden design
strategy.

Every required resource must reach a usable terminal state before the
referencing page is authored. A required `Needs-Manual` resource blocks Quick
delivery even when an unverified candidate file exists. After a manual supply
or replacement, validate the file/provenance and reconcile the row to
`Generated`, `Sourced`, or `Rendered`; do not use file presence as a bypass or
silently replace it with unrelated material.

---

## 3. Direct SVG Authoring

Always read
[`shared-standards-core.md`](../../references/shared-standards-core.md),
[`svg-effects.md`](../../references/svg-effects.md), and
[`native-shape-authoring.md`](../../references/native-shape-authoring.md). Do
not load `executor-base.md`: its persisted-plan prerequisites do not apply to
this profile. For any image/formula, always read
[`executor-image.md`](../../references/executor-image.md),
[`image-layout-spec.md`](../../references/image-layout-spec.md),
[`image-layout-patterns.md`](../../references/image-layout-patterns.md), and
[`svg-image-embedding.md`](../../references/svg-image-embedding.md); add
[`executor-web-image.md`](../../references/executor-web-image.md) for a sourced
web image. Load [`canvas-formats.md`](../../references/canvas-formats.md) only
for a non-default canvas.

Use one zero-padded filename width sized for the resolved roster, such as
`01_cover.svg` through `12_end.svg` or `001_cover.svg` through `120_end.svg`.
Never reuse pages from another run: the exporter publishes every SVG discovered
under `svg_output/`.

**Canvas**: unless the user specifies another canvas, use `ppt169` with
`viewBox="0 0 1280 720"`. For another requested registered format, load
[`canvas-formats.md`](../../references/canvas-formats.md) and use its exact
viewBox. The first SVG establishes the export canvas; every remaining page must
match it exactly.

**Structure**: author flat, Slide-local SVG only. Include the complete visible
page and all resource references in each SVG; set one root
`data-pptx-page-role` from `cover`, `toc`, `section`, `content`, or `ending`,
and omit Master/Layout/layer/placeholder metadata.

**Typography**: name an installed concrete font family in the SVG; do not depend
on a lock or generated font asset.

**Generation pacing**: the current main agent hand-writes the SVG roster in
order. Use P01 as the visual anchor and continue directly through the remaining
pages without a first-page checker or confirmation stop. When a motif was
resolved, reuse it selectively and vary scale, crop, density, position, or
content interaction instead of cloning one ornament. Keep this choice only in
active context; create no planning artifact or approval stop. After the complete
roster exists, run the one final checker below. Apply other supporting tools and
stages only when their capability is actually needed.

---

## 4. Export

After every page and required referenced resource exists, run the lockless
final SVG check:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --quick-generate --stage final --json
```

Fix every blocking error and rerun the same command. Then export:

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate
```

`--quick-generate` reads `svg_output/` as the page source and resolves the
project-local assets referenced by those SVGs. It infers one consistent canvas,
uses a lockless flat PowerPoint package, and does not force-disable ordinary
export options. Notes, custom object animation, and narration remain off unless
selected by the agent. Do not run `finalize_svg.py`.

The exporter requires a passing `final` report whose SVG fingerprint matches
the current `svg_output/`; missing, blocking, non-final, or stale reports stop
before PPTX creation. The default output path retains ordinary backup and
postflight behavior. An explicit `-o <path>.pptx` keeps the ordinary no-backup
behavior. On failure, repair the owning SVG, resource, or optional capability
input, rerun the final checker, then export again; do not create a Design Spec
or lock.

```markdown
## ✅ Quick Generate Complete

- [x] All required source/resource preparation is complete
- [x] Resolved SVG pages and their project-local references exist
- [x] The lockless final SVG quality report passes and matches the current SVGs
- [x] Every selected optional export capability completed
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No Strategist, confirmation, Design Spec, or lock artifact was created
- [ ] **Next**: Report the PPTX path
```
