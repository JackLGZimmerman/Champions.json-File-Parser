from __future__ import annotations

from typing import Any

from champions.models.champion_models import ChampionInformation


def normalize_champions(
    champions: dict[str, ChampionInformation],
) -> dict[str, dict[str, Any]]:
    """Dump validated champion models without trimming simulator source detail."""
    return {
        champion_name: champion.model_dump()
        for champion_name, champion in champions.items()
    }
