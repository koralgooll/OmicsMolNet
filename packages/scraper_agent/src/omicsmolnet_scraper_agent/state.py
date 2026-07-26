from typing import Annotated
from typing_extensions import TypedDict
import operator


class Publication(TypedDict):
    title: str
    authors: list[str]
    journal: str
    year: int | None
    pubmed_url: str | None
    doi: str | None
    other_links: list[str]
    resolved_url: str | None
    confidence: float  # 1.0 for pubmed_url/doi from UniProt; LLM score for resolved_url


class IdState(TypedDict):
    id: str
    publications_url: str
    publications: list[Publication]
    errors: list[str]


class ScraperState(TypedDict):
    config_path: str | None   # path to ids.yaml; loaded by load_ids_node
    extra_ids: list[str]      # IDs passed directly via CLI --ids
    ids: list[str]            # merged + deduplicated; filled by load_ids_node
    results: Annotated[list[IdState], operator.add]
