# OmicsMolNet


## Tagline

Infrastructure for agent-driven biological research


### Description

OmicsMolNet is an AI-native platform that builds unified molecular interaction networks from multi-omics data, enabling autonomous research workflows through agentic AI and MCP-based integration.


## Prerequisites

- **Python 3.11 or newer** — check with `python3 --version`
- **Anthropic API key** — required only for the LLM fallback step in Phase 1 (resolving publications that have no PubMed URL). Export before running:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without the key, Phase 1 still works for all publications that have a PubMed URL directly in the UniProt API response. Only the rare missing-URL cases are skipped.

- **Unpaywall email** — optional but recommended for Phase 2. Unpaywall requires a contact email to serve PDF URLs (100 000 calls/day per address):

```bash
export UNPAYWALL_EMAIL=you@example.com
```

Without it, Phase 2 still runs but skips the Unpaywall PDF path and falls back to CrossRef and PMC sources only.


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


## Phase 1 — Scraper Agent

Fetches publication metadata for UniProt protein IDs using the UniProt REST API
and a LangGraph pipeline. For each ID it returns titles, authors, journal, year,
PubMed URLs, and DOIs. When a publication has no PubMed URL in the UniProt data,
an LLM chain attempts to resolve it.


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

Save output to a JSON file (required as input to Phase 2):

```bash
omicsmolnet-scraper --ids A1A4S6 --output results.json
```

Show debug logs (every HTTP request, URL, and resolution step):

```bash
omicsmolnet-scraper --ids A1A4S6 --log-level DEBUG
```


### Output format

Results are a JSON array, one object per protein ID:

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

`resolved_url` is populated by the LLM chain for publications where both `pubmed_url`
and `doi` are `null`. `errors` lists any fetch failures for that ID.


## Phase 2 — Full-Text Download

Takes the JSON produced by Phase 1 and attempts to download open-access full texts
for each publication. Two independent paths are tried in parallel:

- **PDF path** — Unpaywall (by DOI) → CrossRef fallback
- **XML path** — Europe PMC (by PMID) → NCBI OA Web Service (by PMCID)

Whatever is available gets downloaded; neither path blocks the other.


### Usage

Explore all options:

```bash
omicsmolnet-pdf --help
```

Download full texts to a directory, writing updated results to a new file:

```bash
omicsmolnet-pdf --input results.json --output-dir ./out/ --output results_with_pdfs.json
```

Print updated results to stdout instead of a file:

```bash
omicsmolnet-pdf --input results.json --output-dir ./out/
```

Show debug logs:

```bash
omicsmolnet-pdf --input results.json --output-dir ./out/ --log-level DEBUG
```

Downloaded files are placed in two subdirectories created automatically:

```
out/
  pdf/   ← downloaded PDFs
  xml/   ← downloaded XML full-text packages (.tgz or .xml)
```


### Output format

Each publication gains six additional fields after Phase 2:

```json
{
  "title": "PKNbeta interacts with the SH3 domains of Graf ...",
  "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/11432776/",
  "doi": "10.1093/oxfordjournals.jbchem.a002958",
  "is_open_access": true,
  "oa_status": "gold",
  "pdf_url": "https://...",
  "pdf_path": "/abs/path/to/out/pdf/paper.pdf",
  "xml_url": "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa/...",
  "xml_path": "/abs/path/to/out/xml/PMC123456.tar.gz"
}
```

`pdf_path` and `xml_path` are `null` when the article is not open access or the
download failed. `oa_status` reflects the Unpaywall classification (`"gold"`,
`"hybrid"`, `"bronze"`, `"green"`, or `"closed"`).


## End-to-end pipeline

Run Phase 1 once, then Phase 2 separately — or re-run Phase 2 without repeating
the UniProt API calls:

```bash
# Phase 1: fetch metadata
omicsmolnet-scraper --ids P02649 A1A4S6 --output phase1.json

# Phase 2: download open-access full texts
omicsmolnet-pdf --input phase1.json --output-dir ./out/ --output phase2.json
```


## Run tests

```bash
python -m pytest packages/scraper_agent/tests/ -v
```
