from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

DATA_DIR = Path("data")


def data_segment_dir(segment: str) -> Path:
    return DATA_DIR / segment


def fetch_json(url: str, timeout: int = 10) -> Any:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[Any]:
    records: list[Any] = []
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_json(data: Any, path: Path, *, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=sort_keys,
        )


def write_jsonl(records: list[Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
