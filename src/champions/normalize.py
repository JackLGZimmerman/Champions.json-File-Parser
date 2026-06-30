from __future__ import annotations

from typing import Any

from champions.models.champion_models import ChampionInformation

STAT_PREFIXES_TO_EXCLUDE = ("urf", "aram")
STAT_METRIC_EXCLUDE = {"percent", "percentPerLevel"}
ABILITY_FIELD_EXCLUDE = {"onHitEffects", "occurrence", "missileSpeed"}

EXCLUDE_MAP: dict[str, Any] = {
    "skins": True,
    "lore": True,
    "faction": True,
    "price": True,
    "fullName": True,
    "title": True,
}


def exclude_fields(
    champions: dict[str, ChampionInformation],
) -> dict[str, dict[str, Any]]:
    cleaned: dict[str, dict[str, Any]] = {}

    for champ_name, champ_model in champions.items():
        data = champ_model.model_dump(exclude=EXCLUDE_MAP)

        stats = data.get("stats")
        if isinstance(stats, dict):
            data["stats"] = {
                stat_name: {
                    metric_name: metric_value
                    for metric_name, metric_value in stat_value.items()
                    if metric_name not in STAT_METRIC_EXCLUDE
                }
                for stat_name, stat_value in stats.items()
                if (
                    not stat_name.lower().startswith(STAT_PREFIXES_TO_EXCLUDE)
                    and isinstance(stat_value, dict)
                )
            }

        abilities = data.get("abilities")
        if isinstance(abilities, dict):
            for ability_entries in abilities.values():
                if not isinstance(ability_entries, list):
                    continue
                for entry in ability_entries:
                    if not isinstance(entry, dict):
                        continue
                    for field_name in ABILITY_FIELD_EXCLUDE:
                        entry.pop(field_name, None)

        cleaned[champ_name] = data

    return cleaned


def normalize_champions(
    champions: dict[str, ChampionInformation],
) -> dict[str, dict[str, Any]]:
    return exclude_fields(champions)
