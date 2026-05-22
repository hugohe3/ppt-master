# Kubernetes Cluster Architecture

> Research document for the Blueprint / Isometric capability-showcase deck. Source material gathered from `kubernetes.io` official documentation (2026-05). Concrete facts only; the Strategist composes the final slide copy.

## 1. Cluster topology overview

A Kubernetes cluster is a two-plane system:

- **Control plane** — global decision-making. Schedules workloads, reacts to events, holds the desired-state of every API object.
- **Data plane (worker nodes)** — runs the actual application Pods. One or more nodes; production HA clusters spread the control plane and etcd across ≥3 nodes and across availability zones.

Minimum cluster = 1 control-plane host + 1 worker node. Production = ≥3 control-plane hosts, ≥3 etcd members (odd numbers for quorum), worker pool sized by workload.

All components communicate through **kube-apiserver** — the only component that talks to etcd. Every read/write of cluster state goes through the API server. This is the architectural spine.

## 2. Control plane components

Five components run the control plane:

### 2.1 kube-apiserver
- Front-end of the cluster; exposes the Kubernetes HTTP API
- The **only** component that talks to etcd directly
- Horizontally scalable — multiple `kube-apiserver` instances behind a load balancer
- Validates and admits requests, runs admission controllers, then persists to etcd

### 2.2 etcd
- Distributed, consistent, highly-available key-value store
- Holds **all** cluster state (API objects, config, secrets)
- Raft consensus protocol; needs an odd number of members (typically 3 or 5)
- Backup is operationally critical — losing etcd loses the cluster
- HA topologies: stacked (etcd co-located with control-plane host) vs. external etcd

### 2.3 kube-scheduler
- Watches the API server for Pods with no `nodeName` assigned
- Picks a node for each unscheduled Pod based on:
  - Resource requests (CPU / memory / GPU)
  - Hardware / software / policy constraints
  - Affinity & anti-affinity rules
  - Taints & tolerations
  - Topology spread, data locality, inter-workload interference
- Two-phase pipeline: **filtering** (which nodes are feasible?) → **scoring** (which feasible node is best?)
- Writes the binding decision back to the API server — does not directly talk to the node

### 2.4 kube-controller-manager
- One binary, many logically separate controllers; each runs a `watch → diff desired-vs-actual → act` reconcile loop
- Core controllers:
  - **Node controller** — detects and responds to node failures
  - **Job controller** — creates Pods to drive Job objects to completion
  - **EndpointSlice controller** — maps Services to Pod IPs
  - **ServiceAccount controller** — creates default ServiceAccounts in new namespaces
  - **ReplicaSet / Deployment / StatefulSet / DaemonSet controllers** — workload primitives
- Leader-elected for HA: only one replica is active at a time

### 2.5 cloud-controller-manager (optional)
- Only on cloud-hosted clusters; absent in on-premises / bare-metal / local environments
- Embeds cloud-vendor-specific control logic so the core Kubernetes binary stays vendor-neutral
- Sub-controllers:
  - **Node controller** — confirms whether deleted nodes really were deleted at the cloud provider
  - **Route controller** — sets up cloud routes between nodes
  - **Service controller** — creates / updates / deletes cloud load balancers for Services of type `LoadBalancer`

## 3. Worker node components

Three components run on every worker node:

### 3.1 kubelet
- The node-level agent
- Watches the API server for Pods scheduled to its node
- Takes PodSpecs, instructs the container runtime to start the containers, supervises health via probes
- Reports node and Pod status back through the API server
- Reconciles continuously — if a container dies, kubelet restarts per `restartPolicy` (`Always` / `OnFailure` / `Never`)
- Heartbeats via Lease objects in the `kube-node-lease` namespace

### 3.2 kube-proxy (optional)
- Implements the Kubernetes **Service** abstraction at the node level
- Maintains network rules that translate the Service virtual IP into a backing Pod IP
- Implementation backends:
  - `iptables` (default) — netfilter rules, lower CPU overhead
  - `IPVS` — kernel L4 load balancer, better at very large Service counts
  - `nftables` — modern netfilter framework (newer clusters)
  - `userspace` — legacy, slower, deprecated
- Optional: a CNI plugin (Cilium, Calico-eBPF) can replace kube-proxy entirely

### 3.3 Container runtime
- Actually runs the containers
- CRI (Container Runtime Interface) standardizes the contract between kubelet and the runtime
- Supported runtimes: **containerd**, **CRI-O**, any CRI-conformant implementation
- Docker Engine removed as a built-in runtime (since v1.24)

## 4. Pod lifecycle

A Pod is the smallest deployable unit — one or more containers sharing a network namespace and storage volumes.

**Phases** (set by the control plane):

| Phase | Meaning |
|---|---|
| `Pending` | Accepted; not all containers running yet (waiting on scheduling, image pull, etc.) |
| `Running` | Bound to a node; ≥1 container is starting / running / restarting |
| `Succeeded` | All containers exited 0; will not restart |
| `Failed` | All containers exited; ≥1 with non-zero status |
| `Unknown` | API server cannot reach the node holding the Pod |

**Container states**: `Waiting` / `Running` / `Terminated` (each container in the Pod is tracked independently)

**Probes** (kubelet runs them):
- `livenessProbe` — fail ⇒ kubelet restarts the container
- `readinessProbe` — fail ⇒ kubelet removes Pod from Service endpoints (no restart)
- `startupProbe` — gates the other two until the application has finished initializing
- Probe methods: `exec` (run command) / `httpGet` / `tcpSocket` / `grpc`

