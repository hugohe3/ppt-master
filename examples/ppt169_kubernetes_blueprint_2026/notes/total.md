# 01_cover

Welcome to this engineering walkthrough of Kubernetes cluster architecture. Over the next ten drawings, we will read the system the way an engineer reads a blueprint: starting from the topology overview, going inside each component, then watching the whole thing operate. Every diagram is drawn as an isometric schematic rather than a marketing illustration, because the point is to see the structure, not the brand.

---

# 02_two_planes

The first thing to internalize about Kubernetes is that it has two planes, not one. The control plane makes global decisions and holds the desired state of every API object. The data plane runs the actual workloads, one or more worker nodes carrying the Pods. The spine connecting them is the API server, and every line that crosses from one plane to the other must pass through it. Hold that picture in your head — every later drawing is a zoom into one part of it.

---

# 03_control_plane

The control plane is five components arranged around one hub. At the center sits kube-apiserver, the only component allowed to talk to etcd, the persistent key-value store on its left. Around the apiserver three reconciliation loops listen and act: the scheduler picks a node for every unscheduled Pod, the controller-manager runs the workload controllers, and the optional cloud-controller-manager translates cluster intent into cloud-provider primitives like load balancers and routes. Notice that every spoke watches the apiserver — none of them call each other directly.

---

# 04_worker_node

Now we drop into a single worker node. Three layers stack inside it. At the top, the kubelet acts as the node-level agent — it watches the apiserver for Pods scheduled to this node and instructs the runtime to make those Pods real. Below it, kube-proxy programs the network rules so that Service virtual IPs route to the correct backing Pods, using iptables, IPVS, or nftables depending on configuration. At the base, the container runtime — containerd or CRI-O — actually starts the containers through the CRI interface. The green cubes inside are the Pods, the smallest unit you can schedule.

---

# 05_pod_lifecycle

A Pod is scheduled exactly once in its lifetime. It begins in the Pending phase while the scheduler binds it to a node and the runtime pulls images. Once at least one container is live, the phase becomes Running, the highlighted middle box of this diagram. From Running there are two terminal exits: Succeeded if every container exited cleanly, Failed if any exited with a non-zero status. A third branch, Unknown, appears when the apiserver loses contact with the node. Below the phases, the container-state track shows the per-container view: Waiting, Running, Terminated, with the restart policy controlling how kubelet handles failures, backed by exponential backoff up to five minutes.

---

# 06_service_types

A Service gives you a stable virtual endpoint in front of an ever-changing set of Pods. Four pillars, ordered from internal to external reach. ClusterIP is the default and the most common — internal only, virtual IP only, kube-proxy translates it. NodePort opens a static port on every node in the thirty-thousand range, useful when there is no cloud load balancer available. LoadBalancer, the highlighted production pattern, asks the cloud-controller-manager to provision a real external load balancer with a public IP. ExternalName is the edge case — no proxying, just a DNS CNAME alias pointing at something outside the cluster, typically used as a migration shim or to model an external database as a Kubernetes Service.

---

# 07_storage

Persistent storage in Kubernetes is a three-resource contract. On the left stack, the Pod claims storage by naming a PersistentVolumeClaim, the PVC requests size and access mode, and the PersistentVolume represents a concrete backing disk — a cloud volume, an NFS share, or any storage backend. On the right side, the admin defines a StorageClass — a recipe — and a CSI driver implements it. When dynamic provisioning is enabled, a PVC request triggers the StorageClass to create a fresh PV on demand. The access modes ReadWriteOnce, ReadOnlyMany, ReadWriteMany, and ReadWriteOncePod control how many nodes or Pods can mount the volume, and the reclaim policy decides what happens to the data when the PVC is deleted.

---

# 08_ha_topology

Production clusters need at least three control-plane hosts and an odd number of etcd members for Raft quorum. Two topologies are common. On the left, stacked: etcd runs on the same host as the apiserver, simpler to operate and cheaper, at the cost of weaker failure isolation — losing one host loses one apiserver and one etcd member at the same time. On the right, the recommended external topology: etcd runs on dedicated hosts in its own tier, so the storage layer can survive apiserver pressure independently. Scheduler and controller-manager are leader-elected in either topology, which is why running three replicas is safe.

---

# 09_api_spine

This is the punchline drawing. Every component on the left — kubectl clients, the scheduler, the controller-manager, every kubelet on every node, kube-proxy, and the cloud-controller-manager — talks to one component in the middle, kube-apiserver. On the right, the apiserver is the only thing that writes to etcd, the cluster's sole persistent store. The arrows in green going back left are status reports and decisions; the arrows in cyan going right are watches and patches. This pattern — everything is API-mediated — is what makes Kubernetes pluggable, observable, and auditable. You can join the cluster by writing a controller that watches the API, and everything else falls into place.

---

# 10_takeaways

If you remember three things from this walkthrough, take these. First, one spine — kube-apiserver mediates every state change; no component talks to another directly, and that constraint is the architecture. Second, one truth — etcd is the only persistent store; back it up, run an odd number, and Raft handles the rest. Third, one loop — every controller in Kubernetes is the same shape: watch the API for desired state, diff it against actual state, act to converge. Once you see that loop, you can read the source of any controller in the ecosystem, because they are all variations on it.
