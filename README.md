# Paper Indexer

Local-first academic paper indexing system for browsing paper metadata from OpenAlex, arXiv, Semantic Scholar, and optional Google Scholar.

This project intentionally does **not** summarize, score, classify, or rank papers. It only collects, stores, sorts, filters, and displays metadata.

## Features

- Python 3.11+
- SQLite storage
- Static HTML output
- Client-side filtering and sorting
- Docker Compose deployment
- Daily scheduled refreshes inside the container
- Optional Google Scholar source, disabled by default

## Project Layout

- `config/paper_targets.yaml`: topic and source configuration
- `data/papers.db`: SQLite database
- `outputs/index.html`: generated static site
- `outputs/latest_results.json`: JSON export
- `outputs/latest_results.csv`: CSV export

## Installation

Install dependencies locally:

```bash
python3.11 -m pip install -r requirements.txt
```

## Configuration

Edit `config/paper_targets.yaml` to control:

- database path
- output directory
- minimum year
- maximum results per keyword
- daily schedule
- enabled sources
- topics and keywords

Add new topics by appending another topic block with a `name` and `keywords` list.

## Manual Run

Run one indexing pass:

```bash
python -m src.main --config config/paper_targets.yaml --once
```

Run only one topic:

```bash
python -m src.main --config config/paper_targets.yaml --topic slam --once
```

Run the scheduler service directly:

```bash
python -m src.scheduler --config config/paper_targets.yaml
```

## Docker Usage

Build and start the service:

```bash
docker compose build
docker compose up -d
```

Open:

```text
http://localhost:8089
```

Manual one-time Docker run:

```bash
docker compose run --rm paper-indexer python -m src.main --config config/paper_targets.yaml --once
```

## Volumes

The container expects these bind mounts:

- `./data:/app/data`
- `./outputs:/app/outputs`
- `./config:/app/config`

These keep the database, generated site, and configuration persistent across restarts.

## Daily Updates

The default schedule is `06:00` every day. The long-running container:

1. loads config
2. fetches metadata
3. updates SQLite
4. regenerates the static site
5. serves `outputs/` on port `8080` inside the container and maps it to host port `8089`
6. keeps a daily scheduler running

## Google Scholar Limitations

Google Scholar is disabled by default.

- It may fail because of CAPTCHA, rate limits, or anti-bot protection.
- The implementation stops immediately when unusual traffic is detected.
- No bypass or evasion logic is included.
- If enabled, it appears as its own source tab.

## Mac mini deployment example

1. Clone the repository on the Mac mini.
2. Edit `config/paper_targets.yaml`.
3. Run:

```bash
docker compose up -d
```

4. Open `http://localhost:8089` in a browser on the machine or via the local network.

## VPS deployment example

1. Install Docker and Docker Compose on the VPS.
2. Clone the repository.
3. Expose port `8089` through your firewall or reverse proxy.
4. Start the service:

```bash
docker compose up -d
```

If you want a different host port, adjust the Compose port mapping.

## Local Serving

The generated site is a single-page static HTML app. It does not require a database server or any backend process once generated.

## Troubleshooting

- If a source returns no data, check the network and source rate limits.
- If Google Scholar is enabled and returns no data, CAPTCHAs or unusual traffic detection likely blocked the request.
- If the page is empty, verify the config keywords and `min_year`.
- If Docker cannot bind port `8089`, change the port mapping in `docker-compose.yml`.

## Example Generated HTML Structure

The generated page is a single HTML file with:

- a header
- search inputs for title and author
- topic selector
- sort selector
- source tabs
- a card list rendered client-side from embedded JSON

## Scheduler Configuration Example

Default cron-style schedule:

```yaml
global:
  daily_schedule: "06:00"
```

Equivalent daily cron intent:

```text
0 6 * * *
```

## Known Limitations

- Data quality depends on the upstream source metadata.
- The current implementation stores one merged record per deduplicated paper.
- Google Scholar is best-effort only.
- The static site is intentionally simple and client-side only.

## Future Extension Points

- Add more metadata sources.
- Add pagination or lazy loading in the HTML view.
- Add richer export formats.
- Add incremental source caching.
- Add scheduled source-specific refresh controls.
