import feedparser
import json
import os
from datetime import datetime, timedelta, timezone
from googletrans import Translator
from dateutil import parser as date_parser

# Configuration
COUNTRY = "elsalvador"
RSS_FEEDS = {
    "Diario Co Latino": "https://www.diariocolatino.com/feed/",
    "Cronio": "https://croniosv.com/feed/",
    "Diario La Huella": "https://diariolahuella.com/feed/",
    "El Metropolitano": "https://elmetropolitanodigital.com/feed/",
    "El Salvador Times": "https://www.elsalvadortimes.com/rss/listado/",
    "Periodico Equilibrium": "https://www.periodicoequilibrium.com/feed/",
    "La Pagina": "https://lapagina.com.sv/feed/",
    "Ultima Hora SV": "https://ultimahora.sv/feed/"
}

CATEGORIES = ["Diplomacy", "Military", "Energy", "Economy", "Local Events"]
MAX_AGE_DAYS = 7
TARGET_PER_CAT = 20
FILE_PATH = f"docs/{COUNTRY}_news.json"

translator = Translator()

def get_category(text):
    text = text.lower()
    if any(w in text for w in ['canciller', 'embajador', 'relaciones', 'diplomacia', 'oea', 'onu']): return "Diplomacy"
    if any(w in text for w in ['fuerza armada', 'militar', 'soldado', 'seguridad', 'policía', 'pnc']): return "Military"
    if any(w in text for w in ['energía', 'electricidad', 'combustible', 'petróleo', 'geotérmica']): return "Energy"
    if any(w in text for w in ['economía', 'bitcoin', 'pib', 'hacienda', 'banco', 'comercio']): return "Economy"
    return "Local Events"

def fetch_and_process():
    if not os.path.exists("docs"):
        os.makedirs("docs")

    existing_data = []
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r') as f:
                existing_data = json.load(f)
        except:
            existing_data = []

    new_stories = []
    seen_urls = {s['url'] for s in existing_data}
    now = datetime.now(timezone.utc)

    for source_name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                pub_date = date_parser.parse(entry.published)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                if (now - pub_date).days > MAX_AGE_DAYS:
                    continue
                
                if entry.link not in seen_urls:
                    # Spanish (es) to English (en)
                    translated_title = translator.translate(entry.title, src='es', dest='en').text
                    
                    story = {
                        "title": translated_title,
                        "source": source_name,
                        "url": entry.link,
                        "published_date": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "category": get_category(entry.title + " " + getattr(entry, 'summary', ''))
                    }
                    new_stories.append(story)
                    seen_urls.add(entry.link)
            except:
                continue

    all_stories = new_stories + existing_data
    
    # Filter for age and deduplicate
    fresh_stories = []
    seen = set()
    for s in all_stories:
        dt = datetime.strptime(s['published_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if (now - dt).days <= MAX_AGE_DAYS and s['url'] not in seen:
            fresh_stories.append(s)
            seen.add(s['url'])

    fresh_stories.sort(key=lambda x: x['published_date'], reverse=True)

    final_output = []
    for cat in CATEGORIES:
        cat_group = [s for s in fresh_stories if s['category'] == cat][:TARGET_PER_CAT]
        final_output.extend(cat_group)

    with open(FILE_PATH, 'w') as f:
        json.dump(final_output, f, indent=4)

if __name__ == "__main__":
    fetch_and_process()
