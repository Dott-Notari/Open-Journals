"""Verifiche tecniche periodiche: profondità degli archivi e funzionamento della paginazione."""
from datetime import date, timedelta

from .config import LIMITE_PAGINE
from .esecuzione import Scorrimento
from .modello import SorgenteElenco
from .testate import TESTATE


def ultima_pagina(sc):
    """Ultima pagina non vuota di un elenco (ricerca esponenziale e poi binaria)."""
    if not sc.pagina(1):
        return 0
    lo, hi = 1, 2
    while hi <= LIMITE_PAGINE and sc.pagina(hi):
        lo, hi = hi, hi * 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if sc.pagina(mid):
            lo = mid
        else:
            hi = mid
    # se l'ultima pagina è la copia di una precedente (tetto di paginazione), risale a quella vera
    while lo > 1 and sc.pagina(lo - 1) and sc.pagina(lo) is None:
        lo -= 1
    return lo


def _profondita(t, base, rete, R):
    sc = Scorrimento(t, SorgenteElenco("verifica", base), rete, log=lambda m: None)
    p1, p2 = sc.pagina(1) or [], sc.pagina(2) or []
    sc.comuni = set(p1) & set(p2)
    n = ultima_pagina(sc)
    d1, dn = sc.data_pagina(1), sc.data_pagina(n) if n else None
    R.append(f"  {base}")
    R.append(f"    pagine: {n}   articoli per pagina: {len(p1)}   link ripetuti su ogni pagina: {len(sc.comuni)}")
    R.append(f"    data in prima pagina: {d1}   data nell'ultima pagina raggiungibile: {dn}")


def verifica(chiave, rete, log=print):
    t = TESTATE[chiave]
    R = [f"VERIFICA {t.nome}  ({date.today().isoformat()})", "=" * 60]
    if chiave == "ilgiornale":
        for base in ("https://www.ilgiornale.it/politica/", "https://www.ilgiornale.it/cronache/",
                     "https://www.ilgiornale.it/tag/immigrazione/"):
            log(f"  {base}")
            _profondita(t, base, rete, R)
    elif chiave == "avvenire":
        for base in ("https://www.avvenire.it/tag/migranti_4439", "https://www.avvenire.it/attualita"):
            log(f"  {base}")
            _profondita(t, base, rete, R)
    elif chiave == "fatto":
        g = date.today() - timedelta(days=2)
        base = f"https://www.ilfattoquotidiano.it/{g:%Y/%m/%d}/"
        sc = Scorrimento(t, SorgenteElenco("verifica", base, filtro=f"/{g:%Y/%m/%d}/", usa_date=False),
                         rete, log=lambda m: None)
        visti, n = set(), 1
        R.append(f"  archivio del {g.isoformat()}")
        while n <= 60:
            links = sc.pagina(n)
            if not links:
                break
            nuovi = [l for l in links if l not in visti]
            R.append(f"    pagina {n}: {len(links)} articoli, nuovi {len(nuovi)}")
            if not nuovi:
                break
            visti.update(links)
            n += 1
        R.append(f"    totale articoli distinti del giorno: {len(visti)}")
        _profondita(t, "https://www.ilfattoquotidiano.it/cervelli-fuga/", rete, R)
    elif chiave == "ansa":
        oggi = date.today()
        note = []
        sorg = t.piano_per_data(rete, oggi - timedelta(days=365), oggi, note.append)
        R.append(f"  articoli nelle sitemap negli ultimi 12 mesi: {len(sorg[0].urls)}")
        R += [f"  {n.strip()}" for n in note]
    return "\n".join(R) + "\n"
