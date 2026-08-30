---
description: Generate-PPTX runbook for validating and installing selected Brand, Style, Layout, and Deck workspaces as separate project-local specs.
---

# Apply Template Workspace Stage

> Run from [`generate-pptx.md`](../generate-pptx.md) Step 4 only after Stage 1 confirms at least one exact template workspace; [`quick-generate`](../profiles/quick-generate.md) enters only for exact roots or a current Create Template handoff. Never load for free design, bare names, or style descriptions. This stage applies the completed selection; it never chooses a workspace or changes the communication contract.

## 1. Gate and Normalize Inputs

🚧 **GATE**: Default Stage 1 confirmed a non-free selection, or Quick received exact roots directly from the user/current Create Template handoff — in Quick that input is the complete selection authority (no Confirm UI, no `template_options.json` / `template_selection.json` / `template_handoff.json`). Every selected input resolves to one current contract:

| Input shape | Spec and SVG source | Asset source |
|---|---|---|
| Current workspace root | `<root>/templates/design_spec.md`, or one `design_spec.<kind>.<id>.md` per kind, plus `<root>/templates/` | Existing `<root>/images/` and `<root>/icons/` |
| Current Create Template handoff | Its exact validated library or project workspace root | Portable sibling `images/` and `icons/`; already installed only when the root is the target project |

Spec naming and kind declaration follow [`templates/README.md`](../../templates/README.md); a root exposing several kind-qualified specs contributes all of them. Never accept only another project's inner `templates/` directory — that omits sibling assets.

| Source label | Resolution rule |
|---|---|
| `library` | The normalized root exactly equals `templates/<kind_dir>/<id>/` derived from an entry in that kind's `*_index.json` |
| `explicit` | The user or Create Template supplied an exact root not registered at that canonical index-derived root |

Read library choices only from the four `*_index.json` files; never scan kind directories or promote an unregistered directory into the catalog. The label changes discovery provenance only, never validation, precedence, or installation.

**Selection cardinality**: at most one root per kind; all four kinds may coexist. A multi-kind explicit root contributes all its specs atomically and combines only with non-overlapping kinds; reject duplicate kinds before validation.

**Hard rule — raw source boundary**: a raw PPTX is not a template workspace. Raw PPTX plus new content uses [`edit-native-pptx`](../edit-native-pptx.md); a reusable template request runs [`create-template`](../create-template.md) first, whose validated root becomes a Stage-1 candidate preselected only when it is the sole supplied root. Never add Master/Layout/placeholder structure directly to an existing PPTX or SVG project.

**Current-contract gate**: reject flat-root, semantic-legacy, or incomplete structured packages (old baseline/distillation metadata, incomplete Master identity, legacy direct atomic placeholders); create a new workspace through Create Template, from the original PPTX when native topology must be preserved.

## 2. Read the Matching Schema

Read [`templates/README.md`](../../templates/README.md), then only the README for each supplied kind:

| Kind | Schema | Owned segment |
|---|---|---|
| `brand` | [`templates/brands/README.md`](../../templates/brands/README.md) | Identity: color, typography, logo, voice/tone, icon style |
| `style` | [`templates/styles/README.md`](../../templates/styles/README.md) | Direction/method: communication method, visual language, composition, information-expression defaults |
| `layout` | [`templates/layouts/README.md`](../../templates/layouts/README.md) | Structure: canvas, page structure, semantic text roles, page types, SVG roster |
| `deck` | [`templates/decks/README.md`](../../templates/decks/README.md) | Application plus integrated identity and structure |

