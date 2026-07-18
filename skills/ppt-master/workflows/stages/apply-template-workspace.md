---
description: Conditional Generate-PPTX runbook for validating, installing, or fusing explicit Brand, Layout, and Deck workspaces.
---

# Apply Template Workspace Stage

> Run only from [`generate-pptx.md`](../generate-pptx.md) Step 3 after the user supplies an explicit workspace-root path, or after Create Template hands off its exact validated workspace root in the current conversation. Never load this stage for free design, a bare template name, a style description, or a brand mention.

## 1. Gate and Normalize Inputs

🚧 **GATE**: Every external input resolves to one of these current contracts:

| Input shape | Spec and SVG source | Asset source |
|---|---|---|
| Current workspace root | `<root>/templates/design_spec.md` and `<root>/templates/` | Existing `<root>/images/` and `<root>/icons/` |
| Compatible legacy-flat root | `<root>/design_spec.md` and current-contract SVGs under `<root>/` | Package-local files |
| Current Create Template handoff | Its exact validated library or project workspace root | Existing portable sibling `images/` and `icons/`; already installed only when the root is the target project |

The spec frontmatter MUST declare `kind: brand`, `kind: layout`, or `kind: deck`. Do not accept only another project's inner `templates/` directory because that omits sibling assets.

**Hard rule — raw source boundary**: A raw PPTX is not a Step 3 workspace. Raw PPTX plus new content uses [`template-fill-pptx`](../template-fill-pptx.md). When the user wants reusable SVG/template generation, run [`create-template`](../create-template.md) first and return with its validated workspace root. Never add Master/Layout/placeholder structure directly to an existing PPTX or SVG project.

**Compatibility gate**: Reject semantic-legacy or incomplete structured packages, including old baseline/distillation metadata, incomplete Master identity, or legacy direct atomic placeholders. Create a new current workspace through Create Template; use the original PPTX when native topology must be preserved. A legacy-flat directory is readable only when its SVG contract is current.

## 2. Read the Matching Schema

Read [`templates/README.md`](../../templates/README.md), then only the README for each supplied kind:

| Kind | Schema | Owned segment |
|---|---|---|
| `brand` | [`templates/brands/README.md`](../../templates/brands/README.md) | Identity: color, typography, logo, voice/tone, icon style |
| `layout` | [`templates/layouts/README.md`](../../templates/layouts/README.md) | Structure: canvas, page structure, semantic text roles, page types, SVG roster |
| `deck` | [`templates/decks/README.md`](../../templates/decks/README.md) | Application plus integrated identity and structure |

A Layout created with `mirror` remains eligible only when its source contract is brand-neutral and application-neutral. Keep a branded or application-bearing source as a Deck, or re-author it as Layout through `standard` / `fidelity`; do not remove those semantics through mirror.

## 3. Structured Preflight

Before copying a Deck or Layout workspace, inspect every SVG root and slot:

- Every page declares root Master/Layout keys and PowerPoint picker names.
- Master/Layout visuals are direct atoms, not generic layer `<g>` wrappers.
- Every non-composite slot is a top-level `<g>` with positive bounds and exactly one compatible carrier.
- A composite region uses an explicit `object` proxy; a zero-slot Layout is valid.
- The complete SVG contract is current. Reject a legacy semantic contract instead of repairing it in the target project.

## 4. Install a Single Workspace

| Kind | Install behavior |
|---|---|
| `brand` | Install `templates/` plus existing `images/` and `icons/`; ignore `exports/`. Identity is constrained; structure remains free. |
| `layout` | Install the same portable roots. Expose reusable structure; Strategist later confirms legal `mirror`, `layout`, or `style` reuse. |
| `deck` | Install the same portable roots. Expose application, identity, and structure; Strategist compares the stored application with the current communication contract before choosing reuse. |

For a compatible legacy-flat package, route SVG/spec/non-bitmaps to project `templates/`, bitmaps to project `images/`, and declared icons to project `icons/`. Do not infer legacy Master/Layout semantics from the flat directory shape.

**Atomic install preflight**:

1. Resolve every source and destination path.
2. Enumerate the complete mapping across `templates/`, `images/`, and `icons/`.
3. Reject every destination collision before writing.
4. Write the accepted mapping once; never use recursive copy as an implicit conflict policy.

If the normalized source root equals the target project root, consume it in place and copy nothing. An in-place workspace cannot participate in multi-path fusion. Ignore source `exports/`; it contains review artifacts, not portable template inputs. Empty optional roots remain absent.

Template SVGs are authoring prototypes, not export-time overlays. The generated page remains complete in `svg_output/`; `page_layouts` selects the complete prototype and its explicit structure contract for authoring.


## 5. Fuse Multiple Workspace Paths

Multi-path fusion supports different kinds, or at most two workspaces of the same kind. Resolve all segment and asset conflicts before writing any target file.

### 5.1 Different Kinds

Use segment-level integer replacement; do not mix fields implicitly:

| Combination | Identity from | Structure from | Application from |
|---|---|---|---|
| brand only | brand | free design | none |
| layout only | free design | layout | none |
| deck only | deck | deck | deck |
| brand + layout | brand | layout | current Stage-1 communication contract |
| brand + deck | brand | deck | deck |
| layout + deck | deck | compatible layout | deck |
| brand + layout + deck | brand | compatible layout | deck |

Before Layout overrides Deck structure, verify that every required application/narrative/content role fits the Layout's page roles, slot types, and capacity. On mismatch, stop and surface exactly three remedies: retain Deck structure, select another Layout, or explicitly revise the application contract.

Field-level micro-adjustments such as a primary-color override are not Step 3 fusion. Carry them into the normal Strategist confirmation fields.

### 5.2 Same Kind

Do not use path order as priority. Report every segment-level difference and ask the user to choose workspace A, workspace B, or select per segment. Only the per-segment choice opens a segment-by-segment resolution. Do not resolve field-level conflicts here. Three or more same-kind paths require the user to converge to at most two.

### 5.3 Fused Provenance

Write one final `<project>/templates/design_spec.md`. Immediately under its H1, record every source kind/path, base or override role, and user-resolved segment conflict:

```markdown
> **Fused from:**
> - deck: `templates/decks/example/` (base)
> - brand: `templates/brands/example/` (identity override)
> - layout: `templates/layouts/example/` (structure override)
> - conflicts resolved: Color Scheme from brand (user selected A)
```

Single-path installs do not add provenance. Set fused frontmatter `kind` from the resulting capability: `deck` when identity and structure are both present, `layout` for structure only, or `brand` for identity only. A project-local Brand + Layout fusion uses `kind: deck` for routing but is not automatically a reusable library Deck; its application remains current-project context.

**Completion receipt**: Report `roots=<normalized roots>; kinds=<kind per root>; install=<in-place|copied>; final_spec=<project_path>/templates/design_spec.md`.

## ✅ Template Workspace Applied

- [x] Every input was an explicit root satisfying a listed workspace contract or the exact current Create Template handoff
- [x] Kind schemas and structured SVG contracts passed preflight
- [x] All collisions and fusion conflicts were resolved before one atomic install
- [x] `<project_path>/templates/` and any portable sibling assets are complete
- [ ] **Next**: Return to [`generate-pptx.md`](../generate-pptx.md) Step 4
