# CI/CD in Modern Cloud Development
### A Slide-by-Slide Walkthrough — Using This Flask App as a Live Example

---

## Slide 1 — What is CI/CD?

**CI/CD** stands for **Continuous Integration / Continuous Delivery (or Deployment)**.

It is a software development practice where code changes are automatically **built, tested, and delivered** to production — reducing manual steps and human error.

| Term | What it means |
|---|---|
| **Continuous Integration (CI)** | Every code push triggers an automatic build and test run |
| **Continuous Delivery (CD)** | Every passing build is automatically packaged and made ready to deploy |
| **Continuous Deployment** | Every passing build is automatically deployed to production with no manual gate |

> **Key idea:** Automate the repetitive, error-prone parts of getting code from a developer's laptop into a running system.

---

## Slide 2 — Why CI/CD Matters

Without CI/CD, teams face:

- **"Works on my machine"** — code works locally but fails in production
- **Long release cycles** — weeks or months between deployments
- **Integration hell** — merging code from multiple developers breaks everything
- **Manual and inconsistent deployments** — human steps mean human mistakes

With CI/CD, teams get:

- **Fast feedback** — broken code is caught in minutes, not days
- **Consistent builds** — every build follows the exact same steps
- **Smaller, safer releases** — frequent small changes are easier to debug than rare big ones
- **Audit trails** — every deployment is tied to a specific commit and logged
- **Developer confidence** — automated tests act as a safety net

> **Industry reality:** High-performing teams deploy multiple times per day. CI/CD is what makes that possible.

---

## Slide 3 — The CI/CD Pipeline: A Mental Model

Think of a pipeline as an **assembly line**. Code enters at one end; a running application comes out the other.

```
Developer pushes code
        │
        ▼
┌─────────────────┐
│   Source Control │  ← GitHub / GitLab / Azure DevOps
│   (git push)     │
└────────┬────────┘
         │  triggers
         ▼
┌─────────────────┐
│   CI Stage       │  ← Checkout → Install deps → Run tests → Build artifact
│   (GitHub Action)│
└────────┬────────┘
         │  on success
         ▼
┌─────────────────┐
│   CD Stage       │  ← Build Docker image → Push to registry → Deploy
│   (GitHub Action)│
└────────┬────────┘
         │
         ▼
  Running Application
  (Azure App Service / AKS / etc.)
```

Each stage only runs if the previous one succeeds. A failing test stops the pipeline before bad code ever reaches production.

---

## Slide 4 — Docker's Role in CI/CD

**Docker** solves the "works on my machine" problem by packaging the application and everything it needs into a portable **container image**.

### Why Docker is central to CI/CD:

- **Reproducibility** — the same image runs on a developer laptop, in CI, and in production
- **Isolation** — the app and its dependencies are sealed from the host OS
- **Versioning** — images are tagged (e.g., `flask-app:abc1234`), so every deployment is traceable
- **Speed** — layer caching makes rebuilds fast; only changed layers re-run

### The Docker workflow in a CI/CD pipeline:

```
Code change
    │
    ▼
CI builds a Docker image
    │
    ▼
Image is pushed to a registry (Docker Hub / ACR / ECR)
    │
    ▼
Deployment pulls that exact image and runs it
```

The registry is the **handoff point** between the build system and the deployment system.

---

## Slide 5 — This Project's File Structure

Here is the complete layout of this Flask app and what each file does in the CI/CD context:

```
flask_github_actions_demo/
│
├── .github/
│   └── workflows/
│       └── build-push.yml     ← THE PIPELINE: defines every automated step
│
├── app/
│   ├── __init__.py            ← Marks this folder as a Python package
│   └── routes.py              ← Flask routes: /, /health, /api/info
│
├── tests/
│   ├── __init__.py            ← Marks this folder as a test package
│   └── test_app.py            ← Pytest tests run automatically in CI
│
├── app.py                     ← Flask app factory (entry point for gunicorn)
├── Dockerfile                 ← Instructions to build the container image
├── requirements.txt           ← Python dependencies (pinned versions)
├── .gitignore                 ← Keeps secrets and build artifacts out of git
└── README.md                  ← Human-readable project documentation
```

### Why this structure supports CI/CD:

