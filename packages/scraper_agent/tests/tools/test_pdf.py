"""Tests for tools/pdf.py (Phase 2 stub)."""

import pytest

from omicsmolnet_scraper_agent.tools.pdf import download_pdf


def test_download_pdf_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        download_pdf("https://example.com/paper.pdf", "/tmp/pdfs")
