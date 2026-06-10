from __future__ import annotations

import requests

from src.models.paper import Paper


class SemanticScholarClient:
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

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
            "query": keyword,
            "limit": max_results,
            "fields": "title,authors,year,publicationDate,url,externalIds",
            "offset": 0,
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        papers: list[Paper] = []
        for item in payload.get("data", [])[:max_results]:
            year = item.get("year")
            if year is not None and int(year) < min_year:
                continue
            authors = [author.get("name", "") for author in item.get("authors", []) if author.get("name")]
            external_ids = item.get("externalIds", {}) or {}
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")
            papers.append(
                Paper(
                    title=item.get("title") or keyword,
                    authors=authors,
                    published_date=item.get("publicationDate"),
                    year=year,
                    source="semantic_scholar",
                    topic="",
                    keyword=keyword,
                    url=item.get("url"),
                    doi=doi,
                    arxiv_id=arxiv_id,
                )
            )
        return papers
