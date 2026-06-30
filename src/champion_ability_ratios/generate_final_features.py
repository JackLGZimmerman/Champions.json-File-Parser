from __future__ import annotations

from pathlib import Path
from typing import Any

from champion_ability_ratios.paths import ABILITY_RATIO_FEATURES_FILE_PATH
from champion_ability_ratios.scaling_detection import extract_ability_scaling_stats
from champions.communitydragon import build_ability_row_base, iter_formatted_abilities
from shared import write_jsonl


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


def save_ability_ratio_features(
    ratio_rows: list[dict[str, Any]],
    path: Path = ABILITY_RATIO_FEATURES_FILE_PATH,
) -> None:
    write_jsonl(ratio_rows, path)
