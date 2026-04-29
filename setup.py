#!/usr/bin/env python3
import subprocess
import sys
import ssl

def run(cmd: list[str], description: str) -> None:
    print(f"\n>>> {description}...")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"Error while : {description}", file=sys.stderr)
        sys.exit(1)
    print(f"[ok] {description}")

def install_nltk_data() -> None:
    print("\n>>> Downloading of NLTK...")
    import nltk
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        nltk.download("punkt_tab", quiet=False)
        print("[ok] Downloading of NLTK")
    except Exception as e:
        print(f"NLTK error : {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    print("----- Bookworm Installation... -----")
    run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        "Pip updating, setuptools ...",
    )
    run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Python libs Installation (requirements.txt)",
    )
    run(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
        "Spacy model downloading...",
    )
    install_nltk_data()
    print("\n----- Installation completed. You can use Bookworm with success : -----")

if __name__ == "__main__":
    main()