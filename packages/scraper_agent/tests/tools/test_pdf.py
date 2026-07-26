"""Tests for tools/pdf.py."""

from omicsmolnet_scraper_agent.tools.pdf import download_pdf


def test_download_pdf_returns_empty_string_on_http_error(tmp_path):
    # A URL that won't serve a PDF returns "" without raising
    result = download_pdf("https://example.com/paper.pdf", tmp_path)
    assert result == ""
