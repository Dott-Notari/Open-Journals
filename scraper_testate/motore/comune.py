"""Funzioni di estrazione comuni a tutte le testate."""
import json
import re
import unicodedata
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import trafilatura
from bs4 import BeautifulSoup

from .config import FUSO

ROMA = ZoneInfo(FUSO)

# frasi di muri dei cookie, paywall e interfaccia da togliere dal corpo
RUMORE = re.compile(
    r"(consentless|cookie di\s+profilazione|terze parti selezionate|"
    r"iscriviti alla newsletter|leggi anche:|seguici su|abbonati per|riservato agli abbonati|"
    r"scarica l'app|clicca qui per|p\.\s?iva\s?\d|s\.p\.a\.,\s*via\b)", re.I)
SEGNALI_PAYWALL = re.compile(
    r"(questo articolo è riservato|per continuare a leggere|contenuto riservato agli abbonati|"
    r"sblocca l'articolo|accedi per leggere l'articolo completo|"
    r"subscribe to (continue|read)|already a subscriber|this article is for subscribers|"
    r"suscr[ií]bete para (seguir|continuar) leyendo|contenido exclusivo para suscriptores)", re.I)


# ------------------------------------------------------------------ date
def parse_data(s):
    """Converte una data in formato ISO (anche con 'Z', millisecondi o fuso +0200) in ora italiana."""
    if not s:
        return None
    s = str(s).strip()
    s = re.sub(r"Z$", "+00:00", s)
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        try:
            d = datetime.fromisoformat(s[:10])
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=ROMA)
    return d.astimezone(ROMA)


def data_da_url(url):
    m = re.search(r"/((?:19|20)\d{2})/(\d{2})/(\d{2})/", url)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def giorni(dal: date, al: date):
    g = dal
    while g <= al:
        yield g
        g += timedelta(days=1)


def mesi(dal: date, al: date):
    a, m = dal.year, dal.month
    while (a, m) <= (al.year, al.month):
        yield f"{a:04d}-{m:02d}"
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)


# ------------------------------------------------------------------ metadati
def json_ld(soup):
    """Primo oggetto *Article del JSON-LD, con i campi normalizzati."""
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            dati = json.loads(s.string or s.get_text() or "")
        except (json.JSONDecodeError, TypeError):
            continue
        coda = [dati]
        while coda:
            d = coda.pop(0)
            if isinstance(d, list):
                coda.extend(d)
                continue
            if not isinstance(d, dict):
                continue
            if isinstance(d.get("@graph"), list):
                coda.extend(d["@graph"])
            tipo = d.get("@type", "")
            tipo = " ".join(tipo) if isinstance(tipo, list) else str(tipo)
            if "Article" in tipo:
                autori = d.get("author") or []
                autori = autori if isinstance(autori, list) else [autori]
                kw = d.get("keywords") or []
                if isinstance(kw, str):
                    kw = [k.strip() for k in kw.split(",")]
                libero = d.get("isAccessibleForFree")
                if isinstance(libero, str):
                    libero = libero.strip().lower() == "true"
                return {
                    "titolo": d.get("headline") or "",
                    "data": d.get("datePublished") or "",
                    "sezione": d.get("articleSection") or "",
                    "tag": [k for k in kw if k],
                    "autori": [a.get("name", "") if isinstance(a, dict) else str(a) for a in autori],
                    "libero": libero,
                    "descrizione": d.get("description") or "",
                }
    return {}


def meta(soup, chiave):
    """Valori dei meta con property o name uguale a chiave."""
    trovati = soup.find_all("meta", attrs={"property": chiave}) + \
        soup.find_all("meta", attrs={"name": chiave})
    return [m.get("content", "").strip() for m in trovati if m.get("content")]


def primo(*valori):
    for v in valori:
        if isinstance(v, list):
            v = v[0] if v else ""
        if v:
            return v
    return ""


ELISIONI = re.compile(r"\b((?:[lLdDcCsSmMtTvVnN]|[uU]n|[dD]ell|[nN]ell|[aA]ll|[dD]all|[sS]ull|[qQ]uest|"
                      r"[qQ]uell|[tT]utt|[gG]l)[’'])\s+(?=\w)")


def ricuci(t):
    """Toglie gli spazi spuri lasciati dai link e dai grassetti interni alle frasi."""
    t = re.sub(r"\s+([.,;:!?)\]»”])", r"\1", t)
    t = re.sub(r"([(\[«“])\s+", r"\1", t)
    t = ELISIONI.sub(r"\1", t)                          # l’ articolo -> l’articolo
    return t


def testo_pulito(t):
    t = unicodedata.normalize("NFC", t or "")
    t = t.replace("\xa0", " ")
    return ricuci(re.sub(r"[ \t]+", " ", t).strip())


