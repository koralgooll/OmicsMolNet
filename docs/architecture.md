# OmicsMolNet architecture (draft)

## Modules

- **`packages/core`**: shared types + utilities
- **`packages/data`**: omics data IO/loaders/schemas
- **`packages/agent_graph`**: LangChain/LangGraph graphs and nodes
- **`packages/mcp_server`**: MCP server exposing graphs as tools (SSE/HTTP)
- **`packages/cli`**: CLI entry points for local workflows (optional)

## Flowise integration

Flowise connects to OmicsMolNet by adding a **Custom MCP server** pointing to the MCP SSE endpoint.
