"""File download utilities for Phase 2 full-text retrieval."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_USER_AGENT = "OmicsMolNet/1.0 (https://github.com/koralgooll/OmicsMolNet)"
_TIMEOUT = 30


def _download_file(
    url: str,
    dest_dir: str | Path,
    expected_mime_prefix: str | None = None,
) -> str:
    """Download a file from *url* and save it under *dest_dir*.

    Returns the absolute path of the saved file, or an empty string on failure.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
            stream=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning(f"Failed to download {url}: {exc}")
        return ""

    content_type = response.headers.get("Content-Type", "")
    if expected_mime_prefix and not content_type.startswith(expected_mime_prefix):
        logger.warning(
            f"Unexpected Content-Type '{content_type}' for {url} "
            f"(expected prefix '{expected_mime_prefix}')"
        )
        return ""

    filename = _derive_filename(url)
    dest_path = dest_dir / filename
    try:
        with dest_path.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                fh.write(chunk)
    except OSError as exc:
        logger.error(f"Failed to write {dest_path}: {exc}")
        return ""

    logger.info(f"Downloaded {url} → {dest_path}")
    return str(dest_path.resolve())


def _derive_filename(url: str) -> str:
    """Derive a safe filename from *url*; fall back to SHA-256 of the URL."""
    path_segment = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    if path_segment and "." in path_segment:
        return path_segment
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def download_pdf(url: str, dest_dir: str | Path) -> str:
    """Download a PDF from *url* and save it under *dest_dir*.

    Returns the absolute path of the saved file, or an empty string on failure.
    """
    return _download_file(url, dest_dir, expected_mime_prefix="application/pdf")


def download_xml(url: str, dest_dir: str | Path) -> str:
    """Download an XML file from *url* and save it under *dest_dir*.

    Returns the absolute path of the saved file, or an empty string on failure.
    Accepts text/xml, application/xml, and application/x-tar (for .tgz packages).
    """
    return _download_file(url, dest_dir, expected_mime_prefix=None)
