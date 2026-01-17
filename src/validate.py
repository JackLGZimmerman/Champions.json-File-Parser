from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter, ValidationError

from .error import Error, ValidationIssue
from .models.champion_models import ChampionInformation

ChampionPayloadMap = dict[str, dict[str, Any]]
payload_adapter = TypeAdapter(ChampionPayloadMap)


def validate_champions(
    data: Any,
    *,
    error: Error,
) -> dict[str, ChampionInformation]:
    champion_payloads = payload_adapter.validate_python(data)

    validated: dict[str, ChampionInformation] = {}

    _debug: bool = True
    for champ_name, payload in champion_payloads.items():
        try:
            validated[champ_name] = ChampionInformation.model_validate(payload)

            if _debug:
                champ = validated[champ_name]
                abilities = champ.abilities

                for slot in abilities.model_fields:
                    ability_list = getattr(abilities, slot)
                    if not ability_list:
                        continue

                    for i, ability in enumerate(ability_list):
                        affects = getattr(ability, "affects", None)
                        if affects is None:
                            continue

        except ValidationError as e:
            for err in e.errors():
                error.add(
                    ValidationIssue(
                        champion=champ_name,
                        path=".".join(str(x) for x in err.get("loc", [])),
                        message=err.get("msg", ""),
                        type=err.get("type", ""),
                        context=err.get("ctx"),
                    )
                )

    return validated
