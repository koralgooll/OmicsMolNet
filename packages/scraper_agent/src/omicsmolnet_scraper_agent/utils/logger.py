"""Package-level logger, auto-configured on import.

Every module in omicsmolnet_scraper_agent imports this logger directly:

    from omicsmolnet_scraper_agent.utils import logger

The CLI can adjust the level at startup via set_log_level().
"""

import logging

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger: logging.Logger = logging.getLogger("omicsmolnet_scraper")

_handler = logging.StreamHandler()
_handler.setFormatter(_FORMATTER)
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def set_log_level(level: str) -> None:
    """Adjust the log level at runtime, e.g. from CLI --log-level."""
    logger.setLevel(getattr(logging, level.upper()))
