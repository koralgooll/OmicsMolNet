"""PDF download utilities. Phase 2 — stub only."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def download_pdf(url: str, dest_dir: str | Path) -> str:
    """Download a PDF from *url* and save it under *dest_dir*.

    Returns the absolute path of the saved file.
    Phase 2: not yet implemented.
    """
    raise NotImplementedError("PDF download is planned for Phase 2")
