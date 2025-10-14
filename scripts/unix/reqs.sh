#!/usr/bin/env bash

set -euo pipefail

echo Installing/Checking Packages ...
. ../../.venv/bin/activate
exec python3 -m pip install -r ../../requirements.txt
