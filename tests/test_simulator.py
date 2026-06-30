from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from simulator import SimulationRequest, simulate_actions
from simulator.data import SimulatorDataRepository
from simulator.errors import ActionParseError, MissingStatError, UnsupportedFormulaError
from simulator.parser import parse_actions

CHAMPION_ID_ROWS = [
    {"_key": "266", "name": "Aatrox", "alias": "Aatrox"},
    {"_key": "103", "name": "Ahri", "alias": "Ahri"},
    {"_key": "62", "name": "Wukong", "alias": "MonkeyKing"},
]

STATIC_BASIC_ROWS = [
    {
        "_key": "Aatrox",
        "id": 266,
        "adaptiveType": "Physical",
        "attackType": "Melee",
        "resource": "Blood Well",
        "health_flat": 650.0,
        "health_perLevel": 114.0,
        "attackDamage_flat": 60.0,
        "attackDamage_perLevel": 5.0,
        "armor_flat": 38.0,
        "armor_perLevel": 4.8,
        "magicResistance_flat": 32.0,
        "magicResistance_perLevel": 2.05,
    },
    {
        "_key": "Ahri",
        "id": 103,
        "adaptiveType": "Magic",
        "attackType": "Ranged",
        "resource": "Mana",
        "health_flat": 590.0,
        "health_perLevel": 104.0,
        "attackDamage_flat": 53.0,
        "attackDamage_perLevel": 3.0,
        "armor_flat": 21.0,
        "armor_perLevel": 4.7,
        "magicResistance_flat": 30.0,
        "magicResistance_perLevel": 1.3,
    },
]

ADVANCED_ABILITY_ROWS = [
    {
        "_key": "Aatrox:Q",
        "championName": "Aatrox",
        "championId": 266,
        "abilityKey": "Q",
        "damageType": "PHYSICAL_DAMAGE",
        "projectile": None,
        "targetting": "Direction",
        "spellEffects": "spellaoe",
        "spellshieldable": "True",
        "targetRange": 650.0,
        "castTime": 0.6,
    },
    {
        "_key": "Aatrox:E",
        "championName": "Aatrox",
        "championId": 266,
        "abilityKey": "E",
        "damageType": None,
        "projectile": None,
        "targetting": "Direction",
        "spellEffects": None,
        "spellshieldable": None,
        "targetRange": 300.0,
        "castTime": 0.25,
    },
    {
        "_key": "Ahri:Q",
        "championName": "Ahri",
        "championId": 103,
        "abilityKey": "Q",
        "damageType": "MAGIC_DAMAGE",
        "projectile": "TRUE",
        "targetting": "Direction",
        "spellEffects": "spellaoe",
        "spellshieldable": "True",
        "targetRange": 900.0,
        "castTime": 0.25,
    },
]

ABILITY_FEATURE_ROWS = [
    {
        "_key": "Aatrox:Q",
        "championName": "Aatrox",
        "championId": 266,
        "abilityKey": "Q",
        "stageCount": 2,
        "dmg_phys": 1,
        "percent_ad": 1,
    },
    {
        "_key": "Aatrox:E",
        "championName": "Aatrox",
        "championId": 266,
        "abilityKey": "E",
        "stageCount": 1,
        "eff_dash": 1,
    },
    {
        "_key": "Ahri:Q",
        "championName": "Ahri",
        "championId": 103,
        "abilityKey": "Q",
        "stageCount": 1,
        "dmg_magic": 1,
        "percent_ap": 1,
    },
]

