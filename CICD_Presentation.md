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
│  Source Control  │  ← GitHub / GitLab / Azure DevOps
│  (git push)      │
└────────┬────────┘
         │  triggers
         ▼
┌─────────────────┐
│   CI Stage       │  ← Checkout → Install deps → Run tests → Build artifact
│  (GitHub Actions)│
└────────┬────────┘
         │  on success
         ▼
┌─────────────────┐
│   CD Stage       │  ← Build Docker image → Push to registry → Deploy
│  (GitHub Actions)│
└────────┬────────┘
         │
         ▼
  Running Application
  (Cloud: App Service / Kubernetes / Container Apps)
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
Image is pushed to a registry (Docker Hub / ECR / GitHub Container Registry)
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
| `HEALTHCHECK` | Kubernetes and cloud platforms restart the container if it becomes unhealthy |
| `gunicorn` | Production-grade WSGI server; Flask's built-in server is not for production |

---

## Slide 7 — Understanding YAML

**YAML** (YAML Ain't Markup Language) is the format used for GitHub Actions workflows, Kubernetes manifests, Docker Compose files, and most CI/CD pipeline definitions. It is designed to be human-readable.

### Core syntax rules

**Indentation is structure.** YAML uses spaces (never tabs) to show nesting. Two spaces is standard.

```yaml
# This is a comment
name: my-workflow        # key: value (string)
enabled: true            # boolean
retries: 3               # integer
timeout: null            # null / empty value
```

**Lists** use a dash and a space:

```yaml
branches:
  - main
  - develop
  - feature/login
```

**Nested objects** are created by indenting under a key:

```yaml
jobs:
  build:               # job name (a key)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
```

**Multi-line strings** use `|` (preserves newlines) or `>` (folds into one line):

```yaml
# | keeps line breaks — used for shell scripts
run: |
  pip install -r requirements.txt
  pytest tests/

# > folds into one line — used for long descriptions
description: >
  This sentence continues
  on the next line.
```

**Curly braces** `${{ }}` are GitHub Actions expressions — they are evaluated at runtime:

```yaml
tags: ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
#         ↑ encrypted secret                    ↑ built-in variable
```

### The four top-level keys every GitHub Actions workflow has

```yaml
name:         # display name shown in the GitHub UI
on:           # what events trigger this workflow
permissions:  # what the workflow is allowed to do in the repo
jobs:         # the actual work — one or more named jobs
```

Each `job` contains `steps`. Each `step` is either a shell command (`run:`) or a prebuilt action (`uses:`):

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest   # the OS of the runner VM
    steps:
      - name: A shell command
        run: echo "hello"

      - name: A prebuilt action
        uses: actions/checkout@v4   # owner/repo@version
        with:                        # inputs to the action
          fetch-depth: 0
```

> **Why YAML for pipelines?** It is version-controlled alongside the code, human-readable without special tools, and supported natively by every major CI/CD platform.

---

## Slide 8 — GitHub Actions vs. Azure DevOps Pipelines

Both are full CI/CD platforms. The choice between them comes down to where your code lives and what ecosystem you are already in.

### GitHub Actions

- Pipeline files live in `.github/workflows/` as `.yml` files — version-controlled with the code
- Triggered by GitHub events: `push`, `pull_request`, `schedule`, `workflow_dispatch`, and more
- **Marketplace** of thousands of prebuilt actions (`actions/checkout`, `docker/login-action`, etc.)
- Free for public repositories; included minutes for private repos on paid plans
- The runner is a fresh VM (Ubuntu, Windows, or macOS) spun up for each job
- Secrets stored in repo or environment settings on GitHub

```
GitHub repo → push event → GitHub Actions runner (ubuntu-latest VM)
                                    │
                        reads .github/workflows/build-push.yml
                                    │
                        executes each step in order
```

### Azure DevOps Pipelines

- Pipeline file is `azure-pipelines.yml` at the repo root
- Tight integration with **Azure Boards** (work items), **Azure Repos** (git), and **Azure Artifacts** (packages)
- **Microsoft-hosted agents** or **self-hosted agents** running on your own infrastructure
- Enterprise-grade features: approval gates, audit logs, compliance policies, deployment groups
- Used extensively in organizations already on the Microsoft enterprise stack
- Can deploy to GitHub repos or Azure Repos equally

```
Azure Repos or GitHub repo → push → Azure Pipelines agent
                                            │
                                reads azure-pipelines.yml
                                            │
                              deploys to Azure services natively
```

### Side-by-side comparison

| Feature | GitHub Actions | Azure DevOps Pipelines |
|---|---|---|
| **Config file location** | `.github/workflows/*.yml` | `azure-pipelines.yml` |
| **Trigger syntax** | `on: push` | `trigger: branches:` |
| **Prebuilt components** | Actions (Marketplace) | Tasks (Azure DevOps extensions) |
| **Best for** | Open-source, GitHub-native projects | Enterprise, Microsoft-stack organizations |
| **Free tier** | Generous for public repos | 1,800 free minutes/month |
| **Self-hosted runners** | Yes | Yes (called agents) |
| **Approval gates** | GitHub Environments | Built-in deployment gates |
| **Work item tracking** | GitHub Issues | Azure Boards (more features) |

### This project uses GitHub Actions because:

- The code is hosted on GitHub
- Docker Hub integration is one action (`docker/login-action`)
- No Microsoft enterprise infrastructure is needed for this demo
- The workflow file lives next to the code — no external dashboard required

---

## Slide 9 — The GitHub Actions Workflow File

The pipeline lives at `.github/workflows/build-push.yml`. GitHub reads this file automatically on every push to `main`.

```yaml
name: Build & Push Flask Docker Image to Docker Hub

on:
  push:
    branches: [main]      # runs on every push to main
  workflow_dispatch:       # also allows manual trigger from GitHub UI

permissions:
  contents: read           # the workflow can read repo contents

jobs:
  build-and-push:
    runs-on: ubuntu-latest  # GitHub spins up a fresh Linux VM for each run
    environment: production # references GitHub environment secrets

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
            ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:latest

      - name: Logout from Docker Hub
        if: always()        # runs even if previous steps fail
        run: docker logout
```

---

## Slide 10 — Breaking Down the Pipeline Steps

Each step in the workflow serves a specific purpose:

### Step 1: Checkout code
```yaml
- uses: actions/checkout@v4
```
Clones the repository onto the GitHub-hosted runner VM. Without this, no other step has access to the code.

---

### Step 2: Set up Docker Buildx
```yaml
- uses: docker/setup-buildx-action@v3
```
Enables advanced Docker build features — including layer caching and multi-platform builds (e.g., `linux/amd64` and `linux/arm64` from the same pipeline). This step must run before any build or push step.

---

### Step 3: Login to Docker Hub
```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```
Authenticates the runner with Docker Hub so it can push images. The `${{ secrets.* }}` values are injected at runtime from GitHub's encrypted secret store — they are never visible in logs.

---

### Step 4: Build and Push
```yaml
tags: |
  ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
  ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:latest
```
The image gets **two tags** pushed simultaneously:
- `flask-app:abc1234` — the exact git commit SHA; makes every build traceable and allows rollback to any version
- `flask-app:latest` — a floating tag; deployment configs can always point to the newest build

---

### Step 5: Logout
```yaml
if: always()
run: docker logout
```
`if: always()` ensures cleanup runs even if the build failed. The runner VM is discarded after the job anyway, but logging out is good practice and a defence-in-depth habit.

---

## Slide 11 — Automated Testing in the Pipeline

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
| `test_health` | Health check endpoint returns `{"status": "ok"}` — used by Docker and Kubernetes |
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
Push to Docker Hub
```

To add tests to this workflow, insert these steps before the Docker Buildx step:

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

## Slide 12 — Secrets and Security

The workflow uses **GitHub Secrets** — encrypted values stored in repository or environment settings, never visible in logs or the YAML file itself.

### Secrets needed for this project:

| Secret name | What it holds |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username (e.g., `sola123`) |
| `DOCKERHUB_TOKEN` | A Docker Hub personal access token (not your password) |

### How to add them:

1. Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each one

### Why a token instead of a password:

- Tokens can be scoped (Read & Write only — no account access)
- Tokens can be revoked individually without changing your Docker Hub password
- If a token leaks, the blast radius is limited

### Security model:

```
GitHub Secrets (encrypted at rest, never in logs)
        │
        │  injected at runtime into the runner VM
        ▼
GitHub Actions runner (ephemeral — destroyed after job completes)
        │
        │  token used once to authenticate
        ▼
Docker Hub (accepts the push, stores the image)
```

The runner VM is thrown away after every job. Even if someone accessed the VM mid-run, the token is short-lived and the VM is gone immediately after.

---

## Slide 13 — Infrastructure as Code (IaaC) and CI/CD

**Infrastructure as Code (IaaC)** means defining cloud infrastructure in files (code) rather than clicking through a web console. CI/CD and IaaC are complementary — the same pipeline that deploys the app can also provision the infrastructure it runs on.

### Common IaaC tools:

| Tool | What it manages |
|---|---|
| **Terraform** | Cloud-agnostic — provisions resources on any major cloud from `.tf` files |
| **Bicep / ARM Templates** | Azure-native — defines Azure resources declaratively |
| **Pulumi** | IaaC using general-purpose languages (Python, TypeScript, Go) |
| **Ansible** | Configuration management — installs software, configures OS-level settings |
| **Helm** | Kubernetes package manager — deploys apps into clusters |

### IaaC in a GitHub Actions pipeline:

```yaml
jobs:
  provision:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
      - name: Terraform Apply
        run: |
          terraform init
          terraform apply -auto-approve -var="env=production"

  deploy:
    needs: provision      # waits for infrastructure to exist before deploying
    runs-on: ubuntu-latest
    steps:
      - name: Pull and run image from Docker Hub
        run: |
          docker pull myusername/flask-app:latest
          # deploy to whatever was just provisioned
```

> **The pipeline becomes the single source of truth** — both the infrastructure and the application are deployed through the same automated, audited process. No manual console clicks.

---

## Slide 14 — Docker Hub as the Registry

**Docker Hub** is the world's largest public container image registry, operated by Docker Inc. It is the default registry for the `docker pull` command.

### How Docker Hub fits into CI/CD:

```
GitHub Actions builds the image
        │
        ▼
docker push myusername/flask-app:latest
        │
        ▼
hub.docker.com/r/myusername/flask-app
        │
        ├── Any server can pull it:  docker pull myusername/flask-app:latest
        ├── Kubernetes can pull it:  image: myusername/flask-app:latest
        └── Cloud platforms can pull it automatically on deploy
```

### Key Docker Hub concepts:

| Concept | Meaning |
|---|---|
| **Repository** | A collection of images with the same name — `username/flask-app` |
| **Tag** | A label on a specific image version — `:latest`, `:abc1234` |
| **Public repo** | Anyone can pull — no credentials required |
| **Private repo** | Requires login to pull — free tier allows one private repo |
| **Personal access token** | A scoped credential used instead of a password in CI/CD |

### Image naming convention:

```
myusername/flask-app:abc1234
│           │         │
│           │         └── tag (git SHA or "latest")
│           └──────────── repository name
└──────────────────────── Docker Hub username (acts as the namespace)
```

### This project pushes two tags on every build:

```yaml
tags: |
  ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}  ← exact, immutable
  ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:latest              ← floating, always newest
```

Using the SHA tag means you can always redeploy any past version exactly as it was built.

---

## Slide 15 — The Full Deployment Flow (Docker Hub)

Here is how this project's pipeline fits into the broader deployment picture using Docker Hub:

```
Developer pushes code to GitHub (main branch)
        │
        ▼
GitHub Actions runner starts (ubuntu-latest VM)
        │
        ├── Checks out the code
        │
        ├── Sets up Docker Buildx
        │
        ├── Logs into Docker Hub (using DOCKERHUB_TOKEN)
        │
        ├── Builds Docker image (multi-stage Dockerfile)
        │
        └── Pushes image to Docker Hub with two tags:
                ├── flask-app:abc1234  (git SHA — immutable reference)
                └── flask-app:latest   (floating — always the newest build)
                        │
                        ▼
              hub.docker.com/r/username/flask-app
              (public or private repository)
                        │
            ┌───────────┼──────────────┐
            ▼           ▼              ▼
     Any Linux      Kubernetes     Cloud platform
     server         cluster        (Azure / AWS /
     (docker pull)  (image: ...)    GCP App Service)
```

### Extending this pipeline to deploy after push:

```yaml
- name: Deploy to a server via SSH
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USER }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      docker pull ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
      docker stop flask-app || true
      docker run -d --name flask-app -p 5000:5000 \
        ${{ secrets.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
```

---

## Slide 16 — CI/CD in Kubernetes Orchestration

When the deployment target is **Kubernetes**, CI/CD integrates with the orchestrator to achieve zero-downtime deployments:

### The Kubernetes deployment manifest:

```yaml
# k8s/deployment.yaml (stored in the repo alongside the app code)
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
          image: myusername/flask-app:latest   # updated by the pipeline
          ports:
            - containerPort: 5000
          livenessProbe:
            httpGet:
              path: /health    # our health endpoint — Kubernetes polls this
              port: 5000
```

### How the pipeline updates Kubernetes:

```yaml
# In build-push.yml, after the image push:

- name: Update Kubernetes deployment
  run: |
    kubectl set image deployment/flask-app \
      flask-app=myusername/flask-app:${{ github.sha }}
    kubectl rollout status deployment/flask-app
```

### Kubernetes features CI/CD relies on:

| Feature | Role in CI/CD |
|---|---|
| **Rolling updates** | New pods start before old ones stop — zero downtime |
| **Health checks** | Kubernetes uses our `/health` endpoint to validate new pods before routing traffic |
| **Rollback** | `kubectl rollout undo` reverts to the previous image SHA instantly |
| **Replica sets** | Multiple instances absorb traffic during a rolling update |

---

## Slide 17 — GitOps: The Next Level

**GitOps** is the practice of using git as the **single source of truth** for both application code and infrastructure state.

Instead of the pipeline directly calling `kubectl`, it updates a deployment manifest file in git, and a separate tool (like **Argo CD** or **Flux**) syncs the cluster to match.

```
Developer pushes app code
        │
        ▼
CI pipeline builds image, pushes to Docker Hub
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
- **Rollback**: `git revert` rolls back a deployment without touching the cluster directly
- **Separation of concerns**: CI builds; git stores desired state; the cluster syncs itself

---

## Slide 18 — The Application Routes and Their CI/CD Significance

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
        'description': 'A simple Flask app demonstrating CI/CD with Docker Hub.'
    })
```

| Route | CI/CD role |
|---|---|
| `/` | Basic smoke test — automated tests assert `Hello from Flask!` is present |
| `/health` | Health gate — Docker `HEALTHCHECK`, Kubernetes liveness probe, and cloud load balancers all poll this endpoint. If it fails, the deployment is halted. |
| `/api/info` | Metadata — useful for verifying the correct version is deployed; a post-deploy smoke test can assert `version == "1.0.0"` |

The `/health` endpoint is the most critical. Every layer of the deployment stack uses it:

```
Docker HEALTHCHECK  →  is the container alive?
Kubernetes liveness →  should this pod receive traffic?
Cloud load balancer →  is this instance healthy enough to serve requests?
Post-deploy test    →  did the deployment actually succeed?
```

---

## Slide 19 — Environment Promotion Strategy

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
    environment: production    # requires approval from a designated reviewer in GitHub
    steps:
      - ...
```

This project already uses `environment: production` in the workflow. In GitHub, go to **Settings → Environments → production** to configure required reviewers, wait timers, and branch restrictions.

---

## Slide 20 — Summary: The Complete Picture

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
│  2. Run pytest tests       (quality gate — fails fast)           │
│  3. Set up Docker Buildx   (enables caching + multi-platform)    │
│  4. Login to Docker Hub    (using DOCKERHUB_TOKEN secret)        │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                        CD STAGE (GitHub Actions)                 │
│                                                                  │
│  5. Build Docker image     (multi-stage Dockerfile)              │
│  6. Push to Docker Hub     (SHA tag + latest tag)                │
│  7. Deploy to cloud        (App Service / Kubernetes / server)   │
│  8. Health check validates (via /health endpoint)                │
│  9. Cleanup credentials    (docker logout)                       │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                        RUNNING IN THE CLOUD                      │
│                                                                  │
│  Image pulled from Docker Hub → Started by orchestrator          │
│  /health polled → Traffic routed if healthy                      │
│  Old containers terminated → Zero-downtime rollout complete      │
└─────────────────────────────────────────────────────────────────┘
```

### Key takeaways:

1. **CI/CD is a practice, not a product** — GitHub Actions, Azure DevOps, and Jenkins all implement the same ideas
2. **YAML is the universal language** — every CI/CD platform, Kubernetes, and Docker Compose use it; indentation is structure
3. **Docker is the packaging format** — it makes the build environment match the run environment
4. **Docker Hub is the handoff point** — CI pushes, deployment pulls the exact same image
5. **Tests are the quality gate** — without them, CI/CD just automates the delivery of broken code faster
6. **IaaC brings infrastructure into the same pipeline** — the whole system, not just the app, is version-controlled
7. **Health endpoints are a first-class concern** — every orchestration layer depends on `/health` to make deployment decisions
8. **Secrets never live in code** — GitHub Secrets inject credentials at runtime into ephemeral VMs

---

## Appendix — Quick Reference: Files in This Project

| File | Lines | Purpose |
|---|---|---|
| `.github/workflows/build-push.yml` | 34 | The full CI/CD pipeline definition |
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
*Flask GitHub Actions Demo — flask_github_actions_demo*
