from __future__ import annotations

from shared import data_segment_dir

ABILITY_ADVANCED_DATA_DIR = data_segment_dir("champion-ability-advanced")
ABILITY_ADVANCED_FILE_PATH = ABILITY_ADVANCED_DATA_DIR / "abilities.jsonl"
RAW_FIELD_COVERAGE_FILE_PATH = ABILITY_ADVANCED_DATA_DIR / "raw_field_coverage.json"
RAW_NESTED_PATHS_FILE_PATH = ABILITY_ADVANCED_DATA_DIR / "raw_nested_paths.jsonl"
