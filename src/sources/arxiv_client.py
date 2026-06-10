from __future__ import annotations

from xml.etree import ElementTree as ET

import requests

from src.models.paper import Paper


class ArxivClient:
    base_url = "http://export.arxiv.org/api/query"

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.session = requests.Session()
        self.timeout_seconds = timeout_seconds
        self.session.headers.update(
            {
                "User-Agent": "paper-indexer/1.0 (+https://localhost)",
                "Accept": "application/atom+xml,application/xml,text/xml",
            }
        )

    def fetch(self, keyword: str, max_results: int, min_year: int) -> list[Paper]:
        params = {
            "search_query": f'all:"{keyword}"',
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
        except Exception:
            return []

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return []

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", namespace):
            title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
            published = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()
            year = int(published[:4]) if published[:4].isdigit() else None
            if year is not None and year < min_year:
                continue
            authors = [author.findtext("atom:name", default="", namespaces=namespace) for author in entry.findall("atom:author", namespace)]
            authors = [author for author in authors if author]
            doi = entry.findtext("arxiv:doi", default=None, namespaces=namespace)
            link = None
            for candidate in entry.findall("atom:link", namespace):
                if candidate.attrib.get("rel") == "alternate":
                    link = candidate.attrib.get("href")
                    break
            arxiv_id = None
            entry_id = (entry.findtext("atom:id", default="", namespaces=namespace) or "").strip()
            if entry_id:
                arxiv_id = entry_id.rsplit("/", 1)[-1]
            papers.append(
                Paper(
                    title=title or keyword,
                    authors=authors,
                    published_date=published[:10] or None,
                    year=year,
                    source="arxiv",
                    topic="",
                    keyword=keyword,
                    url=link or entry_id or None,
                    doi=doi,
                    arxiv_id=arxiv_id,
                )
            )
        return papers
