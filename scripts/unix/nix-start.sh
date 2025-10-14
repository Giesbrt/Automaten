#!/usr/bin/env bash

set -euo pipefail

echo Starting ...
exec ../../.nixpy/bin/python ../../src/app/main.py
