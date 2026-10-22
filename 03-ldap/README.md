# 03 - Directory & Identity Service (LDAP)

This section deploys **LLDAP**, a lightweight, high-performance LDAP directory server with a built-in modern web interface.

---

## What is LDAP?

**LDAP** (Lightweight Directory Access Protocol) is the industry standard for centralizing identities, logins, and group permissions across an organization or cluster of applications.

Instead of every microservice maintaining its own `users` table:
1. All users and groups live inside the centralized LDAP directory.
2. When a user logs into our Demo App, the app performs an **LDAP Bind** (submitting the username and password to the LDAP server to verify authenticity).
3. If valid, the app retrieves the user's attributes (email, full name, groups).

### Core LDAP Concepts:
- **Base DN (Distinguished Name):** The root of the directory tree (e.g., `dc=example,dc=com`).
- **Bind DN:** The administrative or service account used to log into LDAP (e.g. `uid=admin,ou=people,dc=example,dc=com`).
- **ObjectClasses:** Schema defining which attributes an entry can have (`person`, `inetOrgPerson`, `groupOfUniqueNames`).

---

## File Breakdown

- `00-configmap.yaml`: Defines base DN (`dc=example,dc=com`), ports (LDAP 3890, HTTP 17170).
- `01-secret.yaml`: Secure admin password and JWT encryption seeds.
- `02-pvc.yaml`: 500Mi persistent storage for SQLite/user database in `/data`.
- `03-deployment.yaml`: Launches the `lldap/lldap:stable` container with HTTP health probes.
- `04-service.yaml`: Multi-port ClusterIP service exposing both the LDAP wire protocol and Web UI.

---

## Hands-On Commands

### Deploy LDAP
```bash
kubectl apply -f 03-ldap/
```

### Accessing the LDAP Web Console
Forward the management port (17170) to your host machine:
```bash
kubectl port-forward -n lab svc/ldap-service 17170:17170
```
Open **http://localhost:17170** in your web browser:
- **Username:** `admin`
- **Password:** `LdapAdminPassword123!`

You can use this web UI to create users, assign passwords, and organize them into groups!
