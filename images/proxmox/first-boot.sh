#!/bin/sh
set -eu

LOG_FILE="/var/log/k8s-tests-first-boot.log"
STORAGE_ID="local"
REQUIRED_CONTENT="backup,iso,vztmpl,snippets,import"

{
  echo "Starting k8s-tests first boot configuration: $(date -Is)"

  if command -v pvesm >/dev/null 2>&1; then
    pvesm set "${STORAGE_ID}" --content "${REQUIRED_CONTENT}"
    echo "Configured storage '${STORAGE_ID}' content types: ${REQUIRED_CONTENT}"
  else
    echo "ERROR: pvesm command not found"
    exit 1
  fi

  echo "Completed k8s-tests first boot configuration: $(date -Is)"
} >>"${LOG_FILE}" 2>&1
