from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from champion_ability_advanced.extract import (  # noqa: E402
    ABILITY_FIELD_NAMES,
    ROW_FIELD_NAMES,
    build_raw_field_coverage,
    build_raw_nested_path_rows,
    extract_ability_advanced,
)
from champion_ability_advanced.detailed_features import (  # noqa: E402
    build_champion_ability_detailed_features,
)
from champions.communitydragon import ABILITY_ORDER  # noqa: E402
from champion_ability_attributes.generate_final_features import (  # noqa: E402
    build_champion_ability_scaling_profiles,
    extract_final_ability_attribute_features,
)


def ability_fixture(ability_key: str) -> dict[str, Any]:
    return {
        "affect": "Self, Enemies",
        "angle": 0.0,
        "castTime": 0.25,
        "collisionRadius": 225.0,
        "cooldown": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0],
        "cost": [50.0, 50.0, 50.0, 50.0, 50.0, 50.0],
        "damageParts": [
            {
                "name": f"{ability_key}Damage",
                "ratioColumns": ["percent_ap"],
                "units": ["% AP"],
            }
        ],
        "damageType": "MAGIC_DAMAGE",
        "dataValues": {"BaseDamage": [40.0, 80.0, 120.0]},
        "description": f"{ability_key} short description",
        "dynamicDescription": (
            f"{ability_key} deals <magicDamage>@BaseDamage@ magic damage</magicDamage> "
            "with + 50% AP."
        ),
        "innerRadius": 0.0,
        "name": f"{ability_key} Ability",
        "onTargetCdStatic": 0.0,
        "projectile": "TRUE",
        "range": [625.0, 625.0, 625.0, 625.0, 625.0, 625.0],
        "ratioColumns": ["percent_ap"],
        "raw": {
            "castConeAngle": None,
            "castRadius": [225.0, 225.0, 225.0],
            "castRange": [625.0, 625.0, 625.0],
            "mAffectsTypeFlags": 6154,
            "mAmmoRechargeTime": None,
            "mCastTime": 0.25,
            "mLineWidth": None,
            "mMissileSpec": {
                "__type": "MissileSpecification",
                "movementComponent": {
                    "__type": "FixedSpeedMovement",
                    "mSpeed": 1400.0,
                },
            },
            "mSpellTags": ["Trait_DamageAbility"],
            "mTargetingTypeData": {"__type": "Target"},
            "missileSpeed": 1400.0,
        },
        "rechargeRate": 0.0,
        "recordPath": f"Characters/Test/Spells/{ability_key}",
        "resource": "MANA",
        "scalingParts": [
            {
                "name": f"{ability_key}Damage",
                "ratioColumns": ["percent_ap"],
                "units": ["% AP"],
            }
        ],
        "speed": 1400.0,
        "spellEffects": "spell",
        "spellshieldable": "True",
        "targetRange": 625.0,
        "targetingType": "Target",
        "targetting": "Unit",
        "tetherRadius": 0.0,
        "units": ["% AP"],
        "width": 0.0,
    }


def champion_fixture(champion_id: int, champion_name: str) -> dict[str, Any]:
    return {
        "id": champion_id,
        "name": champion_name,
        "abilities": {
            ability_key: [ability_fixture(ability_key)]
            for ability_key in ABILITY_ORDER
        },
    }


def formatted_payload_fixture() -> dict[str, Any]:
    return {
        "Brand": champion_fixture(63, "Brand"),
        "Ahri": champion_fixture(103, "Ahri"),
    }


