> Default Generate also loads [`executor-base.md`](./executor-base.md); Quick loads this branch with its own §2 anchors.

# Executor Image Branch

Conditional Executor authority for image status handling, placement, crop behavior, and template-bundled images.

**Trigger**: any image in §VIII, the lock, Quick's active-context resource decisions, or a selected template.

**Contract — status handling** (enum and lifecycle in [`svg-image-embedding.md`](svg-image-embedding.md), reference syntax there too). Executor consumes only prepared assets; derivatives already exist and native treatments are SVG work.

| Status | Handling |
|---|---|
| `Existing` (user-provided) | Reference from `../images/` |
| `Generated` (Image_Generator) | Reference from `../images/`; a manifest-backed file also loads [`executor-web-image.md`](./executor-web-image.md) |
| `Sourced` (Image_Searcher) | Reference from `../images/`; read `image_sources.json` for attribution — load [`executor-web-image.md`](./executor-web-image.md) |
| `Needs-Manual` | Default uses a placeholder until Step 7; Quick blocks every required row, file presence notwithstanding |
| `Placeholder` | Dashed `<rect stroke-dasharray="8,4" …/>` plus description text |

**Template-bundled images**: [`apply-template-workspace.md`](../workflows/stages/apply-template-workspace.md) copies them into project `images/`; every page, including `mirror`, rebases the same bytes to exact `../images/<name>` (a transport rewrite, not a visual edit). Never keep a bare or source-template href.

**Contract — crop policy**: read the §VIII row and its lock projection (`source`, `crop`). On every slide that uses a `crop=no-crop` source (or legacy `| no-crop`), keep one visible complete instance with one of the nine legal `meet` anchors — never `none`, `clip-path`, `mask`, overflow clipping, or a nested crop viewport; an auxiliary same-slide detail or lens may crop the source only while that instance stays visible. `crop=adaptive` permits cropping without requiring it: choose `meet` or a focal-safe `slice` from purpose, ratio, focus, and container. A missing or conflicting projection returns upstream; the §VIII `Layout pattern` is a Reference — a starting sketch adjusted freely unless labeled `(binding)`.

**Hard rule — same-source addressable crops, only when adopted**: no layout suggestion (including `#M1-11`) activates this transport, and `#M1-09` is a deliberate-offset treatment with no registered or Morph continuity. Use it only when independent crops must preserve one exact scene map or an explicit editable/Morph requirement needs them: reuse one exact `href` without slice assets, give every independent object a stable page-unique id and its own nested crop wrapper ([`svg-effects.md`](./svg-effects.md) §6.5) — plain rectangles need no crop marker; shaped frames put `data-pptx-crop="1"` on the wrapper and a matching `userSpaceOnUse` clip on the inner `<image>` — and derive every wrapper `viewBox` from one shared source-to-page transform over the union of the visible containers, so different container positions change the source-unit `x`, `y`, `width`, `height` by the same mapping and gaps remove pixels without rescaling. Repeated crops or SVG/PPT drift fail. A compound clip on one `<image>` is `#M1-10`, not a substitute when the objects must stay independently editable or Morphable.

**Hard rule — visible-layer timing**: every crop, lens, scrim, comparison, evidence, or annotation layer an adopted motion plan needs already exists in the final SVG; the motion stage may regroup ordinary Slide-local content but never invents or modifies visible content. When no legal unit can serve a non-binding suggestion, simplify to available units, a page transition, or `none`; an unrepresentable explicit requirement follows failure recovery.

**Hard rule — narrow visual-inspection scope**: start from §VIII `Reference` plus dimensions; inspect one asset (or its review copy) once only when focal-safe crop, overlay contrast, a quiet region, or the planned subject relationship stays ambiguous — a `Generated` asset only when its intent and dimensions cannot resolve the ambiguity, never routinely. Inspection never reopens selection, changes identity or must-use, infers provenance, substitutes, or invents focus; uncertain `adaptive` focus uses `meet`, and conflicting binding constraints return upstream.

## 1. Image Composition

**Mandatory — per-page image composition decision**: on every page with an image, once, immediately before geometry, in active context only: `role → direction generator → parent contour → slots/rhythm → crop → image-shape action → labels/overlays → depth/continuity`, derived from the communication job, hierarchy, copy, asset ratio/focus, and deck rhythm, using `anchor`, `continue`, `bridge`, `overlap`, `reveal`, `echo`, or `register` only when useful. Compare the candidate with plain / `P`-only placement and implement the stronger legal composition; no artifact, no extra pass, no rereading the branch while the context is valid.

**Default — active image integration (may override when plain placement is stronger)**: [`image-layout-patterns.md`](./image-layout-patterns.md) is vocabulary and [`image-layout-spec.md`](./image-layout-spec.md) is math, neither a quota nor a lock; a `#P…` suggestion is a skeleton to deepen, simplify, or combine through [`svg-effects.md`](./svg-effects.md) and [`native-shape-authoring.md`](./native-shape-authoring.md). Preserve role/source, must-use, crop/content, and explicit constraints; expression-only changes need no upstream rewrite.

**Default — preserve the image job at final size (may override when the planned job is texture only)**: before accepting a narrow band, small placement, or crop, keep the subject or relationship named by the image purpose recognizable at its on-slide size; if it collapses into color texture, enlarge or recompose, and treat it as texture only when the upstream job permits.

**Default — one direction generator per image group (may override when deliberate disorder serves the job)**: derive slot positions, crop edges, overlap, and any rotation from one generator; varied angles need a declared rhythm or collision rule.

| Generator | Behavior |
|---|---|
| `vector` | Progress slots along one shared movement vector |
| `shared-baseline` | Share a baseline while size, offset, or overlap changes systematically |
| `curve-spine` | Derive slots and turns from one continuous curve or folded path |
| `panel` | Subdivide one coherent tilted, stepped, or polygonal parent panel |
| `none/grid` | Calm plain placement or a regular grid |

**Reference — motion-ready layering**: for an adopted §IX or explicit focus, comparison, evidence, reveal-order, or cross-page requirement, decide during authoring whether the composition needs separate visible units — stable framing stays static, each independently revealed or continuing Slide-local unit gets a descriptive direct-root `<g id>`, structured atoms and slots keep their boundaries; existing units or a page transition may suffice. The motion stage owns effects, pairing, order, and timing.
