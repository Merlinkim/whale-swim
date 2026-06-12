from __future__ import annotations

from pathlib import Path
import argparse
import signal
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.collector import collect_papers
from src.config_loader import AppConfig, load_config
from src.report.csv_export import export_csv
from src.report.html_generator import generate_html
from src.report.json_export import export_json
from src.storage.sqlite_store import SQLitePaperStore


def parse_schedule(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)


def _paper_sort_key(record: dict[str, object]) -> tuple[int, str]:
    published_date = record.get("published_date")
    year = record.get("year")
    if isinstance(published_date, str) and published_date:
        return (0, published_date)
    if isinstance(year, int):
        return (1, f"{year:04d}")
    return (2, str(record.get("title", "")))


def sort_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(records, key=_paper_sort_key)


def run_index_update(config: AppConfig, topic_filter: str | None = None) -> dict[str, object]:
    store = SQLitePaperStore(config.global_config.database_path)
    try:
        papers = collect_papers(config, topic_filter=topic_filter)
        store.upsert_many(papers)
        records = sort_records(store.list_papers())
        output_dir = Path(config.global_config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        export_json(records, output_dir / "latest_results.json")
        export_csv(records, output_dir / "latest_results.csv")
        generate_html(
            records,
            output_dir / "index.html",
            topics=[topic.name for topic in config.topics],
            source_labels=[
                ("openalex", "OpenAlex"),
                ("arxiv", "ArXiv"),
                ("semantic_scholar", "Semantic Scholar"),
                ("ieee_xplore", "IEEE Xplore"),
                ("google_scholar", "Google Scholar"),
            ],
        )
        return {
            "count": len(records),
            "database_path": str(config.global_config.database_path),
            "output_dir": str(output_dir),
        }
    finally:
        store.close()


def start_scheduler(config: AppConfig, topic_filter: str | None = None) -> BackgroundScheduler:
    hour, minute = parse_schedule(config.global_config.daily_schedule)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: run_index_update(config, topic_filter=topic_filter),
        CronTrigger(hour=hour, minute=minute),
        id="daily_paper_index_update",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run scheduled paper indexing updates.")
    parser.add_argument("--config", default="config/paper_targets.yaml")
    parser.add_argument("--topic", default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    run_index_update(config, topic_filter=args.topic)
    scheduler = start_scheduler(config, topic_filter=args.topic)

    stop = threading.Event()

    def _shutdown(*_: object) -> None:
        stop.set()
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    stop.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
