from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champions.communitydragon import (
    CHAMP_ID_NAME_MAP_PATH,
    extract_champ_id_name_rows,
    fetch_communitydragon_index_entries,
    save_champ_id_name_rows,
)


def collect(output_path: Path = CHAMP_ID_NAME_MAP_PATH) -> None:
    index_entries = fetch_communitydragon_index_entries()
    rows = extract_champ_id_name_rows(index_entries)
    save_champ_id_name_rows(rows, path=output_path)
    print(f"Wrote CommunityDragon champion id-name map payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champ-id-name-map",
        help="Extract CommunityDragon champion id and alias rows into data/champions/",
    )
    parser.set_defaults(handler=run_from_args)
