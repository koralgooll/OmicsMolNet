FROM python:3.12-slim

WORKDIR /app

RUN python -m pip install --upgrade pip

# Copy packages (single-repo monorepo style)
COPY packages/ ./packages/

# Install local packages in editable mode (no requirements/*.txt)
RUN pip install -e ./packages/core \
  && pip install -e ./packages/data \
  && pip install -e ./packages/agent_graph \
  && pip install -e ./packages/mcp_server

ENV OMN_MCP_HOST=0.0.0.0
ENV OMN_MCP_PORT=8010

EXPOSE 8010

CMD ["omicsmolnet-mcp"]

