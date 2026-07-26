"""Deterministic full-text download pipeline for Phase 2.

Two independent paths are attempted for each publication:

PDF path  (requires doi):
  1. Unpaywall API  → direct url_for_pdf
  2. CrossRef API   → pdf link from work metadata (fallback)

XML path  (requires pubmed_url):
  1. Europe PMC     → isOpenAccess + fullTextUrls
  2. NCBI OA Service (after PMID→PMCID conversion) → confirmed XML/PDF download link

Results are merged; whatever is available gets downloaded.
No LLM is used — all decisions are deterministic from the identifier fields.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

import requests

from omicsmolnet_scraper_agent.state import Publication
from omicsmolnet_scraper_agent.tools.pdf import download_pdf, download_xml
from omicsmolnet_scraper_agent.utils import logger

_TIMEOUT = 15
_USER_AGENT = "OmicsMolNet/1.0 (https://github.com/koralgooll/OmicsMolNet)"
_PMID_RE = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)")


# ---------------------------------------------------------------------------
# Internal API helpers — plain Python, no @tool decorator
# ---------------------------------------------------------------------------

def _extract_pmid(pubmed_url: str) -> str | None:
    m = _PMID_RE.search(pubmed_url)
    return m.group(1) if m else None


def _get(url: str, **kwargs) -> requests.Response | None:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
            **kwargs,
        )
        r.raise_for_status()
        return r
    except requests.RequestException as exc:
        logger.warning(f"HTTP request failed {url}: {exc}")
        return None


# -- PDF path ----------------------------------------------------------------

def _check_unpaywall(doi: str) -> dict:
    email = os.environ.get("UNPAYWALL_EMAIL")
    if not email:
        logger.debug("UNPAYWALL_EMAIL not set — skipping Unpaywall check")
        return {}
    r = _get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email})
    if r is None:
        return {}
    try:
        data = r.json()
        best = data.get("best_oa_location") or {}
        return {
            "is_oa": bool(data.get("is_oa")),
            "oa_status": data.get("oa_status"),
            "url_for_pdf": best.get("url_for_pdf"),
        }
    except Exception as exc:
        logger.warning(f"Failed to parse Unpaywall response for {doi}: {exc}")
        return {}


def _check_crossref(doi: str) -> dict:
    r = _get(f"https://api.crossref.org/v1/works/{doi}")
    if r is None:
        return {}
    try:
        message = r.json().get("message", {})
        pdf_links = [
            lnk["URL"]
            for lnk in message.get("link", [])
            if lnk.get("content-type") == "application/pdf"
        ]
        licenses = message.get("license", [])
        license_url = licenses[0].get("URL") if licenses else None
        return {"pdf_links": pdf_links, "license": license_url}
    except Exception as exc:
        logger.warning(f"Failed to parse CrossRef response for {doi}: {exc}")
        return {}


# -- XML path ----------------------------------------------------------------

def _check_europe_pmc(pmid: str) -> dict:
    r = _get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": f"EXT_ID:{pmid} AND SRC:MED",
            "format": "json",
            "resultType": "lite",
        },
    )
    if r is None:
        return {}
    try:
        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return {}
        hit = results[0]
        full_text_urls = [u for u in hit.get("fullTextUrlList", {}).get("fullTextUrl", []) if u.get("url")]
        return {
            "is_open_access": hit.get("isOpenAccess") == "Y",
            "full_text_urls": [u["url"] for u in full_text_urls],
        }
    except Exception as exc:
        logger.warning(f"Failed to parse Europe PMC response for PMID {pmid}: {exc}")
        return {}


def _check_ncbi_oa_service(pmid: str) -> dict:
    # Step 1: PMID → PMCID
    r = _get(
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
        params={"ids": pmid, "format": "json"},
    )
    if r is None:
        return {}
    try:
        records = r.json().get("records", [])
        pmcid = records[0].get("pmcid") if records else None
    except Exception as exc:
        logger.warning(f"Failed to parse NCBI ID converter response for PMID {pmid}: {exc}")
        return {}

    if not pmcid:
        logger.debug(f"PMID {pmid} not in PMC (no PMCID)")
        return {}

    # Step 2: PMCID → OA links
    r2 = _get(
        "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi",
        params={"id": pmcid},
    )
    if r2 is None:
        return {}
    try:
        root = ET.fromstring(r2.text)
        xml_url: str | None = None
        pdf_url: str | None = None
        license_val: str | None = None
        for record in root.iter("record"):
            license_val = record.get("license")
            for link in record.iter("link"):
                fmt = link.get("format", "")
                href = link.get("href", "")
                if fmt == "tgz" and not xml_url:
                    xml_url = href
                elif fmt == "pdf" and not pdf_url:
                    pdf_url = href
        return {"xml_url": xml_url, "pdf_url": pdf_url, "license": license_val}
    except Exception as exc:
        logger.warning(f"Failed to parse NCBI OA Service response for {pmcid}: {exc}")
        return {}


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def build_publication_pdf_pipeline(
    output_dir: str | Path,
) -> Callable[[Publication], dict]:
    """Return a callable that processes one Publication and returns updated fields.

    The callable runs both the PDF path and the XML path independently and
    downloads whatever is available. No LLM is involved.
    """
    base = Path(output_dir)
    pdf_dir = base / "pdf"
    xml_dir = base / "xml"

    def _process(pub: Publication) -> dict:
        doi = pub.get("doi")
        pubmed_url = pub.get("pubmed_url") or pub.get("resolved_url")

        is_open_access: bool | None = None
        oa_status: str | None = None
        pdf_url: str | None = None
        pdf_path: str | None = None
        xml_url: str | None = None
        xml_path: str | None = None

        # -- PDF path --------------------------------------------------------
        if doi:
            unpaywall = _check_unpaywall(doi)
            if unpaywall:
                is_open_access = unpaywall.get("is_oa")
                oa_status = unpaywall.get("oa_status")
                pdf_url = unpaywall.get("url_for_pdf")

            if not pdf_url:
                crossref = _check_crossref(doi)
                links = crossref.get("pdf_links", [])
                if links:
                    pdf_url = links[0]

            if pdf_url:
                pdf_dir.mkdir(parents=True, exist_ok=True)
                result = download_pdf(pdf_url, pdf_dir)
                if result:
                    pdf_path = result

        # -- XML path --------------------------------------------------------
        if pubmed_url:
            pmid = _extract_pmid(pubmed_url)
            if pmid:
                epmc = _check_europe_pmc(pmid)
                oa_from_epmc = epmc.get("is_open_access", False)

                if is_open_access is None:
                    is_open_access = oa_from_epmc

                if oa_from_epmc:
                    ncbi = _check_ncbi_oa_service(pmid)
                    xml_url = ncbi.get("xml_url")
                    ncbi_pdf = ncbi.get("pdf_url")

                    if xml_url:
                        xml_dir.mkdir(parents=True, exist_ok=True)
                        result = download_xml(xml_url, xml_dir)
                        if result:
                            xml_path = result

                    if ncbi_pdf and not pdf_url:
                        pdf_url = ncbi_pdf
                        pdf_dir.mkdir(parents=True, exist_ok=True)
                        result = download_pdf(ncbi_pdf, pdf_dir)
                        if result:
                            pdf_path = result

        return {
            "is_open_access": is_open_access,
            "oa_status": oa_status,
            "pdf_url": pdf_url,
            "pdf_path": pdf_path,
            "xml_url": xml_url,
            "xml_path": xml_path,
        }

    return _process
