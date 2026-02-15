import os
import pickle
import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import tabula
from pypdf import PdfReader


COMMON_COLUMNS = ["RANK", "TOTAL MARKS", "COMMUNITY", "ALLOTTED TO"]
QUOTA = "7.5%"
YEAR = 2025
CACHE_SCHEMA_VERSION = "v4"


@dataclass(frozen=True)
class ParseStyle:
    table_index: int = 0
    source_columns: Optional[list[str]] = None
    keep_columns: Optional[list[str]] = None
    start_page: int = 1
    lattice: bool = True
    stream: bool = False
    extract_college_from_text: bool = False


STYLE_ROUND1_TABLE0 = ParseStyle(
    table_index=0,
    keep_columns=["RANK", "TOTAL MARKS", "COMMUNITY", "COLLEGE ALLOTTED"],
    extract_college_from_text=True,
)
STYLE_ROUND1_TABLE1 = ParseStyle(
    table_index=1,
    keep_columns=["RANK", "TOTAL MARKS", "COMMUNITY", "COLLEGE ALLOTTED"],
    extract_college_from_text=True,
)
STYLE_DEFAULT = ParseStyle(
    table_index=0,
    source_columns=[
        "SNO",
        "RANK",
        "ARNO",
        "NAME",
        "COMMUNITY",
        "TOTAL MARKS",
        "ALLOTTED FROM",
        "ALLOTTED TO",
        "Status",
    ],
)
STYLE_GOVT_DEFAULT = ParseStyle(
    table_index=0,
    source_columns=[
        "SNO",
        "RANK",
        "ARNO",
        "NAME",
        "COMMUNITY",
        "TOTAL MARKS",
        "ALLOTTED FROM",
        "ALLOTTED TO",
        "CATEGORY",
        "Status",
    ],
    keep_columns=["RANK", "TOTAL MARKS", "COMMUNITY", "ALLOTTED TO", "CATEGORY"],
)
STYLE_MGMT_DEFAULT = ParseStyle(
    table_index=0,
    source_columns=[
        "SNO",
        "RANK",
        "ARNO",
        "NAME",
        "TOTAL MARKS",
        "ALLOTTED FROM",
        "ALLOTTED TO",
        "CATEGORY",
        "Status",
    ],
    keep_columns=["RANK", "TOTAL MARKS", "ALLOTTED TO", "CATEGORY"],
)
STYLE_ROUND4 = ParseStyle(
    table_index=0,
    start_page=2,
    source_columns=["SNO", "RANK", "ARNO", "NAME", "COMMUNITY", "TOTAL MARKS", "ALLOTTED TO"],
)
STYLE_ROUND5 = ParseStyle(
    table_index=0,
    start_page=1,
    source_columns=["SNO", "RANK", "ARNO", "NAME", "COMMUNITY", "TOTAL MARKS", "ALLOTTED TO"],
)

STYLE_GOVT_ROUND1 = ParseStyle(
    table_index=0,
    start_page=1,
    source_columns=["SNO", "RANK", "ARNO", "NAME", "COMMUNITY", "TOTAL MARKS", "ALLOTTED TO", "CATEGORY"],
    keep_columns=["RANK", "TOTAL MARKS", "COMMUNITY", "ALLOTTED TO", "CATEGORY"],
)



def extract_college_name(text: str) -> str:
    match = re.search(r"ALLOTTED\s+(.*)\s+JOIN", text)
    return match.group(1).strip() if match else "UNKNOWN"


def _pdf_label(pdf_path: str) -> str:
    return os.path.basename(pdf_path)


def _cache_path_from_pdf(pdf_path: str) -> str:
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_")
    return os.path.join("cache", f"{safe_stem}.{CACHE_SCHEMA_VERSION}.pkl")


def _add_common_metadata(df: pd.DataFrame, round_name: str, quota: str = QUOTA) -> pd.DataFrame:
    df["QUOTA"] = quota
    df["YEAR"] = YEAR
    df["ROUND"] = round_name
    return df


