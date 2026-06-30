from __future__ import annotations

from typing import Any

from simulator.data import ChampionIdentity
from simulator.errors import DataNotFoundError, UnsupportedFormulaError
from simulator.models import DamageEvent
from simulator.parser import ParsedAction
from simulator.stats import StatBlock, validate_ability_rank

PHYSICAL_DAMAGE = "PHYSICAL_DAMAGE"
MAGIC_DAMAGE = "MAGIC_DAMAGE"
TRUE_DAMAGE = "TRUE_DAMAGE"
SUPPORTED_DAMAGE_TYPES = {PHYSICAL_DAMAGE, MAGIC_DAMAGE, TRUE_DAMAGE}


def calculate_damage_event(
    *,
    action: ParsedAction,
    attacker: ChampionIdentity,
    attacker_stats: StatBlock,
    target_stats: StatBlock,
    ability_rank: int,
    formatted_ability: dict[str, Any] | None,
    advanced_ability: dict[str, Any] | None,
    target_health_before: float | None,
) -> DamageEvent:
    validate_ability_rank(ability_rank)
    raw_damage, damage_type, notes = calculate_raw_damage(
        action=action,
        attacker=attacker,
        attacker_stats=attacker_stats,
        target_stats=target_stats,
        ability_rank=ability_rank,
        formatted_ability=formatted_ability,
        advanced_ability=advanced_ability,
    )
    mitigated_damage = mitigate_damage(raw_damage, damage_type, target_stats)
    target_health_after = (
        None
        if target_health_before is None
        else max(0.0, target_health_before - mitigated_damage)
    )

    return DamageEvent(
        action=action.raw,
        champion_id=attacker.champion_id,
        champion_name=attacker.name,
        ability_key=action.ability_key,
        qualifier=action.qualifier,
        damage_type=damage_type,
        raw_damage=raw_damage,
        mitigated_damage=mitigated_damage,
        target_health_before=target_health_before,
        target_health_after=target_health_after,
        notes=tuple(notes),
    )


def calculate_raw_damage(
    *,
    action: ParsedAction,
    attacker: ChampionIdentity,
    attacker_stats: StatBlock,
    target_stats: StatBlock,
    ability_rank: int,
    formatted_ability: dict[str, Any] | None,
    advanced_ability: dict[str, Any] | None,
) -> tuple[float, str | None, list[str]]:
    if attacker.name == "Aatrox" and action.ability_key == "Q":
        return aatrox_q_damage(
            action=action,
            attacker_stats=attacker_stats,
            target_stats=target_stats,
            ability_rank=ability_rank,
            formatted_ability=formatted_ability,
        )

    if attacker.name == "Aatrox" and action.ability_key == "E":
        return (
            0.0,
            None,
            ["Aatrox E has no direct target damage in simulator V1."],
        )

    return generic_direct_damage(
        action=action,
        attacker_stats=attacker_stats,
        target_stats=target_stats,
        ability_rank=ability_rank,
        formatted_ability=formatted_ability,
        advanced_ability=advanced_ability,
    )


def aatrox_q_damage(
    *,
    action: ParsedAction,
    attacker_stats: StatBlock,
    target_stats: StatBlock,
    ability_rank: int,
    formatted_ability: dict[str, Any] | None,
) -> tuple[float, str, list[str]]:
    if formatted_ability is None:
        raise DataNotFoundError("Aatrox Q formatted ability data is missing.")
    data_values = ability_data_values(formatted_ability)
    activation_index = action.activation_index or 1
    if activation_index < 1 or activation_index > 3:
        raise UnsupportedFormulaError(
            f"Aatrox Q supports Activation 1-3, got {activation_index}."
        )

    base_damage = rank_value(data_values, "QBaseDamage", ability_rank)
    ad_ratio = rank_value(data_values, "QTotalADRatio", ability_rank)
    ramp_bonus = rank_value(data_values, "QRampBonus", ability_rank)
    sweet_spot_bonus = rank_value(data_values, "QSweetSpotBonus", ability_rank)
    attack_damage = attacker_stats.require("attack_damage")

    activation_multiplier = 1.0 + (activation_index - 1) * ramp_bonus
    raw_damage = (base_damage + ad_ratio * attack_damage) * activation_multiplier
    notes = [f"Aatrox Q activation {activation_index}."]
    if action.is_sweet_spot:
        raw_damage *= 1.0 + sweet_spot_bonus
        notes.append("Applied Aatrox Q sweet spot bonus.")

    target_stats.require("armor")
    return raw_damage, PHYSICAL_DAMAGE, notes


