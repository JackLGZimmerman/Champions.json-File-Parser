from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from simulator.errors import DataNotFoundError, UnknownChampionError
from simulator.stats import StatBlock, StatGrowth, stat_at_level

CHAMPION_ID_NAME_MAP_PATH = Path("champions/champ_id_name_map.jsonl")
STATIC_BASIC_PATH = Path("champion-static-basic/basic_stats.jsonl")
VALIDATED_CHAMPIONS_PATH = Path("champions/validated.json")
FORMATTED_ABILITIES_PATH = Path("champions/communitydragon_abilities_formatted.json")
ADVANCED_ABILITIES_PATH = Path("champion-ability-advanced/abilities.jsonl")
ABILITY_FEATURES_PATH = Path("champion-ability-advanced/ability_attribute_features.jsonl")


@dataclass(frozen=True)
class ChampionIdentity:
    champion_id: int
    name: str
    alias: str | None = None


@dataclass(frozen=True)
class ChampionStatGrowth:
    champion_id: int
    champion_name: str
    max_health: StatGrowth = field(default_factory=StatGrowth)
    attack_damage: StatGrowth = field(default_factory=StatGrowth)
    armor: StatGrowth = field(default_factory=StatGrowth)
    magic_resistance: StatGrowth = field(default_factory=StatGrowth)

    def at_level(self, level: int) -> StatBlock:
        return StatBlock(
            champion_id=self.champion_id,
            champion_name=self.champion_name,
            max_health=stat_at_level(self.max_health, level),
            attack_damage=stat_at_level(self.attack_damage, level),
            armor=stat_at_level(self.armor, level),
            magic_resistance=stat_at_level(self.magic_resistance, level),
        )


