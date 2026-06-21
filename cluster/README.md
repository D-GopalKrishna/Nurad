# MONAI Segmentation via Argo Workflows

This uses Docker Desktop's built-in Kubernetes (no separate cluster tooling
like `kind`/`minikube` needed) to run Argo Workflows alongside the main
`docker-compose.yml` stack.

## Architecture

- **Argo Workflows** runs in the `argo` namespace of Docker Desktop's
  Kubernetes cluster.
- **MONAI pipeline image** (`monai-pipeline/`): pulls a CT series from
  Orthanc, runs the MONAI Model Zoo `spleen_ct_segmentation` bundle, encodes
  the mask as a DICOM-SEG instance, and pushes it back into Orthanc. Runs as
  the single step of the `monai-spleen-segmentation` WorkflowTemplate.
- **Django** creates/polls `Workflow` custom resources **directly against the
  Kubernetes API server** (`https://kubernetes.docker.internal:6443`), not
  against Argo Server's own REST API. See "Why not Argo Server's API?" below.

## One-time setup

1. Enable Kubernetes in Docker Desktop settings, confirm with:
   ```
   kubectl config current-context   # should print: docker-desktop
   kubectl get nodes                # should show docker-desktop Ready
   ```

2. Install Argo Workflows:
   ```
   kubectl create namespace argo
   kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.6.5/quick-start-minimal.yaml
   kubectl wait --for=condition=available --timeout=120s deployment/argo-server deployment/workflow-controller -n argo
   ```
   Leave the `minio` deployment from this manifest running - the workflow
   controller uses it as the default artifact/log repository even though our
   pipeline doesn't declare any workflow artifacts itself; deleting it causes
   workflows to fail at the very end with an unrelated "failed to put file"
   error. `httpbin` is unused and safe to delete.

3. Grant the `default` ServiceAccount (in the `argo` namespace) permission to
   create/poll `Workflow` resources:
   ```
   kubectl apply -f cluster/django-client-rbac.yaml
   ```

4. Generate a bearer token for Django to authenticate with, and put it in `.env`:
   ```
   kubectl create token default -n argo --duration=87600h
   ```
   Set `ARGO_TOKEN=<that token>` in `.env` (see `.env.example`).
   `ARGO_SERVER_URL` defaults to `https://kubernetes.docker.internal:6443`.

5. Create the Orthanc credentials secret (see `orthanc-secret.yaml.example`
   for the shape - don't apply that file directly, it has placeholder creds):
   ```
   kubectl create secret generic orthanc-creds -n argo \
     --from-literal=username=<ORTHANC_USERNAME> \
     --from-literal=password=<ORTHANC_PASSWORD>
   ```

6. Build the MONAI pipeline image and apply the WorkflowTemplate:
   ```
   docker build -t monai-pipeline:latest ./monai-pipeline
   kubectl apply -f cluster/workflow-template.yaml
   ```
   No image push/load step needed - Docker Desktop's Kubernetes shares the
   same image store as `docker build`, unlike `kind` or `minikube`.

## Manual test (without Django)

```
argo submit --from workflowtemplate/monai-spleen-segmentation -n argo \
  -p study-instance-uid=<uid> -p series-instance-uid=<uid> --watch
```

## Why not Argo Server's own REST API?

The original plan was for Django to call Argo Server's REST API
(`/api/v1/workflows/...`) directly, exposed on `localhost:2746` via a
`LoadBalancer` Service. That works fine from the **Windows host** (e.g.
`curl http://localhost:2746/...`), but not from another Docker container:

- Docker Desktop's `LoadBalancer` service binding only listens on the
  Windows host's loopback interface, not on the Docker bridge network, so
  `host.docker.internal:2746` from another container gets a connection that
  resets immediately.
- `kubectl port-forward --address 0.0.0.0` (tried as a sidecar) accepts the
  connection but then the stream silently closes (Docker Desktop's
  WebSocket-based port-forward tunnel doesn't seem to complete properly in
  this setup).
- The API server's `services/proxy` and `pods/proxy` subresources (used by
  things like the K8s dashboard to reach in-cluster services) also fail with
  `error trying to reach service: EOF` - Docker Desktop's lightweight
  apiserver apparently can't open its own connection to a pod IP either.

What **does** work reliably from any container: plain CRUD against the API
server's CRD endpoints (e.g. `GET/POST .../apis/argoproj.io/v1alpha1/namespaces/argo/workflows`),
since that only needs etcd access, not a route to a pod's IP. Argo Workflows
natively supports referencing a `WorkflowTemplate` from a `Workflow` object's
`spec.workflowTemplateRef` field - the workflow controller (which *is* running
inside the cluster, so it can reach pods fine) resolves the template, with no
need to go through Argo Server at all. See `backend/worklist/argo_client.py`.

## Notes

- The MONAI pods reach Orthanc via `http://host.docker.internal:8042`
  (Orthanc's port is published to the host by `docker-compose.yml`). This
  direction works fine - it's a normal published container port, not a K8s
  Service, so none of the issues above apply.
