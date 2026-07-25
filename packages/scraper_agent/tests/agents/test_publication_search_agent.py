"""Tests for agents/publication_search_agent.py."""

import pytest

from omicsmolnet_scraper_agent.agents.publication_search_agent import (
    resolve_missing_publications,
)
from omicsmolnet_scraper_agent.state import IdState


def _make_state(**kwargs) -> IdState:
    defaults: IdState = {
        "id": "TEST",
        "publications_url": "https://www.uniprot.org/uniprotkb/TEST/publications",
        "publications": [],
        "errors": [],
    }
    return {**defaults, **kwargs}


def test_resolve_missing_skips_when_all_have_pubmed_url():
    state = _make_state(
        publications=[
            {
                "title": "Has a URL",
                "authors": [],
                "journal": "",
                "year": None,
                "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/111/",
                "doi": None,
                "other_links": [],
                "resolved_url": None,
            }
        ]
    )
    result = resolve_missing_publications(state)
    assert result["publications"][0]["pubmed_url"] == "https://pubmed.ncbi.nlm.nih.gov/111/"


def test_resolve_missing_skips_when_all_have_doi():
    state = _make_state(
        publications=[
            {
                "title": "Has a DOI",
                "authors": [],
                "journal": "",
                "year": None,
                "pubmed_url": None,
                "doi": "10.1000/xyz",
                "other_links": [],
                "resolved_url": None,
            }
        ]
    )
    result = resolve_missing_publications(state)
    assert result["publications"][0]["doi"] == "10.1000/xyz"
