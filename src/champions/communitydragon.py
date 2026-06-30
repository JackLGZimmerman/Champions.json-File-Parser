from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import requests

from shared import data_segment_dir, load_json, write_json, write_jsonl

CHAMPION_DATA_DIR = data_segment_dir("champions")
CHAMP_ID_NAME_MAP_PATH = CHAMPION_DATA_DIR / "champ_id_name_map.jsonl"
COMMUNITYDRAGON_FORMATTED_PATH = (
    CHAMPION_DATA_DIR / "communitydragon_abilities_formatted.json"
)
COMMUNITYDRAGON_INDEX_URL = (
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
    "global/default/v1/champions/"
)
COMMUNITYDRAGON_BIN_URL_TEMPLATE = (
    "https://raw.communitydragon.org/latest/game/data/characters/"
    "{alias_lower}/{alias_lower}.bin.json"
)
ABILITY_ORDER = ("P", "Q", "W", "E", "R")
INDEX_FILE_PATTERN = re.compile(r'href="([^"]+\.json)"')
PLACEHOLDER_PATTERN = re.compile(r"@([A-Za-z0-9_]+)(?:\*[^@]+)?@")
CAMEL_CASE_BOUNDARY_PATTERN = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9%]+")
RESOURCE_TYPE_MAP = {
    0: "MANA",
    1: "ENERGY",
    7: "HEAT",
}
TARGETING_TYPE_MAP = {
    "Arc": "Direction",
    "Area": "Location",
    "AreaClamped": "Location",
    "Cone": "Direction",
    "Direction": "Direction",
    "Location": "Location",
    "LocationClamped": "Location",
    "Self": "Auto",
    "SelfAoe": "Auto",
    "Target": "Unit",
    "TargetOrDirection": "Unit / Direction",
    "TargetOrLocation": "Unit / Location",
}
DAMAGE_TYPE_MAP = {
    "magic": "MAGIC_DAMAGE",
    "physical": "PHYSICAL_DAMAGE",
    "true": "TRUE_DAMAGE",
}
FIELD_KEY_PATTERNS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "angle": (("angle",), ()),
    "castTime": (("casttime", "castdelay", "windup"), ()),
    "collisionRadius": (("collisionradius", "impactradius"), ()),
    "innerRadius": (("innerradius",), ()),
    "onTargetCdStatic": (("ontargetcd", "ontargetcooldown", "targetcooldown"), ()),
    "speed": (
        ("dashespeed", "missilespeed", "projectilespeed", "travelspeed", "pullspeed"),
        ("movementspeedduration",),
    ),
    "targetRange": (
        (
            "targetrange",
            "castrange",
            "maxrange",
            "minrange",
            "spellrange",
            "dashdistance",
            "distance",
        ),
        ("radius", "width", "duration", "cooldown"),
    ),
    "tetherRadius": (("tetherradius", "tetherrange", "pullradius"), ()),
    "width": (("width", "linewidth", "missilewidth"), ()),
}
DAMAGE_CALC_NAME_MARKERS = (
    "damage",
    "hit",
    "detonation",
    "impact",
    "strike",
    "slash",
    "burn",
    "blast",
    "shot",
    "projectile",
)
PART_TYPE_STAT_DEFAULTS = {
    "StatByCoefficientCalculationPart": "percent_ap",
}
STAT_CODE_MAP = {
    1: "percent_armour",
    2: "percent_ad",
    4: "percent_attack_speed",
    6: "percent_magic_resistance",
    8: "flat_crit_chance",
    12: "percent_hp",
}


def _session_get_json(session: requests.Session, url: str, timeout: int = 20) -> Any:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _session_get_text(session: requests.Session, url: str, timeout: int = 20) -> str:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def relevant_champion_index_filenames(index_html: str) -> list[str]:
    filenames = sorted(set(INDEX_FILE_PATTERN.findall(index_html)))
    relevant_filenames: list[str] = []

    for filename in filenames:
        stem = filename.removesuffix(".json")
        try:
            file_id = int(stem)
        except ValueError:
            continue
        if file_id < 0 or len(stem) > 4:
            continue
        relevant_filenames.append(filename)

    return relevant_filenames