| File | CI/CD role |
|---|---|
| `build-push.yml` | The pipeline definition — orchestrates every automated step |
| `Dockerfile` | Tells the pipeline how to package the app |
| `requirements.txt` | Pinned dependencies — guarantees the same libs in every build |
| `tests/test_app.py` | Automated quality gate — pipeline fails if tests fail |
| `.gitignore` | Prevents secrets (`.env`) and cache files from entering the pipeline |

---

## Slide 6 — The Dockerfile: Multi-Stage Build

The `Dockerfile` in this project uses a **multi-stage build** — a best practice for production images.

```dockerfile
# Stage 1: Builder — install dependencies
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final — lean production image
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local   # only copy installed packages
COPY . .

ENV PATH=/root/.local/bin:$PATH

# Security: run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check: lets orchestrators know the app is alive
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Production WSGI server (not Flask's dev server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "app:create_app()"]
```

### What each decision means:

| Choice | Why it matters |
|---|---|
| `python:3.11-slim` | Smaller base image = smaller attack surface + faster pulls |
| Multi-stage build | Build tools don't end up in the production image |
| Non-root user (`appuser`) | Containers should never run as root in production |
| `HEALTHCHECK` | Kubernetes and Azure can restart the container if it becomes unhealthy |
| `gunicorn` | Production-grade WSGI server; Flask's built-in server is not for production |

---

## Slide 7 — The GitHub Actions Workflow File

The pipeline lives at `.github/workflows/build-push.yml`. GitHub reads this file automatically on every push.

```yaml
name: Build & Push Flask Docker Image to ACR

on:
  push:
    branches: [main]        # runs on every push to main
  workflow_dispatch:        # also allows manual trigger from GitHub UI

permissions:
  id-token: write           # required for OIDC (passwordless Azure login)
  contents: read

jobs:
  build-and-push:
    runs-on: ubuntu-latest  # GitHub spins up a fresh Linux VM for each run
    environment: production # references GitHub environment secrets

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Azure (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Log in to ACR
        run: az acr login --name ${{ secrets.ACR_NAME }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ secrets.ACR_NAME }}.azurecr.io/flask-app:${{ github.sha }}
            ${{ secrets.ACR_NAME }}.azurecr.io/flask-app:latest

      - name: Logout from ACR
        if: always()        # runs even if previous steps fail
        run: docker logout ${{ secrets.ACR_NAME }}.azurecr.io
```

---

## Slide 8 — Breaking Down the Pipeline Steps

Each step in the workflow serves a specific purpose:

### Step 1: Checkout code
```yaml
- uses: actions/checkout@v4
```
Clones the repository onto the GitHub-hosted runner VM. Without this, no other step has access to the code.

---

### Step 2: Login to Azure using OIDC
```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```
**OIDC (OpenID Connect)** is a keyless authentication method. Instead of storing a long-lived password as a secret, GitHub and Azure negotiate a short-lived token. This is far more secure than traditional service principal passwords.

---

### Step 3: Login to Azure Container Registry (ACR)
```yaml
- run: az acr login --name ${{ secrets.ACR_NAME }}
```
ACR is Azure's private Docker registry. This step authenticates Docker on the runner so it can push images.

---

### Step 4: Docker Buildx setup
```yaml
- uses: docker/setup-buildx-action@v3
```
Enables advanced Docker build features — including build caching and multi-platform builds (e.g., `linux/amd64` and `linux/arm64` from the same pipeline).

---

### Step 5: Build and Push
```yaml
tags: |
  ${{ secrets.ACR_NAME }}.azurecr.io/flask-app:${{ github.sha }}
  ${{ secrets.ACR_NAME }}.azurecr.io/flask-app:latest
```
The image gets **two tags**:
- `flask-app:abc1234` — the exact git commit SHA; lets you roll back to any specific commit
- `flask-app:latest` — a floating tag; deployment configs can always point to the newest build

---

### Step 6: Logout
```yaml
if: always()
run: docker logout ${{ secrets.ACR_NAME }}.azurecr.io
```
`if: always()` ensures cleanup runs even if the build failed. Leaving credentials active on a shared runner is a security risk.

---

## Slide 9 — Automated Testing in the Pipeline

This project includes a `tests/` directory with **pytest** tests. In a full CI pipeline, these run before the Docker build — ensuring a broken app never gets packaged.

```python
# tests/test_app.py

import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello from Flask!' in response.data

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    assert 'app' in response.json
    assert response.json['version'] == '1.0.0'
```

