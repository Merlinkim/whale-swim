from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from src.models.paper import Paper


class GoogleScholarOptionalClient:
    base_url = "https://scholar.google.com/scholar"

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.session = requests.Session()
        self.timeout_seconds = timeout_seconds
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; paper-indexer/1.0)",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    @staticmethod
    def _blocked(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in ("unusual traffic", "captcha", "sorry", "not a robot"))

    def fetch(self, keyword: str, max_results: int, min_year: int) -> list[Paper]:
        params = {"q": keyword, "hl": "en", "num": min(max_results, 20)}
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
        except Exception:
            return []

        if self._blocked(response.text):
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        papers: list[Paper] = []
        for result in soup.select("div.gs_ri")[:max_results]:
            title_node = result.select_one("h3.gs_rt")
            if not title_node:
                continue
            link_node = title_node.find("a")
            title = title_node.get_text(" ", strip=True)
            url = link_node["href"] if link_node and link_node.has_attr("href") else None
            meta = result.select_one("div.gs_a")
            meta_text = meta.get_text(" ", strip=True) if meta else ""
            year_match = re.search(r"(19|20)\d{2}", meta_text)
            year = int(year_match.group(0)) if year_match else None
            if year is not None and year < min_year:
                continue
            authors = []
            if meta_text:
                authors = [part.strip() for part in meta_text.split(" - ", 1)[0].split(",") if part.strip()]
            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    published_date=None,
                    year=year,
                    source="google_scholar",
                    topic="",
                    keyword=keyword,
                    url=url,
                    doi=None,
                    arxiv_id=None,
                )
            )
        return papers
