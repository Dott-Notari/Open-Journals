"""Ricognizione automatica di nuove testate, per scriverne i moduli.

Per ogni testata: robots.txt, sitemap (dichiarate e consuete), feed, piattaforma e protezioni,
e tre articoli campione presi automaticamente dalle sitemap o dalla home, analizzati per dati
strutturati, date, paywall e contenitore del testo."""
import json
import re
from datetime import date
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from . import comune as C
from .config import UA, radice_locale
from .rete import contenuto_xml

UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

CANDIDATE = {
    "ilpost": ("Il Post", "https://www.ilpost.it"),
    "fanpage": ("Fanpage", "https://www.fanpage.it"),
    "libero": ("Libero", "https://www.liberoquotidiano.it"),
    "manifesto": ("il manifesto", "https://ilmanifesto.it"),
    "mattino": ("Il Mattino", "https://www.ilmattino.it"),
    "corriere": ("Corriere della Sera", "https://www.corriere.it"),
    "repubblica": ("la Repubblica", "https://www.repubblica.it"),
    "lastampa": ("La Stampa", "https://www.lastampa.it"),
    "messaggero": ("Il Messaggero", "https://www.ilmessaggero.it"),
    "verita": ("La Verità", "https://www.laverita.info"),
    "sole24ore": ("Il Sole 24 Ore", "https://www.ilsole24ore.com"),
}
SITEMAP_CONSUETE = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/news-sitemap.xml",
                    "/sitemap_news.xml", "/sitemap-news.xml", "/sitemaps/sitemap-news.xml",
                    "/googlenews.xml", "/sitemap/news.xml"]
PAYWALL = re.compile(r"(abbonati|abbonamento|riservato agli abbonati|contenuto riservato|"
                     r"per continuare a leggere|sblocca|premium|paywall)", re.I)


class Sonda:
    def __init__(self, pausa=2.0):
        import time
        self.time, self.pausa, self.ultimo = time, pausa, 0.0
        self.s = requests.Session()

    def get(self, url, ua=UA):
        attesa = self.pausa - (self.time.monotonic() - self.ultimo)
        if attesa > 0:
            self.time.sleep(attesa)
        try:
            r = self.s.get(url, headers={"User-Agent": ua, "Accept-Language": "it-IT,it;q=0.9"},
                           timeout=30, allow_redirects=True)
        except requests.RequestException as e:
            r = None
            self.errore = str(e)[:150]
        self.ultimo = self.time.monotonic()
        return r


def bloccato(r):
    if r is None:
        return True
    t = r.text[:5000].lower()
    return r.status_code in (401, 403, 429, 503) or any(
        s in t for s in ("cf-chl", "just a moment", "captcha", "access denied", "request unsuccessful"))


def piattaforma(html):
    h = html.lower()
    for nome, segni in (("Arc XP", ("arcpublishing", "fusion-metadata", "/resizer/v2/")),
                        ("Nuxt", ("__nuxt", "/_nuxt/")), ("Next.js", ("__next_data__", "/_next/")),
                        ("WordPress", ("wp-content", "wp-json")), ("Drupal", ("drupal",)),
                        ("Méthode/Eidos", ("methode", "eidos")), ("Brightspot", ("brightspot",))):
        if any(s in h for s in segni):
            return nome
    return "non riconosciuta"


def cdn(r):
    chiavi = ("server", "via", "x-cache", "cf-ray", "x-amz-cf-id", "akamai-grn", "x-served-by",
              "x-azure-ref", "x-akamai-transformed")
    return {k: r.headers[k] for k in chiavi if k in r.headers}


def sitemap(sonda, url, profondita=1):
    r = sonda.get(url)
    if r is None or r.status_code != 200:
        return {"url": url, "stato": getattr(r, "status_code", "nessuna risposta")}
    try:
        dati = contenuto_xml(r)
        soup = BeautifulSoup(dati, "xml")
    except Exception as e:
        return {"url": url, "stato": 200, "tipo": f"illeggibile ({e.__class__.__name__})"}
    info = {"url": url, "stato": 200, "bloccato": bloccato(r)}
    if soup.find("sitemapindex"):
        figli = [s.loc.get_text(strip=True) for s in soup.find_all("sitemap") if s.loc]
        info.update(tipo="indice", voci=len(figli), primi=figli[:6], ultimi=figli[-3:],
                    per_data=sum(bool(re.search(r"(19|20)\d{2}[-/_]?\d{2}", f)) for f in figli))
        if profondita and figli:
            info["figli"] = [sitemap(sonda, u, 0) for u in dict.fromkeys([figli[0], figli[-1]])]
    elif soup.find("urlset"):
        voci = soup.find_all("url")
        testo = dati.decode("utf-8", "ignore")
        date_pub = re.findall(r"<(?:news:)?publication_date>([^<]+)<", testo)
        info.update(tipo="elenco", voci=len(voci),
                    esempi=[v.loc.get_text(strip=True) for v in voci[:4] if v.loc],
                    news=bool(date_pub), data_min=min(date_pub) if date_pub else "",
                    data_max=max(date_pub) if date_pub else "")
    elif soup.find("rss") or soup.find("feed"):
        info.update(tipo="feed", voci=len(soup.find_all(["item", "entry"])))
    else:
        info.update(tipo="sconosciuto", inizio=dati[:150].decode("utf-8", "ignore"))
    return info


