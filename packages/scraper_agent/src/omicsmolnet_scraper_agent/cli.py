"""CLI entry point for the OmicsMolNet scraper agent.

Usage:
    omicsmolnet-scraper --config configs/ids.yaml
    omicsmolnet-scraper --ids A1A4S6 O43826 P02649
    omicsmolnet-scraper --config configs/ids.yaml --ids Q9Y6K9   # merged, deduped
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from omicsmolnet_scraper_agent.graph import build_graph
from omicsmolnet_scraper_agent.state import ScraperState
from omicsmolnet_scraper_agent.utils import logger, set_log_level


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="omicsmolnet-scraper",
        description="Fetch UniProt publication data for a list of protein IDs.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to YAML file containing a list of protein IDs.",
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        metavar="ID",
        help="One or more UniProt protein IDs (e.g. A1A4S6 O43826). Combined with --config.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write JSON results to this file (default: stdout).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    set_log_level(args.log_level)

    if not args.config and not args.ids:
        logger.error("Provide at least --config or --ids (or both).")
        sys.exit(1)

    graph = build_graph()
    initial_state: ScraperState = {
        "config_path": args.config,
        "extra_ids": args.ids or [],
        "ids": [],
        "results": [],
    }
    final_state: ScraperState = graph.invoke(initial_state)

    output = json.dumps(final_state["results"], indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        logger.info(f"Results written to {args.output}")
    else:
        sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
