from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal, NamedTuple, TypedDict, cast

from items.collect import ITEMS_FILE_PATH, load_items_collected
from items.relationships import (
    build_items_by_id,
    extract_direct_related_item_ids,
    extract_item_relation_ids,
)
from items.value_map.item_group_definitions import build_item_group_definitions
from shared import data_segment_dir, write_jsonl

ITEM_VALUE_MAP_FILE_PATH: Path = data_segment_dir("items") / "item_value_map.jsonl"
ITEMS_PATH: Path = ITEMS_FILE_PATH
CHAMPION_POSITION_ITEM_COUNTS_PATH: Path = Path(
    "inputs/item_value_map/championid_position_item_counts.csv"
)
TIE_BREAK_VALUE_OFFSET = 0.01

# Manual membership exceptions for item-value-map inclusion.
# `EXCLUDED_*` stays as the hard deny-list for deprecated/support starter items.
# `COMPONENT_*` covers specific component items we still want even if they are not
# discovered naturally from the current legendary graph.
# `BOOTS_*` and `LEGENDARY_*` cover intentional legendary inclusions that do not
# satisfy the normal shop/in-store rules, such as upgraded boots and evolutions
# like Diadem of Songs.
EXCLUDED_ITEM_VALUE_MAP_IDS = {
    3005,
    3010,
    3095,
    3865,
    3866,
    3867,
    4643,
}
BOOTS_ITEM_VALUE_MAP_ADDITION_IDS = {
    3006,
    3008,
    3009,
    3013,
    3020,
    3047,
    3111,
    3117,
    3158,
    3168,
    3170,
    3171,
    3172,
    3173,
    3174,
    3175,
    3176,
}
COMPONENT_ITEM_VALUE_MAP_ADDITION_IDS = {
    1082,
}
LEGENDARY_ITEM_VALUE_MAP_ADDITION_IDS = BOOTS_ITEM_VALUE_MAP_ADDITION_IDS | {
    2530,
    3002,
    3040,
    3041,
    3042,
    3121,
    3869,
    3870,
    3871,
    3876,
    3877,
    6701,
}


class BuildValues(TypedDict):
    attack_damage: float
    ability_power: float
    lethality: float
    on_hit: float
    crit: float
    ar_tank: float
    mr_tank: float
    ad_off_tank: float
    ap_off_tank: float
    utility_protection: float
    utility_enchanter: float


BuildKey = Literal[
    "attack_damage",
    "ability_power",
    "lethality",
    "on_hit",
    "crit",
    "ar_tank",
    "mr_tank",
    "ad_off_tank",
    "ap_off_tank",
    "utility_protection",
    "utility_enchanter",
]


BUILD_VALUE_DEFAULTS: BuildValues = {
    "attack_damage": 0.0,
    "ability_power": 0.0,
    "lethality": 0.0,
    "on_hit": 0.0,
    "crit": 0.0,
    "ar_tank": 0.0,
    "mr_tank": 0.0,
    "ad_off_tank": 0.0,
    "ap_off_tank": 0.0,
    "utility_protection": 0.0,
    "utility_enchanter": 0.0,
}


class ScopedItemBuild(BuildValues, total=False):
    itemid: int
    championid: int | None
    teamposition: str | None


class ItemGroup(NamedTuple):
    name: str
    itemids: frozenset[int]
    baseline: dict[BuildKey, float]


ChampionPositionKey = tuple[int, str]


class ItemPools(NamedTuple):
    legendary_item_ids: set[int]
    component_item_ids: set[int]
    sub_component_item_ids: set[int]


def item_group(
    name: str,
    itemids: list[int],
    baseline: dict[BuildKey, float],
) -> ItemGroup:
    return ItemGroup(
        name=name,
        itemids=frozenset(itemids),
        baseline=baseline,
    )


def empty_build_values() -> BuildValues:
    return cast(BuildValues, BUILD_VALUE_DEFAULTS.copy())


def build_values(**overrides: float) -> BuildValues:
    values = empty_build_values()
    for key, value in overrides.items():
        if key not in BUILD_VALUE_DEFAULTS:
            raise KeyError(f"Unknown build value key: {key}")
        values[key] = value
    return offset_tie_break_values(values)


def offset_tie_break_values(values: BuildValues) -> BuildValues:
    for key, value in values.items():
        if value in {0.25, 0.5}:
            values[key] = value + TIE_BREAK_VALUE_OFFSET
    return values


# Item-id based baseline groups.
ITEM_GROUP_DEFINITIONS: tuple[ItemGroup, ...] = build_item_group_definitions(
    item_group,
    build_values,
)


