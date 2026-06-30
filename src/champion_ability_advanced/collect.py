from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champion_ability_advanced.extract import (
    build_raw_field_coverage,
    build_raw_nested_path_rows,
    extract_ability_advanced,
)
from champion_ability_advanced.paths import (
    ABILITY_ADVANCED_FILE_PATH,
    RAW_FIELD_COVERAGE_FILE_PATH,
    RAW_NESTED_PATHS_FILE_PATH,
)
from champions.communitydragon import (
    COMMUNITYDRAGON_FORMATTED_PATH,
    load_formatted_communitydragon_data,
)
from shared import write_json, write_jsonl


def collect(
    input_path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
    output_path: Path = ABILITY_ADVANCED_FILE_PATH,
    raw_field_coverage_path: Path = RAW_FIELD_COVERAGE_FILE_PATH,
    raw_nested_paths_path: Path = RAW_NESTED_PATHS_FILE_PATH,
) -> None:
    formatted_payload = load_formatted_communitydragon_data(input_path, refresh=True)
    ability_rows = extract_ability_advanced(formatted_payload)
    write_jsonl(ability_rows, output_path)
    write_json(
        build_raw_field_coverage(ability_rows),
        raw_field_coverage_path,
        sort_keys=True,
    )
    write_jsonl(build_raw_nested_path_rows(ability_rows), raw_nested_paths_path)
    print(f"Wrote champion ability advanced payload to {output_path}")
    print(f"Wrote champion ability raw field coverage to {raw_field_coverage_path}")
    print(f"Wrote champion ability raw nested paths to {raw_nested_paths_path}")
    print(f"Wrote formatted CommunityDragon ability source to {input_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champion-ability-advanced",
        help="Extract CommunityDragon champion ability fields into data/champion-ability-advanced/",
    )
    parser.set_defaults(handler=run_from_args)
