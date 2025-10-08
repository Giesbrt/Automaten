#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "../.venv" ]; then
  python3 -m venv .venv
  python3 -m pip install --upgrade pip
  python3 -m pip install -r ../requirements.txt
fi

source ../.venv/bin/activate

# Run with coverage with github actions:: coverage run --data-file=data.coverage -m
pytest ../test
