import os
import json
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# Sources françaises
SOURCES = {
    "CERT-FR - Alertes": "https://www.cert.ssi.gouv.fr/alerte/feed/",
    "CERT-FR - Avis": "https://www.cert.ssi.gouv.fr/avis/feed/",
    "CERT-FR - Actualités": "https://www.cert.ssi.gouv.fr/actualite/feed/",
}

SEEN_FILE = Path("seen.json")


def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    # On garde les 500 dernières annonces
    SEEN_FILE.write_text(
        json.dumps(list(seen)[-500:]),
        encoding="utf-8"
    )


def send_discord(title, link, source):
    message = {
        "username": "🛡️ CyberWatch FR",
        "embeds": [
            {
                "title": title[:256],
                "url": link,
                "description": (
                    "🇫🇷 Nouvelle publication cybersécurité\n\n"
                    f"**Source :** {source}\n\n"
                    "🔗 Clique sur le titre pour lire l'annonce."
                ),
                "footer": {
                    "text": "CyberWatch FR • Veille cybersécurité automatique"
                }
            }
        ]
    }

    data = json.dumps(message).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request) as response:
        print(f"Discord : {response.status}")


def get_items(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CyberWatchFR/1.0"}
    )

    with urllib.request.urlopen(request) as response:
        content = response.read()

    root = ET.fromstring(content)

    items = []

    for item in root.findall(".//item")[:10]:
        title = item.findtext("title")
        link = item.findtext("link")

        if title and link:
            items.append((title.strip(), link.strip()))

    return items


def main():
    if not WEBHOOK_URL:
        print("ERREUR : DISCORD_WEBHOOK introuvable.")
        return

    seen = load_seen()
    new_seen = set(seen)

    new_articles = []

    for source, url in SOURCES.items():
        try:
            articles = get_items(url)

            for title, link in articles:
                article_id = hashlib.sha256(
                    link.encode()
                ).
