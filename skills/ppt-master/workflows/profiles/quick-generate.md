---
description: Generate profile for agent-decided source and resource preparation, direct SVG authoring, and one PPTX export without Strategist or confirmation artifacts.
---

# Quick Generate Profile

> Generate-PPTX profile, not a top-level route. It removes the separate
> Strategist and confirmation phase; it does not remove the facts or visible
> resources needed to build the deck.

**Trigger**: the user explicitly requests quick/fast generation, asks to skip
strategy/confirmation, or directs the agent to proceed to SVG and export.
Page count alone never activates or blocks this profile.

---

## 1. Profile Boundary

| Concern | Quick Generate contract |
|---|---|
| Interaction | The current main agent resolves routine content, page, visual, and resource choices in active context; do not invoke Strategist, open Confirm UI, or wait for design confirmation |
| Inputs | Any supported Generate input; convert/import sources and run bounded factual research when the input requires them |
| Resources | Prepare every project-local image, icon, formula, and required provenance/manifest artifact before the referencing SVG is authored |
| Planning artifacts | Do not create `design_spec.md`, `spec_lock.md`, confirmation payloads, or a second persisted strategy |
| Delivery | Hand-author the resolved SVG roster and export one native PPTX through `--quick-generate` |

**Hard rule — speed removes interaction, not material**: source conversion,
topic research, supplied/extracted assets, AI or web images, illustration
slices, project icons, formula rendering, and regenerated image facts remain
available whenever the deck needs them. The workspace may therefore contain
`sources/`, `analysis/`, `images/`, `icons/`, and their operational manifests.
Do not misread direct export's lack of report sidecars as a ban on resource
artifacts.

Explicit user facts, wording, choices, exclusions, and permission boundaries
still win. For every unspecified routine choice, decide directly and continue;
do not ask the user to approve a provisional strategy. Stop only when a required
fact/resource cannot be resolved safely or an explicit user decision is
genuinely required.

Structured template reuse, native chart/table replacement, Live Preview,
speaker notes, animation, narration, and visual-review delivery remain
default-pipeline capabilities. Do not silently discard one of those requested
capabilities to fit this profile. Source preparation and visible-page resource
preparation do not disqualify Quick Generate.

---

## 2. Source and Resource Preparation

Run [`generate-pptx.md`](../generate-pptx.md) Step 1 source conversion and
bounded research when applicable. Initialize/import the project through Step 2
when those tools or project-local resources are needed, but never scaffold a
Design Spec or lock. Use a new project path, or first verify that its
`svg_output/` is empty and that no `design_spec.md` / `spec_lock.md` from
another pipeline is present.

Before writing P01, resolve in active context:

- the slide roster, canvas, visual direction, palette, typography, and wording;
- a transient resource roster with page, filename, purpose, visual intent,
  acquisition path, crop behavior, and status; for a hero page or other
  image-led use, the visual intent includes an action-bearing composition;
- the implementation path for each resource. An explicit user path wins;
  otherwise choose the registered automatic/default path without another
  interaction.

**Default — action-bearing image composition (may override only for an explicit user/material boundary or a page-specific restraint decision)**: For a hero page or otherwise image-led resource, resolve one concrete image/content or image/shape relationship before SVG authoring. Position, size, routine crop, and a legibility-only scrim alone do not constitute that relationship. A plain split or full-bleed treatment remains valid only when the explicit boundary requires it or the agent records a page-specific restraint reason in active context; decide and continue without another interaction.

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
[`shared-standards-core.md`](../../references/shared-standards-core.md). Do not
load `executor-base.md`: its persisted-plan prerequisites do not apply to this
profile. Load the conditional image/web/canvas references only when the
resolved SVG needs them.

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
order. Use P01 as the visual anchor, continue directly through the remaining
pages, and skip the default first-page and final checker gates. This profile
still obeys every loaded SVG/resource rule; skipping a report does not relax
the authoring contract.

---

## 4. Direct Export

Run one export command after every page exists and every required referenced
resource in the resolved roster has validated evidence and a usable status:

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate
```

`--quick-generate` reads `svg_output/` as the page source and resolves the
project-local assets referenced by those SVGs. It infers one consistent canvas,
uses a flat PowerPoint package with converter defaults, disables notes and
motion, skips lock/theme export sidecars, and writes no backup, conversion
trace, or validation report. Resource manifests remain in the project. An
explicit `-o <path>.pptx` may replace the default `exports/` destination.

**Package sanity**: the standard non-quiet command succeeds only when
`[QUICK-GENERATE] status=passed`, the discovered SVG count equals the published
Slide count, and the PPTX passes in-memory ZIP integrity. This receipt does not
claim SVG-checker, visual-quality, factual-correctness, or default postflight
approval. On failure, repair the owning SVG/resource and rerun this command; do
not create planning or validation-report artifacts.

```markdown
## ✅ Quick Generate Complete

- [x] All required source/resource preparation is complete
- [x] Resolved SVG pages and their project-local references exist
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No Strategist, confirmation, Design Spec, or lock artifact was created
- [ ] **Next**: Report the PPTX path
```
