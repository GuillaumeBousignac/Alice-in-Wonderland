import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CATALOG_FILE = Path(__file__).resolve().parent.parent / "cleaned_catalog.csv"
FUZZY_THRESHOLD = 0.5

def _load_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"Catalog not found at {CATALOG_FILE}.\n"
            "Run: python clean_data.py"
        )
    return pd.read_csv(CATALOG_FILE, dtype={"Text#": int})

def _row_to_info(row: pd.Series) -> dict:
    return {
        "id":          str(row["Text#"]),
        "title":       str(row["Title"])       if pd.notna(row.get("Title"))       else "",
        "authors":     str(row["Authors"])     if pd.notna(row.get("Authors"))     else "",
        "bookshelves": str(row["Bookshelves"]) if pd.notna(row.get("Bookshelves")) else "",
        "language":    str(row["Language"])    if pd.notna(row.get("Language"))    else "",
        "issued":      str(row["Issued"])      if pd.notna(row.get("Issued"))      else "",
    }

def _similarity(query: str, value: str) -> float:
    query = query.lower().strip()
    value = value.lower().strip()

    if not query or not value:
        return 0.0

    if query in value:
        return 1.0

    return SequenceMatcher(None, query, value).ratio()


def _fuzzy_filter(df: pd.DataFrame, column: str, query: str,
                threshold: float = FUZZY_THRESHOLD) -> pd.DataFrame:
    scores       = df[column].fillna("").astype(str).apply(lambda v: _similarity(query, v))
    df           = df.copy()
    df["_score"] = scores
    return df[df["_score"] >= threshold].sort_values("_score", ascending=False)

def find_by_title(title: str) -> dict:
    df      = _load_catalog()
    matches = _fuzzy_filter(df, "Title", title)

    if matches.empty:
        raise ValueError(
            f"No book found matching '{title}'.\n"
            "Try a shorter or different spelling."
        )

    return _row_to_info(matches.iloc[0])

def find_by_category(category: str, top_n: int = 15) -> list[dict]:
    df    = _load_catalog()
    query = category.strip()

    shelf_scores   = df["Bookshelves"].fillna("").astype(str).apply(lambda v: _similarity(query, v))
    subject_scores = df["Subjects"].fillna("").astype(str).apply(lambda v: _similarity(query, v))

    df           = df.copy()
    df["_score"] = shelf_scores.combine(subject_scores, max)
    matches      = df[df["_score"] >= FUZZY_THRESHOLD].sort_values("_score", ascending=False)

    if matches.empty:
        raise ValueError(
            f"No books found for category '{category}'.\n"
            "Try: 'science fiction', 'mystery', 'children', 'history'..."
        )

    return [_row_to_info(row) for _, row in matches.head(top_n).iterrows()]

def find_by_author(author: str) -> list[dict]:
    df      = _load_catalog()
    matches = _fuzzy_filter(df, "Authors", author)

    if matches.empty:
        raise ValueError(
            f"No books found for author '{author}'.\n"
            "Try last name only, e.g. 'Lovecraft', 'Carroll', 'Doyle'."
        )

    matches = matches.sort_values(["_score", "Issued"], ascending=[False, False])
    return [_row_to_info(row) for _, row in matches.iterrows()]

if __name__ == "__main__":
    import pprint
    import argparse

    parser = argparse.ArgumentParser(description="Search the Gutenberg catalog.")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title",    metavar="TITLE",    type=str, help="Search by title")
    group.add_argument("--category", metavar="CATEGORY", type=str, help="Search by category")
    group.add_argument("--author",   metavar="AUTHOR",   type=str, help="Search by author")
    args = parser.parse_args()

    try:
        if args.title:
            pprint.pprint(find_by_title(args.title), sort_dicts=False)
        elif args.category:
            results = find_by_category(args.category)
            print(f"\n{len(results)} books found for category '{args.category}':")
            for book in results:
                print(f"  [{book['id']}] {book['title']} — {book['authors']}")
        elif args.author:
            results = find_by_author(args.author)
            print(f"\n{len(results)} books found for author '{args.author}':")
            for book in results:
                print(f"  [{book['id']}] {book['title']} ({book['issued']})")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)