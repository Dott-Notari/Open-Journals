"""Estrazione da una testata: il motore lavora con ZipMemoria e restituisce i byte dello zip."""
import io
import re
import shutil
import tempfile
import zipfile
from dataclasses import replace
from datetime import date
from pathlib import Path

from . import MOTORE  # noqa: F401
from motore import comune as C
from motore.destinazioni import ZipMemoria
from motore.esecuzione import cartella_per, esegui
from motore.testate import TESTATE
from motore.rassegna import chiavi_rassegna, descrittore_rassegna, esegui_rassegna
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
        fonte=p.get("fonte", "auto"), usa_ricerca=bool(p.get("usa_ricerca", True)),
        parole_gdelt=list(p.get("parole_gdelt", [])),
        max_articoli=p.get("max_articoli"))   # None: nessun limite


def prepara_ansa(par, sb, rete, stato):
    """Per l'ANSA la ricerca per data passa dall'indice della piattaforma: lo si aggiorna e se ne
    prendono gli indirizzi dell'intervallo, che il motore elabora in modalità «link»."""
    if indice_ansa.da_aggiornare(sb):
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
    rete = Rete(pausa=float(dati.get("pausa") or 2), log=stato.log)
    stato.rete = rete
    with tempfile.TemporaryDirectory() as tmp:
        radice = cartella_per(par, radice=tmp).name     # stesso nome della cartella locale
    righe_nota = []
    # ANSA per periodo: indice quotidiano della piattaforma, salvo che si scelga Wayback o GDELT
    if (par.testata == "ansa" and par.modalita == "data" and par.fonte in ("auto", "archivio")
            and impostazioni["ansa_indicizzazione_attiva"]):
        par, righe_nota = prepara_ansa(par, sb, rete, stato)
    dest = ZipConNota(radice, lambda: testo_nota(
        dati["id"], impostazioni["giorni_conservazione"],
        interrotta=stato.fermata_per_tempo or stato.fermata_richiesta or stato.bloccato or stato.interrotta, righe_extra=righe_nota))

    # stato di lavoro del motore: permette di riprendere un'estrazione interrotta
    lavoro = Path(tempfile.mkdtemp(prefix="lavoro_"))
    if dati.get("riprende_da"):
        stato.fase("recupero del punto di ripresa")
        try:
            pacchetto = sb.scarica(f"{dati['utente']}/{dati['riprende_da']}/_ripresa.zip")
            zipfile.ZipFile(io.BytesIO(pacchetto)).extractall(lavoro)
        except Exception:
            # continuazione di una rassegna: la testata riparte da capo, non c'è stato salvato
            stato.log("nessun punto di ripresa: la testata riparte dall'inizio del periodo")

    tempo = int(dati["tempo_max_minuti"]) * 60
    stato.fase("estrazione degli articoli")
    try:
        with allarme(tempo + 120, stato):   # rete di sicurezza oltre il limite interno del motore
            dati_zip = esegui(par, dest, lavoro, rete=rete, log=stato.log, progresso=stato.progresso,
                              salva_grezzi=False, tempo_max=tempo)
        ripresa = io.BytesIO()
        with zipfile.ZipFile(ripresa, "w", zipfile.ZIP_DEFLATED) as z:
            for nome in ("stato.json", "articoli.jsonl"):
                if (lavoro / nome).exists():
                    z.write(lavoro / nome, nome)
    finally:
        shutil.rmtree(lavoro, ignore_errors=True)

    scheda = leggi_scheda(dati_zip)
    interrotta = stato.fermata_per_tempo or stato.bloccato or stato.interrotta or "INTERROTTA" in scheda
    errore = None
    if stato.fermata_richiesta:
        errore = "Fermata su richiesta: l'archivio contiene ciò che è stato raccolto. Puoi riprenderla quando vuoi."
    elif stato.bloccato:
        errore = "Il sito ha attivato una protezione anti-bot: l'estrazione si è fermata. Riprova più tardi."
    elif stato.fermata_per_tempo:
        errore = f"Fermata dopo {dati['tempo_max_minuti']} minuti: l'archivio contiene ciò che è stato raccolto. Puoi riprenderla."
    esaminati = numero(scheda, "Indirizzi esaminati")
    # tempo illimitato: finito il tempo della parte, si prosegue da soli se questa parte ha lavorato
    # serve un passo avanti rispetto alla parte precedente, altrimenti si girerebbe a vuoto
    prima = 0
    if dati.get("riprende_da"):
        r = sb.seleziona("estrazioni", select="esaminati,fonte", id=f"eq.{dati['riprende_da']}")
        prima = (r[0].get("esaminati") or 0) if r and r[0].get("fonte") == dati["fonte"] else 0
    continua = (stato.fermata_per_tempo and not stato.fermata_richiesta and not stato.bloccato
                and dati.get("tempo_illimitato") and esaminati > prima)
    if continua:
        errore = (f"Parte {dati.get('parte') or 1} conclusa dopo {dati['tempo_max_minuti']} minuti: l'estrazione prosegue da sola "
                  "nella parte successiva, dal punto in cui si è fermata. L'archivio dell'ultima parte conterrà tutti gli articoli.")
    return {
        "continua": {} if continua else None,
        "stato": "interrotta" if interrotta else "completata",
        "articoli": numero(scheda, "Articoli raccolti"),
        "esaminati": esaminati,
        "scheda": scheda,
        "errore": errore,
        "file": [{"nome": f"{radice}.zip", "tipo": "zip", "dati": dati_zip, "mime": "application/zip"}]
                + ([{"nome": "_ripresa.zip", "tipo": "ripresa", "dati": ripresa.getvalue(), "mime": "application/zip"}] if interrotta else []),
    }


