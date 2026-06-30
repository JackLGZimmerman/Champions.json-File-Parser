from __future__ import annotations

from pathlib import Path
from typing import Any

from simulator.data import ChampionIdentity, SimulatorDataRepository
from simulator.errors import SimulatorError, UnsupportedFormulaError
from simulator.formulas import calculate_damage_event
from simulator.models import DamageEvent, SimulationRequest, SimulationResult, SimulationWarning
from simulator.parser import ParsedAction, parse_actions
from simulator.stats import validate_level


def simulate_actions(
    request: SimulationRequest,
    *,
    data_dir: str | Path = "data",
    strict: bool = True,
) -> SimulationResult:
    validate_level(request.attacker_level)
    validate_level(request.target_level)

    repository = SimulatorDataRepository(data_dir=data_dir)
    attacker = repository.resolve_champion(request.attacker)
    target = repository.resolve_champion(request.target)
    attacker_stats = repository.champion_stats(
        attacker,
        level=request.attacker_level,
        overrides=request.attacker_stat_overrides,
    )
    target_stats = repository.champion_stats(
        target,
        level=request.target_level,
        overrides=request.target_stat_overrides,
    )

    actions = parse_actions(request.actions)
    warnings: list[SimulationWarning] = []
    events: list[DamageEvent] = []
    target_health = target_stats.max_health

    for action in actions:
        try:
            action_champion = repository.resolve_champion(action.champion_text)
            ensure_action_owner(action, action_champion, attacker)
            warnings.extend(
                feature_warnings(
                    action,
                    repository.ability_features(attacker, action.ability_key),
                )
            )
            event = calculate_damage_event(
                action=action,
                attacker=attacker,
                attacker_stats=attacker_stats,
                target_stats=target_stats,
                ability_rank=ability_rank_for_action(request, action),
                formatted_ability=repository.formatted_ability(
                    attacker,
                    action.ability_key,
                ),
                advanced_ability=repository.advanced_ability(
                    attacker,
                    action.ability_key,
                ),
                target_health_before=target_health,
            )
        except SimulatorError as error:
            if strict:
                raise
            warnings.append(
                SimulationWarning(
                    code=error.__class__.__name__,
                    message=str(error),
                    action=action.raw,
                )
            )
            event = zero_damage_event(action, attacker, target_health, str(error))

        events.append(event)
        target_health = event.target_health_after

    return SimulationResult(
        attacker_id=attacker.champion_id,
        attacker_name=attacker.name,
        target_id=target.champion_id,
        target_name=target.name,
        events=tuple(events),
        warnings=tuple(warnings),
    )


def ensure_action_owner(
    action: ParsedAction,
    action_champion: ChampionIdentity,
    attacker: ChampionIdentity,
) -> None:
    if action_champion.champion_id != attacker.champion_id:
        raise UnsupportedFormulaError(
            f"Action {action.raw!r} belongs to {action_champion.name}, "
            f"but request attacker is {attacker.name}."
        )


def ability_rank_for_action(request: SimulationRequest, action: ParsedAction) -> int:
    rank = request.ability_ranks.get(action.ability_key, 1)
    return int(rank)


def feature_warnings(
    action: ParsedAction,
    features: dict[str, Any] | None,
) -> list[SimulationWarning]:
    if features is None or action.qualifier is not None:
        return []

    stage_count = features.get("stageCount")
    if not isinstance(stage_count, int) or stage_count <= 1:
        return []

    return [
        SimulationWarning(
            code="MultiStageAbility",
            message=(
                f"{action.raw!r} has {stage_count} detected stages; "
                "simulator V1 defaults to the first activation."
            ),
            action=action.raw,
        )
    ]


def zero_damage_event(
    action: ParsedAction,
    attacker: ChampionIdentity,
    target_health: float | None,
    note: str,
) -> DamageEvent:
    return DamageEvent(
        action=action.raw,
        champion_id=attacker.champion_id,
        champion_name=attacker.name,
        ability_key=action.ability_key,
        qualifier=action.qualifier,
        damage_type=None,
        raw_damage=0.0,
        mitigated_damage=0.0,
        target_health_before=target_health,
        target_health_after=target_health,
        notes=(note,),
    )
