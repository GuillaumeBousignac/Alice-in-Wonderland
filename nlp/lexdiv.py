import re
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_loader import load_book, clean_imports

CACHE_DIR = Path("cache")

def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _tokenize(text: str) -> list[str]:
    return [w for w in text.split() if w]

def _compute(tokens: list[str]) -> dict:
    if not tokens:
        raise ValueError("The book appears to be empty after cleaning.")
    freq = Counter(tokens)
    tok  = len(tokens)
    typ  = len(freq)
    hap  = sum(1 for c in freq.values() if c == 1)
    return {
        "tok": tok,
        "typ": typ,
        "hap": hap,
        "ttr": round(typ / tok, 6),
        "mwl": round(sum(len(w) for w in tokens) / tok, 6),
        "mwf": round(tok / typ, 6),
    }

def _cache_path(book_id: int) -> Path:
    return CACHE_DIR / f"{book_id}_lexdiv.json"


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

def lexdiv(book_id: int) -> dict:
    cached = _read_cache(book_id)
    if cached is not None:
        return cached

    raw    = load_book(book_id)
    body   = clean_imports(raw)
    tokens = _tokenize(_clean_text(body))
    result = _compute(tokens)

    _write_cache(book_id, result)
    return result

if __name__ == "__main__":
    import pprint
    import argparse

    parser = argparse.ArgumentParser(description="Lexical diversity for a Gutenberg book.")
    parser.add_argument("id", type=int, help="Gutenberg book ID")
    args = parser.parse_args()
    pprint.pprint(lexdiv(args.id))