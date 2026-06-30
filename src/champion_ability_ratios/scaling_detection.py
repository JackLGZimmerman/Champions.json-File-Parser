from __future__ import annotations

import re
from typing import Any

DAMAGE_REDUCTION_PATTERNS = (
    r"\bdamage reduction\b",
    r"\breduced damage\b",
    r"\bdamage taken\b",
)
SCALING_DESCRIPTION_PATTERNS = (
    r"\+\s*[^.;\]\[]+",
    r"%[^.;\]\[]*\bof\s+[^.;\]\[]+",
    r"based on\s+[^.;\]\[]+",
    r"per\s+100%?\s+[^.;\]\[]+",
    r"scales?\s+with\s+[^.;\]\[]+",
)
NON_DAMAGE_DESCRIPTION_MARKERS = (
    "heal",
    "heals",
    "healing",
    "restore",
    "restores",
    "restoring",
    "shield",
    "movement speed",
)


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = text.replace("’", "'")
    text = text.replace("move speed", "movement speed")
    text = text.replace("movespeed", "movement speed")
    return re.sub(r"\s+", " ", text.lower()).strip()


def text_has(pattern: str, text: str) -> bool:
    return re.search(pattern, text) is not None


def base_stat_names_from_text(value: Any) -> set[str]:
    text = normalize_text(value)
    if not text:
        return set()

    stats: set[str] = set()

    if text_has(r"\btarget(?:'s)?[^.;,]*\bmissing health\b", text):
        stats.add("target_missing_hp")
    elif "missing health" in text:
        stats.add("missing_hp")

    if text_has(r"\btarget(?:'s)?[^.;,]*\bcurrent health\b", text):
        stats.add("target_current_hp")
    elif "current health" in text:
        stats.add("current_hp")

    if text_has(r"\btarget(?:'s)?[^.;,]*\b(?:maximum|max) health\b", text):
        stats.add("target_max_hp")
    elif text_has(r"\b(?:maximum|max) health\b", text):
        stats.add("max_hp")

    if "bonus health" in text or "bonus hp" in text:
        stats.add("bonus_hp")
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
    elif "maximum mana" in text or "max mana" in text:
        stats.add("max_mana")
    elif "mana" in text:
        stats.add("mana")

    if "bonus attack speed" in text:
        stats.add("bonus_attack_speed")
    elif "attack speed" in text:
        stats.add("attack_speed")

    if "bonus movement speed" in text:
        stats.add("bonus_movement_speed")
    elif "movement speed" in text:
        stats.add("movement_speed")

    if "critical strike" in text or "crit chance" in text or "crit" in text:
        stats.add("crit_chance")

    if text_has(r"\bability power\b|\bap\b", text):
        stats.add("ap")

    if "bonus ad" in text or "bonus attack damage" in text:
        stats.add("bonus_ad")
    elif text_has(r"\battack damage\b|\bad\b|\btotal ad\b", text):
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


def scale_prefix_from_text(value: Any, *, default_prefix: str = "percent") -> str:
    text = normalize_text(value)
    if "%" in text or any(
        marker in text for marker in ("ratio", "coefficient", "scalar", "percent")
    ):
        return "percent"
    return default_prefix


def stat_column_names_from_text(
    value: Any,
    *,
    default_prefix: str = "percent",
) -> set[str]:
    prefix = scale_prefix_from_text(value, default_prefix=default_prefix)
    return {
        f"{prefix}_{stat_name}"
        for stat_name in base_stat_names_from_text(value)
    }


def stat_column_names_from_description(description: Any) -> set[str]:
    text = normalize_text(description)
    if not text:
        return set()
    if any(re.search(pattern, text) for pattern in DAMAGE_REDUCTION_PATTERNS):
        return set()

    stats: set[str] = set()
    for match in re.finditer(r"damage[^.]*based on\s+[^.;\]\[]+", text):
        stats.update(stat_column_names_from_text(match.group(0)))
    fragments = [
        fragment.strip()
        for fragment in re.split(r"[.;]|\band\b", text)
        if fragment.strip()
    ]
    for fragment in fragments:
        if "damage" not in fragment and "on-hit" not in fragment:
            continue
        if any(marker in fragment for marker in NON_DAMAGE_DESCRIPTION_MARKERS):
            continue
        for pattern in SCALING_DESCRIPTION_PATTERNS:
            for match in re.finditer(pattern, fragment):
                stats.update(stat_column_names_from_text(match.group(0)))
    return stats


def extract_ability_scaling_stats(ability: dict[str, Any]) -> set[str]:
    stats: set[str] = set()

    ratio_columns = ability.get("ratioColumns")
    if isinstance(ratio_columns, list):
        stats.update(
            column_name
            for column_name in ratio_columns
            if isinstance(column_name, str)
        )

    description = ability.get("description")
    dynamic_description = ability.get("dynamicDescription")
    stats.update(stat_column_names_from_description(description))
    stats.update(stat_column_names_from_description(dynamic_description))
    return stats
