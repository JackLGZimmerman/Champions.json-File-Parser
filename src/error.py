from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    champion: str
    path: str
    message: str
    type: str
    context: dict[str, Any] | None = None


class Error:
    """
    Collects validation issues and (optionally) writes them to disk on exit.
    Can also raise on exit if any issues exist.
    """

    def __init__(self, log_file: Path, *, raise_on_exit: bool = True, max_preview: int = 30):
        self.log_file = log_file
        self.raise_on_exit = raise_on_exit
        self.max_preview = max_preview
        self._issues: list[ValidationIssue] = []

    def add(self, issue: ValidationIssue) -> None:
        self._issues.append(issue)

    @property
    def issues(self) -> list[ValidationIssue]:
        return self._issues

    def __enter__(self) -> Error:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc is not None:
            return False

        if not self._issues:
            return False

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(i) for i in self._issues]
        self.log_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        if self.raise_on_exit:
            champions = {i.champion for i in self._issues}
            examples = "\n".join(
                f"{i.champion}: {i.path} -> {i.message} ({i.type})"
                for i in self._issues[: self.max_preview]
            )
            raise RuntimeError(
                f"Schema validation failed for {len(champions)} champion(s). "
                f"Wrote details to {self.log_file}.\n\nFirst errors:\n{examples}"
            )

        return False
