#!/usr/bin/env python3
"""Collect Final top-1 accuracy from VideoMAE experiment log files."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


CLASS_SUFFIX = re.compile(r"_c(2|3|10)$")

# Folder names without the trailing _c2/_c3/_c10.
MOVEMENT_GROUPS = {
    "S1": {
        "Demi-plié_1st",
        "Demi-plié_2nd",
        "Demi-plié_4th",
        "Cambré_4th",
        "Full_turn",
        "Grand_plié_4th",
        "Grand_plié_1st",
        "Side_tilt_(barre)",
        "Forward_tilt_1st",
        "Forward_tilt_4th",
        "Outward_tilt",
        "Transition_4th",
        "Transition_5th",
        "Balance_1st",
    },
    "S2": {
        "Gigue_step",
        "Back_ankle_balance",
        "Front_ankle_balance",
    },
    "S3": {
        "Forward_tilt",
        "Right_front_battement_fast",
        "Left_back_battement_fast",
        "Left_front_battement_slow",
        "Left_front_battement_fast",
        "Right_front_battement_slow",
        "Side_battement_slow",
        "Side_battement_fast",
    },
}


def movement_group(experiment_name: str) -> str | None:
    movement = CLASS_SUFFIX.sub("", experiment_name)
    for group, movements in MOVEMENT_GROUPS.items():
        if movement in movements:
            return group
    return None


def last_nonempty_line(path: Path) -> str | None:
    """Return the last non-empty UTF-8 line without loading the whole file."""
    last_line = None
    with path.open("r", encoding="utf-8", errors="replace") as file:
        for line in file:
            if line.strip():
                last_line = line.strip()
    return last_line


def read_final_top1(log_path: Path) -> float | None:
    line = last_nonempty_line(log_path)
    if line is None:
        return None

    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None

    value = record.get("Final top-1")
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read Final top-1 from each experiment's log.txt and summarize c2/c3/c10."
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Results directory (default: current directory)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("top1_results.csv"),
        help="Output CSV path (default: top1_results.csv)",
    )
    args = parser.parse_args()

    results_dir = args.results_dir.expanduser().resolve()
    grouped: dict[int, list[tuple[str, str, float]]] = defaultdict(list)
    skipped: list[tuple[str, str]] = []

    for experiment_dir in sorted(results_dir.iterdir()):
        if not experiment_dir.is_dir():
            continue

        match = CLASS_SUFFIX.search(experiment_dir.name)
        if not match:
            continue

        class_count = int(match.group(1))
        group = movement_group(experiment_dir.name)
        if group is None:
            skipped.append((experiment_dir.name, "movement is not assigned to S1/S2/S3"))
            continue

        log_path = experiment_dir / "log.txt"
        if not log_path.is_file():
            skipped.append((experiment_dir.name, "log.txt missing"))
            continue

        top1 = read_final_top1(log_path)
        if top1 is None:
            skipped.append((experiment_dir.name, "last line has no valid Final top-1"))
            continue

        grouped[class_count].append((group, experiment_dir.name, top1))

    csv_path = args.csv.expanduser()
    if not csv_path.is_absolute():
        csv_path = results_dir / csv_path
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["classes", "group", "experiment", "final_top1"])
        for class_count in (2, 3, 10):
            for group, experiment, top1 in grouped[class_count]:
                writer.writerow([class_count, group, experiment, f"{top1:.6f}"])

    print(f"Results directory: {results_dir}")
    print()
    for class_count in (2, 3, 10):
        rows = grouped[class_count]
        print(f"=== c{class_count} ===")
        if not rows:
            print("No valid results")
            print()
            continue

        for group_name in ("S1", "S2", "S3"):
            group_rows = [
                (experiment, top1)
                for group, experiment, top1 in rows
                if group == group_name
            ]
            print(f"-- {group_name} --")
            if not group_rows:
                print("No valid results")
                continue

            for experiment, top1 in group_rows:
                print(f"{experiment:<40} {top1:8.4f}%")
            average = sum(top1 for _, top1 in group_rows) / len(group_rows)
            print(
                f"{group_name + ' Average':<40} "
                f"{average:8.4f}%  (n={len(group_rows)})"
            )
        overall_average = sum(top1 for _, _, top1 in rows) / len(rows)
        print(f"{'Overall Average':<40} {overall_average:8.4f}%  (n={len(rows)})")
        print()

    if skipped:
        print(f"Skipped ({len(skipped)}):")
        for experiment, reason in skipped:
            print(f"- {experiment}: {reason}")
        print()

    print(f"CSV written to: {csv_path}")


if __name__ == "__main__":
    main()