def descrivi(el):
    parti = []
    while el is not None and getattr(el, "name", None) not in (None, "[document]", "body", "html") and len(parti) < 4:
        nome = el.name + (f"#{el.get('id')}" if el.get("id") else "") + \
            "".join(f".{c}" for c in (el.get("class") or [])[:3])
        parti.append(nome)
        el = el.parent
    return " < ".join(parti)


def contenitore_denso(soup):
    migliore, punti = None, 0
    for el in soup.find_all(["div", "section", "article", "main"]):
        tot = sum(len(p.get_text(strip=True)) for p in el.find_all("p", recursive=False)
                  if len(p.get_text(strip=True)) > 40)
        if tot > punti:
            migliore, punti = el, tot
    return (descrivi(migliore), punti) if migliore is not None else ("", 0)


def articolo(sonda, url):
    r = sonda.get(url, UA_BROWSER)
    r2 = sonda.get(url)
    info = {"url": url, "stato_browser": getattr(r, "status_code", None),
            "stato_ua_dichiarato": getattr(r2, "status_code", None),
            "bloccato_browser": bloccato(r), "bloccato_dichiarato": bloccato(r2)}
    if r is None or r.status_code != 200:
        return info
    soup = BeautifulSoup(r.text, "lxml")
    jl = C.json_ld(soup)
    h1 = soup.find("h1")
    titolo = h1.get_text(" ", strip=True) if h1 else ""
    par, metodo = C.corpo_trafilatura(r.text)
    testo = "\n".join(par)
    sel, punti = contenitore_denso(soup)
    tutto = soup.get_text(" ", strip=True)
    m_paywall = PAYWALL.findall(tutto)
    has_part = re.findall(r'"cssSelector"\s*:\s*"([^"]+)"', r.text)
    info.update(
        url_finale=r.url, piattaforma=piattaforma(r.text), cdn=cdn(r), h1=titolo,
        json_ld={k: (v if not isinstance(v, list) else v[:6]) for k, v in jl.items() if k != "descrizione"},
        meta_published=C.meta(soup, "article:published_time")[:1],
        meta_section=C.meta(soup, "article:section")[:1], meta_tag=C.meta(soup, "article:tag")[:6],
        descrizione=C.primo(C.meta(soup, "description"), C.meta(soup, "og:description"))[:160],
        data_nell_url=bool(C.data_da_url(url)),
        caratteri_trafilatura=len(testo), inizio_testo=testo[:220],
        coerenza=C.coerenza(titolo, "", testo),
        contenitore_denso=sel, caratteri_contenitore=punti,
        parole_paywall=sorted({p.lower() for p in m_paywall})[:8], paywall_css=has_part[:3],
    )
    return info


def campioni(sonda, base, sitemaps, home_html):
    """Tre URL di articoli: dalle sitemap con più voci, altrimenti dalla home."""
    urls = []
    for s in sitemaps:
        for f in [s] + s.get("figli", []):
            urls += f.get("esempi", [])
    if not urls and home_html:
        soup = BeautifulSoup(home_html, "lxml")
        dom = urlparse(base).netloc
        for a in soup.find_all("a", href=True):
            u = urljoin(base, a["href"]).split("#")[0].split("?")[0]
            p = urlparse(u)
            if dom in p.netloc and p.path.count("/") >= 2 and len(p.path) > 40 and \
                    (re.search(r"\d", p.path) or p.path.endswith((".html", ".shtml"))):
                urls.append(u)
    urls = [u for u in dict.fromkeys(urls) if not re.search(r"\.(jpg|png|xml|pdf)$", u)]
    return urls[:3]


