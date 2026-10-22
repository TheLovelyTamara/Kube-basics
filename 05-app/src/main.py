import os
import socket
import psycopg2
import boto3
import requests
from botocore.client import Config
from ldap3 import Server, Connection, ALL
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI(title="Kubernetes Lab Portal")
templates = Jinja2Templates(directory="templates")

# Metrics
REQUESTS_TOTAL = Counter('app_requests_total', 'Total HTTP requests', ['endpoint'])
SERVICE_CALLS = Counter('app_service_calls_total', 'Calls to cluster backend services', ['service', 'status'])
LATENCY = Histogram('app_request_latency_seconds', 'Request latency in seconds', ['endpoint'])

# Environment variables (Injected via Kubernetes Service Discovery)
PG_HOST = os.getenv("POSTGRES_HOST", "postgres-service")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "SuperSecurePassword123!")
PG_DB   = os.getenv("POSTGRES_DB", "appdb")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "MinioAdminPassword123!")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "lab-bucket")

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault-service:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")

LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap-service")
LDAP_PORT = int(os.getenv("LDAP_PORT", "3890"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")

HOSTNAME = socket.gethostname()

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_USER,
        aws_secret_access_key=MINIO_PASS,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def init_postgres():
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, dbname=PG_DB, connect_timeout=3
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"PostgreSQL init error: {e}")

def init_minio():
    try:
        s3 = get_s3_client()
        buckets = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]
        if MINIO_BUCKET not in buckets:
            s3.create_bucket(Bucket=MINIO_BUCKET)
    except Exception as e:
        print(f"MinIO init error: {e}")

@app.on_event("startup")
def startup_event():
    init_postgres()
    init_minio()

@app.get("/metrics")
def metrics():
    REQUESTS_TOTAL.labels(endpoint='/metrics').inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def healthz():
    return {"status": "ok", "pod": HOSTNAME}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    REQUESTS_TOTAL.labels(endpoint='/').inc()
    start_time = time.time()
    
    # 1. PostgreSQL Status & Notes
    pg_status = {"ok": False, "msg": "", "notes": []}
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, dbname=PG_DB, connect_timeout=3
        )
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, content, created_at FROM notes ORDER BY id DESC LIMIT 5;")
            rows = cur.fetchall()
            pg_status["notes"] = [{"id": r[0], "title": r[1], "content": r[2], "date": str(r[3])} for r in rows]
            pg_status["ok"] = True
            pg_status["msg"] = f"Connected ({len(rows)} notes loaded)"
        conn.close()
        SERVICE_CALLS.labels(service='postgres', status='ok').inc()
    except Exception as e:
        pg_status["msg"] = str(e)
        SERVICE_CALLS.labels(service='postgres', status='error').inc()

    # 2. MinIO Status & Files
    s3_status = {"ok": False, "msg": "", "files": []}
    try:
        s3 = get_s3_client()
        resp = s3.list_objects_v2(Bucket=MINIO_BUCKET)
        s3_status["files"] = [obj['Key'] for obj in resp.get('Contents', [])]
        s3_status["ok"] = True
        s3_status["msg"] = f"Bucket '{MINIO_BUCKET}' active ({len(s3_status['files'])} objects)"
        SERVICE_CALLS.labels(service='minio', status='ok').inc()
    except Exception as e:
        s3_status["msg"] = str(e)
        SERVICE_CALLS.labels(service='minio', status='error').inc()

    # 3. HashiCorp Vault Status & Secrets
    vault_status = {"ok": False, "msg": "", "data": {}}
    try:
        headers = {"X-Vault-Token": VAULT_TOKEN}
        v_resp = requests.get(f"{VAULT_ADDR}/v1/secret/data/app", headers=headers, timeout=3)
        if v_resp.status_code == 200:
            vault_status["ok"] = True
            vault_status["data"] = v_resp.json().get('data', {}).get('data', {})
            vault_status["msg"] = "Retrieved live secrets from Vault"
            SERVICE_CALLS.labels(service='vault', status='ok').inc()
        else:
            vault_status["msg"] = f"HTTP {v_resp.status_code}: {v_resp.text}"
            SERVICE_CALLS.labels(service='vault', status='error').inc()
    except Exception as e:
        vault_status["msg"] = str(e)
        SERVICE_CALLS.labels(service='vault', status='error').inc()

    # 4. LDAP Server Connectivity
    ldap_status = {"ok": False, "msg": ""}
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL, connect_timeout=3)
        conn = Connection(server, user=f"uid=admin,ou=people,{LDAP_BASE_DN}", password="LdapAdminPassword123!", auto_bind=True)
        ldap_status["ok"] = True
        ldap_status["msg"] = f"Connected to LDAP at {LDAP_SERVER}:{LDAP_PORT}"
        conn.unbind()
        SERVICE_CALLS.labels(service='ldap', status='ok').inc()
    except Exception as e:
        ldap_status["msg"] = str(e)
        SERVICE_CALLS.labels(service='ldap', status='error').inc()

    LATENCY.labels(endpoint='/').observe(time.time() - start_time)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "pod_name": HOSTNAME,
        "pg": pg_status,
        "s3": s3_status,
        "vault": vault_status,
        "ldap": ldap_status
    })

@app.post("/postgres/add")
def add_note(title: str = Form(...), content: str = Form(...)):
    REQUESTS_TOTAL.labels(endpoint='/postgres/add').inc()
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, dbname=PG_DB, connect_timeout=3
        )
        with conn.cursor() as cur:
            cur.execute("INSERT INTO notes (title, content) VALUES (%s, %s);", (title, content))
        conn.commit()
        conn.close()
        return Response(headers={"Location": "/"}, status_code=303)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/minio/upload")
async def upload_file(file: UploadFile = File(...)):
    REQUESTS_TOTAL.labels(endpoint='/minio/upload').inc()
    try:
        s3 = get_s3_client()
        content = await file.read()
        s3.put_object(Bucket=MINIO_BUCKET, Key=file.filename, Body=content)
        return Response(headers={"Location": "/"}, status_code=303)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/ldap/auth")
def test_ldap_auth(username: str = Form(...), password: str = Form(...)):
    REQUESTS_TOTAL.labels(endpoint='/ldap/auth').inc()
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, connect_timeout=3)
        # Attempt bind with user credentials
        user_dn = f"uid={username},ou=people,{LDAP_BASE_DN}"
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        conn.unbind()
        return JSONResponse({"status": "success", "message": f"Successfully authenticated as {username} via LDAP!"})
    except Exception as e:
        return JSONResponse({"status": "failed", "message": f"LDAP Authentication Failed: {str(e)}"}, status_code=401)