def _post_process_allotted_to(df: pd.DataFrame) -> pd.DataFrame:
    if "RANK" in df.columns:
        df["RANK"] = pd.to_numeric(df["RANK"], errors="coerce").astype("Int64")

    if "COURSE" not in df.columns:
        df["COURSE"] = ""
    if "COLLEGE" not in df.columns:
        df["COLLEGE"] = ""

    if "ROUND" in df.columns:
        round1_mask = df["ROUND"] == "Round1"
    else:
        round1_mask = pd.Series(False, index=df.index)
    if "QUOTA" in df.columns:
        round1_college_only_mask = round1_mask & df["QUOTA"].isin([QUOTA, "EXSRVC", "PWD", "SPORTS"])
    else:
        round1_college_only_mask = round1_mask

    if "ALLOTTED TO" in df.columns:
        df["COURSE"] = ""
        df["COLLEGE"] = ""

        # These Round1 quotas have only college in "ALLOTTED TO"
        df.loc[round1_college_only_mask, "COLLEGE"] = (
            df.loc[round1_college_only_mask, "ALLOTTED TO"].fillna("").astype(str).str.strip()
        )

        # Other rows may contain "COURSE<newline>COLLEGE" or "COURSE (...) COLLEGE"
        other_mask = ~round1_college_only_mask
        allotted_other = df.loc[other_mask, "ALLOTTED TO"].fillna("").astype(str)
        split_other = allotted_other.str.split(r"[\r\n]+", n=1, expand=True)

        if not split_other.empty:
            if 1 in split_other.columns:
                df.loc[other_mask, "COURSE"] = split_other[0].fillna("").str.strip()
                df.loc[other_mask, "COLLEGE"] = split_other[1].fillna("").str.strip()
            else:
                # Single-line fallback: "COURSE (...) COLLEGE,CITY"
                combined_parts = allotted_other.str.extract(r"^(?P<course>.*?\))\s+(?P<college>.+)$")
                df.loc[other_mask, "COURSE"] = combined_parts["course"].fillna(split_other[0]).str.strip()
                df.loc[other_mask, "COLLEGE"] = combined_parts["college"].fillna(allotted_other).str.strip()

        df = df.drop(columns=["ALLOTTED TO"])

    df["COLLEGE"] = (
        df["COLLEGE"]
        .fillna("")
        .astype(str)
        .str.replace(r"[\r\n]+", " ", regex=True)
        .str.replace(r"\s{2,}", " ", regex=True)
        .str.strip()
    )

    df["COURSE"] = (
        df["COURSE"]
        .fillna("")
        .astype(str)
        .str.replace(r"[\r\n]+", " ", regex=True)
        .str.replace(r"\s{2,}", " ", regex=True)
        .str.strip()
    )
    if "CATEGORY" in df.columns:
        df["CATEGORY"] = (
            df["CATEGORY"]
            .fillna("")
            .astype(str)
            .str.replace(r"[\r\n]+", " ", regex=True)
            .str.replace(r"\s{2,}", " ", regex=True)
            .str.strip()
        )

    # Enforce Round1 college-only convention for specific quotas.
    round1_course_only_mask = round1_college_only_mask & (df["COLLEGE"] == "") & (df["COURSE"] != "")
    df.loc[round1_course_only_mask, "COLLEGE"] = df.loc[round1_course_only_mask, "COURSE"]
    df.loc[round1_college_only_mask, "COURSE"] = ""
    df["COLLEGE_TYPE"] = ""

    other_mask = ~round1_college_only_mask
    course_parts = df.loc[other_mask, "COURSE"].str.extract(
        r"^(?P<course>[^(]+?)\s*\((?P<college_type>[^)]*)\)"
    )
    df.loc[other_mask, "COURSE"] = course_parts["course"].fillna(df.loc[other_mask, "COURSE"]).str.strip()
    df.loc[other_mask, "COLLEGE_TYPE"] = course_parts["college_type"].fillna("").str.strip()

    return df


