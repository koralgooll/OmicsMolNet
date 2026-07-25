"""LangGraph StateGraph for the UniProt publication scraping pipeline.

Topology:
  START → load_ids → [fan-out via Send] → process_id → route
                                                         ├─ all resolved → collect
                                                         └─ some missing → resolve_missing → collect
                                                                                              └─ END
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from omicsmolnet_scraper_agent.agents.publication_search_agent import (
    resolve_missing_publications,
)
from omicsmolnet_scraper_agent.config import load_config
from omicsmolnet_scraper_agent.state import IdState, ScraperState
from omicsmolnet_scraper_agent.tools.scraper import fetch_publications
from omicsmolnet_scraper_agent.utils import logger

_UNIPROT_PUB_BASE = "https://www.uniprot.org/uniprotkb"


def load_ids_node(state: ScraperState) -> dict[str, Any]:
    """Load protein IDs from YAML config and/or extra_ids, then deduplicate."""
    ids: list[str] = list(state.get("extra_ids") or [])

    if config_path := state.get("config_path"):
        config = load_config(Path(config_path))
        ids = ids + config.ids

    seen: set[str] = set()
    unique_ids: list[str] = []
    for protein_id in ids:
        if protein_id not in seen:
            seen.add(protein_id)
            unique_ids.append(protein_id)

    logger.info(f"Loaded {len(unique_ids)} unique protein IDs: {unique_ids}")
    return {"ids": unique_ids}


def fan_out_ids(state: ScraperState) -> list[Send]:
    """Edge: spawn one process_id sub-invocation per protein ID."""
    return [
        Send(
            "process_id",
            IdState(
                id=protein_id,
                publications_url=f"{_UNIPROT_PUB_BASE}/{protein_id}/publications",
                publications=[],
                errors=[],
            ),
        )
        for protein_id in state["ids"]
    ]


def process_id_node(state: IdState) -> IdState:
    """Fetch publications for a single protein ID from the UniProt REST API."""
    protein_id = state["id"]
    try:
        publications = fetch_publications(protein_id)
        return {**state, "publications": publications}
    except Exception as exc:
        logger.error(f"Failed to fetch publications for {protein_id}: {exc}")
        return {**state, "errors": [*state.get("errors", []), str(exc)]}


def route_after_fetch(state: IdState) -> str:
    """Route to LLM resolution if any publication is missing a URL."""
    needs_resolution = any(
        pub.get("pubmed_url") is None and pub.get("doi") is None
        for pub in state.get("publications", [])
    )
    return "resolve_missing" if needs_resolution else "collect"


def collect_node(state: IdState) -> dict[str, Any]:
    """Append this ID's result into the top-level ScraperState.results list."""
    return {"results": [state]}


def build_graph() -> Any:
    """Construct and compile the publication scraping StateGraph."""
    builder = StateGraph(ScraperState)

    builder.add_node("load_ids", load_ids_node)
    builder.add_node("process_id", process_id_node)
    builder.add_node("resolve_missing", resolve_missing_publications)
    builder.add_node("collect", collect_node)

    builder.add_edge(START, "load_ids")
    builder.add_conditional_edges("load_ids", fan_out_ids, ["process_id"])
    builder.add_conditional_edges(
        "process_id",
        route_after_fetch,
        {"resolve_missing": "resolve_missing", "collect": "collect"},
    )
    builder.add_edge("resolve_missing", "collect")
    builder.add_edge("collect", END)

    return builder.compile()
