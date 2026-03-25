from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GraphSpec:
    id: str
    name: str
    description: str


_GRAPHS: list[GraphSpec] = [
    GraphSpec(
        id="omicsmolnet_demo",
        name="OmicsMolNet Demo Graph",
        description="Placeholder graph. Replace with real LangGraph graphs.",
    )
]


def list_graphs() -> list[dict[str, str]]:
    return [{"id": g.id, "name": g.name, "description": g.description} for g in _GRAPHS]


def run_graph(graph_id: str, input: dict[str, Any]) -> dict[str, Any]:
    # Placeholder: real implementation will call into LangGraph
    # and return a structured result.
    if graph_id != "omicsmolnet_demo":
        raise ValueError(f"Unknown graph_id: {graph_id}")

    return {"graph_id": graph_id, "received_input": input, "output": {"status": "ok"}}

