"""Classi generiche per le testate con sitemap «a intervalli» o a file fissi (dalla 1.16).

- _Intervalli: un indice elenca sitemap che coprono un giorno, una settimana o un mese, riconoscibili dal nome
  (gruppi nominati della regex RE_FILE: a = anno, m = mese, g = giorno, s = settimana ISO). Si leggono solo i
  file che si sovrappongono al periodo, serie per serie.
- _FileFissi: poche sitemap sempre uguali (spesso solo le uscite recenti).

In entrambi i casi la data di ogni voce si prende dall'indirizzo (DATA_URL, stessi gruppi più y = anno a due
cifre) quando c'è; altrimenti dalla data di pubblicazione o di ultima modifica, tenendo le voci modificate nel
periodo o nei MARGINE giorni successivi (FILTRO_LASTMOD), oppure tutte (per i file di un solo giorno)."""
import re
from datetime import date, timedelta

from .base import Testata
from .napoli import _giorno
from .seconda_ondata import _avviso
from .venezuela import _Titolo
from .. import comune as C
from .. import sitemap as SM
from ..modello import SorgenteURL


def re_dominio(dominio, escludi=r"(?!authors?/|autor(?:es)?/|auteurs?/|tags?/|temas?/|search|buscar|recherche)"):
    """Indirizzi degli articoli: il dominio e almeno uno slug con un trattino (esclude home e sezioni)."""
    return re.compile(rf"^https?://(?:www\.)?{re.escape(dominio)}/{escludi}(?:[^/?#]+/)*[^/?#]*-[^/?#]*/?$")


def _data_da_gruppi(gd):
    try:
        anno = int(gd["a"]) if gd.get("a") else 2000 + int(gd["y"])
        if gd.get("s"):
            return date.fromisocalendar(anno, int(gd["s"]), 1)
        return date(anno, int(gd.get("m") or 1), int(gd.get("g") or 1))
    except (KeyError, TypeError, ValueError):
        return None


class _ConDate(_Titolo, Testata):
    DATA_URL = None          # regex con gruppi nominati per la data nell'indirizzo
    FILTRO_LASTMOD = True
    MARGINE = 7
    INIZIO = None
    paginazione = None

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def data_url(self, u):
        if self.DATA_URL:
            m = re.search(self.DATA_URL, u)
            return _data_da_gruppi(m.groupdict()) if m else None
        return C.data_da_url(u) if self.date_nell_url else None

    def data_da_url(self, url):
        return self.data_url(url)

    def _voci_file(self, rete, f):
        """Voci di una sitemap; se è un indice, quelle dei file che elenca."""
        voci = SM.leggi_urlset(rete, f)
        if voci and not all(re.search(r"\.xml(\.gz)?$", u) for u, _, _ in voci[:5]):
            return voci
        out = []
        for loc, _ in SM.leggi_indice(rete, f):
            if loc != f:
                out += SM.leggi_urlset(rete, loc)
        return out or voci

    def _filtra(self, rete, files, dal, al):
        tetto = al + timedelta(days=self.MARGINE)
        tenute, minima = {}, None
        for f in files:
            for u, lastmod, pub in self._voci_file(rete, f):
                if not self.e_articolo(u):
                    continue
                gu = self.data_url(u)
                g = gu or _giorno(pub or lastmod)
                if g:
                    minima = g if minima is None else min(minima, g)
                if gu:
                    if dal <= gu <= al:
                        tenute[u] = gu
                elif not self.FILTRO_LASTMOD:
                    tenute[u] = g or al
                elif g and dal <= g <= tetto:
                    tenute[u] = g
        urls = sorted(tenute, key=lambda u: (tenute[u] > al, -tenute[u].toordinal()))
        return urls, minima


class _Intervalli(_ConDate):
    INDICI = ()
    RE_FILE = ""

    def _scegli(self, rete, dal, al):
        serie = {}
        for indice in self.INDICI:
            for loc, _ in SM.leggi_indice(rete, indice):
                m = re.search(self.RE_FILE, loc)
                if not m:
                    continue
                inizio = _data_da_gruppi(m.groupdict())
                if inizio:
                    serie.setdefault(loc[:m.start()] + "#" + loc[m.end():], []).append((inizio, loc))
        scelti, prima = [], None
        for voci in serie.values():
            inizi = sorted({i for i, _ in voci})
            prima = inizi[0] if prima is None else min(prima, inizi[0])
            buoni = {i for k, i in enumerate(inizi)
                     if i <= al and (k + 1 == len(inizi) or inizi[k + 1] > dal)}
            scelti += [loc for i, loc in sorted(voci, reverse=True) if i in buoni]
        return scelti, prima

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files, prima = self._scegli(rete, dal, al)
        urls, _ = self._filtra(rete, files, dal, al)
        log(f"  {self.nome}: {len(files)} sitemap del periodo, {len(urls)} articoli da verificare")
        avvisi = [_avviso(self.nome, self.INIZIO or prima, dal)]
        if not files:
            avvisi.append(f"{self.nome}: nessuna sitemap per il periodo richiesto")
        return [SorgenteURL(f"sitemap per periodo ({len(files)})", urls, "; ".join(a for a in avvisi if a))]


class _FileFissi(_ConDate):
    FILES = ()
    SOLO_RECENTI = True       # le sitemap coprono solo le uscite recenti: avviso se il periodo è più vecchio

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls, minima = self._filtra(rete, self.FILES, dal, al)
        log(f"  {self.nome}: {len(self.FILES)} sitemap, {len(urls)} articoli da verificare")
        avviso = _avviso(self.nome, minima, dal, "le sitemap") if self.SOLO_RECENTI else ""
        if avviso:
            avviso += "; per i giorni precedenti usare --fonte wayback"
        return [SorgenteURL("sitemap" + (" delle uscite recenti" if self.SOLO_RECENTI else ""), urls, avviso)]