class ChampionAbilityAdvancedExtractTest(unittest.TestCase):
    def test_extracts_identity_then_all_source_fields(self) -> None:
        rows = extract_ability_advanced(formatted_payload_fixture())

        self.assertEqual(len(rows), 10)
        self.assertEqual(list(rows[0]), list(ROW_FIELD_NAMES))
        self.assertEqual(rows[0]["_key"], "Ahri:P")
        self.assertEqual(rows[0]["championName"], "Ahri")
        self.assertEqual(rows[0]["abilityKey"], "P")
        self.assertEqual(rows[0]["abilityIndex"], 0)
        self.assertEqual(rows[-1]["_key"], "Brand:R")

        for field_name in ABILITY_FIELD_NAMES:
            self.assertIn(field_name, rows[0])

        self.assertIsInstance(rows[0]["cooldown"], list)
        self.assertIsInstance(rows[0]["damageParts"], list)
        self.assertIsInstance(rows[0]["dataValues"], dict)
        self.assertIsInstance(rows[0]["raw"], dict)

    def test_rows_are_json_round_trip_safe(self) -> None:
        rows = extract_ability_advanced(formatted_payload_fixture())

        for row in rows:
            encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            self.assertEqual(json.loads(encoded), row)

    def test_raw_inventory_reports_direct_and_nested_paths(self) -> None:
        rows = extract_ability_advanced(formatted_payload_fixture())

        coverage = build_raw_field_coverage(rows)
        self.assertEqual(coverage["rowCount"], 10)
        self.assertEqual(
            coverage["fields"]["mMissileSpec"]["types"],
            {"dict": 10},
        )
        self.assertEqual(
            coverage["fields"]["mAmmoRechargeTime"]["types"],
            {"NoneType": 10},
        )

        nested_paths = {
            nested_row["path"]
            for nested_row in build_raw_nested_path_rows(rows)
        }
        self.assertIn("raw.mMissileSpec.movementComponent.__type", nested_paths)
        self.assertIn("raw.mTargetingTypeData.__type", nested_paths)

    def test_rejects_missing_extra_or_multi_entry_ability_data(self) -> None:
        cases = [
            (
                "missing slot",
                lambda payload: payload["Ahri"]["abilities"].pop("R"),
                "missing R",
            ),
            (
                "multi entry slot",
                lambda payload: payload["Ahri"]["abilities"]["Q"].append(
                    ability_fixture("Q")
                ),
                "expected exactly one ability entry",
            ),
            (
                "missing field",
                lambda payload: payload["Ahri"]["abilities"]["W"][0].pop("raw"),
                "missing raw",
            ),
            (
                "extra field",
                lambda payload: payload["Ahri"]["abilities"]["E"][0].update(
                    {"unexpected": True}
                ),
                "extra unexpected",
            ),
        ]

        for case_name, mutate, message in cases:
            with self.subTest(case_name):
                payload = deepcopy(formatted_payload_fixture())
                mutate(payload)
                with self.assertRaisesRegex(ValueError, message):
                    extract_ability_advanced(payload)


class ChampionAbilityAttributesRegressionTest(unittest.TestCase):
    def test_attribute_pipeline_stays_separate_from_advanced_table(self) -> None:
        payload = formatted_payload_fixture()
        attribute_rows = extract_final_ability_attribute_features(payload)
        profile_rows = build_champion_ability_scaling_profiles(attribute_rows)

        self.assertEqual(len(attribute_rows), 10)
        self.assertEqual(len(profile_rows), 2)
        self.assertNotIn("raw", attribute_rows[0])
        self.assertIn("stageCount", attribute_rows[0])
        self.assertTrue(
            all(
                value in {0, 1}
                for key, value in attribute_rows[0].items()
                if key not in {"_key", "championName", "championId", "abilityKey"}
                and key != "stageCount"
            )
        )
        self.assertIn("percent_ap", attribute_rows[0])
        self.assertIn("championId", profile_rows[0])
        self.assertIn("championName", profile_rows[0])
        self.assertIn("ability_count", profile_rows[0])
        self.assertIn("scaling_ability_count", profile_rows[0])
        self.assertIn("scaling_trait_type_count", profile_rows[0])
        self.assertIn("scaling_trait_match_count", profile_rows[0])
        self.assertIn("scaling_stage_match_count", profile_rows[0])
        self.assertIn("percent_ap_ability_count", profile_rows[0])
        self.assertIn("percent_ap_stage_count", profile_rows[0])
        self.assertIn("dmg_magic_ability_count", profile_rows[0])
        self.assertNotIn("cid", profile_rows[0])
        self.assertNotIn("champ", profile_rows[0])
        self.assertNotIn("sc_ab", profile_rows[0])
        self.assertNotIn("p_ap_ab", profile_rows[0])
        self.assertNotIn("d_mag_ab", profile_rows[0])


