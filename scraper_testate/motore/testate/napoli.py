"""Testate sportive napoletane, scritte sulla ricognizione del 24 novembre 2026 (robots.txt, sitemap,
API di WordPress, mappatura con reverse-api-engineer di tuttonapoli.net).

Tre testate sono WordPress con l'API REST aperta e si interrogano per data e per parola come La Verità
(CalcioNapoli1926, il Napolista); SpazioNapoli ha l'API ma il robots.txt esclude gli indirizzi con «&»,
quindi si usano le sitemap annuali. TuttoNapoli, CalcioNapoli24 e AreaNapoli hanno CMS propri."""
import re
from datetime import date, timedelta

from .base import Testata
from .seconda_ondata import _avviso
from .. import comune as C
from .. import sitemap as SM
from ..modello import SorgenteURL


def _giorno(s):
    d = C.parse_data(s)
    return d.date() if d else None


def _json(r):
    if r is None or r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


# ------------------------------------------------------------------ WordPress con API REST
class _WordPress(Testata):
    """API /wp-json/wp/v2/posts con filtro per date (after/before) e ricerca (search), 100 per pagina."""
    API = ""
    INIZIO = None          # primo articolo dell'archivio
    paginazione = "{base}page/{n}/"

    def _link(self, rete, **filtri):
        for n in range(1, 2000):
            r = rete.get(self.API, params={**filtri, "per_page": 100, "page": n, "orderby": "date",
                                           "order": "desc", "_fields": "link"})
            voci = _json(r) or []
            yield from (v["link"] for v in voci if v.get("link"))
            if not voci or n >= int(r.headers.get("X-WP-TotalPages", 1)):
                return

    def _periodo(self, dal, al):
        return {"after": f"{dal}T00:00:00", "before": f"{al}T23:59:59"}

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls = [u for u in dict.fromkeys(self._link(rete, **self._periodo(dal, al))) if self.e_articolo(u)]
        log(f"  {self.nome}: API di WordPress, {len(urls)} articoli nel periodo")
        return [SorgenteURL("API REST di WordPress per data", urls, _avviso(self.nome, self.INIZIO, dal,
                                                                            "l'archivio del sito"))]

    def motore_ricerca(self, rete, termine, dal, al):
        return self._link(rete, search=termine, **self._periodo(dal, al))


class CalcioNapoli1926(_WordPress):
    chiave, nome, dominio = "calcionapoli1926", "CalcioNapoli1926", "calcionapoli1926.it"
    API = "https://www.calcionapoli1926.it/wp-json/wp/v2/posts"
    INIZIO = date(2016, 10, 15)
    # le pagine di sezione hanno la stessa forma (/news-calcio-napoli/infortuni/): gli articoli hanno slug lunghi
    re_articolo = re.compile(r"^https://www\.calcionapoli1926\.it/(?!category/|tag/|author/|page/|wp-|feed|"
                             r"api/|modal|team/|redazione/)[a-z0-9-]+/[a-z0-9]+(?:-[a-z0-9]+){3,}/?$")
    elenchi_prova = ("https://www.calcionapoli1926.it/interviste/",)
    paginazione = "{base}pagina-{n}/"     # le categorie usano /pagina-N/, non /page/N/
    note_ricerca_data = "API REST di WordPress con filtro per date: archivio completo dall'ottobre 2016"


class IlNapolista(_WordPress):
    chiave, nome, dominio = "ilnapolista", "il Napolista", "ilnapolista.it"
    API = "https://www.ilnapolista.it/wp-json/wp/v2/posts"
    INIZIO = date(2010, 3, 24)
    re_articolo = re.compile(r"^https://www\.ilnapolista\.it/\d{4}/\d{2}/[a-z0-9-]+/?$")
    elenchi_prova = ("https://www.ilnapolista.it/category/napoli/",)
    note_ricerca_data = ("API REST di WordPress con filtro per date: archivio completo dal marzo 2010. Si interroga "
                         "tutto il sito (calcio, Napoli, altri sport, cultura); per la sola categoria Napoli si usa "
                         "il comando elenco con https://www.ilnapolista.it/category/napoli/")


# ------------------------------------------------------------------ SpazioNapoli: sitemap annuali
class SpazioNapoli(Testata):
    chiave, nome, dominio = "spazionapoli", "SpazioNapoli", "spazionapoli.it"
    re_articolo = re.compile(r"^https://www\.spazionapoli\.it/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?$")
    date_nell_url = True
    paginazione = None
    MODELLO = "https://www.spazionapoli.it/sitemap-posttype-post.{anno}.xml"
    # il robots.txt esclude /2011/ … /2019/, cioè tutti gli articoli di quegli anni
    INIZIO = date(2020, 1, 1)
    note_ricerca_data = ("sitemap annuali degli articoli, con la data nell'indirizzo; il robots.txt esclude gli "
                         "articoli dal 2011 al 2019 e gli indirizzi con «&» (quindi l'API con filtri e la ricerca)")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        anni = range(al.year, max(dal.year, self.INIZIO.year) - 1, -1)
        urls = []
        for a in anni:
            for u, _, _ in SM.leggi_urlset(rete, self.MODELLO.format(anno=a)):
                g = C.data_da_url(u)
                if g and dal <= g <= al and self.e_articolo(u):
                    urls.append(u)
        urls = sorted(dict.fromkeys(urls), key=C.data_da_url, reverse=True)
        log(f"  SpazioNapoli: {len(anni)} sitemap annuali, {len(urls)} articoli nel periodo")
        avviso = (f"SpazioNapoli: il robots.txt esclude gli articoli dal 2011 al 2019; il periodo raggiungibile "
                  f"parte dal {self.INIZIO}") if dal < self.INIZIO else ""
        return [SorgenteURL(f"sitemap annuali ({len(anni)})", urls, avviso)]