### What each test verifies:

| Test | What it checks |
|---|---|
| `test_index` | Root endpoint returns 200 and the expected JSON message |
| `test_health` | Health check endpoint returns `{"status": "ok"}` — used by Docker/Kubernetes |
| `test_info` | API info endpoint returns app metadata in the expected shape |

### Where tests fit in the pipeline:

```
push to main
    │
    ▼
Run pytest tests ──── FAIL ──► Pipeline stops. No image built. Developer notified.
    │
  PASS
    │
    ▼
Build Docker image
    │
    ▼
Push to ACR
```

To add tests to this workflow, you would add these steps before the Docker build:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install dependencies
  run: pip install -r requirements.txt

- name: Run tests
  run: pytest tests/ --cov=app --cov-report=term-missing
```

---

## Slide 10 — Secrets and Security

The workflow uses **GitHub Secrets** — encrypted values stored in the repository or environment settings, never visible in logs.

| Secret | What it holds |
|---|---|
| `AZURE_CLIENT_ID` | Azure app registration identity for OIDC |
| `AZURE_TENANT_ID` | Azure Active Directory tenant |
| `AZURE_SUBSCRIPTION_ID` | The Azure subscription to bill resources to |
| `ACR_NAME` | The name of the Azure Container Registry (e.g., `myregistry`) |

### Security model:

```
GitHub Secrets (encrypted at rest)
        │
        │  injected at runtime only
        ▼
GitHub Actions runner (ephemeral VM, destroyed after job)
        │
        │  OIDC token (expires in minutes)
        ▼
Azure (authenticates the runner, grants push access to ACR)
```

**No long-lived passwords** are stored anywhere in the codebase or CI logs. This is the modern, recommended approach.

---

## Slide 11 — Infrastructure as Code (IaaC) and CI/CD

**Infrastructure as Code (IaaC)** means defining cloud infrastructure in files (code) rather than clicking through a console. CI/CD and IaaC are complementary — the pipeline can provision infrastructure before deploying the app.

### Common IaaC tools:

| Tool | What it manages |
|---|---|
| **Terraform** | Cloud-agnostic — provisions Azure, AWS, GCP resources from `.tf` files |
| **Bicep / ARM Templates** | Azure-native — defines Azure resources declaratively |
| **Pulumi** | IaaC using general-purpose languages (Python, TypeScript) |
| **Ansible** | Configuration management — installs software, configures OS-level settings |
| **Helm** | Kubernetes package manager — deploys apps into clusters |

### IaaC in a CI/CD pipeline:

```yaml
jobs:
  provision:
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with: { ... }
      - name: Deploy infrastructure with Bicep
        run: |
          az deployment group create \
            --resource-group myRG \
            --template-file infra/main.bicep \
            --parameters env=production

  deploy:
    needs: provision      # waits for infrastructure to be ready
    steps:
      - name: Deploy app to Azure App Service
        run: az webapp config container set ...
```

> **The pipeline becomes the single source of truth** — both the infrastructure and the application are deployed through the same automated, audited process.

---

## Slide 12 — Docker Hub vs. Azure Container Registry (ACR)

Both are Docker image registries — the question is which one to use and why.

| Feature | Docker Hub | Azure Container Registry (ACR) |
|---|---|---|
| **Ownership** | Docker Inc. | Microsoft Azure |
| **Access control** | Public by default, basic private tiers | Full Azure RBAC integration |
| **Authentication** | Username + password or token | Azure AD / OIDC (this project) |
| **Network** | Public internet | Can be private (VNet integration) |
| **Best for** | Open-source projects, public images | Enterprise workloads on Azure |
| **Cost** | Free tier limited; paid for private | Pay per storage and transfer |
| **Geo-replication** | Not available | Yes — replicate to multiple Azure regions |
| **Vulnerability scanning** | Available on paid plans | Built-in via Microsoft Defender |

### This project uses ACR because:

- The deployment target is Azure (App Service, AKS, Container Apps)
- OIDC authentication means no stored passwords
- Images stay inside the Azure network boundary (lower latency, lower egress cost)
- Azure RBAC controls who can pull or push images

### If you wanted Docker Hub instead, the push step would change to:

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    push: true
    tags: myusername/flask-app:latest
```

---

