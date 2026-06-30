from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter

from champions.models.champion_models import ChampionInformation

ChampionMap = dict[str, ChampionInformation]
payload_adapter = TypeAdapter(ChampionMap)


def validate_champions(data: Any) -> ChampionMap:
    return payload_adapter.validate_python(data)
