#!/usr/bin/env bash

set -euo pipefail

echo Starting ...
. ../../.venv/bin/activate
exec python3 ../../src/app/main.py
