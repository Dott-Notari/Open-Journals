"""Esecuzione di un'estrazione: sorgenti, scorrimento delle pagine elenco, filtri, ripresa, output."""
import json
import re
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from . import comune as C
from . import formati as F
from .config import FORMATI, LIMITE_PAGINE, STOP_VECCHI, VERSIONE, radice_locale
from .destinazioni import CartellaLocale
from .modello import Articolo, Parametri, SorgenteElenco, SorgenteURL
from .rete import Bloccato, Rete
from .testate import GENERICA, TESTATE, NonSupportato, per_url


# ======================================================================== scorrimento elenchi
class Scorrimento:
    """Scorre una pagina elenco paginata. Se c'è un intervallo di date, salta direttamente alla
    pagina giusta con una ricerca binaria e si ferma quando gli articoli diventano troppo vecchi."""

    def __init__(self, testata, sorgente, rete, dal=None, al=None, log=print):
        self.t, self.s, self.rete = testata, sorgente, rete
        self.dal, self.al, self.log = dal, al, log
        self.visti, self.comuni = set(), set()
        self.vecchi, self.fermo = 0, False
        self.pagine_lette, self.partenza = 0, 1
        self.firme, self.data_minima, self.esaurito = {}, None, False

    def pagina(self, n):
        url = self.t.pagina_elenco(self.s.base, n)
        if url is None:
            return None
        r = self.rete.get(url, cache=True)
        if r is None or r.status_code != 200:
            return None
        links = self.t.link_articoli(r.text, url)
        if self.s.filtro:
            links = [l for l in links if self.s.filtro in l]
        # oltre il limite di paginazione alcuni siti ripetono sempre l'ultima pagina disponibile
        firma = tuple(links)
        if links:
            proprietaria = min(self.firme.get(firma, n), n)
            self.firme[firma] = proprietaria
            if n > proprietaria:
                return None
        return links

    def data_pagina(self, n):
        links = [l for l in (self.pagina(n) or []) if l not in self.comuni]
        if not links:
            return None
        l = links[min(2, len(links) - 1)]
        d = self.t.data_da_url(l)
        if d:
            return d
        r = self.rete.get(l, cache=True)
        if r is None or r.status_code != 200:
            return None
        try:
            return self.t.estrai(r.text, l).giorno()
        except Exception:
            return None

    def _partenza(self):
        if not (self.s.usa_date and self.al) or self.al >= date.today():
            return 1
        if self.t.pagina_elenco(self.s.base, 2) is None:
            return 1
        lo, hi = 1, 2
        while hi <= LIMITE_PAGINE:
            d = self.data_pagina(hi)
            if d is None or d <= self.al:
                break
            lo, hi = hi, hi * 2
        while hi - lo > 1:
            mid = (lo + hi) // 2
            d = self.data_pagina(mid)
            if d is None or d <= self.al:
                hi = mid
            else:
                lo = mid
        if lo > 1:
            self.log(f"    salto direttamente alla pagina {lo}")
        return lo

    def avviso(self):
        """Messaggio se l'elenco è finito prima di arrivare alla data iniziale richiesta."""
        if self.esaurito and self.dal and self.s.usa_date and \
                (self.data_minima is None or self.data_minima > self.dal):
            fino = self.data_minima.isoformat() if self.data_minima else "nessuna data utile"
            return (f"{self.s.descrizione}: l'elenco consultabile online si ferma al {fino}, "
                    f"i giorni precedenti non sono raggiungibili da questa sorgente")
        return ""

    def segnala(self, d):
        """Il chiamante comunica la data di ogni articolo incontrato."""
        if d is not None:
            self.data_minima = d if self.data_minima is None else min(self.data_minima, d)
        if d is None or not self.s.usa_date or self.dal is None:
            return
        if d < self.dal:
            self.vecchi += 1
            if self.vecchi >= STOP_VECCHI:
                self.fermo = True
        elif self.al is None or d <= self.al:
            self.vecchi = 0

    def __iter__(self):
        p1, p2 = self.pagina(1) or [], self.pagina(2) or []
        self.comuni = set(p1) & set(p2)      # link ripetuti su ogni pagina (in evidenza, colonne)
        n = self.partenza = self._partenza()
        while n <= LIMITE_PAGINE and not self.fermo:
            links = self.pagina(n)
            if not links:
                self.esaurito = True
                break
            nuovi = [l for l in links if l not in self.visti]
            if not nuovi:
                self.esaurito = True
                break
            self.pagine_lette += 1
            for l in nuovi:
                self.visti.add(l)
                yield l
                if self.fermo:
                    return
            n += 1