def generic_direct_damage(
    *,
    action: ParsedAction,
    attacker_stats: StatBlock,
    target_stats: StatBlock,
    ability_rank: int,
    formatted_ability: dict[str, Any] | None,
    advanced_ability: dict[str, Any] | None,
) -> tuple[float, str, list[str]]:
    if formatted_ability is None:
        raise DataNotFoundError(f"No formatted ability data for {action.raw!r}.")

    damage_type = ability_damage_type(formatted_ability, advanced_ability)
    if damage_type not in SUPPORTED_DAMAGE_TYPES:
        raise UnsupportedFormulaError(
            f"{action.raw!r} has unsupported or ambiguous damage type: {damage_type}"
        )

    damage_parts = formatted_ability.get("damageParts")
    if not isinstance(damage_parts, list) or len(damage_parts) != 1:
        raise UnsupportedFormulaError(
            f"{action.raw!r} does not have one simple direct damage part."
        )

    damage_part = damage_parts[0]
    if not isinstance(damage_part, dict):
        raise UnsupportedFormulaError(f"{action.raw!r} has malformed damage data.")

    data_values = ability_data_values(formatted_ability)
    base_key = resolve_base_damage_key(
        data_values=data_values,
        damage_part=damage_part,
        ability_key=action.ability_key,
    )
    ratio_columns = [
        column
        for column in damage_part.get("ratioColumns", [])
        if isinstance(column, str)
    ]
    non_zero_ratio_columns = [
        column
        for column in ratio_columns
        if stat_column_value(column, attacker_stats, target_stats) != 0.0
    ]
    if non_zero_ratio_columns:
        raise UnsupportedFormulaError(
            f"{action.raw!r} has unsupported non-zero ratios: "
            f"{', '.join(non_zero_ratio_columns)}"
        )

    raw_damage = rank_value(data_values, base_key, ability_rank)
    notes = [f"Used generic direct damage value {base_key}."]
    if ratio_columns:
        notes.append("Ratio contribution is zero for current simulator stats.")
    return raw_damage, damage_type, notes


def mitigate_damage(raw_damage: float, damage_type: str | None, target_stats: StatBlock) -> float:
    if raw_damage <= 0.0:
        return 0.0
    if damage_type == TRUE_DAMAGE:
        return raw_damage
    if damage_type == PHYSICAL_DAMAGE:
        resistance = target_stats.require("armor")
    elif damage_type == MAGIC_DAMAGE:
        resistance = target_stats.require("magic_resistance")
    else:
        raise UnsupportedFormulaError(f"Cannot mitigate damage type: {damage_type}")

    if resistance >= 0:
        return raw_damage * 100.0 / (100.0 + resistance)
    return raw_damage * (2.0 - 100.0 / (100.0 - resistance))


def ability_data_values(ability: dict[str, Any]) -> dict[str, list[float]]:
    values = ability.get("dataValues")
    if not isinstance(values, dict):
        return {}

    normalized: dict[str, list[float]] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not isinstance(value, list):
            continue
        numeric_values = [
            float(item)
            for item in value
            if isinstance(item, int | float) and not isinstance(item, bool)
        ]
        if numeric_values:
            normalized[key] = numeric_values
    return normalized


def rank_value(data_values: dict[str, list[float]], key: str, rank: int) -> float:
    values = data_values.get(key)
    if not values:
        raise DataNotFoundError(f"Missing ability data value: {key}")
    if len(values) > 6 and rank < len(values):
        return values[rank]
    if len(values) > 1 and values[0] <= 0.0 and rank < len(values):
        return values[rank]
    return values[min(rank - 1, len(values) - 1)]


def ability_damage_type(
    formatted_ability: dict[str, Any],
    advanced_ability: dict[str, Any] | None,
) -> str | None:
    damage_type = formatted_ability.get("damageType")
    if isinstance(damage_type, str):
        return damage_type
    if advanced_ability is not None and isinstance(advanced_ability.get("damageType"), str):
        return advanced_ability["damageType"]
    return None


def resolve_base_damage_key(
    *,
    data_values: dict[str, list[float]],
    damage_part: dict[str, Any],
    ability_key: str,
) -> str:
    part_name = damage_part.get("name")
    preferred_keys = [
        part_name if isinstance(part_name, str) else None,
        "BaseDamage",
        f"{ability_key}BaseDamage",
        "Damage",
        f"{ability_key}Damage",
    ]
    for key in preferred_keys:
        if key in data_values:
            return key

    candidates = [
        key
        for key in data_values
        if key.lower().endswith("basedamage") or key.lower() == "damage"
    ]
    if len(candidates) == 1:
        return candidates[0]

    raise UnsupportedFormulaError(
        "Could not safely identify one base damage value for "
        f"{part_name or ability_key}."
    )


def stat_column_value(
    column: str,
    attacker_stats: StatBlock,
    target_stats: StatBlock,
) -> float:
    if column in {"percent_ad", "flat_ad"}:
        return attacker_stats.require("attack_damage")
    if column in {"percent_bonus_ad", "flat_bonus_ad"}:
        return attacker_stats.bonus_attack_damage
    if column in {"percent_ap", "flat_ap"}:
        return attacker_stats.ability_power
    if column in {"percent_target_max_hp", "flat_target_max_hp"}:
        return target_stats.require("max_health")
    if column in {"percent_target_current_hp", "flat_target_current_hp"}:
        return target_stats.require("max_health")
    raise UnsupportedFormulaError(f"Unsupported scaling stat column: {column}")
