"""LLM-driven chain for resolving publications that have no PubMed URL or DOI.

Used as a fallback node in the graph when the UniProt API returns a publication
with no external identifiers.

Phase 1: build_publication_search_chain() → prompt | llm.with_structured_output(PublicationResolution)
Phase 2 (PDF download): see agents/publication_pdf_agent.py
"""

from __future__ import annotations

import os
from typing import Any

import anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from omicsmolnet_scraper_agent.state import IdState, Publication
from omicsmolnet_scraper_agent.utils import logger

_MODEL = "claude-haiku-4-5-20251001"

_SEARCH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a biomedical literature assistant. "
                "Given a publication's metadata, find its PubMed URL or DOI. "
                "Only return high-confidence matches. "
                "If unsure, return null for both fields."
            ),
        ),
        (
            "human",
            (
                "Find the PubMed URL or DOI for this publication:\n"
                "Title:   {title}\n"
                "Authors: {authors}\n"
                "Journal: {journal}\n"
                "Year:    {year}\n\n"
                "Return the full PubMed URL "
                "(https://pubmed.ncbi.nlm.nih.gov/PMID/) if found, "
                "or the DOI string (e.g. 10.1234/abc) as fallback."
            ),
        ),
    ]
)


class PublicationResolution(BaseModel):
    """Structured output from the publication search LLM call."""

    pubmed_url: str | None = Field(
        default=None,
        description="Full PubMed URL, e.g. https://pubmed.ncbi.nlm.nih.gov/12345/",
    )
    doi: str | None = Field(
        default=None,
        description="DOI string if no PubMed URL was found, e.g. 10.1234/abc",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence 0–1 that the result matches the requested publication",
    )


def build_publication_search_chain() -> Any:
    """Build a prompt | structured-output chain for resolving missing publication URLs.

    Returns a Runnable that accepts a dict with keys
    {title, authors, journal, year} and produces a PublicationResolution.
    """
    llm = ChatAnthropic(model=_MODEL)
    return _SEARCH_PROMPT | llm.with_structured_output(PublicationResolution, include_raw=True)


# ---------------------------------------------------------------------------
# Graph node
# ---------------------------------------------------------------------------

def resolve_missing_publications(
    state: IdState,
    confidence_threshold: float = 0.7,
) -> IdState:
    """Graph node: resolve publications with no pubmed_url and no doi.

    Calls the LLM chain for each unresolved publication and fills in
    resolved_url (from pubmed_url) or doi where confidence is sufficient.
    """
    unresolved = [
        pub
        for pub in state["publications"]
        if pub.get("pubmed_url") is None and pub.get("doi") is None
    ]

    if not unresolved:
        return state

    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning(
            f"Skipping LLM resolution for {len(unresolved)} publication(s) in "
            f"'{state['id']}': ANTHROPIC_API_KEY is not set."
        )
        return state

    chain = build_publication_search_chain()
    resolved_publications: list[Publication] = []

    for i, pub in enumerate(state["publications"]):
        if pub.get("pubmed_url") or pub.get("doi"):
            resolved_publications.append(pub)
            continue

        try:
            prompt_input = {
                "title": pub["title"],
                "authors": ", ".join(pub.get("authors", [])[:3]),
                "journal": pub.get("journal", ""),
                "year": pub.get("year", ""),
            }
            result = chain.invoke(prompt_input)
            raw_response = result["raw"]  # noqa: F841 — uncomment watchpoint when debugging
            logger.debug(f"LLM tool_calls: {raw_response.tool_calls}")
            logger.debug(f"LLM parsing_error: {result['parsing_error']}")
            resolution: PublicationResolution = result["parsed"]
            if resolution.confidence >= confidence_threshold:
                resolved_url = resolution.pubmed_url
                resolved_doi = resolution.doi if not resolved_url else pub.get("doi")
                llm_confidence = resolution.confidence
                logger.info(
                    f"Resolved '{pub['title'][:60]}' → {resolved_url or resolved_doi} "
                    f"(confidence={resolution.confidence:.2f})"
                )
            else:
                logger.warning(
                    f"Low-confidence resolution for '{pub['title'][:60]}' "
                    f"({resolution.confidence:.2f}), skipping"
                )
                resolved_url = None
                resolved_doi = pub.get("doi")
                llm_confidence = resolution.confidence
        except anthropic.AuthenticationError:
            logger.error(
                "Anthropic API key is invalid (401). "
                "Set a valid ANTHROPIC_API_KEY to enable LLM resolution. "
                "Skipping all remaining unresolved publications."
            )
            # Keep already-processed pubs + current + everything not yet reached
            resolved_publications.extend(state["publications"][i:])
            return {**state, "publications": resolved_publications}
        except Exception:
            logger.exception(f"Unexpected error resolving publication: {pub['title']}")
            resolved_url = None
            resolved_doi = pub.get("doi")
            llm_confidence = 0.0

        resolved_publications.append(
            {**pub, "resolved_url": resolved_url, "doi": resolved_doi, "confidence": llm_confidence}
        )

    return {**state, "publications": resolved_publications}
