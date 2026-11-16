"""Stato di un'estrazione in corso: raccoglie il log del motore, aggiorna l'avanzamento su
Supabase a intervalli regolari e gestisce il limite di tempo.

Nei log di GitHub Actions (pubblici, perché il repository è pubblico) finiscono solo fasi e
conteggi: titoli, indirizzi e parole chiave restano nella riga dell'estrazione su Supabase.
"""
import os
import re
import signal
import threading
import time
from datetime import datetime, timezone
from collections import deque
from contextlib import contextmanager

RE_RACCOLTO = re.compile(r"^\s*\[(\d+)\]\s")
RE_LENTO = re.compile(r"il sito risponde (429|503|5\d\d)|chiede \d+ s tra una richiesta")
RE_RETE = re.compile(r"^\s*rete: ")
FINESTRA = 300     # secondi di log considerati per il segnale
FERMO_DOPO = 600   # secondi senza nuovi indirizzi esaminati prima di segnalare un blocco
LOG_MAX = 200_000   # caratteri conservati nella colonna log


def pubblico(messaggio):
    print(messaggio, flush=True)


class Stato:
    def __init__(self, sb, id_estrazione, intervallo=15):
        self.sb, self.id = sb, id_estrazione
        self.righe = deque(maxlen=6000)
        self.articoli = 0
        self.esaminati = 0
        self.fase_corrente = "avvio"
        self.ultima = ""
        self.fermata_per_tempo = False
        self.bloccato = False
        self.interrotta = False
        self.fermata_richiesta = False
        self.eventi = deque(maxlen=200)           # (istante, tipo) dei problemi recenti
        self.ultimo_avanzamento = time.monotonic()
        self._ferma = threading.Event()
        self._intervallo = intervallo
        self._battito = threading.Thread(target=self._ciclo, daemon=True)
        self._battito.start()

    # --------------------------------------------------------------- richiamate dal motore
    def log(self, messaggio):
        testo = str(messaggio)
        for riga in testo.splitlines() or [""]:
            self.righe.append(riga)
            m = RE_RACCOLTO.match(riga)
            if m:
                self.articoli = max(self.articoli, int(m.group(1)))
            if riga.strip():
                self.ultima = riga.strip()[:300]
        if "Fermata per il limite di tempo" in testo:
            self.fermata_per_tempo = True
        if "Il sito ha bloccato le richieste" in testo:
            self.bloccato = True
        for riga in testo.splitlines():
            if RE_LENTO.search(riga):
                self.eventi.append((time.monotonic(), "lento"))
            elif RE_RETE.match(riga):
                self.eventi.append((time.monotonic(), "rete"))
        if testo.lstrip().startswith("Interrotta."):
            self.interrotta = True

    def progresso(self, raccolti, esaminati):
        if esaminati != self.esaminati:
            self.ultimo_avanzamento = time.monotonic()
        self.articoli, self.esaminati = raccolti, esaminati

    def segnale(self):
        """Salute del motore negli ultimi minuti: ok, lento, rete, fermo, bloccato."""
        adesso = time.monotonic()
        recenti = [t for i, t in self.eventi if adesso - i < FINESTRA]
        if self.bloccato:
            return "bloccato", "Il sito ha bloccato le richieste."
        if adesso - self.ultimo_avanzamento > FERMO_DOPO and self.fase_corrente.startswith("estrazione"):
            return "fermo", f"Nessun nuovo articolo da {int((adesso - self.ultimo_avanzamento) // 60)} minuti."
        if recenti.count("rete") >= 3:
            return "rete", "Connessione instabile con il sito: il motore riprova da solo."
        if recenti.count("lento") >= 2:
            return "lento", "Il sito chiede di rallentare: il motore attende e prosegue."
        return "ok", None

    def fase(self, testo):
        self.fase_corrente = testo
        pubblico(f"[fase] {testo}")

    # --------------------------------------------------------------- battito
    def _ciclo(self):
        while not self._ferma.wait(self._intervallo):
            self.invia()

    def invia(self):
        try:
            segnale, testo = self.segnale()
            self.sb.aggiorna("estrazioni", {
                "articoli": self.articoli, "esaminati": self.esaminati,
                "avanzamento": f"{self.fase_corrente}: {self.ultima}"[:500],
                "battito": datetime.now(timezone.utc).isoformat(), "segnale": segnale, "segnale_testo": testo},
                id=f"eq.{self.id}")
            riga = self.sb.seleziona("estrazioni", select="richiesta", id=f"eq.{self.id}")
            if riga and riga[0]["richiesta"] == "ferma" and not self.fermata_richiesta:
                # lo studente ha chiesto di fermare: stessa via dell'interruzione manuale
                self.fermata_richiesta = True
                os.kill(os.getpid(), signal.SIGALRM)
        except Exception:
            pass   # un aggiornamento mancato non deve fermare l'estrazione

    def chiudi(self):
        self._ferma.set()
        self._battito.join(timeout=5)

    def testo_log(self):
        return "\n".join(self.righe)[-LOG_MAX:]


@contextmanager
def allarme(secondi, stato):
    """Allo scadere simula un'interruzione manuale (KeyboardInterrupt), che il motore gestisce
    chiudendo la scheda e scrivendo ciò che ha raccolto. Scatta una sola volta."""
    def gestore(_segnale, _quadro):
        signal.alarm(0)
        if not stato.fermata_richiesta:
            stato.fermata_per_tempo = True
        raise KeyboardInterrupt
    precedente = signal.signal(signal.SIGALRM, gestore)
    signal.alarm(max(1, int(secondi)))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, precedente)
