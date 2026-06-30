from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champions.collect import CHAMPION_VALIDATED_PATH, load_champion_info_validated
from shared import data_segment_dir, write_jsonl

STATIC_DATA_DIR = data_segment_dir("champion-static-basic")
STATIC_FILE_PATH = STATIC_DATA_DIR / "basic_stats.jsonl"
CHAMPION_LEVEL_FIELDS = ("adaptiveType", "attackType", "resource")


def flatten_stat_values(stats: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for stat_name, stat_value in stats.items():
        if isinstance(stat_value, dict):
            for modifier_name, modifier_value in stat_value.items():
                flattened[f"{stat_name}_{modifier_name}"] = modifier_value
        else:
            flattened[stat_name] = stat_value
    return flattened


def extract_basic_static(validation_json: dict[str, Any]) -> dict[str, Any]:
    c_stats: dict[str, Any] = {}
    for c_name, c_info in validation_json.items():
        champion_id = c_info.get("id")
        stats = c_info.get("stats", {})
        if isinstance(champion_id, int) and isinstance(stats, dict) and stats:
            champion_level_values = {
                field_name: c_info.get(field_name)
                for field_name in CHAMPION_LEVEL_FIELDS
            }
            c_stats[c_name] = {
                "id": champion_id,
                **champion_level_values,
                **flatten_stat_values(stats),
            }
    return c_stats


def save_champion_static_data(
    champion_static_stats: dict[str, Any],
    path: Path = STATIC_FILE_PATH,
) -> None:
    records = [
        {"_key": champion_name, **stats}
        for champion_name, stats in champion_static_stats.items()
        if isinstance(stats, dict)
    ]
    write_jsonl(records, path)


def collect(
    input_path: Path = CHAMPION_VALIDATED_PATH,
    output_path: Path = STATIC_FILE_PATH,
) -> None:
    validation_json = load_champion_info_validated(input_path)
    champion_static_stats = extract_basic_static(validation_json)
    save_champion_static_data(champion_static_stats, path=output_path)
    print(f"Wrote champion static basic payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champion-static-basic",
        help="Extract basic champion stats into data/champion-static-basic/",
    )
    parser.set_defaults(handler=run_from_args)
