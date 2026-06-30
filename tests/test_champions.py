from __future__ import annotations

import unittest
from typing import Any

from champions.normalize import normalize_champions
from champions.validate import validate_champions

STAT_NAMES = (
    "health",
    "healthRegen",
    "mana",
    "manaRegen",
    "armor",
    "magicResistance",
    "attackDamage",
    "movespeed",
    "acquisitionRadius",
    "selectionRadius",
    "pathingRadius",
    "gameplayRadius",
    "criticalStrikeDamage",
    "criticalStrikeDamageModifier",
    "attackSpeed",
    "attackSpeedRatio",
    "attackCastTime",
    "attackTotalTime",
    "attackDelayOffset",
    "attackRange",
    "aramDamageTaken",
    "aramDamageDealt",
    "aramHealing",
    "aramShielding",
    "aramTenacity",
    "aramAbilityHaste",
    "aramAttackSpeed",
    "aramEnergyRegen",
    "urfDamageTaken",
    "urfDamageDealt",
    "urfHealing",
    "urfShielding",
)


class ChampionPipelineTests(unittest.TestCase):
    def test_validation_and_normalization_retain_detailed_raw_payload(self) -> None:
        champions = validate_champions({"Example": champion_payload()})

        normalized = normalize_champions(champions)["Example"]
        ability = normalized["abilities"]["Q"][0]

        self.assertEqual(normalized["title"], "The Detailed")
        self.assertEqual(normalized["fullName"], "Example Champion")
        self.assertEqual(normalized["lore"], "Long-form champion lore.")
        self.assertEqual(normalized["faction"], "Test Faction")
        self.assertEqual(normalized["price"]["sourcePrice"]["event"], "retained")
        self.assertEqual(
            normalized["attributeRatings"]["rawDifficultyBand"],
            "expert",
        )
        self.assertIn("skins", normalized)
        self.assertIn("aramDamageTaken", normalized["stats"])
        self.assertEqual(normalized["stats"]["health"]["percent"], 0.1)
        self.assertEqual(normalized["stats"]["health"]["rawFormula"], "retained")
        self.assertEqual(ability["onHitEffects"], [{"name": "retained"}])
        self.assertEqual(ability["occurrence"], "On cast")
        self.assertEqual(ability["missileSpeed"], "1200")
        self.assertEqual(
            ability["rawSimulatorFormula"],
            {"parts": ["base", "ratio"]},
        )
        self.assertEqual(ability["effects"][0]["rawEffectNote"], "retained")
        self.assertEqual(
            ability["effects"][0]["leveling"][0]["rawLevelingNote"],
            "retained",
        )


def champion_payload() -> dict[str, Any]:
    stats = {stat_name: attribute_metric() for stat_name in STAT_NAMES}
    stats["health"]["rawFormula"] = "retained"

    return {
        "id": 1,
        "key": "Example",
        "name": "Example",
        "title": "The Detailed",
        "fullName": "Example Champion",
        "icon": "https://example.com/example.png",
        "resource": "Mana",
        "attackType": "Ranged",
        "adaptiveType": "Magic",
        "stats": stats,
        "positions": ["Middle"],
        "roles": ["Mage"],
        "attributeRatings": {
            "damage": 3,
            "toughness": 1,
            "control": 2,
            "mobility": 2,
            "utility": 1,
            "abilityReliance": 3,
            "difficulty": 2,
            "rawDifficultyBand": "expert",
        },
        "abilities": {
            "P": [],
            "Q": [detailed_ability()],
            "W": [],
            "E": [],
            "R": [],
        },
        "releaseDate": "2026-01-01",
        "releasePatch": "1.0",
        "patchLastChanged": "1.1",
        "price": {
            "blueEssence": 450,
            "rp": 260,
            "saleRp": 0,
            "sourcePrice": {"event": "retained"},
        },
        "lore": "Long-form champion lore.",
        "faction": "Test Faction",
        "skins": [],
    }


def attribute_metric() -> dict[str, Any]:
    return {
        "flat": 10.0,
        "percent": 0.1,
        "perLevel": 1.0,
        "percentPerLevel": 0.01,
    }


def detailed_ability() -> dict[str, Any]:
    return {
        "name": "Detailed Strike",
        "icon": "https://example.com/q.png",
        "effects": [
            {
                "description": "Deals detailed damage.",
                "leveling": [
                    {
                        "attribute": "Damage",
                        "modifiers": [{"values": [10, 20], "units": [""]}],
                        "rawLevelingNote": "retained",
                    }
                ],
                "rawEffectNote": "retained",
            }
        ],
        "cost": {"modifiers": [{"values": [50], "units": ["Mana"]}]},
        "cooldown": {"modifiers": [], "affectedByCdr": True},
        "targeting": "Direction",
        "affects": "Enemies",
        "collisionRadius": 100,
        "innerRadius": 50,
        "angle": 30,
        "castTime": "0.25",
        "onHitEffects": [{"name": "retained"}],
        "occurrence": "On cast",
        "missileSpeed": "1200",
        "rawSimulatorFormula": {"parts": ["base", "ratio"]},
    }


if __name__ == "__main__":
    unittest.main()
