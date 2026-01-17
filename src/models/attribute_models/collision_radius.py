from typing import Any

from pydantic import BaseModel, ConfigDict

from src.models.attribute_models.attribute_models_abstracts import (
    Correction,
    Orchestrator,
    Stage,
    State,
)


class CollisionRadiusModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CollisionRadiusOrchestrator(Orchestrator):
    name = "Collision radius orchestrator"
    location = "root[abilities][*][0]"
    description = (
        "Parse collisionRadius values from the abilities list in champion.json."
    )

    def to_model(self, state: State) -> list[float | None]:
        if state.value is None:
            return []
        return state.value


class CollisionRadiusExtractOptionsStage(Stage):
    name = "collisionRadius.split_options"
    level = "1"
    description = "Split raw collisionRadius string into top-level option tokens."

    def parse(self, state: State) -> State:
        value: Any = state.value

        state.value = value.split("/")

        return state


class CollisionRadiusTrimCorrection(Correction):
    name = "collisionRadius.trim_options"
    level = "1.1"
    description = "Trim leading and trailing spaces in option tokens."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [item.strip() if item is not None else None for item in value]

        return state


class CollisionRadiusStrToFloatCorrection(Correction):
    name = "collisionRadius.to_float"
    level = "1.2"
    description = "Convert option tokens to floats where possible."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [float(item) if item is not None else None for item in value]

        return state
