from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any, Mapping

from pydantic import BaseModel, BeforeValidator
from pydantic_core import PydanticCustomError

"""
Orchestrator
 └── Stage 1
     ├── Correction A
     ├── Correction B
 └── Stage 2
     ├── Correction C
"""
# ===================== Abstract State =====================


@dataclass
class State:
    """Represents the current state of parsed data."""

    attribute: str
    location: str
    description: str
    original: Any
    value: Any
    history: list[str] = field(default_factory=list)


class Level(BaseModel):
    level: int
    sub_level: int | None


def parse_level(v: str) -> Level:
    if not v.replace(".", "", 1).isdigit():
        raise ValueError(f"Invalid level format: {v}")

    level, _, sub_level = v.partition(".")

    return Level(level=int(level), sub_level=int(sub_level) or None)


# ===================== Abstract Implementations =====================


class Correction(ABC):
    name: str
    level: Annotated[Level, BeforeValidator(parse_level)]
    description: str

    @abstractmethod
    def correct(self, state: State) -> State: ...

    def __call__(self, state: State) -> State:
        state.history.append(f"correction.{self.name}.start")
        try:
            state = self.correct(state)
        except Exception:
            state.history.append(f"correction.{self.name}.error")
            raise
        state.history.append(f"correction.{self.name}.end")
        return state


class Stage(ABC):
    name: str
    level: Annotated[Level, BeforeValidator(parse_level)]
    description: str

    def __init__(self, *corrections: Correction):
        self.corrections = list(corrections)

    def __call__(self, state: State) -> State:
        """Run the stage (parse + corrections) as a callable."""
        state = self.parse(state)
        for correction in self.corrections:
            state = correction(state)
        return state

    @abstractmethod
    def parse(self, state: State) -> State: ...


class Orchestrator(ABC):
    name: str
    location: str
    description: str

    NULL_STRINGS = {"none", "null", "", "None", "N/A", "n/a"}
    state_cls = State

    def __init__(self, *stages: "Stage"):
        self.stages = list(stages)

    def __call__(self, value: Any):
        state: State = self.state_cls(
            attribute=self.name,
            location=self.location,
            description=self.description,
            value=value,
            original=value,
            history=[],
        )

        try:
            if self.is_none_like(value):
                state.value = None
                state.history.append("orchestrator.none_like")
                state.history.append("orchestrator.end")
                return self.to_model(state)

            state = self.run(state)
            state.history.append("orchestrator.end")
            return self.to_model(state)

        except Exception as e:
            context = {
                "attribute": self.name,
                "location": self.location,
                "original": state.original,
                "current": state.value,
                "history": state.history,
                "error_type": type(e).__name__,
                "error": str(e),
            }
            raise PydanticCustomError(
                "orchestrator_error",
                "Orchestrator error in {attribute}: {error_type}",
                context,
            ) from e

    def run(self, state: State) -> State:
        for stage in self.stages:
            stage_name = getattr(stage, "name", stage.__class__.__name__)
            state.history.append(f"stage.{stage_name}.start")
            try:
                out = stage(state)

                if out is None:
                    raise TypeError(f"{stage_name} returned None; expected State")

                state = out
                state.history.append(f"stage.{stage_name}.end")
            except Exception:
                state.history.append(f"stage.{stage_name}.error")
                raise
        return state

    @abstractmethod
    def to_model(self, state: State): ...

    def is_none_like(self, value: Any) -> bool:
        return value is None or (
            isinstance(value, str) and value.strip().lower() in self.NULL_STRINGS
        )


# ===================== Utility Classes =====================


class TrimCorrection(Correction):
    name = "Trim whitespace"
    description = "Trim leading/trailing whitespace on strings (str or list[str])."

    def correct(self, state: State) -> State:
        v = state.value

        if isinstance(v, str):
            state.value = v.strip()
            return state

        if isinstance(v, list):
            state.value = [x.strip() if isinstance(x, str) else x for x in v]
            return state

        return state


class AliasCorrection(Correction):
    name = "Correct naming with aliasing"
    description = "Map known aliases to canonical names."

    def __init__(self, *alias_maps: Mapping[str, str]):
        self.alias_map = {k: v for m in alias_maps for k, v in m.items()}

    def correct(self, state: State) -> State:
        m = self.alias_map

        def resolve(x: Any) -> Any:
            if isinstance(x, str):
                if x in m:
                    return m[x]
                state.history.append(f"correction.{self.name}.missing:{x}")
            return x

        v = state.value
        if isinstance(v, list):
            state.value = [resolve(x) for x in v]
        else:
            state.value = resolve(v)

        return state
