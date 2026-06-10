from __future__ import annotations

from pathlib import Path
import csv


CSV_FIELDS = [
    "title",
    "authors",
    "published_date",
    "year",
    "source",
    "topic",
    "keyword",
    "url",
    "doi",
    "arxiv_id",
    "unique_key",
]


def export_csv(papers: list[dict[str, object]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for paper in papers:
            row = {field: paper.get(field) for field in CSV_FIELDS}
            if isinstance(row["authors"], list):
                row["authors"] = "; ".join(row["authors"])
            writer.writerow(row)
    return path
