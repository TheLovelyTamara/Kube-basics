# Kubernetes Foundations & Core Concepts

## 1. What is Kubernetes?
Kubernetes (often abbreviated as **K8s**—"K" followed by 8 letters, then "s") is an open-source container orchestration engine. It automates:
- Deploying containerized applications
- Scaling them up or down on demand
- Self-healing (restarting failed containers, replacing dead nodes)
- Load balancing and service discovery
- Managing configuration, secrets, and persistent storage

---

## 2. Cluster Architecture

A Kubernetes cluster is divided into two primary zones:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE ("The Brain")                       │
│                                                                        │
│   ┌────────────────────┐   ┌───────────────────┐   ┌───────────────┐   │
│   │   kube-apiserver   │   │  kube-scheduler   │   │  Controller   │   │
│   │ (REST API Gateway) │   │ (Assigns to Nodes)│   │    Manager    │   │
│   └─────────┬──────────┘   └───────────────────┘   └───────────────┘   │
│             │                                                          │
│   ┌─────────▼──────────┐                                               │
│   │        etcd        │                                               │
│   │(Key-Value Database)│                                               │
│   └────────────────────┘                                               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       │                                                         │
┌──────▼─────────────────────────┐        ┌──────────────────────▼─────────────────────────┐
│     WORKER NODE 1              │        │     WORKER NODE 2                              │
│                                │        │                                                │
│  ┌──────────────┐ ┌──────────┐ │        │  ┌──────────────┐ ┌──────────┐                 │
│  │   kubelet    │ │kube-proxy│ │        │  │   kubelet    │ │kube-proxy│                 │
│  └──────┬───────┘ └──────────┘ │        │  └──────┬───────┘ └──────────┘                 │
│         │                      │        │         │                                      │
│  ┌──────▼────────────────────┐ │        │  ┌──────▼────────────────────┐                 │
│  │ Container Runtime         │ │        │  │ Container Runtime         │                 │
│  │ (containerd / CRI-O)      │ │        │  │ (containerd / CRI-O)      │                 │
│  │  ┌──────────┐┌──────────┐ │ │        │  │  ┌──────────┐┌──────────┐ │                 │
│  │  │  Pod A   ││  Pod B   │ │ │        │  │  │  Pod C   ││  Pod D   │ │                 │
│  │  └──────────┘└──────────┘ │ │        │  │  └──────────┘└──────────┘ │                 │
│  └───────────────────────────┘ │        │  └───────────────────────────┘                 │
└────────────────────────────────┘        └────────────────────────────────────────────────┘
```

### Control Plane Components:
1. **`kube-apiserver`**: The front door to the cluster. All internal components and external CLI tools (`kubectl`) communicate strictly via this REST API.
2. **`etcd`**: A highly consistent, distributed key-value store. This is the single source of truth for the entire cluster's configuration and current state.
3. **`kube-scheduler`**: Watches for newly created Pods that have no Node assigned, and selects the healthiest, best-fitting Node based on resource requests (CPU, RAM).
4. **`kube-controller-manager`**: Runs background controller loops that compare the **actual state** with the **desired state** (e.g. if 3 replicas are desired and 1 crashes, it orders a new pod).

### Node Components:
1. **`kubelet`**: The node agent that communicates with the control plane and ensures the containers described in PodSpecs are actually running and healthy.
2. **`kube-proxy`**: Manages network rules on nodes. Handles TCP/UDP traffic forwarding and load-balancing for `Services`.
3. **Container Runtime**: The software responsible for downloading images and running containers (in modern K8s, usually `containerd` or `CRI-O`).

---

## 3. Core Objects / Primitives

| Object | Purpose | Analogy |
| :--- | :--- | :--- |
| **Pod** | Smallest deployable unit; one or more containers sharing network and storage. | A pea pod holding peas (containers). |
| **Namespace** | Logical partition inside a single physical cluster. | Different folders or tenants on a drive. |
| **Deployment** | Manages declarative updates for Pods (scaling, rolling updates, self-healing). | A fleet manager keeping N trucks on the road. |
| **Service** | Stable IP address and DNS name that routes traffic across a set of Pods. | A receptionist directing calls to available operators. |
| **ConfigMap** | Injects plain-text configuration files and environment variables into Pods. | A `.env` or `config.json` file. |
| **Secret** | Injects sensitive credentials (passwords, tokens, SSH keys). | A protected credential manager. |
| **PersistentVolumeClaim (PVC)** | Requests persistent disk storage independent of the Pod's lifecycle. | A storage lease ticket. |

---

## 4. Raw Manifests vs. Helm Charts

### Raw Manifests (Native Kubernetes)
- Static YAML files describing resources (`apiVersion`, `kind`, `metadata`, `spec`).
- Applied directly with `kubectl apply -f <file.yaml>`.
- **Pros:** No extra layers, 100% transparent, great for understanding fundamentals.
- **Cons:** Hardcoded values; duplicating configs for dev/staging/prod leads to copy-paste drift.

### Helm Charts
- A **package manager** and **templating engine** for Kubernetes.
- Combines Go templates (`templates/*.yaml`) with variable definitions (`values.yaml`).
- Commands: `helm install <release-name> <chart-dir>`, `helm upgrade`, `helm rollback`.
- **Pros:** Reusable across environments, versioned packages, community ecosystem (Artifact Hub).
- **Cons:** Extra complexity; templating errors can be hard to decipher if you don't already understand raw YAML.
