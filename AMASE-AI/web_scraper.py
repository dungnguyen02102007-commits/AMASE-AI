"""
Retrieves benchmark CVs and job market data from the web
using DuckDuckGo search (no API key required).
"""

from __future__ import annotations
import re
import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from config import MAX_BENCHMARK_RESULTS, MAX_JOB_MARKET_RESULTS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_benchmark_cv(job_role: str, industry: str) -> str:
    """
    Searches for high-standard CV examples relevant to a job role/industry
    and returns a combined text of benchmark content.
    """
    query = (
        f"professional CV resume example {job_role} {industry} "
        f"high standard ATS-friendly format 2024"
    )
    results = _ddg_search(query, max_results=MAX_BENCHMARK_RESULTS)

    all_content = []
    for result in results:
        url  = result.get("href", "")
        body = result.get("body", "")
        if body:
            all_content.append(f"[Source: {url}]\n{body}")

    return "\n\n---\n\n".join(all_content) if all_content else ""


def fetch_job_market_data(job_role: str, industry: str) -> list[dict]:
    """
    Retrieves job market demand, skill requirements, and hiring trends
    from multiple online sources.
    """
    queries = [
        f"{job_role} {industry} job requirements skills 2024 hiring",
        f"{job_role} average candidate profile skills experience",
        f"{industry} industry hiring trends 2024 {job_role}",
        f"{job_role} in-demand skills market demand salary",
        f"what employers look for in {job_role} resume",
    ]

    all_data = []
    for query in queries:
        results = _ddg_search(query, max_results=MAX_JOB_MARKET_RESULTS // len(queries))
        for r in results:
            all_data.append({
                "source":  r.get("href", ""),
                "title":   r.get("title", ""),
                "content": r.get("body", ""),
            })
        time.sleep(0.5)   # Polite crawling delay

    return all_data


def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo text search wrapper."""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"[WebScraper] Search failed for query '{query}': {e}")
        return []


def _scrape_page(url: str, timeout: int = 8) -> str:
    """
    Optional: deeper scrape of a specific URL.
    Returns clean body text.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text[:4000]   # Limit per page
    except Exception as e:
        print(f"[WebScraper] Page scrape failed for {url}: {e}")
        return ""
