from __future__ import annotations

from typing import Any


def build_items_by_id(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }


def extract_item_relation_ids(item: dict[str, Any], key: str) -> tuple[int, ...]:
    related_ids = item.get(key)
    if not isinstance(related_ids, list):
        return ()
    return tuple(
        related_id for related_id in related_ids if isinstance(related_id, int)
    )


def extract_related_non_legendary_item_ids(
    items: list[dict[str, Any]],
    legendary_item_ids: set[int],
) -> set[int]:
    items_by_id = build_items_by_id(items)
    non_legendary_item_ids: set[int] = set()

    for item_id in legendary_item_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue

        for key in ("from", "to"):
            for related_id in extract_item_relation_ids(item, key):
                if related_id in legendary_item_ids:
                    continue

                related_item = items_by_id.get(related_id)
                if related_item is None:
                    continue

                non_legendary_item_ids.add(related_id)

    return non_legendary_item_ids


def extract_direct_related_item_ids(
    items_by_id: dict[int, dict[str, Any]],
    parent_item_ids: set[int],
    exclude_parent_item_ids: bool = True,
) -> set[int]:
    related_item_ids: set[int] = set()

    for item_id in parent_item_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue

        related_item_ids.update(extract_item_relation_ids(item, "from"))

    for item_id, item in items_by_id.items():
        to_item_ids = extract_item_relation_ids(item, "to")
        if any(parent_item_id in parent_item_ids for parent_item_id in to_item_ids):
            related_item_ids.add(item_id)

    cleaned_item_ids = {
        item_id for item_id in related_item_ids if item_id in items_by_id
    }
    if exclude_parent_item_ids:
        cleaned_item_ids.difference_update(parent_item_ids)
    return cleaned_item_ids
