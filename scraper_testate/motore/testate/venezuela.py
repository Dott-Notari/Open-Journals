"""Testate venezuelane, scritte sulla ricognizione del 24-25 novembre 2026 (robots.txt, API di WordPress,
sitemap, prova di scaricamento di un articolo con lo User-Agent dello strumento).

Tre famiglie:
- API REST di WordPress aperta e con filtro per date funzionante: per data e per parola (come La Verità);
- sitemap degli articoli numerate in ordine cronologico (Yoast, WordPress, Wix): ricerca binaria del primo
  file utile e filtro sulla data di ultima modifica (che non può precedere la pubblicazione); la data esatta
  si verifica poi sull'articolo;
- solo sitemap news (ultimi giorni).

Non incluse (vedi schede.ESCLUSE): El Universal e Globovisión (robots.txt «Disallow: /»), TalCual ed
El Periodiquito (protezione anti-bot), Efecto Cocuyo e La Patilla (articoli negati con 403 allo strumento),
El Tiempo (sito irraggiungibile), Frontera Digital (dominio in vendita), Panorama (offline dal 2023),
El Luchador (API disattivata e nessuna sitemap degli articoli)."""
import re
from datetime import date, timedelta

from .base import Testata
from .napoli import _WordPress, _giorno
from .seconda_ondata import _avviso
from .. import comune as C
from .. import sitemap as SM
from ..modello import SorgenteURL

ESCLUSI_PERCORSI = r"(?!category/|categoria/|tag/|etiqueta/|author/|autor/|page/|wp-|feed|amp/|search/|buscar)"


def _re(dominio, percorso=r"(?:[^/?#]+/)*[^/?#]+-[^/?#]+-[^/?#]+/?"):
    """Indirizzi degli articoli: dominio, nessun percorso di servizio, slug di almeno tre parole."""
    return re.compile(rf"^https?://(?:www\.)?{re.escape(dominio)}/{ESCLUSI_PERCORSI}{percorso}$")


class _Titolo:
    """Alcuni temi mettono nel primo <h1> il nome del sito: in quel caso vale og:title."""

    def estrai(self, html, url):
        art = super().estrai(html, url)
        if not art.titolo or art.titolo.lower() == self.nome.lower():
            og = C.meta(C.soup_di(html), "og:title")
            og = og[0] if isinstance(og, list) and og else og
            if og:
                art.titolo = re.sub(r"\s*[|–-]\s*" + re.escape(self.nome) + r"\s*$", "", C.testo_pulito(og))
                art = self.valuta(art)
        return art


# ------------------------------------------------------------------ API REST di WordPress
class _WPVe(_Titolo, _WordPress):
    lingua = "es"
    paginazione = "{base}page/{n}/"


class UltimasNoticias(_WPVe):
    chiave, nome, dominio = "ultimasnoticias", "Últimas Noticias", "ultimasnoticias.com.ve"
    API = "https://ultimasnoticias.com.ve/wp-json/wp/v2/posts"
    re_articolo = _re(dominio)
    note_ricerca_data = "API REST di WordPress con filtro per date (circa 200.000 articoli)"


class DiarioVea(_WPVe):
    chiave, nome, dominio = "diariovea", "Diario VEA", "diariovea.com.ve"
    API = "https://diariovea.com.ve/wp-json/wp/v2/posts"
    INIZIO = date(2020, 9, 9)
    re_articolo = _re(dominio)
    note_ricerca_data = "API REST di WordPress con filtro per date, dal settembre 2020"


class Runrunes(_WPVe):
    chiave, nome, dominio = "runrunes", "Runrun.es", "runrun.es"
    API = "https://runrun.es/wp-json/wp/v2/posts"
    INIZIO = date(2006, 10, 19)
    re_articolo = _re(dominio, r"[a-z0-9-]+/\d+/[a-z0-9-]+/?")
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2006"


class CronicaUno(_WPVe):
    chiave, nome, dominio = "cronicauno", "Crónica Uno", "cronica.uno"
    API = "https://cronica.uno/wp-json/wp/v2/posts"
    INIZIO = date(2015, 1, 4)
    re_articolo = _re(dominio)
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2015"


class ElEstimulo(_WPVe):
    chiave, nome, dominio = "elestimulo", "El Estímulo", "elestimulo.com"
    API = "https://elestimulo.com/wp-json/wp/v2/posts"
    INIZIO = date(2014, 4, 8)
    re_articolo = _re(dominio, r"[a-z0-9-]+/\d{4}-\d{2}-\d{2}/[a-z0-9-]+/?")
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2014"


