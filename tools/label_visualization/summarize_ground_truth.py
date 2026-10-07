"""Create count plots for selected columns in a ground-truth CSV or XLSX file."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
import pandas as pd


def load_table(path: Path, sheet_name: Optional[Union[str, int]]) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=0 if sheet_name is None else sheet_name)
    raise ValueError("Input must be a .csv, .xlsx, or .xls file.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Ground-truth CSV/XLSX file")
    parser.add_argument(
        "--columns",
        nargs="+",
        required=True,
        help="One or more columns to summarize; quote names containing spaces.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output PNG path")
    parser.add_argument("--sheet", default=None, help="Excel sheet name, if applicable")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")

    frame = load_table(args.input, args.sheet)
    missing = [column for column in args.columns if column not in frame.columns]
    if missing:
        parser.error(f"Columns not found: {', '.join(missing)}. Available: {', '.join(map(str, frame.columns))}")

    figure, axes = plt.subplots(1, len(args.columns), figsize=(5 * len(args.columns), 4), squeeze=False)
    for axis, column in zip(axes.flat, args.columns):
        counts = frame[column].dropna().value_counts().sort_index()
        counts.plot.bar(ax=axis, color="#4C78A8")
        axis.set_title(column)
        axis.set_xlabel("")
        axis.set_ylabel("Count")
        axis.tick_params(axis="x", rotation=45)
        for bar, count in zip(axis.patches, counts.values):
            axis.annotate(str(count), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                          ha="center", va="bottom", fontsize=9)

    figure.suptitle("Ground-truth label summary", y=1.02)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=300, bbox_inches="tight")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
