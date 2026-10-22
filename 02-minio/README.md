# 02 - Blob Storage (MinIO - S3 Compatible)

This section deploys **MinIO**, a high-performance, S3-compatible object storage server, into the `lab` namespace.

---

## What is Object / Blob Storage?

In computing, there are three primary storage models:
1. **File Storage** (e.g. NFS, SMB): Hierarchical folder trees (`/home/user/docs/report.pdf`).
2. **Block Storage** (e.g. AWS EBS, K8s PersistentVolumes): Raw block devices formatted with a filesystem (ext4, xfs) attached to a single machine.
3. **Object/Blob Storage** (e.g. AWS S3, MinIO): Flat namespace of **Buckets** containing **Objects** (blobs of bytes + metadata) accessed over HTTP REST APIs (`GET /my-bucket/photo.jpg`).

---

## Key Kubernetes Concepts Taught in This Section

### 1. Multi-Port Services (`04-service.yaml`)
MinIO operates two separate network listeners:
- Port **9000**: S3 REST API (used by our Demo App code).
- Port **9001**: Web Console (used by human operators via a browser).

In Kubernetes, a single `Service` can expose multiple ports. **Rule:** Whenever a Service exposes more than one port, **every port entry MUST have a unique `name` attribute** (e.g., `s3-api` and `console`).

### 2. HTTP Probes (`03-deployment.yaml`)
In PostgreSQL, we used `exec` probes running `pg_isready`. For web services like MinIO, Kubernetes supports native `httpGet` probes:
```yaml
livenessProbe:
  httpGet:
    path: /minio/health/live
    port: 9000
```
Kubernetes periodically sends an HTTP GET request to this path. If the status code is between 200 and 399, the container is deemed healthy.

---

## File Breakdown

- `00-configmap.yaml`: Enables MinIO browser UI and exposes Prometheus metrics endpoints.
- `01-secret.yaml`: Configures root credentials (`minioadmin` / `MinioAdminPassword123!`).
- `02-pvc.yaml`: Dynamically provisions 2Gi of durable host storage for stored objects.
- `03-deployment.yaml`: Launches `alpine/minio:latest-release` with persistent volume mount to `/data`.
- `04-service.yaml`: Multi-port ClusterIP service routing port 9000 (S3 API) and 9001 (Web Console).

---

## Real-World Lesson: Debugging `ImagePullBackOff`

During our deployment, the Pod initially entered `ImagePullBackOff`. 
We ran:
```bash
kubectl describe pod -l app=minio -n lab
```
Under **Events**, Kubernetes told us:
> `Failed to pull image "minio/minio:latest": pull access denied, repository does not exist or may require authorization`

**Why did this happen?** MinIO shifted their community distribution model, removing the unauthenticated `:latest` tag on Docker Hub. We switched to the community-maintained `alpine/minio:latest-release` image, applied the update, and Kubernetes instantly resolved the issue and brought the Pod to `1/1 Running`.

This is a classic Kubernetes debugging workflow:
1. `kubectl get pods` -> See something wrong (e.g. `CrashLoopBackOff`, `ImagePullBackOff`, `Pending`).
2. `kubectl describe pod <name>` -> Read the **Events** at the bottom.
3. `kubectl logs <name>` -> Read application startup logs if the container crashed.

---

## Hands-On Commands

### Deploy MinIO
```bash
kubectl apply -f 02-minio/
```

### Check Status
```bash
kubectl get pods,pvc,svc -l app=minio -n lab
```

### Accessing the Web Console in your Browser
Forward the console port (9001) to your desktop:
```bash
kubectl port-forward -n lab svc/minio-service 9001:9001
```
Open **http://localhost:9001** in your web browser:
- **Username:** `minioadmin`
- **Password:** `MinioAdminPassword123!`