class ElCarabobeno(_WPVe):
    chiave, nome, dominio = "elcarabobeno", "El Carabobeño", "el-carabobeno.com"
    API = "https://www.el-carabobeno.com/wp-json/wp/v2/posts"
    INIZIO = date(2014, 6, 5)
    re_articolo = _re(dominio)
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2014"


class Venezuelanalysis(_WPVe):
    chiave, nome, dominio = "venezuelanalysis", "Venezuelanalysis", "venezuelanalysis.com"
    lingua = "en"
    API = "https://venezuelanalysis.com/wp-json/wp/v2/posts"
    INIZIO = date(2003, 8, 23)
    re_articolo = _re(dominio)
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2003 (in inglese)"


class CaracasChronicles(_WPVe):
    chiave, nome, dominio = "caracaschronicles", "Caracas Chronicles", "caracaschronicles.com"
    lingua = "en"
    API = "https://www.caracaschronicles.com/wp-json/wp/v2/posts"
    INIZIO = date(2002, 9, 20)
    re_articolo = _re(dominio, r"\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?")
    date_nell_url = True
    note_ricerca_data = "API REST di WordPress con filtro per date, dal 2002 (in inglese)"


# ------------------------------------------------------------------ sitemap numerate in ordine cronologico
class _SitemapOrdinate(_Titolo, Testata):
    """Sitemap degli articoli numerate (post-sitemap.xml, post-sitemap2.xml…), in ordine cronologico
    crescente o decrescente (riconosciuto da solo). Si cerca con una ricerca binaria il primo file che arriva
    al periodo, poi si leggono i file successivi. Le voci si filtrano sulla data dell'indirizzo, se c'è, o
    sulla data di ultima modifica: si tengono quelle modificate nel periodo o nei MARGINE giorni successivi
    (prima quelle nel periodo); la data di pubblicazione si verifica sull'articolo."""
    lingua = "es"
    INDICE = ""
    RE_FILE = r"post-sitemap(\d*)\.xml$"
    MARGINE = 7
    paginazione = None
    AFFIDABILE_DAL = None    # prima di questa data le date di modifica non permettono di trovare gli articoli
    FINE_SITEMAP = None      # le sitemap non sono più aggiornate dopo questa data

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def _files(self, rete):
        fs = [loc for loc, _ in SM.leggi_indice(rete, self.INDICE) if re.search(self.RE_FILE, loc)]
        return sorted(fs, key=lambda f: int(re.search(self.RE_FILE, f).group(1) or 1))

    def _data(self, u, lastmod, pub):
        return (C.data_da_url(u) if self.date_nell_url else None) or _giorno(pub or lastmod)

    def _voci(self, rete, f):
        return [(u, self._data(u, lm, pub)) for u, lm, pub in SM.leggi_urlset(rete, f) if self.e_articolo(u)]

    @staticmethod
    def _quantile(voci, q):
        ds = sorted(g for _, g in voci if g)
        return ds[int(q * (len(ds) - 1))] if ds else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        fs = self._files(rete)
        if not fs:
            return [SorgenteURL("sitemap degli articoli", [], f"{self.nome}: sitemap degli articoli non raggiungibili")]
        cache = {}

        def voci(i):
            if i not in cache:
                cache[i] = self._voci(rete, fs[i])
            return cache[i]

        n = len(fs)
        primo, ultimo = self._quantile(voci(0), .5), self._quantile(voci(n - 1), .5)
        ordine = list(range(n)) if not (primo and ultimo) or primo <= ultimo else list(range(n - 1, -1, -1))
        lo, hi = 0, n - 1                   # primo file (in ordine cronologico) che arriva al periodo
        while lo < hi:
            mid = (lo + hi) // 2
            q = self._quantile(voci(ordine[mid]), .9)
            if q is None or q >= dal:
                hi = mid
            else:
                lo = mid + 1
        tetto = al if self.date_nell_url else al + timedelta(days=self.MARGINE)
        mesi_ok = {(d.year, d.month) for d in (dal + timedelta(days=i) for i in range((al - dal).days + 1))}

        def nel_mese(u):          # indirizzi con /AAAA/MM/: il mese di pubblicazione deve essere nel periodo
            m = re.search(r"/((?:19|20)\d{2})/(\d{2})/", u)
            return not m or (int(m.group(1)), int(m.group(2))) in mesi_ok

        trovate, letti = {}, 0
        for j in range(max(0, lo - 1), n):
            v = voci(ordine[j])
            letti += 1
            trovate.update({u: g for u, g in v if g and dal <= g <= tetto and nel_mese(u)})
            q = self._quantile(v, .1)
            if q and q > tetto:
                break
        urls = sorted(trovate, key=lambda u: (trovate[u] > al, -trovate[u].toordinal()))
        log(f"  {self.nome}: {n} sitemap degli articoli, {letti} lette, {len(urls)} indirizzi da verificare")
        minima = self._quantile(voci(ordine[0]), .1)
        avvisi = [_avviso(self.nome, minima, dal, "le sitemap")]
        if self.AFFIDABILE_DAL and dal < self.AFFIDABILE_DAL:
            avvisi.append(f"{self.nome}: prima del {self.AFFIDABILE_DAL} le sitemap riportano date di modifica in "
                          f"blocco e la ricerca per data è incompleta; per quei giorni usare --fonte wayback")
        if self.FINE_SITEMAP and al > self.FINE_SITEMAP:
            avvisi.append(f"{self.nome}: le sitemap non sono aggiornate dopo il {self.FINE_SITEMAP}; per i giorni "
                          f"successivi usare --fonte wayback")
        return [SorgenteURL(f"sitemap degli articoli in ordine cronologico ({letti} lette)", urls,
                            "; ".join(a for a in avvisi if a))]


