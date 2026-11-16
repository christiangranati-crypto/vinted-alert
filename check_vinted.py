import json
import os
import re
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.vinted.it/catalog?search_text=naruto%20shippuden%20ultimate%20ninja%20storm%203%20true%20despair"

SEEN_FILE = "seen.json"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()


def main():
    seen = load_seen()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        SEARCH_URL,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    page = response.text

    print("Status:", response.status_code)
    print("URL:", response.url)
    print("Pagina ricevuta:", len(page), "caratteri")

    # Vinted può restituire gli URL dentro JSON con gli slash codificati.
    normalized_page = page.replace("\\/", "/")

    print("items/ presenti:", normalized_page.count("/items/"))
    print("item presenti:", normalized_page.lower().count("item"))
    print("naruto presenti:", normalized_page.lower().count("naruto"))

    found = {}

    # Cerca gli URL degli annunci direttamente nella pagina.
    pattern = r'(?:https://www\.vinted\.it)?/items/(\d+)(?:-[^"\'<>\s\\]*)?'

    matches = re.findall(pattern, normalized_page)

    for item_id in matches:
        item_url = f"https://www.vinted.it/items/{item_id}"

        if item_id not in found:
            found[item_id] = item_url

    print(f"Annunci trovati: {len(found)}")

    new_items = []

    for item_id, item_url in found.items():
        if item_id not in seen:
            new_items.append((item_id, item_url))
            seen.add(item_id)

    for item_id, item_url in new_items:
        message = (
            "🚨 NUOVO ANNUNCIO VINTED\n\n"
            "Naruto Shippuden Ultimate Ninja Storm 3 True Despair\n\n"
            f"{item_url}"
        )

        send_telegram(message)

        print("Nuovo annuncio:", item_url)

    save_seen(seen)

    print(f"Nuovi annunci: {len(new_items)}")


if __name__ == "__main__":
    main()
