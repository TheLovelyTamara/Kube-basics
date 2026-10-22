# 05 - The Demo Application (Connected Microservice Portal)

This section deploys our custom multi-service portal that unifies and exercises all four backend services in real time.

---

## How It Integrates the Cluster

```
                            [User Browser: http://localhost:8000]
                                              │
                                              ▼
                                 ┌───────────────────────────┐
                                 │ Service: demo-app-service │
                                 │   (Round-robin balancing) │
                                 └─────────────┬─────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
             ┌─────────────────────┐                       ┌─────────────────────┐
             │ Pod: demo-app (rep1)│                       │ Pod: demo-app (rep2)│
             └──────────┬──────────┘                       └──────────┬──────────┘
                        │                                             │
      ┌─────────────────┼──────────────────────┬──────────────────────┤
      │                 │                      │                      │
      ▼                 ▼                      ▼                      ▼
┌───────────┐     ┌───────────┐          ┌───────────┐          ┌───────────┐
│PostgreSQL │     │   MinIO   │          │   Vault   │          │   LLDAP   │
│(:5432)    │     │ (:9000)   │          │ (:8200)   │          │ (:3890)   │
└───────────┘     └───────────┘          └───────────┘          └───────────┘
```

### 1. Internal DNS Service Discovery
In traditional infrastructure, you often have to configure hardcoded IP addresses. In Kubernetes, **CoreDNS** automatically resolves service names:
- `postgres-service:5432` → Routes to PostgreSQL
- `minio-service:9000` → Routes to MinIO S3 API
- `vault-service:8200` → Routes to HashiCorp Vault REST API
- `ldap-service:3890` → Routes to LDAP protocol listener

### 2. Multi-Replica Load Balancing
Notice in `01-deployment.yaml`, we specified:
```yaml
spec:
  replicas: 2
```
When requests arrive at `demo-app-service`, Kubernetes distributes incoming TCP packets across both Pod replicas. Look at the top right of the dashboard: as you refresh, you will see the **Served by Pod** identifier alternate between the two pods!

### 3. Built-in Telemetry for Prometheus
The application exposes a `/metrics` route containing standard Prometheus metrics:
- `app_requests_total{endpoint="..."}`: Request counters
- `app_service_calls_total{service="postgres|minio|vault|ldap", status="ok|error"}`
- `app_request_latency_seconds`: Execution histograms

---

## Hands-On Commands

### Deploy the App
```bash
kubectl apply -f 05-app/
```

### Accessing the Web Portal
Forward port 8000 to your host machine:
```bash
kubectl port-forward -n lab svc/demo-app-service 8000:8000
```
Open **http://localhost:8000** in your web browser!
- **Postgres:** Add a note and observe it persist to the database table.
- **MinIO:** Upload a file and observe it populate in the S3 bucket.
- **Vault:** View decrypted application secrets fetched dynamically from the vault engine.
- **LDAP:** Test authenticating with `admin` / `LdapAdminPassword123!`.
