import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from deep_translator import GoogleTranslator
import time

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

def get_articles():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    translator = GoogleTranslator(source='auto', target='fr')
    date_now = datetime.now().strftime("%d/%m")
    
    print("Récupération et traduction en cours (soyez patient)...")
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
                    title = a.get_text().strip()
                    if len(title) > 30 and "facebook.com" not in url:
                        # Chercher un petit résumé autour du lien
                        parent = a.find_parent(['div', 'li', 'section', 'article'])
                        desc = ""
                        if parent:
                            p_tag = parent.find('p')
                            if p_tag: desc = p_tag.get_text().strip()[:150]
                        temp_list.append({"title": title, "link": url, "desc": desc})
            
            count = 0
            for item in temp_list:
                if count >= 10: break # Limite pour la vitesse de traduction
                if item["link"] not in articles:
                    try:
                        trad_title = translator.translate(item["title"])
                        trad_desc = translator.translate(item["desc"]) if len(item["desc"]) > 10 else ""
                        articles[item["link"]] = {
                            "title": trad_title, "desc": trad_desc, "orig": item["title"],
                            "link": item["link"], "source": src["name"], "date": date_now
                        }
                        count += 1
                        time.sleep(0.1) # Pause pour éviter d'être bloqué
                    except: continue
        except: print(f"Erreur: {src['name']}")
    return list(articles.values())

def main():
    data = get_articles()
    now_full = datetime.now().strftime("%d/%m %H:%M")
    sources_names = sorted(list(set(a['source'] for a in data)))
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>Veille Japon - FR</title><style>")
        f.write("body { font-family: sans-serif; background: #f4f7f6; margin: 0; padding: 15px; color: #333; }")
        f.write(".header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); position: sticky; top: 10px; z-index: 100; margin-bottom: 20px; }")
        f.write(".filters { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }")
        f.write(".btn { padding: 8px 14px; border-radius: 8px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 0.8rem; font-weight: 600; }")
        f.write(".btn.active { background: #1a73e8; color: white; border-color: #1a73e8; }")
        f.write(".btn-smart { background: #34a853; color: white; border: none; }")
        f.write(".btn-util { background: #f8f9fa; color: #5f6368; border: 1px solid #ddd; font-size: 0.7rem; }")
        f.write(".article { background: white; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); border-top: 4px solid #1a73e8; }")
        f.write(".hidden { display: none; }")
        f.write(".meta { font-size: 0.75rem; color: #1a73e8; font-weight: bold; margin-bottom: 8px; display: flex; justify-content: space-between; }")
        f.write(".badge { background: #fbbc04; color: #000; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: bold; margin-top: 10px; display: inline-block; }")
        f.write("a { text-decoration: none; color: #202124; font-weight: 700; display: block; font-size: 1.25rem; line-height: 1.3; margin-bottom: 10px; }")
        f.write(".summary { font-size: 0.95rem; color: #5f6368; line-height: 1.5; margin-bottom: 10px; }")
        f.write(".orig { font-size: 0.7rem; color: #9aa0a6; font-style: italic; border-top: 1px solid #eee; padding-top: 5px; }")
        f.write("#search { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #ddd; font-size: 1rem; box-sizing: border-box; }")
        f.write("</style></head><body>")

        f.write("<div class='header'><h1>🇫🇷 Veille Japon</h1>")
        f.write(f"<div style='font-size:0.8rem; color:#888;'>Actualisé le {now_full}</div>")
        f.write("<input type='text' id='search' placeholder='Rechercher dans les titres et résumés...' onkeyup='filter()'>")
        f.write("<div class='filters'><button class='btn btn-smart' id='smBtn' onclick='tgSm()'>Regroupement : ON</button>")
        f.write("<button class='btn btn-util' onclick='mass(true)'>TOUT COCHER</button>")
        f.write("<button class='btn btn-util' onclick='mass(false)'>TOUT DÉCOCHER</button></div>")
        f.write("<div class='filters' id='srcFilters'>")
        for s in sources_names:
            f.write(f"<button class='btn active filter-src' onclick='toggleSrc(\"{s}\", this)'>{s.upper()}</button>")
        f.write("</div></div><div id='feed'>")

        for a in data:
            title_js = a['title'].replace("'", " ").replace('"', ' ')
            f.write(f"<div class='article' data-src='{a['source']}' data-title='{title_js}'>")
            f.write(f"<div class='meta'><span>{a['source'].upper()}</span><span>{a['date']}</span></div>")
            f.write(f"<a href='{a['link']}' target='_blank'>{a['title']}</a>")
            if a['desc']: f.write(f"<div class='summary'>{a['desc']}</div>")
            f.write(f"<div class='orig'>{a['orig']}</div><div class='ex'></div></div>")
        
        f.write("</div><script>")
        f.write("let activeSrcs = new Set(" + str(sources_names).replace("[","['").replace("]","']").replace(", ","','") + "); let sm = true;")
        f.write("function tgSm(){ sm=!sm; document.getElementById('smBtn').innerText='Regroupement : '+(sm?'ON':'OFF'); filter(); }")
        f.write("function toggleSrc(src, btn){ if(activeSrcs.has(src)){ activeSrcs.delete(src); btn.classList.remove('active'); } else { activeSrcs.add(src); btn.classList.add('active'); } filter(); }")
        f.write("function mass(val){ const btns = document.querySelectorAll('.filter-src'); btns.forEach(b => { const s = b.innerText.charAt(0) + b.innerText.slice(1).toLowerCase(); if(val){ activeSrcs.add(s); b.classList.add('active'); } else { activeSrcs.clear(); b.classList.remove('active'); } }); filter(); }")
        f.write("function getSim(s1, s2){ let x=new Set(s1.toLowerCase().split(' ')), y=new Set(s2.toLowerCase().split(' ')); let i=new Set([...x].filter(z=>y.has(z))); return i.size/Math.max(x.size,y.size); }")
        f.write("function filter(){ let q=document.getElementById('search').value.toLowerCase(); let arts=Array.from(document.querySelectorAll('.article'));")
        f.write("arts.forEach(a=>{ a.classList.remove('hidden'); a.querySelector('.ex').innerHTML=''; }); let seen=[];")
        f.write("arts.forEach(a=>{ let t=a.getAttribute('data-title'), s=a.getAttribute('data-src'), txt=a.innerText.toLowerCase();")
        f.write("let v=activeSrcs.has(s) && txt.includes(q);")
        f.write("if(v&&sm){ let d=seen.find(dupe=>getSim(dupe.t,t)>0.6); if(d){ v=false; d.e.querySelector('.ex').innerHTML='<span class=\"badge\">+ Sujet similaire</span>'; } else { seen.push({t:t,e:a}); } }")
        f.write("if(!v) a.classList.add('hidden'); }); } filter();")
        f.write("</script></body></html>")

if __name__ == "__main__":
    main()
