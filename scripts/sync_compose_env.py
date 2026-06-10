from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "paper_targets.yaml"
ENV_PATH = ROOT / ".env"


def main() -> int:
    text = CONFIG_PATH.read_text()
    match = re.search(r"(?m)^\s*port:\s*(\d+)\s*$", text)
    port = int(match.group(1)) if match else 8089

    ENV_PATH.write_text(f"PAPER_PORT={port}\n")
    print(f"Wrote {ENV_PATH} with PAPER_PORT={port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
