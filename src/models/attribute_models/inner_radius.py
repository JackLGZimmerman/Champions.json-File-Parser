import re
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from src.models.attribute_models.attribute_models_abstracts import (
    Orchestrator,
    Stage,
    State,
)

ATTRIBUTE_TOKENS: dict[str, str] = {
    "Stardust": "Stardust",
}


InnerRadiusValue = float | dict[str, Any] | None


class InnerRadiusModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: list[InnerRadiusValue] | None = None


class InnerRadiusOrchestrator(Orchestrator):
    name = "Inner radius orchestrator"
    location = "root[abilities][*][0]"
    description = (
        "Parse innerRadius values from the abilities list in champion.json."
    )

    def to_model(self, state: State) -> InnerRadiusModel:
        if state.value is None:
            return InnerRadiusModel(values=None)
        return InnerRadiusModel(values=state.value)


class InnerRadiusExtractOptionsStage(Stage):
    name = "innerRadius.split_options"
    level = "1"
    description = "Split raw innerRadius string into top-level option tokens."

    def parse(self, state: State) -> State:
        value: Any = state.value

        state.value = value.split("/")

        return state


class InnerRadiusTransformValuesStage(Stage):
    name = "innerRadius.transform_values"
    level = "2"
    description = "Parse tokens into floats or formula dictionaries."

    def is_float(self, item: Any) -> bool:
        try:
            float(item)
            return True
        except Exception as _:
            return False

    def is_formula(self, item: Any) -> bool:
        return "√" in item or "²" in item

    def parse_formula(self, item) -> dict:
        raw = str(item)
        tokens = [t.strip() for t in re.findall(r"[A-Za-z][A-Za-z\s']*", raw)]
        attribute = None
        text_items: list[str] = []

        for token in tokens:
            canonical = ATTRIBUTE_TOKENS.get(token)
            if canonical:
                attribute = canonical
            else:
                text_items.append(token)

        return {
            "attribute": attribute,
            "text_items": text_items,
            "formula": raw,
        }

    def parse_float(self, item) -> float:
        return float(item)

    def _dispatch(self) -> tuple[Callable[[str], bool], Callable]:
        return (
            (self.is_formula, self.parse_formula),
            (self.is_float, self.parse_float),
        )

    def parse(self, state: State) -> State:
        value: Any = state.value
        out: list[Any] = []
        dispatch = self._dispatch()

        for item in value:
            if item is None:
                out.append(None)
                continue

            for predicate, handler in dispatch:
                if predicate(item):
                    out.append(handler(item))
                    break
            else:
                out.append(item)

        state.value = out

        return state
