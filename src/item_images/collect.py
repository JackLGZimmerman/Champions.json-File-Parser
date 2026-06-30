from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from item_value_map.collect import (
    EXCLUDED_ITEM_VALUE_MAP_IDS,
    LEGENDARY_ITEM_VALUE_MAP_ADDITION_IDS,
    extract_legendary_item_ids,
)
from items.collect import ITEMS_FILE_PATH, load_items_collected
from items.relationships import extract_related_non_legendary_item_ids
from shared import write_jsonl

ITEM_INFO_FILE_PATH = ITEMS_FILE_PATH.parent / "item_info.jsonl"
COMMUNITY_DRAGON_BASE_URL = "https://raw.communitydragon.org/latest/game"


def build_item_image_url(icon_path: str) -> str:
    return COMMUNITY_DRAGON_BASE_URL + icon_path.lower().replace("/lol-game-data/assets", "")


def is_eligible_item_info_item(item: dict[str, Any]) -> bool:
    item_id = item.get("id")
    is_value_map_exception = item_id in LEGENDARY_ITEM_VALUE_MAP_ADDITION_IDS

    return (
        isinstance(item_id, int)
        and isinstance(item.get("name"), str)
        and isinstance(item.get("iconPath"), str)
        and (item.get("inStore") is True or is_value_map_exception)
        and isinstance(item.get("priceTotal"), int)
        and item.get("priceTotal", 0) >= 200
    )


def extract_item_info(
    items: list[dict[str, Any]],
    *,
    legendary_item_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    if legendary_item_ids is None:
        legendary_item_ids = extract_legendary_item_ids(items)

    items_by_id = {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    non_legendary_item_ids = extract_related_non_legendary_item_ids(items, legendary_item_ids)
    included_item_ids = legendary_item_ids | non_legendary_item_ids

    records: list[dict[str, Any]] = []
    for item_id in sorted(included_item_ids):
        item = items_by_id.get(item_id)
        if item is None:
            continue
        if item_id in EXCLUDED_ITEM_VALUE_MAP_IDS:
            continue
        if not is_eligible_item_info_item(item):
            continue

        records.append(
            {
                "id": item_id,
                "name": item["name"],
                "price": item["priceTotal"],
                "image": build_item_image_url(item["iconPath"]),
            }
        )

    return records


def collect(
    input_path: Path = ITEMS_FILE_PATH,
    output_path: Path = ITEM_INFO_FILE_PATH,
) -> None:
    items = load_items_collected(input_path)
    legendary_item_ids = extract_legendary_item_ids(items)
    records = extract_item_info(items, legendary_item_ids=legendary_item_ids)
    write_jsonl(records, output_path)

    print(f"Wrote item info payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "item-images",
        help="Extract item info data into data/items/",
    )
    parser.set_defaults(handler=run_from_args)
