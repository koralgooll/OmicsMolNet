"""UniProt REST API client for fetching publication metadata.

Uses https://rest.uniprot.org/uniprotkb/{ID}/publications (JSON) rather than
scraping the React-rendered web page.
"""

from __future__ import annotations

import requests

from omicsmolnet_scraper_agent.state import Publication
from omicsmolnet_scraper_agent.utils import logger

_UNIPROT_API_BASE = "https://rest.uniprot.org/uniprotkb"
_PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov"
_REQUEST_TIMEOUT = 30
_HEADERS = {"Accept": "application/json"}


def _build_publications_url(protein_id: str) -> str:
    return f"{_UNIPROT_API_BASE}/{protein_id}/publications"


def _parse_entry(entry: dict) -> Publication:
    citation = entry.get("citation", {})

    title: str = citation.get("title", "")
    authors: list[str] = [
        a.get("value", "") for a in citation.get("authors", []) if a.get("value")
    ]
    journal: str = citation.get("journal", "")

    publication_date: str = citation.get("publicationDate", "")
    year: int | None = None
    if publication_date:
        try:
            year = int(publication_date[:4])
        except ValueError:
            pass

    pubmed_id: str | None = citation.get("pubMedId")
    pubmed_url: str | None = f"{_PUBMED_BASE}/{pubmed_id}/" if pubmed_id else None

    doi: str | None = None
    other_links: list[str] = []
    for db_ref in citation.get("citationCrossReferences", []):
        db = db_ref.get("database", "")
        db_id = db_ref.get("id", "")
        if db == "DOI":
            doi = db_id
        elif db_id:
            other_links.append(f"{db}:{db_id}")

    return Publication(
        title=title,
        authors=authors,
        journal=journal,
        year=year,
        pubmed_url=pubmed_url,
        doi=doi,
        other_links=other_links,
        resolved_url=None,
    )


def fetch_publications(protein_id: str) -> list[Publication]:
    """Fetch all publications for a UniProt protein ID via the REST API.

    Returns a list of Publication dicts with pubmed_url set where available.
    Raises requests.HTTPError on non-2xx responses.
    """
    url = _build_publications_url(protein_id)
    logger.debug(f"Fetching publications for {protein_id} from {url}")

    response = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])
    publications = [_parse_entry(entry) for entry in results]

    logger.info(f"Fetched {len(publications)} publications for {protein_id}")
    return publications
