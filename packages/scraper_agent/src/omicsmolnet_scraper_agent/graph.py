"""LangGraph StateGraph for the UniProt publication scraping pipeline.

Topology:
  START → load_ids → [fan-out via Send] → process_single_id → END

Each Send arm runs process_single_id independently and returns
{"results": [IdState]} — the only key ScraperState knows how to reduce
(via operator.add). Routing logic (LLM fallback vs skip) lives inside
process_single_id as plain Python, not as graph edges, because intermediate
nodes in a Send arm must write back to the parent ScraperState keys only.
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
    """Edge: spawn one process_single_id invocation per protein ID."""
    return [
        Send(
            "process_single_id",
            IdState(
                id=protein_id,
                publications_url=f"{_UNIPROT_PUB_BASE}/{protein_id}/publications",
                publications=[],
                errors=[],
            ),
        )
        for protein_id in state["ids"]
    ]


def build_graph(uniprot_resolve_missing_publications: bool = True) -> Any:
    """Construct and compile the publication scraping StateGraph."""

    def process_single_id(state: IdState) -> dict[str, Any]:
        """Full per-ID pipeline: fetch publications, then resolve any missing URLs.

        Returns {"results": [IdState]} — a valid ScraperState partial update.
        Routing (LLM fallback vs skip) is plain Python here rather than graph edges
        because all Send arms write to the same parent state channels.
        """
        protein_id = state["id"]

        try:
            publications = fetch_publications(protein_id)
            state = {**state, "publications": publications}
        except Exception as exc:
            logger.error(f"Failed to fetch publications for {protein_id}: {exc}")
            state = {**state, "errors": [*state.get("errors", []), str(exc)]}

        if uniprot_resolve_missing_publications and any(
            pub.get("pubmed_url") is None and pub.get("doi") is None
            for pub in state.get("publications", [])
        ):
            state = resolve_missing_publications(state)

        return {"results": [state]}

    builder = StateGraph(ScraperState)

    builder.add_node("load_ids", load_ids_node)
    builder.add_node("process_single_id", process_single_id)

    builder.add_edge(START, "load_ids")
    builder.add_conditional_edges("load_ids", fan_out_ids, ["process_single_id"])
    builder.add_edge("process_single_id", END)

    return builder.compile()
