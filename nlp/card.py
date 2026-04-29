import json
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp.lexdiv    import lexdiv
from nlp.topics    import topics
from nlp.entities  import entities
from nlp.summarize import summarize
from nlp.similar   import similar

CACHE_DIR    = Path("cache")
CATALOG_FILE = Path(__file__).resolve().parent.parent / "cleaned_catalog.csv"

def _get_info(book_id: int) -> dict:
    """Read book metadata from cleaned_catalog.csv."""
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(f"Catalog not found at {CATALOG_FILE}")

    df  = pd.read_csv(CATALOG_FILE, dtype={"Text#": int})
    row = df[df["Text#"] == book_id]

    if row.empty:
        raise ValueError(f"Book ID {book_id} not found in catalog.")

    row = row.iloc[0]
    return {
        "id":          str(row["Text#"]),
        "authors":     str(row["Authors"])     if pd.notna(row.get("Authors"))     else "",
        "bookshelves": str(row["Bookshelves"]) if pd.notna(row.get("Bookshelves")) else "",
    }

def _cache_path(book_id: int) -> Path:
    return CACHE_DIR / f"{book_id}_card.json"

def _read_cache(book_id: int) -> dict | None:
    path = _cache_path(book_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None

def _write_cache(book_id: int, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _cache_path(book_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def card(book_id: int) -> dict:
    cached = _read_cache(book_id)
    if cached is not None:
        return cached

    result = {
        "info":     _get_info(book_id),
        "lexdiv":   lexdiv(book_id),
        "topics":   topics(book_id),
        "entities": entities(book_id),
        "summary":  summarize(book_id),
        "similar":  similar(book_id),
    }

    _write_cache(book_id, result)
    return result

if __name__ == "__main__":
    import pprint, argparse

    parser = argparse.ArgumentParser(description="Full book card for a Gutenberg book.")
    parser.add_argument("id", type=int, help="Gutenberg book ID")
    args = parser.parse_args()
    pprint.pprint(card(args.id))