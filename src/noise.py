from __future__ import annotations

from typing import Any

from src.models.champion_models import Abilities, ChampionInformation, Stats

STAT_PREFIXES_TO_EXCLUDE = ("urf", "aram")
STAT_METRIC_EXCLUDE = {"percent", "percentPerLevel"}
ABILITY_FIELD_EXCLUDE = {"onHitEffects", "occurrence", "missileSpeed"}

EXCLUDE_MAP: dict[str, Any] = {
    "stats": {stat_name: STAT_METRIC_EXCLUDE for stat_name in Stats.model_fields},
    "abilities": {
        slot: {"__all__": ABILITY_FIELD_EXCLUDE} for slot in Abilities.model_fields
    },
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
                stat_name: stat_value
                for stat_name, stat_value in stats.items()
                if not stat_name.lower().startswith(STAT_PREFIXES_TO_EXCLUDE)
            }

        cleaned[champ_name] = data

    return cleaned
