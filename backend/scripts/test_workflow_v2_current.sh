#!/usr/bin/env bash
set -euo pipefail

backend_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${WORKFLOW_V2_TEST_IMAGE:-luceonweb2026-review-backend:local}"
if [[ "$#" -eq 0 ]]; then
  set -- tests/test_workflow_v2_runtime_assets.py
fi

exec docker run --rm \
  -v "${backend_dir}:/app" \
  -w /app \
  "${image}" \
  pytest -q "$@"
