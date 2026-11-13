"""Motori di ricerca delle testate che il robots.txt consente di interrogare (verifica del 12 novembre 2026).

Ogni funzione restituisce gli indirizzi degli articoli trovati per un termine nell'intervallo richiesto;
gli articoli vengono poi scaricati e verificati dal motore come in tutte le altre modalità.
Non sono inclusi i motori esclusi dal robots.txt: la Repubblica (ricerca.repubblica.it),
Il Mattino e Il Messaggero (/ricerca/), El Mundo (ariadna.elmundo.es)."""
import re
from datetime import datetime, time as ora
from urllib.parse import urljoin

from ..comune import ROMA, data_da_url, parse_data
from ..config import LIMITE_PAGINE


def _json(r):
    if r is None or r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def _iso(giorno, fine=False):
    return datetime.combine(giorno, ora(23, 59, 59) if fine else ora(0, 0), ROMA).isoformat()


def _giorno(s):
    d = parse_data(s)
    return d.date() if d else None


class FuoriPortata(Exception):
    """Il motore della testata non arriva indietro fino al periodo richiesto."""


def _ordinati(pagina, dal, al, prima=1, ultima=None):
    """Scorre i risultati di un motore ordinato dal più recente. pagina(n) restituisce [(url, giorno)].
    Per i periodi lontani salta alla prima pagina utile con una ricerca esponenziale e poi binaria
    sul numero di pagina, invece di leggere tutte le pagine più recenti."""
    letto = {}

    def p(n):
        if n not in letto:
            letto[n] = pagina(n) if ultima is None or n <= ultima else []
        return letto[n]

    def utile(n):          # la pagina arriva già al periodo richiesto (o è oltre la fine dei risultati)
        date = [g for _, g in p(n) if g]
        return not p(n) or (bool(date) and min(date) <= al)

    lo, passo = prima, 1
    if not utile(prima):
        hi = prima + passo
        while not utile(hi) and hi - prima < LIMITE_PAGINE:
            lo, passo = hi, passo * 2
            hi = prima + passo
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if utile(mid):
                hi = mid
            else:
                lo = mid
        lo = hi
    if not p(lo) and lo > prima:
        piene = [n for n in letto if letto[n]]
        date = [g for _, g in letto[max(piene)] if g] if piene else []
        if date and min(date) > al:
            raise FuoriPortata(f"la ricerca del sito arriva indietro solo fino al {min(date).isoformat()}")
    for n in range(lo, lo + LIMITE_PAGINE):
        voci = p(n)
        if not voci:
            return
        yield from (u for u, g in voci if u and (g is None or dal <= g <= al))
        date = [g for _, g in voci if g]
        if date and max(date) < dal:
            return


def fatto(rete, termine, dal, al):
    """Feed RSS della ricerca di WordPress (/?s=…&feed=rss2&paged=N), dal più recente."""
    def pagina(n):
        r = rete.get("https://www.ilfattoquotidiano.it/",
                     params={"s": termine, "feed": "rss2", **({"paged": n} if n > 1 else {})})
        if r is None or r.status_code != 200:
            return []
        links = re.findall(r"<link>(https://www\.ilfattoquotidiano\.it/\d{4}/[^<]+)</link>", r.text)
        return [(l, data_da_url(l)) for l in links]
    return _ordinati(pagina, dal, al)


def avvenire(rete, termine, dal, al):
    """API del sito (/api/naxos/search): ricerca con filtro per date, 30 risultati per pagina."""
    for n in range(1, LIMITE_PAGINE):
        d = _json(rete.get("https://www.avvenire.it/api/naxos/search", params={
            "qs": termine, "page": n, "dateFrom": _iso(dal), "dateTo": _iso(al, fine=True)}))
        if not d or not d.get("data"):
            return
        for it in d["data"]:
            if it.get("URL"):
                yield urljoin("https://www.avvenire.it/", it["URL"])
        if not d.get("meta", {}).get("pagination", {}).get("morePages"):
            return


