from __future__ import annotations

import re
from dataclasses import dataclass

from simulator.errors import ActionParseError
from simulator.models import ActionInput

ABILITY_ACTION_PATTERN = re.compile(
    r"^(?P<champion>.+?)\s+(?P<ability>[PQWER])(?:\s*-\s*(?P<qualifier>.+))?$",
    re.IGNORECASE,
)
ACTIVATION_PATTERN = re.compile(r"\bactivation\s+(?P<number>\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedAction:
    raw: str
    champion_text: str
    ability_key: str
    qualifier: str | None

    @property
    def activation_index(self) -> int | None:
        if self.qualifier is None:
            return None
        match = ACTIVATION_PATTERN.search(self.qualifier)
        if match is None:
            return None
        return int(match.group("number"))

    @property
    def is_sweet_spot(self) -> bool:
        if self.qualifier is None:
            return False
        qualifier = self.qualifier.lower()
        return "edge" in qualifier or "sweet" in qualifier


def split_actions(actions: ActionInput) -> list[str]:
    if isinstance(actions, str):
        return [action.strip() for action in actions.split(",") if action.strip()]
    return [str(action).strip() for action in actions if str(action).strip()]


def parse_action(action: str) -> ParsedAction:
    match = ABILITY_ACTION_PATTERN.match(action.strip())
    if match is None:
        raise ActionParseError(
            "Action must look like '<Champion> <P/Q/W/E/R>' with an optional "
            f"qualifier after '-': {action!r}"
        )

    return ParsedAction(
        raw=action,
        champion_text=match.group("champion").strip(),
        ability_key=match.group("ability").upper(),
        qualifier=(match.group("qualifier") or "").strip() or None,
    )


def parse_actions(actions: ActionInput) -> list[ParsedAction]:
    return [parse_action(action) for action in split_actions(actions)]
