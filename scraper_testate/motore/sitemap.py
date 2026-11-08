"""Lettura delle sitemap XML (indici ed elenchi di URL, anche Google News)."""
import re

from bs4 import BeautifulSoup

from .rete import contenuto_xml


def _scarica(rete, url):
    r = rete.get(url)
    if r is None or r.status_code != 200:
        return None
    return BeautifulSoup(contenuto_xml(r), "xml")


def leggi_indice(rete, url):
    soup = _scarica(rete, url)
    if soup is None:
        return []
    voci = [(s.loc.get_text(strip=True), s.lastmod.get_text(strip=True) if s.lastmod else "")
            for s in soup.find_all("sitemap") if s.loc]
    if not voci:   # alcuni siti servono l'indice come elenco di <url> che puntano ad altre sitemap
        voci = [(u.loc.get_text(strip=True), u.lastmod.get_text(strip=True) if u.lastmod else "")
                for u in soup.find_all("url") if u.loc and re.search(r"\.xml(\.gz)?$", u.loc.get_text(strip=True))]
    return voci


def leggi_urlset(rete, url):
    """Lista di (loc, lastmod, data_pubblicazione_news)."""
    soup = _scarica(rete, url)
    if soup is None:
        return []
    out = []
    for u in soup.find_all("url"):
        if not u.loc:
            continue
        pub = u.find(re.compile(r"(^|:)publication_date$"))
        out.append((u.loc.get_text(strip=True),
                    u.lastmod.get_text(strip=True) if u.lastmod else "",
                    pub.get_text(strip=True) if pub else ""))
    return out


def _giorno(s):
    from .comune import parse_data
    d = parse_data(s)
    return d.date() if d else None


def per_data_pubblicazione(rete, files, dal, al, e_articolo):
    """URL delle sitemap con data di pubblicazione (o lastmod) nell'intervallo; restituisce anche
    la data più vecchia incontrata, per gli avvisi di copertura."""
    urls, minima = [], None
    for f in files:
        for u, lastmod, pub in leggi_urlset(rete, f):
            g = _giorno(pub or lastmod)
            if g is None or not e_articolo(u):
                continue
            minima = g if minima is None else min(minima, g)
            if dal <= g <= al:
                urls.append(u)
    return list(dict.fromkeys(urls)), minima


def per_lastmod(rete, indice, regex_file, dal, e_articolo, al=None, margine=60):
    """Per i siti con sitemap non ordinate per data: si leggono i file modificati dopo `dal`
    e se ne tengono gli URL modificati dopo `dal` (la data esatta si verifica poi sull'articolo)."""
    from datetime import timedelta
    tetto = (al + timedelta(days=margine)) if al else None
    voci = {}
    for loc, lm in leggi_indice(rete, indice):
        if not re.search(regex_file, loc):
            continue
        g = _giorno(lm)
        if g is not None and g < dal:
            continue
        for u, lastmod, _ in leggi_urlset(rete, loc):
            g2 = _giorno(lastmod)
            if e_articolo(u) and g2 is not None and g2 >= dal and (tetto is None or g2 <= tetto):
                voci[u] = g2
    # prima gli articoli modificati dentro il periodo, poi quelli modificati dopo, dal più vicino
    return sorted(voci, key=lambda u: (voci[u] > (al or voci[u]), voci[u]))
