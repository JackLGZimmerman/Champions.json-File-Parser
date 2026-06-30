from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

ActionInput = str | Sequence[str]


@dataclass(frozen=True)
class SimulationRequest:
    attacker: str
    target: str
    actions: ActionInput
    attacker_level: int = 1
    target_level: int = 1
    ability_ranks: Mapping[str, int] = field(default_factory=dict)
    attacker_stat_overrides: Mapping[str, float] = field(default_factory=dict)
    target_stat_overrides: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationWarning:
    code: str
    message: str
    action: str | None = None


@dataclass(frozen=True)
class DamageEvent:
    action: str
    champion_id: int
    champion_name: str
    ability_key: str
    qualifier: str | None
    damage_type: str | None
    raw_damage: float
    mitigated_damage: float
    target_health_before: float | None
    target_health_after: float | None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimulationResult:
    attacker_id: int
    attacker_name: str
    target_id: int
    target_name: str
    events: tuple[DamageEvent, ...]
    warnings: tuple[SimulationWarning, ...] = ()

    @property
    def total_raw_damage(self) -> float:
        return sum(event.raw_damage for event in self.events)

    @property
    def total_damage(self) -> float:
        return sum(event.mitigated_damage for event in self.events)

    @property
    def remaining_health(self) -> float | None:
        if not self.events:
            return None
        return self.events[-1].target_health_after
