import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

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
                    if len(title) > 25 and "/category/" not in url:
                        if url not in articles:
                            articles[url] = {"title": title, "link": url, "source": src["name"], "cat": src["cat"]}
        except Exception as e:
            print(f"Erreur sur {src['name']}")
    return list(articles.values())

def main():
    print("Démarrage du script...")
    data = get_articles()
    now = datetime.now().strftime("%d/%m %H:%M")
    cats = sorted(list(set(a['cat'] for a in data)))
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'>")
        f.write("<meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Veille Japon</title>")
        f.write("<style>")
        f.write("body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 15px; }")
        f.write(".header { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 10px; z-index: 100; margin-bottom: 20px; }")
        f.write(".filters { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }")
        f.write(".btn { padding: 8px 14px; border-radius: 20px; border: 1px solid #ddd; background: white; cursor: pointer; }")
        f.write(".btn.active { background: #007bff; color: white; }")
        f.write(".btn-smart { background: #28a745; color: white; border: none; font-weight: bold; }")
        f.write(".article { background: white; padding: 15px; margin-bottom: 12px; border-radius: 12px; border-left: 5px solid #007bff; position: relative; }")
        f.write(".hidden { display: none; }")
        f.write(".badge { background: #ffc107; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-top: 10px; display: inline-block; }")
        f.write("a { text-decoration: none; color: #1c1e21; font-weight: bold; display: block; margin-top: 10px; }")
        f.write("</style></head><body>")
        
        f.write("<div class='header'><h1>🇯🇵 Veille Japon</h1>")
        f.write(f"<div>Mise à jour : {now}</div>")
        f.write("<input type='text' id='search' placeholder='Rechercher...' style='width:100%;padding:10px;margin-top:10px;' onkeyup='filter()'>")
        f.write("<div class='filters'><button class='btn btn-smart' id='smBtn' onclick='tgSm()'>Regroupement : ON</button>")
        f.write("<button class='btn active' onclick='setCat(\"all\", this)'>TOUT</button>")
        for c in cats:
            f.write(f"<button class='btn' onclick='setCat(\"{c}\", this)'>{c.upper()}</button>")
        f.write("</div></div><div id='feed'>")
        
        for a in data:
            f.write(f"<div class='article' data-cat='{a['cat']}' data-title='{a['title'].replace(chr(39), chr(92)+chr(39))}'>")
            f.write(f"<span>{a['cat']} | {a['source']}</span>")
            f.write(f"<a href='{a['link']}' target='_blank'>{a['title']}</a><div class='ex'></div></div>")
        
        f.write("</div><script>")
        f.write("let cCat='all'; let sm=true;")
        f.write("function tgSm(){ sm=!sm; document.getElementById('smBtn').innerText='Regroupement : '+(sm?'ON':'OFF'); filter(); }")
        f.write("function setCat(c, b){ cCat=c; document.querySelectorAll('.btn').forEach(x=>x.classList.remove('active')); b.classList.add('active'); filter(); }")
        f.write("function getSim(s1, s2){ let x=new Set(s1.split('')), y=new Set(s2.split('')); let i=new Set([...x].filter(z=>y.has(z))); return i.size/Math.max(x.size,y.size); }")
        f.write("function filter(){ let q=document.getElementById('search').value.toLowerCase(); let arts=Array.from(document.querySelectorAll('.article'));")
        f.write("arts.forEach(a=>{ a.classList.remove('hidden'); a.querySelector('.ex').innerHTML=''; }); let seen=[];")
        f.write("arts.forEach(a=>{ let t=a.getAttribute('data-title'), c=a.getAttribute('data-cat');")
        f.write("let v=(cCat==='all'||c===cCat)&&t.toLowerCase().includes(q);")
        f.write("if(v&&sm){ let d=seen.find(s=>getSim(s.t,t)>0.6); if(d){ v=false; d.e.querySelector('.ex').innerHTML='<span class='+'badge'+'>+ Sujet similaire</span>'; } else { seen.push({t:t,e:a}); } }")
        f.write("if(!v) a.classList.add('hidden'); }); } filter();")
        f.write("</script></body></html>")
    print("Fichier index.html généré avec succès.")

if __name__ == "__main__":
    main()
