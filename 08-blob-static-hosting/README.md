# 08 - Blob Storage (S3 / MinIO) Static Web Hosting Architecture

This section implements the **Cloud-Native "S3 + CloudFront CDN" pattern** inside Kubernetes.

---

## Architectural Comparison

| Traditional Pod Hosting (Phase 7) | Blob Storage Hosting (Phase 8) |
| :--- | :--- |
| HTML/CSS/JS files baked into Docker images or stored in ConfigMaps. | HTML/CSS/JS files stored as **unstructured objects in an S3/MinIO bucket**. |
| Updating the site requires rebuilding container images or updating K8s YAML. | Updating the site requires running `aws s3 cp` or uploading via MinIO Web Console. |
| Web server pods store files on their local filesystem. | Web server pods are stateless proxies pulling bytes from S3. |

---

## How The Architecture Works

```
                                  [User's Browser]
                                         │
                                         ▼
                            http://localhost:8089/
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       Edge CDN Gateway: Nginx (Port 80)      │
                  │         `blob-cdn-gateway-service`           │
                  │             (Stateless Proxy)                │
                  └──────────────┬───────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────────────────────┐
                 │                                               │
                 ▼ Path: `/` & static assets                     ▼ Path: `/api/*`
  ┌──────────────────────────────┐                ┌──────────────────────────────┐
  │     MinIO (S3 Blob Store)    │                │       Backend REST API       │
  │     Bucket: `web-bucket`     │                │   `backend-api-service:5000` │
  │                              │                └──────────────────────────────┘
  │ - index.html (text/html)     │
  │ - style.css  (text/css)      │
  │ - app.js     (application/js)│
  └──────────────────────────────┘
```

---

## New Kubernetes Primitive Taught: `Job` (`01-seeder-job.yaml`)

Unlike a `Deployment` or `StatefulSet` (which are designed to run long-lived server processes indefinitely), a **`Job`** creates one or more Pods and ensures that a specified number of them successfully terminate.

### Typical uses for a Kubernetes `Job`:
1. Database schema migrations (e.g. `alembic upgrade head`, `prisma migrate`)
2. Initializing cloud storage buckets and seeding assets (like our MinIO static seeder!)
3. One-off backup scripts or data processing batches

---

## File Breakdown

- `00-site-content.yaml`: Source HTML, CSS, and JS stored temporarily for initial seeding.
- `01-seeder-job.yaml`: Kubernetes `Job` that executes Python + Boto3 to create `web-bucket`, set the **Public Read** policy, and upload all static files to MinIO S3.
- `02-gateway-config.yaml`: Edge Gateway Nginx config proxying `/` to `http://minio-service:9000/web-bucket/` and `/api/` to `backend-api-service`.
- `03-gateway-deployment.yaml`: Deployment of the Edge Gateway (2 replicas).
- `04-gateway-service.yaml`: ClusterIP service exposing the gateway on port 80.

---

## Hands-On Commands

### 1. Run the Seeder Job and Deploy the Gateway
```bash
kubectl apply -f 08-blob-static-hosting/
```

### 2. Verify the Seeder Job Completed
```bash
kubectl get jobs -n lab
```
You will see `minio-static-seeder-job` report `1/1` in `COMPLETIONS`.

### 3. Access the S3-Hosted Website
Forward the Edge Gateway service to port **8089**:
```bash
kubectl port-forward -n lab svc/blob-cdn-gateway-service 8089:80
```
Open **http://localhost:8089** in your browser:
- Every byte of HTML, CSS, and JavaScript was delivered directly from your **MinIO Object Store**!
- The page dynamically calls the backend REST API at `/api/system`.

---

## Try Updating the Site Live via S3!

Because the site is hosted in MinIO, you can edit it live without restarting any pods!
1. Open your MinIO Web Console at **http://localhost:9001** (or via `kubectl port-forward -n lab svc/minio-service 9001:9001`).
2. Log in (`minioadmin` / `MinioAdminPassword123!`).
3. Click on **`web-bucket`**.
4. You will see `index.html`, `style.css`, and `app.js` sitting in the bucket!
5. Delete or upload an updated file, refresh **http://localhost:8089**, and watch the changes apply immediately!