class ElDiario(_SitemapOrdinate):
    chiave, nome, dominio = "eldiario", "El Diario", "eldiario.com"
    INDICE = "https://eldiario.com/sitemap_index.xml"
    re_articolo = _re(dominio, r"\d{4}/\d{2}/\d{2}/[^/?#]+/?")
    date_nell_url = True
    note_ricerca_data = ("sitemap degli articoli (Yoast) con la data nell'indirizzo, dal 2019; l'API di WordPress "
                         "risponde ma ignora il filtro per date")


class ElNacional(_SitemapOrdinate):
    chiave, nome, dominio = "elnacional", "El Nacional", "elnacional.com"
    INDICE = "https://www.elnacional.com/sitemap_index.xml"
    re_articolo = _re(dominio)
    note_ricerca_data = ("circa 316 sitemap degli articoli (Yoast) in ordine cronologico, filtrate per data di "
                         "modifica; l'API di WordPress è esclusa dal robots.txt")


class CaraotaDigital(_SitemapOrdinate):
    chiave, nome, dominio = "caraotadigital", "Caraota Digital", "caraotadigital.net"
    INDICE = "https://caraotadigital.net/wp-sitemap.xml"
    re_articolo = _re(dominio)
    note_ricerca_data = ("sitemap degli articoli in ordine cronologico, filtrate per data di modifica; l'API di "
                         "WordPress e la paginazione /page/ sono escluse dal robots.txt")


class AVN(_SitemapOrdinate):
    chiave, nome, dominio = "avn", "AVN – Agencia Venezolana de Noticias", "avn.info.ve"
    INDICE = "https://avn.info.ve/sitemap_index.xml"
    re_articolo = _re(dominio)
    note_ricerca_data = ("sitemap degli articoli (Yoast) dall'aprile 2024, filtrate per data di modifica; l'API di "
                         "WordPress è esclusa dal robots.txt")


class TelesurEnglish(_SitemapOrdinate):
    chiave, nome, dominio = "telesur", "teleSUR English", "telesurenglish.net"
    lingua = "en"
    INDICE = "https://www.telesurenglish.net/sitemap_index.xml"
    FINE_SITEMAP = date(2025, 11, 19)
    re_articolo = _re(dominio)
    note_ricerca_data = ("sitemap degli articoli (Yoast, 200 per file, dal più recente) dal luglio 2024 al 19 "
                         "novembre 2025, filtrate per data di modifica; dopo, le sitemap non sono aggiornate (usare "
                         "--fonte wayback); l'API di WordPress è esclusa dal robots.txt")


