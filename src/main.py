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


def write_loading_page(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.html"
    if index_path.exists():
        return
    index_path.write_text(
        """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paper Indexer</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f6f5f0; color: #222; }
    .box { max-width: 720px; margin: 0 auto; background: white; border: 1px solid #ddd; border-radius: 16px; padding: 24px; }
    h1 { margin-top: 0; }
  </style>
</head>
<body>
  <div class="box">
    <h1>Paper Indexer</h1>
    <p>데이터를 불러오는 중입니다. 잠시 후 다시 새로고침해 주세요.</p>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local-first academic paper indexer.")
    parser.add_argument("--config", default="config/paper_targets.yaml")
    parser.add_argument("--topic", default=None)
    parser.add_argument("--once", action="store_true", help="Run a single update and exit.")
    parser.add_argument("--serve", action="store_true", help="Serve the generated outputs directory on the configured port.")
    parser.add_argument("--schedule", action="store_true", help="Enable the daily scheduled update loop.")
    args = parser.parse_args(argv)

    config = load_config(args.config)

    if args.once and not args.serve and not args.schedule:
        run_index_update(config, topic_filter=args.topic)
        return 0

    server = None
    scheduler = None
    stop_event = threading.Event()
    output_dir = Path(config.global_config.output_dir)

    if args.serve:
        write_loading_page(output_dir)
        server = serve_directory(output_dir, port=config.global_config.port)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

    def _run_initial_update() -> None:
        run_index_update(config, topic_filter=args.topic)

    update_thread = threading.Thread(target=_run_initial_update, daemon=True)
    update_thread.start()

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
        update_thread.join()
        return 0

    update_thread.join()
    stop_event.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
