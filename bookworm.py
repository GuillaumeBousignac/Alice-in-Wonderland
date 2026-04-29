#!/usr/bin/env python3
import argparse
import sys
import pprint
from pathlib import Path
import pandas as pd
from nlp.lexdiv import lexdiv
from nlp.topics import topics
from nlp.entities import entities
from nlp.summarize import summarize
from nlp.similar import similar
from nlp.card import card
from nlp.find import find_by_title, find_by_category, find_by_author
from tools import get_info

from data_loader import load_book

CORPUS_IDS = [11, 12, 16, 55, 113, 120, 236, 108, 834, 863, 1661, 61262, 69087, 70114, 35, 36, 84, 159, 164, 345, 68283]

for book_id in CORPUS_IDS:
    load_book(book_id)

CATALOG_FILE = Path(__file__).parent / "cleaned_catalog.csv"

def _load_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        sys.exit(f"Error: catalog not found at {CATALOG_FILE}")
    return pd.read_csv(CATALOG_FILE, dtype={"Text#": int})

def _check_id(book_id: int) -> None:
    """Exit with a clear message if the ID is not in the catalog."""
    df = _load_catalog()
    if df[df["Text#"] == book_id].empty:
        sys.exit(
            f"Error: book ID {book_id} not found in cleaned_catalog.csv.\n"
            "Tip: check the ID on https://www.gutenberg.org"
        )

def _build_card(book_id: int) -> dict:
    info = get_info(book_id)
    return {
        "info": {
            "id":          info["id"],
            "authors":     info["authors"],
            "bookshelves": info["bookshelves"],
        },
        "lexdiv":   lexdiv(book_id),
        "topics":   topics(book_id),
        "entities": entities(book_id),
        "summary":  summarize(book_id),
        "similar":  similar(book_id),
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bookworm.py",
        description="NLP engine for Project Gutenberg books.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bookworm.py --lexdiv    11\n"
            "  python bookworm.py --topics    11\n"
            "  python bookworm.py --entities  11\n"
            "  python bookworm.py --summarize 11\n"
            "  python bookworm.py --similar   11\n"
            "  python bookworm.py --card      11\n"
            "  python bookworm.py --find --title      'Alice'\n"
            "  python bookworm.py --find --category   'science fiction'\n"
            "  python bookworm.py --find --author     'Lovecraft'\n"
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--lexdiv",
        metavar="ID",
        type=int,
        help="Lexical diversity metrics (tok, typ, hap, ttr, mwl, mwf)",
    )
    group.add_argument(
        "--topics",
        metavar="ID",
        type=int,
        help="Topic modeling — top 10 words per section (TF-IDF + NMF)",
    )
    group.add_argument(
        "--entities",
        metavar="ID",
        type=int,
        help="Named entity recognition — characters and locations (spaCy)",
    )
    group.add_argument(
        "--summarize",
        metavar="ID",
        type=int,
        help="Structured summary — metadata + chapter arc + opening sentences",
    )
    group.add_argument(
        "--similar",
        metavar="ID",
        type=int,
        help="5 most similar books, sorted by decreasing similarity (~60k catalog)",
    )
    group.add_argument(
        "--card",
        metavar="ID",
        type=int,
        help="Full book card — all metrics combined into one dict",
    )
    group.add_argument(
        "--find",
        action="store_true",
        help="Search in the Catalog"
    )

    parser.add_argument(
        "--title",
        metavar="TITLE",
        type=str,
        help="Search by Title"
    )
    parser.add_argument(
        "--category",
        metavar="CATEGORY",
        type=str,
        help="Search by Category"
    )
    parser.add_argument(
        "--author",
        metavar="AUTHOR",
        type=str,
        help="Search by Author"
    )

    args = parser.parse_args()

    try:
        if args.lexdiv is not None:
            pprint.pprint(lexdiv(args.lexdiv))
        elif args.topics is not None:
            pprint.pprint(topics(args.topics))
        elif args.entities is not None:
            pprint.pprint(entities(args.entities))
        elif args.summarize is not None:
            print(summarize(args.summarize))
        elif args.similar is not None:
            result = similar(args.similar)
            df     = _load_catalog()
            title  = df[df["Text#"] == args.similar].iloc[0]["Title"]
            print(f"\n5 books most similar to '{title}':")
            for i, t in enumerate(result, 1):
                print(f"  {i}. {t}")
        elif args.card is not None:
            pprint.pprint(_build_card(args.card), sort_dicts=False)
        elif args.find:
            if not any([args.title, args.category, args.author]):
                sys.exit(
                    "Error: --find requires one of: --title, --category, --author\n"
                    "Examples:\n"
                    "  python bookworm.py --find --title    'Alice'\n"
                    "  python bookworm.py --find --category 'science fiction'\n"
                    "  python bookworm.py --find --author   'Lovecraft'\n"
                )
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
            
            else:
                book_id = (
                    args.lexdiv    or args.topics   or args.entities or
                    args.summarize or args.similar  or args.card
                )
                _check_id(book_id)

                if args.lexdiv is not None:
                    pprint.pprint(lexdiv(args.lexdiv), sort_dicts=False)
                elif args.topics is not None:
                    pprint.pprint(topics(args.topics), sort_dicts=False)
                elif args.entities is not None:
                    pprint.pprint(entities(args.entities), sort_dicts=False)
                elif args.summarize is not None:
                    print(summarize(args.summarize))
                elif args.similar is not None:
                    result = similar(args.similar)
                    df     = _load_catalog()
                    title  = df[df["Text#"] == args.similar].iloc[0]["Title"]
                    print(f"\n5 books most similar to '{title}':")
                    for i, t in enumerate(result, 1):
                        print(f"  {i}. {t}")
                elif args.card is not None:
                    pprint.pprint(card(args.card), sort_dicts=False)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()