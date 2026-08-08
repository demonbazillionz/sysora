#!/bin/bash

echo "================================"
echo "       Sysora Installer"
echo "================================"
echo

echo "Checking Python..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is not installed."
    echo "Please install Python 3 first."
    exit 1
fi

echo "Python found!"
echo

echo "Creating virtual environment..."

python3 -m venv .venv

echo
echo "Installing dependencies..."

source .venv/bin/activate
pip install -r requirements.txt

echo
echo "================================"
echo "   Sysora installed successfully!"
echo "================================"
echo
echo "Start Sysora with:"
echo "./run.sh"