**Termination flow** (graceful, default 30s):
1. API server marks the Pod for deletion
2. `preStop` hook (if defined) runs in the container
3. `SIGTERM` to the container main process
4. Up to `terminationGracePeriodSeconds` to exit cleanly
5. `SIGKILL` if still alive

A Pod is scheduled **once** in its lifetime. Failed Pods are replaced (by their controller — Deployment / StatefulSet / Job — with a new UID), not rescheduled.

## 5. Service networking

A Service gives a stable virtual IP and DNS name in front of an ever-changing set of Pods.

**Service types**:

| Type | Where reachable | How |
|---|---|---|
| `ClusterIP` (default) | Inside the cluster only | Virtual IP in the Service CIDR; kube-proxy programs the iptables/IPVS rules |
| `NodePort` | Any node's IP at a static port (30000–32767) | NodePort opens on every node; routes to the ClusterIP |
| `LoadBalancer` | External cloud LB | cloud-controller-manager provisions the LB; targets the NodePort |
| `ExternalName` | DNS CNAME | API server returns a CNAME record; no proxying |

**EndpointSlices** (replaced the older `Endpoints` resource in v1.21): track the Pod IPs backing a Service. Controller continuously rebuilds the slice as Pods come and go.

**DNS**: every Service is resolvable at `<svc>.<namespace>.svc.cluster.local`. Cluster DNS (CoreDNS) is a mandatory addon.

**Headless Service** (`clusterIP: None`): returns Pod IPs directly via DNS A records, no virtual IP — used by StatefulSets so each replica gets its own resolvable name.

## 6. Storage

Persistent storage in Kubernetes is split across three resources:

- **PersistentVolume (PV)** — a piece of provisioned storage; cluster-scoped resource with its own lifecycle
- **PersistentVolumeClaim (PVC)** — a Pod's request for storage; namespaced
- **StorageClass** — an admin-defined recipe for dynamically provisioning PVs on demand

**Access modes**:

| Mode | Meaning |
|---|---|
| `ReadWriteOnce` (RWO) | Mountable read-write on a single node |
| `ReadOnlyMany` (ROX) | Mountable read-only on many nodes |
| `ReadWriteMany` (RWX) | Mountable read-write on many nodes |
| `ReadWriteOncePod` (RWOP) | Mountable read-write by a single Pod |

**Reclaim policies** (what happens when the PVC is deleted): `Retain` / `Delete` / `Recycle` (deprecated).

**CSI (Container Storage Interface)** is the modern plugin contract — every storage backend (cloud block storage, NFS, Ceph, etc.) ships a CSI driver, the in-tree plugins are deprecated.

**Volume modes**: `Filesystem` (default — mounted as a directory) vs. `Block` (raw block device).

## 7. High availability and topology

For production:

- **Control plane** — ≥3 control-plane hosts, kube-apiserver load-balanced, kube-scheduler and kube-controller-manager leader-elected
- **etcd** — ≥3 members across hosts; **odd number** for quorum (3 or 5)
- **Multi-zone** — spread control-plane hosts and worker nodes across availability zones; lose one zone, the cluster keeps going
- **Two topologies** for control plane:
  - **Stacked** — each control-plane host runs an etcd member alongside kube-apiserver (simpler, less HW)
  - **External etcd** — etcd cluster on dedicated hosts (better failure isolation, more HW)

## 8. Self-healing and observability

What Kubernetes recovers from automatically:

- Container crash → kubelet restarts per `restartPolicy` with exponential backoff (100ms → 5min cap, resets after 10min healthy)
- Pod failure → controller (Deployment / ReplicaSet / StatefulSet) creates a new Pod
- Node failure → node controller marks the node `NotReady`; after `pod-eviction-timeout` (default 5min) Pods on it are marked for deletion, controllers replace them on other nodes
- Workload imbalance → kube-scheduler places the new Pods on under-loaded nodes

What it does **not** recover from:

- Lost etcd quorum — cluster state is gone, manual restore from backup required
- Lost API server — no new decisions possible, existing workloads keep running on their nodes until kubelet hits its watch timeout

**Observability addons** (universal in production):

- **DNS** (CoreDNS) — required; cluster DNS resolution
- **Metrics** — metrics-server + Prometheus
- **Logs** — Fluent Bit / Fluentd → central store (Loki, Elasticsearch, cloud log services)
- **Dashboard** — optional web UI

## 9. Component communication summary

The traffic pattern is simple:

```
kubectl / clients ──HTTPS──► kube-apiserver ◄──gRPC──► etcd
                                    ▲
                                    │ watch / report
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
kube-scheduler          kube-controller-manager       cloud-controller-manager
                                    │
                                    │ watch
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
   kubelet (node 1)           kubelet (node 2)            kubelet (node N)
        │                           │                           │
        ▼                           ▼                           ▼
container runtime          container runtime           container runtime
   + kube-proxy               + kube-proxy                + kube-proxy
```

Every line is API-server-mediated. No component talks directly to another except via the API server (and only the API server talks to etcd). This is what makes Kubernetes pluggable and observable — every state transition is an API event.

## Sources

- [Cluster Architecture | Kubernetes](https://kubernetes.io/docs/concepts/architecture/)
- [Kubernetes Components | Kubernetes](https://kubernetes.io/docs/concepts/overview/components/)
- [Service | Kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Pod Lifecycle | Kubernetes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Persistent Volumes | Kubernetes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
