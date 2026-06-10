from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.config_loader import AppConfig
from src.models.paper import Paper
from src.sources.arxiv_client import ArxivClient
from src.sources.google_scholar_optional import GoogleScholarOptionalClient
from src.sources.openalex_client import OpenAlexClient
from src.sources.semantic_scholar_client import SemanticScholarClient


SOURCE_LABELS: dict[str, str] = {
    "openalex": "OpenAlex",
    "arxiv": "arXiv",
    "semantic_scholar": "Semantic Scholar",
    "google_scholar": "Google Scholar",
}


def _build_clients(timeout_seconds: int) -> dict[str, object]:
    return {
        "openalex": OpenAlexClient(timeout_seconds=timeout_seconds),
        "arxiv": ArxivClient(timeout_seconds=timeout_seconds),
        "semantic_scholar": SemanticScholarClient(timeout_seconds=timeout_seconds),
        "google_scholar": GoogleScholarOptionalClient(timeout_seconds=timeout_seconds),
    }


def collect_papers(config: AppConfig, topic_filter: str | None = None) -> list[Paper]:
    clients = _build_clients(config.global_config.request_timeout_seconds)
    papers: list[Paper] = []
    topics = [topic for topic in config.topics if topic_filter in (None, "", topic.name)]

    for topic in topics:
        for keyword in topic.keywords:
            for source_name, flags in config.sources.items():
                if not flags.enabled:
                    continue
                client = clients[source_name]
                fetch = getattr(client, "fetch")
                collected = fetch(keyword, config.global_config.max_results_per_keyword, config.global_config.min_year)
                for paper in collected:
                    paper.topic = topic.name
                    paper.keyword = keyword
                    paper.source = source_name
                papers.extend(collected)
    return papers
