from __future__ import annotations

from pathlib import Path
from typing import Any

from champion_ability_ratios.paths import (
    ABILITY_RATIO_FEATURES_FILE_PATH,
    CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
)
from champion_ability_ratios.scaling_detection import extract_ability_scaling_stats
from champions.communitydragon import build_ability_row_base, iter_formatted_abilities
from shared import write_jsonl

RATIO_IDENTITY_FIELDS = frozenset(
    ("_key", "championName", "championId", "abilityKey", "stageCount")
)


def collect_partial_rows_and_stat_types(
    formatted_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    partial_rows: list[dict[str, Any]] = []
    stat_types: set[str] = set()

    for champion_name, champion_info, ability_key, ability in iter_formatted_abilities(
        formatted_payload
    ):
        stats = extract_ability_scaling_stats(ability)
        stat_types.update(stats)
        partial_rows.append(
            {
                **build_ability_row_base(champion_name, champion_info, ability_key),
                "stageCount": max(
                    len(ability.get("damageParts", []))
                    if isinstance(ability.get("damageParts"), list)
                    else 0,
                    1,
                ),
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


def extract_final_ability_ratio_features(
    formatted_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    partial_rows, stat_types = collect_partial_rows_and_stat_types(formatted_payload)
    return build_final_feature_rows(partial_rows, stat_types)


def ratio_stat_types_from_rows(ratio_rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            key
            for row in ratio_rows
            for key, value in row.items()
            if key not in RATIO_IDENTITY_FIELDS and value in {0, 1}
        }
    )


def empty_champion_scaling_profile(
    champion_id: int,
    champion_name: str,
    stat_types: list[str],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "_key": str(champion_id),
        "championName": champion_name,
        "championId": champion_id,
        "abilityCount": 0,
        "scalingAbilityCount": 0,
        "scalingTypeCount": 0,
        "scalingStatMentionCount": 0,
        "scalingStageMentionCount": 0,
    }
    for stat_type in stat_types:
        row[f"{stat_type}_ability_count"] = 0
        row[f"{stat_type}_stage_count"] = 0
    return row


def build_champion_ability_scaling_profiles(
    ratio_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stat_types = ratio_stat_types_from_rows(ratio_rows)
    profiles: dict[int, dict[str, Any]] = {}

    for ratio_row in ratio_rows:
        champion_id = ratio_row.get("championId")
        champion_name = ratio_row.get("championName")
        if not isinstance(champion_id, int) or not isinstance(champion_name, str):
            continue

        if champion_id not in profiles:
            profiles[champion_id] = empty_champion_scaling_profile(
                champion_id,
                champion_name,
                stat_types,
            )
        profile = profiles[champion_id]
        stage_count = ratio_row.get("stageCount")
        if not isinstance(stage_count, int) or stage_count < 1:
            stage_count = 1

        profile["abilityCount"] += 1
        ability_stat_count = 0
        for stat_type in stat_types:
            if ratio_row.get(stat_type) != 1:
                continue
            profile[f"{stat_type}_ability_count"] += 1
            profile[f"{stat_type}_stage_count"] += stage_count
            ability_stat_count += 1

        if ability_stat_count:
            profile["scalingAbilityCount"] += 1
            profile["scalingStatMentionCount"] += ability_stat_count
            profile["scalingStageMentionCount"] += ability_stat_count * stage_count

    for profile in profiles.values():
        profile["scalingTypeCount"] = sum(
            1
            for stat_type in stat_types
            if profile[f"{stat_type}_ability_count"] > 0
        )

    return sorted(
        profiles.values(),
        key=lambda profile: (
            str(profile.get("championName") or ""),
            int(profile.get("championId") or 0),
        ),
    )


def save_ability_ratio_features(
    ratio_rows: list[dict[str, Any]],
    path: Path = ABILITY_RATIO_FEATURES_FILE_PATH,
) -> None:
    write_jsonl(ratio_rows, path)


def save_champion_ability_scaling_profiles(
    profile_rows: list[dict[str, Any]],
    path: Path = CHAMPION_ABILITY_SCALING_PROFILE_FILE_PATH,
) -> None:
    write_jsonl(profile_rows, path)
