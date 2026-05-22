# ppt169_kubernetes_blueprint - Design Spec

> Capability-showcase deck for the Blueprint / Isometric Technical Drawing direction (P0 in `docs/roadmap.md`). Stress-tests geometric shape generalization and chart-structure extensibility through a Kubernetes cluster architecture walkthrough.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | ppt169_kubernetes_blueprint |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | B) General Consulting + Blueprint / Isometric Technical Drawing |
| **Target Audience** | Engineers / DevOps / SRE / technical decision-makers |
| **Use Case** | Internal technical briefing, training material, engineering whitepaper hero chapter |
| **Created Date** | 2026-05-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 60px left/right, 50px top/bottom |
| **Content Area** | 1160×620 (header 60px, body 510px, footer 50px) |

---

## III. Visual Theme

### Theme Style

- **Style**: Blueprint / Isometric Technical Drawing — engineering schematic on dark blueprint paper, thin cyan line work, isometric 3D projection of components, technical annotation language (dimension lines, arrows, component codes, coordinate grids)
- **Theme**: Dark theme
- **Tone**: Engineering, technical, precise, schematic — speaks the language of an industrial blueprint hung on a wall, not a marketing slide

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0E2A47` | Deep navy blueprint paper |
| **Secondary bg** | `#1A3A5C` | Region / panel backing |
| **Primary** | `#5BA3E0` | Blueprint line color — component frames, connectors, isometric edges |
| **Accent** | `#FFB627` | Single-spot amber — callouts, current state, key path highlight (classic engineering drawing convention) |
| **Secondary accent** | `#3E7AB8` | Line darker tone, secondary borders |
| **Body text** | `#F0F4F8` | Chalk-on-blueprint off-white |
| **Secondary text** | `#A0B8D0` | Sub-annotation, captions |
| **Tertiary text** | `#6B85A3` | Footer / page-number / coordinate labels |
| **Border / grid** | `#2D4A6B` | Blueprint grid (thin gridlines under everything) |
| **Success** | `#7FD99F` | Healthy / Running state |
| **Warning** | `#FF6B6B` | Failed / NotReady / error state |

60-30-10: deep navy background ~60%, cyan line work ~30%, amber accent <10%

### Gradient Scheme

```xml
<!-- Subtle blueprint paper vignette (corner darkening, like an old technical drawing) -->
<radialGradient id="bgVignette" cx="50%" cy="50%" r="75%">
  <stop offset="60%" stop-color="#0E2A47" stop-opacity="0"/>
  <stop offset="100%" stop-color="#000000" stop-opacity="0.35"/>
</radialGradient>

<!-- Amber callout glow -->
<radialGradient id="amberGlow" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="#FFB627" stop-opacity="0.4"/>
  <stop offset="100%" stop-color="#FFB627" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Tech / developer — sans-serif body for readability + monospace for every K8s component name (`kube-apiserver` / `etcd` / `PVC` / `ClusterIP`), mirroring engineering documentation conventions.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | same as Body | — | — |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Arial, "Microsoft YaHei", sans-serif`