class CorreoDelOrinoco(_SitemapOrdinate):
    chiave, nome, dominio = "correodelorinoco", "Correo del Orinoco", "correodelorinoco.gob.ve"
    INDICE = "https://www.correodelorinoco.gob.ve/wp-sitemap.xml"
    RE_FILE = r"wp-sitemap-posts-post-(\d+)\.xml$"
    re_articolo = _re(dominio)

    MARGINE = 0

    def __init__(self):
        self._date = {}           # data di ogni articolo letta dalla sitemap (la pagina non la riporta)

    def _voci(self, rete, f):
        voci = super()._voci(rete, f)
        self._date.update({u: g for u, g in voci if g})
        return voci

    def estrai(self, html, url):
        """La pagina non dichiara la data dell'articolo (le date visibili sono degli articoli correlati):
        si usa quella della sitemap, che segue la numerazione degli articoli; altrimenti resta vuota."""
        art = super().estrai(html, url)
        g = self._date.get(url)
        art.data = f"{g.isoformat()}T00:00:00" if g else ""
        if not g:
            art.note = "; ".join(x for x in (art.note, "data non dichiarata dalla pagina") if x)
        return self.valuta(art)
    note_ricerca_data = ("sitemap di WordPress degli articoli (2000 per file) in ordine cronologico; le pagine non "
                         "dichiarano la data, quindi vale quella della sitemap (giorno, senza ora); l'API di WordPress "
                         "richiede l'accesso (401). Con link ed elenco la data resta vuota")


class Primicia(_SitemapOrdinate):
    chiave, nome, dominio = "primicia", "Primicia", "primicia.com.ve"
    INDICE = "https://primicia.com.ve/sitemap_index.xml"
    re_articolo = _re(dominio)
    note_ricerca_data = ("circa 176 sitemap degli articoli (Yoast) in ordine cronologico dal 2019, filtrate per data "
                         "di modifica; l'API di WordPress richiede l'accesso (401)")


class ElPitazo(_SitemapOrdinate):
    chiave, nome, dominio = "elpitazo", "El Pitazo", "elpitazo.net"
    INDICE = "https://elpitazo.net/sitemap.xml"
    AFFIDABILE_DAL = date(2025, 12, 1)
    re_articolo = _re(dominio)
    note_ricerca_data = ("sitemap degli articoli (Yoast) in ordine cronologico, filtrate per data di modifica; affidabile "
                         "dal dicembre 2025: gli articoli precedenti risultano modificati in blocco (gennaio 2019 e "
                         "fine 2025), quindi per quei periodi la ricerca per data è incompleta (meglio --fonte "
                         "wayback); anche l'API di WordPress restituisce solo gli articoli recenti")


class Informe21(_SitemapOrdinate):
    chiave, nome, dominio = "informe21", "Informe21", "informe21.com"
    INDICE = "https://www.informe21.com/sitemap.xml"
    RE_FILE = r"blog-posts_p_[0-9a-f]+-sitemap\.xml$"
    re_articolo = _re(dominio, r"post/[^/?#]+/?")
    note_ricerca_data = "sitemap del blog (piattaforma Wix), filtrate per data di modifica"

    def _files(self, rete):
        return [loc for loc, _ in SM.leggi_indice(rete, self.INDICE) if re.search(self.RE_FILE, loc)]


# ------------------------------------------------------------------ solo sitemap news
class Online2001(_Titolo, Testata):
    chiave, nome, dominio = "2001online", "2001online", "2001online.com"
    lingua = "es"
    re_articolo = _re(dominio, r"[a-z0-9-]+/[^/?#]+-\d{10,}/?")
    paginazione = None
    NEWS = "https://2001online.com/sitemap-news.xml"
    note_ricerca_data = ("solo la sitemap news (articoli degli ultimi giorni); per il passato --fonte wayback. "
                         "La ricerca /buscar/ è esclusa dal robots.txt")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        voci = [(u, _giorno(pub or lm)) for u, lm, pub in SM.leggi_urlset(rete, self.NEWS) if self.e_articolo(u)]
        urls = [u for u, g in voci if g and dal <= g <= al]
        minima = min((g for _, g in voci if g), default=None)
        log(f"  2001online: sitemap news, {len(urls)} articoli nel periodo")
        return [SorgenteURL("sitemap news", urls, _avviso(self.nome, minima, dal, "la sitemap news"))]


VENEZUELA = (ElNacional(), UltimasNoticias(), ElDiario(), Online2001(), CorreoDelOrinoco(), DiarioVea(),
             ElPitazo(), Runrunes(), CronicaUno(), ElEstimulo(), CaraotaDigital(), Informe21(), AVN(),
             TelesurEnglish(), Venezuelanalysis(), CaracasChronicles(), ElCarabobeno(), Primicia())


def _registra_motori():
    from .ricerca import MOTORI
    for t in VENEZUELA:
        if isinstance(t, _WordPress):
            MOTORI[t.chiave] = (t.motore_ricerca, "API REST di WordPress con ricerca e filtro per date", False)


_registra_motori()
