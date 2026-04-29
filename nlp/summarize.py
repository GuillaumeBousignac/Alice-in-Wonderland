import re
import json
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_loader import load_book, clean_imports

CACHE_DIR    = Path("cache")
CATALOG_FILE = Path(__file__).resolve().parent.parent / "cleaned_catalog.csv"

CHAPTER_PATTERNS = [
    re.compile(r"^CHAPTER\s+[IVXLCDM]+\.?\s*(.*)", re.MULTILINE),
    re.compile(r"^CHAPTER\s+\d+\.?\s*(.*)",         re.MULTILINE),
    re.compile(r"^Chapter\s+[IVXLCDM]+\.?\s*(.*)",  re.MULTILINE),
    re.compile(r"^Chapter\s+\d+\.?\s*(.*)",          re.MULTILINE),
    re.compile(r"^\s*[IVX]+\.\s+([A-Z][^\n]{3,50})$", re.MULTILINE),
]

def _clean_gutenberg(text: str) -> str:
    text = re.sub(r"_([^_\n]+)_", r"\1", text)
    text = re.sub(r"\[Illustration[^\]]*\]", "", text)
    text = re.sub(r"\*{2,}", "", text)
    text = re.sub(r"-{2,}", " ", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _get_metadata(book_id: int) -> dict:
    if not CATALOG_FILE.exists():
        return {"title": "", "author": "", "subjects": ""}

    df  = pd.read_csv(CATALOG_FILE, dtype={"Text#": int})
    row = df[df["Text#"] == book_id]
    if row.empty:
        return {"title": "", "author": "", "subjects": ""}

    row  = row.iloc[0]
    raw  = str(row.get("Subjects", "")) if pd.notna(row.get("Subjects")) else ""
    tags = [s.split("--")[0].strip() for s in raw.split(";") if s.strip()]
    tags = [t for t in tags if len(t) > 2][:3]

    return {
        "title":    str(row["Title"])         if pd.notna(row.get("Title"))         else "",
        "author":   str(row["Authors_clean"])  if pd.notna(row.get("Authors_clean")) else "",
        "subjects": ", ".join(tags),
    }

def _extract_chapters(text: str) -> list[dict]:
    matches = []
    for pattern in CHAPTER_PATTERNS:
        found = list(pattern.finditer(text))
        if len(found) >= 2:
            matches = found
            break

    if not matches:
        words = text.split()
        size  = max(len(words) // 4, 1)
        return [
            {"title": f"Part {i + 1}", "body": " ".join(words[i * size:(i + 1) * size])}
            for i in range(4)
        ]

    chapters = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body  = text[start:end].strip()
        if body:
            chapters.append({"title": title, "body": body})

    return chapters

def _first_sentence(body: str) -> str:
    body       = re.sub(r"\r\n", "\n", body)
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]

    target = ""
    for para in paragraphs:
        para_flat = re.sub(r"\s+", " ", para).strip()
        if len(para_flat.split()) >= 15:
            target = para_flat
            break

    if not target:
        target = re.sub(r"\s+", " ", body[:500]).strip()

    match = re.search(r"^(.+?[.!?])\s", target)
    if match:
        sentence = match.group(1).strip()
        if len(sentence.split()) >= 6 and not re.match(r"^[A-Z\s]{8,}$", sentence):
            return sentence

    words = target.split()
    return " ".join(words[:30]) + ("..." if len(words) > 30 else "")

def _build_summary(book_id: int, text: str) -> str:
    meta     = _get_metadata(book_id)
    clean    = _clean_gutenberg(text)
    chapters = _extract_chapters(clean)

    lines = []

    if meta["title"] and meta["author"]:
        intro = f"{meta['title']} by {meta['author']}"
        intro += f" is a work of {meta['subjects']}." if meta["subjects"] else "."
        lines.append(intro)

    titles = [c["title"] for c in chapters if c["title"]]
    if titles:
        shown = titles[:8]
        arc   = f"The story unfolds across {len(titles)} chapters: "
        arc  += ", ".join(f'"{t}"' for t in shown)
        arc  += f", and {len(titles) - 8} more." if len(titles) > 8 else "."
        lines.append(arc)

    for chapter in chapters[:4]:
        sentence = _first_sentence(chapter["body"])
        if not sentence:
            continue
        prefix = f'In "{chapter["title"]}": ' if chapter["title"] else ""
        lines.append(prefix + sentence)

    return " ".join(lines)

def _cache_path(book_id: int) -> Path:
    return CACHE_DIR / f"{book_id}_summarize.json"

def _read_cache(book_id: int) -> str | None:
    path = _cache_path(book_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None

def _write_cache(book_id: int, data: str) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _cache_path(book_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def summarize(book_id: int) -> str:
    cached = _read_cache(book_id)
    if cached is not None:
        return cached

    raw    = load_book(book_id)
    body   = clean_imports(raw)
    result = _build_summary(book_id, body)

    _write_cache(book_id, result)
    return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Structured summarization for a Gutenberg book."
    )
    parser.add_argument("id", type=int, help="Gutenberg book ID")
    args = parser.parse_args()
    print(summarize(args.id))