## Slide 13 — The Full Azure Deployment Flow

Here is how this project's pipeline fits into the broader Azure deployment picture:

```
Developer pushes code to GitHub (main branch)
        │
        ▼
GitHub Actions runner starts (ubuntu-latest VM)
        │
        ├── Authenticates to Azure via OIDC
        │
        ├── Logs into ACR
        │
        ├── Runs Docker Buildx (multi-stage build from Dockerfile)
        │
        └── Pushes image to ACR with two tags:
                ├── flask-app:abc1234  (git SHA — immutable)
                └── flask-app:latest   (floating — always newest)
                        │
                        ▼
              Azure Container Registry
              (private registry inside Azure)
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
     Azure App      Azure       Azure
     Service        Kubernetes  Container
     (pulls latest) Service     Apps
                    (pulls SHA) (pulls latest)
```

### Extending this pipeline to deploy:

After the push step, you could add:

```yaml
- name: Deploy to Azure App Service
  uses: azure/webapps-deploy@v3
  with:
    app-name: my-flask-app
    images: ${{ secrets.ACR_NAME }}.azurecr.io/flask-app:${{ github.sha }}
```

This pulls the exact image just built and swaps it into the running App Service — zero-downtime deployment if slot swapping is configured.

---

## Slide 14 — CI/CD in Kubernetes / AKS Orchestration

When the deployment target is **Kubernetes (AKS)**, CI/CD integrates with the orchestrator:

### The Kubernetes deployment pattern:

```yaml
# k8s/deployment.yaml (stored in the repo)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flask-app
  template:
    spec:
      containers:
        - name: flask-app
          image: myregistry.azurecr.io/flask-app:latest  # updated by pipeline
          ports:
            - containerPort: 5000
          livenessProbe:
            httpGet:
              path: /health    # our health endpoint
              port: 5000
```

### How CI/CD updates Kubernetes:

```yaml
# In build-push.yml, after the image push:

- name: Update Kubernetes deployment
  run: |
    az aks get-credentials --resource-group myRG --name myAKS
    kubectl set image deployment/flask-app \
      flask-app=${{ secrets.ACR_NAME }}.azurecr.io/flask-app:${{ github.sha }}
    kubectl rollout status deployment/flask-app
```

### Kubernetes features CI/CD relies on:

| Feature | Role in CI/CD |
|---|---|
| **Rolling updates** | New pods start before old ones stop — zero downtime |
| **Health checks** | Kubernetes uses our `/health` endpoint to validate the new pods |
| **Rollback** | `kubectl rollout undo` reverts to the previous image SHA instantly |
| **Replica sets** | Multiple instances absorb traffic during a rolling update |

---

## Slide 15 — GitOps: The Next Level

**GitOps** is the practice of using git as the **single source of truth** for both application code and infrastructure state.

Instead of the pipeline directly calling `kubectl`, it updates a deployment manifest file in git, and a separate tool (like **Argo CD** or **Flux**) syncs the cluster to match.

```
Developer pushes app code
        │
        ▼
CI pipeline builds image, pushes to ACR
        │
        ▼
Pipeline updates image tag in k8s/deployment.yaml
git commit: "chore: bump flask-app to sha-abc1234"
        │
        ▼
Argo CD (running in cluster) detects the git change
        │
        ▼
Argo CD applies the new manifest to the cluster
        │
        ▼
Cluster matches git — drift is detected and corrected automatically
```

### Benefits over direct kubectl in CI:

- **Audit trail**: every deployment is a git commit with author and timestamp
- **Rollback**: `git revert` rolls back a deployment
- **Separation of concerns**: CI builds; git stores desired state; the cluster syncs itself

---

## Slide 16 — The Application Routes and Their CI/CD Significance

This Flask app exposes three routes, each with a specific role in the CI/CD ecosystem:

```python
# app/routes.py

@main_bp.route('/')
def index():
    return jsonify({'message': 'Hello from Flask!', 'status': 'healthy'})

@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@main_bp.route('/api/info')
def info():
    return jsonify({
        'app': 'Flask Demo App',
        'version': '1.0.0',
        'description': 'A simple Flask app with CI/CD to Azure testing.'
    })
```

