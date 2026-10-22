# 04 - Secrets Management (HashiCorp Vault)

This section deploys **HashiCorp Vault**, the gold standard in enterprise secrets management and data protection.

---

## Why HashiCorp Vault when Kubernetes has `Secret`s?

This is one of the most common questions in modern cloud-native architectures:

| Feature | Kubernetes Native `Secret` | HashiCorp Vault |
| :--- | :--- | :--- |
| **Storage & Encryption** | Stored in `etcd` (base64 obfuscated; unencrypted unless KMS is explicitly configured). | Strongly encrypted in transit and at rest using AES-GCM-256. |
| **Lifecycle** | Static: updated manually by changing manifests. | Dynamic: can generate temporary DB credentials with automatic TTL expiration. |
| **Audit Trails** | Basic K8s API audit logs. | Detailed cryptographic logs: tracks *who*, *when*, and *what IP* requested any secret. |
| **Access Control** | K8s RBAC (all or nothing per namespace). | Granular path-based policies (`secret/data/finance/*` vs `secret/data/dev/*`). |
| **Multi-Cloud** | Tied strictly to that one Kubernetes cluster. | Centralized secrets hub across multiple clouds, clusters, and on-prem VMs. |

---

## File Breakdown

- `00-configmap.yaml`: Sets up dev mode with root token `root`, UI enabled, and listening on `0.0.0.0:8200`.
- `01-deployment.yaml`: Launches the `hashicorp/vault:latest` container with `IPC_LOCK` capability and HTTP probes on `/v1/sys/health`.
- `02-service.yaml`: ClusterIP service exposing port 8200 internally as `http://vault-service:8200`.

---

## Hands-On Commands

### Deploy Vault
```bash
kubectl apply -f 04-vault/
```

### Accessing the Vault Web UI
Forward port 8200 to your host:
```bash
kubectl port-forward -n lab svc/vault-service 8200:8200
```
Open **http://localhost:8200** in your browser:
- **Method:** Token
- **Token:** `root`

### Reading & Writing Secrets via `kubectl exec`
You can interact with Vault directly through the CLI inside the pod:
```bash
# Write a secret to the key-value store (kv-v2)
kubectl exec -n lab deploy/vault-deployment -- vault kv put secret/app \
  api_key="sk-live-super-secret-production-key" \
  maintenance_mode="false"

# Read the secret back
kubectl exec -n lab deploy/vault-deployment -- vault kv get secret/app
```
