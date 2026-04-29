import re
import json
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_loader import load_book, clean_imports

CACHE_DIR  = Path("cache")
N_SECTIONS = 4
N_TOPICS   = 4
N_WORDS    = 10

def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _split_sections(text: str, n: int = N_SECTIONS) -> list[str]:
    words = text.split()
    if len(words) < n:
        raise ValueError(f"Text too short to split into {n} sections.")
    size = len(words) // n
    return [" ".join(words[i * size:(i + 1) * size]) for i in range(n)]

def _extract_topics(sections: list[str]) -> dict:
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5_000,
        min_df=1,
        ngram_range=(1, 1),
    )
    matrix = vectorizer.fit_transform(sections)

    nmf = NMF(n_components=N_TOPICS, random_state=42, max_iter=500)
    nmf.fit(matrix)

    vocab = vectorizer.get_feature_names_out()
    return {
        i + 1: [vocab[j] for j in row.argsort()[-N_WORDS:][::-1]]
        for i, row in enumerate(nmf.components_)
    }

def _cache_path(book_id: int) -> Path:
    return CACHE_DIR / f"{book_id}_topics.json"

def _read_cache(book_id: int) -> dict | None:
    path = _cache_path(book_id)
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {int(k): v for k, v in raw.items()}
    return None


def _write_cache(book_id: int, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _cache_path(book_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def topics(book_id: int) -> dict:
    cached = _read_cache(book_id)
    if cached is not None:
        return cached

    raw      = load_book(book_id)
    body     = clean_imports(raw)
    sections = _split_sections(_clean_text(body))
    result   = _extract_topics(sections)

    _write_cache(book_id, result)
    return result

if __name__ == "__main__":
    import pprint
    import argparse

    parser = argparse.ArgumentParser(description="Topic modeling for a Gutenberg book.")
    parser.add_argument("id", type=int, help="Gutenberg book ID")
    args = parser.parse_args()
    pprint.pprint(topics(args.id))