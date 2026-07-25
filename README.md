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


## Scraper Agent

Fetches publication metadata for UniProt protein IDs using the UniProt REST API and a LangGraph pipeline.

### Install

```bash
pip install -e packages/scraper_agent
```

### Run

From a YAML config file (see `packages/scraper_agent/configs/ids.yaml`):

```bash
omicsmolnet-scraper --config packages/scraper_agent/configs/ids.yaml
```

Pass IDs directly on the command line:

```bash
omicsmolnet-scraper --ids A1A4S6 O43826 P02649
```

Combine both — results are merged and deduplicated:

```bash
omicsmolnet-scraper --config packages/scraper_agent/configs/ids.yaml --ids Q9Y6K9
```

Write results to a JSON file instead of stdout:

```bash
omicsmolnet-scraper --config packages/scraper_agent/configs/ids.yaml --output results.json
```

Increase log verbosity:

```bash
omicsmolnet-scraper --ids A1A4S6 --log-level DEBUG
```

### Run tests

```bash
python -m pytest packages/scraper_agent/tests/ -v
```
