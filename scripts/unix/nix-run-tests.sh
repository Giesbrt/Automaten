#!/usr/bin/env bash
set -euo pipefail

../../.nixpy/bin/python -m pip install pytest-cov

# Run with coverage with github actions:: coverage run --data-file=data.coverage -m
exec ../../.nixpy/bin/python -m pytest \
    --cov=../../src/mainpkg \
    --cov-report=term-missing \
    ../../src/mainpkg/tests
