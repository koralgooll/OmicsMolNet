# OmicsMolNet


## Tagline

Infrastructure for agent-driven biological research


### Description

OmicsMolNet is an AI-native platform that builds unified molecular interaction networks from multi-omics data, enabling autonomous research workflows through agentic AI and MCP-based integration.


## Prerequisites

- **Python 3.11 or newer** — check with `python3 --version`
- **Anthropic API key** — required only for the LLM fallback step in the scraper agent (resolving publications that have no PubMed URL). Export before running:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without the key, the scraper still works for all publications that have a PubMed URL directly in the UniProt API response. Only the rare missing-URL cases are skipped.


## Development setup (pip + venv)

This repository is a single repo with multiple installable Python packages under `packages/`.


### One-time setup

Creates a virtual environment in `.venv` and installs all local packages in editable mode:

```bash
bash scripts/dev.sh
```

If your Python executable is not `python3`, override it:

```bash
PYTHON_BIN=python bash scripts/dev.sh
```


### Activate the environment

Run this in every new terminal session before using any CLI commands or running tests:

```bash
# Linux/macOS:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate
```


## Scraper Agent

Fetches publication metadata for UniProt protein IDs using the UniProt REST API
and a LangGraph pipeline. For each ID it returns titles, authors, journal, year,
PubMed URLs, and DOIs. When a publication has no PubMed URL in the UniProt data,
an LLM agent attempts to resolve it.


### Usage

Explore all options:

```bash
omicsmolnet-scraper --help
```

Run from a YAML config file (see `packages/scraper_agent/configs/ids.yaml`):

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

Save output to a JSON file instead of printing to the terminal:

```bash
omicsmolnet-scraper --ids A1A4S6 --output results.json
```

Show debug logs (every HTTP request, URL, and resolution step):

```bash
omicsmolnet-scraper --ids A1A4S6 --log-level DEBUG
```


### Output format

Results are printed as a JSON array, one object per protein ID:

```json
[
  {
    "id": "A1A4S6",
    "publications_url": "https://www.uniprot.org/uniprotkb/A1A4S6/publications",
    "publications": [
      {
        "title": "PKNbeta interacts with the SH3 domains of Graf ...",
        "authors": ["Shibata H.", "Oishi K.", "Yamagiwa A."],
        "journal": "J. Biochem.",
        "year": 2001,
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/11432776/",
        "doi": "10.1093/oxfordjournals.jbchem.a002958",
        "other_links": [],
        "resolved_url": null
      }
    ],
    "errors": []
  }
]
```

`resolved_url` is populated by the LLM agent for publications where `pubmed_url`
is `null` and `doi` is `null`. `errors` lists any fetch failures for that ID.


### Run tests

```bash
python -m pytest packages/scraper_agent/tests/ -v
```
