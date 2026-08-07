---
description: Generate-PPTX runbook for validating and installing selected Brand, Style, Layout, and Deck workspaces as separate project-local specs.
---

# Apply Template Workspace Stage

> Run from [`generate-pptx.md`](../generate-pptx.md) Step 4 only after Stage 1 confirms at least one exact template workspace. [`quick-generate`](../profiles/quick-generate.md) enters only for exact roots or a current Create Template handoff. Never load for free design, bare names, or style descriptions. This stage applies the completed Stage-1 selection; it never chooses a workspace or changes the communication contract.

## 1. Gate and Normalize Inputs

🚧 **GATE**: Either Default Stage 1 confirmed a non-free template selection, or
Quick received exact roots directly from the
user/current Create Template handoff. In Quick, that explicit input is the complete selection authority: do
not launch Confirm UI or create `template_options.json`,
`template_selection.json`, or `template_handoff.json`. Every selected input must
resolve to one of these current contracts:

| Input shape | Spec and SVG source | Asset source |
|---|---|---|
| Current workspace root | `<root>/templates/design_spec.md` and `<root>/templates/` | Existing `<root>/images/` and `<root>/icons/` |
| Compatible legacy-flat Brand/Layout/Deck root | `<root>/design_spec.md`; Layout/Deck also require current-contract SVGs under `<root>/` | Package-local files |
| Current Create Template handoff | Its exact validated library or project workspace root | Existing portable sibling `images/` and `icons/`; already installed only when the root is the target project |

The spec frontmatter MUST declare `kind: brand`, `kind: style`, `kind: layout`, or `kind: deck`. Do not accept only another project's inner `templates/` directory because that omits sibling assets.

**Selection-source classification**:

| Source label | Resolution rule |
|---|---|
| `library` | The normalized root exactly equals `templates/<kind_dir>/<id>/` derived from an entry in that kind's `*_index.json` |
| `explicit` | The user or Create Template supplied an exact workspace root that is not registered at that canonical index-derived root |

Read library choices only from `brands_index.json`, `styles_index.json`,
`layouts_index.json`, and `decks_index.json`. Never scan kind directories or
promote an unregistered directory into the UI catalog. An explicit root remains
valid without index membership; exact equality with a registered root may be
reported as `library`. The label changes discovery provenance only, never schema
validation, segment precedence, or installation behavior.

**Selection cardinality**: Default Stage 1 permits one registered root per kind plus one explicit root; its explicit root may pair with a same-kind library root under §5.2. Quick has no page or catalog selection and accepts at most one supplied exact root per declared kind (four roots total). Kinds compose freely in both profiles. Reject larger default receipts server-side; require an oversized or duplicate-kind Quick input to converge in chat before installation, never through Confirm UI.

**Hard rule — raw source boundary**: A raw PPTX is not a template workspace. Raw PPTX plus new content uses [`template-fill-pptx`](../template-fill-pptx.md). When the user wants reusable SVG/template generation, run [`create-template`](../create-template.md) first; its validated workspace-root handoff becomes a Stage-1 candidate and is preselected only when it is the sole supplied root. Never add Master/Layout/placeholder structure directly to an existing PPTX or SVG project.

**Compatibility gate**: Reject semantic-legacy or incomplete structured packages, including old baseline/distillation metadata, incomplete Master identity, or legacy direct atomic placeholders. Create a new current workspace through Create Template; use the original PPTX when native topology must be preserved. A legacy-flat Brand/Layout/Deck directory is readable only when it satisfies its current kind contract; Layout/Deck also require a current structured SVG contract. Style has no legacy-flat form and always requires `<root>/templates/design_spec.md`.

## 2. Read the Matching Schema

Read [`templates/README.md`](../../templates/README.md), then only the README for each supplied kind:

| Kind | Schema | Owned segment |
|---|---|---|
| `brand` | [`templates/brands/README.md`](../../templates/brands/README.md) | Identity: color, typography, logo, voice/tone, icon style |
| `style` | [`templates/styles/README.md`](../../templates/styles/README.md) | Direction/method: reusable communication method, visual language, composition, and information-expression defaults |
| `layout` | [`templates/layouts/README.md`](../../templates/layouts/README.md) | Structure: canvas, page structure, semantic text roles, page types, SVG roster |
| `deck` | [`templates/decks/README.md`](../../templates/decks/README.md) | Application plus integrated identity and structure |

A Layout created with `mirror` remains eligible only when its source contract is brand-neutral and application-neutral. Keep a branded or application-bearing source as a Deck, or re-author it as Layout through `standard` / `fidelity`; do not remove those semantics through mirror.