def fetch_communitydragon_index_entries() -> list[dict[str, Any]]:
    with requests.Session() as session:
        index_html = _session_get_text(session, COMMUNITYDRAGON_INDEX_URL)
        filenames = relevant_champion_index_filenames(index_html)
        entries: list[dict[str, Any]] = []

        for filename in filenames:
            entry = _session_get_json(session, COMMUNITYDRAGON_INDEX_URL + filename)
            if not isinstance(entry, dict):
                continue
            champion_id = entry.get("id")
            alias = entry.get("alias")
            name = entry.get("name")
            if not isinstance(champion_id, int):
                continue
            if not isinstance(alias, str) or not alias:
                continue
            if not isinstance(name, str) or not name:
                continue
            entries.append(entry)

    entries.sort(key=lambda entry: int(entry["id"]))
    return entries


def extract_champ_id_name_rows(
    index_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in index_entries:
        champion_id = entry.get("id")
        alias = entry.get("alias")
        name = entry.get("name")
        if not isinstance(champion_id, int):
            continue
        if not isinstance(alias, str) or not alias:
            continue
        if not isinstance(name, str) or not name:
            continue
        rows.append(
            {
                "_key": str(champion_id),
                "name": name,
                "alias": alias,
            }
        )
    return rows


def save_champ_id_name_rows(
    rows: list[dict[str, Any]],
    path: Path = CHAMP_ID_NAME_MAP_PATH,
) -> None:
    write_jsonl(rows, path)


def clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def clean_text_lower(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return NON_ALNUM_PATTERN.sub(
        " ",
        CAMEL_CASE_BOUNDARY_PATTERN.sub(" ", value).lower(),
    ).strip()


def extract_numeric_values(value: Any) -> list[float]:
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, int | float):
        return [float(value)]
    if isinstance(value, list):
        return [
            numeric_value
            for item in value
            for numeric_value in extract_numeric_values(item)
        ]
    if isinstance(value, dict):
        return [
            numeric_value
            for item in value.values()
            for numeric_value in extract_numeric_values(item)
        ]
    return []


def average_numbers(
    values: list[float],
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    ignore_values: set[float] | None = None,
) -> float:
    filtered_values: list[float] = []
    for value in values:
        if ignore_values and value in ignore_values:
            continue
        if min_value is not None and value < min_value:
            continue
        if max_value is not None and value > max_value:
            continue
        filtered_values.append(value)
    if not filtered_values:
        return 0.0
    return sum(filtered_values) / len(filtered_values)


def spell_data_value_map(spell: dict[str, Any]) -> dict[str, list[float]]:
    data_values = spell.get("DataValues")
    if not isinstance(data_values, list):
        return {}

    value_map: dict[str, list[float]] = {}
    for data_value in data_values:
        if not isinstance(data_value, dict):
            continue
        name = data_value.get("name")
        values = data_value.get("values")
        if not isinstance(name, str):
            continue
        numeric_values = extract_numeric_values(values)
        if not numeric_values:
            continue
        value_map[name] = numeric_values
    return value_map


def collect_matching_named_values(
    data_value_map: dict[str, list[float]],
    include_markers: tuple[str, ...],
    exclude_markers: tuple[str, ...] = (),
) -> list[float]:
    values: list[float] = []
    for name, numeric_values in data_value_map.items():
        normalized_name = clean_text_lower(name)
        if not normalized_name:
            continue
        if include_markers and not any(
            marker.lower() in normalized_name
            for marker in include_markers
        ):
            continue
        if any(marker.lower() in normalized_name for marker in exclude_markers):
            continue
        values.extend(numeric_values)
    return values


def collect_matching_nested_values(
    payload: Any,
    include_markers: tuple[str, ...],
    exclude_markers: tuple[str, ...] = (),
) -> list[float]:
    values: list[float] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                normalized_key = clean_text_lower(key)
                if normalized_key and any(
                    marker.lower() in normalized_key
                    for marker in include_markers
                ) and not any(
                    marker.lower() in normalized_key
                    for marker in exclude_markers
                ):
                    values.extend(extract_numeric_values(value))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return values


def resolve_spell_field(
    spell: dict[str, Any],
    v1_spell_info: dict[str, Any] | None,
    data_value_map: dict[str, list[float]],
    field_name: str,
) -> float:
    if field_name == "angle":
        direct_values = extract_numeric_values(spell.get("castConeAngle"))
        nested_values = collect_matching_nested_values(
            spell.get("mTargetingTypeData"),
            ("angle",),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(direct_values + nested_values + named_values)

    if field_name == "castTime":
        direct_values = extract_numeric_values(spell.get("mCastTime"))
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(direct_values + named_values)

    if field_name == "collisionRadius":
        direct_values = extract_numeric_values(spell.get("castRadius"))
        missile_values = collect_matching_nested_values(
            spell.get("mMissileSpec"),
            ("collision", "radius"),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(direct_values + missile_values + named_values)

    if field_name == "innerRadius":
        nested_values = collect_matching_nested_values(
            spell.get("mTargetingTypeData"),
            ("innerradius",),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(nested_values + named_values)

    if field_name == "onTargetCdStatic":
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(named_values)

    if field_name == "rechargeRate":
        direct_values = extract_numeric_values(spell.get("mAmmoRechargeTime"))
        ammo_values = extract_numeric_values((v1_spell_info or {}).get("ammo", {}).get("ammoRechargeTime"))
        return average_numbers(direct_values + ammo_values, min_value=0.0)

    if field_name == "speed":
        direct_values = extract_numeric_values(spell.get("missileSpeed"))
        missile_values = collect_matching_nested_values(
            spell.get("mMissileSpec"),
            ("speed",),
            ("movementspeedduration",),
        )
        targeting_values = collect_matching_nested_values(
            spell.get("mTargetingTypeData"),
            ("speed",),
            ("movementspeedduration",),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(
            direct_values + missile_values + targeting_values + named_values,
            min_value=0.0,
            max_value=10000.0,
        )

    if field_name == "targetRange":
        v1_range_values = extract_numeric_values((v1_spell_info or {}).get("range"))
        direct_values = extract_numeric_values(spell.get("castRange"))
        targeting_values = collect_matching_nested_values(
            spell.get("mTargetingTypeData"),
            ("range", "distance"),
            ("radius", "width", "duration", "cooldown"),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(
            v1_range_values + direct_values + targeting_values + named_values,
            min_value=0.0,
            max_value=10000.0,
            ignore_values={25000.0},
        )

    if field_name == "tetherRadius":
        targeting_values = collect_matching_nested_values(
            spell.get("mTargetingTypeData"),
            ("tether", "pull"),
            ("speed",),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(targeting_values + named_values, min_value=0.0)

    if field_name == "width":
        direct_values = extract_numeric_values(spell.get("mLineWidth"))
        missile_values = collect_matching_nested_values(
            spell.get("mMissileSpec"),
            ("width",),
        )
        named_values = collect_matching_named_values(
            data_value_map,
            *FIELD_KEY_PATTERNS[field_name],
        )
        return average_numbers(
            direct_values + missile_values + named_values,
            min_value=0.0,
        )

    raise ValueError(f"Unsupported spell field: {field_name}")


def ability_target_range(
    spell: dict[str, Any],
    v1_spell_info: dict[str, Any] | None,
    data_value_map: dict[str, list[float]],
    root: dict[str, Any],
) -> float:
    direct_range = resolve_spell_field(
        spell,
        v1_spell_info,
        data_value_map,
        "targetRange",
    )
    if direct_range > 0.0:
        return direct_range

    bonus_range_values = collect_matching_named_values(
        data_value_map,
        ("bonusrange",),
    )
    attack_range = root_stat_value(root, "attackRangeModifiable")
    if bonus_range_values and attack_range > 0.0:
        return attack_range + average_numbers(
            bonus_range_values,
            min_value=0.0,
            max_value=10000.0,
        )
    return 0.0


def champion_resource_type(root_record: dict[str, Any]) -> str | None:
    primary_resource = root_record.get("primaryAbilityResource")
    if not isinstance(primary_resource, dict):
        return None
    resource_type = primary_resource.get("arType")
    if not isinstance(resource_type, int):
        return None
    return RESOURCE_TYPE_MAP.get(resource_type)


def ability_resource_type(
    spell: dict[str, Any],
    root_record: dict[str, Any],
) -> str | None:
    cost_values = extract_numeric_values(spell.get("mana"))
    if cost_values and any(value > 0 for value in cost_values):
        return champion_resource_type(root_record) or "OTHER"
    return None


def damage_type_from_text(*values: Any) -> str | None:
    text = " ".join(clean_text(value) or "" for value in values).lower()
    present_damage_types = [
        damage_type
        for token, damage_type in DAMAGE_TYPE_MAP.items()
        if f"{token} damage" in text
    ]
    present_damage_types = sorted(set(present_damage_types))
    if not present_damage_types:
        return None
    if len(present_damage_types) == 1:
        return present_damage_types[0]
    return "OTHER_DAMAGE"


def raw_targeting_type(spell: dict[str, Any]) -> str | None:
    target_data = spell.get("mTargetingTypeData")
    if not isinstance(target_data, dict):
        return None
    target_type = target_data.get("__type")
    if not isinstance(target_type, str):
        return None
    return target_type


def targetting_from_spell(
    ability_key: str,
    spell: dict[str, Any],
    target_range: float,
) -> str:
    if ability_key == "P":
        return "Passive"

    raw_type = raw_targeting_type(spell)
    if isinstance(raw_type, str) and raw_type in TARGETING_TYPE_MAP:
        return TARGETING_TYPE_MAP[raw_type]
    if target_range == 0.0:
        return "Auto"
    if isinstance(raw_type, str):
        return CAMEL_CASE_BOUNDARY_PATTERN.sub(" ", raw_type).replace("  ", " ").strip()
    return "Auto"


def projectile_from_spell(spell: dict[str, Any]) -> str | None:
    missile_spec = spell.get("mMissileSpec")
    missile_speed = average_numbers(
        extract_numeric_values(spell.get("missileSpeed")),
        min_value=0.0,
    )
    if isinstance(missile_spec, dict) and missile_spec:
        return "TRUE"
    if missile_speed > 0.0:
        return "TRUE"
    return None


def affect_from_spell(
    ability_key: str,
    targetting: str,
    description: str | None,
    dynamic_description: str | None,
    damage_type: str | None,
) -> str | None:
    text = " ".join(filter(None, (description, dynamic_description))).lower()
    affects: list[str] = []

    if ability_key == "P":
        if "ally" in text or "allies" in text:
            affects.append("Allies")
        if "enemy" in text or "enemies" in text or damage_type is not None:
            affects.append("Enemies")
        if any(word in text for word in ("gain", "gains", "heals", "revive", "revives")):
            affects.append("Self")
    else:
        if "ally" in text or "allies" in text or targetting.startswith("Unit"):
            if "ally" in text or "allies" in text:
                affects.append("Allies")
        if (
            "enemy" in text
            or "enemies" in text
            or "target" in text
            or damage_type is not None
            or targetting in {"Direction", "Location"}
        ):
            affects.append("Enemies")
        if any(
            word in text
            for word in (
                "gain",
                "gains",
                "dash",
                "dashes",
                "heal",
                "heals",
                "shield",
                "revive",
                "recast",
            )
        ) or targetting == "Auto":
            affects.append("Self")

    ordered_affects: list[str] = []
    for affect in ("Self", "Allies", "Enemies"):
        if affect in affects:
            ordered_affects.append(affect)

    if not ordered_affects:
        return None
    return ", ".join(ordered_affects)


def spell_effects_from_spell(
    ability_key: str,
    projectile: str | None,
    targetting: str,
    damage_type: str | None,
    collision_radius: float,
    width: float,
    description: str | None,
    dynamic_description: str | None,
) -> str | None:
    if ability_key == "P":
        return "proc" if damage_type is not None else None

    text = " ".join(filter(None, (description, dynamic_description))).lower()
    if any(token in text for token in ("nearby enemies", "around", "area")):
        return "spellaoe"
    if collision_radius > 0.0 or width > 0.0:
        return "spellaoe"
    if projectile == "TRUE":
        if targetting.startswith("Unit"):
            return "spell"
        return "spellaoe" if targetting == "Location" else "spell"
    if damage_type is not None and targetting in {"Direction", "Location"}:
        return "spellaoe"
    return None


def spellshieldable_from_spell(
    ability_key: str,
    affect: str | None,
    projectile: str | None,
    targetting: str,
    damage_type: str | None,
) -> str | None:
    if ability_key == "P":
        return "False"
    if damage_type is None or affect is None or "Enemies" not in affect:
        return None
    if projectile == "TRUE":
        return "True"
    if targetting in {"Direction", "Unit", "Unit / Direction"}:
        return "True"
    if targetting in {"Location", "Unit / Location"}:
        return "Special"
    return None


def human_stat_label(column_name: str) -> str:
    if column_name.startswith("percent_"):
        return "%" + " " + column_name.removeprefix("percent_").replace("_", " ").upper().replace("HP", "HP")
    if column_name.startswith("flat_"):
        return column_name.removeprefix("flat_").replace("_", " ").upper()
    return column_name.replace("_", " ").upper()


def normalize_stat_columns(column_names: set[str]) -> list[str]:
    return sorted(
        {
            column_name
            for column_name in column_names
            if isinstance(column_name, str) and column_name
        }
    )


def text_has(pattern: str, text: str) -> bool:
    return re.search(pattern, text) is not None


def base_stat_names_from_text(value: Any) -> set[str]:
    text = clean_text_lower(value)
    if not text:
        return set()

    stats: set[str] = set()

    if text_has(r"\btarget(?:s)?[^.;,]*\bmissing health\b", text):
        stats.add("target_missing_hp")
    elif "missing health" in text:
        stats.add("missing_hp")

    if text_has(r"\btarget(?:s)?[^.;,]*\bcurrent health\b", text):
        stats.add("target_current_hp")
    elif "current health" in text:
        stats.add("current_hp")

    if text_has(r"\btarget(?:s)?[^.;,]*\b(?:max|maximum) health\b", text):
        stats.add("target_max_hp")
    elif text_has(r"\b(?:max|maximum) health\b", text):
        stats.add("max_hp")

    if "bonus health" in text or "bonus hp" in text:
        stats.add("bonus_hp")
    elif text_has(r"\bhp\b", text) and not any(stat.endswith("_hp") for stat in stats):
        stats.add("hp")
    elif "health" in text and not any(stat.endswith("_hp") for stat in stats):
        stats.add("hp")

    if "bonus armor" in text or "bonus armour" in text:
        stats.add("bonus_armour")
    elif "armor" in text or "armour" in text:
        stats.add("armour")

    if "bonus magic resistance" in text or "bonus mr" in text:
        stats.add("bonus_magic_resistance")
    elif "magic resistance" in text or text_has(r"\bmr\b", text):
        stats.add("magic_resistance")

    if "bonus mana" in text:
        stats.add("bonus_mana")
    elif "missing mana" in text:
        stats.add("missing_mana")
    elif "max mana" in text or "maximum mana" in text:
        stats.add("max_mana")
    elif "mana" in text:
        stats.add("mana")

    if "bonus attack speed" in text:
        stats.add("bonus_attack_speed")
    elif "attack speed" in text or text_has(r"\bas\b", text):
        stats.add("attack_speed")

    if "bonus movement speed" in text:
        stats.add("bonus_movement_speed")
    elif "movement speed" in text:
        stats.add("movement_speed")

    if "critical strike" in text or "crit chance" in text or "crit" in text:
        stats.add("crit_chance")

    if text_has(r"\bability power\b|\bap\b", text):
        stats.add("ap")

    if "bonus ad" in text or "bonus attack damage" in text or "bad" in text:
        stats.add("bonus_ad")
    elif "total ad" in text or "attack damage" in text or text_has(r"\bad\b", text):
        stats.add("ad")

    if "stardust" in text:
        stats.add("stardust")
    if "soul" in text:
        stats.add("soul")
    if "chime" in text:
        stats.add("chime")
    if "mist" in text:
        stats.add("mist")
    if "feast stack" in text:
        stats.add("feast_stack")
    if "siphoning strike stack" in text:
        stats.add("siphoning_strike_stack")

    return stats


def prefixed_stat_columns_from_text(
    value: Any,
    *,
    default_prefix: str = "percent",
) -> set[str]:
    text = clean_text_lower(value)
    if not text:
        return set()

    prefix = default_prefix
    if "%" not in text and not any(
        marker in text
        for marker in ("ratio", "coefficient", "scalar", "percent")
    ):
        prefix = "flat"

    return {
        f"{prefix}_{stat_name}"
        for stat_name in base_stat_names_from_text(text)
    }


def stat_columns_from_stat_metadata(part: dict[str, Any]) -> set[str]:
    stat_code = part.get("mStat")
    stat_formula = part.get("mStatFormula")
    if stat_code == 2 and stat_formula == 2:
        return {"percent_bonus_ad"}
    if stat_code == 12 and stat_formula == 2:
        return {"percent_bonus_hp"}

    column_name = STAT_CODE_MAP.get(stat_code)
    if column_name is None:
        return set()
    return {column_name}


def collect_calc_stat_columns(
    calc_node: Any,
    calc_map: dict[str, Any],
) -> set[str]:
    if isinstance(calc_node, list):
        return set().union(
            *(collect_calc_stat_columns(item, calc_map) for item in calc_node)
        )

    if not isinstance(calc_node, dict):
        return set()

    part_type = calc_node.get("__type")
    column_names: set[str] = set()

    if part_type == "StatByNamedDataValueCalculationPart":
        column_names.update(
            prefixed_stat_columns_from_text(
                calc_node.get("mDataValue"),
                default_prefix="percent",
            )
        )
        column_names.update(stat_columns_from_stat_metadata(calc_node))
    elif part_type == "StatByCoefficientCalculationPart":
        column_names.update(stat_columns_from_stat_metadata(calc_node))
        default_column = PART_TYPE_STAT_DEFAULTS.get(part_type)
        if default_column is not None:
            column_names.add(default_column)
    elif part_type == "GameCalculationModified":
        modified_name = calc_node.get("mModifiedGameCalculation")
        if isinstance(modified_name, str):
            modified_calc = calc_map.get(modified_name)
            column_names.update(collect_calc_stat_columns(modified_calc, calc_map))

    for value in calc_node.values():
        column_names.update(collect_calc_stat_columns(value, calc_map))

    return column_names


def damage_calc_names(
    calc_map: dict[str, Any],
    dynamic_description: str | None,
) -> list[str]:
    calc_names: list[str] = []
    placeholders = {
        placeholder.lower()
        for placeholder in PLACEHOLDER_PATTERN.findall(dynamic_description or "")
    }

    for calc_name in calc_map:
        normalized_name = clean_text_lower(calc_name)
        if not normalized_name:
            continue
        if any(marker in normalized_name for marker in DAMAGE_CALC_NAME_MARKERS):
            calc_names.append(calc_name)
            continue
        if calc_name.lower() in placeholders and "damage" in (dynamic_description or "").lower():
            calc_names.append(calc_name)

    return calc_names


def extract_damage_parts(
    spell: dict[str, Any],
    dynamic_description: str | None,
) -> list[dict[str, Any]]:
    calc_map = spell.get("mSpellCalculations")
    if not isinstance(calc_map, dict):
        return []

    parts: list[dict[str, Any]] = []
    for calc_name in damage_calc_names(calc_map, dynamic_description):
        calc = calc_map.get(calc_name)
        if calc is None:
            continue
        ratio_columns = normalize_stat_columns(collect_calc_stat_columns(calc, calc_map))
        units = [human_stat_label(column_name) for column_name in ratio_columns]
        parts.append(
            {
                "name": calc_name,
                "ratioColumns": ratio_columns,
                "units": units,
            }
        )
    return parts


def ability_units_from_parts(damage_parts: list[dict[str, Any]]) -> list[str]:
    units: list[str] = []
    for damage_part in damage_parts:
        part_units = damage_part.get("units")
        if not isinstance(part_units, list):
            continue
        for unit in part_units:
            if isinstance(unit, str) and unit not in units:
                units.append(unit)
    return units


def ability_ratio_columns_from_parts(damage_parts: list[dict[str, Any]]) -> list[str]:
    columns: set[str] = set()
    for damage_part in damage_parts:
        part_columns = damage_part.get("ratioColumns")
        if not isinstance(part_columns, list):
            continue
        columns.update(
            column_name
            for column_name in part_columns
            if isinstance(column_name, str)
        )
    return normalize_stat_columns(columns)


def selected_raw_spell_fields(spell: dict[str, Any]) -> dict[str, Any]:
    return {
        "castRange": spell.get("castRange"),
        "castRadius": spell.get("castRadius"),
        "castConeAngle": spell.get("castConeAngle"),
        "mCastTime": spell.get("mCastTime"),
        "mLineWidth": spell.get("mLineWidth"),
        "missileSpeed": spell.get("missileSpeed"),
        "mAmmoRechargeTime": spell.get("mAmmoRechargeTime"),
        "mTargetingTypeData": spell.get("mTargetingTypeData"),
        "mAffectsTypeFlags": spell.get("mAffectsTypeFlags"),
        "mSpellTags": spell.get("mSpellTags"),
        "mMissileSpec": spell.get("mMissileSpec"),
    }


def root_record(bin_data: dict[str, Any]) -> dict[str, Any]:
    for record in bin_data.values():
        if isinstance(record, dict) and "spellNames" in record and "spells" in record:
            return record
    raise ValueError("Could not locate CommunityDragon root character record.")


def root_stat_value(root: dict[str, Any], field_name: str) -> float:
    field = root.get(field_name)
    if not isinstance(field, dict):
        return 0.0
    return average_numbers(
        extract_numeric_values(field.get("baseValue")),
        min_value=0.0,
    )


def champion_stats_from_root(root: dict[str, Any]) -> dict[str, float]:
    return {
        "baseMoveSpeed": root_stat_value(root, "baseMoveSpeedModifiable"),
        "attackRange": root_stat_value(root, "attackRangeModifiable"),
        "baseHP": root_stat_value(root, "baseHPModifiable"),
        "hpPerLevel": root_stat_value(root, "hpPerLevelModifiable"),
        "baseDamage": root_stat_value(root, "baseDamageModifiable"),
        "damagePerLevel": root_stat_value(root, "damagePerLevelModifiable"),
    }


def v1_spell_entries(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    spell_entries: dict[str, dict[str, Any]] = {}
    passive = entry.get("passive")
    if isinstance(passive, dict):
        spell_entries["P"] = passive

    spells = entry.get("spells")
    if isinstance(spells, list):
        for ability_key, spell_entry in zip(ABILITY_ORDER[1:], spells, strict=False):
            if isinstance(spell_entry, dict):
                spell_entries[ability_key] = spell_entry

    return spell_entries


def bin_spell_paths(root: dict[str, Any]) -> dict[str, str]:
    spell_paths: dict[str, str] = {}

    passive_path = root.get("mCharacterPassiveSpell")
    if isinstance(passive_path, str) and passive_path:
        spell_paths["P"] = passive_path

    spells = root.get("spells")
    if isinstance(spells, list):
        for ability_key, spell_path in zip(ABILITY_ORDER[1:], spells, strict=False):
            if isinstance(spell_path, str) and spell_path:
                spell_paths[ability_key] = spell_path

    return spell_paths


def build_formatted_ability(
    ability_key: str,
    root: dict[str, Any],
    v1_spell_info: dict[str, Any] | None,
    spell_record: dict[str, Any],
    spell_path: str,
) -> dict[str, Any]:
    spell = spell_record.get("mSpell")
    if not isinstance(spell, dict):
        spell = {}

    data_value_map = spell_data_value_map(spell)
    description = clean_text((v1_spell_info or {}).get("description"))
    dynamic_description = clean_text((v1_spell_info or {}).get("dynamicDescription"))
    target_range = ability_target_range(spell, v1_spell_info, data_value_map, root)
    collision_radius = resolve_spell_field(
        spell,
        v1_spell_info,
        data_value_map,
        "collisionRadius",
    )
    width = resolve_spell_field(spell, v1_spell_info, data_value_map, "width")
    projectile = projectile_from_spell(spell)
    damage_type = damage_type_from_text(description, dynamic_description)
    targetting = targetting_from_spell(ability_key, spell, target_range)
    affect = affect_from_spell(
        ability_key,
        targetting,
        description,
        dynamic_description,
        damage_type,
    )
    damage_parts = extract_damage_parts(spell, dynamic_description)

    return {
        "name": (v1_spell_info or {}).get("name"),
        "description": description,
        "dynamicDescription": dynamic_description,
        "recordPath": spell_path,
        "targetingType": raw_targeting_type(spell),
        "affect": affect,
        "resource": ability_resource_type(spell, root),
        "angle": resolve_spell_field(spell, v1_spell_info, data_value_map, "angle"),
        "castTime": resolve_spell_field(spell, v1_spell_info, data_value_map, "castTime"),
        "collisionRadius": collision_radius,
        "damageType": damage_type,
        "innerRadius": resolve_spell_field(
            spell,
            v1_spell_info,
            data_value_map,
            "innerRadius",
        ),
        "onTargetCdStatic": resolve_spell_field(
            spell,
            v1_spell_info,
            data_value_map,
            "onTargetCdStatic",
        ),
        "projectile": projectile,
        "rechargeRate": resolve_spell_field(
            spell,
            v1_spell_info,
            data_value_map,
            "rechargeRate",
        ),
        "speed": resolve_spell_field(spell, v1_spell_info, data_value_map, "speed"),
        "spellEffects": spell_effects_from_spell(
            ability_key,
            projectile,
            targetting,
            damage_type,
            collision_radius,
            width,
            description,
            dynamic_description,
        ),
        "spellshieldable": spellshieldable_from_spell(
            ability_key,
            affect,
            projectile,
            targetting,
            damage_type,
        ),
        "targetRange": target_range,
        "targetting": targetting,
        "tetherRadius": resolve_spell_field(
            spell,
            v1_spell_info,
            data_value_map,
            "tetherRadius",
        ),
        "width": width,
        "damageParts": damage_parts,
        "units": ability_units_from_parts(damage_parts),
        "ratioColumns": ability_ratio_columns_from_parts(damage_parts),
        "dataValues": data_value_map,
        "cost": (v1_spell_info or {}).get("costCoefficients"),
        "cooldown": (v1_spell_info or {}).get("cooldownCoefficients"),
        "range": (v1_spell_info or {}).get("range"),
        "raw": selected_raw_spell_fields(spell),
    }


def build_formatted_champion_entry(
    champion_entry: dict[str, Any],
    bin_data: dict[str, Any],
) -> dict[str, Any]:
    root = root_record(bin_data)
    spell_paths = bin_spell_paths(root)
    spell_entries = v1_spell_entries(champion_entry)
    abilities: dict[str, list[dict[str, Any]]] = {}

    for ability_key in ABILITY_ORDER:
        spell_path = spell_paths.get(ability_key)
        spell_record = bin_data.get(spell_path) if isinstance(spell_path, str) else None
        if not isinstance(spell_record, dict):
            continue
        v1_spell_info = spell_entries.get(ability_key)
        abilities[ability_key] = [
            build_formatted_ability(
                ability_key,
                root,
                v1_spell_info,
                spell_record,
                spell_path,
            )
        ]

    return {
        "id": champion_entry.get("id"),
        "name": champion_entry.get("name"),
        "alias": champion_entry.get("alias"),
        "lowerAlias": str(champion_entry.get("alias", "")).lower(),
        "roles": champion_entry.get("roles"),
        "resourceType": champion_resource_type(root),
        "stats": champion_stats_from_root(root),
        "sourceUrls": {
            "index": COMMUNITYDRAGON_INDEX_URL + f"{champion_entry['id']}.json",
            "bin": COMMUNITYDRAGON_BIN_URL_TEMPLATE.format(
                alias_lower=str(champion_entry["alias"]).lower(),
            ),
        },
        "abilities": abilities,
    }


def collect_formatted_communitydragon_data(
    path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
) -> dict[str, Any]:
    index_entries = fetch_communitydragon_index_entries()
    champ_id_rows = extract_champ_id_name_rows(index_entries)
    save_champ_id_name_rows(champ_id_rows)

    formatted_entries: list[tuple[str, dict[str, Any]]] = []
    with requests.Session() as session:
        for entry in index_entries:
            alias = entry.get("alias")
            name = entry.get("name")
            if not isinstance(alias, str) or not alias:
                continue
            if not isinstance(name, str) or not name:
                continue
            bin_url = COMMUNITYDRAGON_BIN_URL_TEMPLATE.format(
                alias_lower=alias.lower(),
            )
            bin_data = _session_get_json(session, bin_url)
            if not isinstance(bin_data, dict):
                continue
            formatted_entries.append(
                (name, build_formatted_champion_entry(entry, bin_data))
            )

    formatted_payload = {
        champion_name: champion_info
        for champion_name, champion_info in formatted_entries
    }
    write_json(formatted_payload, path, sort_keys=True)
    return formatted_payload


def ensure_formatted_communitydragon_data(
    *,
    refresh: bool = False,
    path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
) -> dict[str, Any]:
    if not refresh and path.exists():
        data = load_json(path)
        if isinstance(data, dict):
            return data
    return collect_formatted_communitydragon_data(path=path)


def load_formatted_communitydragon_data(
    path: Path = COMMUNITYDRAGON_FORMATTED_PATH,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    data = ensure_formatted_communitydragon_data(refresh=refresh, path=path)
    if not isinstance(data, dict):
        raise ValueError(
            "Formatted CommunityDragon payload must be a JSON object keyed by champion name."
        )
    return data


def iter_formatted_abilities(
    formatted_payload: dict[str, Any],
) -> Iterator[tuple[str, dict[str, Any], str, dict[str, Any]]]:
    for champion_name, champion_info in formatted_payload.items():
        if not isinstance(champion_name, str) or not isinstance(champion_info, dict):
            continue
        abilities = champion_info.get("abilities")
        if not isinstance(abilities, dict):
            continue
        for ability_key in ABILITY_ORDER:
            ability_entries = abilities.get(ability_key)
            if not isinstance(ability_entries, list):
                continue
            for ability in ability_entries:
                if isinstance(ability, dict):
                    yield champion_name, champion_info, ability_key, ability


def build_ability_row_base(
    champion_name: str,
    champion_info: dict[str, Any],
    ability_key: str,
) -> dict[str, Any]:
    return {
        "_key": f"{champion_name}:{ability_key}",
        "championName": champion_name,
        "championId": champion_info.get("id"),
        "abilityKey": ability_key,
    }
