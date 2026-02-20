import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

# CONFIGURATION DE VOS SOURCES
SOURCES = [
    {"name": "Mainichi", "url": "https://mainichi.jp/shakai/", "cat": "Shakai", "type": "html"},
    {"name": "Mainichi", "url": "https://mainichi.jp/incident/", "cat": "Incident", "type": "html"},
    {"name": "News On Japan", "url": "https://newsonjapan.com/html/newsdesk/Society_News/rss/index.xml", "cat": "Society", "type": "rss"},
    {"name": "Asahi AJW", "url": "https://www.asahi.com/ajw/travel/", "cat": "Travel", "type": "html"},
    {"name": "Ouest France", "url": "https://altselection.ouest-france.fr/asie/japon/", "cat": "Japon", "type": "html"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/culture/", "cat": "Culture", "type": "html"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/travel/", "cat": "Voyage", "type": "html"},
    {"name": "Japan Forward", "url": "https://japan-forward.com/category/culture/", "cat": "Culture", "type": "html"},
    {"name": "Japan Today", "url": "https://japantoday.com/category/national", "cat": "National", "type": "html"},
    {"name": "Sora News", "url": "https://soranews24.com/category/japan/", "cat": "Japon", "type": "html"},
]

def get_articles():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for src in SOURCES:
        try:
            if src["type"] == "rss":
                d = feedparser.parse(src["url"])
                for e in d.entries:
                    articles[e.link] = {"title": e.title, "link": e.link, "source": src["name"], "cat": src["cat"]}
            else:
                resp = requests.get(src["url"], headers=headers, timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    url = a['href']
                    if not url.startswith("http"):
                        base = "/".join(src["url"].split("/")[:3])
                        url = base + ("" if url.startswith("/") else "/") + url
                    
                    title = a.get_text().strip()
                    if len(title) > 25 and "/category/" not in url and "facebook.com" not in url:
                        if url not in articles:
                            articles[url] = {"title": title, "link": url, "source": src["name"], "cat": src["cat"]}
        except Exception as e:
            print(f"Erreur sur {src['name']}: {e}")
    return list(articles.values())

def generate_html(data):
    now = datetime.now().strftime("%d/%m %H:%M")
    
    # On prépare les boutons de catégories proprement pour éviter l'erreur de f-string
    cats = sorted(list(set(a['cat'] for a in data)))
    buttons_html = ""
    for c in cats:
        buttons_html += f'<button class="btn" onclick="setCat(\'{c}\', this)">{c.upper()}</button> '

    # On prépare la liste des articles
    articles_html = ""
    for a in data:
        articles_html += f"""
        <div class="article" data-cat="{a['cat']}" data-title="{a['title']}">
            <span class="tag">{a['cat']}</span><span class="src">{a['source']}</span>
            <a href="{a['link']}" target="_blank">{a['title']}</a>
            <div class="extra"></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veille Japon</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; color: #1c1e21; }}
        .header {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 10px; z-index: 100; margin-bottom: 20px; }}
        h1 {{ margin: 0 0 15px 0; font-size: 1.5rem; }}
        #search {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }}
        .filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }}
        .btn {{ padding: 8px 14px; border-radius: 20px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 0.85rem; }}
        .btn.active {{ background: #007bff; color: white; border-color: #007bff; }}
        .btn-smart {{ background: #28a745; color: white; border: none; font-weight: bold; }}
        .btn-smart.off {{ background: #6c757d; }}
        .article {{ background: white; padding: 15px; margin-bottom: 12px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #007bff; position: relative; }}
        .article.hidden {{ display: none; }}
        .tag {{ font-size: 0.7rem; font-weight: bold; color: #007bff; text-transform: uppercase; background: #e7f3ff; padding: 3px 8px; border-radius: 5px; margin-right: 8px; }}
        .src {{ font-size: 0.8rem; color: #65676b; }}
        a {{ text-decoration: none; color: #1c1e21; font-weight: 600; display: block; margin-top: 8px; font-size: 1.05rem; line-height: 1.4; }}
        .badge {{ display: inline-block; background: #ffc107; color: black; font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; font-weight: bold; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🇯🇵 Veille Japon</h1>
        <input type="text" id="search" placeholder="Recherche