Before mapping any current workspace, run its shared package validator from the
workspace root. This is the same schema authority used during creation and
library registration; Brand/Style pass without SVG, while Layout/Deck validate
their roster and structure:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<workspace_root>/templates" --template-mode
```

Any error blocks installation. A compatible legacy-flat root uses its own root
as the checker target.

## 3. Structured Preflight

Before copying a Deck or Layout workspace, inspect every SVG root and slot. Brand and Style workspaces are roster-free and skip this structured preflight:

- Every page declares root Master/Layout keys and PowerPoint picker names.
- Master/Layout visuals are direct atoms, not generic layer `<g>` wrappers.
- Every non-composite slot is a top-level `<g>` with positive bounds and exactly one compatible carrier.
- A composite region uses an explicit `object` proxy; a zero-slot Layout is valid.
- The complete SVG contract is current. Reject a legacy semantic contract instead of repairing it in the target project.

## 4. Install Each Workspace Separately

**Hard rule — one installed spec file per source workspace**: Never merge two
source specs into one file. Install each selected workspace's `design_spec.md`
as its own project-local file named `design_spec.<kind>.<id>.md`, where `<id>`
is that spec's frontmatter `brand_id` / `style_id` / `layout_id` / `deck_id`.
Copy its body unchanged. Several workspaces of the same kind therefore coexist
as separate files. Segment precedence is resolved by the consuming role while
reading (§5), never by rewriting spec content at install time.

| Installed file | Meaning |
|---|---|
| `templates/design_spec.<kind>.<id>.md` | A template workspace installed into this project |
| `templates/design_spec.md` | This project *is itself* a template workspace produced by project-scope Create Template; it is not an installed template and is never consumed as one |

Prepend exactly one provenance line under each installed file's H1, then leave
the rest of the document untouched:

```markdown
> **Installed from**: `skills/ppt-master/templates/brands/mckinsey/` (library)
```

| Kind | Install behavior |
|---|---|
| `brand` | Install `templates/` plus existing `images/` and `icons/`; ignore `exports/`. Identity is constrained; structure remains free. |
| `style` | Install its `design_spec.md` only. Ignore sibling project scaffolding and reject a library Style carrying asset/review payloads. Expose reusable direction/method without identity truth, page prototypes, or native structure. Default Style-only and Style + Brand derive `template_reuse_scope: style` and stay flat; Style + Layout/Deck follows the selected structure plan. Quick always realizes the resolved combination as flat pages. A Style workspace never activates visual review. |
| `layout` | Install the same portable roots. Expose the actual reusable structure; Default Strategist later inspects the prototypes, while Quick's current agent uses them for immediate flat authoring decisions in active context. |
| `deck` | Install the same portable roots. Expose descriptive application context, identity, structure, and the actual prototype roster; Default Strategist or Quick's current agent compares them with the current communication contract and content, then derives the applicable plan. |

For a compatible legacy-flat package, route SVG/spec/non-bitmaps to project `templates/`, bitmaps to project `images/`, and declared icons to project `icons/`. Do not infer legacy Master/Layout semantics from the flat directory shape.

**Atomic install preflight**:

1. Resolve every source and destination path.
2. Enumerate the complete mapping across `templates/`, `images/`, and `icons/`.
3. Reject every destination collision before writing.
4. Write the accepted mapping once; never use recursive copy as an implicit conflict policy.

If the normalized source root equals the target project root, consume it in place and copy nothing. An in-place workspace cannot be combined with other installed roots. Ignore source `exports/`; it contains review artifacts, not portable template inputs. Empty optional roots remain absent.

**Hard rule — project-local consumer boundary**: After installation,
Default template-aware Strategist work in final Stage 2, Quick's current
agent before direct authoring, and every later role read only
`<project_path>/templates/` and the project-local `images/` / `icons/` pools. The original library or external root
is installation input, not a later prompt source. If source and target are the
same project root, that in-place root already satisfies this boundary.

Template SVGs are authoring prototypes, not export-time overlays. The generated page remains complete in `svg_output/`; `page_layouts` selects the complete prototype and its explicit structure contract for authoring.
Quick instead realizes the selected prototypes into complete flat, Slide-local
SVGs and never writes `page_layouts` or Master/Layout/placeholder metadata.


## 5. Segment Precedence Is Resolved While Reading

Installation copies specs; it never merges them. The consuming role — Default
final Stage 2 through [`strategist-template.md`](../../references/strategist-template.md),
or Quick's current agent before authoring — reads **every** installed
`design_spec.<kind>.<id>.md` and resolves the segments below in context. Asset
collisions are still rejected at install time (§4); segment conflicts are a
reading decision, not a write-time one.

Never reinterpret, predict, or revise the confirmed Stage-1 communication
contract here. Default obtains any additional material conflict decision
through the active chat channel after Stage 1; this does not reopen template
selection. Quick follows explicit conflict instructions; an unresolved material
compatibility conflict is a hard prerequisite handled in chat, never by
launching Confirm UI or by using path order.

### 5.1 Different Kinds

Resolve four whole template segments. This table names the starting owner;
current user instructions and the consuming plan still govern project use:

| Segment | Starting owner |
|---|---|
| Identity | Brand, otherwise Deck, otherwise unresolved until the consuming plan (Default final Stage 2 or Quick active context). Style color/type/icon/image values are direction candidates, never identity truth. |
| Structure | A compatible Layout, otherwise Deck, otherwise unresolved/free design until the consuming plan. Style owns no canvas, prototype, Master/Layout, slot, or page mapping. |
| Reusable application context | Deck only when present. Preserve it for the consuming comparison; it never becomes the current project's application contract. |
| Direction / method | Style when present, otherwise unresolved until the consuming plan. Actual Deck prototypes and Signature facts may inform compatibility, but Deck does not own the Style-only method segment. |

Apply each selected segment wholesale; do not mix its fields implicitly. Brand or Deck identity overrides any identity-adjacent defaults carried by Style. A Style direction may adapt to that resolved identity, but cannot relabel its candidates as official brand facts.

**Hard rule — an owned segment governs visual weight, not only values**: when a
segment owner declares how a value should dominate, recede, or stay rare, that
instruction carries the same authority as the value itself. A Style's
composition or whitespace tendency never demotes a Brand's declared dominant
color to an incidental accent.

Before Layout overrides Deck structure, compare Deck's reusable roles with Layout roles, slots, and capacity. On mismatch, offer exactly three remedies: retain Deck structure, select another Layout, or omit Deck. Default resolves only this template-to-template conflict and must not reinterpret the confirmed Stage-1 communication contract; Quick compares against the current request/content and treats any unresolved material mismatch as a chat hard prerequisite.

Before Style overlays Deck guidance, verify that its method serves Deck's reusable context and fits the selected structure. On mismatch, require omitting Style or choosing a compatible Style/structure; never silently weaken a segment. Default final Stage 2 separately checks the result against the confirmed project contract; Quick checks it against the current request/content before authoring.

Field-level micro-adjustments such as a primary-color override are not a workspace selection. Default carries them into the normal final Stage-2 confirmation fields; Quick treats explicit adjustments as direct active-context authoring constraints.

### 5.2 Same Kind

Several roots of one kind install as separate files distinguished by their
`<id>`, exactly like different kinds. Do not merge them and do not use path
order as priority. The consuming role reads all of them and decides which
governs each part of the owned segment, following the latest explicit user
instruction first; where the user gave none and two same-kind specs make
materially incompatible claims over the same segment, surface the conflict in
chat rather than silently averaging them. Two Style workspaces contend over the
complete Direction / method segment; two Brand workspaces contend over
Identity.

### 5.3 Installed Set

Each installed file keeps its own frontmatter `kind` and `<id>` from its source
workspace; nothing is relabelled. There is no combined capability label and no
merged spec: the installed set is exactly what was selected, and the routing
consequence is derived while reading — structure comes from an installed Layout
or Deck, identity from an installed Brand or Deck, direction from an installed
Style. A project-local Brand + Layout pair does not become a reusable library
Deck; its application remains current-project context.

**Completion receipt**: Report `roots=<normalized roots>; sources=<library|explicit per root>; kinds=<kind per root>; segments=identity:<owner>,structure:<owner>,application_context:<owner>,direction:<owner>; install=<in-place|copied>; installed_specs=<comma-separated design_spec.<kind>.<id>.md>`.

## ✅ Template Workspace Applied

- [x] Every selected input was an index-derived library root or an exact explicit/Create Template root satisfying a listed workspace contract
- [x] Every kind schema passed preflight; structured SVG checks ran only for Layout/Deck inputs
- [x] All destination collisions were rejected before one atomic install; no two source specs were merged into one file
- [x] `<project_path>/templates/` and any portable sibling assets are complete and are the only downstream template source
- [ ] **Next**: Default completes the template-selection handoff and continues [`generate-pptx.md`](../generate-pptx.md) Step 4 Stage 2; Quick returns to [`quick-generate`](../profiles/quick-generate.md) §2
