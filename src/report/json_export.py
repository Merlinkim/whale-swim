from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone


def export_json(papers: list[dict[str, object]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(papers),
        "papers": papers,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return path
