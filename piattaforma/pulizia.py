"""Cancella dallo storage i file delle estrazioni concluse da più giorni di quelli impostati.
Il registro delle estrazioni resta; si annota solo la data di cancellazione dei file.

Uso: python -m piattaforma.pulizia
"""
import sys
from datetime import datetime, timedelta, timezone

from .servizi import Supabase
from .stato import pubblico


def main():
    sb = Supabase()
    giorni = int(sb.impostazioni()["giorni_conservazione"])
    soglia = (datetime.now(timezone.utc) - timedelta(days=giorni)).isoformat()
    righe = sb.seleziona("estrazione_file", select="id,percorso,estrazione_id,estrazioni!inner(conclusa_il)",
                         **{"estrazioni.conclusa_il": f"lt.{soglia}"}, limit="5000")
    if not righe:
        pubblico("[pulizia] nessun file da cancellare")
        return 0
    sb.elimina_file([r["percorso"] for r in righe])
    estrazioni = sorted({r["estrazione_id"] for r in righe})
    for i in range(0, len(righe), 100):
        blocco = ",".join(r["id"] for r in righe[i:i + 100])
        sb.elimina("estrazione_file", id=f"in.({blocco})")
    for i in range(0, len(estrazioni), 100):
        blocco = ",".join(estrazioni[i:i + 100])
        sb.aggiorna("estrazioni", {"file_cancellati_il": datetime.now(timezone.utc).isoformat()},
                    id=f"in.({blocco})")
    pubblico(f"[pulizia] file cancellati: {len(righe)} di {len(estrazioni)} estrazioni")
    return 0


if __name__ == "__main__":
    sys.exit(main())
