from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import threading

from src.collector import collect_papers
from src.config_loader import load_config
from src.report.csv_export import export_csv
from src.report.html_generator import generate_html
from src.report.json_export import export_json
from src.scheduler import run_index_update, start_scheduler
from src.storage.sqlite_store import SQLitePaperStore


def serve_directory(directory: Path, host: str = "0.0.0.0", port: int = 8089) -> ThreadingHTTPServer:
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((host, port), handler)
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local-first academic paper indexer.")
    parser.add_argument("--config", default="config/paper_targets.yaml")
    parser.add_argument("--topic", default=None)
    parser.add_argument("--once", action="store_true", help="Run a single update and exit.")
    parser.add_argument("--serve", action="store_true", help="Serve the generated outputs directory on the configured port.")
    parser.add_argument("--schedule", action="store_true", help="Enable the daily scheduled update loop.")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    result = run_index_update(config, topic_filter=args.topic)
    if args.once and not args.serve and not args.schedule:
        return 0

    server = None
    scheduler = None
    stop_event = threading.Event()

    if args.serve:
        output_dir = Path(config.global_config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        server = serve_directory(output_dir, port=config.global_config.port)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

    if args.schedule:
        scheduler = start_scheduler(config, topic_filter=args.topic)

    def _shutdown(*_: object) -> None:
        stop_event.set()
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        if server is not None:
            server.shutdown()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    if not args.serve and not args.schedule:
        return 0

    stop_event.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
