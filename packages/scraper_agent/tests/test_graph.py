"""Tests for the top-level LangGraph pipeline."""

import pytest
from unittest.mock import patch

from omicsmolnet_scraper_agent.graph import build_graph
from omicsmolnet_scraper_agent.state import ScraperState


def test_build_graph_returns_compiled_graph():
    graph = build_graph()
    assert graph is not None


@patch("omicsmolnet_scraper_agent.graph.fetch_publications")
def test_graph_invoke_single_id(mock_fetch):
    mock_fetch.return_value = [
        {
            "title": "Test publication",
            "authors": ["Smith J"],
            "journal": "Nature",
            "year": 2020,
            "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "doi": None,
            "other_links": [],
            "resolved_url": None,
        }
    ]

    graph = build_graph()
    result: ScraperState = graph.invoke({
        "config_path": None,
        "extra_ids": ["A1A4S6"],
        "ids": [],
        "results": [],
    })

    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "A1A4S6"
    assert len(result["results"][0]["publications"]) == 1
    assert result["results"][0]["publications"][0]["pubmed_url"] == (
        "https://pubmed.ncbi.nlm.nih.gov/12345/"
    )
