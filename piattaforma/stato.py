"""Stato di un'estrazione in corso: raccoglie il log del motore, aggiorna l'avanzamento su
Supabase a intervalli regolari e gestisce il limite di tempo.

Nei log di GitHub Actions (pubblici, perché il repository è pubblico) finiscono solo fasi e
conteggi: titoli, indirizzi e parole chiave restano nella riga dell'estrazione su Supabase.
"""
import re
import signal
import threading
from collections import deque
from contextlib import contextmanager

RE_RACCOLTO = re.compile(r"^\s*\[(\d+)\]\s")
LOG_MAX = 200_000   # caratteri conservati nella colonna log


def pubblico(messaggio):
    print(messaggio, flush=True)


class Stato:
    def __init__(self, sb, id_estrazione, intervallo=30):
        self.sb, self.id = sb, id_estrazione
        self.righe = deque(maxlen=6000)
        self.articoli = 0
        self.esaminati = 0
        self.fase_corrente = "avvio"
        self.ultima = ""
        self.fermata_per_tempo = False
        self.bloccato = False
        self.interrotta = False
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
        if testo.lstrip().startswith("Interrotta."):
            self.interrotta = True

    def progresso(self, raccolti, esaminati):
        self.articoli, self.esaminati = raccolti, esaminati

    def fase(self, testo):
        self.fase_corrente = testo
        pubblico(f"[fase] {testo}")

    # --------------------------------------------------------------- battito
    def _ciclo(self):
        while not self._ferma.wait(self._intervallo):
            self.invia()

    def invia(self):
        try:
            self.sb.aggiorna("estrazioni", {
                "articoli": self.articoli, "esaminati": self.esaminati,
                "avanzamento": f"{self.fase_corrente}: {self.ultima}"[:500]}, id=f"eq.{self.id}")
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
        stato.fermata_per_tempo = True
        raise KeyboardInterrupt
    precedente = signal.signal(signal.SIGALRM, gestore)
    signal.alarm(max(1, int(secondi)))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, precedente)
