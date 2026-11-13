"""Classe base delle testate: riconoscimento degli URL, paginazione, estrazione dell'articolo."""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .. import comune as C
from ..modello import Articolo, SorgenteURL

FINE_COMUNE = ("riproduzione riservata",)


class NonSupportato(Exception):
    pass


def termini_ricerca(parole, finali=("",)):
    """Parole da passare ai motori di ricerca: senza asterisco (migrant* -> migrant), almeno 3 lettere.
    Ai motori che cercano solo parole intere si passano anche le forme con i finali indicati
    (migrant* -> migrant, migranta, migrante, migranti, migranto)."""
    out = []
    for p in parole:
        radice = p.replace("*", "").strip()
        out += [radice + f for f in finali] if p.strip().endswith("*") else [radice]
    return list(dict.fromkeys(t for t in out if len(t) >= 3))


class Testata:
    chiave = ""
    nome = ""
    dominio = ""
    re_articolo = None
    selettori_corpo = ()
    fine_testo = ()
    date_nell_url = False
    note_ricerca_data = ""

    # ------------------------------------------------ URL
    def riconosce(self, url):
        return self.dominio and self.dominio in urlparse(url).netloc

    def e_articolo(self, url):
        return bool(self.re_articolo and self.re_articolo.search(url))

    def normalizza(self, url):
        return url.split("#")[0].split("?")[0]

    def data_da_url(self, url):
        return C.data_da_url(url) if self.date_nell_url else None

    def wayback_prefissi(self, dal, al):
        """Prefissi da chiedere all'indice CDX della Wayback Machine: (url, matchType). Più sono stretti,
        più l'indice risponde in fretta; le testate con la data nel percorso li danno per giorno."""
        return [(self.dominio, "domain")]

    paginazione = None   # es. "{base}page/{n}/": come si ottiene la pagina n di un elenco
    elenchi_prova = ()   # pagine elenco su cui il collaudo verifica la paginazione

    def pagina_elenco(self, base, n):
        """URL della pagina n di un elenco; None se la testata non pagina."""
        if n == 1:
            return base
        if self.paginazione:
            b = base if base.endswith("/") or "?" in self.paginazione[:7] else base + "/"
            return self.paginazione.format(base=b if not self.paginazione.startswith("{base}?") else base, n=n)
        return None

    def link_articoli(self, html, url_pagina):
        soup = BeautifulSoup(html, "lxml")
        visti, out = set(), []
        for a in soup.find_all("a", href=True):
            u = self.normalizza(urljoin(url_pagina, a["href"]))
            if u not in visti and self.e_articolo(u):
                visti.add(u)
                out.append(u)
        return out

    # ------------------------------------------------ ricerca per data
    def piano_per_data(self, rete, dal, al, log, parole=None):
        raise NonSupportato(f"{self.nome}: ricerca per data non disponibile")

    # ------------------------------------------------ ricerca per parole
    nota_ricerca = ""   # descrizione del motore di ricerca della testata, per la scheda

    def piano_per_parole(self, rete, parole, dal, al, log):
        """Sorgenti dal motore di ricerca della testata; None se non c'è o se il robots.txt lo esclude.
        Le parole trovate dal motore vengono comunque verificate sull'articolo scaricato."""
        from .ricerca import FINALI, MOTORI, FuoriPortata
        if self.chiave not in MOTORI:
            return None
        motore, self.nota_ricerca, intere = MOTORI[self.chiave]
        termini = termini_ricerca(parole, FINALI if intere else ("",))
        if not termini:
            return None
        urls = []
        for t in termini:
            try:
                trovati = [self.normalizza(u) for u in motore(rete, t, dal, al) if self.e_articolo(self.normalizza(u))]
            except FuoriPortata as e:
                log(f"  {self.nome}: {e}; per questo periodo si usa l'archivio per data")
                return None
            log(f"  {self.nome}: la ricerca del sito per «{t}» propone {len(trovati)} articoli")
            urls += trovati
        desc = ", ".join(p.strip() for p in parole) + (f" (cercate come: {', '.join(termini)})" if intere else "")
        return [SorgenteURL(f"ricerca del sito per «{desc}»", list(dict.fromkeys(urls)))]

    # ------------------------------------------------ estrazione
    def tag_pagina(self, soup):
        return C.meta(soup, "article:tag")

    def corpo(self, soup, html):
        par, metodo = C.corpo_selettori(soup, self.selettori_corpo)
        if par:
            return par, metodo
        denso, m_denso = C.corpo_denso(soup)
        traf, m_traf = C.corpo_trafilatura(html)
        l_d, l_t = sum(map(len, denso)), sum(map(len, traf))
        if l_d >= 300 and l_d >= 0.6 * l_t:
            return denso, m_denso
        return (traf, m_traf) if l_t else (denso, m_denso)

    def estrai(self, html, url):
        soup = C.soup_di(html)
        jl = C.json_ld(soup)
        h1 = soup.find("h1")
        titolo = C.testo_pulito(C.primo(h1.get_text(" ", strip=True) if h1 else "",
                                        jl.get("titolo"), C.meta(soup, "og:title")))
        sommario = C.testo_pulito(C.primo(C.meta(soup, "description"),
                                          C.meta(soup, "og:description"), jl.get("descrizione")))
        data = C.parse_data(C.primo(jl.get("data"), C.meta(soup, "article:published_time")))
        if data is None:
            meta_t = trafilatura_data(html)
            data = C.parse_data(meta_t)
        sommario = self.pulisci_sommario(sommario)
        par, metodo = self.corpo(soup, html)
        par = C.togli_intestazione(par, titolo, sommario)
        par = C.taglia_a(par, tuple(self.fine_testo) + FINE_COMUNE)
        while par and par[-1].startswith(("- ", "• ")):   # elenchi di articoli correlati in coda
            par = par[:-1]
        testo = "\n".join(par)
        if C.sommario_ridondante(sommario, testo):
            sommario = ""
        elif sommario and par:
            # prima riga = occhiello + sommario (es. «Regionali Contro Occhiuto…»): è intestazione
            norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()
            if norm(par[0]).endswith(norm(sommario)) and len(par[0]) - len(sommario) < 60:
                par = par[1:]
                testo = "\n".join(par)
        tag = list(dict.fromkeys([t for t in (jl.get("tag") or []) + self.tag_pagina(soup) if t]))
        autori = [a for a in (jl.get("autori") or C.meta(soup, "author")) if a and not str(a).startswith("@")]
        art = Articolo(
            url=url, testata=self.nome, titolo=titolo, sommario=sommario, testo=testo,
            data=data.isoformat() if data else "", autori=[a for a in autori if a],
            sezione=C.testo_pulito(C.primo(jl.get("sezione"), C.meta(soup, "article:section"),
                                           self.sezione_da_url(url))),
            tag=tag, accesso_libero=jl.get("libero"), metodo=metodo,
        )
        return self.valuta(art, soup)

    def sezione_da_url(self, url):
        return ""

    def pulisci_sommario(self, s):
        return s

    def valuta(self, art, soup=None):
        art.coerenza = C.coerenza(art.titolo, art.sommario, art.testo)
        art.virgolettati = C.virgolettati(art.testo)
        # le diciture sugli abbonati compaiono spesso nell'interfaccia: contano solo se sono nel testo.
        # Un articolo dichiarato riservato può avere comunque il testo integrale nella pagina.
        art.parziale = bool(C.SEGNALI_PAYWALL.search(art.testo)) or \
            (art.accesso_libero is False and (len(art.testo) < 600 or
                                              art.testo.rstrip().endswith(("...", "…"))))
        note = []
        if len(art.testo) < 150:
            note.append("testo molto breve")
        if art.coerenza < 0.25:
            note.append("testo poco coerente con il titolo")
        if not art.data:
            note.append("data mancante")
        if art.parziale:
            note.append("testo parziale")
        if art.accesso_libero is False:
            note.append("dichiarato riservato agli abbonati")
        art.sospetto = len(art.testo) < 150 or art.coerenza < 0.25
        art.note = "; ".join(note)
        return art


def trafilatura_data(html):
    try:
        import trafilatura
        m = trafilatura.extract_metadata(html)
        return m.date if m else ""
    except Exception:
        return ""


class Generica(Testata):
    """Qualsiasi sito non coperto da un modulo dedicato: estrazione generica."""
    chiave = "generica"
    nome = "Altra fonte"

    def riconosce(self, url):
        return True

    def e_articolo(self, url):
        return True

    def estrai(self, html, url):
        art = super().estrai(html, url)
        art.testata = urlparse(url).netloc.replace("www.", "")
        return art
