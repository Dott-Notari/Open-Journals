"""Rassegna stampa: una sola estrazione su più testate, con un corpus unico.

Ogni testata è interrogata con il suo metodo migliore (ricerca del sito se ci sono parole chiave e la testata
la consente, altrimenti archivio per data), con le stesse regole delle estrazioni singole: robots.txt,
pause, nessun aggiramento di paywall. Il risultato ha la struttura di una normale estrazione (un file per
articolo, corpus Word, indice Excel, JSONL, T-LAB con la variabile *TESTATA) e una scheda della rassegna;
in testate/<chiave>/ restano la scheda di ciascuna testata e, in locale, lo stato per la ripresa.

Uso locale:      python scraper.py rassegna napoli,verita --dal 2026-01-01 --al 2026-01-31 --parole "migrant*"
Piattaforma:     esegui_rassegna(p, ["calcionapoli1926", "ilnapolista"], ZipMemoria(), None)"""
import json
import time
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from .config import FORMATI, VERSIONE, radice_locale
from .esecuzione import descrittore, esegui, scrivi_corpus
from .formati import ascii_slug
from .modello import Parametri
from .rete import Rete
from .testate import GRUPPI, TESTATE, NonSupportato

SOLO_SCHEDA = ("scheda_estrazione.txt",)


class _Sottocartella:
    """Destinazione delle singole testate dentro la rassegna: si conserva solo la loro scheda
    (gli articoli finiscono nel corpus unico, senza doppioni di file)."""

    def __init__(self, dest, prefisso):
        self.dest, self.prefisso = dest, prefisso

    def scrivi(self, rel, dati):
        if rel in SOLO_SCHEDA:
            self.dest.scrivi(f"{self.prefisso}/{rel}", dati)

    def chiudi(self):
        return None


def chiavi_rassegna(testate):
    """Chiavi da una lista o da una stringa con chiavi e gruppi separati da virgola (es. «napoli,verita»)."""
    if isinstance(testate, str):
        testate = [x.strip() for x in testate.split(",") if x.strip()]
    out = []
    for x in testate:
        out += GRUPPI.get(x.lower(), [x])
    ignote = [k for k in out if k not in TESTATE]
    if ignote:
        raise NonSupportato(f"testate non previste: {', '.join(ignote)}")
    return list(dict.fromkeys(out))


def descrittore_rassegna(p, chiavi):
    nomi = "-".join(chiavi) if len(chiavi) <= 3 else f"{len(chiavi)}testate"
    return f"rassegna-{ascii_slug(nomi, 40)}_{descrittore(replace(p, testata=None))}"


def cartella_rassegna(p, chiavi, radice=None):
    """Cartella in _rassegna/: riusa quella di una rassegna stampa identica rimasta a metà."""
    base = Path(radice or radice_locale()) / "_rassegna"
    desc = descrittore_rassegna(p, chiavi)
    firma = {"parametri": p.chiave_ripresa(), "testate": chiavi}
    if base.exists():
        for c in sorted(base.iterdir(), reverse=True):
            st = c / "_rassegna.json"
            if c.is_dir() and c.name.endswith(desc) and st.exists():
                d = json.loads(st.read_text(encoding="utf-8"))
                if not d.get("completata") and d.get("firma") == firma:
                    return c
    nuova, n = base / f"{date.today().isoformat()}_{desc}", 2
    while nuova.exists():
        nuova = base / f"{date.today().isoformat()}_{desc}_{n}"
        n += 1
    return nuova


def esegui_rassegna(p: Parametri, testate, destinazione, cartella=None, rete=None, log=print,
                  salva_grezzi=True, tempo_max=None):
    """p: parametri come per modalita="data" (testata ignorata). testate: chiavi o gruppi.
    destinazione: CartellaLocale o ZipMemoria. cartella: cartella locale della rassegna (per la ripresa),
    None sulla piattaforma. tempo_max vale per l'insieme delle testate. Restituisce destinazione.chiudi()."""
    if p.modalita != "data":
        raise NonSupportato("La rassegna stampa funziona per intervallo di date (modalita=data)")
    chiavi = chiavi_rassegna(testate)
    rete = rete or Rete(log=log)
    t0, inizio = time.monotonic(), datetime.now().isoformat(timespec="seconds")
    firma = {"parametri": p.chiave_ripresa(), "testate": chiavi}
    stato_file = Path(cartella) / "_rassegna.json" if cartella else None
    if stato_file:
        stato_file.parent.mkdir(parents=True, exist_ok=True)
        stato_file.write_text(json.dumps({"firma": firma, "completata": False, "inizio": inizio}), encoding="utf-8")
    righe, articoli, interrotta = [], [], False
    for k in chiavi:
        t = TESTATE[k]
        log(f"\n{'=' * 70}\n{t.nome}  ({chiavi.index(k) + 1} di {len(chiavi)})\n{'=' * 70}")
        residuo = None
        if tempo_max:
            residuo = tempo_max - (time.monotonic() - t0)
            if residuo <= 0:
                righe.append((t.nome, "non avviata: limite di tempo raggiunto", None))
                interrotta = True
                continue
        esito = {}
        try:
            esegui(replace(p, testata=k), _Sottocartella(destinazione, f"testate/{k}"),
                   Path(cartella) / "testate" / k / "_lavoro" if cartella else None,
                   rete=rete, log=log, salva_grezzi=salva_grezzi, tempo_max=residuo, esito=esito)
        except NonSupportato as e:
            log(str(e))
            righe.append((t.nome, f"saltata: {e}", None))
            continue
        articoli += esito.get("articoli", [])
        righe.append((t.nome, "completata" if esito.get("completata") else "INTERROTTA", esito))
        if not esito.get("completata"):
            interrotta = True
            if not tempo_max:       # Ctrl+C o blocco del sito: ci si ferma, il rilancio riprende da qui
                break
    for k in chiavi[len(righe):]:
        righe.append((TESTATE[k].nome, "non avviata (rilanciare lo stesso comando per riprendere)", None))
    arts = sorted(articoli, key=lambda a: (a.data or "9999", a.testata, a.titolo))
    scrivi_corpus(arts, p.formati, destinazione, f"Rassegna stampa {descrittore_rassegna(p, chiavi)}")
    destinazione.scrivi("scheda_rassegna.txt", _scheda(p, chiavi, righe, arts, inizio,
                                                      time.monotonic() - t0, rete, not interrotta))
    if stato_file:
        stato_file.write_text(json.dumps({"firma": firma, "completata": not interrotta, "inizio": inizio}),
                              encoding="utf-8")
    log(f"\nRassegna stampa: {len(arts)} articoli da {sum(1 for _, s, e in righe if e)} testate"
        + ("" if not interrotta else " (incompleta: rilanciare lo stesso comando per riprendere)"))
    return destinazione.chiudi()


