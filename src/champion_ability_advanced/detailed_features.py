from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from champion_ability_advanced.paths import (
    ABILITY_ADVANCED_FILE_PATH,
    CHAMPION_ABILITY_DETAILED_FEATURES_FILE_PATH,
)
from champion_ability_attributes.paths import ABILITY_ATTRIBUTE_FEATURES_FILE_PATH
from champions.communitydragon import ABILITY_ORDER
from shared import load_jsonl, write_jsonl

ATTRIBUTE_IDENTITY_FIELDS = frozenset(
    ("_key", "championName", "championId", "abilityKey", "stageCount")
)
SCALAR_FIELDS = (
    "castTime",
    "collisionRadius",
    "innerRadius",
    "onTargetCdStatic",
    "rechargeRate",
    "speed",
    "targetRange",
    "tetherRadius",
    "width",
    "angle",
)
ARRAY_FIELDS = ("cooldown", "cost", "range")
ARRAY_METRICS = ("rank1", "rankmax", "min", "max", "mean", "delta", "has_values")
CATEGORICAL_FIELDS = (
    "damageType",
    "targetingType",
    "targetting",
    "spellEffects",
    "spellshieldable",
    "projectile",
    "resource",
)
ATTRIBUTE_FEATURE_RENAMES = {
    "aoe": "area_of_effect",
    "cc": "crowd_control",
    "proj": "projectile_trait",
}
CATEGORY_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9%]+")


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _number_or_zero(value: Any) -> float:
    if not _is_number(value):
        return 0.0
    return float(value)


def _numeric_values(value: Any) -> list[float]:
    if _is_number(value):
        return [float(value)]
    if isinstance(value, list):
        return [
            numeric_value
            for item in value
            for numeric_value in _numeric_values(item)
        ]
    if isinstance(value, dict):
        return [
            numeric_value
            for item in value.values()
            for numeric_value in _numeric_values(item)
        ]
    return []


