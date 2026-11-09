"""Assegna le estrazioni in coda (al più una per fonte libera) e avvia i relativi workflow.
La chiamano il workflow di estrazione alla fine di ogni lavoro e il controllo programmato.

Uso: python -m piattaforma.coda
"""
import sys

from .servizi import Supabase, avvia_workflow
from .stato import pubblico


def main():
    sb = Supabase()
    avviate = 0
    for riga in sb.rpc("assegna_estrazioni") or []:
        try:
            avvia_workflow(riga["id"], riga["fonte"])
            avviate += 1
        except Exception as e:
            # la riga resta «avviata» e torna in coda da sola dopo 20 minuti
            pubblico(f"[coda] avvio non riuscito ({e.__class__.__name__}), verrà ritentato")
    pubblico(f"[coda] estrazioni avviate: {avviate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
