from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import champ_id_name_map.collect as champ_id_name_map
import champion_ability_advanced.collect as champion_ability_advanced
import champion_ability_attributes.collect as champion_ability_attributes
import champion_static_basic.collect as champion_static_basic
import champions.collect as champions
import item_images.collect as item_images
import item_value_map.collect as item_value_map
import items.collect as items

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

COLLECTION_MODULES = (
    champions,
    items,
    item_images,
    champion_static_basic,
    champion_ability_advanced,
    champion_ability_attributes,
    champ_id_name_map,
    item_value_map,
)
COLLECT_ALL_MODULES = tuple(
    module for module in COLLECTION_MODULES if module is not champ_id_name_map
)


def register_collections(subparsers: Any) -> None:
    for module in COLLECTION_MODULES:
        module.register_parser(subparsers)


def collect_all() -> None:
    for module in COLLECT_ALL_MODULES:
        module.collect()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect project data into segment folders under data/.",
    )
    subparsers = parser.add_subparsers(dest="segment")
    register_collections(subparsers)

    all_parser = subparsers.add_parser(
        "all",
        help="Collect default data segments with default settings.",
    )
    all_parser.set_defaults(handler=run_all_from_args)
    return parser


def run_all_from_args(args: Any) -> None:
    collect_all()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv or sys.argv[1:] or ["champions"])
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(2)
    handler(args)


if __name__ == "__main__":
    main()
