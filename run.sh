#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Sysora is not installed yet."
    echo
    echo "Run:"
    echo "    ./install.sh"
    exit 1
fi

source .venv/bin/activate

python app.py