- Body: `Arial, "Microsoft YaHei", sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **18px** (dense — many components / labels per page)

| Purpose | Ratio to body | This deck (body=18) | Weight |
| ------- | ------------- | ------------------- | ------ |
| Cover title (hero) | 3.5x | 64px | Bold |
| Chapter / section opener | 2.5x | 45px | Bold |
| Page title | 1.7x | 30px | Bold |
| Hero number | 1.7-2x | 32-36px | Bold |
| Subtitle | 1.3x | 24px | SemiBold |
| **Body** | **1x** | **18px** | Regular |
| Annotation / caption | 0.75x | 13-14px | Regular |
| Coordinate label / footer | 0.6x | 11px | Regular (mono) |

---

## V. Layout Principles

### Page Structure

- **Header area**: 60px — page title + small page-code (`P03 / 10`) in monospace right-aligned
- **Content area**: 510px — central drawing region, often an isometric/blueprint diagram
- **Footer area**: 50px — coordinate-grid origin marker, project code (`K8S-ARCH-2026`), page number

### Layout Pattern Library (this deck uses)

| Pattern | Pages |
| ------- | ----- |
| Single-element isometric centered | P01 (cover), P05 (lifecycle), P08 (HA topology), P09 (comm flow), P10 (closing) |
| Two-plane vertical split (control/data) | P02 |
| Hub-and-spoke (centered apiserver) | P03 |
| Module composition (isometric node anatomy) | P04 |
| Vertical pillars (4 parallel columns) | P06 |
| Layered stack (PV / PVC / StorageClass) | P07 |

### Spacing Specification

| Element | This Project |
| ------- | ------------ |
| Safe margin from canvas edge | 60px (L/R), 50px (T/B) |
| Content block gap | 30px |
| Icon-text gap | 10px |
| Isometric tile depth (3D z-offset) | 12px |
| Grid spacing (background) | 40px (major) / 8px (minor) |
| Annotation leader-line length | 60-120px |
| Component-frame border-radius | 4px (engineering-precise, not soft cards) |

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline` (line-art, matches blueprint line work)
- **Stroke width**: `1.5` (deck-wide)
- **Usage method**: SVG placeholder `<use data-icon="tabler-outline/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Network / cluster | `tabler-outline/network` | P02, P09 |
| Server / API | `tabler-outline/server` | P03 |
| Database / store | `tabler-outline/database` | P03 (etcd) |
| Cog / scheduler | `tabler-outline/settings` | P03 (scheduler) |
| Refresh / controller loop | `tabler-outline/refresh` | P03 (controller-manager) |
| Cloud | `tabler-outline/cloud` | P03 (cloud-controller-manager) |
| Cube / pod | `tabler-outline/cube` | P04, P05 |
| Box / container | `tabler-outline/box` | P04 |
| Route / proxy | `tabler-outline/route` | P04, P06 |
| Heartbeat / lifecycle | `tabler-outline/heartbeat` | P05 |
| Plug / service | `tabler-outline/plug` | P06 |
| Disk / storage | `tabler-outline/device-floppy` | P07 |
| Stack / layered | `tabler-outline/stack` | P02, P07 |
| Shield / health | `tabler-outline/shield-check` | P08 |
| Send / arrow | `tabler-outline/arrow-right` | universal |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P03 | hub_spoke | `templates/charts/hub_spoke.svg` | "Pick for 1 core capability + 4-8 surrounding capabilities (platform/ecosystem); each spoke = title or title + 1-2 line description. Skip if" | kube-apiserver as central hub + 4 other control-plane components as spokes — captures the architectural truth that "everything goes through apiserver" |
| P05 | process_flow | `templates/charts/process_flow.svg` | "Pick for 3-8 sequential steps connected by simple arrows — approval workflows, customer onboarding, request handling, lifecycle stages. Skip" | Pod lifecycle phases Pending → Running → Succeeded / Failed (with Unknown branch) |
| P06 | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic" | 4 Service types as parallel pillars: ClusterIP / NodePort / LoadBalancer / ExternalName |
| P09 | client_server_flow | `templates/charts/client_server_flow.svg` | "Pick for left-side clients + right-side servers with labeled bidirectional arrows for key interactions (request/response/push). Each module" | Components on the left + kube-apiserver center + etcd right, with labeled watch/write arrows |

**Runners-up considered**:

- `hub_inward_arrows` | rejected for P03: that template is for "forces pointing inward" (Porter's Five Forces). Apiserver is a hub all roads pass *through*, not a target of inward pressure — `hub_spoke` reads truer.
- `numbered_steps` | rejected for P05: pod lifecycle is not a fixed sequence; it has a fork (Succeeded vs Failed) and a re-entry path (restart). `process_flow` handles branching arrows; `numbered_steps` forces a single chain.
- `comparison_table` | rejected for P06: Service types vary along too many independent axes (scope / port range / external requirement / use case). A pillars layout lets each type carry its own structure without forcing parallel rows.
- `layered_architecture` | rejected for P02 (P02 is free design): the catalog template is too card-heavy for the blueprint aesthetic — re-implementing the two-plane split as a custom isometric diagram is exactly the capability this deck demonstrates.

---

## VIII. Image Resource List

**No images.** This deck is intentionally all-SVG / all-vector — every architectural diagram is a hand-drawn isometric blueprint. Mixing raster AI images would dilute the stress-test of geometric shape generalization that the Blueprint direction is meant to demonstrate.

---

## IX. Content Outline

### Part 1: Setting the frame

#### Slide 01 — Cover

- **Layout**: Single isometric hero — a stylized cluster of cube-stacks rendered in cyan line art, centered, with title overlay
- **Title**: `Kubernetes Cluster Architecture`
- **Subtitle**: `A Blueprint of the Modern Container Orchestrator`
- **Meta**: `K8S-ARCH-2026 · DRAWING 01 OF 10 · ENGINEERING REFERENCE`

#### Slide 02 — Two planes: control vs data

- **Layout**: Vertical split — top half = control plane (5 component glyphs in a row), bottom half = data plane (3 worker-node isometric blocks), connected by a single labeled spine
- **Title**: `Two Planes, One Spine`
- **Content**:
  - Control plane → global decisions, desired-state holder
  - Data plane → workload execution (Pods)
  - `kube-apiserver` is the only link — every line crosses through it

### Part 2: Component anatomy

#### Slide 03 — Control plane components

- **Layout**: Hub-and-spoke; `kube-apiserver` at the hub with `etcd` adjacent (the only direct talker); `kube-scheduler` / `kube-controller-manager` / `cloud-controller-manager` as spokes
- **Visualization**: hub_spoke (adapted)
- **Title**: `The Control Plane: 5 Components`
- **Content**: one-line role for each component, mono code label per component

#### Slide 04 — Worker node anatomy

- **Layout**: Isometric exploded-view of a single worker node — outer shell labeled, kubelet/kube-proxy/runtime as inner modules, Pods stacked as cubes inside the runtime
- **Title**: `Worker Node: Three Layers`
- **Content**:
  - `kubelet` — agent reconciling PodSpecs against the local node
  - `kube-proxy` — Service rules via iptables / IPVS / nftables
  - Container runtime — `containerd` / `CRI-O` over the CRI contract

### Part 3: Lifecycle and networking

#### Slide 05 — Pod lifecycle phases

- **Layout**: Horizontal process flow; 4 phase nodes + 1 Unknown branch; restart loop callout
- **Visualization**: process_flow (adapted)
- **Title**: `Pod Lifecycle: One Schedule, Many States`
- **Content**: `Pending → Running → {Succeeded | Failed}`; Unknown branch when node unreachable; restart policy `Always` / `OnFailure` / `Never`

#### Slide 06 — Service networking: 4 types

- **Layout**: 4 parallel pillars, each pillar an isometric tower showing what gets exposed where
- **Visualization**: vertical_pillars (adapted)
- **Title**: `Services: Four Ways to Be Reachable`
- **Content**: ClusterIP (internal) / NodePort (30000-32767 on every node) / LoadBalancer (cloud LB) / ExternalName (DNS CNAME)

### Part 4: Persistence and topology

#### Slide 07 — Storage: three resources

- **Layout**: Layered stack — top: Pod, mid: PVC, bottom: PV; right side: StorageClass + CSI driver as the provisioner spine
- **Title**: `Storage: PV / PVC / StorageClass`
- **Content**: Static vs dynamic provisioning; access modes `RWO` / `ROX` / `RWX` / `RWOP`; reclaim `Retain` / `Delete`

#### Slide 08 — HA topology: stacked vs external etcd

- **Layout**: Two isometric diagrams side by side — left: stacked (etcd co-located with control-plane host); right: external (etcd on dedicated hosts) — each annotated with trade-offs
- **Title**: `HA Topology: Stacked or External`
- **Content**: ≥3 hosts; odd-numbered etcd members (3 or 5); leader-elected scheduler / controller-manager

### Part 5: The spine + closing

#### Slide 09 — Everything-through-apiserver

- **Layout**: client_server_flow — clients (kubectl / kubelet / scheduler / controller-manager) on the left, kube-apiserver center, etcd on the right; labeled arrows
- **Visualization**: client_server_flow (adapted)
- **Title**: `Every Line Crosses the API Server`
- **Content**: API-mediated state transitions enable plug-ability, observability, audit

#### Slide 10 — Takeaways

- **Layout**: Negative-space-driven, three condensed lines centered against the blueprint grid
- **Title**: `Three Things to Remember`
- **Content**:
  - One spine — `kube-apiserver` mediates every state change
  - One truth — `etcd` is the only persistent store
  - One reconcile loop — controllers watch, diff, act; everything else is a variation

---

## X. Speaker Notes Requirements

- **Filename**: match SVG name (`01_cover.svg` → `notes/01_cover.md`)
- **Total duration target**: ~12 minutes (1-1.5 min per content page; cover/closing shorter)
- **Notes style**: Technical / informative — speaker is a senior engineer walking a peer audience through architecture; avoid marketing tone

---

## XI. Technical Constraints Reminder

Standard PPT Master SVG constraints (see `references/shared-standards.md`). Key reminders for this deck:

1. Every isometric line drawing is hand-authored SVG — `<polygon>` / `<line>` / `<path>` primitives; no raster fallback
2. The blueprint grid background is a `<pattern>` ref'd by `<rect>` (allowed) — not `class` / `<style>`
3. `<g opacity>` forbidden; set opacity per child
4. All transparency via `stop-opacity` / `fill-opacity`; no `rgba()`
5. Component codes (`kube-apiserver`, `etcd`, `PVC`, etc.) MUST use `font-family="Consolas, 'Courier New', monospace"` for the mono visual contract
6. Coordinate labels in footer use the same mono family — engineering-document texture
