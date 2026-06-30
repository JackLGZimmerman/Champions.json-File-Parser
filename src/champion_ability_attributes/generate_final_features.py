from __future__ import annotations

from pathlib import Path
from typing import Any

from champion_ability_attributes.paths import (
    ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
    CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
)
from champion_ability_attributes.scaling_detection import (
    extract_ability_concepts,
    extract_ability_scaling_stats,
)
from champions.communitydragon import build_ability_row_base, iter_formatted_abilities
from shared import write_jsonl

ATTRIBUTE_IDENTITY_FIELDS = frozenset(
    ("_key", "championName", "championId", "abilityKey", "stageCount")
)
FEATURE_NAME_REPLACEMENTS = (
    ("stack_scaling", "stk"),
    ("percent_", "p_"),
    ("flat_", "f_"),
    ("target_", "t_"),
    ("bonus_", "b_"),
    ("current_", "cur_"),
    ("missing_", "miss_"),
    ("magic_resistance", "mr"),
    ("magic_pen", "mpen"),
    ("armour_pen", "arpen"),
    ("armour", "ar"),
    ("attack_speed", "as"),
    ("movement_speed", "ms"),
    ("crit_chance", "crit"),
    ("eff_", "e_"),
    ("dmg_", "d_"),
    ("physical", "phys"),
    ("magic", "mag"),
)


def ability_scaling_stage_count(ability: dict[str, Any]) -> int:
    for key in ("scalingParts", "damageParts"):
        parts = ability.get(key)
        if isinstance(parts, list) and parts:
            return len(parts)
    return 1


def collect_partial_rows_and_stat_types(
    formatted_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    partial_rows: list[dict[str, Any]] = []
    stat_types: set[str] = set()

    for champion_name, champion_info, ability_key, ability in iter_formatted_abilities(
        formatted_payload
    ):
        stats = extract_ability_scaling_stats(ability) | extract_ability_concepts(ability)
        stat_types.update(stats)
        partial_rows.append(
            {
                **build_ability_row_base(champion_name, champion_info, ability_key),
                "stageCount": ability_scaling_stage_count(ability),
                "_stats": stats,
            }
        )

    return partial_rows, sorted(stat_types)


def build_final_feature_rows(
    partial_rows: list[dict[str, Any]],
    stat_types: list[str],
) -> list[dict[str, Any]]:
    final_rows: list[dict[str, Any]] = []

    for partial_row in partial_rows:
        stats = partial_row.get("_stats")
        if not isinstance(stats, set):
            stats = set()
        row = {key: value for key, value in partial_row.items() if key != "_stats"}
        for stat_type in stat_types:
            row[stat_type] = int(stat_type in stats)
        final_rows.append(row)

    return final_rows


def extract_final_ability_attribute_features(
    formatted_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    partial_rows, stat_types = collect_partial_rows_and_stat_types(formatted_payload)
    return build_final_feature_rows(partial_rows, stat_types)


def attribute_stat_types_from_rows(attribute_rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            key
            for row in attribute_rows
            for key, value in row.items()
            if key not in ATTRIBUTE_IDENTITY_FIELDS and value in {0, 1}
        }
    )


def compact_feature_name(feature_name: str) -> str:
    compact_name = feature_name
    for source, replacement in FEATURE_NAME_REPLACEMENTS:
        compact_name = compact_name.replace(source, replacement)
    return compact_name


def compact_feature_names(feature_names: list[str]) -> dict[str, str]:
    compact_names: dict[str, str] = {}
    used_names: dict[str, str] = {}

    for feature_name in feature_names:
        compact_name = compact_feature_name(feature_name)
        existing_feature = used_names.get(compact_name)
        if existing_feature is not None and existing_feature != feature_name:
            raise ValueError(
                "Compact feature name collision: "
                f"{feature_name} and {existing_feature} both map to {compact_name}"
            )
        compact_names[feature_name] = compact_name
        used_names[compact_name] = feature_name

    return compact_names


def empty_champion_scaling_profile(
    champion_id: int,
    champion_name: str,
    compact_features_by_name: dict[str, str],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "_key": str(champion_id),
        "cid": champion_id,
        "champ": champion_name,
        "ab": 0,
        "sc_ab": 0,
        "sc_ty": 0,
        "sc_m": 0,
        "sc_st": 0,
    }
    for compact_feature in compact_features_by_name.values():
        row[f"{compact_feature}_ab"] = 0
        row[f"{compact_feature}_st"] = 0
    return row


def build_champion_ability_scaling_profiles(
    attribute_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_names = attribute_stat_types_from_rows(attribute_rows)
    compact_features_by_name = compact_feature_names(feature_names)
    profiles: dict[int, dict[str, Any]] = {}

    for attribute_row in attribute_rows:
        champion_id = attribute_row.get("championId")
        champion_name = attribute_row.get("championName")
        if not isinstance(champion_id, int) or not isinstance(champion_name, str):
            continue

        if champion_id not in profiles:
            profiles[champion_id] = empty_champion_scaling_profile(
                champion_id,
                champion_name,
                compact_features_by_name,
            )
        profile = profiles[champion_id]
        stage_count = attribute_row.get("stageCount")
        if not isinstance(stage_count, int) or stage_count < 1:
            stage_count = 1

        profile["ab"] += 1
        ability_stat_count = 0
        for feature_name, compact_feature in compact_features_by_name.items():
            if attribute_row.get(feature_name) != 1:
                continue
            profile[f"{compact_feature}_ab"] += 1
            profile[f"{compact_feature}_st"] += stage_count
            ability_stat_count += 1

        if ability_stat_count:
            profile["sc_ab"] += 1
            profile["sc_m"] += ability_stat_count
            profile["sc_st"] += ability_stat_count * stage_count

    for profile in profiles.values():
        profile["sc_ty"] = sum(
            1
            for compact_feature in compact_features_by_name.values()
            if profile[f"{compact_feature}_ab"] > 0
        )

    return sorted(
        profiles.values(),
        key=lambda profile: (
            str(profile.get("champ") or ""),
            int(profile.get("cid") or 0),
        ),
    )


def save_ability_attribute_features(
    attribute_rows: list[dict[str, Any]],
    path: Path = ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
) -> None:
    write_jsonl(attribute_rows, path)


def save_champion_ability_scaling_profiles(
    profile_rows: list[dict[str, Any]],
    path: Path = CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
) -> None:
    write_jsonl(profile_rows, path)