# ------------------------------------------------------------------ TuttoNapoli: identificativi progressivi
class TuttoNapoli(Testata):
    """CMS TCC (rete TuttoMercatoWeb), senza API. Il robots.txt esclude «start=», cioè la paginazione di
    sezioni e ricerca; gli articoli hanno però un identificativo progressivo e /?action=read&idnotizia=N
    rimanda all'articolo. Per data: ricerca binaria dell'identificativo del primo e dell'ultimo giorno,
    poi tutti gli identificativi compresi."""
    chiave, nome, dominio = "tuttonapoli", "TuttoNapoli", "tuttonapoli.net"
    re_articolo = re.compile(r"^https://www\.tuttonapoli\.net/(?:[a-z0-9-]+/[a-z0-9-]+-\d{4,}|"
                             r"\?action=read&idnotizia=\d+)$")
    paginazione = None
    LEGGI = "https://www.tuttonapoli.net/?action=read&idnotizia={}"
    NEWS = "https://www.tuttonapoli.net/sitemap-news.xml"
    note_ricerca_data = ("identificativi progressivi degli articoli (/?action=read&idnotizia=N): ricerca binaria "
                         "del primo e dell'ultimo articolo del periodo, poi tutti quelli compresi; archivio completo")

    def normalizza(self, url):
        return url if "action=read" in url else super().normalizza(url)

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def estrai(self, html, url):
        art = super().estrai(html, url)
        canon = C.meta(C.soup_di(html), "og:url")
        if canon and "action=read" in url:
            art.url = canon if isinstance(canon, str) else canon[0]
        return art

    def _giorno_id(self, rete, i, salti=6):
        """Data dell'articolo i (o del primo esistente dopo di lui); None se non ce ne sono."""
        for j in range(i, i + salti):
            r = rete.get(self.LEGGI.format(j))
            if r is not None and r.status_code == 200:
                g = super().estrai(r.text, r.url).giorno()
                if g:
                    return g
        return None

    def _primo_dal(self, rete, giorno, alto):
        """Primo identificativo con data >= giorno (ricerca binaria)."""
        lo, hi = 1, alto + 1
        while lo < hi:
            mid = (lo + hi) // 2
            g = self._giorno_id(rete, mid)
            if g is None or g >= giorno:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def piano_per_data(self, rete, dal, al, log, parole=None):
        ids = [int(m.group(1)) for u, _, _ in SM.leggi_urlset(rete, self.NEWS)
               for m in [re.search(r"-(\d{4,})$", u)] if m]
        if not ids:
            return [SorgenteURL("identificativi progressivi", [], "TuttoNapoli: sitemap news non raggiungibile")]
        massimo = max(ids)
        log(f"  TuttoNapoli: ultimo articolo {massimo}; cerco gli estremi del periodo (ricerca binaria)")
        primo = self._primo_dal(rete, dal, massimo)
        ultimo = self._primo_dal(rete, al + timedelta(days=1), massimo) - 1
        urls = [self.LEGGI.format(i) for i in range(min(ultimo, massimo), primo - 1, -1)]
        log(f"  TuttoNapoli: articoli dal n. {primo} al n. {ultimo}, {len(urls)} da scaricare")
        return [SorgenteURL("identificativi progressivi degli articoli", urls)]


