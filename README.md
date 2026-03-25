# OmicsMolNet

## Tagline

Infrastructure for agent-driven biological research

### Description

OmicsMolNet is an AI-native platform that builds unified molecular interaction networks from multi-omics data, enabling autonomous research workflows through agentic AI and MCP-based integration.

## Development setup (pip + venv)

This repository is a single repo with multiple installable Python packages under `packages/`.

### One-time setup (bash)

Creates a virtual environment in `.venv` and installs all local packages in editable mode:

```bash
bash scripts/dev.sh
```

Activate the environment:

```bash
# Linux/macOS:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate
```

If your Python executable is not `python3`, you can override it:

```bash
PYTHON_BIN=python bash scripts/dev.sh
```
