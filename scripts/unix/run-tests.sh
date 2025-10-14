#!/usr/bin/env bash
set -euo pipefail

# Run with coverage with github actions:: coverage run --data-file=data.coverage -m
. ../../.venv/bin/activate
exec python3 -m pytest ../../src/mainpkg/tests
