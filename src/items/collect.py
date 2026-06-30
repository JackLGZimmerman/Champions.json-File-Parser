from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from shared import (
    data_segment_dir,
    fetch_json,
    load_jsonl,
    write_jsonl,
)

ITEMS_URL = (
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
    "global/en_gb/v1/items.json"
)
ITEMS_DATA_DIR = data_segment_dir("items")
ITEMS_FILE_PATH = ITEMS_DATA_DIR / "items.jsonl"


def fetch_items_raw(timeout: int = 10) -> list[dict[str, Any]]:
    data: Any = fetch_json(ITEMS_URL, timeout=timeout)
    if not isinstance(data, list):
        raise ValueError("Item payload must be a JSON array.")
    return data


def load_items_collected(path: Path = ITEMS_FILE_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Item data file not found: {path}")

    records = load_jsonl(path)
    if not isinstance(records, list):
        raise ValueError("Collected item payload must be a JSON array.")
    return [
        item
        for item in records
        if isinstance(item, dict)
    ]


def write_items_collected(
    data: list[dict[str, Any]],
    path: Path = ITEMS_FILE_PATH,
) -> None:
    write_jsonl(data, path)


def collect(output_path: Path = ITEMS_FILE_PATH, timeout: int = 10) -> None:
    data = fetch_items_raw(timeout=timeout)
    write_items_collected(data, path=output_path)
    print(f"Wrote item payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect(timeout=args.timeout)


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "items",
        help="Collect item data into data/items/",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout in seconds.",
    )
    parser.set_defaults(handler=run_from_args)
