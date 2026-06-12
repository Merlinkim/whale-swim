from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.models.paper import Paper


class IEEEXploreOptionalClient:
    base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp"

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
        return any(marker in lowered for marker in ("captcha", "unusual traffic", "access denied", "robot"))

    @staticmethod
    def _clean_text(value: str | None) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def fetch(self, keyword: str, max_results: int, min_year: int) -> list[Paper]:
        params = {
            "newsearch": "true",
            "queryText": keyword,
            "highlight": "true",
            "returnType": "SEARCH",
            "pageNumber": 1,
            "rowsPerPage": min(max_results, 25),
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
        except Exception:
            return []

        if self._blocked(response.text):
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        papers: list[Paper] = []
        seen_urls: set[str] = set()

        for anchor in soup.select('a[href*="/document/"]'):
            href = anchor.get("href")
            if not href or "/document/" not in href:
                continue

            url = urljoin("https://ieeexplore.ieee.org", href)
            if url in seen_urls:
                continue

            title = self._clean_text(anchor.get_text(" ", strip=True))
            if not title:
                continue

            container = anchor.parent
            nearby_text = self._clean_text(container.get_text(" ", strip=True) if container else "")
            year_match = re.search(r"(19|20)\d{2}", nearby_text)
            year = int(year_match.group(0)) if year_match else None
            if year is not None and year < min_year:
                continue

            authors: list[str] = []
            if container:
                for link in container.select('a[href*="/author/"]'):
                    name = self._clean_text(link.get_text(" ", strip=True))
                    if name and name not in authors:
                        authors.append(name)

            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    published_date=None,
                    year=year,
                    source="ieee_xplore",
                    topic="",
                    keyword=keyword,
                    url=url,
                    doi=None,
                    arxiv_id=None,
                )
            )
            seen_urls.add(url)

            if len(papers) >= max_results:
                break

        return papers
