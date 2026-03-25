from __future__ import annotations

import os

import uvicorn
from mcp.server.fastmcp.server import FastMCP

from omicsmolnet_agent_graph import list_graphs, run_graph


def create_mcp() -> FastMCP:
    mcp = FastMCP(
        name="OmicsMolNet MCP",
        instructions="MCP server exposing OmicsMolNet LangGraph graphs as tools.",
    )

    @mcp.tool()
    def list_available_graphs() -> list[dict[str, str]]:
        """List runnable graphs exposed by OmicsMolNet."""
        return list_graphs()

    @mcp.tool()
    def run_named_graph(graph_id: str, input: dict) -> dict:
        """Run a graph by id with JSON input and return JSON output."""
        return run_graph(graph_id=graph_id, input=input)

    return mcp


def main() -> None:
    host = os.environ.get("OMN_MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("OMN_MCP_PORT", "8010"))

    mcp = create_mcp()
    app = mcp.sse_app()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

