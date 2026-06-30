# Collection CLI

Run collection through the single collection CLI:

```bash
uv run collect <segment>
uv run collect all
```

The direct script wrapper is still available for compatibility:

```bash
python scripts/collect.py <segment>
python scripts/collect.py all
```

With no segment, both entry points default to `champions`.

Generated outputs under `data/` and examples under `examples/` are intentionally ignored and can be recreated by the collectors. Source inputs that are required for regeneration live outside `data/`, such as `inputs/item_value_map/championid_position_item_counts.csv`.

## Collection Segments

| Segment | Purpose | Relevant files | Main output |
| --- | --- | --- | --- |
| `champions` | Fetch or load champion data, validate it, normalize it, and optionally refresh the raw cache. | `scripts/collect.py`, `src/collect.py`, `src/champions/collect.py`, `src/champions/normalize.py`, `src/champions/validate.py`, `src/champions/models/champion_models.py` | `data/champions/raw.json`, `data/champions/validated.json` |
| `items` | Fetch the current CommunityDragon item payload. | `scripts/collect.py`, `src/collect.py`, `src/items/collect.py`, `src/shared.py` | `data/items/items.jsonl` |
| `item-images` | Extract item id, name, price, and image URL records from collected item data. | `scripts/collect.py`, `src/collect.py`, `src/items/info.py`, `src/items/value_map/scoring.py`, `src/items/relationships.py` | `data/items/item_info.jsonl` |
| `champion-static-basic` | Flatten validated champion stats into basic static rows. | `scripts/collect.py`, `src/collect.py`, `src/champion_static_basic/collect.py`, `src/champions/collect.py` | `data/champion-static-basic/basic_stats.jsonl` |
| `champion-ability-advanced` | Refresh formatted CommunityDragon ability data and extract one rich JSONL row per champion ability, including complex source fields and raw-field diagnostics. | `scripts/collect.py`, `src/collect.py`, `src/champion_ability_advanced/collect.py`, `src/champion_ability_advanced/extract.py`, `src/champion_ability_advanced/detailed_features.py`, `src/champion_ability_advanced/paths.py`, `src/champions/communitydragon.py` | `data/champion-ability-advanced/abilities.jsonl`, `data/champion-ability-advanced/raw_field_coverage.json`, `data/champion-ability-advanced/raw_nested_paths.jsonl`, `data/champions/communitydragon_abilities_formatted.json` |
| `champion-ability-attributes` | Extract ability-level scaling rows and the model-ready detailed per-champion ability feature view derived from `abilities.jsonl`. | `scripts/collect.py`, `src/collect.py`, `src/champion_ability_attributes/collect.py`, `src/champion_ability_attributes/generate_final_features.py`, `src/champion_ability_attributes/scaling_detection.py`, `src/champion_ability_attributes/paths.py`, `src/champion_ability_advanced/detailed_features.py` | `data/champion-ability-advanced/ability_attribute_features.jsonl`, `data/champion-ability-advanced/champion_ability_detailed_features.jsonl` |
| `champ-id-name-map` | Fetch CommunityDragon champion index rows and save champion id, name, and alias mappings. Also refreshed by `champion-ability-advanced`. | `scripts/collect.py`, `src/collect.py`, `src/champ_id_name_map/collect.py`, `src/champions/communitydragon.py` | `data/champions/champ_id_name_map.jsonl` |
| `item-value-map` | Build the scoped item value map from item baselines and champion-position item counts. | `scripts/collect.py`, `src/collect.py`, `src/items/value_map/collect.py`, `src/items/value_map/scoring.py`, `src/items/value_map/item_group_definitions.py`, `inputs/item_value_map/championid_position_item_counts.csv` | `data/items/item_value_map.jsonl` |
| `all` | Run the default collection flow in order; skips the standalone id-map command because `champion-ability-advanced` writes that output from the same CommunityDragon index fetch. | `scripts/collect.py`, `src/collect.py`, all default collector modules above | All outputs above |

`champion_ability_detailed_features.jsonl` is a fixed-schema, per-champion model view with P/Q/W/E/R-prefixed ability fields. It flattens scalar ability fields, summarizes cooldown/cost/range arrays, one-hot encodes categorical ability fields, includes per-slot binary trait flags from `ability_attribute_features.jsonl`, and omits source text fields such as descriptions, names, and record paths.

## Executable Files

| File | Purpose |
| --- | --- |
| `collect` | Installed console entry point for the collection CLI. |
| `scripts/collect.py` | Compatibility wrapper that adds `src/` to `sys.path` and runs `src/collect.py`. |
| `src/collect.py` | Root argparse orchestrator. Registers segment subcommands and runs individual collectors or `all`. |
| `src/items/value_map/scoring.py` | Source-controlled item-value scorer that regenerates `data/items/item_value_map.jsonl` from collected item data and `inputs/item_value_map/championid_position_item_counts.csv`. |

## Shared Support

- `src/shared.py` contains common JSON, JSONL, filesystem, and HTTP helpers.
- `pyproject.toml` defines the package metadata and runtime dependencies.

## Champion Simulator API

The deterministic simulator lives in `src/simulator/` and is exposed through
`simulate_actions`.

```python
from simulator import SimulationRequest, simulate_actions

request = SimulationRequest(
    attacker="Aatrox",
    target="Ahri",
    actions=(
        "Aatrox Q - Activation 1, "
        "Aatrox Q - Activation 2, "
        "Aatrox Q - Activation 3, "
        "Aatrox E"
    ),
)

result = simulate_actions(request)
print(result.total_damage)
```

V1 supports deterministic champion base stats, action parsing, direct ability
damage, physical/magic/true mitigation, Aatrox Q activation handling, and
explicit warnings or errors for unsupported formulas. Items, runes, buffs,
cooldowns, resources, crits, DOT timing, shields, healing, and complex champion
state are intentionally out of scope for this first simulator layer.