FORMATTED_ABILITIES = {
    "Aatrox": {
        "id": 266,
        "alias": "Aatrox",
        "name": "Aatrox",
        "stats": {
            "baseHP": 650.0,
            "hpPerLevel": 114.0,
            "baseDamage": 60.0,
            "damagePerLevel": 5.0,
        },
        "abilities": {
            "Q": [
                {
                    "name": "The Darkin Blade",
                    "damageType": "PHYSICAL_DAMAGE",
                    "damageParts": [
                        {
                            "name": "QDamage",
                            "ratioColumns": ["percent_ad"],
                            "units": ["% AD"],
                        },
                        {
                            "name": "QEdgeDamage",
                            "ratioColumns": ["percent_ad"],
                            "units": ["% AD"],
                        },
                    ],
                    "dataValues": {
                        "QBaseDamage": [-5.0, 10.0, 25.0, 40.0, 55.0, 70.0, 85.0],
                        "QTotalADRatio": [0.525, 0.6, 0.675, 0.75, 0.825, 0.9, 0.975],
                        "QRampBonus": [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
                        "QSweetSpotBonus": [0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75],
                    },
                }
            ],
            "E": [
                {
                    "name": "Umbral Dash",
                    "damageType": None,
                    "damageParts": [
                        {
                            "name": "TotalEVamp",
                            "ratioColumns": ["percent_bonus_hp"],
                            "units": ["% BONUS HP"],
                        }
                    ],
                    "dataValues": {
                        "EBonusAD": [5.0, 15.0, 25.0, 35.0, 45.0, 55.0, 65.0]
                    },
                }
            ],
        },
    },
    "Ahri": {
        "id": 103,
        "alias": "Ahri",
        "name": "Ahri",
        "stats": {
            "baseHP": 590.0,
            "hpPerLevel": 104.0,
            "baseDamage": 53.0,
            "damagePerLevel": 3.0,
        },
        "abilities": {
            "Q": [
                {
                    "name": "Orb of Deception",
                    "damageType": "MAGIC_DAMAGE",
                    "damageParts": [
                        {
                            "name": "TotalDamage",
                            "ratioColumns": ["percent_ap"],
                            "units": ["% AP"],
                        }
                    ],
                    "dataValues": {
                        "BaseDamage": [10.0, 35.0, 60.0, 85.0, 110.0, 135.0]
                    },
                }
            ]
        },
    },
}


class SimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_data_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._temp_data_dir.name)
        write_simulator_fixture(self.data_dir)

    def tearDown(self) -> None:
        self._temp_data_dir.cleanup()

    def test_parse_multiple_actions(self) -> None:
        actions = parse_actions("Aatrox Q - Activation 1, Aatrox E")

        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].champion_text, "Aatrox")
        self.assertEqual(actions[0].ability_key, "Q")
        self.assertEqual(actions[0].activation_index, 1)
        self.assertEqual(actions[1].ability_key, "E")

    def test_resolves_aliases_from_champ_id_name_map(self) -> None:
        repository = SimulatorDataRepository(self.data_dir)

        champion = repository.resolve_champion("Monkey King")

        self.assertEqual(champion.champion_id, 62)
        self.assertEqual(champion.name, "Wukong")

    def test_level_growth_curve_for_static_stats(self) -> None:
        repository = SimulatorDataRepository(self.data_dir)
        ahri = repository.resolve_champion("Ahri")

        stats = repository.champion_stats(ahri, level=2, overrides={})

        self.assertAlmostEqual(stats.max_health or 0.0, 590.0 + 104.0 * 0.72)

    def test_aatrox_combo_against_ahri(self) -> None:
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

        result = simulate_actions(request, data_dir=self.data_dir)

        raw_damages = [event.raw_damage for event in result.events]
        mitigated = 100.0 / 121.0
        self.assertEqual(len(result.events), 4)
        self.assertEqual(result.events[0].damage_type, "PHYSICAL_DAMAGE")
        self.assertAlmostEqual(raw_damages[0], 46.0)
        self.assertAlmostEqual(raw_damages[1], 57.5)
        self.assertAlmostEqual(raw_damages[2], 69.0)
        self.assertAlmostEqual(raw_damages[3], 0.0)
        self.assertAlmostEqual(result.total_damage, (46.0 + 57.5 + 69.0) * mitigated)
        self.assertIn("no direct target damage", result.events[3].notes[0])

    def test_generic_magic_damage_when_ratio_stat_is_zero(self) -> None:
        request = SimulationRequest(
            attacker="Ahri",
            target="Aatrox",
            actions="Ahri Q",
        )

        result = simulate_actions(request, data_dir=self.data_dir)

        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].damage_type, "MAGIC_DAMAGE")
        self.assertAlmostEqual(result.events[0].raw_damage, 10.0)
        self.assertAlmostEqual(result.events[0].mitigated_damage, 10.0 * 100.0 / 132.0)

    def test_nonzero_unknown_ratio_raises_in_strict_mode(self) -> None:
        request = SimulationRequest(
            attacker="Ahri",
            target="Aatrox",
            actions="Ahri Q",
            attacker_stat_overrides={"ability_power": 50.0},
        )

        with self.assertRaises(UnsupportedFormulaError):
            simulate_actions(request, data_dir=self.data_dir)

    def test_non_strict_mode_records_warning_for_unsupported_formula(self) -> None:
        request = SimulationRequest(
            attacker="Ahri",
            target="Aatrox",
            actions="Ahri Q",
            attacker_stat_overrides={"ability_power": 50.0},
        )

        result = simulate_actions(request, data_dir=self.data_dir, strict=False)

        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0].code, "UnsupportedFormulaError")
        self.assertEqual(result.events[0].mitigated_damage, 0.0)

    def test_invalid_action_raises(self) -> None:
        request = SimulationRequest(
            attacker="Aatrox",
            target="Ahri",
            actions="Aatrox Slash",
        )

        with self.assertRaises(ActionParseError):
            simulate_actions(request, data_dir=self.data_dir)

    def test_missing_resistance_in_strict_formatted_fallback_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            write_formatted_only_fixture(data_dir)
            request = SimulationRequest(
                attacker="Aatrox",
                target="Ahri",
                actions="Aatrox Q - Activation 1",
            )

            with self.assertRaises(MissingStatError):
                simulate_actions(request, data_dir=data_dir)

    def test_stat_override_allows_formatted_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            write_formatted_only_fixture(data_dir)
            request = SimulationRequest(
                attacker="Aatrox",
                target="Ahri",
                actions="Aatrox Q - Activation 1",
                target_stat_overrides={"armor": 0.0},
            )

            result = simulate_actions(request, data_dir=data_dir)

            self.assertAlmostEqual(result.events[0].raw_damage, 46.0)
            self.assertAlmostEqual(result.events[0].mitigated_damage, 46.0)


def write_simulator_fixture(data_dir: Path) -> None:
    write_jsonl(
        data_dir / "champion-static-basic" / "basic_stats.jsonl",
        STATIC_BASIC_ROWS,
    )
    write_jsonl(data_dir / "champions" / "champ_id_name_map.jsonl", CHAMPION_ID_ROWS)
    write_json(
        data_dir / "champions" / "communitydragon_abilities_formatted.json",
        FORMATTED_ABILITIES,
    )
    write_jsonl(
        data_dir / "champion-ability-advanced" / "abilities.jsonl",
        ADVANCED_ABILITY_ROWS,
    )
    write_jsonl(
        data_dir / "champion-ability-advanced" / "ability_attribute_features.jsonl",
        ABILITY_FEATURE_ROWS,
    )


def write_formatted_only_fixture(data_dir: Path) -> None:
    write_json(
        data_dir / "champions" / "communitydragon_abilities_formatted.json",
        FORMATTED_ABILITIES,
    )
    write_jsonl(
        data_dir / "champions" / "champ_id_name_map.jsonl",
        CHAMPION_ID_ROWS[:2],
    )


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row) for row in rows)
    path.write_text(f"{payload}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
