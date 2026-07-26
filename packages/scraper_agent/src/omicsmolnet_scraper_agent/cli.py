"""CLI entry point for the OmicsMolNet scraper agent.

Usage:
    omicsmolnet-scraper --config configs/ids.yaml
    omicsmolnet-scraper --ids A1A4S6 O43826 P02649
    omicsmolnet-scraper --config configs/ids.yaml --ids Q9Y6K9   # merged, deduped
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from omicsmolnet_scraper_agent.graph import build_graph
from omicsmolnet_scraper_agent.state import ScraperState
from omicsmolnet_scraper_agent.utils import logger, parse_args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    graph = build_graph(
        uniprot_resolve_missing_publications=args.uniprot_resolve_missing_publications,
    )
    initial_state: ScraperState = {
        "config_path": args.config,
        "extra_ids": args.ids or [],
        "ids": [],
        "results": [],
    }
    final_state: ScraperState = graph.invoke(initial_state)

    output = json.dumps(final_state["results"], indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        logger.info(f"Results written to {args.output}")
    else:
        sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
