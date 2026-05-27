#!/usr/bin/env bash
set -e

if [ -f ".venv/bin/activate" ]; then
  . ".venv/bin/activate"
elif [ -f "venv/bin/activate" ]; then
  . "venv/bin/activate"
fi

python -m uvicorn app.main:app --reload