class ChampionAbilityDetailedFeaturesTest(unittest.TestCase):
    def build_rows(self) -> list[dict[str, Any]]:
        payload = formatted_payload_fixture()
        ability_rows = extract_ability_advanced(payload)
        attribute_rows = extract_final_ability_attribute_features(payload)
        return build_champion_ability_detailed_features(ability_rows, attribute_rows)

    def test_outputs_one_fixed_schema_row_per_champion(self) -> None:
        rows = self.build_rows()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["_key"], "103")
        self.assertEqual(rows[0]["championId"], 103)
        self.assertEqual(rows[0]["championName"], "Ahri")
        self.assertEqual(rows[1]["_key"], "63")
        self.assertEqual(rows[1]["championName"], "Brand")
        self.assertEqual(
            {tuple(row.keys()) for row in rows},
            {tuple(rows[0].keys())},
        )

    def test_slot_fields_include_detailed_traits_and_summaries(self) -> None:
        row = self.build_rows()[0]

        for slot in ABILITY_ORDER:
            self.assertIn(f"{slot}_castTime", row)
            self.assertIn(f"{slot}_cooldown_rank1", row)
            self.assertIn(f"{slot}_cooldown_rankmax", row)
            self.assertIn(f"{slot}_cooldown_has_values", row)
            self.assertIn(f"{slot}_damageType_MAGIC_DAMAGE", row)
            self.assertIn(f"{slot}_targetingType_Target", row)
            self.assertIn(f"{slot}_projectile_true", row)
            self.assertIn(f"{slot}_spellshieldable_true", row)
            self.assertIn(f"{slot}_dataValues_count", row)
            self.assertIn(f"{slot}_scalingPart_count", row)
            self.assertIn(f"{slot}_raw_has_missile_spec", row)
            self.assertIn(f"{slot}_raw_missile_speed", row)
            self.assertIn(f"{slot}_percent_ap", row)
            self.assertIn(f"{slot}_dmg_magic", row)
            self.assertIn(f"{slot}_projectile_trait", row)

        self.assertEqual(row["Q_cooldown_rank1"], 10.0)
        self.assertEqual(row["Q_cooldown_rankmax"], 5.0)
        self.assertEqual(row["Q_cooldown_delta"], -5.0)
        self.assertEqual(row["Q_percent_ap"], 1)
        self.assertEqual(row["Q_dmg_magic"], 1)
        self.assertEqual(row["Q_raw_missile_speed"], 1400.0)

    def test_expands_generic_compact_attribute_trait_names(self) -> None:
        payload = formatted_payload_fixture()
        ability_rows = extract_ability_advanced(payload)
        attribute_rows = extract_final_ability_attribute_features(payload)
        for attribute_row in attribute_rows:
            attribute_row["aoe"] = 0
            attribute_row["cc"] = 0
            if (
                attribute_row["championId"] == 103
                and attribute_row["abilityKey"] == "Q"
            ):
                attribute_row["aoe"] = 1
                attribute_row["cc"] = 1

        row = build_champion_ability_detailed_features(
            ability_rows,
            attribute_rows,
        )[0]

        self.assertEqual(row["Q_area_of_effect"], 1)
        self.assertEqual(row["Q_crowd_control"], 1)
        self.assertNotIn("Q_aoe", row)
        self.assertNotIn("Q_cc", row)
        self.assertNotIn("Q_proj", row)

    def test_excludes_source_text_and_compact_alias_fields(self) -> None:
        row = self.build_rows()[0]
        text_fields = {"description", "dynamicDescription", "name", "recordPath"}
        compact_aliases = {"aoe", "cc", "sc_ab", "p_ap", "d_mag", "stk", "proj"}

        for key in row:
            self.assertFalse(
                any(key == field or key.endswith(f"_{field}") for field in text_fields)
            )
            self.assertFalse(
                any(key == alias or key.endswith(f"_{alias}") for alias in compact_aliases)
            )

    def test_does_not_mutate_source_rows(self) -> None:
        payload = formatted_payload_fixture()
        ability_rows = extract_ability_advanced(payload)
        attribute_rows = extract_final_ability_attribute_features(payload)
        original_ability_rows = deepcopy(ability_rows)

        build_champion_ability_detailed_features(ability_rows, attribute_rows)

        self.assertEqual(ability_rows, original_ability_rows)


if __name__ == "__main__":
    unittest.main()