# ------------------------------------------------------------------ corpo del testo
def paragrafi(el):
    out = []
    for p in el.find_all(["p", "h2", "h3", "li", "blockquote"]):
        if p.find_parent(["figure", "figcaption", "aside", "nav", "footer"]):
            continue
        t = testo_pulito(p.get_text(" ", strip=True))
        if t and not RUMORE.search(t):
            out.append(t)
    # elimina ripetizioni (es. un li che contiene un p già preso)
    visti, uniq = set(), []
    for t in out:
        if t not in visti:
            visti.add(t)
            uniq.append(t)
    return uniq


def corpo_selettori(soup, selettori):
    for sel in selettori:
        el = soup.select_one(sel)
        if el:
            par = paragrafi(el)
            if not par:
                t = testo_pulito(el.get_text("\n", strip=True))
                par = [r for r in t.split("\n") if r.strip() and not RUMORE.search(r)]
            if sum(len(p) for p in par) >= 120:
                return par, f"selettore {sel}"
    return [], ""


def corpo_denso(soup):
    """Contenitore con la maggiore quantità di testo in paragrafi figli diretti."""
    migliore, punteggio = None, 0
    for el in soup.find_all(["div", "section", "article", "main"]):
        figli = el.find_all("p", recursive=False)
        tot = sum(len(p.get_text(strip=True)) for p in figli
                  if len(p.get_text(strip=True)) > 40)
        if tot > punteggio:
            migliore, punteggio = el, tot
    if migliore is None:
        return [], ""
    par = [testo_pulito(p.get_text(" ", strip=True)) for p in migliore.find_all("p", recursive=False)]
    par = [p for p in par if p and not RUMORE.search(p)]
    return par, "contenitore più denso"


def corpo_trafilatura(html):
    t = trafilatura.extract(html, include_comments=False, include_tables=False,
                            favor_precision=True) or ""
    par = [testo_pulito(r) for r in t.split("\n")]
    return [p for p in par if p and not RUMORE.search(p)], "trafilatura"


def togli_intestazione(par, titolo, sommario):
    """Toglie dall'inizio del corpo le righe che ripetono titolo o sommario."""
    norm = lambda s: re.sub(r"\W+", " ", (s or "").lower()).strip()
    da_togliere = {norm(titolo), norm(sommario)} - {""}
    while par and norm(par[0]) in da_togliere:
        par = par[1:]
    return par


def taglia_a(par, marcatori):
    for i, p in enumerate(par):
        if any(m.lower() in p.lower() for m in marcatori):
            return par[:i]
    return par


def sommario_ridondante(sommario, testo):
    """Vero se il sommario è solo l'attacco del testo (come nelle notizie d'agenzia)."""
    norm = lambda s: re.sub(r"\W+", " ", (s or "").lower()).strip()
    s = re.sub(r"(\.\.\.|…)?\s*\(ANSA\)\.?\s*$", "", sommario or "")
    s, t = norm(s), norm(testo)
    return bool(s) and t.startswith(s[:80])


def coerenza(titolo, sommario, testo):
    """Quota di parole significative del titolo che compaiono nell'avvio del testo (titolo escluso)."""
    parole = {p for p in re.findall(r"\w+", (titolo or "").lower()) if len(p) > 3}
    if not parole:
        return 1.0
    avvio = ((sommario or "") + " " + (testo or "")[:1500]).lower()
    return round(sum(p in avvio for p in parole) / len(parole), 2)


VIRG = re.compile(r"«([^»]{15,})»|“([^”]{15,})”|\"([^\"]{15,})\"")


def virgolettati(testo):
    return [next(g for g in m.groups() if g).strip() for m in VIRG.finditer(testo or "")]


def soup_di(html):
    return BeautifulSoup(html, "lxml")


# ------------------------------------------------------------------ parole chiave
def compila_parole(parole):
    pat = []
    for p in parole:
        p = p.strip()
        if not p:
            continue
        esc = re.escape(p).replace(r"\*", r"\w*")
        pat.append(re.compile(rf"(?<!\w){esc}(?!\w)", re.I))
    return pat


def corrisponde(pattern, testo, tutte=False):
    if not pattern:
        return True
    esiti = [bool(p.search(testo)) for p in pattern]
    return all(esiti) if tutte else any(esiti)


def piega(s):
    """Minuscole senza accenti (per confrontare parole chiave e indirizzi)."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[-_]+", " ", s.lower())


def slug_url(url):
    """Parole del titolo ricavabili dall'URL (per il filtro rapido sul titolo)."""
    parti = [p for p in url.split("?")[0].split("/") if p]
    candidati = [p for p in parti if "-" in p]
    s = max(candidati, key=len) if candidati else (parti[-1] if parti else "")
    s = re.sub(r"(_[0-9a-f-]{8,}|_\d+|-\d{5,})(\.html)?$", "", s)
    s = re.sub(r"\.html?$", "", s)
    return s.replace("-", " ")
