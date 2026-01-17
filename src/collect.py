import json
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python

from src.load import fetch_champion_info_raw, load_champion_info_collected
from src.models.champion_models import ChampionInformation
from src.noise import exclude_fields

from .error import Error
from .validate import validate_champions

log_file = Path("logs/champion_validation_errors.json")
champion_file = Path("data/validated_champion.json")
example_file = Path("examples/champions.json")


def collect():
    data: Any
    if example_file.exists():
        data = load_champion_info_collected()
        print("Loaded data")

    else:
        data = fetch_champion_info_raw()
        print("Fetched data")

    with example_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with Error(log_file, raise_on_exit=True) as error:
        validated: dict[str, ChampionInformation] = validate_champions(
            data, error=error
        )

    validated: dict[str, dict[str, Any]] = exclude_fields(validated)
    validated_jsonable = to_jsonable_python(validated)

    champion_file.parent.mkdir(parents=True, exist_ok=True)

    with champion_file.open("w", encoding="utf-8") as f:
        json.dump(
            validated_jsonable,
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )


if __name__ == "__main__":
    collect()
