# 01 - Relational Database (PostgreSQL)

This section deploys a production-patterned PostgreSQL instance into the `lab` namespace using native Kubernetes primitives.

---

## Architecture of this Component

```
                            [Cluster DNS: postgres-service.lab.svc.cluster.local:5432]
                                                       │
                                                       ▼
                                            ┌─────────────────────┐
                                            │   Service: ClusterIP│
                                            │  (Stable virtual IP)│
                                            └──────────┬──────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Namespace: lab                                                                              │
│                                                                                             │
│  ┌───────────────────────┐         ┌───────────────────────┐                                │
│  │ ConfigMap:            │         │ Secret:               │                                │
│  │ postgres-config       │         │ postgres-secret       │                                │
│  │ - POSTGRES_DB: appdb  │         │ - POSTGRES_USER       │                                │
│  │ - PGDATA              │         │ - POSTGRES_PASSWORD   │                                │
│  └───────────┬───────────┘         └───────────┬───────────┘                                │
│              │                                 │                                            │
│              └───────────────┬─────────────────┘                                            │
│                              ▼                                                              │
│                   ┌───────────────────────┐                                                 │
│                   │      Deployment       │                                                 │
│                   │  postgres-deployment  │                                                 │
│                   │  ┌─────────────────┐  │                                                 │
│                   │  │ Pod (1 replica) │  │                                                 │
│                   │  │ [postgres:16]   │  │                                                 │
│                   │  └────────┬────────┘  │                                                 │
│                   └───────────┼───────────┘                                                 │
│                               │                                                             │
│                               ▼ Mount: /var/lib/postgresql/data                             │
│                   ┌───────────────────────┐                                                 │
│                   │ PersistentVolumeClaim │                                                 │
│                   │ (postgres-pvc: 1Gi)   │                                                 │
│                   └───────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## File Breakdown & Explanations

### 1. `00-namespace.yaml`
Creates the `lab` namespace.
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lab
```
- **Why?** Avoids cluttering the `default` namespace and allows clean deletion of all resources with `kubectl delete namespace lab`.

### 2. `01-configmap.yaml`
Stores non-sensitive key-value pairs (`POSTGRES_DB: "appdb"`, `PGDATA`).
- Injected into the container via `envFrom: - configMapRef: name: postgres-config`.

### 3. `02-secret.yaml`
Stores sensitive credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`).
- `stringData`: Allows cleartext definition in the YAML file; Kubernetes encodes it into base64 upon submission to the API server.
- Injected into the container via `envFrom: - secretRef: name: postgres-secret`.

### 4. `03-pvc.yaml`
Requests 1 Gigabyte of persistent storage with `accessModes: [ReadWriteOnce]`.
- Because our local `kind` cluster has `local-path-storage` installed, this claim is dynamically provisioned and bound immediately.
- If the Pod crashes or is deleted, data written to `/var/lib/postgresql/data` remains safe on disk.

### 5. `04-deployment.yaml`
Declares the desired state for our PostgreSQL Pod:
- **`replicas: 1`**: Ensures 1 pod is always running.
- **`selector` & `labels`**: Key-value pairs (`app: postgres`) that connect the Deployment to the Pods it controls.
- **Probes**:
  - `readinessProbe`: Runs `pg_isready -U admin`. Ensures traffic is only sent to the database once the engine is accepting socket connections.
  - `livenessProbe`: Periodically verifies Postgres is still responding. If deadlocked, K8s restarts it.
- **Resource requests & limits**:
  - Requests: Guaranteed minimum resources (`128Mi` RAM, `100m` CPU = 0.1 cores).
  - Limits: Hard ceiling (`512Mi` RAM, `500m` CPU).

### 6. `05-service.yaml`
Exposes the Pod internally at port `5432`.
- `type: ClusterIP` (default): Only reachable from inside the cluster.
- Other pods in the `lab` namespace connect to hostname: `postgres-service:5432`.

---

## Hands-On Commands & Verification

### Inspecting Resources
```bash
# View all workloads and storage in the lab namespace
kubectl get all,pvc -n lab

# View detailed information and events for the Pod
kubectl describe pod -l app=postgres -n lab
```

### Viewing Logs
```bash
# Follow live logs from the database
kubectl logs -f -n lab deploy/postgres-deployment
```

### Testing SQL via CLI
```bash
# Run a query directly inside the running container
kubectl exec -it -n lab deploy/postgres-deployment -- psql -U admin -d appdb -c "SELECT version();"
```

### Accessing Postgres from your Host Machine
By default, `ClusterIP` services are unreachable from outside the cluster. You can open a secure tunnel using `kubectl port-forward`:
```bash
kubectl port-forward -n lab svc/postgres-service 5432:5432
```
Now you can connect using any desktop client (DBeaver, DataGrip, `psql`) at `localhost:5432` with user `admin` and password `SuperSecurePassword123!`.
