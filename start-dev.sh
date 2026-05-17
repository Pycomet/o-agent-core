#!/bin/bash
set -e

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "Starting FastAPI on http://localhost:8000 ..."
python main.py