def verita(rete, termine, dal, al):
    """API REST di WordPress (/wp-json/wp/v2/posts) con ricerca e filtro per date, 100 per pagina."""
    for n in range(1, LIMITE_PAGINE):
        r = rete.get("https://www.laverita.info/wp-json/wp/v2/posts", params={
            "search": termine, "after": f"{dal}T00:00:00", "before": f"{al}T23:59:59",
            "per_page": 100, "page": n, "_fields": "link,date"})
        d = _json(r)
        if not d:
            return
        yield from (it["link"] for it in d if it.get("link"))
        if n >= int(r.headers.get("X-WP-TotalPages", 1)):
            return


def ilpost(rete, termine, dal, al):
    """API di ricerca di Il Post (api.ilpost.org), ordinata dal più recente, 10 per pagina."""
    def pagina(n):
        d = _json(rete.get("https://api.ilpost.org/search/api/site_search/", params={
            "qs": termine, "pg": n, "sort": "date_d", "filters": "ctype:articoli"}))
        return [(doc.get("link"), _giorno(doc.get("timestamp"))) for doc in (d or {}).get("docs") or []]
    return _ordinati(pagina, dal, al)


def corriere(rete, termine, dal, al):
    """API di ricerca del Corriere (searchapiservice.corriere.it): senza filtro per date, ordinata
    dal più recente; comprende le edizioni locali."""
    def pagina(n):
        d = _json(rete.get("https://searchapiservice.corriere.it/api/search",
                           params={"find": termine, "page": n, "limit": 100}))
        return [(it.get("url"), _giorno(it.get("firstPublicationDate"))) for it in (d or {}).get("data") or []]
    return _ordinati(pagina, dal, al)


_SOLE_Q = """query($keyword:String!,$filter:R24Filter,$page:Int,$pageSize:Int,$sort:SortClause){
 findByKeyword(input:{keyword:$keyword,filter:$filter,page:$page,pageSize:$pageSize,sort:$sort}){
  metadata{page pages} items{url data}}}"""


def sole24ore(rete, termine, dal, al):
    """Ricerca per parola di argomenti.ilsole24ore.com (GraphQL), solo notizie, dal più recente;
    il motore non va oltre circa 250 pagine."""
    def pagina(n):
        d = _json(rete.get("https://argomenti.ilsole24ore.com/api/graphql",
                           headers={"Origin": "https://argomenti.ilsole24ore.com"},
                           json={"query": _SOLE_Q, "variables": {"keyword": termine, "filter": "Notizie",
                                                                 "page": n, "pageSize": 50, "sort": "Data"}}))
        voci = []
        for it in (((d or {}).get("data") or {}).get("findByKeyword") or {}).get("items") or []:
            try:
                g = datetime.strptime(it.get("data") or "", "%d/%m/%Y").date()
            except ValueError:
                g = None
            voci.append((urljoin("https://www.ilsole24ore.com/", it.get("url") or ""), g))
        return voci
    return _ordinati(pagina, dal, al, prima=0, ultima=249)


# chiave: (funzione, descrizione per la scheda, il motore cerca solo parole intere)
MOTORI = {
    "fatto": (fatto, "feed della ricerca interna di WordPress, dal più recente, con salto alla pagina del periodo", False),
    "avvenire": (avvenire, "API di ricerca del sito con filtro per date", False),
    "verita": (verita, "API REST di WordPress con ricerca e filtro per date", False),
    "ilpost": (ilpost, "API di ricerca di Il Post, solo articoli, con salto alla pagina del periodo", True),
    "corriere": (corriere, "API di ricerca del Corriere, edizioni locali comprese, con salto alla pagina del periodo", True),
    "sole24ore": (sole24ore, "ricerca per parola di argomenti.ilsole24ore.com, solo notizie, al massimo "
                             "circa 12.500 risultati per termine", True),
}

# finali provati quando il motore cerca solo parole intere e la parola chiave ha l'asterisco
FINALI = ("", "a", "e", "i", "o")