# ------------------------------------------------------------------ CalcioNapoli24: sitemap numerate in ordine
class CalcioNapoli24(Testata):
    """Circa 500 sitemap art-sitemap-N.xml di circa 1000 articoli ciascuna, in ordine cronologico dal 2011:
    ricerca binaria del primo file utile, poi lettura in avanti fino alla fine del periodo."""
    chiave, nome, dominio = "calcionapoli24", "CalcioNapoli24", "calcionapoli24.it"
    re_articolo = re.compile(r"^https://www\.calcionapoli24\.it/[a-z0-9_-]+/[a-z0-9-]+-n\d+\.html$")
    paginazione = None
    INDICE = "https://www.calcionapoli24.it/apk/sitemap/index-sitemap-gl.xml"
    FILE = "https://www.calcionapoli24.it/apk/sitemap/art-sitemap-{}.xml"
    RECENTI = "https://www.calcionapoli24.it/apk/sitemap/recent-sitemap.xml"
    INIZIO = date(2011, 3, 30)
    note_ricerca_data = ("sitemap numerate in ordine cronologico (circa 1000 articoli ciascuna, dal marzo 2011) "
                         "più la sitemap degli articoli recenti; la ricerca del sito è esclusa dal robots.txt")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def estrai(self, html, url):
        """Negli articoli meno recenti il testo è solo nel campo articleBody del JSON-LD."""
        art = super().estrai(html, url)
        if len(art.testo) < 150:
            corpo = C.testo_pulito(C.json_ld(C.soup_di(html)).get("corpo", ""))
            if len(corpo) > len(art.testo):
                art.testo, art.metodo = corpo, "JSON-LD (articleBody)"
                art = self.valuta(art)
        return art

    def _voci(self, rete, n):
        return [(u, _giorno(lm)) for u, lm, _ in SM.leggi_urlset(rete, self.FILE.format(n))]

    def piano_per_data(self, rete, dal, al, log, parole=None):
        nums = [int(m.group(1)) for loc, _ in SM.leggi_indice(rete, self.INDICE)
                for m in [re.search(r"art-sitemap-(\d+)\.xml", loc)] if m]
        ultimo = max(nums) if nums else 1
        while self._voci(rete, ultimo + 1):      # l'indice può non elencare ancora l'ultimo file
            ultimo += 1
        lo, hi = 1, ultimo            # ultimo file il cui ultimo articolo è precedente a dal
        while lo < hi:
            mid = (lo + hi + 1) // 2
            date_ = [g for _, g in self._voci(rete, mid) if g]
            if date_ and max(date_) < dal:
                lo = mid
            else:
                hi = mid - 1
        urls, letti = [], 0
        for n in range(lo, ultimo + 1):
            voci = self._voci(rete, n)
            letti += 1
            urls += [u for u, g in voci if g and dal <= g <= al and self.e_articolo(u)]
            if any(g and g > al for _, g in voci):
                break
        else:
            urls += [u for u, lm, _ in SM.leggi_urlset(rete, self.RECENTI)
                     if (g := _giorno(lm)) and dal <= g <= al and self.e_articolo(u)]
        urls = list(dict.fromkeys(urls))[::-1]
        log(f"  CalcioNapoli24: {letti} sitemap lette, {len(urls)} articoli nel periodo")
        return [SorgenteURL("sitemap numerate in ordine cronologico", urls,
                            _avviso(self.nome, self.INIZIO, dal, "le sitemap"))]


# ------------------------------------------------------------------ AreaNapoli: sitemap per blocchi di 25.000
class AreaNapoli(Testata):
    """Indice con circa 12 sitemap da 25.000 articoli, dal più recente; ogni voce ha la data (lastmod)."""
    chiave, nome, dominio = "areanapoli", "AreaNapoli", "areanapoli.it"
    re_articolo = re.compile(r"^https://www\.areanapoli\.it/[a-z0-9-]+/[a-z0-9-]+_\d+\.html$")
    paginazione = None
    INDICE = "https://www.areanapoli.it/sitemap.xml"
    MARGINE = 1      # la data delle sitemap è quella di pubblicazione (verifica del 24 novembre 2026)
    note_ricerca_data = ("sitemap da 25.000 articoli in ordine dal più recente, con la data di ogni articolo; "
                         "si leggono solo i blocchi che coprono il periodo")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = [loc for loc, _ in SM.leggi_indice(rete, self.INDICE) if re.search(r"sitemap-\d+\.xml$", loc)]
        files.sort(key=lambda f: int(re.search(r"(\d+)\.xml$", f).group(1)))
        tetto = al + timedelta(days=self.MARGINE)
        urls, letti, minima = [], 0, None
        for f in files:
            voci = [(u, _giorno(lm)) for u, lm, _ in SM.leggi_urlset(rete, f)]
            letti += 1
            date_ = [g for _, g in voci if g]
            if date_:
                minima = min(date_) if minima is None else min(minima, min(date_))
            if date_ and min(date_) > tetto:
                continue
            urls += [u for u, g in voci if g and dal <= g <= tetto and self.e_articolo(u)]
            if date_ and min(date_) < dal:
                break
        urls = list(dict.fromkeys(urls))
        log(f"  AreaNapoli: {letti} sitemap lette, {len(urls)} articoli nel periodo")
        return [SorgenteURL(f"sitemap a blocchi ({letti})", urls, _avviso(self.nome, minima, dal, "le sitemap"))]


NAPOLI = (TuttoNapoli(), CalcioNapoli24(), AreaNapoli(), CalcioNapoli1926(), SpazioNapoli(), IlNapolista())


def _registra_motori():
    from .ricerca import MOTORI
    for t in NAPOLI:
        if isinstance(t, _WordPress):
            MOTORI[t.chiave] = (t.motore_ricerca, "API REST di WordPress con ricerca e filtro per date", False)


_registra_motori()
