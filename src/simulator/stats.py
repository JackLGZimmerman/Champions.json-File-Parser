from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from simulator.errors import MissingStatError


@dataclass(frozen=True)
class StatGrowth:
    base: float | None = None
    per_level: float = 0.0


@dataclass(frozen=True)
class StatBlock:
    champion_id: int
    champion_name: str
    max_health: float | None = None
    attack_damage: float | None = None
    armor: float | None = None
    magic_resistance: float | None = None
    ability_power: float = 0.0
    bonus_attack_damage: float = 0.0

    def with_overrides(self, overrides: Mapping[str, float]) -> StatBlock:
        normalized = {
            normalize_stat_name(stat_name): float(value)
            for stat_name, value in overrides.items()
        }
        values: dict[str, float | int | str | None] = {
            "champion_id": self.champion_id,
            "champion_name": self.champion_name,
            "max_health": self.max_health,
            "attack_damage": self.attack_damage,
            "armor": self.armor,
            "magic_resistance": self.magic_resistance,
            "ability_power": self.ability_power,
            "bonus_attack_damage": self.bonus_attack_damage,
        }
        unknown_stats = sorted(set(normalized) - set(values))
        if unknown_stats:
            raise ValueError(
                "Unknown stat override(s): " + ", ".join(unknown_stats)
            )
        values.update(normalized)
        return replace(self, **values)

    def require(self, stat_name: str) -> float:
        normalized_name = normalize_stat_name(stat_name)
        value = getattr(self, normalized_name, None)
        if value is None:
            raise MissingStatError(
                f"{self.champion_name} is missing required stat: {normalized_name}"
            )
        return float(value)


STAT_NAME_ALIASES = {
    "ad": "attack_damage",
    "attackdamage": "attack_damage",
    "attack_damage": "attack_damage",
    "armor": "armor",
    "armour": "armor",
    "ap": "ability_power",
    "abilitypower": "ability_power",
    "ability_power": "ability_power",
    "bonusad": "bonus_attack_damage",
    "bonusattackdamage": "bonus_attack_damage",
    "bonus_attack_damage": "bonus_attack_damage",
    "health": "max_health",
    "hp": "max_health",
    "maxhp": "max_health",
    "maxhealth": "max_health",
    "max_health": "max_health",
    "magicresistance": "magic_resistance",
    "magic_resistance": "magic_resistance",
    "mr": "magic_resistance",
}


def normalize_stat_name(stat_name: str) -> str:
    key = "".join(character for character in stat_name.lower() if character.isalnum())
    return STAT_NAME_ALIASES.get(key, stat_name)


def growth_multiplier(level: int) -> float:
    validate_level(level)
    if level == 1:
        return 0.0
    levels_gained = level - 1
    return levels_gained * (0.7025 + 0.0175 * levels_gained)


def stat_at_level(growth: StatGrowth, level: int) -> float | None:
    if growth.base is None:
        return None
    return growth.base + growth.per_level * growth_multiplier(level)


def validate_level(level: int) -> None:
    if level < 1 or level > 18:
        raise ValueError(f"Champion level must be between 1 and 18: {level}")


def validate_ability_rank(rank: int) -> None:
    if rank < 1 or rank > 6:
        raise ValueError(f"Ability rank must be between 1 and 6: {rank}")
