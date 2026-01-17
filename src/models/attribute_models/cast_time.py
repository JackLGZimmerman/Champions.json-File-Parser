import re
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict

from src.models.attribute_models.attribute_models_abstracts import (
    Correction,
    Orchestrator,
    Stage,
    State,
)


class CastTimeReferenceTarget(BaseModel):
    """Reference target for percent-based cast time values."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    owner: str


class CastTimeCoreRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["range"]
    upper: float
    lower: float


class CastTimeCoreFixed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["fixed"]
    value: float


class CastTimeCoreReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["reference"]
    reference: CastTimeReferenceTarget
    multiplier: float


class CastTimeCoreUnknown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["unknown"]
    raw: str


class CastTimeCoreError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["error"]
    raw: str
    error: str


CastTimeCoreValue = (
    CastTimeCoreRange
    | CastTimeCoreFixed
    | CastTimeCoreReference
    | CastTimeCoreUnknown
    | CastTimeCoreError
)


class CastTimeContextScalesWith(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["scales_with"]
    attribute: str


class CastTimeContextBaseline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["baseline"]
    value: float
    attribute: str


class CastTimeContextUnknown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["unknown"]
    raw: str


class CastTimeContextError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["error"]
    raw: str
    error: str


CastTimeContextValue = (
    CastTimeContextScalesWith
    | CastTimeContextBaseline
    | CastTimeContextUnknown
    | CastTimeContextError
)


class CastTimeItem(BaseModel):
    """Structured cast time option derived from a single raw token."""

    model_config = ConfigDict(extra="forbid")

    value: CastTimeCoreValue | None = None
    context: CastTimeContextValue | None = None


class CastTimeModel(BaseModel):
    """Normalized castTime values and their parsed structure."""

    model_config = ConfigDict(extra="forbid")

    values: list[CastTimeItem] | None = None


class CastTimeOrchestrator(Orchestrator):
    name = "Cast time orchestrator"
    location = "root[abilities][*][0]"
    description = (
        "This will parse the values found in the castTime key of the abilities list "
        "inside the champion.json file"
    )

    state_cls = State

    def to_model(self, state: State) -> CastTimeModel:
        return CastTimeModel(values=state.value)


class CastTimeExtractOptionsStage(Stage):
    """Split raw castTime string into option tokens.

    Example:
        in: "0.5 : 0.19 (based on bonus attack speed) / None"
        out: ["0.5 : 0.19 (based on bonus attack speed) ", " None"]
    """

    name = "castTime.split_options"
    level = "1"
    description = "Split raw castTime string into top-level option tokens."

    def parse(self, state: State) -> State:
        value = state.value
        if not isinstance(value, str):
            state.history.append(f"{self.name}:NotString:{value}")
            raise TypeError(
                f"{self.name} expected str, got {type(value).__name__}: {value}"
            )

        state.value = value.split("/")
        state.history.append(f"{self.name}:options:{len(state.value)}")
        return state


class TrimCorrection(Correction):
    """Trim leading and trailing whitespace in each option.

    Example:
        in: ["0.5 : 0.19 (based on bonus attack speed) ", " None"]
        out: ["0.5 : 0.19 (based on bonus attack speed)", "None"]
    """

    name = "castTime.trim_options"
    level = "1.1"
    description = "Trim leading and trailing spaces in option tokens."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        state.value = [
            item.strip() if isinstance(item, str) else item for item in value
        ]

        return state


class NormaliseWhitespaceCorrection(Correction):
    """Collapse repeated spaces inside each option.

    Example:
        in: ["0.5  : 0.19 (based  on bonus attack speed)"]
        out: ["0.5 : 0.19 (based on bonus attack speed)"]
    """

    name = "castTime.normalize_whitespace"
    level = "1.3"
    description = "Collapse repeated spaces inside each option."

    def correct(self, state: State) -> State:
        value: list[Any] = state.value

        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", s).strip()

        state.value = [norm(x) if isinstance(x, str) else x for x in value]

        return state


class NoneTypeCorrection(Correction):
    """Convert none-like option tokens to None.

    Example:
        in: ["0.5 : 0.19 (based on bonus attack speed)", "None"]
        out: ["0.5 : 0.19 (based on bonus attack speed)", None]
    """

    name = "castTime.none_tokens"
    level = "1.2"
    description = "Convert none-like option strings to None."

    NONE_TOKENS = {"none", "false", "null", ""}

    def correct(self, state: State) -> State:
        value: Any = state.value

        def to_none(x: Any):
            if x is None:
                return None
            if isinstance(x, str) and x.strip().lower() in self.NONE_TOKENS:
                return None
            return x

        state.value = [to_none(item) for item in value]

        return state


class CastTimeCoreAndContextStage(Stage):
    """Split each option into a core value and a context string.

    Example:
        in: ["0.5 : 0.19 (based on bonus attack speed)", None]
        out: [
            {"core": "0.5 : 0.19", "context": "(based on bonus attack speed)"},
            {"core": None, "context": None},
        ]
    """

    name = "castTime.split_core_context"
    level = "2"
    description = "Split each option into core text and parenthesized context."

    def parse(self, state: State) -> State:
        value: list[Any] = state.value
        out: list[dict[str, Any]] = []

        for item in value:
            if item is None:
                out.append({"core": None, "context": None})
                continue
            if not isinstance(item, str):
                state.history.append(f"{self.name}:NotString:{item}")
                out.append({"core": None, "context": None})
                continue

            context_match = re.search(r"\(.*\)", item)
            context = context_match.group(0) if context_match else None
            core = re.sub(r"\s*\(.*?\)", "", item).strip() or None
            out.append({"core": core, "context": context})

        state.value = out
        state.history.append(f"{self.name}:items:{len(out)}")
        return state


class CastTimeParseCoreStage(Stage):
    """Parse core strings into structured value dictionaries.

    Example:
        in: [{"core": "0.5 : 0.19", "context": "(based on bonus attack speed)"}]
        out: [
            {
                "context": "(based on bonus attack speed)",
                "value": {"kind": "range", "upper": 0.5, "lower": 0.19},
            }
        ]
    """

    name = "castTime.parse_core"
    level = "3"
    description = "Parse core strings into structured cast time values."

    @staticmethod
    def is_range(item: str) -> bool:
        return ":" in item

    @staticmethod
    def is_number(item: str) -> bool:
        try:
            float(item)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_explicit_reference(item: str) -> bool:
        return "%" in item

    @staticmethod
    def is_implicit_reference(item: str) -> bool:
        return "%" not in item and not item.isdigit() and ":" not in item

    def parse_range(self, item: str) -> dict[str, Any]:
        start, end = item.split(":", 1)
        return {"kind": "range", "upper": float(start), "lower": float(end)}

    def parse_number(self, item: str) -> dict[str, Any]:
        return {"kind": "fixed", "value": float(item)}

    def parse_explicit_reference(self, item: str) -> dict[str, Any]:
        """Example: 140% of Viego's windup time"""
        match = re.match(
            r"(\d{1,3})%\sof\s(.+?)'s\s(.+)",
            item,
            re.IGNORECASE,
        )

        multiplier = float(match.group(1))
        owner = match.group(2)
        kind = match.group(3)

        return {
            "kind": "reference",
            "reference": {
                "kind": kind,
                "owner": owner,
            },
            "multiplier": multiplier,
        }

    def parse_implicit_reference(self, item: str) -> dict[str, Any]:
        """Examples: Attack Windup Time and Basic Attack Timer"""

        return {
            "kind": "reference",
            "reference": {
                "kind": item.lower(),
                "owner": "$owner",
            },
            "multiplier": 100,
        }

    def parse_unknown(self, item: str) -> dict[str, Any]:
        return {"kind": "unknown", "raw": item}

    def _dispatch(
        self,
    ) -> list[tuple[Callable[[str], bool], Callable[[str], dict[str, Any]]]]:
        return [
            (self.is_range, self.parse_range),
            (self.is_number, self.parse_number),
            (self.is_explicit_reference, self.parse_explicit_reference),
            (self.is_implicit_reference, self.parse_implicit_reference),
        ]

    def parse(self, state: State) -> State:
        items: list[dict[str, Any]] = state.value

        dispatch = self._dispatch()
        out: list[dict[str, Any]] = []

        for item in items:
            core = item.get("core")
            context = item.get("context")
            if not isinstance(core, str) or not core:
                out.append({"value": None, "context": context})
                continue

            for predicate, handler in dispatch:
                if predicate(core):
                    try:
                        parsed_core = handler(core)
                    except Exception as exc:
                        parsed_core = {
                            "kind": "error",
                            "raw": core,
                            "error": str(exc),
                        }
                    out.append(
                        {
                            "value": parsed_core,
                            "context": context,
                        }
                    )
                    break
            else:
                out.append({"value": self.parse_unknown(core), "context": context})

        state.value = out
        state.history.append(f"{self.name}:ParseCore:{out}")
        return state


