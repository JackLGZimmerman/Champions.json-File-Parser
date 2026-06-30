from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

from champions.communitydragon import ABILITY_ORDER, build_ability_row_base

IDENTITY_FIELD_NAMES = (
    "_key",
    "championName",
    "championId",
    "abilityKey",
)
ABILITY_FIELD_NAMES = (
    "affect",
    "angle",
    "castTime",
    "collisionRadius",
    "cooldown",
    "cost",
    "damageParts",
    "damageType",
    "dataValues",
    "description",
    "dynamicDescription",
    "name",
    "projectile",
    "range",
    "ratioColumns",
    "raw",
    "rechargeRate",
    "recordPath",
    "resource",
    "scalingParts",
    "speed",
    "spellEffects",
    "spellshieldable",
    "targetRange",
    "targetingType",
    "targetting",
    "units",
    "width",
)
SOURCE_ABILITY_FIELD_NAMES = (
    *ABILITY_FIELD_NAMES,
    "innerRadius",
    "onTargetCdStatic",
    "tetherRadius",
)
ROW_FIELD_NAMES = IDENTITY_FIELD_NAMES + ABILITY_FIELD_NAMES
RAW_NESTED_INVENTORY_FIELDS = ("mMissileSpec", "mTargetingTypeData")
RAW_FIELD_COVERAGE_NOTE = (
    "raw is the selected raw spell subset produced by "
    "champions.communitydragon.selected_raw_spell_fields."
)

AbilityContext = tuple[str, dict[str, Any], str, int, dict[str, Any]]


def _format_keys(keys: Iterable[str]) -> str:
    return ", ".join(sorted(keys)) or "<none>"


def _type_name(value: Any) -> str:
    return type(value).__name__


def _has_example_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _champion_sort_key(context: AbilityContext) -> tuple[str, int, int, int]:
    champion_name, champion_info, ability_key, ability_index, _ability = context
    champion_id = champion_info.get("id")
    if not isinstance(champion_id, int):
        champion_id = 0
    return (
        champion_name,
        champion_id,
        ABILITY_ORDER.index(ability_key),
        ability_index,
    )


def collect_ability_contexts(
    formatted_payload: dict[str, Any],
) -> list[AbilityContext]:
    contexts: list[AbilityContext] = []

    for champion_name, champion_info in formatted_payload.items():
        if not isinstance(champion_name, str):
            raise ValueError("Formatted champion keys must be strings.")
        if not isinstance(champion_info, dict):
            raise ValueError(f"{champion_name}: champion payload must be an object.")

        abilities = champion_info.get("abilities")
        if not isinstance(abilities, dict):
            raise ValueError(f"{champion_name}: abilities must be an object.")

        ability_keys = set(abilities)
        expected_keys = set(ABILITY_ORDER)
        if ability_keys != expected_keys:
            missing = expected_keys - ability_keys
            extra = ability_keys - expected_keys
            raise ValueError(
                f"{champion_name}: expected ability slots {_format_keys(ABILITY_ORDER)}; "
                f"missing {_format_keys(missing)}; extra {_format_keys(extra)}."
            )

        for ability_key in ABILITY_ORDER:
            ability_entries = abilities[ability_key]
            if not isinstance(ability_entries, list):
                raise ValueError(f"{champion_name}:{ability_key}: entries must be a list.")
            if len(ability_entries) != 1:
                raise ValueError(
                    f"{champion_name}:{ability_key}: expected exactly one ability "
                    f"entry, found {len(ability_entries)}."
                )
            ability = ability_entries[0]
            if not isinstance(ability, dict):
                raise ValueError(
                    f"{champion_name}:{ability_key}: ability entry must be an object."
                )
            contexts.append((champion_name, champion_info, ability_key, 0, ability))

    return sorted(contexts, key=_champion_sort_key)


def discover_ability_fields(contexts: list[AbilityContext]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field_name
                for _champion_name, _champion_info, _ability_key, _index, ability
                in contexts
                for field_name in ability
            }
        )
    )


def validate_ability_fields(
    contexts: list[AbilityContext],
    expected_fields: tuple[str, ...] = SOURCE_ABILITY_FIELD_NAMES,
) -> None:
    expected_field_set = set(expected_fields)
    for champion_name, _champion_info, ability_key, _index, ability in contexts:
        ability_field_set = set(ability)
        if ability_field_set != expected_field_set:
            missing = expected_field_set - ability_field_set
            extra = ability_field_set - expected_field_set
            raise ValueError(
                f"{champion_name}:{ability_key}: ability fields do not match the "
                f"expected schema; missing {_format_keys(missing)}; "
                f"extra {_format_keys(extra)}."
            )

    discovered_fields = set(discover_ability_fields(contexts))
    if discovered_fields != expected_field_set:
        missing = expected_field_set - discovered_fields
        extra = discovered_fields - expected_field_set
        raise ValueError(
            "Formatted ability fields do not match the expected schema; "
            f"missing {_format_keys(missing)}; extra {_format_keys(extra)}."
        )


