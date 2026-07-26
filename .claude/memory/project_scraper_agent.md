---
name: project-scraper-agent
description: Context for the omicsmolnet-scraper-agent package — UniProt publication pipeline built with LangGraph
metadata: 
  node_type: memory
  type: project
  originSessionId: 6574d139-aceb-42f3-92ac-6a3e0f8c674f
---

New package `packages/scraper_agent/` (module `omicsmolnet_scraper_agent`) added to the monorepo.

**Purpose:** Fetch publication metadata for UniProt protein IDs, extract PubMed links, and (Phase 2) download PDFs.

**Pipeline:**
1. Load IDs from `configs/ids.yaml` (starting IDs: A1A4S6, O43826, P02649)
2. Fan-out per ID via LangGraph `Send` API
3. Fetch from UniProt REST API: `https://rest.uniprot.org/uniprotkb/{ID}/publications`
4. Route: if all pubs have pubmed_url/doi → collect; otherwise → LLM resolution agent
5. PDF download: Phase 2 stub only

**Key files:**
- `src/omicsmolnet_scraper_agent/state.py` — `ScraperState`, `IdState`, `Publication` TypedDicts
- `src/omicsmolnet_scraper_agent/tools/scraper.py` — deterministic UniProt REST client
- `src/omicsmolnet_scraper_agent/agents/publication_search_agent.py` — LLM ReAct agent (tool stubs need implementing)
- `src/omicsmolnet_scraper_agent/graph.py` — StateGraph with `Send` fan-out
- `src/omicsmolnet_scraper_agent/cli.py` — `omicsmolnet-scraper` entry point

**CLI:** `omicsmolnet-scraper --config configs/ids.yaml` or `--ids A1A4S6 O43826`

**Why:** User requested a LangGraph agentic pipeline for scraping UniProt publications with mixed deterministic + LLM agents.

**How to apply:** When user asks to extend the scraper pipeline (add PDF download, fix agent tools, add new agents), start from these files.
