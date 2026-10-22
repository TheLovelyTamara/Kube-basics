# Kubernetes Basics Lab: Multi-Service Architecture

Welcome to the **Kubernetes Basics Lab**! This repository is an end-to-end, hands-on learning project designed to build a complete cluster of enterprise services and a connected demo application from scratch.

---

## Architecture Overview

```
                                  ┌──────────────────────────────┐
                                  │      Monitoring & Dashboards │
                                  │      - Prometheus (Metrics)  │
                                  │      - Grafana (Visuals)     │
                                  └──────────────▲───────────────┘
                                                 │ scrapes
┌────────────────────────────────────────────────┼────────────────────────────────────────┐
│ Namespace: lab                                 │                                        │
│                                                │                                        │
│                        ┌───────────────────────┴────────────────────────┐               │
│                        │               DEMO APPLICATION                 │               │
│                        │  - Authenticates users against LDAP            │               │
│                        │  - Fetches credentials from HashiCorp Vault    │               │
│                        │  - Queries & writes records to PostgreSQL      │               │
│                        │  - Uploads & retrieves files from MinIO        │               │
│                        └───────┬──────────────┬──────────────┬──────────┘               │
│                                │              │              │                          │
│               ┌────────────────┘              │              └────────────────┐         │
│               ▼                               ▼                               ▼         │
│     ┌──────────────────┐            ┌──────────────────┐            ┌──────────────────┐│
│     │   PostgreSQL     │            │  MinIO (S3 Blob) │            │ HashiCorp Vault  ││
│     │ (Relational DB)  │            │ (Object Storage) │            │ (Secrets Engine) ││
│     └──────────────────┘            └──────────────────┘            └──────────────────┘│
│                                               ▲                                         │
│                                               │                                         │
│                                     ┌─────────┴────────┐                                │
│                                     │  LLDAP / OpenLDAP│                                │
│                                     │(Identity Service)│                                │
│                                     └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Lab Curriculum & Progress

- [x] **Phase 0: Cluster Foundations & Setup** → [`docs/00-kubernetes-foundations.md`](docs/00-kubernetes-foundations.md)
  - `kind` (Kubernetes in Docker/Podman) with CNI & dynamic local storage.
  - Core mental model: Control Plane, Nodes, Pods, Declarative YAML vs Helm.
- [x] **Phase 1: Relational Database (PostgreSQL)** → [`01-postgres/README.md`](01-postgres/README.md)
  - Namespaces, ConfigMaps, Secrets, PVCs, Deployments, Health Probes, ClusterIP Services.
- [x] **Phase 2: Blob Storage (MinIO - S3 Compatible)** → [`02-minio/README.md`](02-minio/README.md)
  - Object storage, multi-port services (API + Web Console), persistent volumes.
- [x] **Phase 3: Directory & Identity (LDAP)** → [`03-ldap/README.md`](03-ldap/README.md)
  - Lightweight LDAP (LLDAP / OpenLDAP), user directory, auth tokens.
- [x] **Phase 4: Secrets Management (HashiCorp Vault)** → [`04-vault/README.md`](04-vault/README.md)
  - Centralized secret engine, dynamic secrets, sidecar injection vs API.
- [x] **Phase 5: The Demo Application** → [`05-app/README.md`](05-app/README.md)
  - Connecting all services together into a working web application.
- [x] **Phase 6: Monitoring & Dashboards (Prometheus + Grafana)** → [`06-monitoring/README.md`](06-monitoring/README.md)
  - Metrics collection, PromQL, Grafana dashboards, Helm charts in practice.
- [x] **Phase 7: Static Web & Backend API Architecture** → [`07-static-web-and-api/README.md`](07-static-web-and-api/README.md)
  - Decoupled SPAs, Nginx reverse proxy, CORS elimination, independent scaling.
- [x] **Phase 8: S3 / Blob Storage Static Web Hosting** → [`08-blob-static-hosting/README.md`](08-blob-static-hosting/README.md)
  - S3 static buckets, Kubernetes Jobs, CloudFront-style edge gateway proxying.

---

## Quick Reference Commands

```bash
# Check cluster nodes
kubectl get nodes -o wide

# Check all lab workloads
kubectl get all,pvc -n lab

# Tail logs of any deployment
kubectl logs -f -n lab deploy/<deployment-name>

# Port-forward a service to localhost
kubectl port-forward -n lab svc/<service-name> <local-port>:<service-port>
```
