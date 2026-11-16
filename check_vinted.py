import json
import os
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

    soup = BeautifulSoup(response.text, "html.parser")

    print("Status:", response.status_code)
    print("URL:", response.url)
    print("Pagina ricevuta:", len(response.text), "caratteri")
    print("items/ presenti:", response.text.count("/items/"))
    print("item presenti:", response.text.lower().count("item"))
    print("naruto presenti:", response.text.lower().count("naruto"))

    found = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/items/" not in href:
            continue

        title = link.get_text(" ", strip=True)

        if not title:
            continue

        item_url = href

        if item_url.startswith("/"):
            item_url = "https://www.vinted.it" + item_url

        item_id = item_url.split("/items/")[-1].split("-")[0]

        found.add((item_id, title, item_url))

    new_items = []

    for item_id, title, item_url in found:
        if item_id not in seen:
            new_items.append((item_id, title, item_url))
            seen.add(item_id)

    for item_id, title, item_url in new_items:
        message = (
            "🚨 NUOVO ANNUNCIO VINTED\n\n"
            f"{title}\n\n"
            f"{item_url}"
        )

        send_telegram(message)

    save_seen(seen)

    print(f"Annunci trovati: {len(found)}")
    print(f"Nuovi annunci: {len(new_items)}")


if __name__ == "__main__":
    main()