def _array_numbers(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    return [float(item) for item in value if _is_number(item)]


def _array_summary(value: Any) -> dict[str, float | int]:
    values = _array_numbers(value)
    if not values:
        return {
            "rank1": 0.0,
            "rankmax": 0.0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "delta": 0.0,
            "has_values": 0,
        }

    return {
        "rank1": values[0],
        "rankmax": values[-1],
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "delta": values[-1] - values[0],
        "has_values": 1,
    }


def _category_token(value: Any) -> str | None:
    if isinstance(value, bool):
        return str(value).lower()
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower()

    token = CATEGORY_TOKEN_PATTERN.sub("_", value).strip("_")
    return token or None


def _category_sets(ability_rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        field_name: sorted(
            {
                token
                for row in ability_rows
                if (token := _category_token(row.get(field_name))) is not None
            }
        )
        for field_name in CATEGORICAL_FIELDS
    }


def _data_values_summary(value: Any) -> dict[str, float | int]:
    if not isinstance(value, dict):
        values: list[float] = []
        return {
            "dataValues_count": 0,
            "dataValues_ranked_count": 0,
            "dataValues_scalar_count": 0,
            "dataValues_min": 0.0,
            "dataValues_max": 0.0,
            "dataValues_abs_max": 0.0,
            "dataValues_has_negative": 0,
        }

    values = _numeric_values(value)
    ranked_count = sum(1 for item in value.values() if isinstance(item, list))
    scalar_count = sum(1 for item in value.values() if _is_number(item))
    return {
        "dataValues_count": len(value),
        "dataValues_ranked_count": ranked_count,
        "dataValues_scalar_count": scalar_count,
        "dataValues_min": min(values) if values else 0.0,
        "dataValues_max": max(values) if values else 0.0,
        "dataValues_abs_max": max((abs(item) for item in values), default=0.0),
        "dataValues_has_negative": int(any(item < 0 for item in values)),
    }


def _list_count(value: Any) -> int:
    if not isinstance(value, list):
        return 0
    return len(value)


def _raw_missile_summary(value: Any) -> dict[str, float | int | str]:
    raw = value if isinstance(value, dict) else {}
    missile_spec = raw.get("mMissileSpec")
    missile = missile_spec if isinstance(missile_spec, dict) else {}
    movement = missile.get("movementComponent")
    movement_component = movement if isinstance(movement, dict) else {}
    targeting = raw.get("mTargetingTypeData")
    targeting_type = ""
    if isinstance(targeting, dict) and isinstance(targeting.get("__type"), str):
        targeting_type = targeting["__type"]

    missile_width = _number_or_zero(missile.get("mMissileWidth"))
    if not missile_width:
        missile_width = _number_or_zero(missile.get("scanWidthOverride"))
    if not missile_width:
        missile_width = _number_or_zero(raw.get("mLineWidth"))

    missile_speed = _number_or_zero(movement_component.get("mSpeed"))
    if not missile_speed:
        missile_speed = _number_or_zero(movement_component.get("mInitialSpeed"))
    if not missile_speed:
        missile_speed = _number_or_zero(movement_component.get("mMaxSpeed"))
    if not missile_speed:
        missile_speed = _number_or_zero(raw.get("missileSpeed"))

    behaviors = missile.get("behaviors")
    return {
        "raw_has_missile_spec": int(bool(missile)),
        "raw_missile_width": missile_width,
        "raw_missile_speed": missile_speed,
        "raw_missile_tracks_target": int(
            movement_component.get("mTracksTarget") is True
        ),
        "raw_missile_project_to_cast_range": int(
            movement_component.get("mProjectTargetToCastRange") is True
        ),
        "raw_missile_behavior_count": _list_count(behaviors),
        "raw_targeting_type": targeting_type,
    }


def _attribute_feature_pairs(
    attribute_rows: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    feature_names = sorted(
        {
            key
            for row in attribute_rows
            for key, value in row.items()
            if key not in ATTRIBUTE_IDENTITY_FIELDS and value in {0, 1}
        }
    )
    pairs = [
        (feature_name, ATTRIBUTE_FEATURE_RENAMES.get(feature_name, feature_name))
        for feature_name in feature_names
    ]
    output_names = [output_name for _feature_name, output_name in pairs]
    if len(output_names) != len(set(output_names)):
        raise ValueError("Attribute feature names are not unique after renaming.")
    return sorted(pairs, key=lambda pair: pair[1])


def _attribute_row_key(row: dict[str, Any]) -> tuple[int, str]:
    champion_id = row.get("championId")
    ability_key = row.get("abilityKey")
    if not isinstance(champion_id, int) or not isinstance(ability_key, str):
        raise ValueError("Attribute rows must include integer championId and abilityKey.")
    return champion_id, ability_key


def _attribute_rows_by_ability(
    attribute_rows: list[dict[str, Any]],
) -> dict[tuple[int, str], dict[str, Any]]:
    rows_by_ability: dict[tuple[int, str], dict[str, Any]] = {}
    for attribute_row in attribute_rows:
        row_key = _attribute_row_key(attribute_row)
        if row_key in rows_by_ability:
            raise ValueError(
                "Duplicate attribute feature row for "
                f"championId={row_key[0]}, abilityKey={row_key[1]}."
            )
        rows_by_ability[row_key] = attribute_row
    return rows_by_ability


def _ability_groups(
    ability_rows: list[dict[str, Any]],
) -> dict[tuple[str, int], dict[str, dict[str, Any]]]:
    champions: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    seen_abilities: set[tuple[int, str]] = set()

    for ability_row in ability_rows:
        champion_id = ability_row.get("championId")
        champion_name = ability_row.get("championName")
        ability_key = ability_row.get("abilityKey")
        if (
            not isinstance(champion_id, int)
            or not isinstance(champion_name, str)
            or ability_key not in ABILITY_ORDER
        ):
            raise ValueError(
                "Ability rows must include championId, championName, and a P/Q/W/E/R "
                "abilityKey."
            )

        seen_key = (champion_id, ability_key)
        if seen_key in seen_abilities:
            raise ValueError(
                f"Duplicate ability row for championId={champion_id}, "
                f"abilityKey={ability_key}."
            )
        seen_abilities.add(seen_key)

        champion_key = (champion_name, champion_id)
        champions.setdefault(champion_key, {})[ability_key] = ability_row

    missing_slots = [
        f"{champion_name}:{champion_id}:{ability_key}"
        for (champion_name, champion_id), abilities in champions.items()
        for ability_key in ABILITY_ORDER
        if ability_key not in abilities
    ]
    if missing_slots:
        raise ValueError(
            "Every champion must include P/Q/W/E/R rows; missing "
            + ", ".join(sorted(missing_slots)[:10])
        )

    return champions


def _add_slot_fields(
    output_row: dict[str, Any],
    slot: str,
    ability_row: dict[str, Any],
    attribute_row: dict[str, Any],
    category_sets: dict[str, list[str]],
    attribute_feature_pairs: Iterable[tuple[str, str]],
) -> None:
    for field_name in SCALAR_FIELDS:
        output_row[f"{slot}_{field_name}"] = _number_or_zero(ability_row.get(field_name))

    for field_name in ARRAY_FIELDS:
        summary = _array_summary(ability_row.get(field_name))
        for metric in ARRAY_METRICS:
            output_row[f"{slot}_{field_name}_{metric}"] = summary[metric]

    for field_name in CATEGORICAL_FIELDS:
        row_token = _category_token(ability_row.get(field_name))
        for category in category_sets[field_name]:
            output_row[f"{slot}_{field_name}_{category}"] = int(row_token == category)

    output_row.update(
        {
            f"{slot}_{field_name}": value
            for field_name, value in _data_values_summary(
                ability_row.get("dataValues")
            ).items()
        }
    )
    output_row[f"{slot}_scalingPart_count"] = _list_count(
        ability_row.get("scalingParts")
    )
    output_row[f"{slot}_damagePart_count"] = _list_count(ability_row.get("damageParts"))
    output_row[f"{slot}_ratioColumn_count"] = _list_count(
        ability_row.get("ratioColumns")
    )
    output_row[f"{slot}_unit_count"] = _list_count(ability_row.get("units"))
    output_row.update(
        {
            f"{slot}_{field_name}": value
            for field_name, value in _raw_missile_summary(
                ability_row.get("raw")
            ).items()
        }
    )

    for feature_name, output_name in attribute_feature_pairs:
        output_row[f"{slot}_{output_name}"] = int(attribute_row.get(feature_name) == 1)


def build_champion_ability_detailed_features(
    ability_rows: list[dict[str, Any]],
    attribute_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    category_sets = _category_sets(ability_rows)
    attribute_feature_pairs = _attribute_feature_pairs(attribute_rows)
    attribute_by_ability = _attribute_rows_by_ability(attribute_rows)
    champions = _ability_groups(ability_rows)
    detailed_rows: list[dict[str, Any]] = []

    for champion_name, champion_id in sorted(champions):
        abilities = champions[(champion_name, champion_id)]
        output_row: dict[str, Any] = {
            "_key": str(champion_id),
            "championId": champion_id,
            "championName": champion_name,
        }
        for slot in ABILITY_ORDER:
            attribute_key = (champion_id, slot)
            attribute_row = attribute_by_ability.get(attribute_key)
            if attribute_row is None:
                raise ValueError(
                    "Missing attribute feature row for "
                    f"championId={champion_id}, abilityKey={slot}."
                )
            _add_slot_fields(
                output_row,
                slot,
                abilities[slot],
                attribute_row,
                category_sets,
                attribute_feature_pairs,
            )
        detailed_rows.append(output_row)

    return detailed_rows


def save_champion_ability_detailed_features(
    rows: list[dict[str, Any]],
    path: Path = CHAMPION_ABILITY_DETAILED_FEATURES_FILE_PATH,
) -> None:
    write_jsonl(rows, path)


def generate_champion_ability_detailed_features(
    ability_path: Path = ABILITY_ADVANCED_FILE_PATH,
    attribute_path: Path = ABILITY_ATTRIBUTE_FEATURES_FILE_PATH,
    output_path: Path = CHAMPION_ABILITY_DETAILED_FEATURES_FILE_PATH,
) -> list[dict[str, Any]]:
    ability_rows = load_jsonl(ability_path)
    attribute_rows = load_jsonl(attribute_path)
    detailed_rows = build_champion_ability_detailed_features(
        ability_rows,
        attribute_rows,
    )
    save_champion_ability_detailed_features(detailed_rows, output_path)
    return detailed_rows
