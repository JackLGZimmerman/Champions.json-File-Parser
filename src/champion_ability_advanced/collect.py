from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champions.communitydragon import (
    COMMUNITYDRAGON_FORMATTED_PATH,
    build_ability_row_base,
    iter_formatted_abilities,
    load_formatted_communitydragon_data,
)
from shared import data_segment_dir, write_jsonl

ABILITY_ADVANCED_DATA_DIR = data_segment_dir("champion-ability-advanced")
ABILITY_ADVANCED_FILE_PATH = ABILITY_ADVANCED_DATA_DIR / "abilities.jsonl"


def extract_ability_advanced(formatted_payload: dict[str, Any]) -> list[dict[str, Any]]:
    ability_rows: list[dict[str, Any]] = []

    for champion_name, champion_info, ability_key, ability in iter_formatted_abilities(
        formatted_payload
    ):
        row = build_ability_row_base(champion_name, champion_info, ability_key)
        row["abilityIndex"] = 0
        row.update(
            {
                "affect": ability.get("affect"),
                "angle": ability.get("angle", 0.0),
                "castTime": ability.get("castTime", 0.0),
                "collisionRadius": ability.get("collisionRadius", 0.0),
                "damageType": ability.get("damageType"),
                "innerRadius": ability.get("innerRadius", 0.0),
                "onTargetCdStatic": ability.get("onTargetCdStatic", 0.0),
                "projectile": ability.get("projectile"),
                "rechargeRate": ability.get("rechargeRate", 0.0),
                "resource": ability.get("resource"),
                "speed": ability.get("speed", 0.0),
                "spellEffects": ability.get("spellEffects"),
                "spellshieldable": ability.get("spellshieldable"),
                "targetRange": ability.get("targetRange", 0.0),
                "targetting": ability.get("targetting"),
                "tetherRadius": ability.get("tetherRadius", 0.0),
                "width": ability.get("width", 0.0),
            }
        )
        ability_rows.append(row)

    return ability_rows


def collect(
    input_path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
    output_path: Path = ABILITY_ADVANCED_FILE_PATH,
) -> None:
    formatted_payload = load_formatted_communitydragon_data(input_path, refresh=True)
    ability_rows = extract_ability_advanced(formatted_payload)
    write_jsonl(ability_rows, output_path)
    print(f"Wrote champion ability advanced payload to {output_path}")
    print(f"Wrote formatted CommunityDragon ability source to {input_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champion-ability-advanced",
        help="Extract CommunityDragon champion ability fields into data/champion-ability-advanced/",
    )
    parser.set_defaults(handler=run_from_args)
