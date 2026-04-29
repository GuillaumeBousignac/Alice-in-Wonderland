import json
import sys
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CACHE_DIR    = Path("cache")
CATALOG_FILE = Path(__file__).resolve().parent.parent / "cleaned_catalog.csv"

def _load_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"Catalog not found at {CATALOG_FILE}.\n"
            "Make sure cleaned_catalog.csv is in the project root."
        )
    df = pd.read_csv(CATALOG_FILE, dtype={"Text#": int})
    df = df[(df["Language"] == "en") & (df["Type"] == "Text")].copy()
    return df.reset_index(drop=True)


def _build_metadata(row: pd.Series) -> str:
    parts = []
    for col in ("Subjects", "Bookshelves"):
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            cleaned = str(val).replace(";", " ").replace("--", " ")
            parts.append(cleaned)
    title = str(row.get("Title", ""))
    if title:
        parts.extend([title, title])
    return " ".join(parts)

def _get_corpus() -> tuple[list[int], object]:
    pkl = CACHE_DIR / "catalog_tfidf.pkl"

    if pkl.exists():
        with open(pkl, "rb") as f:
            ids, matrix = pickle.load(f)
        return ids, matrix

    print("Building metadata TF-IDF corpus from catalog (~60k books, first run)...")
    df    = _load_catalog()
    ids   = df["Text#"].tolist()
    texts = [_build_metadata(row) for _, row in df.iterrows()]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=20_000,
        sublinear_tf=True,
        ngram_range=(1, 2),
    )
    matrix = vectorizer.fit_transform(texts)

    CACHE_DIR.mkdir(exist_ok=True)
    with open(pkl, "wb") as f:
        pickle.dump((ids, matrix), f)

    print(f"Corpus cached ({len(ids)} books).\n")
    return ids, matrix

def _title_map() -> dict[int, str]:
    df = _load_catalog()
    return dict(zip(df["Text#"], df["Title"].fillna("Unknown")))


def similar(book_id: int, top_n: int = 5) -> list[str]:
    cache = CACHE_DIR / f"{book_id}_similar.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    ids, matrix = _get_corpus()

    if book_id not in ids:
        raise ValueError(
            f"Book ID {book_id} not found in the catalog.\n"
            "Check that cleaned_catalog.csv contains this ID."
        )

    idx    = ids.index(book_id)
    scores = cosine_similarity(matrix[idx], matrix).flatten()

    ranked = sorted(
        [(ids[i], float(scores[i])) for i in range(len(ids)) if ids[i] != book_id],
        key=lambda x: x[1],
        reverse=True,
    )

    titles = _title_map()
    result = [titles.get(bid, f"ID {bid}") for bid, _ in ranked[:top_n]]

    CACHE_DIR.mkdir(exist_ok=True)
    cache.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result