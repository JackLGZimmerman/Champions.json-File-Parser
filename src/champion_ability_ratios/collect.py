from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from champion_ability_ratios.generate_final_features import (
    build_champion_ability_scaling_profiles,
    extract_final_ability_ratio_features,
    save_ability_ratio_features,
    save_champion_ability_scaling_profiles,
)
from champion_ability_ratios.paths import (
    ABILITY_RATIO_FEATURES_FILE_PATH,
    CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
)
from champions.communitydragon import (
    COMMUNITYDRAGON_FORMATTED_PATH,
    load_formatted_communitydragon_data,
)

def collect(
    input_path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
    output_path: Path = ABILITY_RATIO_FEATURES_FILE_PATH,
    profile_output_path: Path = CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
) -> None:
    formatted_payload = load_formatted_communitydragon_data(input_path, refresh=False)
    ratio_rows = extract_final_ability_ratio_features(formatted_payload)
    profile_rows = build_champion_ability_scaling_profiles(ratio_rows)
    save_ability_ratio_features(ratio_rows, path=output_path)
    save_champion_ability_scaling_profiles(profile_rows, path=profile_output_path)
    print(f"Wrote champion ability ratio features to {output_path}")
    print(f"Wrote champion ability scaling profile to {profile_output_path}")


def run_from_args(args: Namespace) -> None:
    collect()


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champion-ability-ratios",
        help=(
            "Extract CommunityDragon ability ratio features and champion scaling "
            "profiles into data/champion-ability-advanced/"
        ),
    )
    parser.set_defaults(handler=run_from_args)
