import re
import json
import sys
import subprocess
from pathlib import Path
import spacy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_loader import load_book

CACHE_DIR  = Path(__file__).resolve().parent.parent / "cache"
CHUNK_SIZE = 100_000

def _load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("spaCy model 'en_core_web_sm' not found. Downloading it now...")
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        return spacy.load("en_core_web_sm")

def _clean_text(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _is_valid_entity(name: str) -> bool:
    if len(name) < 2:
        return False
    if not name[0].isupper():
        return False
    if any(c.isdigit() for c in name):
        return False
    if re.search(r"[''`]", name):
        return False
    if re.search(r"[^a-zA-Z\s\-\.]", name):
        return False
    if name.isupper() and len(name) > 2:
        return False
    if len(name.split()) > 3:
        return False
    return True

def _extract_entities(text: str) -> dict:
    nlp        = _load_spacy_model()
    characters = set()
    locations  = set()

    for start in range(0, len(text), CHUNK_SIZE):
        chunk = text[start:start + CHUNK_SIZE]
        doc   = nlp(chunk)
        for ent in doc.ents:
            name = ent.text.strip()
            if not _is_valid_entity(name):
                continue
            if ent.label_ == "PERSON":
                characters.add(name)
            elif ent.label_ in ("GPE", "LOC"):
                locations.add(name)

    return {
        "characters": sorted(characters),
        "locations":  sorted(locations),
    }

def _cache_path(book_id: int) -> Path:
    return CACHE_DIR / f"{book_id}_entities.json"

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

def entities(book_id: int) -> dict:
    cached = _read_cache(book_id)
    if cached is not None:
        return cached

    text   = load_book(book_id)
    clean  = _clean_text(text)
    result = _extract_entities(clean)

    _write_cache(book_id, result)
    return result

if __name__ == "__main__":
    import pprint, argparse

    parser = argparse.ArgumentParser(description="Named entity recognition for a Gutenberg book.")
    parser.add_argument("id", type=int, help="Gutenberg book ID")
    args = parser.parse_args()
    pprint.pprint(entities(args.id))