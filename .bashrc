#!/usr/bin/env bash

# Repo-local Git Bash init (used by Cursor/VS Code terminal via --rcfile).
# Auto-activate .venv when opening a terminal in this workspace.

if [[ -z "${OMN_VENV_AUTOACTIVATE_DONE:-}" ]]; then
  export OMN_VENV_AUTOACTIVATE_DONE=1

  if [[ -f ".venv/Scripts/activate" ]]; then
    # Windows venv layout (Git Bash/MSYS/MINGW)
    # shellcheck disable=SC1091
    source ".venv/Scripts/activate"
  elif [[ -f ".venv/bin/activate" ]]; then
    # Linux/macOS venv layout
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
  fi
fi

