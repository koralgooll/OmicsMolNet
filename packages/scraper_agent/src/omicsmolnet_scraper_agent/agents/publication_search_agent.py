"""LLM-driven agent for resolving publications that have no PubMed URL or DOI.

Used as a fallback node in the graph when the UniProt API returns a publication
with no external identifiers.

Architecture:
  - build_publication_search_chain() → prompt | llm.with_structured_output(PublicationResolution)
    Used now: LLM reasons from its own knowledge to return a structured result.
  - build_publication_search_agent() → ReAct agent with real search tools.
    Intended for Phase 2 when search_pubmed_by_title / search_crossref_by_doi are implemented.
"""

from __future__ import annotations

from typing import Any  # noqa: F401 — kept for build_publication_search_agent return type

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent  # type: ignore[import]  # Pylance stubs incorrect
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
    return _SEARCH_PROMPT | llm.with_structured_output(PublicationResolution)


# ---------------------------------------------------------------------------
# Phase 2: ReAct agent with real external search tools
# ---------------------------------------------------------------------------


@tool
def search_pubmed_by_title(title: str, authors: str) -> str:
    """Search PubMed for a publication by title and author names.

    Returns a PubMed URL (https://pubmed.ncbi.nlm.nih.gov/PMID/) if found,
    or an empty string if the publication cannot be located.
    """
    raise NotImplementedError("PubMed search tool not yet implemented")


@tool
def search_crossref_by_doi(doi: str) -> str:
    """Resolve a DOI to a full article URL via the CrossRef API.

    Returns the resolved URL or an empty string.
    """
    raise NotImplementedError("CrossRef DOI lookup not yet implemented")


def build_publication_search_agent() -> Any:
    """Build a LangGraph ReAct agent that can call external search tools.

    Phase 2: use this instead of build_publication_search_chain() once
    search_pubmed_by_title and search_crossref_by_doi are implemented.
    """
    llm = ChatAnthropic(model=_MODEL)
    tools = [search_pubmed_by_title, search_crossref_by_doi]
    return create_react_agent(llm, tools)


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

    chain = build_publication_search_chain()
    resolved_publications: list[Publication] = []

    for pub in state["publications"]:
        if pub.get("pubmed_url") or pub.get("doi"):
            resolved_publications.append(pub)
            continue

        try:
            resolution: PublicationResolution = chain.invoke(
                {
                    "title": pub["title"],
                    "authors": ", ".join(pub.get("authors", [])[:3]),
                    "journal": pub.get("journal", ""),
                    "year": pub.get("year", ""),
                }
            )
            if resolution.confidence >= confidence_threshold:
                resolved_url = resolution.pubmed_url
                resolved_doi = resolution.doi if not resolved_url else pub.get("doi")
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
        except Exception:
            logger.exception(f"LLM chain failed to resolve publication: {pub['title']}")
            resolved_url = None
            resolved_doi = pub.get("doi")

        resolved_publications.append(
            {**pub, "resolved_url": resolved_url, "doi": resolved_doi}
        )

    return {**state, "publications": resolved_publications}
