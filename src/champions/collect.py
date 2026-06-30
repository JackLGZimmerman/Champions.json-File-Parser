from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any, Literal

from shared import (
    data_segment_dir,
    fetch_json,
    load_json,
    write_json,
)

CHAMPION_DATA_DIR = data_segment_dir("champions")
CHAMPION_CACHE_PATH = CHAMPION_DATA_DIR / "raw.json"
CHAMPION_VALIDATED_PATH = CHAMPION_DATA_DIR / "validated.json"

RawChampionPayload = dict[str, object]
RawChampionMap = dict[str, RawChampionPayload]
SourceMode = Literal["auto", "cache", "remote"]


def fetch_champion_info_raw(timeout: int = 10) -> RawChampionMap:
    from champions.settings import get_settings

    settings = get_settings()
    data: Any = fetch_json(str(settings.champions_info_json), timeout=timeout)
    if not isinstance(data, dict):
        raise ValueError("Champion payload must be a JSON object keyed by champion name.")
    return data


def load_champion_info_raw(path: Path = CHAMPION_CACHE_PATH) -> RawChampionMap:
    if not path.exists():
        raise FileNotFoundError(f"Champion cache file not found: {path}")

    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("Cached champion payload must be a JSON object keyed by champion name.")
    return data


def write_champion_info_raw(
    data: RawChampionMap,
    path: Path = CHAMPION_CACHE_PATH,
) -> None:
    write_json(data, path)


def load_champion_info_validated(path: Path = CHAMPION_VALIDATED_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Validated champion file not found: {path}")

    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("Validated champion payload must be a JSON object keyed by champion name.")
    return data


def write_champion_info_validated(
    data: dict[str, Any],
    path: Path = CHAMPION_VALIDATED_PATH,
) -> None:
    write_json(data, path, sort_keys=True)


def _resolve_input_data(
    source: SourceMode,
    cache_path: Path,
    timeout: int,
) -> tuple[RawChampionMap, str]:
    if source == "cache":
        return load_champion_info_raw(cache_path), "cache"

    if source == "remote":
        return fetch_champion_info_raw(timeout=timeout), "remote"

    if cache_path.exists():
        return load_champion_info_raw(cache_path), "cache"

    return fetch_champion_info_raw(timeout=timeout), "remote"


def collect(
    source: SourceMode = "auto",
    cache_path: Path = CHAMPION_CACHE_PATH,
    output_path: Path = CHAMPION_VALIDATED_PATH,
    write_cache: bool = True,
    timeout: int = 10,
) -> None:
    from pydantic_core import to_jsonable_python

    from champions.normalize import normalize_champions
    from champions.validate import validate_champions

    data, source_used = _resolve_input_data(
        source=source,
        cache_path=cache_path,
        timeout=timeout,
    )
    print(f"Loaded champion data from {source_used}")

    if source_used == "remote" and write_cache:
        write_champion_info_raw(data, path=cache_path)
        print(f"Wrote raw champion cache to {cache_path}")

    validated_models = validate_champions(data)
    validated_payload = normalize_champions(validated_models)
    validated_jsonable = to_jsonable_python(validated_payload)

    write_champion_info_validated(validated_jsonable, path=output_path)
    print(f"Wrote validated champion payload to {output_path}")


def run_from_args(args: Namespace) -> None:
    collect(
        source=args.source,
        write_cache=not args.no_write_cache,
        timeout=args.timeout,
    )


def register_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "champions",
        help="Collect champion data into data/champions/",
    )
    parser.add_argument(
        "--source",
        choices=("auto", "cache", "remote"),
        default="auto",
        help="Choose whether to use cached champion data or fetch remotely.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--no-write-cache",
        action="store_true",
        help="Skip writing the raw champion cache file.",
    )
    parser.set_defaults(handler=run_from_args)
