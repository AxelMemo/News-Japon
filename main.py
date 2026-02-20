import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from deep_translator import GoogleTranslator
import time
import re
import json

# CONFIGURATION DES SOURCES
SOURCES = [
    {"name": "Mainichi", "url": "https://mainichi.jp/shakai/", "type": "html", "sel": "section.articlelist", "lang": "ja"},
    {"name": "Mainichi", "url": "https://mainichi.jp/incident/", "type": "html", "sel": "section.articlelist", "lang": "ja"},
    {"name": "News On Japan", "url": "https://newsonjapan.com/html/newsdesk/Society_News/rss/index.xml", "type": "rss", "lang": "en"},
    {"name": "Asahi AJW", "url": "https://www.asahi.com/ajw/travel/", "type": "html", "sel": ".list-style-01", "lang": "en"},
    {"name": "Ouest France", "url": "https://altselection.ouest-france.fr/asie/japon/", "type": "html", "sel": "main", "lang": "fr"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/culture/", "type": "html", "sel": "#main", "lang": "en"},
    {"name": "Japan Forward", "url": "https://japan-forward.com/category/culture/", "type": "html", "sel": ".archive-content", "lang": "en"},
    {"name": "Japan Today", "url": "https://japantoday.com/category/national", "type": "html", "sel": ".media-body", "lang": "en"},
    {"name": "Sora News", "url": "https://soranews24.com/category/japan/", "type": "html", "sel": "#content", "lang": "en"},
]

def clean_text_aggressive(text):
    """ Nettoyage profond pour éviter les résidus japonais et les bugs de traduction """
    if not text: return ""
    # Supprime les dates japonaises types 21/02 ou 2/21
    text = re.sub(r'\d{1,2}/\d{1,2}', '', text)
    # Supprime les heures types 07:00 ou 7:00
    text = re.sub(r'\d{1,2}:\d{2}', '', text)
    # Supprime les années types 2024, 2025, 2026
    text = re.sub(r'202\d', '', text)
    # Supprime les mentions spécifiques au Mainichi
    garbage = ["Illustré", "Avec illustrations", "有料記事", "写真付き", "図解あり", "文字", "文字数"]
    for word in garbage:
        text = text.replace(word, "")
    # Supprime les crochets japonais et parenthèses qui troublent Google Trad
    text = text.replace("「", "").replace("」", "").replace("（", "").replace("）", "").replace("(", "").replace(")", "")
    return text.strip()

def get_articles():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    # On crée deux traducteurs pour plus de précision
    translator_ja = GoogleTranslator(source='ja', target='fr')
    translator_auto = GoogleTranslator(source='auto', target='fr')
    
    date_now = datetime.now().strftime("%d/%m")
    
    print("Récupération avec nettoyage profond...")
    for src in SOURCES:
        try:
            temp_list = []
            if src["type"] == "rss":
                d = feedparser.parse(src["url"])
                for e in d.entries[:10]:
                    summary = BeautifulSoup(e.summary, "html.parser").get_text()[:180] if 'summary' in e else ""
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
                    if len(raw_title) > 20:
                        # On cherche le résumé
                        parent = a.find_parent(['div', 'li', 'section', 'article'])
                        desc = ""
                        if parent:
                            p_tag = parent.find(['p', 'span'], class_=re.compile(r'txt|summary|lead'))
                            if not p_tag: p_tag = parent.find('p')
                            if p_tag: desc = p_tag.get_text().strip()[:200]
                        
                        temp_list.append({"title": raw_title, "link": url, "desc": desc})
            
            # Phase de Traduction
            translator = translator_ja if src.get("lang") == "ja" else translator_auto
            
            count = 0
            for item in temp_list[:10]:
                if item["link"] not in articles:
                    try:
                        # NETTOYAGE AVANT TRADUCTION
                        clean_t = clean_text_aggressive(item["title"])
                        clean_d = clean_text_aggressive(item["desc"])
                        
                        if not clean_t: continue
                        
                        trad_t = translator.translate(clean_t)
                        trad_d = translator.translate(clean_d) if len(clean_d) > 10 else ""
                        
                        articles[item["link"]] = {
                            "title": trad_t, "desc": trad_d, "orig": item["title"],
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
    available_dates = sorted(list(set(a['date'] for a in data)), reverse=True)
    sources_json = json.dumps(sources_names)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>Veille Japon Pro</title><style>")
        f.write("body { font-family: system-ui, -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 10px; color: #1c1e21; }")
        f.write(".header { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); position: sticky; top: 10px; z-index: 100; margin-bottom: 20px; }")
        f.write("h1 { font-size: 1.4rem; margin: 0 0 10px 0; }")
        f.write(".filters-group { margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px; }")
        f.write(".label { font-size: 0.7rem; font-weight: bold; color: #65676b; display: block; margin-bottom: 5px; text-transform: uppercase; }")
        f.write(".btn { padding: 6px 12px; border-radius: 8px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 0.8rem; font-weight: 600; margin: 2px; }")
        f.write(".btn.active { background: #1a73e8; color: white; border-color: #1a73e8; }")
        f.write(".btn-smart { background: #34a853; color: white; border: none; }")
        f.write(".btn-util { background: #6c757d; color: white; border: none; }")
        f.write(".article { background: white; padding: 20px; margin-bottom: 15px; border-radius: 10px; border-top: 5px solid #1a73e8; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }")
        f.write(".hidden { display: none !important; }")
        f.write(".meta { font-size: 0.7rem; color: #1a73e8; font-weight: bold; margin-bottom: 10px; display: flex; justify-content: space-between; }")
        f.write("a { text-decoration: none; color: #000; font-weight: 800; display: block; font-size: 1.25rem; line-height: 1.3; margin-bottom: 10px; }")
        f.write(".summary { font-size: 0.95rem; color: #444; background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 10px; line-height: 1.5; }")
        f.write(".orig { font-size: 0.7rem; color: #bbb; font-style: italic; display: block; border-top: 1px solid #eee; padding-top: 5px; }")
        f.write("#search { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; box-sizing: border-box; font-size: 1rem; }")
        f.write(".badge { background: #ffd400; color: black; font-size: 0.7rem; padding: 3px 8px; border-radius: 5px; font-weight: bold; margin-top: 8px; display: inline-block; }")
        f.write(".btn-scope.active { background: #ffc107; color: black; border-color: #ffc107; }")
        f.write("</style></head><body>")

        f.write("<div class='header'><h1>🇯🇵 Veille Japon</h1>")
        f.write("<input type='text' id='search' placeholder='Rechercher...' onkeyup='filter()'>")
        
        f.write("<div class='filters-group'><span class='label'>Rechercher dans :</span>")
        f.write("<button class='btn btn-scope active' onclick='setScope(\"all\", this)'>TITRE + RÉSUMÉ</button>")
        f.write("<button class='btn btn-scope' onclick='setScope(\"title\", this)'>TITRE</button></div>")

        f.write("<div class='filters-group'><button class='btn btn-smart' id='smBtn' onclick='tgSm()'>Regroupement : ON</button>")
        f.write("<button class='btn btn-util' onclick='mass(true)'>TOUT COCHER</button>")
        f.write("<button class='btn btn-util' onclick='mass(false)'>TOUT DÉCOCHER</button></div>")
        
        f.write("<div class='filters-group'><span class='label'>Journaux :</span>")
        for s in sources_names:
            f.write(f"<button class='btn active filter-src' data-src='{s}' onclick='toggleSrc(\"{s}\", this)'>{s.upper()}</button>")
        f.write("</div>")
        
        f.write("<div class='filters-group'><span class='label'>Dates :</span>")
        f.write("<button class='btn active filter-date' onclick='setDate(\"all\", this)'>TOUTES</button>")
        for d in available_dates:
            f.write(f"<button class='btn filter-date' onclick='setDate(\"{d}\", this)'>{d}</button>")
        f.write("</div></div>")

        f.write("<div id='feed'>")
        for a in data:
            t_safe = a['title'].replace("'", " ").replace('"', ' ')
            d_safe = a['desc'].replace("'", " ").replace('"', ' ')
            f.write(f"<div class='article' data-src='{a['source']}' data-date='{a['date']}' data-title='{t_safe}' data-desc='{d_safe}'>")
            f.write(f"<div class='meta'><span>{a['source'].upper()}</span><span>{a['date']}</span></div>")
            f.write(f"<a href='{a['link']}' target='_blank'>{a['title']}</a>")
            if a['desc']: f.write(f"<div class='summary'>{a['desc']}</div>")
            f.write(f"<div class='orig'>{a['orig']}</div><div class='ex'></div></div>")
        
        f.write("</div><script>")
        f.write(f"let activeSrcs = new Set({sources_json}); let sm=true; let scope='all'; let selDate='all';")
        f.write("function tgSm(){ sm=!sm; const b=document.getElementById('smBtn'); b.innerText='Regroupement : '+(sm?'ON':'OFF'); b.style.background=sm?'#34a853':'#6c757d'; filter(); }")
        f.write("function setScope(s, btn){ scope=s; document.querySelectorAll('.btn-scope').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); filter(); }")
        f.write("function setDate(d, btn){ selDate=d; document.querySelectorAll('.filter-date').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); filter(); }")
        f.write("function toggleSrc(src, btn){ if(activeSrcs.has(src)){ activeSrcs.delete(src); btn.classList.remove('active'); } else { activeSrcs.add(src); btn.classList.add('active'); } filter(); }")
        f.write("function mass(val){ const btns=document.querySelectorAll('.filter-src'); btns.forEach(b=>{ const s=b.getAttribute('data-src'); if(val){ activeSrcs.add(s); b.classList.add('active'); } else { activeSrcs.clear(); b.classList.remove('active'); } }); filter(); }")
        f.write("function getSim(s1, s2){ let x=new Set(s1.toLowerCase().split(' ')), y=new Set(s2.toLowerCase().split(' ')); let i=new Set([...x].filter(z=>y.has(z))); return i.size/Math.max(x.size,y.size); }")
        f.write("function filter(){ const q=document.getElementById('search').value.toLowerCase(); const arts=Array.from(document.querySelectorAll('.article'));")
        f.write("arts.forEach(a=>{ a.classList.remove('hidden'); a.querySelector('.ex').innerHTML=''; }); let seen=[];")
        f.write("arts.forEach(a=>{ const t=a.getAttribute('data-title').toLowerCase(); const d=a.getAttribute('data-desc').toLowerCase(); const s=a.getAttribute('data-src'); const date=a.getAttribute('data-date');")
        f.write("let matchQ = false; if(scope==='all') matchQ = t.includes(q) || d.includes(q); else matchQ = t.includes(q);")
        f.write("let v = activeSrcs.has(s) && matchQ && (selDate==='all' || date===selDate);")
        f.write("if(v&&sm){ let dupe=seen.find(x=>getSim(x.t,t)>0.55); if(dupe){ v=false; dupe.e.querySelector('.ex').innerHTML='<span class=\"badge\">+ Sujet similaire</span>'; } else { seen.push({t:t,e:a}); } }")
        f.write("if(!v) a.classList.add('hidden'); }); } window.onload = filter;")
        f.write("</script></body></html>")

if __name__ == "__main__":
    main()
