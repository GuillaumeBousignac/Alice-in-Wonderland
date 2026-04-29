import os
import requests

books_dir = "books"

def get_book_path(book_id: int) -> str:
    return os.path.join(books_dir, f"{book_id}.txt")

def download_book(book_id: int) -> str:
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        raise Exception(f"Error while downloading the book {book_id}")
    return response.text

def save_book(book_id: int, text: str) -> None:
    os.makedirs(books_dir, exist_ok=True)
    with open(get_book_path(book_id), "w", encoding="utf-8") as f:
        f.write(text)

def load_book(book_id: int) -> str:
    path = get_book_path(book_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"Book {book_id} not found locally — downloading...")
    text = download_book(book_id)
    text = clean_imports(text)
    save_book(book_id, text)
    print(f"Book {book_id} saved to {path}")
    return text

def clean_imports(text: str) -> str:
    start_marker = "*** START OF"
    end_marker   = "*** END OF"
    start = text.find(start_marker)
    end   = text.find(end_marker)
    if start != -1 and end != -1:
        return text[text.find("\n", start) + 1 : end]
    return text