def validate_unique_rows(rows: list[dict[str, Any]]) -> None:
    seen_keys: set[str] = set()
    seen_champion_abilities: set[tuple[int, str]] = set()

    for row in rows:
        row_key = row.get("_key")
        if not isinstance(row_key, str):
            raise ValueError("Ability row _key must be a string.")
        if row_key in seen_keys:
            raise ValueError(f"Duplicate ability row _key: {row_key}")
        seen_keys.add(row_key)

        champion_id = row.get("championId")
        ability_key = row.get("abilityKey")
        if not isinstance(champion_id, int) or not isinstance(ability_key, str):
            raise ValueError(
                f"{row_key}: championId must be an integer and abilityKey must be a string."
            )
        champion_ability = (champion_id, ability_key)
        if champion_ability in seen_champion_abilities:
            raise ValueError(
                f"Duplicate champion ability row for championId={champion_id}, "
                f"abilityKey={ability_key}."
            )
        seen_champion_abilities.add(champion_ability)


def build_ability_row(context: AbilityContext) -> dict[str, Any]:
    champion_name, champion_info, ability_key, _ability_index, ability = context
    row = build_ability_row_base(champion_name, champion_info, ability_key)
    for field_name in ABILITY_FIELD_NAMES:
        row[field_name] = ability[field_name]
    return row


def extract_ability_advanced(formatted_payload: dict[str, Any]) -> list[dict[str, Any]]:
    contexts = collect_ability_contexts(formatted_payload)
    validate_ability_fields(contexts)
    rows = [build_ability_row(context) for context in contexts]
    validate_unique_rows(rows)
    return rows


def build_raw_field_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw_field_names = sorted(
        {
            field_name
            for row in rows
            if isinstance(row.get("raw"), dict)
            for field_name in row["raw"]
        }
    )
    coverage: dict[str, Any] = {}

    for field_name in raw_field_names:
        present_count = 0
        non_null_count = 0
        type_counts: Counter[str] = Counter()
        example: Any = None

        for row in rows:
            raw = row.get("raw")
            if not isinstance(raw, dict) or field_name not in raw:
                continue
            present_count += 1
            value = raw[field_name]
            type_counts[_type_name(value)] += 1
            if value is not None:
                non_null_count += 1
            if example is None and _has_example_value(value):
                example = value

        coverage[field_name] = {
            "presentCount": present_count,
            "nonNullCount": non_null_count,
            "types": dict(sorted(type_counts.items())),
            "example": example,
        }

    return {
        "note": RAW_FIELD_COVERAGE_NOTE,
        "rowCount": len(rows),
        "rawFieldCount": len(raw_field_names),
        "fields": coverage,
    }


def _walk_json_paths(
    value: Any,
    path: str,
) -> Iterable[tuple[str, str, Any]]:
    yield path, _type_name(value), value

    if isinstance(value, dict):
        for key, child_value in value.items():
            yield from _walk_json_paths(child_value, f"{path}.{key}")
    elif isinstance(value, list):
        for child_value in value:
            yield from _walk_json_paths(child_value, f"{path}[]")


def build_raw_nested_path_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path_row_counts: Counter[str] = Counter()
    path_value_counts: Counter[str] = Counter()
    type_counts_by_path: defaultdict[str, Counter[str]] = defaultdict(Counter)
    examples_by_path: dict[str, Any] = {}

    for row in rows:
        raw = row.get("raw")
        if not isinstance(raw, dict):
            continue

        paths_seen_in_row: set[str] = set()
        for raw_field_name in RAW_NESTED_INVENTORY_FIELDS:
            value = raw.get(raw_field_name)
            if value is None:
                continue
            for path, type_name, path_value in _walk_json_paths(
                value,
                f"raw.{raw_field_name}",
            ):
                paths_seen_in_row.add(path)
                path_value_counts[path] += 1
                type_counts_by_path[path][type_name] += 1
                if path not in examples_by_path and _has_example_value(path_value):
                    examples_by_path[path] = path_value

        path_row_counts.update(paths_seen_in_row)

    return [
        {
            "path": path,
            "rowCount": path_row_counts[path],
            "valueCount": path_value_counts[path],
            "types": dict(sorted(type_counts_by_path[path].items())),
            "example": examples_by_path.get(path),
        }
        for path in sorted(path_row_counts)
    ]
