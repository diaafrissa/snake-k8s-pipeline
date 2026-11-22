# 🐍 Automated GitOps, K8s & CI/CD Pipeline for Phosphor Snake Arcade Game

**Repositories:** `snake-game` (Application & CI) | `Gitops-infra` (GitOps Manifests)

A complete, production-ready DevOps implementation of a microservice-based Retro CRT Snake Game deployed on **Kubernetes (`K8s` / `k3s`)**. Built following DevOps, GitOps, Security, and Observability best practices, featuring automated testing, Docker builds, automated manifest tag updates (`[skip ci]`), Argo CD reconciliation, automated SSL/TLS encryption, and Prometheus/Grafana monitoring.

## 🌐 Live URL
- **Live Application URL (HTTPS/TLS Encrypted):** [https://snake-game.duckdns.org](https://snake-game.duckdns.org)
- **GitOps Repository:** [gitlab.com/diaa.frissan.1-group/Gitops-infra](https://gitlab.com/diaa.frissan.1-group/Gitops-infra.git)

## 🏗️ Pipeline & GitOps Flow
`Code Change → Git Push → Test (backend/**) → Build & Push Images → Update k8s/ Tags ([skip ci]) → Argo CD Sync → K8s Cluster`

- **Test (`test`):** Runs `pytest` unit tests in an isolated `python:3.12-slim` container (`set -eou pipefail`) when `backend/**/*` changes.
- **Build & Update (`build-and-update` on `main`):** Builds and pushes Docker images (`game-api` & `frontend`) tagged with `$CI_COMMIT_SHORT_SHA` and `latest` to GitLab Registry, updates image tags in `k8s/*.y*ml` via `sed`, and pushes back with `[skip ci]`.
- **Reconcile (GitOps):** **Argo CD** (App of Apps) monitors manifests and synchronizes the **Kubernetes (`K8s` / `k3s`)** cluster with automated sync, pruning, and self-healing.

## 📁 Repository Structure
```text
.
├── backend/
│   ├── app/
│   │   └── main.py                      # FastAPI application, /metrics & Redis lifecycle
│   ├── Dockerfile                       # Python container build
│   ├── pytest.ini                       # Pytest configuration
│   ├── requirements-dev.txt             # Testing & development dependencies
│   ├── requirements.txt                 # Production dependencies
│   └── tests/
│       ├── conftest.py                  # Test fixtures & mocks
│       └── test_api.py                  # API test suite
├── docker-compose.yml                   # Local development multi-container stack
├── frontend/
│   ├── Dockerfile                       # Nginx container build
│   ├── index.html                       # HTML5 Canvas UI & Arcade game engine
│   └── nginx.conf                       # Nginx reverse proxy & /healthz config
├── gitlab-ci.yml                        # GitLab CI/CD pipeline (test & build-and-update)
└── k8s/                                 # Kubernetes (K8s) manifests
    ├── cluster-issuser.yaml             # Cert-Manager Let's Encrypt issuer
    ├── configmap.yaml                   # Application configuration variables
    ├── frontend-deployment.yaml         # Frontend deployment & service
    ├── game-api-deployment.yaml         # Backend API deployment & service
    ├── game-api-servicemonitor.yaml     # Prometheus ServiceMonitor for /metrics
    ├── ingress.yaml                     # Traefik ingress rules & TLS routing
    ├── redirect-middleware.yaml         # HTTP-to-HTTPS redirect middleware
    ├── redis-deployment.yaml            # Redis stateful deployment (Recreate)
    ├── redis-pvc.yaml                   # ReadWriteOnce Persistent Volume Claim
    ├── redis-secret.yaml                # Encrypted Redis authentication credentials
    └── storageclass.yaml                # Rancher Local-Path StorageClass (snake-path)

```

## 🛠️ Tech Stack & DevOps Tools

* **App & DB:** Python 3.12 (FastAPI), HTML5 Canvas, Nginx 1.27 Alpine, Redis 7 (AOF Persistence)
* **CI/CD & GitOps:** GitLab CI/CD (`vps` Runner), GitLab Container Registry, Argo CD (App of Apps)
* **Orchestration & Network:** Kubernetes (`K8s` / `k3s`), Traefik Ingress Controller, Dynamic DNS (DuckDNS)
* **Security & SSL/TLS:** Cert-Manager, Let's Encrypt (TLS 1.3), K8s Secrets
* **Monitoring & Testing:** Helm, `kube-prometheus-stack` (Prometheus & Grafana), ServiceMonitor, Redis Exporter, Pytest, Fakeredis

## 🔒 Security & DevOps Best Practices

* **GitOps Reconciliation (`Argo CD`):** Declarative cluster reconciliation with automated sync, pruning, and self-healing.
* **CI/CD Safety (`set -eou pipefail`):** Enforced in test scripts to exit immediately on errors, with `[skip ci]` on automated manifest commits.
* **Automated SSL/TLS:** Cert-Manager provisions Let's Encrypt certificates with HTTP-to-HTTPS (301) redirection via Traefik.
* **Secrets Isolation:** Sensitive credentials (Redis auth, `PROJECT_PUSH_TOKEN`, registry credentials) are injected via K8s Secrets and GitLab CI/CD variables.
* **Hardened Workloads:** Minimal base images (`python:3.12-slim`, `nginx:alpine`) with `/healthz`, `/api/health`, and `/api/ready` probes.

## ⚙️ Environment Variables Configured in GitLab CI

* `BACKEND_IMAGE`: `$CI_REGISTRY_IMAGE/game-api`
* `FRONTEND_IMAGE`: `$CI_REGISTRY_IMAGE/frontend`
* `PROJECT_PUSH_TOKEN`: Push token used over `https://oauth2:${PROJECT_PUSH_TOKEN}@...` to commit updated `k8s/` image tags to `main`
* `CI_REGISTRY_USER` / `CI_REGISTRY_PASSWORD`: Container Registry authentication credentials

## 🚀 Local Development & Setup

**Prerequisites:** Python 3.12+, Docker & Docker Compose

**Running Locally with Docker Compose:**

```bash
docker compose -f docker-compose.yml up --build
# Frontend UI: http://localhost:8080

```

**Running Backend Tests Locally:**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
pytest

```