#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import pandas as pd
from data_loader import load_book, get_book_path
import re

CATALOG_FILE = Path(__file__).parent / "cleaned_catalog.csv"

def load_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        sys.exit(f"Missing Catalog File : {CATALOG_FILE}")
    return pd.read_csv(CATALOG_FILE, dtype={"Text#": int})

def get_info(book_id: int) -> dict:
    df = load_catalog()
    row = df[df["Text#"] == book_id]
    if row.empty:
        sys.exit(f"No book found with the ID : {book_id}.")
    row = row.iloc[0]
    return {
        "id":          str(row["Text#"]),
        "title":       str(row["Title"])       if pd.notna(row["Title"])       else "",
        "authors":     str(row["Authors"])     if pd.notna(row["Authors"])     else "",
        "bookshelves": str(row["Bookshelves"]) if pd.notna(row["Bookshelves"]) else "",
    }

def download_book(book_id: int) -> None:
    df = load_catalog()
    if df[df["Text#"] == book_id].empty:
        sys.exit(f"No book found with the ID {book_id} in the catalog.")
    try:
        load_book(book_id)
        print(f"Book Saved Successfuly : {get_book_path(book_id)}")
    except Exception as e:
        sys.exit(f"{e}")

def clean_text(text: str, lower: bool = False) -> str:
    start_marker = "*** START OF"
    end_marker   = "*** END OF"
    start = text.find(start_marker)
    end   = text.find(end_marker)
    if start != -1 and end != -1:
        text = text[text.find("\n", start) + 1 : end]

    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    if lower:
        text = text.lower()

    return text

def main():
    parser = argparse.ArgumentParser(
        description="Gutenberg Project Tools : info et download of the books.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples :\n"
            "  python tools.py --info 11\n"
            "  python tools.py --download 11\n"
            "  python tools.py --clean \"Some text here\"\n"
            "  python tools.py --clean \"Some text here\" --lower\n"
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--info",
        metavar="ID",
        type=int,
        help="Display the book informations (id, title, authors, bookshelves)",
    )
    group.add_argument(
        "--download",
        metavar="ID",
        type=int,
        help="Download the book in Plain Text UTF-8",
    )
    group.add_argument(
        "--clean",
        metavar="TEXT",
        type=str,
        help="Clean a text string (removes Gutenberg header/footer, normalizes spaces)",
    )
    parser.add_argument(
        "--lower",
        action="store_true",
        help="Lowercase the text (only used with --clean)",
    )

    args = parser.parse_args()

    if args.info is not None:
        info = get_info(args.info)
        print(info)

    elif args.download is not None:
        download_book(args.download)

    elif args.clean is not None:
        result = clean_text(args.clean, lower=args.lower)
        print(result)

if __name__ == "__main__":
    main()