#!/bin/bash
set -e
cd -- "$(dirname -- "$0")"
python3 scripts/serve.py --open
