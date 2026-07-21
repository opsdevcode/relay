#!/usr/bin/env bash
# Render templates/k8s-service into DEST from env: SERVICE_NAME, GITHUB_ORG, DESCRIPTION, OWNER
set -euo pipefail

: "${SERVICE_NAME:?SERVICE_NAME required}"
: "${DEST:?DEST required}"

GITHUB_ORG="${GITHUB_ORG:-opsdevcode}"
DESCRIPTION="${DESCRIPTION:-Containerized service}"
OWNER="${OWNER:-platform-team}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/templates/k8s-service"

mkdir -p "$DEST/deploy/k8s" "$DEST/src"

subst() {
  sed \
    -e "s/{{ service_name }}/${SERVICE_NAME}/g" \
    -e "s/{{ github_org }}/${GITHUB_ORG}/g" \
    -e "s/{{ description | default(\"Containerized service\") }}/${DESCRIPTION}/g" \
    -e "s/{{ owner | default(\"platform-team\") }}/${OWNER}/g"
}

subst < "$TEMPLATE/catalog-info.yaml" > "$DEST/catalog-info.yaml"
subst < "$TEMPLATE/Dockerfile" > "$DEST/Dockerfile"
subst < "$TEMPLATE/README.md" > "$DEST/README.md"
subst < "$TEMPLATE/src/main.py" > "$DEST/src/main.py"
subst < "$TEMPLATE/deploy/k8s/manifests.yaml" > "$DEST/deploy/k8s/manifests.yaml"

echo "Rendered $SERVICE_NAME -> $DEST"
