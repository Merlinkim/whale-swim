from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GlobalConfig:
    database_path: str = "data/papers.db"
    output_dir: str = "outputs"
    min_year: int = 2020
    max_results_per_keyword: int = 50
    daily_schedule: str = "06:00"
    request_timeout_seconds: int = 20


@dataclass
class SourceFlags:
    enabled: bool = False


@dataclass
class TopicConfig:
    name: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    global_config: GlobalConfig
    sources: dict[str, SourceFlags]
    topics: list[TopicConfig]
    config_path: Path


DEFAULT_SOURCE_ORDER = ["openalex", "semantic_scholar", "arxiv", "google_scholar"]


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return bool(value)


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path)
    data = yaml.safe_load(path.read_text()) or {}

    global_section = data.get("global", {})
    global_config = GlobalConfig(
        database_path=str(global_section.get("database_path", "data/papers.db")),
        output_dir=str(global_section.get("output_dir", "outputs")),
        min_year=int(global_section.get("min_year", 2020)),
        max_results_per_keyword=int(global_section.get("max_results_per_keyword", 50)),
        daily_schedule=str(global_section.get("daily_schedule", "06:00")),
        request_timeout_seconds=int(global_section.get("request_timeout_seconds", 20)),
    )

    sources_section = data.get("sources", {})
    sources: dict[str, SourceFlags] = {}
    for source_name in DEFAULT_SOURCE_ORDER:
        source_data = sources_section.get(source_name, {})
        sources[source_name] = SourceFlags(enabled=_as_bool(source_data.get("enabled", False)))

    topics: list[TopicConfig] = []
    for topic in data.get("topics", []):
        topics.append(
            TopicConfig(
                name=str(topic.get("name", "")).strip(),
                keywords=[str(keyword).strip() for keyword in topic.get("keywords", []) if str(keyword).strip()],
            )
        )

    if not topics:
        raise ValueError("config must define at least one topic")

    return AppConfig(global_config=global_config, sources=sources, topics=topics, config_path=path)


def topic_names(config: AppConfig) -> list[str]:
    return [topic.name for topic in config.topics]
