#!/usr/bin/env python3

import sys
import re
from pathlib import Path
import pandas as pd

input_file  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pg_catalog.csv")
output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.parent / "cleaned_catalog.csv"

df = pd.read_csv(input_file)
original_len = len(df)

df["Title"] = (
    df["Title"]
    .str.replace("\r\n", " ", regex=False)
    .str.replace("\n",   " ", regex=False)
    .str.replace(r"  +", " ", regex=True)
    .str.strip()
)

df["Issued"] = pd.to_datetime(df["Issued"], errors="coerce")
df = df.sort_values("Issued", ascending=False)
before_dedup = len(df)
df = df.drop_duplicates(subset=["Title", "Authors"], keep="first")
dedup_removed = before_dedup - len(df)
df["Issued"] = df["Issued"].dt.strftime("%Y-%m-%d")

def clean_author_dates(s: str) -> str:
    if pd.isna(s):
        return s
    s = re.sub(r",\s*\d{4}\??\s*BCE?[-–]\d{4}\??\s*BCE?", "", s)
    s = re.sub(r",\s*\d{4}\??\s*BCE?", "", s)
    s = re.sub(r",\s*\d{3,4}\??\s*[-–]\d{3,4}\??\s*(\[)", r" \1", s)
    s = re.sub(r",\s*\d{3,4}\??\s*[-–]\d{3,4}\??", "", s)
    s = re.sub(r",\s*\d{3,4}\??\s*-?\s*$", "", s)
    return s.strip().rstrip(",").strip()

df["Authors_clean"] = df["Authors"].apply(clean_author_dates)

def clean_special_chars(s: str) -> str:
    if pd.isna(s):
        return s
    s = s.replace("\u2018", "'").replace("\u2019", "'").replace("\u201a", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u201e", '"')
    s = s.replace("\u2014", "").replace("\u2013", "")
    s = s.replace("\u2026", "...")
    s = s.replace("'", "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    s = re.sub(r"  +", " ", s).strip()
    return s

text_cols = ["Title", "Authors", "Authors_clean", "Subjects", "LoCC", "Bookshelves"]
for col in text_cols:
    df[col] = df[col].apply(clean_special_chars)

for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip()

cols_ordered = ["Text#", "Type", "Issued", "Title", "Language",
                "Authors", "Authors_clean", "Subjects", "LoCC", "Bookshelves"]
df = df[cols_ordered].sort_values("Text#").reset_index(drop=True)
df.to_csv(output_file, index=False, encoding="utf-8")
