#!/usr/bin/env bash
# Convenience wrapper around the pieces you need to run Nurad locally.
# See README.md for what each command does and does not cover.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

cmd="${1:-up}"

ensure_env() {
  if [ ! -f .env ]; then
    echo "No .env found — copying .env.example -> .env"
    echo "Edit .env before relying on this for anything but local dev (default secrets are placeholders)."
    cp .env.example .env
  fi
}

case "$cmd" in
  up)
    ensure_env
    docker compose up --build
    ;;
  down)
    docker compose down
    ;;
  status)
    docker compose ps
    ;;
  logs)
    docker compose logs -f "${2:-}"
    ;;
  argo-check)
    echo "== kubectl context =="
    kubectl config current-context || { echo "kubectl not configured"; exit 1; }
    echo
    echo "== docker-desktop node =="
    kubectl get nodes
    echo
    echo "== argo namespace =="
    kubectl get deployment -n argo argo-server workflow-controller 2>/dev/null \
      || echo "argo namespace/deployments not found — run the one-time setup in cluster/README.md"
    echo
    echo "== workflow template =="
    kubectl get workflowtemplate -n argo monai-spleen-segmentation 2>/dev/null \
      || echo "monai-spleen-segmentation WorkflowTemplate not applied — see cluster/README.md step 6"
    echo
    if [ -f .env ] && grep -q '^ARGO_TOKEN=change-me$' .env; then
      echo "ARGO_TOKEN in .env is still the placeholder — generate one (cluster/README.md step 4)"
    fi
    ;;
  *)
    echo "usage: ./run.sh {up|down|status|logs [service]|argo-check}"
    exit 1
    ;;
esac