def load_champion_position_item_counts(
    path: Path = CHAMPION_POSITION_ITEM_COUNTS_PATH,
) -> dict[ChampionPositionKey, dict[int, int]]:
    counts_by_combo: dict[ChampionPositionKey, dict[int, int]] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            championid_text = row.get("championid")
            teamposition = row.get("teamposition")
            item_text = row.get("item")
            pick_count_text = row.get("pick_count")

            if not isinstance(teamposition, str) or not teamposition:
                continue

            try:
                championid = int(championid_text or "")
                itemid = int(item_text or "")
                pick_count = int(pick_count_text or "")
            except ValueError:
                continue

            combo_counts = counts_by_combo.setdefault((championid, teamposition), {})
            combo_counts[itemid] = combo_counts.get(itemid, 0) + pick_count

    return counts_by_combo


def is_legendary_item_value_item(item: dict[str, Any]) -> bool:
    item_id = item.get("id")
    if not isinstance(item_id, int):
        return False
    if item_id < 1000 or item_id > 9999:
        return False
    if item_id in EXCLUDED_ITEM_VALUE_MAP_IDS:
        return False
    if item_id in LEGENDARY_ITEM_VALUE_MAP_ADDITION_IDS:
        return True
    if item.get("inStore") is not True:
        return False
    if item.get("displayInItemSets") is not True:
        return False
    price_total = item.get("priceTotal")
    return isinstance(price_total, int) and price_total > 1800


def extract_legendary_item_ids(
    items: list[dict[str, Any]] | None = None,
) -> set[int]:
    items = load_items_collected(ITEMS_PATH) if items is None else items
    return {
        item["id"]
        for item in items
        if isinstance(item, dict) and is_legendary_item_value_item(item)
    }


def clean_related_item_ids(
    item_ids: set[int],
    legendary_item_ids: set[int],
) -> set[int]:
    cleaned_item_ids = set(item_ids)
    cleaned_item_ids.difference_update(EXCLUDED_ITEM_VALUE_MAP_IDS)
    cleaned_item_ids.difference_update(legendary_item_ids)
    return cleaned_item_ids


def extract_item_pools_from_items(
    items: list[dict[str, Any]] | None = None,
) -> ItemPools:
    items = load_items_collected(ITEMS_PATH) if items is None else items
    items_by_id = build_items_by_id(items)
    legendary_item_ids = extract_legendary_item_ids(items)

    direct_component_item_ids = extract_direct_related_item_ids(
        items_by_id,
        legendary_item_ids,
    )
    direct_component_item_ids.update(COMPONENT_ITEM_VALUE_MAP_ADDITION_IDS)
    direct_component_item_ids = clean_related_item_ids(
        direct_component_item_ids,
        legendary_item_ids,
    )

    sub_component_item_ids = extract_direct_related_item_ids(
        items_by_id,
        direct_component_item_ids,
        exclude_parent_item_ids=False,
    )
    sub_component_item_ids = clean_related_item_ids(
        sub_component_item_ids,
        legendary_item_ids,
    )

    component_item_ids = direct_component_item_ids - sub_component_item_ids
    return ItemPools(
        legendary_item_ids=legendary_item_ids,
        component_item_ids=component_item_ids,
        sub_component_item_ids=sub_component_item_ids,
    )


def extract_build_value_fields(build: dict[str, Any]) -> BuildValues:
    values = empty_build_values()
    for key in BUILD_VALUE_DEFAULTS:
        value = build.get(key)
        if isinstance(value, (int, float)):
            values[key] = float(value)
    return values


def index_scoped_build_values(
    builds: list[ScopedItemBuild],
) -> dict[ChampionPositionKey, dict[int, BuildValues]]:
    values_by_combo: dict[ChampionPositionKey, dict[int, BuildValues]] = {}

    for build in builds:
        championid = build.get("championid")
        teamposition = build.get("teamposition")
        itemid = build.get("itemid")
        if (
            not isinstance(championid, int)
            or not isinstance(teamposition, str)
            or not isinstance(itemid, int)
        ):
            continue

        combo_values = values_by_combo.setdefault((championid, teamposition), {})
        combo_values[itemid] = extract_build_value_fields(build)

    return values_by_combo


