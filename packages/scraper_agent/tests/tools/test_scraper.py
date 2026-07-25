"""Tests for tools/scraper.py (UniProt REST API client)."""

import pytest
from unittest.mock import MagicMock, patch

from omicsmolnet_scraper_agent.tools.scraper import fetch_publications, _parse_entry


def test_parse_entry_with_pubmed_id():
    entry = {
        "citation": {
            "title": "Some protein study",
            "authors": [{"value": "Doe J"}, {"value": "Smith A"}],
            "journal": "Cell",
            "publicationDate": "2021",
            "pubMedId": "98765",
            "citationCrossReferences": [{"database": "DOI", "id": "10.1000/xyz123"}],
        }
    }
    pub = _parse_entry(entry)

    assert pub["title"] == "Some protein study"
    assert pub["authors"] == ["Doe J", "Smith A"]
    assert pub["year"] == 2021
    assert pub["pubmed_url"] == "https://pubmed.ncbi.nlm.nih.gov/98765/"
    assert pub["doi"] == "10.1000/xyz123"
    assert pub["resolved_url"] is None


def test_parse_entry_missing_pubmed_id():
    entry = {"citation": {"title": "No PMID paper", "pubMedId": None}}
    pub = _parse_entry(entry)
    assert pub["pubmed_url"] is None


@patch("omicsmolnet_scraper_agent.tools.scraper.requests.get")
def test_fetch_publications_calls_correct_url(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_publications("A1A4S6")

    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "A1A4S6" in called_url
    assert result == []
