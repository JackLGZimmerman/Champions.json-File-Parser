from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from simulator import SimulationRequest, simulate_actions
from simulator.data import SimulatorDataRepository
from simulator.errors import ActionParseError, MissingStatError, UnsupportedFormulaError
from simulator.parser import parse_actions

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DATA_DIR = ROOT / "tests" / "fixtures" / "simulator_data"


class SimulatorTests(unittest.TestCase):
    def test_parse_multiple_actions(self) -> None:
        actions = parse_actions("Aatrox Q - Activation 1, Aatrox E")

        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].champion_text, "Aatrox")
        self.assertEqual(actions[0].ability_key, "Q")
        self.assertEqual(actions[0].activation_index, 1)
        self.assertEqual(actions[1].ability_key, "E")

    def test_resolves_aliases_from_champ_id_name_map(self) -> None:
        repository = SimulatorDataRepository(FIXTURE_DATA_DIR)

        champion = repository.resolve_champion("Monkey King")

        self.assertEqual(champion.champion_id, 62)
        self.assertEqual(champion.name, "Wukong")

    def test_level_growth_curve_for_static_stats(self) -> None:
        repository = SimulatorDataRepository(FIXTURE_DATA_DIR)
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

        result = simulate_actions(request, data_dir=FIXTURE_DATA_DIR)

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

        result = simulate_actions(request, data_dir=FIXTURE_DATA_DIR)

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
            simulate_actions(request, data_dir=FIXTURE_DATA_DIR)

    def test_non_strict_mode_records_warning_for_unsupported_formula(self) -> None:
        request = SimulationRequest(
            attacker="Ahri",
            target="Aatrox",
            actions="Ahri Q",
            attacker_stat_overrides={"ability_power": 50.0},
        )

        result = simulate_actions(request, data_dir=FIXTURE_DATA_DIR, strict=False)

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
            simulate_actions(request, data_dir=FIXTURE_DATA_DIR)

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


def write_formatted_only_fixture(data_dir: Path) -> None:
    formatted_source = FIXTURE_DATA_DIR / "champions" / (
        "communitydragon_abilities_formatted.json"
    )
    formatted_payload = json.loads(formatted_source.read_text(encoding="utf-8"))

    champion_dir = data_dir / "champions"
    champion_dir.mkdir(parents=True)
    (champion_dir / "communitydragon_abilities_formatted.json").write_text(
        json.dumps(formatted_payload),
        encoding="utf-8",
    )
    (champion_dir / "champ_id_name_map.jsonl").write_text(
        "\n".join(
            [
                '{"_key":"266","name":"Aatrox","alias":"Aatrox"}',
                '{"_key":"103","name":"Ahri","alias":"Ahri"}',
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
