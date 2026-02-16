from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class FieldStats:
    present_rows: int
    type_counts: dict[str, int]


def iter_rows(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict):
                yield row


def summarize_top_level(rows: Iterable[dict[str, Any]]) -> tuple[int, dict[str, FieldStats]]:
    total_rows = 0
    present = Counter()
    types: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        total_rows += 1
        for key, value in row.items():
            present[key] += 1
            types[key][type(value).__name__] += 1

    stats = {
        key: FieldStats(present_rows=count, type_counts=dict(types[key]))
        for key, count in present.items()
    }
    return total_rows, stats


def summarize_nested_dict(rows: Iterable[dict[str, Any]], field: str) -> tuple[int, Counter[str], dict[str, Any] | None]:
    total_days_with_dict = 0
    subkeys = Counter()
    example: dict[str, Any] | None = None

    for row in rows:
        value = row.get(field)
        if not isinstance(value, dict):
            continue
        total_days_with_dict += 1
        if example is None:
            example = value
        subkeys.update(value.keys())

    return total_days_with_dict, subkeys, example


def summarize_nested_list_items(
    rows: Iterable[dict[str, Any]],
    dict_field: str,
    list_field: str,
) -> tuple[int, Counter[str], dict[str, Counter[str]]]:
    item_count = 0
    item_keys = Counter()
    item_types: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        outer = row.get(dict_field)
        if not isinstance(outer, dict):
            continue
        inner = outer.get(list_field)
        if not isinstance(inner, list):
            continue
        for item in inner:
            if not isinstance(item, dict):
                continue
            item_count += 1
            for key, value in item.items():
                item_keys[key] += 1
                item_types[key][type(value).__name__] += 1

    return item_count, item_keys, item_types


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Garmin DI-Connect Aggregator UDSFile schema")
    parser.add_argument(
        "--glob",
        default="data/raw/DI_CONNECT/DI-Connect-Aggregator/UDSFile_*.json",
        help="Glob for UDSFile JSON files",
    )
    parser.add_argument("--top", type=int, default=60, help="How many top-level fields to print")
    args = parser.parse_args()

    paths = sorted(Path().glob(args.glob))
    if not paths:
        raise SystemExit(f"No files found for glob: {args.glob}")

    rows_list = list(iter_rows(paths))

    total_rows, top_level = summarize_top_level(rows_list)

    print(f"files: {len(paths)}")
    print(f"rows: {total_rows}")
    print(f"unique top-level keys: {len(top_level)}")

    print("\nMost common top-level keys (key | %rows | types):")
    for key, st in sorted(top_level.items(), key=lambda kv: kv[1].present_rows, reverse=True)[: args.top]:
        pct = 100.0 * st.present_rows / max(total_rows, 1)
        top_types = ", ".join(f"{t}:{n}" for t, n in sorted(st.type_counts.items(), key=lambda kv: kv[1], reverse=True)[:3])
        print(f"{key} | {pct:5.1f}% | {top_types}")

    nested_dict_fields = ["allDayStress", "bodyBattery", "respiration", "hydration"]
    for field in nested_dict_fields:
        days, subkeys, example = summarize_nested_dict(rows_list, field)
        print(f"\n{field}: days_with_dict={days}, subkeys={len(subkeys)}")
        for sk, c in subkeys.most_common(30):
            print(f"  {sk}: {c}")
        if example is not None:
            print(f"  example_keys: {sorted(example.keys())}")

    print("\nNested list item schemas:")
    n, keys, types = summarize_nested_list_items(rows_list, "allDayStress", "aggregatorList")
    print(f"allDayStress.aggregatorList: items={n}, unique_keys={len(keys)}")
    for k, c in keys.most_common(30):
        top_types = ", ".join(f"{t}:{n}" for t, n in types[k].most_common(2))
        print(f"  {k}: {c} ({top_types})")

    n, keys, types = summarize_nested_list_items(rows_list, "bodyBattery", "bodyBatteryStatList")
    print(f"bodyBattery.bodyBatteryStatList: items={n}, unique_keys={len(keys)}")
    for k, c in keys.most_common(30):
        top_types = ", ".join(f"{t}:{n}" for t, n in types[k].most_common(2))
        print(f"  {k}: {c} ({top_types})")


if __name__ == "__main__":
    main()
