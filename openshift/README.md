# Shaman on OpenShift — Quick Start

This guide helps you build and deploy **Shaman** on OpenShift using the provided manifests.

---

## Prerequisites

- OpenShift cluster access and `oc` CLI installed.
- Logged in to the right cluster:  
  ```bash
  oc whoami
  oc project

Need sufficient permissions to create namespace/projects, routes, deployments, and PVCs.

## All commands below assume the namespace is shaman.

1. (One‑time) Create the namespace
``` 
oc apply -f openshift/deploy/namespace.yaml
```
2. Build pipeline (ImageStream + BuildConfigs)
```
oc -n shaman apply -f openshift/build/
```
3. (a) Build from upstream Git
```
oc -n shaman start-build bc/shaman-git --follow
```
3. (b) OR build from your working tree (binary build)

Use this when you want to build the image from your local repo state.
```
oc -n shaman start-build bc/shaman-binary --from-dir=. --follow
```
4. Deploy infra and app configs

Apply app configuration, secrets, and infra components (Postgres, RabbitMQ, PVC):
```
oc -n shaman apply -f openshift/deploy/configmap.yaml
oc -n shaman apply -f openshift/deploy/secret.yaml
oc -n shaman apply -f openshift/deploy/postgres.yaml
oc -n shaman apply -f openshift/deploy/rabbitmq.yaml
oc -n shaman apply -f openshift/deploy/postgres-pvc.yaml
```
5. Run DB migrations (Alembic → Postgres)
```
oc -n shaman apply -f openshift/deploy/migration-job.yaml
oc -n shaman wait --for=condition=complete job/shaman-migrate --timeout=180s
```
6. Deploy Shaman API and static assets
```
oc -n shaman apply -f openshift/deploy/deployment.yaml
oc -n shaman apply -f openshift/deploy/service.yaml
oc -n shaman apply -f openshift/deploy/route.yaml
oc -n shaman apply -f openshift/deploy/shaman-static.yaml
```
The shaman-static.yaml serves CSS/JS over a path-based Route (e.g., /static).

The Shaman API itself is exposed by the shaman Route.

7. Verify the rollout

Wait for the Shaman API deployment to be ready
```
oc -n shaman rollout status deploy/shaman
```
Get the public host
```
oc -n shaman get route shaman -o jsonpath='{.spec.host}{"\n"}'
```
Open the URL in your browser:
```
https://<printed-host>/
```
---
## Quick checks

1. API root:
```
curl -k -I "https://<printed-host>/api/"
```
2. (If you used the static server) CSS/JS:
```
curl -k -I "https://<printed-host>/static/css/bootstrap.min.css"
```
