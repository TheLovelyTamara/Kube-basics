# 07 - Static Web Frontend & Backend API Architecture

This section demonstrates the standard production pattern for running **decoupled frontend Single Page Applications (SPAs)** and **microservice backend APIs** inside Kubernetes.

---

## The Fundamental Problem Beginners Face

When people deploy a static website (HTML, CSS, JS) and a backend API to Kubernetes for the first time, they often make this mistake:

> *"My frontend JavaScript calls `fetch('http://backend-api-service:5000/api/items')`."*

**Why does this fail?**
- JavaScript executes **inside the client's web browser** on their personal laptop or phone.
- The user's laptop is **NOT** on the Kubernetes cluster's internal private network (`10.96.0.0/12`).
- The user's laptop cannot resolve Kubernetes internal DNS names like `backend-api-service.lab.svc.cluster.local`.

Furthermore, if the backend was exposed directly on another public port, the browser would block the requests due to **CORS (Cross-Origin Resource Sharing)** restrictions.

---

## The Industry Solution: Nginx Reverse Proxy (BFF Pattern)

```
                            [User Laptop / Web Browser]
                                         │
                                         ▼
                            http://localhost:8080/
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Frontend: Nginx (Port 80)           │
                  │         `frontend-web-service`               │
                  └──────────────┬───────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────────────────────┐
                 │                                               │
                 ▼ (Serves static assets)                        ▼ (Reverse proxies `/api/*`)
     ┌───────────────────────┐                       ┌───────────────────────┐
     │ /usr/share/nginx/html │                       │ `backend-api-service` │
     │ - index.html          │                       │ (CoreDNS: port 5000)  │
     │ - style.css           │                       └───────────┬───────────┘
     │ - app.js              │                                   │
     └───────────────────────┘                                   ▼
                                                     ┌───────────────────────┐
                                                     │ Backend REST API Pods │
                                                     │ (2 replicas)          │
                                                     └───────────────────────┘
```

### Why this pattern is best-practice:
1. **Zero CORS Issues:** To the browser, all traffic (both HTML and API data) goes to the exact same origin (`http://localhost:8080`).
2. **Independent Scaling:** 
   - The Nginx frontend consumes ~10MB RAM and can serve tens of thousands of static files per second.
   - The backend API can scale horizontally (e.g. 2, 5, 20 replicas) based on CPU/memory workload without touching the frontend.
3. **Security:** The backend API never needs to be exposed to the outside internet. It lives exclusively inside the cluster's internal network.

---

## File Breakdown

- `00-nginx-config.yaml`: Nginx configuration mapping `/` to static files and reverse-proxying `/api/` to `backend-api-service.lab.svc.cluster.local:5000`.
- `01-static-content.yaml`: Modern responsive SPA (`index.html`, `style.css`, `app.js`).
- `02-api-code.yaml`: Python REST API script responding to `/api/system`, `/api/items`, and `/api/health`.
- `03-api-deployment.yaml`: Deployment of the backend API (2 replicas).
- `04-api-service.yaml`: ClusterIP Service for the API (`backend-api-service:5000`).
- `05-frontend-deployment.yaml`: Deployment of Nginx (2 replicas).
- `06-frontend-service.yaml`: ClusterIP Service for the frontend (`frontend-web-service:80`).

---

## Hands-On Commands

### Deploy Both Services
```bash
kubectl apply -f 07-static-web-and-api/
```

### Open the Application
Forward the frontend web service to port 8080 on your host:
```bash
kubectl port-forward -n lab svc/frontend-web-service 8080:80
```
Open **http://localhost:8080** in your browser:
1. Observe the architecture diagram and live telemetry banner.
2. Watch the **API Pod Hostname** cycle between your backend replicas as it polls `/api/system` every 3 seconds.
3. Add a new item through the form to test asynchronous `POST` requests travelling through the Nginx reverse proxy to the backend API!
