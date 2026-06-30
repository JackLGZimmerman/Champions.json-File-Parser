from __future__ import annotations


class SimulatorError(Exception):
    """Base error for deterministic simulator failures."""


class DataNotFoundError(SimulatorError):
    """Required simulator source data could not be loaded."""


class UnknownChampionError(SimulatorError):
    """A champion name or alias could not be resolved."""


class ActionParseError(SimulatorError):
    """An action string cannot be parsed into champion, ability, and qualifier."""


class MissingStatError(SimulatorError):
    """A required champion stat is unavailable."""


class UnsupportedFormulaError(SimulatorError):
    """An ability formula is not supported by the deterministic V1 simulator."""
