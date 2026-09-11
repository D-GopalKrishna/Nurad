# Nurad

Self-hosted DICOM worklist + viewer + AI segmentation, for local use.

- **backend** — Django + DRF worklist API, JWT auth, proxies DICOMweb to Orthanc
- **frontend** — React worklist (login, study list, "Open in Viewer", "Run AI Segmentation")
- **viewer** — OHIF, vendored and Nurad-themed
- **orthanc** — the actual DICOM server / PACS
- **db** — Postgres, backs the worklist API
- **monai-pipeline** + **cluster** — MONAI segmentation model, run as an Argo Workflow on a local Kubernetes cluster (Docker Desktop's built-in one)

## Quick start (core stack, no AI segmentation)

```
./run.sh up
```

This copies `.env.example` → `.env` on first run (edit the placeholder secrets before trusting it with real data), then builds and starts `db`, `orthanc`, `backend`, `frontend`, `viewer` via `docker-compose.yml`.

| Service  | URL                     |
|----------|-------------------------|
| frontend | http://localhost:5173   |
| viewer   | http://localhost:3030   |
| backend  | http://localhost:8000   |
| orthanc  | http://localhost:8042   |

Other `run.sh` commands: `down`, `status`, `logs [service]`.

## AI segmentation (optional, needs local Kubernetes)

The "Run AI Segmentation" button submits an Argo Workflow that runs a MONAI model against the study's CT series and writes the result back into Orthanc as a DICOM-SEG. This needs a one-time setup that the core stack doesn't need:

1. Follow **[cluster/README.md](cluster/README.md)** — enables Kubernetes in Docker Desktop, installs Argo Workflows, grants RBAC, generates an `ARGO_TOKEN`, builds the `monai-pipeline` image, applies the WorkflowTemplate.
2. Check it's all in place with:
   ```
   ./run.sh argo-check
   ```
3. Then `./run.sh up` as usual — the backend picks up `ARGO_SERVER_URL` / `ARGO_TOKEN` from `.env`.

Without this setup, the rest of the app (worklist, viewer) works fine — segmentation requests will just fail.

## Repo layout

```
backend/          Django API (worklist app: Study, SegmentationJob, Orthanc + Argo clients)
frontend/         React worklist UI
viewer/           OHIF viewer (vendored fork)
orthanc/          Orthanc config + theme
monai-pipeline/   Segmentation container (pulls CT, runs MONAI, writes DICOM-SEG)
cluster/          Argo Workflows manifests + local-k8s setup notes
```