A Layout created with `mirror` stays eligible only when its source is brand-neutral and application-neutral; keep a branded or application-bearing source as a Deck or re-author it through `standard` / `fidelity`. Before mapping any workspace, run the shared package validator from its root — Brand/Style are roster-free, the active structure validates its roster, a shadowed Deck still validates its contract; any error blocks installation:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<workspace_root>/templates" --template-mode --canonical-authoring
```

## 3. Structured Preflight

Before copying a Deck or Layout workspace (Brand and Style skip this), inspect every SVG root and slot: every page declares root Master/Layout keys and picker names; Master/Layout visuals are direct atoms, not layer `<g>` wrappers; every non-composite slot is a top-level `<g>` with positive bounds and exactly one compatible carrier; a composite region uses an explicit `object` proxy; zero-slot Layouts are valid; the contract is current — reject a legacy contract instead of repairing it in the target project.

## 4. Install Each Distinct Root Once

Validate each normalized root once. The effective structural owner is Layout when selected, otherwise Deck; install only its SVG/non-bitmap structural payload, but install every selected spec. A library root's bare `templates/design_spec.md` installs as `design_spec.<kind>.<id>.md` (`<id>` from its frontmatter); a project root's qualified specs keep their validated filenames. Never merge spec bodies, and never copy one multi-kind root's shared SVG or asset pool once per kind. `templates/design_spec.md` is never valid beside qualified project specs. Prepend exactly one provenance line under each copied spec's H1 and leave the rest untouched (an in-place root is not rewritten):

```markdown
> **Installed from**: `skills/ppt-master/templates/brands/mckinsey/` (library)
```

**Root mapping**: copy every selected spec to its qualified destination; if the root is the structural owner, copy its declared SVG roster and other non-bitmap structural files once (including mirror `source_themes.json`), never a Deck roster shadowed by a selected Layout, preserving inline `<metadata type="application/json">` and `data-pptx-native-authority="json"` exactly; copy the root's package-owned `images/` and `icons/` once (a Style-only root has none — reject a Style-only library package carrying asset or review payloads); ignore `exports/`.

| Kind | Consumption behavior |
|---|---|
| `brand` | Identity constrained; structure free unless Layout or Deck is also selected |
| `style` | Direction/method without identity, prototypes, or structure; Style-only and Style + Brand stay flat, Style + Layout/Deck follows that owner; Style never activates visual review |
| `layout` | Reusable structure, precedence over Deck; Default plans against its prototypes, Quick reads the roster and authors its Master/Layout/slot contract directly |
| `deck` | Descriptive application context and identity; structure and prototype roster only when no Layout is selected |

**Atomic install preflight**: resolve every source and destination path; enumerate the union mapping across all roots and across `templates/`, `images/`, `icons/`, mapping each source file at most once; resolve Layout-over-Deck precedence before building the map so the shadowed roster never enters it; reject every destination collision and duplicate kind before writing; write the accepted mapping once — never recursive copy as an implicit conflict policy. An input equal to the target project is consumed in place; if a selected Layout supersedes its in-place Deck roster, stage the mapping and replace the roster atomically.

**Hard rule — project-local consumer boundary**: after installation, Default final Stage 2, Quick's agent before authoring, and every later role read only `<project_path>/templates/` and the project-local `images/` / `icons/` pools; the library or external root is installation input only.

Template SVGs are complete Slide authoring prototypes (Master + Layout context already resolved), so `page_layouts` selects one directly; standalone Master/Layout definition SVGs are invalid, and an unselected authored prototype may still back a reusable Layout definition. Default records `page_layouts` and the structure lock; Quick freezes the natural-language application paragraph in active context and writes the Master/Layout/slot contract directly into the output SVGs, staying flat only without a structure owner or under an explicit visual-only instruction. For a template-owned Chart/Table carrying `data-pptx-native-authority="json"`, the installed inline JSON remains the object's authority: a page may keep or regenerate the preview from that JSON but never derives replacement JSON from the preview.

## 5. Segment Precedence Is Resolved While Reading

Installation copies specs; it never merges them. The consuming role — Default final Stage 2 through [`strategist-template.md`](../../references/strategist-template.md), or Quick's agent before authoring — reads every installed `design_spec.<kind>.<id>.md` and resolves the segments in context; asset collisions are rejected at install time (§4), segment conflicts are a reading decision. Never reinterpret the confirmed Stage-1 contract here: Default obtains any additional material conflict decision through chat after Stage 1 without reopening selection; Quick follows explicit conflict instructions, and an unresolved material conflict is a hard prerequisite handled in chat, never by Confirm UI or path order.

### 5.1 Different Kinds

| Segment | Starting owner |
|---|---|
| Identity | Brand, otherwise Deck, otherwise unresolved until the consuming plan; Style color/type/icon/image values are direction candidates, never identity truth |
| Structure | Layout when present, otherwise Deck, otherwise free design until the consuming plan; Style owns no canvas, prototype, Master/Layout, slot, or page mapping |
| Reusable application context | Deck only; preserved for comparison, never the current project's application contract |
| Direction / method | Style when present, otherwise unresolved; Deck prototypes and Signature facts inform compatibility but do not own this segment |

Apply each segment wholesale; never mix fields implicitly. Brand or Deck identity overrides Style's identity-adjacent defaults; a Style direction adapts to that identity but cannot relabel its candidates as brand facts. **Hard rule — an owned segment governs visual weight, not only values**: when an owner declares how a value dominates, recedes, or stays rare, that instruction carries the value's authority; a Style's whitespace tendency never demotes a Brand's dominant color to an accent. Before Style overlays Layout or Deck guidance, verify its method fits the structure (and, for Deck, its reusable context); on mismatch require omitting Style or choosing a compatible pair, never silently weakening a segment. Field-level micro-adjustments such as a primary-color override are not a workspace selection: Default carries them into the Stage-2 confirmation fields, Quick treats them as direct authoring constraints.

### 5.2 Selection Conflicts

Duplicate kinds are selection errors: Default returns them to Stage 1, Quick asks for narrower roots. Layout plus Deck is valid — Layout owns structure, Deck keeps its other segments. Never split a multi-kind root, average same-kind specs, or choose by path order.

### 5.3 Installed Set

Each installed file keeps its own frontmatter `kind` and `<id>`; nothing is relabelled or merged. Routing is derived while reading — structure from Layout, else Deck; identity from Brand or Deck; direction from Style. A project-local Brand + Layout pair does not become a reusable library Deck.

**Completion receipt**: `roots=<unique normalized roots>; sources=<library|explicit per root>; kinds=<all contributed kinds per root>; segments=identity:<owner>,structure:<owner>,application_context:<owner>,direction:<owner>; active_roster=<layout|deck|none>:<source root>; install=<in-place|copied>; installed_specs=<comma-separated design_spec.<kind>.<id>.md>`.

## ✅ Template Workspace Applied

- [x] Every selected input was an index-derived library root or an exact explicit/Create Template root satisfying a listed contract
- [x] Every kind schema passed preflight; structured SVG checks ran only for Layout/Deck inputs
- [x] Duplicate kinds and destination collisions were rejected before one atomic install; Layout-over-Deck precedence selected exactly one active roster
- [x] `<project_path>/templates/` and portable sibling assets are complete and the only downstream template source
- [ ] **Next**: Default completes the template-selection handoff and continues [`generate-pptx.md`](../generate-pptx.md) Step 4 Stage 2; Quick returns to [`quick-generate`](../profiles/quick-generate.md) §2
