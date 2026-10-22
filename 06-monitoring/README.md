# 06 - Monitoring & Dashboards (Prometheus + Grafana)

This section deploys the industry-standard observability stack (**Prometheus** for metrics collection and **Grafana** for visualization) into our `lab` namespace.

---

## Observability Architecture

```
                                  ┌───────────────────────────────┐
                                  │      Grafana (Port 3000)      │
                                  │   (Visual Dashboards & Graphs)│
                                  └───────────────▲───────────────┘
                                                  │ PromQL queries
                                  ┌───────────────┴───────────────┐
                                  │    Prometheus (Port 9090)     │
                                  │ (Scrapes & Stores Time-Series)│
                                  └───────────────▲───────────────┘
                                                  │
                 ┌────────────────────────────────┴───────────────────────────────┐
                 │ scrapes /metrics every 10s                                    │
                 ▼                                                               ▼
    ┌───────────────────────────┐                                   ┌───────────────────────────┐
    │     Demo Application      │                                   │           MinIO           │
    │   (demo-app-service:8000) │                                   │    (minio-service:9000)   │
    │ - HTTP request rates      │                                   │ - Bucket & storage stats  │
    │ - Backend call statuses   │                                   │ - S3 traffic metrics      │
    └───────────────────────────┘                                   └───────────────────────────┘
```

---

## Key Kubernetes Concepts Taught

### 1. Prometheus Scraping (`00-prometheus-config.yaml`)
Prometheus uses a **pull model**: it reads a list of target endpoints from its configuration and initiates periodic HTTP GET requests to `/metrics`.
Notice the target addresses use internal cluster DNS:
- `demo-app-service.lab.svc.cluster.local:8000`
- `minio-service.lab.svc.cluster.local:9000`

### 2. Declarative Grafana Provisioning (`03-grafana-config.yaml` & `04-grafana-dashboard-data.yaml`)
In amateur setups, people log into Grafana and manually click buttons to add datasources and import dashboards.
In production GitOps, **everything is declared as code**:
- `datasources.yaml`: Instructs Grafana to automatically connect to Prometheus on boot.
- `dashboards.yaml`: Instructs Grafana to automatically scan `/var/lib/grafana/dashboards` and load `lab-dashboard.json`.
- The dashboard is instantly available without any manual configuration!

---

## File Breakdown

- `00-prometheus-config.yaml`: Scrape configuration (`prometheus.yml`).
- `01-prometheus-deployment.yaml`: Prometheus server deployment mounting configuration via `subPath`.
- `02-prometheus-service.yaml`: ClusterIP service exposing Prometheus on port 9090.
- `03-grafana-config.yaml`: Datasource and dashboard provider provisioning files.
- `04-grafana-dashboard-data.yaml`: Full JSON definition of the "Kubernetes Microservices Lab Dashboard".
- `05-grafana-deployment.yaml`: Grafana deployment mounting provisioning configs and dashboards.
- `06-grafana-service.yaml`: ClusterIP service exposing Grafana on port 3000.

---

## Hands-On Commands

### Deploy Monitoring Stack
```bash
kubectl apply -f 06-monitoring/
```

### Accessing Grafana Dashboard
Forward port 3000 to your host machine:
```bash
kubectl port-forward -n lab svc/grafana-service 3000:3000
```
Open **http://localhost:3000** in your web browser:
- **Username:** `admin`
- **Password:** `admin`
- Go to **Dashboards** → Open **"Kubernetes Microservices Lab Dashboard"**!

### Accessing Prometheus PromQL Explorer
Forward port 9090 to your host:
```bash
kubectl port-forward -n lab svc/prometheus-service 9090:9090
```
Open **http://localhost:9090** to explore raw metrics, view active scrape targets (**Status** → **Targets**), and test PromQL queries like:
- `app_requests_total`
- `rate(app_requests_total[1m])`
- `up`
