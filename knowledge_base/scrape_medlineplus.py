# ============================================================
# MEDLINEPLUS SCRAPER
# ============================================================
# This script downloads plain-English medical information from
# MedlinePlus (U.S. National Library of Medicine) for the
# blood tests MedAgent supports. The content becomes the
# knowledge base for the RAG component.
#
# MedlinePlus content is public domain and free to use for
# academic purposes, which is why I chose it as my source.
# ============================================================

import requests
from bs4 import BeautifulSoup
import os
import time

# Where to save the downloaded content
OUTPUT_DIR = "knowledge_base/sources"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# List of tests + their MedlinePlus URLs.
# Manually collected to make sure each URL points to a real,
# high-quality article about that specific test.
TEST_SOURCES = {
    "haemoglobin": "https://medlineplus.gov/lab-tests/hemoglobin-test/",
    "wbc": "https://medlineplus.gov/lab-tests/white-blood-count-wbc/",
    "rbc": "https://medlineplus.gov/ency/article/003644.htm",
    "platelets": "https://medlineplus.gov/lab-tests/platelet-tests/",
    "haematocrit": "https://medlineplus.gov/lab-tests/hematocrit-test/",
    "alt": "https://medlineplus.gov/lab-tests/alt-blood-test/",
    "ast": "https://medlineplus.gov/lab-tests/ast-test/",
    "alp": "https://medlineplus.gov/lab-tests/alkaline-phosphatase/",
    "bilirubin": "https://medlineplus.gov/lab-tests/bilirubin-blood-test/",
    "albumin": "https://medlineplus.gov/lab-tests/albumin-blood-test/",
    "creatinine": "https://medlineplus.gov/lab-tests/creatinine-test/",
    "urea": "https://medlineplus.gov/lab-tests/bun-blood-urea-nitrogen/",
    "sodium": "https://medlineplus.gov/lab-tests/sodium-blood-test/",
    "potassium": "https://medlineplus.gov/lab-tests/potassium-blood-test/",
    "glucose": "https://medlineplus.gov/lab-tests/blood-glucose-test/",
    "hba1c": "https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/",
    "tsh": "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/",
    "cholesterol": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
    "hdl": "https://medlineplus.gov/ency/article/007810.htm",
    "ldl": "https://medlineplus.gov/ency/article/007811.htm",
    "triglycerides": "https://medlineplus.gov/lab-tests/triglycerides-test/",
}


def scrape_page(url):
    """Download a MedlinePlus page and extract the main article text."""
    # Pretend to be a normal browser so the site doesn't block us
    headers = {"User-Agent": "Mozilla/5.0 (Research Project)"}

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Crash loudly if the download failed

    # Parse the HTML into a searchable tree structure
    soup = BeautifulSoup(response.text, "html.parser")

    # MedlinePlus has two page layouts:
    # 1. lab-tests pages use <div id="mplus-content">
    # 2. encyclopedia pages use <article> or <div id="d-article">
    # Try each in turn.
    content_div = (
        soup.find("div", id="mplus-content")
        or soup.find("div", id="d-article")
        or soup.find("article")
        or soup.find("main")
    )

    if not content_div:
        return None

    # Extract clean text (strip HTML tags)
    text = content_div.get_text(separator="\n", strip=True)
    return text


def main():
    print(f"Scraping {len(TEST_SOURCES)} medical articles from MedlinePlus...\n")

    success_count = 0
    fail_count = 0

    for test_name, url in TEST_SOURCES.items():
        print(f"  Downloading: {test_name}...", end=" ")

        try:
            text = scrape_page(url)

            if text:
                # Save each article to its own text file
                filepath = os.path.join(OUTPUT_DIR, f"{test_name}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    # Write the source URL at the top for citation
                    f.write(f"SOURCE: {url}\n")
                    f.write(f"TEST: {test_name}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(text)

                print(f"OK ({len(text)} chars)")
                success_count += 1
            else:
                print("FAILED (no content found)")
                fail_count += 1

        except Exception as e:
            print(f"ERROR: {e}")
            fail_count += 1

        # Be polite - wait 1 second between requests
        # so we don't hammer MedlinePlus's servers
        time.sleep(1)

    print(f"\n{'=' * 50}")
    print(f"Done! Success: {success_count}, Failed: {fail_count}")
    print(f"All articles saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()