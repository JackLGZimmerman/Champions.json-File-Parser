from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field

from src.models.attribute_models.attribute_models_abstracts import (
    Orchestrator,
    Stage,
    State,
)


class AffectType(str, Enum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class AffectCardinality(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class AffectDomain(str, Enum):
    PLAYERS = "players"
    STRUCTURES = "structures"
    ITEMS = "items"
    MONSTERS = "monsters"
    ENVIRONMENT = "environment"


@dataclass(frozen=True)
class TokenSpec:
    type: AffectType | None = None  # Semantic intent (offensive/defensive/etc.)
    cardinality: AffectCardinality | None = None  # Single vs multiple targets
    domain: AffectDomain | None = None  # Target category (players, structures, etc.)
    special: bool = False  # Any special-case target or summon


TOKEN_SPECS: dict[str, TokenSpec] = {
    "Self": TokenSpec(
        type=AffectType.NEUTRAL,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.PLAYERS,
    ),
    "Allies": TokenSpec(
        type=AffectType.DEFENSIVE,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.PLAYERS,
    ),
    "Enemy": TokenSpec(
        type=AffectType.OFFENSIVE,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.PLAYERS,
    ),
    "Enemies": TokenSpec(
        type=AffectType.OFFENSIVE,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.PLAYERS,
    ),
    "Structure": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.STRUCTURES,
    ),
    "Structures": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.STRUCTURES,
    ),
    "Turrets": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.STRUCTURES,
    ),
    "Allied Turrets": TokenSpec(
        type=AffectType.DEFENSIVE,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.STRUCTURES,
    ),
    "Turret Ruins": TokenSpec(
        type=AffectType.NEUTRAL,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.STRUCTURES,
    ),
    "Wards": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.ITEMS,
    ),
    "Terrain": TokenSpec(
        type=AffectType.NEUTRAL,
        domain=AffectDomain.ENVIRONMENT,
    ),
    "Monsters": TokenSpec(
        type=AffectType.NEUTRAL,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.MONSTERS,
    ),
    "Elemental": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.MONSTERS,
    ),
    "Oathsworn Ally": TokenSpec(
        type=AffectType.DEFENSIVE,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.MONSTERS,
        special=True,
    ),
    "Tibbers": TokenSpec(
        type=AffectType.OFFENSIVE,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.MONSTERS,
        special=True,
    ),
    "Spiderlings": TokenSpec(
        type=AffectType.OFFENSIVE,
        cardinality=AffectCardinality.MULTIPLE,
        domain=AffectDomain.MONSTERS,
        special=True,
    ),
    "Rakan": TokenSpec(
        type=AffectType.UNKNOWN,
        cardinality=AffectCardinality.SINGLE,
        domain=AffectDomain.PLAYERS,
        special=True,
    ),
}


class AffectsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[str] | None = None

    def _specs(self) -> list[TokenSpec]:
        tokens = self.values or []
        return [TOKEN_SPECS[t] for t in tokens if t in TOKEN_SPECS]

    @computed_field
    @property
    def types(self) -> list[AffectType]:
        out = {s.type for s in self._specs() if s.type}
        return sorted(out, key=lambda x: x.value)

    @computed_field
    @property
    def cardinalities(self) -> list[AffectCardinality]:
        out = {s.cardinality for s in self._specs() if s.cardinality}
        return sorted(out, key=lambda x: x.value)

    @computed_field
    @property
    def domains(self) -> list[AffectDomain]:
        out = {s.domain for s in self._specs() if s.domain}
        return sorted(out, key=lambda x: x.value)

    @computed_field
    @property
    def special(self) -> bool:
        return any(s.special for s in self._specs())


class AffectsOrchestrator(Orchestrator):
    name = "Affects orchestrator"
    location = "root[abilities][*][0]"
    description = (
        "This will parse the values found in the affect key of the abilities list "
        "inside the champion.json file"
    )

    state_cls = State

    def to_model(self, state: State) -> AffectsModel:
        return AffectsModel(values=state.value)


class AffectsExtractOptionsStage(Stage):
    name = "Extract options"
    level = "1"
    description = "Extract the options from attribute via splitting (',' and '/')"

    def parse(self, state: State) -> State:
        value: Any = state.value
        if isinstance(value, str):
            state.value = value.replace("/", ",").split(",")
        return state
