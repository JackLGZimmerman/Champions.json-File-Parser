import re

from pydantic import BaseModel, ConfigDict, Field

from src.aliases.modifers import MODIFIERS_TOKEN_ALIASES
from src.models.attribute_models.attribute_models_abstracts import (
    Correction,
    Orchestrator,
    Stage,
    State,
)

MODIFER_ATTRIBUTE_LIST = [
    "% AD",
    "% AP",
    "% armor",
    "% bonus AD",
    "% bonus armor",
    "% bonus health",
    "% bonus magic resistance",
    "% bonus mana",
    "% bonus movement speed",
    "% life steal",
    "% maximum health",
    "% maximum mana",
    "% missing health",
    "% missing mana",
    "% total armor",
    "% total magic resistance",
    "% per 1% missing health",
    "% per 1% of health lost in the past 4 seconds",
    "% per 100 AD",
    "% per 100 AP",
    "% per 100 bonus AD",
    "% per 100 bonus armor",
    "% per 100 bonus health",
    "% per 100 bonus magic resistance",
    "% per 100 of Sona's AP",
    "% per 100 Pantheon's bonus health",
    "% per 100% bonus attack speed",
    "% per 4% critical strike chance",
    "% per Feast stack",
    "% per Mark",
    "% per Mist collected",
    "% per Overwhelm stack on the target",
    "% per Soul collected",
    "% of Braum's maximum health",
    "% of Ivern's AP",
    "% of Siphoning Strike stacks",
    "% of Sona's AP",
    "% of Taric's armor",
    "% of Zac's maximum health",
    "% of damage dealt",
    "% of damage stored",
    "% of her maximum health",
    "% of his bonus health",
    "% of his maximum health",
    "% of his missing health",
    "% of missing health",
    "% of missing mana",
    "% of primary target's bonus health",
    "% of target's armor",
    "% of target's current health",
    "% of target's maximum health",
    "% of target's missing health",
    "% of turret's maximum health",
    "% of maximum health",
    "AD",
    "AP",
    "AP per 100 bonus health",
    "armor",
    "bonus AD",
    "bonus armor",
    "bonus health",
    "bonus magic resistance",
    "bonus mana",
    "bonus movement speed",
    "Braum's maximum health",
    "chunks of ice",
    "critical strike chance",
    "damage dealt",
    "damage stored",
    "expended Grit",
    "her maximum health",
    "his bonus health",
    "his maximum health",
    "his missing health",
    "Ivern's AP",
    "level",
    "life steal",
    "mana",
    "maximum health",
    "maximum mana",
    "missing health",
    "missing mana",
    "Moonlight",
    "original damage",
    "per 1% missing health",
    "per 1% of health lost in the past 4 seconds",
    "per 100 AD",
    "per 100 AP",
    "per 100 bonus AD",
    "per 100 bonus armor",
    "per 100 bonus health",
    "per 100 bonus magic resistance",
    "per 100 of Sona's AP",
    "per 100 Pantheon's bonus health",
    "per 100% bonus attack speed",
    "per 4% critical strike chance",
    "per Feast stack",
    "per Mark",
    "per Mist collected",
    "per Overwhelm stack on the target",
    "per Soul collected",
    "primary target's bonus health",
    "seconds",
    "Siphoning Strike stacks",
    "soldiers",
    "Sona's AP",
    "Stacks",
    "Style",
    "target's armor",
    "target's current health",
    "target's maximum health",
    "target's missing health",
    "Taric's armor",
    "total armor",
    "total magic resistance",
    "turret's maximum health",
    "units",
    "Zac's maximum health",
]


class ModifierBlock(BaseModel):
    """Shared shape for `base` and each entry in `enhancements`."""

    model_config = ConfigDict(extra="forbid")

    values: list[float]
    base_unit: str | None = None
    enhancement_stats: list[str] = Field(default_factory=list)


class ModifiersModel(BaseModel):
    """Final model == state.value (unchanged structure)."""

    model_config = ConfigDict(extra="forbid")

    attributes: list[str] = Field(default_factory=list)
    sub_attributes: list[str] = Field(default_factory=list)
    base: ModifierBlock
    enhancements: list[ModifierBlock] = Field(default_factory=list)


class ModifiersOrchestrator(Orchestrator):
    name = "Modifier orchestrator"
    location = "root[abilities][*][affects][leveling][modifiers]"
    description = (
        "This will parse the values found in the effects key of the abilities list "
        "inside the champion.json file"
    )

    state_cls = State

    def to_model(self, state: State) -> ModifiersModel:
        return ModifiersModel.model_validate(state.value)


class ModifierNormalizeUnitsStage(Stage):
    name = "modifier.reduce_units"
    level = "1"
    description = "Normalize unit fields into a single base_unit string."

    def parse(self, state: State):
        value: list[dict] = state.value

        for modifier in value:
            unit = modifier.get("unit")
            units = modifier.get("units", [])
            base_unit = modifier.get("base_unit")
            if base_unit is None:
                if unit is not None:
                    modifier["base_unit"] = unit
                elif isinstance(units, list) and units:
                    modifier["base_unit"] = units[0]
                elif isinstance(units, str):
                    modifier["base_unit"] = units
                else:
                    modifier["base_unit"] = None

            if "units" in modifier:
                del modifier["units"]
            if "unit" in modifier:
                del modifier["unit"]
            modifier.setdefault("enhancement_stats", [])

        state.history.append(f"{self.name}.items:{len(value)}")
        return state


