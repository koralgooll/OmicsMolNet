"""LLM-driven agent for resolving publications that have no PubMed URL or DOI.

Used as a fallback node in the graph when the UniProt API returns a publication
with no external identifiers. The agent uses title + authors to search for the
publication and returns a resolved URL.
"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from omicsmolnet_scraper_agent.state import IdState, Publication
from omicsmolnet_scraper_agent.utils import logger

_MODEL = "claude-haiku-4-5-20251001"


@tool
def search_pubmed_by_title(title: str, authors: str) -> str:
    """Search PubMed for a publication by title and author names.

    Returns a PubMed URL if found, or an empty string if not found.
    """
    raise NotImplementedError("PubMed search tool not yet implemented")


@tool
def search_crossref_by_doi(doi: str) -> str:
    """Resolve a DOI to a full URL via CrossRef.

    Returns the resolved URL or an empty string.
    """
    raise NotImplementedError("CrossRef DOI lookup not yet implemented")


def build_publication_search_agent() -> Any:
    """Build a LangGraph ReAct agent for resolving missing publication URLs."""
    llm = ChatAnthropic(model=_MODEL)
    tools = [search_pubmed_by_title, search_crossref_by_doi]
    return create_react_agent(llm, tools)


def resolve_missing_publications(state: IdState) -> IdState:
    """Graph node: resolve publications with no pubmed_url and no doi.

    Calls the LLM agent for each unresolved publication and fills in
    resolved_url where possible.
    """
    unresolved = [
        pub
        for pub in state["publications"]
        if pub.get("pubmed_url") is None and pub.get("doi") is None
    ]

    if not unresolved:
        return state

    agent = build_publication_search_agent()
    resolved_publications: list[Publication] = []

    for pub in state["publications"]:
        if pub.get("pubmed_url") or pub.get("doi"):
            resolved_publications.append(pub)
            continue

        authors_str = ", ".join(pub.get("authors", [])[:3])
        prompt = (
            f"Find the PubMed URL for this publication:\n"
            f"Title: {pub['title']}\n"
            f"Authors: {authors_str}\n"
            f"Journal: {pub.get('journal', '')}\n"
            f"Year: {pub.get('year', '')}\n\n"
            f"Return only the PubMed URL (https://pubmed.ncbi.nlm.nih.gov/...) "
            f"or 'NOT_FOUND' if you cannot find it."
        )

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            last_message = result["messages"][-1].content
            resolved_url = last_message.strip() if "pubmed" in last_message.lower() else None
        except Exception:
            logger.exception(f"Agent failed to resolve publication: {pub['title']}")
            resolved_url = None

        resolved_publications.append({**pub, "resolved_url": resolved_url})

    return {**state, "publications": resolved_publications}
