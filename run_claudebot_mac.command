#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv-mac ]; then
  python3 -m venv .venv-mac
fi

source .venv-mac/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m claudebot run "$@"
