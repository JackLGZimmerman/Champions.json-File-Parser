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


def empty_champion_scaling_profile(
    champion_id: int,
    champion_name: str,
    feature_names: list[str],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "_key": str(champion_id),
        "championId": champion_id,
        "championName": champion_name,
        "ability_count": 0,
        "scaling_ability_count": 0,
        "scaling_trait_type_count": 0,
        "scaling_trait_match_count": 0,
        "scaling_stage_match_count": 0,
    }
    for feature_name in feature_names:
        row[f"{feature_name}_ability_count"] = 0
        row[f"{feature_name}_stage_count"] = 0
    return row


def build_champion_ability_scaling_profiles(
    attribute_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_names = attribute_stat_types_from_rows(attribute_rows)
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
                feature_names,
            )
        profile = profiles[champion_id]
        stage_count = attribute_row.get("stageCount")
        if not isinstance(stage_count, int) or stage_count < 1:
            stage_count = 1

        profile["ability_count"] += 1
        ability_stat_count = 0
        for feature_name in feature_names:
            if attribute_row.get(feature_name) != 1:
                continue
            profile[f"{feature_name}_ability_count"] += 1
            profile[f"{feature_name}_stage_count"] += stage_count
            ability_stat_count += 1

        if ability_stat_count:
            profile["scaling_ability_count"] += 1
            profile["scaling_trait_match_count"] += ability_stat_count
            profile["scaling_stage_match_count"] += ability_stat_count * stage_count

    for profile in profiles.values():
        profile["scaling_trait_type_count"] = sum(
            1
            for feature_name in feature_names
            if profile[f"{feature_name}_ability_count"] > 0
        )

    return sorted(
        profiles.values(),
        key=lambda profile: (
            str(profile.get("championName") or ""),
            int(profile.get("championId") or 0),
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
