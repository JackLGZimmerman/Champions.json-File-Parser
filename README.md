# Collection CLI

Run collection through the primary CLI wrapper:

```bash
python scripts/collect.py <segment>
python scripts/collect.py all
```

With no segment, the CLI defaults to `champions`.

Generated outputs under `data/` and examples under `examples/` are intentionally ignored and can be recreated by the collectors. Source inputs that are required for regeneration live outside `data/`, such as `inputs/item_value_map/championid_position_item_counts.csv`.

## Collection Segments

| Segment | Purpose | Relevant files | Main output |
| --- | --- | --- | --- |
| `champions` | Fetch or load champion data, validate it, normalize it, and optionally refresh the raw cache. | `scripts/collect.py`, `src/collect.py`, `src/champions/collect.py`, `src/champions/normalize.py`, `src/champions/validate.py`, `src/champions/models/champion_models.py` | `data/champions/raw.json`, `data/champions/validated.json` |
| `items` | Fetch the current CommunityDragon item payload. | `scripts/collect.py`, `src/collect.py`, `src/items/collect.py`, `src/shared.py` | `data/items/items.jsonl` |
| `item-images` | Extract item id, name, price, and image URL records from collected item data. | `scripts/collect.py`, `src/collect.py`, `src/item_images/collect.py`, `src/item_value_map/collect.py`, `src/items/relationships.py` | `data/items/item_info.jsonl` |
| `champion-static-basic` | Flatten validated champion stats into basic static rows. | `scripts/collect.py`, `src/collect.py`, `src/champion_static_basic/collect.py`, `src/champions/collect.py` | `data/champion-static-basic/basic_stats.jsonl` |
| `champion-ability-advanced` | Refresh formatted CommunityDragon ability data and extract advanced ability fields. | `scripts/collect.py`, `src/collect.py`, `src/champion_ability_advanced/collect.py`, `src/champions/communitydragon.py` | `data/champion-ability-advanced/abilities.jsonl`, `data/champions/communitydragon_abilities_formatted.json` |
| `champion-ability-ratios` | Extract ability ratio feature columns from formatted CommunityDragon ability data. | `scripts/collect.py`, `src/collect.py`, `src/champion_ability_ratios/collect.py`, `src/champion_ability_ratios/generate_final_features.py`, `src/champion_ability_ratios/scaling_detection.py`, `src/champion_ability_ratios/paths.py` | `data/champion-ability-advanced/ability_ratio_features.jsonl` |
| `champ-id-name-map` | Fetch CommunityDragon champion index rows and save champion id, name, and alias mappings. | `scripts/collect.py`, `src/collect.py`, `src/champ_id_name_map/collect.py`, `src/champions/communitydragon.py` | `data/champions/champ_id_name_map.jsonl` |
| `item-value-map` | Build the scoped item value map from item baselines and champion-position item counts. | `scripts/collect.py`, `src/collect.py`, `src/item_value_map/collect.py`, `src/item_value_map/scoring.py`, `src/item_value_map/item_group_definitions.py`, `inputs/item_value_map/championid_position_item_counts.csv` | `data/items/item_value_map.jsonl` |
| `all` | Run every configured collection segment in order. | `scripts/collect.py`, `src/collect.py`, all collector modules above | All outputs above |

## Executable Files

| File | Purpose |
| --- | --- |
| `scripts/collect.py` | Compatibility wrapper that adds `src/` to `sys.path` and runs `src/collect.py`. |
| `src/collect.py` | Root argparse orchestrator. Registers segment subcommands and runs individual collectors or `all`. |
| `src/item_value_map/scoring.py` | Source-controlled item-value scorer that regenerates `data/items/item_value_map.jsonl` from collected item data and `inputs/item_value_map/championid_position_item_counts.csv`. |

## Shared Support

- `src/shared.py` contains common JSON, JSONL, filesystem, and HTTP helpers.
- `pyproject.toml` defines the package metadata and runtime dependencies.
