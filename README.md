# Invoice-PO-Reconciler

A small microservices example to upload invoices, extract PO details, and reconcile them. This repository includes services for auth, upload, worker, an API gateway and a frontend with Kubernetes manifests for local deployment with Minikube.

**Goals:** simple local development, repeatable Docker images, and a Minikube deployment recipe.

**Services**
- `auth-service` — user authentication (FastAPI / Python)
- `upload-service` — receives CSV invoice files and stores to S3 (FastAPI / Python)
- `worker-service` — background processing and reconciliation (Python)
- `api-gateway` — lightweight gateway (Node.js)
- `frontend` — Next.js UI

Prerequisites
- Python 3.12
- Node 18+ / npm
- Docker
- Minikube (for Kubernetes deployment)
- kubectl
- (Optional) Redis locally via Docker

Quick local setup (small env and DB checks)

1. Install Python deps used by the repo (global helper):

```powershell
pip install psycopg2-binary python-dotenv
```

2. Verify database connection and apply schema (uses `.env` DATABASE_URL):

```powershell
python .\scripts\test_db_connection.py
python .\scripts\apply_schema.py
```

3. Seed sample data for POs and invoices:

```powershell
python .\scripts\seed_pos.py
python .\scripts\seed_po.py
```

Run services individually

Each Python service has its own `requirements.txt` inside its folder. Example — `auth-service`:

```powershell
cd services\auth-service
python -m venv .ipo_auth --prompt ipo_auth
.ipo_auth\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload
```

Repeat for `upload-service` (port 8002) and `worker-service` (the worker is a Python script you run directly).

Redis (local, optional):

```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Upload a sample invoice (example uses `Sample1.csv` present in `services/upload-service/test_files`):

```powershell
curl.exe -X POST "http://localhost:8002/upload/invoice" -H "Authorization: Bearer <JWT>" -F "file=@services/upload-service/test_files/Sample1.csv"
```

Replace `<JWT>` with a token from the `auth-service` (example credentials are in the project run order notes).

API gateway and Frontend (local dev)

api-gateway (Node):

```powershell
cd services\api-gateway
npm install
node index.js
```

frontend (Next.js):

```powershell
cd services\frontend
npm install
npm run dev
```

Docker images (optional)

Build images for local use (these tags are used by `k8s` manifests):

```powershell
docker build -t auth-service:v1 .\services\auth-service\
docker build -t upload-service:v1 .\services\upload-service\
docker build -t worker-service:v1 .\services\worker-service\
docker build -t api-gateway:v1 .\services\api-gateway\
docker build -t frontend:v1 .\services\frontend\
```

Minikube / Kubernetes deploy (recommended for end-to-end testing)

1. Start Minikube and enable useful addons:

```powershell
# set MINIKUBE_HOME if you want a custom directory
minikube start
minikube addons enable ingress
minikube addons enable metrics-server
```

2. Make Docker build images available to Minikube (optionally):

```powershell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
# then re-run the docker build commands so images exist inside minikube's docker daemon
```

3. Create namespace, configmap and secrets, then apply workloads:

```powershell
minikube kubectl -- apply -f .\k8s\namespace.yaml
minikube kubectl -- apply -f .\k8s\configmap.yaml
minikube kubectl -- apply -f .\k8s\secrets.yaml
minikube kubectl -- apply -f .\k8s\redis-deployment.yaml
minikube kubectl -- apply -f .\k8s\auth-deployment.yaml
minikube kubectl -- apply -f .\k8s\upload-deployment.yaml
minikube kubectl -- apply -f .\k8s\worker-deployment.yaml
minikube kubectl -- apply -f .\k8s\gateway-deployment.yaml
minikube kubectl -- apply -f .\k8s\frontend-deployment.yaml
minikube kubectl -- apply -f .\k8s\ingress.yaml
minikube kubectl -- apply -f .\k8s\hpa.yaml
```

4. Inspect resources:

```powershell
minikube kubectl -- get pods -n invoice-app
minikube kubectl -- get svc -n invoice-app
minikube kubectl -- get ingress -n invoice-app
minikube kubectl -- get hpa -n invoice-app
```

Secrets and `.env`

- This repo includes a `.env` (for local development) and `k8s/secrets.yaml` (base64-encoded values). Keep secrets safe — do not commit real credentials.
- To update Kubernetes secrets from values, base64-encode them and replace the entries in `k8s/secrets.yaml` or create a secret directly:

```powershell
# Example PowerShell base64 encoding (matches .run_order notes)
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('your_value_here'))
```

Helpful files
- [k8s/configmap.yaml](k8s/configmap.yaml) — app config
- [k8s/secrets.yaml](k8s/secrets.yaml) — encoded secrets for k8s
- [services/upload-service/test_files](services/upload-service/test_files) — sample CSVs
- [scripts/apply_schema.py](scripts/apply_schema.py) — DB schema setup
- [scripts/test_db_connection.py](scripts/test_db_connection.py) — DB connectivity check

Troubleshooting
- If services don't connect to Postgres, verify `DATABASE_URL` in `.env` and run `scripts/test_db_connection.py`.
- If Minikube pods are CrashLooping, check pod logs:

```powershell
minikube kubectl -- logs <pod-name> -n invoice-app
```

- If an upload fails, ensure `auth-service` is running and the JWT used in the `Authorization` header is valid.

Next steps and automation
- You can containerize and push images to a registry and update `imagePullPolicy` in `k8s` manifests for production testing.
- Consider adding a Makefile or scripts to automate building, tagging, and applying manifests.

Contact / Notes
- Example run-order and environment values are included in the repository root: `.run_order.txt` and `.env` — use them as a reference for reproducible local runs.

Enjoy exploring the Invoice-PO Reconciler! If you want, I can also:
- run a quick verification of the README format,
- commit the change, or
- add a small `make`/`scripts` helper to automate the common commands.
# Invoice-PO-Reconciler