class CastTimeParseContextStage(Stage):
    """Parse context strings into structured value dictionaries.

    Example:
        in: [
            {
                "context": "(based on bonus attack speed)",
                "value": {"kind": "range", "upper": 0.5, "lower": 0.19},
            }
        ]
        out: [
            {
                "context": {"kind": "scales_with", "attribute": "bonus attack speed"},
                "value": {"kind": "range", "upper": 0.5, "lower": 0.19},
            }
        ]
    """

    name = "castTime.parse_context"
    level = "4"
    description = "Parse context strings into structured cast time meaning."

    @staticmethod
    def is_scales_with(context: str) -> bool:
        return "based on" in context

    @staticmethod
    def is_baseline(context: str) -> bool:
        return " at " in context

    def parse_scales_with(self, context: str) -> dict[str, Any]:
        attribute = context.replace("based on", "").strip()
        return {
            "kind": "scales_with",
            "attribute": attribute,
        }

    def parse_baseline(self, context: str) -> dict[str, Any]:
        value, attribute = context.split(" at ", 1)
        return {
            "kind": "baseline",
            "value": float(value),
            "attribute": attribute.strip(),
        }

    def parse_unknown(self, context: str) -> dict[str, Any]:
        return {
            "kind": "unknown",
            "raw": context,
        }

    def _dispatch(
        self,
    ) -> list[tuple[Callable[[str], bool], Callable[[str], dict[str, Any]]]]:
        return [
            (self.is_scales_with, self.parse_scales_with),
            (self.is_baseline, self.parse_baseline),
        ]

    def parse(self, state: State) -> State:
        items: list[dict[str, Any]] = state.value
        dispatch = self._dispatch()
        out: list[dict[str, Any]] = []

        for item in items:
            value = item.get("value")
            context_raw = item.get("context")

            if not context_raw:
                out.append({"value": value, "context": None})
                continue

            if not isinstance(context_raw, str):
                out.append({"value": value, "context": context_raw})
                continue

            context = context_raw.strip()
            if context.startswith("(") and context.endswith(")"):
                context = context[1:-1]
            context = context.strip().lower()

            for predicate, handler in dispatch:
                if predicate(context):
                    try:
                        parsed_context = handler(context)
                    except Exception as exc:
                        parsed_context = {
                            "kind": "error",
                            "raw": context,
                            "error": str(exc),
                        }
                    break
            else:
                parsed_context = self.parse_unknown(context)

            out.append({"value": value, "context": parsed_context})

        state.value = out
        state.history.append(f"{self.name}:ParseContext:{out}")
        return state