def calculate_related_item_build_values(
    source_item_ids: set[int],
    target_item_ids: set[int],
    items_by_id: dict[int, dict[str, Any]],
    generic_target_values_by_itemid: dict[int, BuildValues],
    scoped_target_values_by_combo: dict[ChampionPositionKey, dict[int, BuildValues]],
    counts_by_combo: dict[ChampionPositionKey, dict[int, int]],
) -> list[ScopedItemBuild]:
    upgrade_map = build_item_upgrade_map(source_item_ids, items_by_id)
    priced_item_ids = source_item_ids | target_item_ids
    price_by_itemid = build_item_price_map(priced_item_ids, items_by_id)
    calculated_builds: list[ScopedItemBuild] = []
    generic_target_values_by_itemid = {
        itemid: values
        for itemid, values in generic_target_values_by_itemid.items()
        if itemid in target_item_ids
    }

    for (championid, teamposition), item_counts in sorted(counts_by_combo.items()):
        combo_source_item_ids = sorted(
            itemid for itemid in item_counts if itemid in source_item_ids
        )
        target_values_by_itemid = dict(generic_target_values_by_itemid)
        target_values_by_itemid.update(
            scoped_target_values_by_combo.get((championid, teamposition), {})
        )

        for itemid in combo_source_item_ids:
            matching_to_itemids = tuple(
                to_itemid
                for to_itemid in upgrade_map.get(itemid, ())
                if to_itemid in item_counts and to_itemid in target_item_ids
            )
            values = weighted_build_values_from_matching_items(
                itemid,
                matching_to_itemids,
                item_counts,
                target_values_by_itemid,
                price_by_itemid,
            )
            calculated_builds.append(
                {
                    "championid": championid,
                    "teamposition": teamposition,
                    "itemid": itemid,
                    **values,
                }
            )

    return calculated_builds


def calculate_component_build_values(
    item_pools: ItemPools,
    items_by_id: dict[int, dict[str, Any]],
    baseline_by_itemid: dict[int, BuildValues],
    counts_by_combo: dict[ChampionPositionKey, dict[int, int]],
) -> list[ScopedItemBuild]:
    return calculate_related_item_build_values(
        source_item_ids=item_pools.component_item_ids,
        target_item_ids=item_pools.legendary_item_ids,
        items_by_id=items_by_id,
        generic_target_values_by_itemid=baseline_by_itemid,
        scoped_target_values_by_combo={},
        counts_by_combo=counts_by_combo,
    )


def calculate_sub_component_build_values(
    item_pools: ItemPools,
    items_by_id: dict[int, dict[str, Any]],
    baseline_by_itemid: dict[int, BuildValues],
    component_values: list[ScopedItemBuild],
    counts_by_combo: dict[ChampionPositionKey, dict[int, int]],
) -> list[ScopedItemBuild]:
    return calculate_related_item_build_values(
        source_item_ids=item_pools.sub_component_item_ids,
        target_item_ids=item_pools.component_item_ids | item_pools.legendary_item_ids,
        items_by_id=items_by_id,
        generic_target_values_by_itemid=baseline_by_itemid,
        scoped_target_values_by_combo=index_scoped_build_values(component_values),
        counts_by_combo=counts_by_combo,
    )


def calculate_legendary_build_values(
    legendary_item_ids: set[int],
    baseline_by_itemid: dict[int, BuildValues],
) -> list[ScopedItemBuild]:
    return [
        {
            "championid": None,
            "teamposition": None,
            "itemid": itemid,
            **dict(baseline_by_itemid.get(itemid, empty_build_values())),
        }
        for itemid in sorted(legendary_item_ids)
    ]


def validate_item_group_definitions() -> None:
    item_groups_by_id: dict[int, list[str]] = {}
    for group in ITEM_GROUP_DEFINITIONS:
        for itemid in group.itemids:
            item_groups_by_id.setdefault(itemid, []).append(group.name)

    duplicate_item_groups = {
        itemid: group_names
        for itemid, group_names in item_groups_by_id.items()
        if len(group_names) > 1
    }
    if duplicate_item_groups:
        details = ", ".join(
            f"{itemid}: {group_names}"
            for itemid, group_names in sorted(duplicate_item_groups.items())
        )
        raise ValueError(f"Duplicate item baseline definitions found: {details}")


def build_item_group_baseline_map() -> dict[int, BuildValues]:
    validate_item_group_definitions()
    return {
        itemid: dict(group.baseline)
        for group in ITEM_GROUP_DEFINITIONS
        for itemid in group.itemids
    }


def format_item_names(
    item_ids: set[int],
    items_by_id: dict[int, dict[str, Any]],
) -> str:
    return ", ".join(
        f"{itemid} {items_by_id.get(itemid, {}).get('name', '<unknown>')}"
        for itemid in sorted(item_ids)
    )


def format_item_name(
    item_id: int,
    items_by_id: dict[int, dict[str, Any]],
) -> str:
    return str(items_by_id.get(item_id, {}).get("name", "<unknown>"))


def validate_item_pools(
    item_pools: ItemPools,
    baseline_by_itemid: dict[int, BuildValues],
    items_by_id: dict[int, dict[str, Any]],
) -> None:
    missing_legendary_baselines = item_pools.legendary_item_ids - set(
        baseline_by_itemid
    )
    if missing_legendary_baselines:
        raise ValueError(
            "Missing baseline definitions for legendary item ids: "
            f"{format_item_names(missing_legendary_baselines, items_by_id)}"
        )


