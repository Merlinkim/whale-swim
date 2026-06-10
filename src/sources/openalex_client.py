from __future__ import annotations

from urllib.parse import quote_plus

import requests

from src.models.paper import Paper


class OpenAlexClient:
    base_url = "https://api.openalex.org/works"

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.session = requests.Session()
        self.timeout_seconds = timeout_seconds
        self.session.headers.update(
            {
                "User-Agent": "paper-indexer/1.0 (+https://localhost)",
                "Accept": "application/json",
            }
        )

    def fetch(self, keyword: str, max_results: int, min_year: int) -> list[Paper]:
        params = {
            "search": keyword,
            "per-page": max_results,
            "filter": f"from_publication_date:{min_year}-01-01",
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        papers: list[Paper] = []
        for item in payload.get("results", [])[:max_results]:
            authors = [authorship.get("author", {}).get("display_name", "") for authorship in item.get("authorships", [])]
            authors = [author for author in authors if author]
            doi = item.get("doi")
            if doi:
                doi = doi.replace("https://doi.org/", "").strip()
            url = (
                item.get("primary_location", {}).get("landing_page_url")
                or item.get("primary_location", {}).get("pdf_url")
                or item.get("id")
            )
            papers.append(
                Paper(
                    title=item.get("display_name") or keyword,
                    authors=authors,
                    published_date=item.get("publication_date"),
                    year=item.get("publication_year"),
                    source="openalex",
                    topic="",
                    keyword=keyword,
                    url=url,
                    doi=doi,
                    arxiv_id=None,
                )
            )
        return papers
