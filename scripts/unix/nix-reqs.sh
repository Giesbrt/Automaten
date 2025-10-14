#!/usr/bin/env bash

set -euo pipefail

echo Installing/Checking Packages ...
exec ../../.nixpy/bin/python -m pip install -r ../../requirements.txt