class TempoMax(float):
    """Limite di tempo della rassegna stampa. Il motore calcola il tempo residuo prima di ogni
    testata (tempo_max - trascorso): se lo studente ha chiesto di fermare, o il limite è già
    scattato, il residuo vale zero e le testate rimaste non partono."""

    def __new__(cls, secondi, stato):
        x = super().__new__(cls, secondi)
        x.stato = stato
        return x

    def __sub__(self, altro):
        if self.stato.fermata_richiesta or self.stato.fermata_per_tempo:
            return 0.0
        return float(self) - altro


RE_RIGA_TESTATA = re.compile(r"^  (.{24})\s+(\d+)\s+(\d+)  (.+)$", re.M)


def esegui_rassegna_piattaforma(dati, sb, stato, impostazioni):
    """Rassegna stampa: più testate, un corpus unico. Ogni testata usa il suo metodo migliore."""
    p = dati["parametri"]
    par = Parametri(
        modalita="data", dal=p["dal"], al=p["al"], parole=list(p.get("parole", [])),
        tutte=bool(p.get("tutte", False)), escludi_riservati=False, cerca_in=p.get("cerca_in", "testo"),
        formati=list(p.get("formati", [])), max_articoli=p.get("max_articoli"),
        usa_ricerca=bool(p.get("usa_ricerca", True)))
    chiavi = chiavi_rassegna(p["testate"])
    radice = f"{date.today().isoformat()}_{descrittore_rassegna(par, chiavi)}"
    righe = ["Rassegna stampa: ogni testata è stata interrogata con il proprio metodo e la propria",
             "copertura (ricerca del sito se ci sono parole chiave e la testata la consente, altrimenti",
             "archivio per data). L'esito di ciascuna testata è in scheda_rassegna.txt. Il limite di",
             "tempo vale per l'intera rassegna, il numero massimo di articoli per ciascuna testata.",
             "Nella rassegna l'ANSA copre solo gli ultimi giorni.", ""]
    dest = ZipConNota(radice, lambda: testo_nota(
        dati["id"], impostazioni["giorni_conservazione"], interrotta=False, righe_extra=righe))
    rete = Rete(pausa=float(dati.get("pausa") or 2), log=stato.log)
    stato.rete = rete
    tempo = int(dati["tempo_max_minuti"]) * 60
    stato.fase(f"rassegna stampa di {len(chiavi)} testate")
    with allarme(tempo + 120, stato):
        dati_zip = esegui_rassegna(par, chiavi, dest, None, rete=rete, log=stato.log,
                                   salva_grezzi=False, tempo_max=TempoMax(tempo, stato))

    with zipfile.ZipFile(io.BytesIO(dati_zip)) as z:
        nomi = [n for n in z.namelist() if n.endswith("scheda_rassegna.txt")]
        scheda = z.read(nomi[0]).decode("utf-8") if nomi else ""
    m = re.search(r"TOTALE\s+(\d+)", scheda)
    righe_t = RE_RIGA_TESTATA.findall(scheda.split("ESITO PER TESTATA")[-1].split("SORGENTI")[0])
    saltate = [r[0].strip() for r in righe_t if r[3].startswith("saltata")]
    interrotta = "INCOMPLETA" in scheda or not scheda
    errore = None
    if stato.fermata_richiesta:
        errore = "Fermata su richiesta: l'archivio contiene le testate già raccolte."
    elif interrotta:
        errore = (f"Rassegna incompleta: limite di {dati['tempo_max_minuti']} minuti raggiunto o sito che ha "
                  "bloccato le richieste. L'esito per testata è nella scheda.")
    # tempo illimitato: le testate interrotte o non avviate passano alla parte successiva
    continua = None
    if interrotta and stato.fermata_per_tempo and not stato.fermata_richiesta and dati.get("tempo_illimitato") \
            and len(righe_t) == len(chiavi):
        interrotte = [k for k, r in zip(chiavi, righe_t) if r[3].startswith("INTERROTTA")]
        non_avviate = [k for k, r in zip(chiavi, righe_t) if r[3].startswith("non avviata")]
        fatte = len(chiavi) - len(interrotte) - len(non_avviate)
        # se in tutta la parte non si è chiusa nessuna testata, quella interrotta è troppo lunga per una
        # rassegna: si lascia fuori (si estrae da sola), così ogni parte fa comunque un passo avanti
        lasciate = [] if fatte else interrotte
        restanti = [k for k in chiavi if (k in interrotte and fatte) or k in non_avviate]
        if restanti:
            base = {k: v for k, v in p.items() if k != "testate"}
            continua = ({"fonte": restanti[0], "parametri": {**base, "fonte": "auto"}} if len(restanti) == 1
                        else {"fonte": "rassegna", "parametri": {**base, "testate": restanti}})
            nomi = lambda ks: ", ".join(TESTATE[k].nome if k in TESTATE else k for k in ks)
            errore = (f"Parte {dati.get('parte') or 1} conclusa dopo {dati['tempo_max_minuti']} minuti. "
                      f"Proseguono da sole nella parte successiva, con un archivio a parte: {nomi(restanti)}.")
            if lasciate:
                errore += (f" {nomi(lasciate)} richiede più tempo di una parte: per averla completa "
                           "avviala da sola dalla sua pagina, dove prosegue in più parti.")
    if saltate:
        errore = ((errore or "") + f" Testate saltate: {', '.join(saltate)}.").strip()
    return {
        "continua": continua,
        "stato": "interrotta" if (interrotta or stato.fermata_richiesta) else "completata",
        "articoli": int(m.group(1)) if m else stato.articoli,
        "esaminati": sum(int(r[2]) for r in righe_t),
        "scheda": scheda,
        "errore": errore,
        "file": [{"nome": f"{radice}.zip", "tipo": "zip", "dati": dati_zip, "mime": "application/zip"}],
    }
