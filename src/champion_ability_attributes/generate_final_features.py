from __future__ import annotations

from pathlib import Path
from typing import Any

from champion_ability_attributes.paths import ABILITY_ATTRIBUTE_FEATURES_FILE_PATH
from champion_ability_attributes.scaling_detection import (
    extract_ability_concepts,
    extract_ability_scaling_stats,
)
from champions.communitydragon import build_ability_row_base, iter_formatted_abilities
from shared import write_jsonl


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


def save_ability_attribute_features(
    attribute_rows: list[dict[str, Any]],
    path: Path = ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
) -> None:
    write_jsonl(attribute_rows, path)
