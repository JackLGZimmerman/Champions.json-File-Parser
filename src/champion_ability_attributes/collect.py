from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champion_ability_advanced.detailed_features import (
    build_champion_ability_detailed_features,
    save_champion_ability_detailed_features,
)
from champion_ability_advanced.paths import (
    ABILITY_ADVANCED_FILE_PATH,
    CHAMPION_ABILITY_DETAILED_FEATURES_FILE_PATH,
)
from champion_ability_attributes.generate_final_features import (
    build_champion_ability_scaling_profiles,
    extract_final_ability_attribute_features,
    save_ability_attribute_features,
    save_champion_ability_scaling_profiles,
)
from champion_ability_attributes.paths import (
    ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
    CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
)
from champions.communitydragon import (
    COMMUNITYDRAGON_FORMATTED_PATH,
    load_formatted_communitydragon_data,
)
from shared import load_jsonl


def collect(
    input_path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
    output_path: Path = ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
    profile_output_path: Path = CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
    ability_input_path: Path = ABILITY_ADVANCED_FILE_PATH,
    detailed_output_path: Path = CHAMPION_ABILITY_DETAILED_FEATURES_FILE_PATH,
) -> None:
    formatted_payload = load_formatted_communitydragon_data(input_path, refresh=False)
    attribute_rows = extract_final_ability_attribute_features(formatted_payload)
    profile_rows = build_champion_ability_scaling_profiles(attribute_rows)
    ability_rows = load_jsonl(ability_input_path)
    detailed_rows = build_champion_ability_detailed_features(
        ability_rows,
        attribute_rows,
    )
    save_ability_attribute_features(attribute_rows, path=output_path)
    save_champion_ability_scaling_profiles(profile_rows, path=profile_output_path)
    save_champion_ability_detailed_features(
        detailed_rows,
        path=detailed_output_path,
    )
    print(f"Wrote champion ability attribute features to {output_path}")
    print(f"Wrote champion ability scaling profile to {profile_output_path}")
    print(f"Wrote champion ability detailed features to {detailed_output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champion-ability-attributes",
        help=(
            "Extract CommunityDragon ability attribute features, champion scaling "
            "profiles, and detailed features into data/champion-ability-advanced/"
        ),
    )
    parser.set_defaults(handler=run_from_args)
