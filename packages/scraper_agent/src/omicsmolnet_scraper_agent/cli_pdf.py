"""CLI entry point for the Phase 2 full-text download pipeline.

Usage:
    omicsmolnet-pdf --input phase1.json --output-dir ./out/
    omicsmolnet-pdf --input phase1.json --output-dir ./out/ --output phase2.json

Environment variables:
    UNPAYWALL_EMAIL   Contact email for Unpaywall API (100k calls/day).
                      If not set, the Unpaywall PDF path is skipped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from omicsmolnet_scraper_agent.graph_pdf import FullTextDownloadState, build_pdf_graph
from omicsmolnet_scraper_agent.utils import logger, parse_pdf_args


def main(argv: list[str] | None = None) -> None:
    args = parse_pdf_args(argv)

    output_dir = Path(args.output_dir)
    (output_dir / "pdf").mkdir(parents=True, exist_ok=True)
    (output_dir / "xml").mkdir(parents=True, exist_ok=True)

    graph = build_pdf_graph()
    initial_state: FullTextDownloadState = {
        "input_path": args.input,
        "output_dir": str(output_dir),
        "results": [],
    }
    final_state: FullTextDownloadState = graph.invoke(initial_state)

    output = json.dumps(final_state["results"], indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        logger.info(f"Results written to {args.output}")
    else:
        sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