def _scheda(p, chiavi, righe, arts, inizio, durata, rete, completata):
    per_testata = {}
    for a in arts:
        per_testata[a.testata] = per_testata.get(a.testata, 0) + 1
    R = ["SCHEDA DELLA RASSEGNA STAMPA", "=" * 60,
         f"Strumento: Scraper didattico testate, versione {VERSIONE}",
         f"Avvio: {inizio}    Fine: {datetime.now().isoformat(timespec='seconds')}"
         f"    Durata di questa sessione: {durata / 60:.1f} minuti",
         f"Stato: {'completata' if completata else 'INCOMPLETA (rilanciare per completare)'}", "",
         "PARAMETRI",
         f"  Testate richieste: {len(chiavi)} ({', '.join(TESTATE[k].nome for k in chiavi)})",
         f"  Intervallo: {p.dal or '-'} / {p.al or '-'}",
         f"  Parole chiave: {', '.join(p.parole) or 'nessuna'}"
         + (f" ({'tutte' if p.tutte else 'almeno una'}, cercate nel "
            f"{'solo titolo e sommario' if p.cerca_in == 'titolo' else 'titolo, sommario e testo'})" if p.parole else ""),
         f"  Fonte degli indirizzi: {p.fonte}" + ("" if p.usa_ricerca else " (senza la ricerca dei siti)"),
         f"  Limite articoli per testata: {p.max_articoli or 'nessuno'}",
         f"  Formati: {', '.join(p.formati or FORMATI)}", "",
         "ESITO PER TESTATA",
         f"  {'Testata':24} {'Articoli':>8} {'Esaminati':>10}  Stato"]
    for nome, stato, e in righe:
        R.append(f"  {nome:24} {per_testata.get(nome, 0):>8} {(e or {}).get('esaminati', 0):>10}  {stato}")
    R += [f"  {'TOTALE':24} {len(arts):>8}", "",
          "SORGENTI CONSULTATE"]
    for nome, _, e in righe:
        for s in (e or {}).get("sorgenti", []):
            R.append(f"  {s}")
    avvisi = [a for _, _, e in righe for a in (e or {}).get("avvisi", [])]
    if avvisi:
        R += ["", "AVVISI SULLA COPERTURA"] + [f"  {a}" for a in avvisi]
    R += ["", f"Richieste di rete in questa sessione: {rete.richieste}",
          f"Indirizzi esclusi dal robots.txt (non scaricati): {len(rete.esclusi)}", "",
          "COME LEGGERE IL CORPUS",
          "  Il corpus unico riunisce gli articoli di tutte le testate in ordine di data. La testata è",
          "  indicata nell'indice Excel (colonna Testata), nel JSONL (campo testata) e nel file T-LAB",
          "  (variabile *TESTATA). La scheda di ciascuna testata, con i dettagli su sorgenti, scarti ed",
          "  errori, è in testate/<testata>/scheda_estrazione.txt.",
          "  Le testate hanno metodi e coperture diversi (ricerca del sito, sitemap, archivi per giorno):",
          "  nel confrontarle conviene tenerne conto, perché a parità di periodo la completezza può variare.",
          "",
          "NOTE METODOLOGICHE",
          "  Lo strumento rispetta il robots.txt di ogni testata (RFC 9309) e l'eventuale Crawl-delay,",
          "  si presenta con un User-Agent che dichiara la finalità di ricerca e non aggira paywall",
          "  né protezioni anti-bot.",
          "  I testi sono raccolti per finalità di studio e ricerca e non vanno ridistribuiti."]
    return "\n".join(R) + "\n"