# ======================================================================== stato e ripresa
class Lavoro:
    def __init__(self, cartella_lavoro, parametri: Parametri):
        self.dir = Path(cartella_lavoro) if cartella_lavoro else None
        self.parametri = parametri
        self.fatti, self.articoli, self.errori, self.sorgenti, self.avvisi = {}, [], [], [], []
        self.inizio = datetime.now().isoformat(timespec="seconds")
        self.completata = False
        self._da_salvare = 0
        if self.dir:
            self.dir.mkdir(parents=True, exist_ok=True)
            st = self.dir / "stato.json"
            if st.exists():
                d = json.loads(st.read_text(encoding="utf-8"))
                self.fatti, self.errori = d.get("fatti", {}), d.get("errori", [])
                # alla ripresa gli avvisi di arresto della sessione precedente non valgono più
                self.avvisi = [a for a in d.get("avvisi", []) if not a.startswith("estrazione fermata dopo")]
                self.inizio = d.get("inizio", self.inizio)
                arts = self.dir / "articoli.jsonl"
                if arts.exists():
                    self.articoli = [Articolo.from_dict(json.loads(r))
                                     for r in arts.read_text(encoding="utf-8").splitlines() if r]

    def ripresa(self):
        return bool(self.fatti)

    def registra(self, url, esito, motivo="", art=None, html=None):
        self.fatti[url] = {"esito": esito, "motivo": motivo}
        if esito == "errore":
            self.errori.append(f"{url}  {motivo}")
        if art is not None:
            self.articoli.append(art)
            if self.dir:
                with open(self.dir / "articoli.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(art.to_dict(), ensure_ascii=False) + "\n")
                if html:
                    g = self.dir / "html_grezzi"
                    g.mkdir(exist_ok=True)
                    (g / f"{len(self.articoli):05d}_{F.ascii_slug(art.titolo, 40)}.html").write_text(
                        html, encoding="utf-8")
        self._da_salvare += 1
        if self._da_salvare >= 10:
            self.salva()

    def salva(self):
        self._da_salvare = 0
        if self.dir:
            (self.dir / "stato.json").write_text(json.dumps({
                "parametri": self.parametri.chiave_ripresa(), "inizio": self.inizio,
                "completata": self.completata, "fatti": self.fatti, "errori": self.errori,
                "avvisi": self.avvisi,
            }, ensure_ascii=False, indent=1), encoding="utf-8")

    def conteggi(self):
        return Counter(v["esito"] for v in self.fatti.values())


def descrittore(p: Parametri):
    if p.modalita == "link":
        base = f"link-{len(p.link)}"
    elif p.modalita == "elenco":
        parti = [x for x in re.sub(r"https?://[^/]+", "", p.elenco or "").split("/") if x]
        base = "elenco-" + F.ascii_slug("-".join(parti[-2:]) or "home", 40)
    else:
        base = "data"
    if p.parole:
        base += "_" + F.ascii_slug("-".join(p.parole), 40)
    if p.dal or p.al:
        base += f"_{p.dal or 'inizio'}_{p.al or 'oggi'}"
    return base


def cartella_per(p: Parametri, radice=None):
    """Cartella dell'estrazione: riusa quella di un'estrazione identica rimasta a metà."""
    radice = Path(radice) if radice else radice_locale()
    if p.testata:
        sotto = p.testata
    else:
        chiavi = {per_url(u).chiave for u in p.link} if p.link else {per_url(p.elenco or "").chiave}
        sotto = chiavi.pop() if len(chiavi) == 1 else "misti"
    base = radice / sotto
    desc = descrittore(p)
    if base.exists():
        for c in sorted(base.iterdir(), reverse=True):
            st = c / "_lavoro" / "stato.json"
            if c.is_dir() and c.name.endswith(desc) and st.exists():
                d = json.loads(st.read_text(encoding="utf-8"))
                if not d.get("completata") and d.get("parametri") == p.chiave_ripresa():
                    return c
    nuova, k = base / f"{date.today().isoformat()}_{desc}", 2
    while nuova.exists():               # un'estrazione identica già completata oggi: nuova cartella
        nuova, k = base / f"{date.today().isoformat()}_{desc}_{k}", k + 1
    return nuova


# ======================================================================== esecuzione
def sorgenti_per(p: Parametri, rete, log):
    if p.modalita == "link":
        gruppi = {}
        for u in p.link:
            gruppi.setdefault(per_url(u).chiave, []).append(u)
        return [(TESTATE.get(k, GENERICA), SorgenteURL("link inseriti", us)) for k, us in gruppi.items()]
    if p.modalita == "elenco":
        t = TESTATE.get(p.testata) if p.testata else per_url(p.elenco)
        return [(t, SorgenteElenco(f"elenco {p.elenco}", p.elenco))]
    t = TESTATE[p.testata]
    return [(t, s) for s in t.piano_per_data(rete, p.d_dal(), p.d_al(), log, parole=p.parole)]


def esegui(p: Parametri, destinazione=None, cartella_lavoro=None, rete=None, log=print,
           progresso=None, salva_grezzi=True, tempo_max=None):
    """Esegue l'estrazione. Uso locale: destinazione=CartellaLocale, cartella_lavoro=<cartella>/_lavoro.
    Piattaforma: destinazione=ZipMemoria, cartella_lavoro=None. Restituisce destinazione.chiudi()."""
    rete = rete or Rete(log=log)
    lav = Lavoro(cartella_lavoro, p)
    if lav.ripresa():
        log(f"Riprendo un'estrazione interrotta: {len(lav.fatti)} indirizzi già esaminati, "
            f"{len(lav.articoli)} articoli già raccolti.")
    dal, al = p.d_dal(), p.d_al()
    pat = C.compila_parole(p.parole)
    pat_ascii = C.compila_parole([C.piega(x) for x in p.parole])
    t0, interrotta = time.monotonic(), False
    try:
        for testata, sorg in sorgenti_per(p, rete, log):
            lav.sorgenti.append(f"{testata.nome}: {sorg.descrizione}")
            if getattr(sorg, "avviso", "") and sorg.avviso not in lav.avvisi:
                lav.avvisi.append(sorg.avviso)
                log(f"  ATTENZIONE: {sorg.avviso}")
            log(f"> {testata.nome}: {sorg.descrizione}")
            scorr = Scorrimento(testata, sorg, rete, dal, al, log) if isinstance(sorg, SorgenteElenco) else None
            for url in (scorr if scorr else sorg.urls):
                if p.max_articoli and len(lav.articoli) >= p.max_articoli:
                    break
                if tempo_max and time.monotonic() - t0 > tempo_max:
                    raise TimeoutError
                t = testata if testata.riconosce(url) else per_url(url)
                url = t.normalizza(url)
                if url in lav.fatti:
                    continue
                d_url = t.data_da_url(url)
                if d_url and p.modalita != "link":
                    if scorr:
                        scorr.segnala(d_url)
                    if (dal and d_url < dal) or (al and d_url > al):
                        lav.registra(url, "fuori_intervallo")
                        continue
                if pat and p.cerca_in == "titolo" and p.modalita != "link" and \
                        not C.corrisponde(pat_ascii, C.piega(C.slug_url(url)), p.tutte):
                    lav.registra(url, "parole_assenti", "titolo (dall'indirizzo)")
                    continue
                r = rete.get(url, cache=True)
                if r is None or r.status_code != 200:
                    lav.registra(url, "errore", f"HTTP {r.status_code if r is not None else 'nessuna risposta'}")
                    continue
                try:
                    art = t.estrai(r.text, url)
                except Exception as e:  # una pagina anomala non ferma l'estrazione
                    lav.registra(url, "errore", f"estrazione: {e!r}")
                    continue
                g = art.giorno()
                if scorr:
                    scorr.segnala(g)
                if p.modalita != "link" and g and ((dal and g < dal) or (al and g > al)):
                    lav.registra(url, "fuori_intervallo")
                    continue
                if p.escludi_riservati and art.accesso_libero is False:
                    lav.registra(url, "riservato")
                    continue
                campo = f"{art.titolo} {art.sommario} {' '.join(art.tag)}" + \
                    (f" {art.testo}" if p.cerca_in == "testo" else "")
                if not C.corrisponde(pat, campo, p.tutte):
                    lav.registra(url, "parole_assenti")
                    continue
                lav.registra(url, "ok", art=art, html=r.text if salva_grezzi else None)
                n = len(lav.articoli)
                log(f"  [{n}] {art.data[:10] or '----------'}  {art.titolo[:90]}"
                    + ("   (DA CONTROLLARE)" if art.sospetto else ""))
                if progresso:
                    progresso(n, len(lav.fatti))
            if scorr and scorr.avviso() and scorr.avviso() not in lav.avvisi:
                lav.avvisi.append(scorr.avviso())
                log(f"  ATTENZIONE: {scorr.avviso()}")
    except KeyboardInterrupt:
        interrotta = True
        log("\nInterrotta. Rilancia lo stesso comando per riprendere da dove si è fermata.")
    except TimeoutError:
        interrotta = True
        lav.avvisi.append(f"estrazione fermata dopo {tempo_max / 60:.0f} minuti per il limite di tempo impostato")
        log(f"\nFermata per il limite di tempo ({tempo_max / 60:.0f} minuti).")
    except Bloccato as e:
        interrotta = True
        log(f"\nIl sito ha bloccato le richieste: {e}. Riprova più tardi con lo stesso comando, "
            f"eventualmente aumentando la pausa (--pausa 4).")
    lav.completata = not interrotta
    lav.salva()
    durata = time.monotonic() - t0
    destinazione = destinazione or CartellaLocale(Path.cwd())
    scrivi_output(lav, p, destinazione, durata, rete)
    return destinazione.chiudi()


def scrivi_output(lav, p, dest, durata, rete):
    arts = sorted(lav.articoli, key=lambda a: (a.data or "9999", a.titolo))
    for i, a in enumerate(arts, 1):
        a.id = i
    formati = p.formati or list(FORMATI)
    if hasattr(dest, "pulisci"):
        dest.pulisci(("docx", "txt", "html"))
    titolo = f"Corpus {descrittore(p)}"
    for a in arts:
        nome = F.nome_file(a)
        if "docx" in formati:
            dest.scrivi(f"docx/{nome}.docx", F.docx_articolo(a))
        if "txt" in formati:
            dest.scrivi(f"txt/{nome}.txt", F.txt_articolo(a))
        if "html" in formati:
            dest.scrivi(f"html/{nome}.html", F.html_articolo(a))
    if arts:
        if "docx" in formati:
            dest.scrivi("corpus_completo.docx", F.docx_corpus(arts, titolo))
        if "xlsx" in formati:
            dest.scrivi("indice_articoli.xlsx", F.xlsx_indice(arts))
        if "jsonl" in formati:
            dest.scrivi("corpus.jsonl", F.jsonl(arts))
        if "tlab" in formati:
            dest.scrivi("corpus_tlab.txt", F.tlab(arts))
    dest.scrivi("scheda_estrazione.txt", scheda(lav, p, arts, durata, rete))


def scheda(lav, p, arts, durata, rete):
    c = lav.conteggi()
    testate = sorted({a.testata for a in arts}) or ([TESTATE[p.testata].nome] if p.testata in TESTATE else [])
    note_data = {TESTATE[k].nome: TESTATE[k].note_ricerca_data for k in TESTATE
                 if TESTATE[k].nome in testate and TESTATE[k].note_ricerca_data}
    metodi = Counter(a.metodo for a in arts)
    R = ["SCHEDA DI ESTRAZIONE", "=" * 60,
         f"Strumento: Scraper didattico testate, versione {VERSIONE}",
         f"Avvio: {lav.inizio}    Fine: {datetime.now().isoformat(timespec='seconds')}"
         f"    Durata di questa sessione: {durata / 60:.1f} minuti",
         f"Stato: {'completata' if lav.completata else 'INTERROTTA (rilanciare per completare)'}", "",
         "PARAMETRI",
         f"  Testata: {', '.join(testate) or '-'}",
         f"  Modalità: {p.modalita}"]
    if p.elenco:
        R.append(f"  Pagina elenco di partenza: {p.elenco}")
    if p.link:
        R.append(f"  Link inseriti: {len(p.link)}")
    R += [f"  Intervallo: {p.dal or '-'} / {p.al or '-'}",
          f"  Parole chiave: {', '.join(p.parole) or 'nessuna'}"
          + (f" ({'tutte' if p.tutte else 'almeno una'}, cercate nel {'solo titolo e sommario' if p.cerca_in == 'titolo' else 'titolo, sommario e testo'})" if p.parole else ""),
          f"  Limite articoli: {p.max_articoli or 'nessuno'}",
          f"  Articoli riservati agli abbonati: {'esclusi' if p.escludi_riservati else 'inclusi'}",
          f"  Formati: {', '.join(p.formati or FORMATI)}", "",
          "SORGENTI CONSULTATE"] + [f"  {s}" for s in lav.sorgenti]
    for nome, nota in note_data.items():
        R.append(f"  Nota su {nome}: {nota}")
    R += ["", "ESITI",
          f"  Indirizzi esaminati: {len(lav.fatti)}",
          f"  Articoli raccolti: {len(arts)}",
          f"  Fuori dall'intervallo di date: {c.get('fuori_intervallo', 0)}",
          f"  Scartati perché senza le parole chiave: {c.get('parole_assenti', 0)}",
          f"  Scartati perché riservati agli abbonati: {c.get('riservato', 0)}",
          f"  Errori: {c.get('errore', 0)}",
          f"  Articoli dichiarati riservati agli abbonati: {sum(a.accesso_libero is False for a in arts)}"
          f" (di cui con testo parziale: {sum(a.parziale and a.accesso_libero is False for a in arts)})",
          f"  Articoli con testo parziale: {sum(a.parziale for a in arts)}",
          f"  Articoli da controllare (testo breve o poco coerente col titolo): {sum(a.sospetto for a in arts)}",
          f"  Richieste di rete in questa sessione: {rete.richieste}", "",
          "MODALITÀ DI ESTRAZIONE DEL TESTO"]
    R += [f"  {m or 'non determinata'}: {n} articoli" for m, n in metodi.most_common()]
    if lav.avvisi:
        R += ["", "AVVISI SULLA COPERTURA"] + [f"  {a}" for a in lav.avvisi]
    sosp = [a for a in arts if a.sospetto or a.parziale or a.accesso_libero is False]
    if sosp:
        R += ["", "ARTICOLI DA CONTROLLARE"] + [f"  {a.id:04d}  {a.note}  {a.url}" for a in sosp]
    if lav.errori:
        R += ["", "ERRORI"] + [f"  {e}" for e in lav.errori[:200]]
    R += ["", "NOTE METODOLOGICHE",
          "  Le date sono quelle di pubblicazione dichiarate da ciascun articolo, in ora italiana.",
          "  Il corpus riflette ciò che la testata rende disponibile online al momento dell'estrazione,",
          "  che per gli anni meno recenti può non coincidere con quanto pubblicato in edizione cartacea.",
          "  L'indicatore di coerenza misura la quota di parole del titolo presenti nell'avvio del testo:",
          "  valori bassi segnalano estrazioni da verificare a mano.",
          "  I testi sono raccolti per finalità di studio e ricerca e non vanno ridistribuiti."]
    return "\n".join(R) + "\n"
