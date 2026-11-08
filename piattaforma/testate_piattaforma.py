"""Estrazione da una testata: il motore lavora con ZipMemoria e restituisce i byte dello zip."""
import io
import re
import tempfile
import zipfile
from dataclasses import replace
from datetime import date
from pathlib import Path

from . import MOTORE  # noqa: F401
from motore import comune as C
from motore.destinazioni import ZipMemoria
from motore.esecuzione import cartella_per, esegui
from motore.modello import Parametri
from motore.rete import Rete

from . import indice_ansa
from .nota import testo_nota
from .stato import allarme


class ZipConNota(ZipMemoria):
    """ZipMemoria del motore con in più nota_piattaforma.txt, scritta alla chiusura."""

    def __init__(self, radice, nota):
        super().__init__(radice)
        self._nota = nota

    def chiudi(self):
        self.scrivi("nota_piattaforma.txt", self._nota())
        return super().chiudi()


def numero(scheda, etichetta):
    m = re.search(rf"{re.escape(etichetta)}:\s*(\d+)", scheda)
    return int(m.group(1)) if m else 0


def leggi_scheda(dati_zip):
    with zipfile.ZipFile(io.BytesIO(dati_zip)) as z:
        nomi = [n for n in z.namelist() if n.endswith("scheda_estrazione.txt")]
        return z.read(nomi[0]).decode("utf-8") if nomi else ""


def parametri_da_riga(dati):
    p = dati["parametri"]
    return Parametri(
        modalita=dati["modalita"], testata=dati["fonte"], link=list(p.get("link", [])),
        elenco=p.get("elenco"), dal=p.get("dal"), al=p.get("al"), parole=list(p.get("parole", [])),
        tutte=bool(p.get("tutte", False)), escludi_riservati=False,   # decisione: riservati sempre inclusi
        cerca_in=p.get("cerca_in", "testo"), formati=list(p.get("formati", [])),
        max_articoli=int(p["max_articoli"]))


def prepara_ansa(par, sb, rete, stato):
    """Per l'ANSA la ricerca per data passa dall'indice della piattaforma: lo si aggiorna e se ne
    prendono gli indirizzi dell'intervallo, che il motore elabora in modalità «link»."""
    stato.fase("aggiornamento dell'indice ANSA")
    indice_ansa.aggiorna(sb, rete, stato.log)
    dal, al = date.fromisoformat(par.dal), date.fromisoformat(par.al)
    voci = indice_ansa.indirizzi(sb, dal, al)
    inizio = indice_ansa.inizio_indice(sb)
    if par.parole and par.cerca_in == "titolo":
        # stesso filtro rapido che il motore applica agli indirizzi, qui sul titolo dell'indice
        pat = C.compila_parole([C.piega(x) for x in par.parole])
        voci = [v for v in voci
                if C.corrisponde(pat, C.piega(v.get("titolo") or C.slug_url(v["url"])), par.tutte)]
    righe = ["Gli indirizzi degli articoli ANSA sono stati presi dall'indice della piattaforma, che",
             "registra ogni giorno le sitemap dell'agenzia (solo indirizzo, titolo, data e sezione).",
             "Per questo la scheda riporta la modalità «link»; date e testi sono comunque letti da",
             f"ciascun articolo. Indirizzi dell'intervallo trovati nell'indice: {len(voci)}."]
    if inizio is None or dal < inizio:
        righe += [f"ATTENZIONE: l'indice comincia il {inizio.strftime('%d/%m/%Y') if inizio else '(vuoto)'};",
                  "i giorni precedenti dell'intervallo richiesto non sono coperti."]
    stato.log(f"Indice ANSA: {len(voci)} indirizzi nell'intervallo")
    return replace(par, modalita="link", link=[v["url"] for v in voci]), righe + [""]


def esegui_testata(dati, sb, stato, impostazioni):
    par = parametri_da_riga(dati)
    rete = Rete(log=stato.log)
    with tempfile.TemporaryDirectory() as tmp:
        radice = cartella_per(par, radice=tmp).name     # stesso nome della cartella locale
    righe_nota = []
    if par.testata == "ansa" and par.modalita == "data" and impostazioni["ansa_indicizzazione_attiva"]:
        par, righe_nota = prepara_ansa(par, sb, rete, stato)
    dest = ZipConNota(radice, lambda: testo_nota(
        dati["id"], impostazioni["giorni_conservazione"],
        interrotta=stato.fermata_per_tempo or stato.bloccato or stato.interrotta, righe_extra=righe_nota))

    tempo = int(dati["tempo_max_minuti"]) * 60
    stato.fase("estrazione degli articoli")
    with allarme(tempo + 300, stato):   # rete di sicurezza oltre il limite interno del motore
        dati_zip = esegui(par, dest, None, rete=rete, log=stato.log, progresso=stato.progresso,
                          salva_grezzi=False, tempo_max=tempo)

    scheda = leggi_scheda(dati_zip)
    interrotta = stato.fermata_per_tempo or stato.bloccato or stato.interrotta or "INTERROTTA" in scheda
    errore = None
    if stato.bloccato:
        errore = "Il sito ha attivato una protezione anti-bot: l'estrazione si è fermata. Riprova più tardi."
    elif stato.fermata_per_tempo:
        errore = f"Estrazione fermata dopo {dati['tempo_max_minuti']} minuti: i file contengono ciò che è stato raccolto."
    return {
        "stato": "interrotta" if interrotta else "completata",
        "articoli": numero(scheda, "Articoli raccolti"),
        "esaminati": numero(scheda, "Indirizzi esaminati"),
        "scheda": scheda,
        "errore": errore,
        "file": [{"nome": f"{radice}.zip", "tipo": "zip", "dati": dati_zip, "mime": "application/zip"}],
    }
