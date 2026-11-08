"""Collaudo delle testate: una breve estrazione reale per testata e la prova della paginazione.
Produce un unico file di riepilogo da cui correggere i moduli."""
import io
import json
import statistics
import zipfile
from datetime import date, timedelta

from .config import radice_locale
from .destinazioni import ZipMemoria
from .esecuzione import esegui
from .modello import Parametri
from .rete import Rete
from .testate import TESTATE

SCHEMI = ["{base}page/{n}/", "{base}{n}/", "{base}?page={n}", "{base}?p={n}", "{base}pagina/{n}/",
          "{base}?pagina={n}", "{base}?refresh_ce&page={n}"]


def prova_paginazione(t, base, rete):
    righe = []
    r1 = rete.get(base, cache=True)
    if r1 is None or r1.status_code != 200:
        return [f"    {base}: pagina 1 non raggiungibile ({getattr(r1, 'status_code', 'nessuna risposta')})"]
    l1 = set(t.link_articoli(r1.text, base))
    righe.append(f"    {base}: {len(l1)} articoli riconosciuti in prima pagina")
    b = base if base.endswith("/") else base + "/"
    for schema in SCHEMI:
        u = schema.format(base=base if schema.startswith("{base}?") else b, n=2)
        r = rete.get(u)
        if r is None or r.status_code != 200:
            righe.append(f"      {schema:24} stato {getattr(r, 'status_code', '-')}")
            continue
        l2 = set(t.link_articoli(r.text, u))
        nuovi = len(l2 - l1)
        righe.append(f"      {schema:24} stato 200  articoli {len(l2)}  nuovi {nuovi}"
                     + ("   <-- FUNZIONA" if nuovi >= max(3, len(l2) // 2) else ""))
    return righe


def collauda(chiavi, giorni=2, massimo=5, log=print):
    rete = Rete(log=lambda m: None)
    al = date.today()
    dal = al - timedelta(days=giorni)
    R = [f"COLLAUDO TESTATE  {al.isoformat()}  (intervallo {dal} / {al}, al massimo {massimo} articoli)", "=" * 78]
    for k in chiavi:
        t = TESTATE[k]
        log(f">>> {t.nome}")
        R += ["", f"## {t.nome} ({k})"]
        try:
            z = esegui(Parametri("data", testata=k, dal=dal.isoformat(), al=al.isoformat(),
                                 max_articoli=massimo, formati=["jsonl"]),
                       ZipMemoria(), None, rete=rete, log=lambda m: None, salva_grezzi=False)
            zf = zipfile.ZipFile(io.BytesIO(z))
            scheda = zf.read("scheda_estrazione.txt").decode()
            arts = [json.loads(r) for r in zf.read("corpus.jsonl").decode().splitlines()] \
                if "corpus.jsonl" in zf.namelist() else []
            esiti = scheda.split("ESITI")[1].split("MODALITÀ")[0].strip().splitlines()
            R += ["  " + e.strip() for e in esiti if e.strip()]
            if "AVVISI" in scheda:
                R.append("  avvisi: " + scheda.split("AVVISI SULLA COPERTURA")[1].split("\n\n")[0].strip())
            if "ERRORI" in scheda:
                R.append("  errori: " + " | ".join(scheda.split("ERRORI")[1].strip().splitlines()[:3]))
            if arts:
                R.append(f"  coerenza media {statistics.mean(a['coerenza'] for a in arts):.2f}  "
                         f"parole medie {statistics.mean(len(a['testo'].split()) for a in arts):.0f}")
            for a in arts[:3]:
                R += [f"  - {a['data'][:16]}  {a['titolo'][:90]}",
                      f"    sezione {a['sezione']!r}  autori {a['autori'][:2]}  tag {a['tag'][:4]}",
                      f"    metodo {a['metodo']}  parole {len(a['testo'].split())}  coerenza {a['coerenza']}  "
                      f"riservato {a['accesso_libero'] is False}  parziale {a['parziale']}",
                      f"    sommario: {a['sommario'][:150]!r}",
                      f"    inizio: {a['testo'][:200]!r}",
                      f"    fine:   {a['testo'][-150:]!r}",
                      f"    {a['url']}"]
        except Exception as e:
            R.append(f"  ERRORE nell'estrazione: {e!r}")
        R.append("  paginazione delle pagine elenco:")
        for base in t.elenchi_prova:
            try:
                R += prova_paginazione(t, base, rete)
            except Exception as e:
                R.append(f"    {base}: errore {e!r}")
    out = radice_locale() / "_ricognizione" / al.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    f = out / "collaudo.txt"
    f.write_text("\n".join(R) + "\n", encoding="utf-8")
    log(f"\nFatto. Riepilogo in {f}")
    return f
