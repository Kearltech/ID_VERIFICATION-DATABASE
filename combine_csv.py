"""Combine two CSV files (main CSV + name dataset) into one joined CSV.

Usage examples (PowerShell / command line):

# Basic merge on column 'name' (inner join):
python combine_csv.py --input data.csv --names names.csv --on name --output combined.csv

# Left join on 'id', keep only certain columns from names file:
python combine_csv.py --input data.csv --names names.csv --on id --how left --names-cols id,name,email --output combined.csv

This script does not run anything by default; it's safe to open and adapt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge a main CSV with a name dataset CSV")
    p.add_argument("--input", "-i", required=True, help="Path to the main input CSV file")
    p.add_argument("--names", "-n", required=True, help="Path to the names CSV file to merge in")
    p.add_argument("--on", "-k", required=True, help="Column name to join on (must exist in both files)")
    p.add_argument("--how", "-H", default="inner", choices=["left", "right", "inner", "outer"], help="Join type (default: inner)")
    p.add_argument("--names-cols", help="Comma-separated subset of columns from the names CSV to keep (default: all)")
    p.add_argument("--suffixes", default="_x,_y", help="Comma-separated suffixes for overlapping columns (default: _x,_y)")
    p.add_argument("--output", "-o", required=True, help="Path for the combined CSV output")
    p.add_argument("--encoding", default="utf-8", help="File encoding for read/write (default: utf-8)")
    p.add_argument("--preview", action="store_true", help="Print a brief preview of the merged DataFrame and exit")
    return p.parse_args()


def read_csv(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    # Let pandas infer types; keep low_memory False to avoid dtype warnings
    return pd.read_csv(path, encoding=encoding, low_memory=False)


def main(argv: list[str] | None = None) -> int:
    args = parse_args() if argv is None else parse_args()

    input_path = Path(args.input)
    names_path = Path(args.names)
    output_path = Path(args.output)

    # Read files
    print(f"Reading main CSV: {input_path}")
    df_main = read_csv(input_path, encoding=args.encoding)
    print(f"Main rows: {len(df_main)}, columns: {list(df_main.columns)}")

    print(f"Reading names CSV: {names_path}")
    df_names = read_csv(names_path, encoding=args.encoding)
    print(f"Names rows: {len(df_names)}, columns: {list(df_names.columns)}")

    join_key = args.on
    if join_key not in df_main.columns:
        print(f"Warning: join key '{join_key}' not found in main CSV columns", file=sys.stderr)
    if join_key not in df_names.columns:
        print(f"Warning: join key '{join_key}' not found in names CSV columns", file=sys.stderr)

    # Optionally select a subset of columns from names CSV
    if args.names_cols:
        cols = [c.strip() for c in args.names_cols.split(",") if c.strip()]
        # Ensure join key is present
        if join_key not in cols:
            cols = [join_key] + cols
        missing = [c for c in cols if c not in df_names.columns]
        if missing:
            raise KeyError(f"Requested names-cols not found in names CSV: {missing}")
        df_names = df_names[cols]

    suffixes = tuple(s.strip() for s in args.suffixes.split(",")) if args.suffixes else ("_x", "_y")

    print(f"Merging on '{join_key}' with how='{args.how}' and suffixes={suffixes}")
    df_merged = pd.merge(df_main, df_names, on=join_key, how=args.how, suffixes=suffixes)

    print(f"Merged rows: {len(df_merged)}, columns: {list(df_merged.columns)}")

    if args.preview:
        print(df_merged.head(10).to_string(index=False))
        return 0

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing merged CSV to {output_path}")
    df_merged.to_csv(output_path, index=False, encoding=args.encoding)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

