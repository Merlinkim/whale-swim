from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(title: str) -> str:
    cleaned = _clean_whitespace(title).casefold()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")))
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value.casefold()


def normalize_arxiv_id(arxiv_id: str | None) -> str | None:
    if not arxiv_id:
        return None
    value = arxiv_id.strip()
    value = re.sub(r"^arxiv:", "", value, flags=re.IGNORECASE)
    return value.casefold()


def merge_tokens(existing: str | None, incoming: str | None) -> str | None:
    values: list[str] = []
    for item in (existing, incoming):
        if not item:
            continue
        for token in item.split(","):
            cleaned = token.strip()
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return ", ".join(values) if values else None


@dataclass
class Paper:
    title: str
    authors: list[str]
    published_date: str | None = None
    year: int | None = None
    source: str = ""
    topic: str = ""
    keyword: str = ""
    url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def unique_key(self) -> str:
        if self.doi:
            return f"doi:{normalize_doi(self.doi)}"
        if self.arxiv_id:
            return f"arxiv:{normalize_arxiv_id(self.arxiv_id)}"
        if self.title:
            return f"title:{normalize_title(self.title)}"
        if self.url:
            return f"url:{normalize_url(self.url)}"
        return f"title:{normalize_title(self.title)}"

    @property
    def normalized_title(self) -> str:
        return normalize_title(self.title)

    @property
    def normalized_url(self) -> str | None:
        return normalize_url(self.url) if self.url else None

    @property
    def normalized_doi(self) -> str | None:
        return normalize_doi(self.doi)

    @property
    def normalized_arxiv_id(self) -> str | None:
        return normalize_arxiv_id(self.arxiv_id)

    def merge_with(self, other: "Paper") -> "Paper":
        return Paper(
            title=self.title or other.title,
            authors=self.authors or other.authors,
            published_date=self.published_date or other.published_date,
            year=self.year or other.year,
            source=merge_tokens(self.source, other.source) or "",
            topic=merge_tokens(self.topic, other.topic) or "",
            keyword=merge_tokens(self.keyword, other.keyword) or "",
            url=self.url or other.url,
            doi=self.doi or other.doi,
            arxiv_id=self.arxiv_id or other.arxiv_id,
        )