| Route | CI/CD role |
|---|---|
| `/` | Basic smoke test — automated tests assert `Hello from Flask!` is present |
| `/health` | Health gate — Docker `HEALTHCHECK`, Kubernetes liveness probe, and Azure App Service health checks all hit this endpoint. If it fails, the deployment is halted. |
| `/api/info` | Metadata — useful for verifying the correct version is deployed; a smoke test after deployment can assert `version == "1.0.0"` |

The `/health` endpoint is the most critical. Every layer of the deployment stack uses it:

```
Docker HEALTHCHECK  →  is the container alive?
Kubernetes liveness →  should this pod receive traffic?
Azure App Service   →  should this slot be promoted?
Load balancer       →  is this instance healthy?
```

---

## Slide 17 — Environment Promotion Strategy

Professional CI/CD pipelines have multiple environments. Code flows from development toward production through a series of gates:

```
feature branch push
        │
        ▼
  dev environment
  (auto-deploy, no approval)
        │
  integration tests pass?
        │ yes
        ▼
  staging environment
  (mirrors production config)
        │
  manual approval gate
        │ approved
        ▼
  production environment
  (deploy with canary or blue/green)
```

### In GitHub Actions, environment protection rules enforce this:

```yaml
jobs:
  deploy-production:
    environment: production    # this line requires approval from a designated reviewer
    steps:
      - ...
```

This project already uses `environment: production` in the workflow — meaning a GitHub environment with that name can be configured to require a human approval before the build is pushed.

---

## Slide 18 — Summary: The Complete Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER WORKFLOW                        │
│                                                                  │
│  Write code  →  git push  →  Pull Request  →  merge to main     │
└──────────────────────────────────┬──────────────────────────────┘
                                   │ triggers
┌──────────────────────────────────▼──────────────────────────────┐
│                        CI STAGE (GitHub Actions)                 │
│                                                                  │
│  1. Checkout code          (actions/checkout)                    │
│  2. Run pytest tests       (quality gate)                        │
│  3. Authenticate to Azure  (OIDC — no passwords stored)          │
│  4. Login to ACR           (az acr login)                        │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                        CD STAGE (GitHub Actions)                 │
│                                                                  │
│  5. Build Docker image     (multi-stage Dockerfile)              │
│  6. Push to ACR            (SHA tag + latest tag)                │
│  7. Deploy to Azure        (App Service / AKS / Container Apps)  │
│  8. Health check validates (via /health endpoint)                │
│  9. Cleanup credentials    (docker logout)                       │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                        RUNNING IN AZURE                          │
│                                                                  │
│  Container pulled from ACR → Started by orchestrator            │
│  /health polled → Traffic routed if healthy                      │
│  Old containers terminated → Zero-downtime rollout complete      │
└─────────────────────────────────────────────────────────────────┘
```

### Key takeaways:

1. **CI/CD is a practice, not a product** — GitHub Actions, Azure DevOps, and Jenkins all implement the same ideas
2. **Docker is the packaging format** — it makes the build environment match the run environment
3. **Registries (ACR, Docker Hub) are the handoff** — CI pushes, CD pulls
4. **Tests are the quality gate** — without them, CI/CD just automates the delivery of broken code faster
5. **IaaC brings infrastructure into the same pipeline** — the whole system, not just the app, is version-controlled
6. **Secrets management and OIDC replace passwords** — modern pipelines use short-lived tokens, not stored credentials
7. **Health endpoints are a first-class concern** — every orchestration layer depends on `/health` to make deployment decisions

---

## Appendix — Quick Reference: Files in This Project

| File | Lines | Purpose |
|---|---|---|
| `.github/workflows/build-push.yml` | 47 | The full CI/CD pipeline definition |
| `Dockerfile` | 37 | Multi-stage container build instructions |
| `app.py` | 7 | Flask app factory — creates and configures the app |
| `app/routes.py` | 19 | HTTP route handlers including the `/health` endpoint |
| `app/__init__.py` | 1 | Python package marker |
| `tests/test_app.py` | 26 | Automated pytest tests for all three routes |
| `tests/__init__.py` | 0 | Python package marker for the test directory |
| `requirements.txt` | 6 | Pinned Python dependencies (Flask, gunicorn, pytest) |
| `.gitignore` | 180 | Excludes secrets, caches, and compiled files from git |

---

*Presented for CPSY 300 — Cloud Computing, Unit 3*
*Flask GitHub Actions Demo — github.com/your-repo/flask_github_actions_demo*
