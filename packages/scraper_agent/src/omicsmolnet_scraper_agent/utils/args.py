"""CLI argument parser for the OmicsMolNet scraper agent."""

from __future__ import annotations

import argparse


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
    return parser.parse_args(argv)
