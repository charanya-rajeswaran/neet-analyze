import argparse
import json
from pathlib import Path

import pandas as pd

from pdf_to_csv import build_master_dataframe


def _norm_str(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def dataframe_to_json_summaries(df: pd.DataFrame) -> list[dict]:
    out = pd.DataFrame()

    out["college"] = _norm_str(df.get("COLLEGE", pd.Series(index=df.index, dtype="string")))
    out["course"] = _norm_str(df.get("COURSE", pd.Series(index=df.index, dtype="string")))
    out["college_type"] = _norm_str(df.get("COLLEGE_TYPE", pd.Series(index=df.index, dtype="string")))
    out["quota"] = _norm_str(df.get("QUOTA", pd.Series(index=df.index, dtype="string")))
    out["community"] = _norm_str(df.get("COMMUNITY", pd.Series(index=df.index, dtype="string")))
    out["category"] = _norm_str(df.get("CATEGORY", pd.Series(index=df.index, dtype="string")))
    out["round"] = _norm_str(df.get("ROUND", pd.Series(index=df.index, dtype="string")))
    out["year"] = pd.to_numeric(df.get("YEAR", pd.Series(index=df.index)), errors="coerce").astype("Int64")
    out["rank"] = pd.to_numeric(
        df.get("RANK", pd.Series(index=df.index)),
        errors="coerce",
    )
    out["cutoff_marks"] = pd.to_numeric(
        df.get("TOTAL MARKS", pd.Series(index=df.index)),
        errors="coerce",
    )

    out = out.dropna(subset=["cutoff_marks"]).copy()
    out = out.dropna(subset=["rank"]).copy()
    out["rank"] = out["rank"].astype(float)
    out["cutoff_marks"] = out["cutoff_marks"].astype(float)

    group_cols = [
        "college",
        "course",
        "college_type",
        "quota",
        "community",
        "category",
        "round",
        "year",
    ]

    summary = (
        out.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            rank_mean=("rank", "mean"),
            rank_std=("rank", "std"),
            rank_min=("rank", "min"),
            rank_max=("rank", "max"),
            marks_mean=("cutoff_marks", "mean"),
            marks_std=("cutoff_marks", "std"),
            marks_min=("cutoff_marks", "min"),
            marks_max=("cutoff_marks", "max"),
        )
        .copy()
    )

    summary[["rank_std", "marks_std"]] = summary[["rank_std", "marks_std"]].fillna(0.0)

    # Round for compact JSON output while preserving useful precision.
    stat_cols = [
        "rank_mean",
        "rank_std",
        "rank_min",
        "rank_max",
        "marks_mean",
        "marks_std",
        "marks_min",
        "marks_max",
    ]
    summary[stat_cols] = summary[stat_cols].round(3)

    return summary.to_dict(orient="records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export NEET dataframe to JSON summaries.")
    parser.add_argument(
        "--output",
        default="data/tn_cutoffs.json",
        help="Output JSON file path (default: data/tn_cutoffs.json)",
    )
    args = parser.parse_args()

    df = build_master_dataframe()
    records = dataframe_to_json_summaries(df)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(records)} combination summaries to {output_path}")


if __name__ == "__main__":
    main()
