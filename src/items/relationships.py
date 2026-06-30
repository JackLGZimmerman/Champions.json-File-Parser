from __future__ import annotations

from typing import Any


def extract_related_non_legendary_item_ids(
    items: list[dict[str, Any]],
    legendary_item_ids: set[int],
) -> set[int]:
    items_by_id = {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    non_legendary_item_ids: set[int] = set()

    for item_id in legendary_item_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue

        for key in ("from", "to"):
            related_ids = item.get(key)
            if not isinstance(related_ids, list):
                continue

            for related_id in related_ids:
                if not isinstance(related_id, int):
                    continue
                if related_id in legendary_item_ids:
                    continue

                related_item = items_by_id.get(related_id)
                if related_item is None:
                    continue

                non_legendary_item_ids.add(related_id)

    return non_legendary_item_ids
