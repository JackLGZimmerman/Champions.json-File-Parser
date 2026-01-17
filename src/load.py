import json
from pathlib import Path
from typing import Any

import requests

from src.settings import settings


def fetch_champion_info_raw() -> Any:
    response = requests.get(settings.champion_info_json, timeout=10)
    response.raise_for_status()
    return response.json()


def load_champion_info_collected() -> Any:
    path = Path("examples/champions.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
