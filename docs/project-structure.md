‏<div dir="rtl">

‏snake-k8s-pipeline
‏├── backend
‏│   ├── app
‏│   │   └── main.py
‏│   ├── Dockerfile
‏│   ├── pytest.ini
‏│   ├── requirements-dev.txt
‏│   ├── requirements.txt
‏│   └── tests
‏│       ├── conftest.py
‏│       └── test_api.py
‏├── docker-compose.yml
‏├── frontend
‏│   ├── Dockerfile
‏│   ├── index.html
‏│   └── nginx.conf
‏├── gitlab-ci.yml
‏└── k8s
‏    ├── configmap.yaml
‏    ├── frontend-deployment.yaml
‏    ├── frontend-service.yaml
‏    ├── game-api-deployment.yaml
‏    ├── game-api-service.yaml
‏    ├── ingress.yaml
‏    ├── redis-deployment.yaml
‏    ├── redis-pvc.yaml
‏    ├── redis-secret.yaml
‏    ├── redis-service.yaml
‏    └── storageclass.yaml


‏</div>