class SimulatorDataRepository:
    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self._formatted_abilities = self._load_optional_json(FORMATTED_ABILITIES_PATH)
        self._advanced_abilities = self._index_ability_rows(
            self._load_optional_jsonl(ADVANCED_ABILITIES_PATH)
        )
        self._ability_features = self._index_ability_rows(
            self._load_optional_jsonl(ABILITY_FEATURES_PATH)
        )
        self._champions_by_key = self._load_champion_identities()
        self._stats_by_id = self._load_stat_growth()

    def resolve_champion(self, value: str) -> ChampionIdentity:
        key = normalize_lookup_key(value)
        champion = self._champions_by_key.get(key)
        if champion is None:
            raise UnknownChampionError(f"Unknown champion: {value!r}")
        return champion

    def champion_stats(
        self,
        champion: ChampionIdentity,
        *,
        level: int,
        overrides: Mapping[str, float],
    ) -> StatBlock:
        growth = self._stats_by_id.get(champion.champion_id)
        if growth is None:
            raise DataNotFoundError(
                f"No stat data available for {champion.name} ({champion.champion_id})"
            )
        return growth.at_level(level).with_overrides(overrides)

    def formatted_ability(
        self,
        champion: ChampionIdentity,
        ability_key: str,
    ) -> dict[str, Any] | None:
        champion_entry = self._formatted_abilities.get(champion.name)
        if not isinstance(champion_entry, dict):
            return None
        abilities = champion_entry.get("abilities")
        if not isinstance(abilities, dict):
            return None
        ability_entries = abilities.get(ability_key)
        if not isinstance(ability_entries, list) or not ability_entries:
            return None
        ability = ability_entries[0]
        return ability if isinstance(ability, dict) else None

    def advanced_ability(
        self,
        champion: ChampionIdentity,
        ability_key: str,
    ) -> dict[str, Any] | None:
        return self._advanced_abilities.get((champion.champion_id, ability_key))

    def ability_features(
        self,
        champion: ChampionIdentity,
        ability_key: str,
    ) -> dict[str, Any] | None:
        return self._ability_features.get((champion.champion_id, ability_key))

    def _path(self, relative_path: Path) -> Path:
        return self.data_dir / relative_path

    def _load_optional_json(self, relative_path: Path) -> dict[str, Any]:
        path = self._path(relative_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}

    def _load_optional_jsonl(self, relative_path: Path) -> list[dict[str, Any]]:
        path = self._path(relative_path)
        if not path.exists():
            return []

        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
        return rows

    def _load_champion_identities(self) -> dict[str, ChampionIdentity]:
        champions: dict[int, ChampionIdentity] = {}
        for row in self._load_optional_jsonl(CHAMPION_ID_NAME_MAP_PATH):
            champion_id = int(row["_key"])
            champions[champion_id] = ChampionIdentity(
                champion_id=champion_id,
                name=str(row["name"]),
                alias=str(row["alias"]) if row.get("alias") else None,
            )

        for champion_name, champion_entry in self._formatted_abilities.items():
            if not isinstance(champion_entry, dict):
                continue
            champion_id = champion_entry.get("id")
            if not isinstance(champion_id, int) or champion_id in champions:
                continue
            champions[champion_id] = ChampionIdentity(
                champion_id=champion_id,
                name=champion_name,
                alias=(
                    str(champion_entry["alias"])
                    if isinstance(champion_entry.get("alias"), str)
                    else None
                ),
            )

        if not champions:
            raise DataNotFoundError(
                "No champion identity data found in champ_id_name_map or "
                "communitydragon_abilities_formatted.json"
            )

        champions_by_key: dict[str, ChampionIdentity] = {}
        for champion in champions.values():
            for value in (champion.name, champion.alias, str(champion.champion_id)):
                if value:
                    champions_by_key[normalize_lookup_key(value)] = champion
        return champions_by_key

    def _load_stat_growth(self) -> dict[int, ChampionStatGrowth]:
        stats = self._stats_from_static_basic()
        if stats:
            return stats

        stats = self._stats_from_validated_champions()
        if stats:
            return stats

        return self._stats_from_formatted_abilities()

    def _stats_from_static_basic(self) -> dict[int, ChampionStatGrowth]:
        stats: dict[int, ChampionStatGrowth] = {}
        for row in self._load_optional_jsonl(STATIC_BASIC_PATH):
            champion_id = row.get("id")
            if not isinstance(champion_id, int):
                continue
            stats[champion_id] = ChampionStatGrowth(
                champion_id=champion_id,
                champion_name=str(row.get("_key") or champion_id),
                max_health=flat_per_level(row, "health"),
                attack_damage=flat_per_level(row, "attackDamage"),
                armor=flat_per_level(row, "armor"),
                magic_resistance=flat_per_level(row, "magicResistance"),
            )
        return stats

    def _stats_from_validated_champions(self) -> dict[int, ChampionStatGrowth]:
        data = self._load_optional_json(VALIDATED_CHAMPIONS_PATH)
        stats: dict[int, ChampionStatGrowth] = {}
        for champion_name, champion_entry in data.items():
            if not isinstance(champion_entry, dict):
                continue
            champion_id = champion_entry.get("id")
            champion_stats = champion_entry.get("stats")
            if not isinstance(champion_id, int) or not isinstance(champion_stats, dict):
                continue
            stats[champion_id] = ChampionStatGrowth(
                champion_id=champion_id,
                champion_name=champion_name,
                max_health=metric_growth(champion_stats.get("health")),
                attack_damage=metric_growth(champion_stats.get("attackDamage")),
                armor=metric_growth(champion_stats.get("armor")),
                magic_resistance=metric_growth(
                    champion_stats.get("magicResistance")
                ),
            )
        return stats

    def _stats_from_formatted_abilities(self) -> dict[int, ChampionStatGrowth]:
        stats: dict[int, ChampionStatGrowth] = {}
        for champion_name, champion_entry in self._formatted_abilities.items():
            if not isinstance(champion_entry, dict):
                continue
            champion_id = champion_entry.get("id")
            root_stats = champion_entry.get("stats")
            if not isinstance(champion_id, int) or not isinstance(root_stats, dict):
                continue
            stats[champion_id] = ChampionStatGrowth(
                champion_id=champion_id,
                champion_name=champion_name,
                max_health=StatGrowth(
                    optional_float(root_stats.get("baseHP")),
                    optional_float(root_stats.get("hpPerLevel")) or 0.0,
                ),
                attack_damage=StatGrowth(
                    optional_float(root_stats.get("baseDamage")),
                    optional_float(root_stats.get("damagePerLevel")) or 0.0,
                ),
            )
        return stats

    def _index_ability_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[tuple[int, str], dict[str, Any]]:
        indexed: dict[tuple[int, str], dict[str, Any]] = {}
        for row in rows:
            champion_id = row.get("championId")
            ability_key = row.get("abilityKey")
            if isinstance(champion_id, int) and isinstance(ability_key, str):
                indexed[(champion_id, ability_key.upper())] = row
        return indexed


def normalize_lookup_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def flat_per_level(row: Mapping[str, Any], stat_name: str) -> StatGrowth:
    return StatGrowth(
        base=optional_float(row.get(f"{stat_name}_flat")),
        per_level=optional_float(row.get(f"{stat_name}_perLevel")) or 0.0,
    )


def metric_growth(metric: Any) -> StatGrowth:
    if not isinstance(metric, dict):
        return StatGrowth()
    return StatGrowth(
        base=optional_float(metric.get("flat")),
        per_level=optional_float(metric.get("perLevel")) or 0.0,
    )