class EmptyUnitCorrection(Correction):
    name = "effects.normalize_empty_units"
    level = "1.1"
    description = "Replace empty unit strings with None."

    def correct(self, state: State) -> State:
        modifiers: list[dict] = state.value
        EMPTY_UNIT = {"", " ", "  "}
        replaced = 0

        for modifier in modifiers:
            unit = modifier.get("base_unit")

            if unit is None:
                continue

            if unit in EMPTY_UNIT:
                replaced += 1
                modifier["base_unit"] = None

        if replaced:
            state.history.append(f"{self.name}.replaced:{replaced}")

        return state


class TrimUnitCorrection(Correction):
    name = "effects.trim_unit_spaces"
    level = "1.2"
    description = "Trim leading and trailing spaces in base_unit."

    def correct(self, state: State) -> State:
        modifiers: list[dict] = state.value
        trimmed = 0

        for modifier in modifiers:
            unit = modifier.get("base_unit")
            if unit is None:
                continue
            stripped = unit.strip()
            if stripped != unit:
                trimmed += 1
            modifier["base_unit"] = stripped

        if trimmed:
            state.history.append(f"{self.name}.trimmed:{trimmed}")

        return state


class ModifierSplitBaseEnhancementsStage(Stage):
    name = "modifier.split_base_and_enhancements"
    level = "2"
    description = "Split modifiers into base (first) and enhancement (rest)."

    def parse(self, state: State):
        modifiers: list[dict] = state.value

        if not modifiers:
            result = {"base": None, "enhancements": []}
        else:
            result = {"base": modifiers[0], "enhancements": modifiers[1:]}

        base_state = "present" if result["base"] else "none"
        state.history.append(f"{self.name}.base:{base_state}")
        state.history.append(f"{self.name}.enhancements:{len(result['enhancements'])}")
        state.value = result
        return state


class ModifierExtractBracketStatsStage(Stage):
    name = "modifier.parse_units"
    level = "3"
    description = "Extract bracket content into enhancement_stats and clean base_unit."

    def parse(self, state: State):
        modifiers: dict = state.value
        enhancements: list = modifiers.get("enhancements", [])

        for enhancement in enhancements:
            if enhancement.get("enhancement_stats") is None:
                enhancement["enhancement_stats"] = []

            base_unit = enhancement.get("base_unit", "")
            if base_unit is None:
                enhancement["base_unit"] = None
                enhancement["enhancement_stats"] = []
                continue
            if not isinstance(base_unit, str):
                base_unit = str(base_unit)

            bracket_content = re.findall(r"\((.*?)\)", base_unit)

            base_unit = re.sub(r"\(.*?\)", "", base_unit)
            base_unit = " ".join(base_unit.split())

            enhancement["base_unit"] = base_unit
            enhancement.setdefault("enhancement_stats", []).extend(bracket_content)

        state.history.append(f"{self.name}.enhancements:{len(enhancements)}")
        return state


class ModifierCollectAttributesStage(Stage):
    name = "modifier.collect_attributes"
    level = "4"
    description = "Collect attribute tokens and smaller sub-terms from unit text."

    def parse(self, state: State):
        modifiers: dict = state.value
        parts: list[str] = []

        def collect_units(modifier: dict) -> None:
            base_unit = modifier["base_unit"]
            if base_unit is not None:
                parts.append(base_unit)
            parts.extend(modifier["enhancement_stats"])

        base = modifiers.get("base")
        if base:
            collect_units(base)

        enhancements = modifiers.get("enhancements", [])
        for enhancement in enhancements:
            collect_units(enhancement)

        combined = " ".join(parts).strip()
        if not combined:
            modifiers["attributes"] = []
            modifiers["sub_attributes"] = []
            return state

        combined = " ".join(combined.split())
        matched: list[str] = []
        for token in MODIFER_ATTRIBUTE_LIST:
            if token in combined:
                matched.append(token)

        attributes: list[str] = []
        sub_attributes: list[str] = []
        seen = set()
        sub_seen = set()
        for token in matched:
            is_subterm = any(token != other and token in other for other in matched)
            canonical = MODIFIERS_TOKEN_ALIASES.get(token, token)
            if is_subterm:
                if canonical not in sub_seen:
                    sub_seen.add(canonical)
                    sub_attributes.append(canonical)
            else:
                if canonical not in seen:
                    seen.add(canonical)
                    attributes.append(canonical)

        modifiers["attributes"] = attributes
        modifiers["sub_attributes"] = sub_attributes
        if attributes:
            state.history.append(f"{self.name}.attributes:{len(attributes)}")
        if sub_attributes:
            state.history.append(f"{self.name}.sub_attributes:{len(sub_attributes)}")
        return state