def extract_counted_item_ids(
    counts_by_combo: dict[ChampionPositionKey, dict[int, int]],
) -> set[int]:
    return {
        itemid for item_counts in counts_by_combo.values() for itemid in item_counts
    }


def extract_item_value_ids(builds: list[ScopedItemBuild]) -> set[int]:
    return {
        itemid for build in builds if isinstance(itemid := build.get("itemid"), int)
    }


def report_counted_items_missing_from_map(
    counted_item_ids: set[int],
    item_value_ids: set[int],
    items_by_id: dict[int, dict[str, Any]],
) -> None:
    missing_item_ids = sorted(counted_item_ids - item_value_ids)
    if not missing_item_ids:
        print("All counted item ids are present in item_value_map.")
        return

    print("Counted item ids missing from item_value_map:")
    for itemid in missing_item_ids:
        print(f"{itemid} {format_item_name(itemid, items_by_id)}")


def build_item_upgrade_map(
    item_ids: set[int],
    items_by_id: dict[int, dict[str, Any]],
) -> dict[int, tuple[int, ...]]:
    upgrade_map: dict[int, tuple[int, ...]] = {}

    for item_id in item_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue

        upgrade_map[item_id] = extract_item_relation_ids(item, "to")

    return upgrade_map


def build_item_price_map(
    item_ids: set[int],
    items_by_id: dict[int, dict[str, Any]],
) -> dict[int, int]:
    price_map: dict[int, int] = {}

    for item_id in item_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue
        price_total = item.get("priceTotal")
        if isinstance(price_total, int) and price_total > 0:
            price_map[item_id] = price_total

    return price_map


def weighted_build_values_from_matching_items(
    source_itemid: int,
    matching_itemids: tuple[int, ...],
    item_counts: dict[int, int],
    target_values_by_itemid: dict[int, BuildValues],
    price_by_itemid: dict[int, int],
) -> BuildValues:
    scored_matching_itemids = tuple(
        itemid
        for itemid in matching_itemids
        if itemid in target_values_by_itemid and itemid in price_by_itemid
    )
    total_matching_count = sum(
        item_counts[itemid] for itemid in scored_matching_itemids
    )
    if total_matching_count <= 0:
        return build_values()

    source_price = price_by_itemid.get(source_itemid)
    if source_price is None:
        return build_values()

    weighted_values = build_values()

    for itemid in scored_matching_itemids:
        pick_count = item_counts[itemid]
        if pick_count <= 0:
            continue

        baseline = target_values_by_itemid[itemid]
        target_price = price_by_itemid[itemid]

        weight = pick_count / total_matching_count
        attenuation = source_price / target_price
        for key, value in baseline.items():
            weighted_values[key] += value * weight * attenuation

    return offset_tie_break_values(weighted_values)


def build_sort_key(build: dict[str, Any]) -> tuple[int, str, int]:
    championid = build.get("championid")
    return (
        -1 if championid is None else championid,
        str(build.get("teamposition") or ""),
        build["itemid"],
    )


def save_build_values(path: Path, builds: list[dict[str, Any]]) -> None:
    sorted_builds = sorted(
        builds,
        key=build_sort_key,
    )
    write_jsonl(sorted_builds, path)


def calculate_build_values(
    output_path: Path = ITEM_VALUE_MAP_FILE_PATH,
) -> list[ScopedItemBuild]:
    items = load_items_collected(ITEMS_PATH)
    items_by_id = build_items_by_id(items)
    item_pools = extract_item_pools_from_items(items)
    baseline_by_itemid = build_item_group_baseline_map()
    validate_item_pools(item_pools, baseline_by_itemid, items_by_id)
    counts_by_combo = load_champion_position_item_counts()

    legendary_values = calculate_legendary_build_values(
        item_pools.legendary_item_ids,
        baseline_by_itemid,
    )
    component_values = calculate_component_build_values(
        item_pools,
        items_by_id,
        baseline_by_itemid,
        counts_by_combo,
    )
    sub_component_values = calculate_sub_component_build_values(
        item_pools,
        items_by_id,
        baseline_by_itemid,
        component_values,
        counts_by_combo,
    )
    item_values = sub_component_values + component_values + legendary_values
    report_counted_items_missing_from_map(
        extract_counted_item_ids(counts_by_combo),
        extract_item_value_ids(item_values),
        items_by_id,
    )
    save_build_values(output_path, item_values)
    return item_values


if __name__ == "__main__":
    calculate_build_values()
