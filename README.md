# Automated K8s & CI/CD Pipeline for Phosphor Snake Arcade Game

`Repository Name: snake-k8s-pipeline`

A complete, production-ready DevOps implementation of a microservice-based Retro CRT Snake Game deployed on **Kubernetes**. Built following **DevOps, Security & CI/CD Best Practices**, the pipeline features automated unit testing, multi-container Docker image construction, strict shell execution safety, automated **SSL/TLS encryption**, and zero-downtime rolling deployments to a self-hosted VPS cluster.

---

## 🌐 Live URL 
- **Live Application URL (HTTPS/TLS Encrypted):** [Open the application](https://snake-game.duckdns.org)

---

## 🏗️ Pipeline

any code Change → Git Push → Test → Build & Push Images → Secure K8s Deployment

• **Test:** Runs `pytest` unit tests in an isolated Python container.

• **Build:** Builds and pushes Docker images (`game-api` & `frontend`) to GitLab Registry tagged with `$CI_COMMIT_SHORT_SHA`.

• **Deploy:** Applies K8s manifests and executes zero-downtime rolling updates (`kubectl rollout`).

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   └── main.py                  # FastAPI application & Redis lifecycle
│   ├── Dockerfile                   # Python container build
│   ├── pytest.ini                   # Pytest configuration
│   ├── requirements-dev.txt         # Testing & development dependencies
│   ├── requirements.txt             # Production dependencies
│   └── tests/
│       ├── conftest.py              # Test fixtures & mocks
│       └── test_api.py              # API test suite
├── docker-compose.yml               # Local development multi-container stack
├── frontend/
│   ├── Dockerfile                   # Nginx container build
│   ├── index.html                   # HTML5 Canvas UI & Arcade game engine
│   └── nginx.conf                   # Nginx reverse proxy configuration
├── gitlab-ci.yml                    # GitLab CI/CD pipeline definition
└── k8s/                             # Kubernetes manifests
    ├── cluster-issuser.yaml         # Cert-Manager Let's Encrypt issuer
    ├── configmap.yaml               # Application configuration variables
    ├── frontend-deployment.yaml     # Frontend deployment & service
    ├── game-api-deployment.yaml     # Backend API deployment & service
    ├── ingress.yaml                 # Traefik ingress rules & TLS routing
    ├── redirect-middleware.yaml     # HTTP-to-HTTPS redirect middleware
    ├── redis-deployment.yaml        # Redis stateful deployment
    ├── redis-pvc.yaml               # Persistent Volume Claim
    ├── redis-secret.yaml            # Encrypted Redis authentication credentials
    └── storageclass.yaml            # Rancher Local-Path StorageClass
```
---

## 🛠️ Tech Stack & DevOps Tools

- **App & DB:** Python 3.12 (FastAPI), HTML5 Canvas, Nginx 1.27 Alpine, Redis 7 (AOF Persistence)
- **CI/CD & Registry:** GitLab CI/CD, GitLab Container Registry
- **Orchestration & Network:** Kubernetes, Traefik Ingress Controller, Dynamic DNS (DuckDNS)
- **Security & SSL/TLS:** Cert-Manager, Let's Encrypt (TLS 1.3), K8s Secrets
- **Testing & Tooling:** Pytest, Fakeredis, Docker Engine

---

## 🔒 Security & DevOps Best Practices

- **CI/CD Safety (`set -eou pipefail`)**: Enforced in pipeline scripts to exit immediately on error, undefined variables, or piped command failure.
- **Automated SSL/TLS**: Cert-Manager provisions Let's Encrypt certificates with HTTP-to-HTTPS (301) redirection via Traefik.
- **Secrets Isolation**: Sensitve credentials (Redis auth, authentication tokens, kubeconfig) are injected via K8s Secrets and masked GitLab CI/CD variables.
- **Hardened Workloads**: Minimal base images (`python:3.12-slim`, `nginx:alpine`) with explicit K8s Liveness and Readiness probes.

---

## ⚙️Environment Variables Configured in GitLab CI:

- BACKEND_IMAGE: `$CI_REGISTRY_IMAGE/game-api`

- FRONTEND_IMAGE: `$CI_REGISTRY_IMAGE/frontend`

- KUBECONFIG: `/kube/config` (Masked file variable containing cluster connection credentials)

- CI_REGISTRY_USER / CI_REGISTRY_PASSWORD: Masked Container Registry authentication tokens

---

## 🚀 Local Development & Setup

Prerequisites:
Python 3.12+

Docker & Docker Compose installed locally

### Running Locally with Docker Compose

Bash:

- **Start all microservices**
  ```bash
  docker compose -f docker-compose.yml up --build
  ```

- **Access Local Endpoints**
  ```bash
  # Frontend UI: http://localhost:8080
  ```

### Running Backend Tests Locally

Bash:

- **Install dependencies**
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements-dev.txt
  ```

- **Execute Unit Tests**
  ```bash
  pytest
  ```