import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from deep_translator import GoogleTranslator
import time
import re
import json # Module indispensable pour la stabilité du JavaScript

# CONFIGURATION DES SOURCES
SOURCES = [
    {"name": "Mainichi", "url": "https://mainichi.jp/shakai/", "type": "html", "sel": "section.articlelist"},
    {"name": "Mainichi", "url": "https://mainichi.jp/incident/", "type": "html", "sel": "section.articlelist"},
    {"name": "News On Japan", "url": "https://newsonjapan.com/html/newsdesk/Society_News/rss/index.xml", "type": "rss"},
    {"name": "Asahi AJW", "url": "https://www.asahi.com/ajw/travel/", "type": "html", "sel": ".list-style-01"},
    {"name": "Ouest France", "url": "https://altselection.ouest-france.fr/asie/japon/", "type": "html", "sel": "main"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/culture/", "type": "html", "sel": "#main"},
    {"name": "Japan Forward", "url": "https://japan-forward.com/category/culture/", "type": "html", "sel": ".archive-content"},
    {"name": "Japan Today", "url": "https://japantoday.com/category/national", "type": "html", "sel": ".media-body"},
    {"name": "Sora News", "url": "https://soranews24.com/category/japan/", "type": "html", "sel": "#content"},
]

def clean_title(text):
    text = re.split(r'\d{4}/\d{1,2}/\d{1,2}', text)[0]
    text = re.split(r'\d+文字', text)[0]
    text = re.split(r' \d{1,2}日', text)[0]
    return text.strip()

def get_articles():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    translator = GoogleTranslator(source='auto', target='fr')
    date_now = datetime.now().strftime("%d/%m")
    
    for src in SOURCES:
        try:
            temp_list = []
            if src["type"] == "rss":
                d = feedparser.parse(src["url"])
                for e in d.entries[:10]:
                    summary = BeautifulSoup(e.summary, "html.parser").get_text()[:150] if 'summary' in e else ""
                    temp_list.append({"title": e.title, "link": e.link, "desc": summary})
            else:
                resp = requests.get(src["url"], headers=headers, timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")
                area = soup.select_one(src["sel"]) if "sel" in src else soup
                if not area: area = soup
                
                for a in area.find_all("a", href=True):
                    url = a['href']
                    if not url.startswith("http"):
                        base = "/".join(src["url"].split("/")[:3])
                        url = base + ("" if url.startswith("/") else "/") + url
                    raw_title = a.get_text().strip()
                    if len(raw_title) > 25:
                        cleaned = clean_title(raw_title)
                        parent = a.find_parent(['div', 'li', 'section', 'article'])
                        desc = ""
                        if parent:
                            p_tag = parent.find('p')
                            if p_tag: desc = p_tag.get_text().strip()[:180]
                        temp_list.append({"title": cleaned, "link": url, "desc": desc})
            
            count = 0
            for item in temp_list:
                if count >= 10: break
                if item["link"] not in articles:
                    try:
                        trad_title = translator.translate(item["title"])
                        trad_desc = translator.translate(item["desc"]) if len(item["desc"]) > 15 else ""
                        articles[item["link"]] = {
                            "title": trad_title, "desc": trad_desc, "orig": item["title"],
                            "link": item["link"], "source": src["name"], "date": date_now
                        }
                        count += 1
                        time.sleep(0.05)
                    except: continue
        except: print(f"Erreur: {src['name']}")
    return list(articles.values())

def main():
    data = get_articles()
    now_full = datetime.now().strftime("%d/%m %H:%M")
    sources_names = sorted(list(set(a['source'] for a in data)))
    
    # Transformation de la liste Python en texte JSON sécurisé pour JS
    sources_json = json.dumps(sources_names)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>Veille Japon - Stable</title><style>")
        f.write("body { font-family: system-ui, -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; color: #1c1e21; }")
        f.write(".header { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); position: sticky; top: 10px; z-index: 100; margin-bottom: 25px; }")
        f.write(".btn { padding: 10px 16px; border-radius: 10px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: 0.2s; margin: 2px; }")
        f.write(".btn.active { background: #1a73e8; color: white; border-color: #1a73e8; }")
        f.write(".btn-smart { background: #34a853; color: white; border: none; }")
        f.write(".btn-util { background: #6c757d; color: white; border: none; }")
        f.write(".article { background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-top: 5px solid #1a73e8; }")
        f.write(".hidden { display: none !important; }")
        f.write(".meta { font-size: 0.75rem; color: #1a73e8; font-weight: bold; margin-bottom: 15px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 8px; }")
        f.write("a { text-decoration: none; color: #000; font-weight: 800; display: block; font-size: 1.4rem; line-height: 1.25; margin-bottom: 12px; }")
        f.write(".summary { font-size: 1rem; color: #444; line-height: 1.6; margin-bottom: 15px; background: #f9f9f9; padding: 12px; border-radius: 8px; }")
        f.write(".orig { font-size: 0.75rem; color: #999; font-style: italic; }")
        f.write("#search { width: 100%; padding: 15px; margin: 15px 0; border-radius: 10px; border: 1px solid #ddd; font-size: 1rem; box-sizing: border-box; }")
        f.write(".badge { background: #ffd400; color: black; font-size: 0.7rem; padding: 3px 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; display: inline-block; }")
        f.write("</style></head><body>")

        f.write("<div class='header'><h1>🇯🇵 Veille Japon</h1>")
        f.write(f"<div style='font-size:0.8rem; color:#888;'>Mise à jour : {now_full}</div>")
        f.write("<input type='text' id='search' placeholder='Tapez un mot en français pour filtrer...' onkeyup='filter()'>")
        f.write("<div class='filters'><button class='btn btn-smart' id='smBtn' onclick='tgSm()'>Regroupement : ON</button>")
        f.write("<button class='btn btn-util' onclick='mass(true)'>TOUT COCHER</button>")
        f.write("<button class='btn btn-util' onclick='mass(false)'>DÉCOCHER</button></div>")
        f.write("<div class='filters' id='srcFilters' style='margin-top:10px;'>")
        for s in sources_names:
            # On utilise data-src pour éviter les problèmes de texte
            f.write(f"<button class='btn active filter-src' data-src='{s}' onclick='toggleSrc(\"{s}\", this)'>{s.upper()}</button>")
        f.write("</div></div><div id='feed'>")

        for a in data:
            # Sécurisation du titre pour le JS (remplace les guillemets)
            t_safe = a['title'].replace("'", " ").replace('"', ' ')
            f.write(f"<div class='article' data-src='{a['source']}' data-title='{t_safe}'>")
            f.write(f"<div class='meta'><span>{a['source'].upper()}</span><span>{a['date']}</span></div>")
            f.write(f"<a href='{a['link']}' target='_blank'>{a['title']}</a>")
            if a['desc']: f.write(f"<div class='summary'>{a['desc']}</div>")
            f.write(f"<div class='orig'>{a['orig']}</div><div class='ex'></div></div>")
        
        f.write("</div><script>")
        # On injecte la liste JSON proprement
        f.write(f"let activeSrcs = new Set({sources_json}); let sm = true;")
        
        f.write("function tgSm(){ sm=!sm; const b=document.getElementById('smBtn'); b.innerText='Regroupement : '+(sm?'ON':'OFF'); b.style.background=sm?'#34a853':'#6c757d'; filter(); }")
        
        f.write("function toggleSrc(src, btn){ if(activeSrcs.has(src)){ activeSrcs.delete(src); btn.classList.remove('active'); } else { activeSrcs.add(src); btn.classList.add('active'); } filter(); }")
        
        f.write("function mass(val){ const btns=document.querySelectorAll('.filter-src'); btns.forEach(b=>{ const s=b.getAttribute('data-src'); if(val){ activeSrcs.add(s); b.classList.add('active'); } else { activeSrcs.clear(); b.classList.remove('active'); } }); filter(); }")
        
        f.write("function getSim(s1, s2){ let x=new Set(s1.toLowerCase().split(' ')), y=new Set(s2.toLowerCase().split(' ')); let i=new Set([...x].filter(z=>y.has(z))); return i.size/Math.max(x.size,y.size); }")
        
        f.write("function filter(){ const q=document.getElementById('search').value.toLowerCase(); const arts=Array.from(document.querySelectorAll('.article'));")
        f.write("arts.forEach(a=>{ a.classList.remove('hidden'); a.querySelector('.ex').innerHTML=''; }); let seen=[];")
        f.write("arts.forEach(a=>{ const t=a.getAttribute('data-title'), s=a.getAttribute('data-src'), txt=a.innerText.toLowerCase();")
        f.write("let v=activeSrcs.has(s) && txt.includes(q);")
        f.write("if(v&&sm){ let d=seen.find(dupe=>getSim(dupe.t,t)>0.55); if(d){ v=false; d.e.querySelector('.ex').innerHTML='<span class=\"badge\">+ Sujet similaire</span>'; } else { seen.push({t:t,e:a}); } }")
        f.write("if(!v) a.classList.add('hidden'); }); }")
        
        f.write("window.onload = filter;")
        f.write("</script></body></html>")

if __name__ == "__main__":
    main()
