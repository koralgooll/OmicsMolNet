#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: '$PYTHON_BIN' not found. Set PYTHON_BIN=python if needed." >&2
  exit 1
fi

echo "[dev.sh] Creating venv at: $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "[dev.sh] Activating venv"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # Linux/macOS venv layout
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
elif [[ -f "$VENV_DIR/Scripts/activate" ]]; then
  # Windows venv layout (Git Bash/MSYS/MINGW)
  # shellcheck disable=SC1090
  source "$VENV_DIR/Scripts/activate"
else
  echo "ERROR: Could not find venv activation script in:" >&2
  echo "  - $VENV_DIR/bin/activate" >&2
  echo "  - $VENV_DIR/Scripts/activate" >&2
  echo "Venv creation may have failed. Try: $PYTHON_BIN -m venv $VENV_DIR" >&2
  exit 1
fi

echo "[dev.sh] Upgrading pip"
python -m pip install --upgrade pip

echo "[dev.sh] Installing OmicsMolNet packages (editable)"
pip install -e packages/core
pip install -e packages/data
pip install -e packages/agent_graph
pip install -e packages/mcp_server
pip install -e packages/cli

echo "[dev.sh] Done."
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  echo "[dev.sh] Activate later with: source $VENV_DIR/bin/activate"
else
  echo "[dev.sh] Activate later with: source $VENV_DIR/Scripts/activate"
fi

