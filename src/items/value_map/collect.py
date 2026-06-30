from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from items.value_map.scoring import (
    ITEM_VALUE_MAP_FILE_PATH,
    calculate_build_values,
)


def collect(
    output_path: Path = ITEM_VALUE_MAP_FILE_PATH,
) -> None:
    calculate_build_values(output_path=output_path)
    print(f"Wrote item value map payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "item-value-map",
        help="Extract item value map data into data/items/",
    )
    parser.set_defaults(handler=run_from_args)