def ricognisci(chiave, sonda, log):
    nome, base = CANDIDATE[chiave]
    R = {"nome": nome, "base": base}
    rb = sonda.get(base + "/robots.txt")
    dichiarate = []
    if rb is not None and rb.status_code == 200:
        rp = robotparser.RobotFileParser()
        rp.parse(rb.text.splitlines())
        dichiarate = rp.site_maps() or []
        R["robots"] = {"stato": 200, "sitemap": dichiarate[:15], "crawl_delay": rp.crawl_delay("*"),
                       "home_consentita": rp.can_fetch(UA, base + "/"),
                       "agenti": sorted({a.strip() for a in re.findall(r"(?im)^user-agent:\s*(.+)$", rb.text)})[:30]}
    else:
        R["robots"] = {"stato": getattr(rb, "status_code", "nessuna risposta")}
    log("    robots.txt")
    home = sonda.get(base + "/", UA_BROWSER)
    home2 = sonda.get(base + "/")
    R["home"] = {"stato_browser": getattr(home, "status_code", None),
                 "stato_ua_dichiarato": getattr(home2, "status_code", None),
                 "bloccato_dichiarato": bloccato(home2),
                 "piattaforma": piattaforma(home.text) if home is not None else "",
                 "cdn": cdn(home) if home is not None else {}}
    if home is not None and home.status_code == 200:
        soup = BeautifulSoup(home.text, "lxml")
        R["feed"] = [urljoin(base, l.get("href", "")) for l in soup.find_all("link", type=re.compile(r"rss|atom", re.I))][:5]
    candidati = list(dict.fromkeys(dichiarate[:6] + [base + s for s in SITEMAP_CONSUETE]))
    R["sitemap"] = []
    trovate = 0
    for u in candidati:
        s = sitemap(sonda, u)
        if s.get("stato") == 200 or u in dichiarate:
            R["sitemap"].append(s)
        trovate += s.get("stato") == 200
        if trovate >= 5:
            break
    log("    sitemap")
    R["articoli"] = [articolo(sonda, u) for u in campioni(sonda, base, R["sitemap"],
                                                           home.text if home is not None and home.status_code == 200 else "")]
    log("    articoli campione")
    return R


def report(R):
    L = [f"RICOGNIZIONE {R['nome']} ({R['base']})", "=" * 70]
    rb = R["robots"]
    L.append(f"robots.txt: {rb.get('stato')}  crawl-delay {rb.get('crawl_delay')}  home consentita {rb.get('home_consentita')}")
    for s in rb.get("sitemap", []):
        L.append(f"  sitemap dichiarata: {s}")
    h = R["home"]
    L.append(f"home: browser {h['stato_browser']}  UA dichiarato {h['stato_ua_dichiarato']} "
             f"(bloccato {h['bloccato_dichiarato']})  piattaforma {h['piattaforma']}  {h['cdn']}")
    for f in R.get("feed", []):
        L.append(f"  feed: {f}")
    L.append("SITEMAP")
    for s in R["sitemap"]:
        L.append(f"  {s['url']}  stato {s.get('stato')}  {s.get('tipo', '')}  voci {s.get('voci', '')}"
                 + (f"  per data {s.get('per_data')}" if s.get("tipo") == "indice" else "")
                 + (f"  news {s.get('news')} {s.get('data_min', '')[:10]}..{s.get('data_max', '')[:10]}" if s.get("tipo") == "elenco" else ""))
        for x in s.get("primi", [])[:4] + (["..."] if s.get("ultimi") else []) + s.get("ultimi", []):
            L.append(f"      {x}")
        for f in s.get("figli", []):
            L.append(f"    figlio {f['url']}  {f.get('tipo')}  voci {f.get('voci')}  news {f.get('news')} "
                     f"{f.get('data_min', '')[:10]}..{f.get('data_max', '')[:10]}")
            for x in f.get("esempi", [])[:2]:
                L.append(f"      {x}")
        for x in s.get("esempi", [])[:3]:
            L.append(f"      {x}")
    L.append("ARTICOLI CAMPIONE")
    for a in R["articoli"]:
        L.append(f"  {a['url']}")
        L.append(f"    stato browser {a['stato_browser']}  UA dichiarato {a['stato_ua_dichiarato']}  "
                 f"bloccato {a['bloccato_browser']}/{a['bloccato_dichiarato']}")
        if a.get("h1") is None:
            continue
        L += [f"    piattaforma {a['piattaforma']}  data nell'URL {a['data_nell_url']}",
              f"    h1: {a['h1'][:110]}",
              f"    JSON-LD: {json.dumps(a['json_ld'], ensure_ascii=False)[:400]}",
              f"    meta: pubbl {a['meta_published']}  sezione {a['meta_section']}  tag {a['meta_tag']}",
              f"    descrizione: {a['descrizione']}",
              f"    trafilatura {a['caratteri_trafilatura']} caratteri, coerenza {a['coerenza']}",
              f"    contenitore più denso ({a['caratteri_contenitore']} caratteri): {a['contenitore_denso']}",
              f"    parole di paywall nella pagina: {a['parole_paywall']}  selettori paywall JSON-LD: {a['paywall_css']}",
              f"    inizio: {a['inizio_testo'][:200]!r}"]
    return "\n".join(L) + "\n"


def esegui_ricognizione(chiavi=None, log=print):
    chiavi = chiavi or list(CANDIDATE)
    out = radice_locale() / "_ricognizione" / date.today().isoformat() / "nuove_testate"
    out.mkdir(parents=True, exist_ok=True)
    sonda, tutto = Sonda(), {}
    for k in chiavi:
        log(f">>> {CANDIDATE[k][0]}")
        try:
            R = ricognisci(k, sonda, log)
            (out / f"report_{k}.txt").write_text(report(R), encoding="utf-8")
            tutto[k] = R
        except Exception as e:
            tutto[k] = {"errore": repr(e)}
            log(f"    ERRORE {e!r}")
    (out / "riepilogo.json").write_text(json.dumps(tutto, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log(f"\nFatto. Report in {out}")
    return out
