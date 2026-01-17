from typing import Any

from pydantic import BaseModel, ConfigDict

from src.models.attribute_models.attribute_models_abstracts import (
    Correction,
    Orchestrator,
    Stage,
    State,
)


class AngleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: list[float | None] | None = None


class AngleOrchestrator(Orchestrator):
    name = "Angle orchestrator"
    location = "root[abilities][*][0]"
    description = (
        "This will parse the values found in the angle key of the abilities list "
        "inside the champion.json file"
    )

    def to_model(self, state: State) -> list[float | None]:
        if state.value is None:
            return []
        return state.value


class AngleExtractOptionsStage(Stage):
    name = "angle.split_options"
    level = "1"
    description = "Split raw angle string into top-level option tokens."

    def parse(self, state: State) -> State:
        value: Any = state.value

        if isinstance(value, str):
            state.value = value.split("/")
        elif value is None:
            state.value = []
        else:
            state.history.append(f"{self.name}:NotString:{value}")
            raise TypeError(
                f"{self.name} expected str, got {type(value).__name__}: {value}"
            )

        return state


class TrimCorrection(Correction):
    name = "angle.trim_options"
    level = "1.1"
    description = "Trim leading and trailing spaces in option tokens."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [
            item.strip() if isinstance(item, str) else None for item in value
        ]

        return state


class AngleParseDegreesStage(Stage):
    name = "angle.strip_degree_suffix"
    level = "2"
    description = "Remove the trailing degree marker from each option."

    def parse(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [
            item.rstrip("¶ø°") if isinstance(item, str) else None for item in value
        ]

        return state


class AngleStrToFloatCorrection(Correction):
    name = "angle.to_float"
    level = "2.1"
    description = "Convert option tokens to floats where possible."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [
            float(item) if isinstance(item, str) and item else None for item in value
        ]

        return state
