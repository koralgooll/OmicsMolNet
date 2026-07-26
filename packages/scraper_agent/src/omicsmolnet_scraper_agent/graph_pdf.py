"""LangGraph StateGraph for the Phase 2 full-text download pipeline.

Topology:
  START → load_phase1_results → [fan-out via Send per IdState] → download_for_id → END

Each Send arm runs download_for_id independently for one protein ID and returns
{"results": [IdState]} — the only key FullTextDownloadState knows how to reduce
(via operator.add).
"""

from __future__ import annotations

import json
import operator
from pathlib import Path
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import TypedDict

from omicsmolnet_scraper_agent.agents.publication_pdf_agent import (
    build_publication_pdf_pipeline,
)
from omicsmolnet_scraper_agent.state import IdState
from omicsmolnet_scraper_agent.utils import logger


class FullTextDownloadState(TypedDict):
    input_path: str
    output_dir: str
    results: Annotated[list[IdState], operator.add]


def load_phase1_results(state: FullTextDownloadState) -> list[Send]:
    """Node + conditional edge: read Phase 1 JSON and fan-out one arm per IdState."""
    path = Path(state["input_path"])
    id_states: list[IdState] = json.loads(path.read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(id_states)} ID result(s) from {path}")
    return [
        Send("download_for_id", {**id_state, "_output_dir": state["output_dir"]})
        for id_state in id_states
    ]


def build_pdf_graph() -> Any:
    """Construct and compile the full-text download StateGraph."""

    def download_for_id(state: dict) -> dict[str, Any]:
        output_dir = state.pop("_output_dir")
        id_state: IdState = state  # type: ignore[assignment]
        pipeline = build_publication_pdf_pipeline(output_dir)

        updated_publications = []
        for pub in id_state.get("publications", []):
            try:
                updates = pipeline(pub)
                updated_publications.append({**pub, **updates})
            except Exception:
                logger.exception(
                    f"Unexpected error downloading full text for "
                    f"'{pub.get('title', '')[:60]}'"
                )
                updated_publications.append(pub)

        return {"results": [{**id_state, "publications": updated_publications}]}

    builder = StateGraph(FullTextDownloadState)
    builder.add_node("download_for_id", download_for_id)
    builder.add_conditional_edges(START, load_phase1_results, ["download_for_id"])
    builder.add_edge("download_for_id", END)

    return builder.compile()
