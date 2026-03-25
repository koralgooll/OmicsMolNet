# Flowise assets

This directory is intended for:

- **`exports/`**: versioned Flowise exports (JSON) so chatflows/agentflows can be tracked in Git
- documentation describing how Flowise is configured to connect to OmicsMolNet services (MCP, HTTP tools, etc.)

## OmicsMolNet MCP server

When running via `[docker/docker-compose.yml](../../docker/docker-compose.yml)`, the MCP SSE endpoint is:

- Inside Docker: `http://omicsmolnet-mcp:8010/sse`
- From host: `http://localhost:8010/sse`

Configure Flowise to use **SSE transport** and point it at that URL.
