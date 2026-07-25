"""Tests for the top-level LangGraph pipeline."""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from omicsmolnet_scraper_agent.graph import build_graph, load_ids_node
from omicsmolnet_scraper_agent.state import ScraperState


def _pub(pubmed_id: str) -> dict:
    return {
        "title": f"Publication {pubmed_id}",
        "authors": ["Smith J"],
        "journal": "Nature",
        "year": 2020,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
        "doi": None,
        "other_links": [],
        "resolved_url": None,
    }


def _empty_state(**kwargs) -> ScraperState:
    defaults: ScraperState = {
        "config_path": None,
        "extra_ids": [],
        "ids": [],
        "results": [],
    }
    return {**defaults, **kwargs}


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def test_build_graph_returns_compiled_graph():
    graph = build_graph()
    assert graph is not None


# ---------------------------------------------------------------------------
# load_ids_node
# ---------------------------------------------------------------------------


def test_load_ids_node_from_extra_ids_only():
    state = _empty_state(extra_ids=["A1A4S6", "O43826"])
    result = load_ids_node(state)
    assert result["ids"] == ["A1A4S6", "O43826"]


def test_load_ids_node_from_yaml(tmp_path: Path):
    config_file = tmp_path / "ids.yaml"
    config_file.write_text(textwrap.dedent("""\
        ids:
          - A1A4S6
          - O43826
    """))

    state = _empty_state(config_path=str(config_file))
    result = load_ids_node(state)
    assert result["ids"] == ["A1A4S6", "O43826"]


def test_load_ids_node_merges_and_deduplicates(tmp_path: Path):
    config_file = tmp_path / "ids.yaml"
    config_file.write_text(textwrap.dedent("""\
        ids:
          - A1A4S6
          - O43826
    """))

    state = _empty_state(config_path=str(config_file), extra_ids=["O43826", "P02649"])
    result = load_ids_node(state)
    # extra_ids come first, then config; O43826 appears in both → deduplicated
    assert result["ids"] == ["O43826", "P02649", "A1A4S6"]


# ---------------------------------------------------------------------------
# Full graph — single ID
# ---------------------------------------------------------------------------


@patch("omicsmolnet_scraper_agent.graph.fetch_publications")
def test_graph_invoke_single_id(mock_fetch):
    mock_fetch.return_value = [_pub("12345")]

    graph = build_graph()
    result: ScraperState = graph.invoke(_empty_state(extra_ids=["A1A4S6"]))

    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "A1A4S6"
    assert result["results"][0]["publications"][0]["pubmed_url"] == (
        "https://pubmed.ncbi.nlm.nih.gov/12345/"
    )


# ---------------------------------------------------------------------------
# Full graph — two IDs fan-out
# ---------------------------------------------------------------------------


@patch("omicsmolnet_scraper_agent.graph.fetch_publications")
def test_graph_invoke_two_ids_fan_out(mock_fetch):
    mock_fetch.side_effect = lambda protein_id: [_pub(protein_id)]

    graph = build_graph()
    result: ScraperState = graph.invoke(
        _empty_state(extra_ids=["A1A4S6", "O43826"])
    )

    assert len(result["results"]) == 2
    returned_ids = {r["id"] for r in result["results"]}
    assert returned_ids == {"A1A4S6", "O43826"}

    for id_result in result["results"]:
        assert len(id_result["publications"]) == 1
        expected_url = f"https://pubmed.ncbi.nlm.nih.gov/{id_result['id']}/"
        assert id_result["publications"][0]["pubmed_url"] == expected_url
