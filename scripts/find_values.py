import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.load import fetch_champion_info_raw
from src.models.champion_models import ChampionInformation


def ability_values(payload: dict, values: defaultdict[set], keys: list[str]):
    abilities: dict[str, Any] = payload["abilities"]
    for _, ability_list in abilities.items():
        for ability in ability_list:
            for key in keys:
                values[key].add(
                    ability[key]
                    if not isinstance(ability[key], list)
                    else tuple(ability[key])
                )


def root_values(payload: dict, values: defaultdict[set], keys: list[str]):
    for k, v in payload.items():
        if k not in keys:
            continue

        if k in ["roles", "positions"]:
            for role in v:
                values[k].add(role)
        else:
            values[k].add(v if not isinstance(v, list) else tuple(v))


def effect_descriptions(payload: dict, values: defaultdict[set]) -> None:
    abilities: dict[str, Any] = payload["abilities"]

    for _, ability_list in abilities.items():
        for ability in ability_list:
            effects = ability.get("effects", [])
            for effect in effects:
                description = effect.get("description")
                if description:
                    values["descriptions"].add(description)


# def collect_modifier_units(
#     payload: dict[str, Any], values: defaultdict[str, set]
# ) -> None:
#     abilities = payload["abilities"]

#     for ability_list in abilities.values():
#         for ability in ability_list:
#             for key in ("cost", "cooldown"):
#                 container = ability.get(key)
#                 if container:
#                     values["modifer_length"].add(len(container["modifiers"]))

#                     if len(container["modifiers"]) == 6:
#                         print(payload["name"])

#                     for modifier in container["modifiers"]:
#                         units = modifier["units"]
#                         values["modifier_units"].add(units[0])

#             for effect in ability.get("effects", []):
#                 for lvl in effect.get("leveling", []):
#                     if len(lvl["modifiers"]) == 6:
#                         print(payload["name"])
#                     values["modifer_length"].add(len(lvl["modifiers"]))
#                     for modifier in lvl["modifiers"]:
#                         units = modifier["units"]
#                         values["modifier_units"].add(units[0])


def find_values(data: ChampionInformation, keys: dict[str, list]) -> dict[str, Any]:
    values: defaultdict[set] = defaultdict(set)
    for name, payload in data.items():
        print(f"Checking: {name}")
        if isinstance(payload, dict):
            ability_values(payload, values, keys["abilities"])
            root_values(payload, values, keys["root"])
            # effect_descriptions(payload, values)
            # collect_modifier_units(payload, values) # DONE
    return values


def save_values(data: dict[str, Any]) -> None:
    path: Path = Path(
        r"C:\Users\Jack\Documents\GitHub\Fifth-Time-Lucky\champion_parser\scripts\find_values.json"
    )

    serializable = {k: list(v) if isinstance(v, set) else v for k, v in data.items()}

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            serializable,
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )


def main():
    data: Any = fetch_champion_info_raw()
    values: dict[str, Any] = find_values(
        data,
        {
            "root": [
                "name",
                "resource",
                # "attackType", # DONE as LITERAL
                # "adaptiveType", # DONE as LITERAL
                # "roles", # DONE as LITERAL
                # "positions", # DONE as LITERAL
            ],
            "abilities": [
                "targeting",
                # "affects", # DONE
                "spellshieldable",
                # "resource",  # DONE as LITERAL
                # "damageType",  # DONE as LITERAL
                "spellEffects",
                # "projectile",  # DONE as LITERAL
                # "onHitEffects",  # DONE as ALWAYS NULL
                # "occurrence",  # DONE as ALWAYS NULL
                # "missileSpeed",  # DONE as ALWAYS NULL
                "rechargeRate",
                # "collisionRadius", # DONE
                "tetherRadius",
                "onTargetCdStatic",
                # "innerRadius", # DONE
                "speed",
                "width",
                # "angle", # DONE
                # "castTime", # DONE
                "effectRadius",
                "targetRange",
            ],
        },
    )
    save_values(values)


if __name__ == "__main__":
    main()