def _extract_page_table(
    pdf_path: str,
    page_number: int,
    style: ParseStyle,
    round_name: str,
    quota: str = QUOTA,
    page_text: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    tables = tabula.read_pdf(
        pdf_path,
        pages=page_number,
        multiple_tables=True,
        lattice=style.lattice,
        stream=style.stream,
    )
    if not tables:
        return None
    if style.table_index >= len(tables):
        return None

    df = tables[style.table_index]
    if style.source_columns is None:
        df.columns = df.columns.str.strip()
    else:
        if len(df.columns) != len(style.source_columns):
            return None
        df.columns = style.source_columns

    keep_columns = style.keep_columns if style.keep_columns is not None else COMMON_COLUMNS
    df = df[[c for c in keep_columns if c in df.columns]]
    if "RANK" not in df.columns:
        return None

    df = df.dropna(subset=["RANK"]).copy()
    if df.empty:
        return None

    df["RANK"] = pd.to_numeric(df["RANK"], errors="coerce")
    if "ALLOTTED TO" not in df.columns:
        if "COLLEGE ALLOTTED" in df.columns:
            df["ALLOTTED TO"] = df["COLLEGE ALLOTTED"]
            df = df.drop(columns=["COLLEGE ALLOTTED"])
        elif style.extract_college_from_text:
            df["ALLOTTED TO"] = extract_college_name(page_text or "")

    return _add_common_metadata(df, round_name, quota=quota)


def parse_pdf_with_style(
    pdf_path: str, round_name: str, style: ParseStyle, quota: str = QUOTA
) -> pd.DataFrame:
    reader = PdfReader(pdf_path)
    all_data: list[pd.DataFrame] = []
    label = _pdf_label(pdf_path)
    pdf_total_rows = 0

    for page_index in range(style.start_page, len(reader.pages) + 1):
        page_text = reader.pages[page_index - 1].extract_text() if style.extract_college_from_text else None
        df = _extract_page_table(
            pdf_path,
            page_index,
            style=style,
            round_name=round_name,
            quota=quota,
            page_text=page_text,
        )
        if df is None:
            print(f"[{label}] Page {page_index}: +0 rows")
        else:
            all_data.append(df)
            page_rows = len(df)
            pdf_total_rows += page_rows
            print(f"[{label}] Page {page_index}: +{page_rows} rows")

    print(f"[{label}] PDF total added rows: {pdf_total_rows}")

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def load_or_parse(
    pdf_path: str,
    round_name: str,
    style: ParseStyle,
    quota: str = QUOTA,
) -> pd.DataFrame:
    pickle_path = _cache_path_from_pdf(pdf_path)
    pdf_mtime = os.path.getmtime(pdf_path)
    label = _pdf_label(pdf_path)

    if os.path.exists(pickle_path):
        pkl_mtime = os.path.getmtime(pickle_path)
        if pkl_mtime >= pdf_mtime:
            print("Loading data from pickle")
            with open(pickle_path, "rb") as f:
                df = pickle.load(f)
                print(f"[{label}] PDF total rows (from cache): {len(df)}")
                return df

    print("Parsing PDF (cache miss or outdated)")

    df = parse_pdf_with_style(pdf_path, round_name, style=style, quota=quota)

    df = _post_process_allotted_to(df)
    print(f"[{label}] PDF total rows (final): {len(df)}")

    os.makedirs(os.path.dirname(pickle_path), exist_ok=True)
    with open(pickle_path, "wb") as f:
        pickle.dump(df, f)

    return df


def get_datasets() -> list[tuple[str, str, str, ParseStyle, str]]:
    return [
        (
            "Reading Round1 7.5% Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\7p5 reservation round 1.pdf",
            "Round1",
            STYLE_ROUND1_TABLE0,
            QUOTA,
        ),
        (
            "Reading Round2 7.5% Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\7p5 reservation round 2.pdf",
            "Round2",
            STYLE_DEFAULT,
            QUOTA,
        ),
        (
            "Reading Round3 7.5% Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\7p5 reservation round 3.pdf",
            "Round3",
            STYLE_DEFAULT,
            QUOTA,
        ),
        (
            "Reading Round4 7.5% Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\7p5 reservation round 4.pdf",
            "Round4",
            STYLE_ROUND4,
            QUOTA,
        ),
        (
            "Reading Round5 7.5% Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\7p5 reservation round 5.pdf",
            "Round5",
            STYLE_ROUND5,
            QUOTA,
        ),
        (
            "Reading Round1 Ex-Servicemen Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\exservicemen category round 1.pdf",
            "Round1",
            STYLE_ROUND1_TABLE1,
            "EXSRVC",
        ),
        (
            "Reading Round1 PWD Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\pwd category round 1.pdf",
            "Round1",
            STYLE_ROUND1_TABLE1,
            "PWD",
        ),
        (
            "Reading Round1 Sports Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\sports category round 1.pdf",
            "Round1",
            STYLE_ROUND1_TABLE1,
            "SPORTS",
        ),
        (
            "Reading Round1 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 1.pdf",
            "Round1",
            STYLE_GOVT_ROUND1,
            "GOVT",
        ),
        (
            "Reading Round2 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 2.pdf",
            "Round2",
            STYLE_GOVT_DEFAULT,
            "GOVT",
        ),
        (
            "Reading Round3 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 3.pdf",
            "Round3",
            STYLE_GOVT_DEFAULT,
            "GOVT",
        ),
        (
            "Reading Round4 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 4.pdf",
            "Round4",
            STYLE_ROUND4,
            "GOVT",
        ),
        (
            "Reading Round5 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 5.pdf",
            "Round5",
            STYLE_ROUND5,
            "GOVT",
        ),
        (
            "Reading Round6 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 6.pdf",
            "Round6",
            STYLE_ROUND5,
            "GOVT",
        ),
        (
            "Reading Round7 Govt Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\govt round 7.pdf",
            "Round7",
            STYLE_ROUND5,
            "GOVT",
        ),
        (
            "Reading Round1 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 1.pdf",
            "Round1",
            STYLE_GOVT_ROUND1,
            "MGMT",
        ),
        (
            "Reading Round2 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 2.pdf",
            "Round2",
            STYLE_MGMT_DEFAULT,
            "MGMT",
        ),
        (
            "Reading Round3 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 3.pdf",
            "Round3",
            STYLE_MGMT_DEFAULT,
            "MGMT",
        ),
        (
            "Reading Round4 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 4.pdf",
            "Round4",
            STYLE_GOVT_ROUND1,
            "MGMT",
        ),
        (
            "Reading Round5 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 5.pdf",
            "Round5",
            STYLE_ROUND5,
            "MGMT",
        ),
        (
            "Reading Round6 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 6.pdf",
            "Round6",
            STYLE_ROUND5,
            "MGMT",
        ),            
        (
            "Reading Round7 Management Quota Allotment",
            r"C:\Users\chara\OneDrive\Desktop\TN NEET RESULTS\mgmt round 7.pdf",
            "Round7",
            STYLE_ROUND5,
            "MGMT",
        ),
    ]


def build_master_dataframe() -> pd.DataFrame:
    datasets = get_datasets()
    frames: list[pd.DataFrame] = []
    for message, pdf_path, round_name, style, quota in datasets:
        print(message)
        frame = load_or_parse(
            pdf_path,
            round_name,
            style=style,
            quota=quota,
        )
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    df_non_round1_course_college = (
        df.loc[df["ROUND"] != "Round1", ["COLLEGE", "COLLEGE_TYPE", "COURSE"]].copy()
    )
    college_city_parts = df_non_round1_course_college["COLLEGE"].str.split(",", n=1, expand=True)
    if 1 in college_city_parts.columns:
        df_non_round1_course_college["CITY"] = college_city_parts[1].fillna("").str.strip()
    else:
        df_non_round1_course_college["CITY"] = ""

    # Backfill missing COURSE and COLLEGE_TYPE in master df using non-Round1 reference rows.
    reference_pairs = (
        df_non_round1_course_college.loc[
            (df_non_round1_course_college["COURSE"] != "")
            | (df_non_round1_course_college["COLLEGE_TYPE"] != ""),
            ["COLLEGE", "COURSE", "COLLEGE_TYPE"],
        ]
        .groupby(["COLLEGE", "COURSE", "COLLEGE_TYPE"], dropna=False)
        .size()
        .reset_index(name="COUNT")
        .sort_values(["COLLEGE", "COUNT"], ascending=[True, False])
        .drop_duplicates(subset=["COLLEGE"], keep="first")
    )
    course_map = reference_pairs.set_index("COLLEGE")["COURSE"]
    college_type_map = reference_pairs.set_index("COLLEGE")["COLLEGE_TYPE"]

    missing_course_mask = df["COURSE"].fillna("").str.strip() == ""
    df.loc[missing_course_mask, "COURSE"] = (
        df.loc[missing_course_mask, "COLLEGE"].map(course_map).fillna(df.loc[missing_course_mask, "COURSE"])
    )

    missing_college_type_mask = df["COLLEGE_TYPE"].fillna("").str.strip() == ""
    df.loc[missing_college_type_mask, "COLLEGE_TYPE"] = (
        df.loc[missing_college_type_mask, "COLLEGE"]
        .map(college_type_map)
        .fillna(df.loc[missing_college_type_mask, "COLLEGE_TYPE"])
    )

    if {"CATEGORY", "QUOTA"}.issubset(df.columns):
        govt_missing_category_mask = (
            df["QUOTA"].ne("MGMT")
            & (
                df["CATEGORY"].fillna("").astype(str).str.strip().eq("")
                | df["CATEGORY"].fillna("").astype(str).str.strip().str.lower().eq("nan")
            )
        )
        df.loc[govt_missing_category_mask, "CATEGORY"] = "Government Quota"
        mgmt_missing_category_mask = (
            df["QUOTA"].eq("MGMT")
            & (
                df["CATEGORY"].fillna("").astype(str).str.strip().eq("")
                | df["CATEGORY"].fillna("").astype(str).str.strip().str.lower().eq("nan")
            )
        )
        df.loc[mgmt_missing_category_mask, "CATEGORY"] = "Management Quota"

    if {"CATEGORY", "ROUND", "QUOTA"}.issubset(df.columns):
        category_text = df["CATEGORY"].fillna("").astype(str).str.strip()
        empty_category_mask = category_text.eq("") | category_text.str.lower().eq("nan")
        print("ROUND and QUOTA for empty CATEGORY:")
        print(df.loc[empty_category_mask, ["ROUND", "QUOTA"]].value_counts().sort_index())

    if "COURSE" in df.columns:
        df["COURSE"] = df["COURSE"].fillna("").astype(str).str.strip()
        df["COURSE"] = df["COURSE"].replace(
            {
                r"^\*\s*MBBS$": "MBBS",
                r"^\*\s*BDS$": "BDS",
                r"^[A-Za-z0-9]+_\s*MBBS$": "MBBS",
                r"^[A-Za-z0-9]+_\s*BDS$": "BDS",
            },
            regex=True,
        )

    print(df[df.COLLEGE_TYPE=="Private"][["ROUND", "QUOTA"]].value_counts())
    return df


def main() -> None:


    df = build_master_dataframe()
    print(f"Built dataframe rows: {len(df)}")

if __name__ == "__main__":
    main()
