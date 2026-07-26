"""CLI argument parser for the OmicsMolNet scraper agent."""

from __future__ import annotations

import argparse

from omicsmolnet_scraper_agent.utils.logger import set_log_level


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
    parser.add_argument(
        "--uniprot-resolve-missing-publications",
        dest="uniprot_resolve_missing_publications",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Call the LLM to resolve publications with no PubMed URL or DOI "
            "(default: enabled). Use --no-uniprot-resolve-missing-publications to skip."
        ),
    )
    args = parser.parse_args(argv)

    set_log_level(args.log_level)

    if not args.config and not args.ids:
        parser.error("Provide at least --config or --ids (or both).")

    return args
