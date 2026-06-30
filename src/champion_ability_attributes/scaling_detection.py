from __future__ import annotations

import re
from typing import Any

SCALING_DESCRIPTION_PATTERNS = (
    (r"\+\s*[^.;\]\[]+", "flat"),
    (r"%[^.;\]\[]*\bof\s+[^.;\]\[]+", "percent"),
    (
        r"%\s+(?:of\s+)?(?:the\s+)?(?:target(?:'s)?|enemy(?:'s)?|their\s+)?"
        r"(?:max(?:imum)?|missing|current) health\b[^.;\]\[]*",
        "percent",
    ),
    (r"\bpercentage[^.;\]\[]*\bof\s+[^.;\]\[]+", "percent"),
    (r"based on\s+[^.;\]\[]+", "percent"),
    (r"per\s+(?:\d+|@\w+@)%?\s+[^.;\]\[]+", "percent"),
    (r"scales?\s+with\s+[^.;\]\[]+", "percent"),
    (r"increases?\s+with\s+[^.;\]\[]+", "percent"),
    (r"increased by\s+[^.;\]\[]+", "percent"),
    (
        r"\b(?:max(?:imum)?|missing|current) health\b"
        r"\s+(?:magic|physical|true)?\s*damage\b",
        "percent",
    ),
)
CC_PATTERNS = {
    "cc_slow": r"\bslow(?:s|ed|ing)?\b",
    "cc_stun": r"\bstun(?:s|ned|ning)?\b",
    "cc_root": r"\broot(?:s|ed|ing)?\b|immobili[sz]",
    "cc_knock": r"\bknock(?:s|ed|ing)?\b|airborne|pull(?:s|ed|ing)?",
    "cc_suppress": r"\bsuppress(?:es|ed|ing)?\b",
    "cc_fear": r"\bfear(?:s|ed|ing)?\b",
    "cc_charm": r"\bcharm(?:s|ed|ing)?\b",
    "cc_silence": r"\bsilenc(?:e|es|ed|ing)\b",
    "cc_taunt": r"\btaunt(?:s|ed|ing)?\b",
    "cc_blind": r"\bblind(?:s|ed|ing)?\b",
    "cc_sleep": r"\bsleep|drowsy\b",
}
CONCEPT_PATTERNS = {
    "eff_heal": r"\bheal(?:s|ed|ing)?\b|\brestore(?:s|d|ing)?\b",
    "eff_shield": r"\bshield(?:s|ed|ing)?\b",
    "eff_ms": r"\bmovement speed\b|\bmove speed\b",
    "eff_dash": r"\bdash(?:es|ed|ing)?\b|\bblink(?:s|ed|ing)?\b|\bleap(?:s|ed|ing)?\b",
    "eff_dr": r"\bdamage reduction\b|\breduced damage\b|\bdamage taken\b",
    "eff_arpen": r"\b(?:armor|armour) penetration\b",
    "eff_mpen": r"\bmagic penetration\b",
    "eff_stealth": r"\bstealth\b|\binvisible\b|\bcamouflage\b",
    "eff_reveal": r"\breveal(?:s|ed|ing)?\b",
    "eff_as": r"\battack speed\b",
}
DAMAGE_TYPE_CONCEPTS = {
    "MAGIC_DAMAGE": "dmg_magic",
    "PHYSICAL_DAMAGE": "dmg_phys",
    "TRUE_DAMAGE": "dmg_true",
    "OTHER_DAMAGE": "dmg_mixed",
}
STACK_SCALING_PATTERNS = (
    r"\bstardust\b",
    r"\bphenomenal evil\b",
    r"\bdragon practice\b",
    r"\bsplinters of wrath\b",
    r"\bhex fragments?\b",
    r"\badoration\b",
    r"\bscalemail\b",
    r"\baccelerando\b",
    r"\bdetermination\b[^.;]*(?:stack|bonus attack damage)",
    r"\boverwhelm\b[^.;]*(?:stack|damage)",
    r"\bvoid coral\b|\blavender\b",
    r"\bfeast\b[^.;]*\bstack|\bstack[^.;]*\bfeast",
    r"\bfuture siphoning strikes?\b|\bsiphoning strike[^.;]*permanent",
    r"\bsoul fragments?\b",
    r"\bharvest[^.;]*\bsouls?\b",
    r"\bmist fuels\b",
    r"\bsouls?\b[^.;]*(?:trapped|absorbing|attack damage|attack range|critical strike)",
    r"\bchimes?\b|\bmeeps?\b",
    r"\bhunts? completed\b|\bhunt permanently empowers\b",
    r"\bpermanent(?:ly)?\b[^.;]*(?:stacks?|ability power|max(?:imum)? health)",
    r"\bpermanent(?:ly)?\b[^.;]*(?:ability haste|augments?|empowers?|improves?)",
    r"\bpermanently increases?[^.;]*damage",
    r"\bpermanently granting[^.;]*(?:armor|armour|ability power)",
    r"\bkilling units permanently grants?\b[^.;]*(?:resists?|armor|armour|magic resist)",
    r"\bgains?[^.;]*max health[^.;]*(?:kills?|takedowns?)",
    r"\bkills?[^.;]*gains?[^.;]*max health",
    r"\bcollect(?:s|ed|ing)?[^.;]*(?:stardust|chimes?|souls?|soul fragments?)",
    r"\bcollect(?:s|ed|ing)?[^.;]*(?:splinters|hex fragments)",
    r"\bstacks? increase[^.;]*(?:damage|abilities)",
    r"\bbased on stacks of\b",
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

    target_reference = r"(?:targets?|enemies|enemy(?: champion)?|their)"
    possessive_target_reference = rf"{target_reference}(?:'s)?"

    if text_has(rf"\b{possessive_target_reference}\s+missing health\b", text):
        stats.add("target_missing_hp")
    elif "missing health" in text:
        stats.add("missing_hp")

    if text_has(rf"\b{possessive_target_reference}\s+current health\b", text):
        stats.add("target_current_hp")
    elif "current health" in text:
        stats.add("current_hp")

    if text_has(
        rf"\b{possessive_target_reference}\s+(?:maximum|max) health\b",
        text,
    ) or text_has(
        r"\b(?:maximum|max) health\b\s+(?:magic|physical|true)?\s*damage\b",
        text,
    ):
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

    if "armor penetration" in text or "armour penetration" in text:
        stats.add("armour_pen")
    if "magic penetration" in text:
        stats.add("magic_pen")
    if "lethality" in text:
        stats.add("lethality")
    if text_has(r"\b(?:champion )?level\b", text):
        stats.add("level")
    if "tenacity" in text:
        stats.add("tenacity")

    if text_has(r"\bability power\b|\bap\b", text):
        stats.add("ap")

    if "bonus ad" in text or "bonus attack damage" in text:
        stats.add("bonus_ad")
    elif text_has(r"\battack damage\b|\bad\b|\btotal ad\b", text):
        stats.add("ad")

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

    stats: set[str] = set()
    for match in re.finditer(r"damage[^.]*based on\s+[^.;\]\[]+", text):
        stats.update(stat_column_names_from_text(match.group(0)))
    for fragment in (fragment.strip() for fragment in re.split(r"[.;]", text)):
        for match in re.finditer(r"\bpercentage[^.;\]\[]*\bof\s+[^.;\]\[]+", fragment):
            stats.update(stat_column_names_from_text(match.group(0)))
    fragments = [
        fragment.strip()
        for fragment in re.split(r"[.;]|\band\b", text)
        if fragment.strip()
    ]
    for fragment in fragments:
        for pattern, default_prefix in SCALING_DESCRIPTION_PATTERNS:
            for match in re.finditer(pattern, fragment):
                stats.update(
                    stat_column_names_from_text(
                        match.group(0),
                        default_prefix=default_prefix,
                    )
                )
    return stats


def extract_ability_concepts(ability: dict[str, Any]) -> set[str]:
    text = normalize_text(
        " ".join(
            str(ability.get(key) or "")
            for key in ("description", "dynamicDescription")
        )
    )
    concepts = {
        concept
        for concept, pattern in CONCEPT_PATTERNS.items()
        if text_has(pattern, text)
    }
    if grants_resist_buff(text):
        concepts.add("eff_resist")
    if has_stack_scaling(text):
        concepts.add("stack_scaling")
    cc_concepts = {
        concept
        for concept, pattern in CC_PATTERNS.items()
        if text_has(pattern, text)
    }
    concepts.update(cc_concepts)
    if cc_concepts:
        concepts.add("cc")

    damage_type = ability.get("damageType")
    if isinstance(damage_type, str) and damage_type in DAMAGE_TYPE_CONCEPTS:
        concepts.add(DAMAGE_TYPE_CONCEPTS[damage_type])
    if ability.get("projectile") == "TRUE":
        concepts.add("proj")
    if ability.get("spellEffects") == "spellaoe":
        concepts.add("aoe")
    return concepts


def has_stack_scaling(text: str) -> bool:
    return any(text_has(pattern, text) for pattern in STACK_SCALING_PATTERNS)


def grants_resist_buff(text: str) -> bool:
    for fragment in re.split(r"[.;]", text):
        if "penetration" in fragment:
            continue
        if text_has(
            r"\b(?:gain|gains|gaining|grant|grants|increas\w+|bonus)\b"
            r"[^.;]*\b(?:armor|armour|magic resist|magic resistance|resists)\b",
            fragment,
        ):
            return True
    return False


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
