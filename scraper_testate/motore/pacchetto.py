"""Pacchetto per aggiornare la piattaforma online con Claude (chat): regole per testata, interfaccia del
motore, istruzioni e codice. python scraper.py pacchetto  scrive la cartella Siti_API/piattaforma.

Le regole sono ricavate dal codice (testate, motori di ricerca, paginazione, Wayback) e dalle schede,
più i dati di copertura qui sotto, verificati con le prove del 12 novembre 2026."""
import json
import re
import shutil
import zipfile
from dataclasses import fields
from datetime import date
from pathlib import Path

from .config import PAUSA_DEFAULT, PAUSA_MINIMA, UA, VERSIONE, cartella_desktop
from .modello import Parametri

# copertura verificata: (archivio per data dal, nota sulla profondità dell'archivio, profondità della ricerca)
COPERTURA = {
    "fatto": ("2009-01-01", "completo", "circa due anni (il feed si ferma dopo 150-200 pagine)"),
    "avvenire": ("2000-01-01", "completo; per gli anni meno recenti l'archivio online è una selezione", "filtro per date sul sito"),
    "ilgiornale": (None, "sitemap giornaliere solo recenti; prima, pagine tag e macrosezioni (circa 10.000 articoli ciascuna)", None),
    "ansa": (None, "solo gli ultimi due giorni circa; il passato con fonte wayback", None),
    "ilpost": ("2009-01-01", "completo (brevi «flashes» escluse)", "tutto l'archivio"),
    "libero": (None, "dalla migrazione dell'11 novembre 2026 sitemap giornaliere; prima elenchi API (circa 3,5 mesi per "
                     "tutto il sito, mesi o anni per sezione); oltre, fonte wayback", None),
    "manifesto": (None, "sitemap per data di modifica, verificate articolo per articolo", None),
    "mattino": (None, "solo le uscite del giorno (sitemap news); il passato con elenco o wayback", None),
    "messaggero": (None, "solo le uscite del giorno (sitemap news); il passato con elenco o wayback", None),
    "corriere": ("2020-05-27", "sitemap giornaliere", "tutto l'archivio della ricerca (anche prima del 2020)"),
    "repubblica": ("2010-01-01", "sitemap mensili; il mese in corso solo gli ultimi giorni", None),
    "lastampa": ("2022-08-01", "sitemap mensili (circa 50 mesi); il mese in corso solo gli ultimi giorni", None),
    "verita": ("2018-12-01", "completo tramite API WordPress", "filtro per date sul sito"),
    "sole24ore": (None, "sitemap news di sezione, profondità variabile", "al massimo circa 12.500 risultati per parola"),
    "independent": (None, "ultimi 90 giorni circa (sitemap giornaliere); prima, fonte wayback", None),
    "mirror": ("1998-01-01", "sitemap mensili filtrate per data di modifica", None),
    "elmundo": (None, "emeroteca giornaliera (profondità non verificata oltre il 2015)", None),
    "guardian": ("1999-01-01", "API ufficiale con chiave", "API ufficiale"),
    # testate napoletane (verifica del 24 novembre 2026)
    "tuttonapoli": ("2010-01-01", "completo: identificativi progressivi degli articoli, estremi del periodo "
                                  "trovati con una ricerca binaria (circa un minuto prima di iniziare)", None),
    "calcionapoli24": ("2011-03-30", "completo: sitemap numerate in ordine cronologico", None),
    "areanapoli": (None, "sitemap a blocchi di 25.000 articoli (circa un anno ciascuno), dal più recente", None),
    "calcionapoli1926": ("2016-10-15", "completo tramite API WordPress", "filtro per date sul sito"),
    "spazionapoli": ("2020-01-01", "sitemap annuali; il robots.txt esclude gli articoli 2011-2019", None),
    "ilnapolista": ("2010-03-24", "completo tramite API WordPress (tutto il sito, non solo la categoria Napoli)",
                    "filtro per date sul sito"),
}

STATO = {"guardian": "non attivata: serve la chiave GUARDIAN_API_KEY, il progetto ha scelto di non usarla"}

ESCLUSE_MOTIVI = None   # dalle schede


def regole():
    from .schede import ESCLUSE, FONTI_NUOVE, S
    from .testate import TESTATE
    from .testate.base import Testata
    from .testate.ricerca import MOTORI
    from .testate import gruppo_di
    out = []
    for k, t in TESTATE.items():
        sc = S.get(k, {})
        motore = MOTORI.get(k)
        inizio = getattr(t, "INIZIO", None)
        dal, nota_arch, prof_ric = COPERTURA.get(k) or (
            inizio.isoformat() if inizio else None, t.note_ricerca_data,
            "filtro per date sul sito" if motore else None)
        ha_ricerca = bool(motore) or k == "guardian"
        pag = t.pagina_elenco("https://esempio/elenco/", 2)
        solo_prima = pag is None
        wb_eff = type(t).wayback_prefissi is not Testata.wayback_prefissi   # interrogazioni per giorno
        crawl = {"mirror": 10}.get(k)
        fonti = ["auto", "archivio"] + (["ricerca"] if ha_ricerca else []) + ["wayback", "gdelt"]
        out.append({
            "chiave": k, "nome": t.nome, "sito": sc.get("sito", ""), "dominio": t.dominio,
            "lingua": t.lingua,
            "gruppo": gruppo_di(k),
            "stato": STATO.get(k, "attiva"), "piattaforma_sito": sc.get("piattaforma", ""),
            "modalita": {
                "data": {
                    "disponibile": True, "copertura_dal": dal, "copertura": nota_arch,
                    "come": t.note_ricerca_data,
                    "fonti_consentite": fonti, "fonte_predefinita": "auto",
                },
                "parole_con_ricerca_del_sito": {
                    "disponibile": ha_ricerca,
                    "motore": motore[1] if motore else ("API ufficiale" if k == "guardian" else None),
                    "solo_parole_intere": bool(motore and motore[2]),
                    "profondita": prof_ric,
                    "se_non_arriva_al_periodo": "passa da solo all'archivio per data" if ha_ricerca else None,
                    "motivo_se_assente": None if ha_ricerca else sc.get("ricerca", ("", ""))[1],
                },
                "parole_come_filtro": {"disponibile": True, "cerca_in": ["testo", "titolo"],
                                       "nota": "con cerca_in=titolo gli articoli senza le parole nell'indirizzo non vengono scaricati"},
                "elenco": {"disponibile": True, "solo_prima_pagina": solo_prima,
                           "paginazione": None if solo_prima else
                           re.sub(r"(?<=[/=])2(?=/|$)", "{n}", pag.replace("https://esempio/elenco", "{base}")),
                           "pagine": sc.get("elenchi", "")},
                "link": {"disponibile": True},
                "wayback": {"disponibile": True, "efficiente": bool(wb_eff), "nota": sc.get("wayback", "")},
                "gdelt": {"disponibile": True, "sperimentale": True, "parole": "in inglese (parole_gdelt)",
                          "nota": sc.get("gdelt", "")},
                "rss": {"nel_motore": False, "nota": sc.get("rss", "")},
            },
            "vincoli": {
                "robots_txt": sc.get("robots", ""), "crawl_delay_secondi": crawl,
                "pausa_minima_secondi": max(PAUSA_MINIMA, crawl or 0),
                "testo": sc.get("testo", ""),
                "paywall": "mai aggirato: gli articoli riservati hanno il testo che la testata rende pubblico",
            },
            "consigli": sc.get("consigli", ""),
            "risorse_non_usate": sc.get("altre", []),
        })
    escluse = [{"testata": n, "motivo": m} for n, m in ESCLUSE.items()]
    fonti = [{"nome": n, "descrizione": m} for n, m in FONTI_NUOVE]
    return out, escluse, fonti


def interfaccia():
    campi = []
    note = {
        "modalita": "\"data\" | \"elenco\" | \"link\"",
        "testata": "chiave della testata (solo con modalita=data; con elenco/link si riconosce dall'indirizzo)",
        "link": "lista di URL di articoli (modalita=link)",
        "elenco": "URL di una pagina di sezione, tag o autore (modalita=elenco)",
        "dal": "AAAA-MM-GG (obbligatoria con modalita=data)", "al": "AAAA-MM-GG, predefinita oggi",
        "parole": "lista; * per i suffissi (migrant*)", "tutte": "true = tutte le parole, false = almeno una",
        "escludi_riservati": "scarta gli articoli dichiarati riservati agli abbonati",
        "cerca_in": "\"testo\" | \"titolo\"", "formati": "sottoinsieme di docx, txt, html, xlsx, jsonl, tlab",
        "max_articoli": "intero o null", "usa_ricerca": "false = non usare la ricerca del sito (come fonte=archivio)",
        "fonte": "\"auto\" | \"archivio\" | \"ricerca\" | \"wayback\" | \"gdelt\" (solo modalita=data)",
        "parole_gdelt": "parole in inglese per fonte=gdelt",
    }
    for f in fields(Parametri):
        d = f.default if f.default is not f.default_factory else []
        try:
            json.dumps(d)
        except TypeError:
            d = []
        campi.append({"campo": f.name, "predefinito": d, "descrizione": note.get(f.name, "")})
    return campi


def _md_regole(testate, escluse, fonti):
    R = [f"# Regole di estrazione per testata (motore {VERSIONE}, {date.today().isoformat()})", "",
         "Generato da `python scraper.py pacchetto`. La versione leggibile da un programma è `02_regole_testate.json`.", ""]
    for t in testate:
        m = t["modalita"]
        R += [f"## {t['nome']} (`{t['chiave']}`)", "",
              f"Sito {t['sito']} · lingua {t['lingua']} · stato: {t['stato']}", "",
              f"- **Per data**: " + (f"copertura dal {m['data']['copertura_dal']}" if m['data']['copertura_dal']
                                     else "copertura non fissa") + f"; {m['data']['copertura']}. "
              f"Fonti consentite: {', '.join(m['data']['fonti_consentite'])}.",
              f"- **Parole con la ricerca del sito**: " + (
                  f"sì, {m['parole_con_ricerca_del_sito']['motore']}"
                  + (" (parole intere: migrant* viene cercato come migrant, migranta, migrante, migranti, migranto)"
                     if m['parole_con_ricerca_del_sito']['solo_parole_intere'] else "")
                  + (f"; profondità: {m['parole_con_ricerca_del_sito']['profondita']}" if m['parole_con_ricerca_del_sito']['profondita'] else "")
                  if m['parole_con_ricerca_del_sito']['disponibile'] else
                  f"no ({m['parole_con_ricerca_del_sito']['motivo_se_assente']})"),
              "- **Parole come filtro**: sì, su testo o solo titolo.",
              f"- **Elenco**: " + ("solo la prima pagina" if m['elenco']['solo_prima_pagina'] else
                                   f"paginazione `{m['elenco']['paginazione']}`") + f"; {m['elenco']['pagine']}.",
              "- **Link**: sì.",
              f"- **Wayback**: {'efficiente' if m['wayback']['efficiente'] else 'lenta'}; {m['wayback']['nota']}.",
              f"- **GDELT**: sperimentale; {m['gdelt']['nota']}.",
              f"- **RSS** (non nel motore): {m['rss']['nota']}.",
              f"- **Vincoli**: pausa minima {t['vincoli']['pausa_minima_secondi']} s"
              + (f" (Crawl-delay {t['vincoli']['crawl_delay_secondi']} s)" if t['vincoli']['crawl_delay_secondi'] else "")
              + f"; robots.txt: {t['vincoli']['robots_txt']}; testo: {t['vincoli']['testo']}.",
              f"- **Consiglio**: {t['consigli']}", ""]
    R += ["## Testate escluse", ""] + [f"- **{e['testata']}**: {e['motivo']}" for e in escluse]
    R += ["", "## Fonti e modalità da valutare", ""] + [f"- **{f['nome']}**: {f['descrizione']}" for f in fonti]
    return "\n".join(R) + "\n"


def _md_interfaccia(campi):
    R = [f"# Interfaccia del motore {VERSIONE}", "",
         "La piattaforma usa il motore così:", "", "```python",
         "from motore.esecuzione import esegui",
         "from motore.destinazioni import ZipMemoria",
         "from motore.modello import Parametri",
         "from motore.rete import Rete", "",
         "p = Parametri(modalita=\"data\", testata=\"verita\", dal=\"2026-01-01\", al=\"2026-01-31\",",
         "              parole=[\"migrant*\"], fonte=\"auto\", formati=[\"xlsx\", \"jsonl\", \"docx\"])",
         "zip_bytes = esegui(p, ZipMemoria(), None, rete=Rete(pausa=2), tempo_max=None)", "```", "",
         "`esegui` restituisce lo zip dell'estrazione (stessa struttura della cartella locale, senza `_lavoro`). "
         "Se la testata non si può interrogare in quel modo solleva `motore.testate.NonSupportato` con un messaggio "
         "da mostrare all'utente.", "",
         "## Campi di `Parametri`", "", "| Campo | Predefinito | Descrizione |", "|---|---|---|"]
    R += [f"| `{c['campo']}` | `{json.dumps(c['predefinito'], ensure_ascii=False)}` | {c['descrizione']} |" for c in campi]
    R += ["", "## Regole generali di esecuzione", "",
          f"- User-Agent fisso: `{UA}`.",
          f"- Pausa predefinita {PAUSA_DEFAULT} s, minima {PAUSA_MINIMA} s tra richieste allo stesso sito; il Crawl-delay "
          "del robots.txt, se maggiore, la sostituisce. GDELT almeno 6 s, Wayback almeno 2 s.",
          "- Ogni richiesta è confrontata con il robots.txt del sito (RFC 9309, con caratteri jolly): gli indirizzi "
          "esclusi non vengono scaricati e sono contati nella scheda di estrazione.",
          "- Nessun aggiramento di paywall o protezioni anti-bot: con una protezione attiva il motore solleva "
          "`motore.rete.Bloccato` e l'estrazione si ferma.",
          "- `tempo_max` (secondi) vale per lo scaricamento degli articoli, non per la raccolta degli indirizzi.",
          "- Con Wayback e GDELT si usano solo gli indirizzi; gli articoli si scaricano dal sito della testata.",
          "- Doppioni (stesso titolo e data) scartati; ricerche che non arrivano al periodo passano all'archivio.", "",
          "## Rassegna stampa (dalla 1.14)", "",
          "Una sola estrazione su più testate, con un corpus unico:", "", "```python",
          "from motore.rassegna import esegui_rassegna",
          "p = Parametri(modalita=\"data\", dal=\"2026-11-01\", al=\"2026-11-07\", parole=[\"de bruyne\"],",
          "              formati=[\"xlsx\", \"jsonl\", \"tlab\"])",
          "zip_bytes = esegui_rassegna(p, [\"napoli\", \"verita\"], ZipMemoria(), None, rete=Rete(pausa=2), tempo_max=None)",
          "```", "",
          "- Il secondo argomento accetta chiavi e gruppi (`italiane`, `estere`, `napoli`, `venezuela`, `videogiochi`, `francesi`, `spagnole`, `tutte`); `p.testata` è ignorato.",
          "- Ogni testata usa il suo metodo migliore (ricerca del sito se ci sono parole e la testata la consente, "
          "altrimenti archivio), con le regole di sempre.",
          "- Lo zip contiene il corpus unico (un file per articolo, `corpus_completo.docx`, `indice_articoli.xlsx`, "
          "`corpus.jsonl`, `corpus_tlab.txt` con la variabile `*TESTATA`), `scheda_rassegna.txt` con l'esito per testata "
          "e `testate/<chiave>/scheda_estrazione.txt`.",
          "- Una testata che non si può interrogare viene saltata e segnalata nella scheda della rassegna, senza fermare le altre.",
          "- `tempo_max` vale per l'insieme delle testate; `max_articoli` vale per ciascuna testata.", "",
          "## Novità della versione 1.16 rispetto alla 1.15", "",
          "- Testate francesi, gruppo `francesi` (16, `motore/testate/francia.py`): lemonde, lefigaro, 20minutesfr, "
          "franceinfo, bfmtv, lci, cnews, france24, latribune, humanite, lacroix, lobs, lexpress, mediapart, canard, courrier.",
          "- Testate spagnole, gruppo `spagnole` (17, `motore/testate/spagna.py`): abc, eldiarioes, elconfidencial, larazon, 20minutoses, elespanol, "
          "publico, libertaddigital, okdiario, efe, europapress, ara (in catalano), diariovasco, elcorreo, ideal, "
          "surinenglish (in inglese), diariosur. Alcune espongono solo le uscite recenti (copertura «solo recente»).",
          "- Nove testate di videogiochi in più nel gruppo `videogiochi` (28 in tutto): eurogameres, ignespana, "
          "gamereactores, 3djuegos, vandal, hobbyconsolas, pushsquare, purexbox, nintendolife.",
          "- Nuove lingue nell'attributo `lingua`: fr, ca.",
          "- Nuovo modulo `motore/testate/generiche.py` (sitemap per giorno, settimana o mese; sitemap a file fissi).",
          "- `comune.testo_pulito` accetta anche i valori non testuali di alcuni JSON-LD (correzione di un errore).",
          "- Nessun cambiamento nell'interfaccia del motore.", "",
          "## Novità della versione 1.15 rispetto alla 1.14", "",
          "- Testate di videogiochi e recensioni, gruppo `videogiochi` (19 testate, `motore/testate/videogiochi.py`): "
          "ign, ignitalia, eurogamer, polygon, kotaku, pcgamer, rockpapershotgun, gamesradar, gameinformer, vgc, "
          "thegamer, gamerant, multiplayer, everyeye, spaziogames, gamereactor, gamesource, gamesindustry, gamedeveloper. "
          "Lingua it o en.",
          "- Metodi: sitemap mensili o annuali filtrate per data di modifica; sitemap numerate in ordine cronologico; "
          "per VGC ricerca binaria sulla data degli articoli (2-3 minuti prima di iniziare, il robots.txt chiede 5 s "
          "tra le richieste); API di WordPress con ricerca per Gamereactor Italia.",
          "- Nuove escluse: GameSpot, Destructoid, GamesVillage (anti-bot), Eurogamer Italia (non più online), "
          "OpenCritic e Metacritic (aggregatori di voti, da valutare a parte).",
          "- Nessun cambiamento nell'interfaccia del motore: `esegui` ed `esegui_rassegna` restano identici.", "",
          "## Novità della versione 1.14 rispetto alla 1.13", "",
          "- Rassegna stampa (`motore/rassegna.py`, comando `python scraper.py rassegna`).",
          "- Testate napoletane, gruppo `napoli`: tuttonapoli, calcionapoli24, areanapoli, calcionapoli1926, "
          "spazionapoli, ilnapolista (`motore/testate/napoli.py`).",
          "- Testate venezuelane, gruppo `venezuela` (18 testate, `motore/testate/venezuela.py`): API di WordPress, "
          "sitemap in ordine cronologico filtrate per data di modifica, una sola testata con la sola sitemap news.",
          "- Attributo `lingua` di ogni testata (it, es, en), riportato nelle regole.",
          "- `esegui` accetta il parametro facoltativo `esito` (dizionario con articoli e stato), usato dalla rassegna stampa.",
          "- Gruppi di testate in `motore.testate.GRUPPI`; `gruppo_di(chiave)` dà il gruppo di una testata.", "",
          "## Novità della versione 1.13 rispetto alla 1.12", "",
          "- Nuovi campi `usa_ricerca`, `fonte`, `parole_gdelt` (i vecchi parametri restano validi).",
          "- Nuove testate: independent, mirror, elmundo, guardian (non attivata). Libero riscritto (nuova piattaforma "
          "del sito), La Verità per data via API, Mirror filtrato per data di modifica.",
          "- Nuovi moduli: `motore/robots.py`, `motore/scoperta.py`, `motore/testate/ricerca.py`, "
          "`motore/testate/estere.py`, `motore/schede.py`, `motore/pacchetto.py`.",
          "- `config.RADICE` vale ora `Siti_API/estrazioni` (solo uso locale; la piattaforma usa ZipMemoria).",
          "- Requisiti invariati (`requirements.txt`)."]
    return "\n".join(R) + "\n"


ISTRUZIONI = """# Istruzioni per Claude: aggiornamento della piattaforma di scraping didattico

## Contesto
Gestisco la piattaforma online «Open New Media», che permette a studenti e ricercatori del corso di Sociologia
della comunicazione interculturale di estrarre corpora di articoli di giornale. È fatta così: interfaccia
Next.js su Vercel (`web/`), database Supabase con migrazioni numerate (`supabase/migrations/`), estrazioni
eseguite da GitHub Actions (`piattaforma/`, `.github/workflows/`), motore Python in `scraper_testate/`.
La piattaforma online è ferma alla versione {versione_online} del motore e funziona. Le versioni intermedie non sono
mai state applicate: questo aggiornamento porta la piattaforma direttamente alla {versione} e comprende tutto.
Rispetto alla piattaforma online, il motore ha **{n_nuove} testate nuove**:
{elenco_nuove}
L'interfaccia del motore (`esegui`, `esegui_rassegna`, `Parametri`) non cambia.

## File
- `caricamento_piattaforma.zip` (lo allego io in chat, da solo o dentro `per_la_piattaforma_{versione_file}.zip`): lo stato attuale della piattaforma, con il codice
  di `web/`, `piattaforma/`, `supabase/` e i workflow. È la base su cui lavorare.
- `02_regole_testate.json`: per ogni testata le modalità consentite, le coperture, i vincoli e i testi d'aiuto.
  È la fonte di verità per le impostazioni.
- `03_regole_testate.md`: la stessa cosa in forma leggibile.
- `04_interfaccia_motore.md`: come chiamare il motore e le novità delle ultime versioni.
- `05_esiti_prove.json`: esiti delle prove reali, caso per caso.
- `06_motore_{versione_file}.zip`: il codice aggiornato del motore (cartella `motore/` e `scraper.py`).
- `07_schede_testate.md`: le schede di tutte le testate in un solo file; `07_riepilogo_testate.xlsx`.

## Cosa ti chiedo
1. **Parti da `caricamento_piattaforma.zip`.** Se ti manca, chiedimelo prima di modificare qualcosa.
2. **Aggiorna il motore**: sostituisci `scraper_testate/` con il contenuto di `06_motore_{versione_file}.zip`
   (senza toccare nient'altro della cartella) e `web/lib/regole_testate.json` con `02_regole_testate.json`.
3. **Scrivi la migrazione `{migrazione}`** sul modello della `0008`: aggiungi i gruppi nuovi
   ({gruppi_nuovi}) ai valori ammessi di `gruppo`, inserisci le {n_nuove} testate nuove in `stato_testate` (chiave, nome, domini, ordine,
   fonti consentite, gruppo) e aggiorna ciò che nel database controlla domini e fonti. Le testate nuove nascono
   non disponibili e le accende il collaudo, come per la 0008. Deve potersi rieseguire senza danni.
4. **Aggiorna l'interfaccia**: i gruppi «Videogiochi», «Francesi» e «Spagnole» nella griglia delle fonti e nella
   rassegna stampa (caselle per gruppo: {tutti_gruppi}), `web/lib/fonti.js` e i testi della guida.
   **Loghi: i {n_loghi} loghi delle testate nuove non ci sono ancora**; li caricherò io più avanti in
   `web/public/loghi/<chiave>.webp`. Prevedi quindi un ripiego che funzioni da subito (per esempio il nome della
   testata in un riquadro) quando il file manca, e fai in modo che per aggiungere un logo basti caricare il file
   con il nome giusto e, se serve, una voce in `RAPPORTI`. I loghi esistenti restano come sono.
5. **Controlla i limiti di tempo e le coperture**: VGC impiega 2-3 minuti a trovare gli estremi del periodo (il
   robots.txt chiede 5 secondi tra le richieste), Kotaku verifica tutti gli articoli del mese, CNews e Courrier
   international chiedono 10 secondi tra le richieste. Per le testate con copertura «solo recente» (ABC,
   El Confidencial, 20minutos, El Español, Libertad Digital, testate Vocento, Vandal, Hobby Consolas) vale l'avviso con
   `fonte = wayback`. Valgono le stesse durate massime
   delle altre testate; mostra all'utente il testo `consigli` della testata.
6. **Restituiscimi** l'elenco delle modifiche, i file modificati completi (o un nuovo zip con la stessa struttura
   di `caricamento_piattaforma.zip`) e una breve lista di controlli da fare dopo la pubblicazione: migrazione,
   collaudo, un'estrazione di prova per testata nuova con le date di `05_esiti_prove.json`.

## Vincoli da rispettare (non negoziabili)
- Il motore deve continuare a rispettare il robots.txt, a usare il suo User-Agent dichiarato e le pause minime.
  Non aggiungere opzioni per disattivare questi controlli.
- Nessun aggiramento di paywall, verifiche anti-bot, login altrui o copie archiviate per leggere testi riservati.
  Gli articoli riservati restano segnalati e con il testo che la testata rende pubblico.
- Le testate escluse (sezione `escluse` del JSON) non vanno aggiunte.
- Il Guardian resta non attivo finché non lo chiedo.
- I testi raccolti servono per studio e ricerca e non vanno ridistribuiti: mantieni questa nota nell'interfaccia
  e nella scheda di estrazione.

## Domande utili
Se una regola del JSON non trova posto nell'interfaccia attuale, proponi la soluzione più semplice e chiedimi
conferma prima di aggiungere nuove schermate.
"""

LEGGIMI = """# Come usare questo pacchetto con Claude (chat)

Aggiornamento della piattaforma online dalla versione {versione_online} alla {versione} del motore
({n_nuove} testate nuove). I file da caricare sono già pronti, nell'ordine giusto, in `da_caricare_in_chat/`.

## Metodo rapido (un solo file)
In una nuova chat su https://claude.ai (con l'esecuzione di codice attiva) allega `per_la_piattaforma_{versione_file}.zip`
e scrivi: «Leggi 01_ISTRUZIONI_PER_CLAUDE.md nello zip e procedi con l'aggiornamento. Lo stato attuale della
piattaforma è in caricamento_piattaforma.zip, dentro lo stesso zip.»

## Metodo con un Progetto (utile se lavorerai in più chat)
1. Apri https://claude.ai e crea un **Progetto** (per esempio «Piattaforma scraping testate {versione_file}»).
   Serve che nelle impostazioni sia attiva l'esecuzione di codice e la creazione di file, per leggere gli zip.
2. **Istruzioni del progetto**: copia e incolla il testo di `da_caricare_in_chat/1_istruzioni_del_progetto.md`.
3. **Conoscenze del progetto**: carica tutti i file della cartella `da_caricare_in_chat/2_conoscenze_del_progetto/`.
4. **Nuova chat nel progetto**: allega `da_caricare_in_chat/3_da_allegare_in_chat/caricamento_piattaforma.zip` e
   scrivi, per esempio: «Ecco lo stato attuale della piattaforma: procedi con l'aggiornamento come da istruzioni».
5. Applica le modifiche che Claude restituisce (migrazione su Supabase, file su GitHub), lancia il collaudo dalla
   scheda Actions, poi fai le estrazioni di prova che indica.
6. Dopo la pubblicazione, sostituisci `caricamento_piattaforma.zip` con il nuovo stato della piattaforma.

## Loghi
I {n_loghi} loghi mancanti si raccolgono con `Siti_API/Loghi_testate_nuove.xlsx` e si caricano dopo, in
`web/public/loghi/<chiave>.webp`: la piattaforma mostra il nome della testata finché il logo manca.

## Quando rigenerare il pacchetto
Dopo ogni aggiornamento del motore o nuova prova:
```
cd ~/Desktop/Siti_API/motore_testate
source .venv/bin/activate
python scraper.py schede
python scraper.py pacchetto
```

## Nota
Non caricare chiavi, password o file `.env`: il pacchetto non ne contiene e non ne servono.
"""


def stato_online(cartella):
    """Testate, loghi, gruppi e migrazioni della piattaforma online, letti da caricamento_piattaforma.zip."""
    z = cartella / "caricamento_piattaforma.zip"
    if not z.exists():
        return None
    with zipfile.ZipFile(z) as zz:
        nomi = zz.namelist()
        regole_f = next((n for n in nomi if n.endswith("web/lib/regole_testate.json")), None)
        online = json.loads(zz.read(regole_f)) if regole_f else {}
    loghi = {Path(n).stem for n in nomi if "/public/loghi/" in n and n.endswith(".webp")}
    migr = sorted(Path(n).name for n in nomi if "/supabase/migrations/" in n and n.endswith(".sql"))
    return {"versione": online.get("motore", "?").split()[0], "chiavi": {t["chiave"] for t in online.get("testate", [])},
            "gruppi": {t.get("gruppo") for t in online.get("testate", [])}, "loghi": loghi, "migrazioni": migr}


def scrivi_pacchetto(cartella=None, log=print):
    from .config import radice_locale
    from .schede import ultimi_esiti
    radice_motore = Path(__file__).resolve().parent.parent
    cartella = Path(cartella or cartella_desktop() / "Siti_API" / "piattaforma")
    cartella.mkdir(parents=True, exist_ok=True)
    versione_file = VERSIONE.split()[0]
    testate, escluse, fonti = regole()
    dati = {"motore": VERSIONE, "generato": date.today().isoformat(),
            "regole_generali": {"user_agent": UA, "pausa_predefinita_secondi": PAUSA_DEFAULT,
                                "pausa_minima_secondi": PAUSA_MINIMA, "rispetto_robots_txt": True,
                                "aggiramento_paywall": False,
                                "fonti": {"auto": "ricerca del sito se ci sono parole e la testata la consente, altrimenti archivio",
                                          "archivio": "sitemap, archivi ed elenchi della testata",
                                          "ricerca": "solo il motore di ricerca della testata",
                                          "wayback": "indirizzi dall'indice CDX dell'Internet Archive; articoli scaricati dal sito",
                                          "gdelt": "indirizzi dall'indice GDELT (parole in inglese); sperimentale"}},
            "testate": testate, "escluse": escluse, "fonti_da_valutare": fonti}
    sostituzioni = {"versione": VERSIONE, "versione_file": versione_file, "oggi": date.today().isoformat()}
    on = stato_online(cartella) or {"versione": "?", "chiavi": set(), "gruppi": set(), "loghi": set(), "migrazioni": []}
    nuove = [t for t in testate if t["chiave"] not in on["chiavi"] and t.get("stato") == "attiva"]
    per_gruppo = {}
    for t in nuove:
        per_gruppo.setdefault(t["gruppo"], []).append(t["chiave"])
    ordine_gruppi = list(dict.fromkeys(t["gruppo"] for t in testate))
    num = max([int(m[:4]) for m in on["migrazioni"] if m[:4].isdigit()] or [9]) + 1
    senza_logo = [t["chiave"] for t in testate if t["chiave"] not in on["loghi"] and t.get("stato") == "attiva"]
    sostituzioni.update(
        versione_online=on["versione"], n_nuove=len(nuove), n_loghi=len(senza_logo),
        elenco_nuove="\n".join(f"- gruppo `{g}` ({len(ks)}): " + ", ".join(ks) for g, ks in per_gruppo.items()),
        gruppi_nuovi=", ".join(f"`{g}`" for g in per_gruppo if g not in on["gruppi"]) or "nessuno",
        tutti_gruppi=", ".join(ordine_gruppi),
        migrazione=f"{num:04d}_motore_{versione_file.replace('.', '')}.sql")
    (cartella / "00_LEGGIMI.md").write_text(LEGGIMI.format(**sostituzioni), encoding="utf-8")
    (cartella / "01_ISTRUZIONI_PER_CLAUDE.md").write_text(ISTRUZIONI.format(**sostituzioni), encoding="utf-8")
    (cartella / "02_regole_testate.json").write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")
    (cartella / "03_regole_testate.md").write_text(_md_regole(testate, escluse, fonti), encoding="utf-8")
    (cartella / "04_interfaccia_motore.md").write_text(_md_interfaccia(interfaccia()), encoding="utf-8")
    esiti = sorted(ultimi_esiti(radice_locale()).values(), key=lambda e: (e.get("testata", ""), e["caso"]))
    for e in esiti:
        e.pop("cartella", None)   # percorsi del Mac locale: non servono alla piattaforma
        e.pop("esempi", None)     # titoli degli articoli raccolti: non servono alla configurazione
    (cartella / "05_esiti_prove.json").write_text(json.dumps(esiti, ensure_ascii=False, indent=1), encoding="utf-8")
    for vecchio in cartella.glob("06_motore_*.zip"):
        vecchio.unlink()
    with zipfile.ZipFile(cartella / f"06_motore_{versione_file}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(radice_motore.glob("motore/**/*.py")) + [radice_motore / n for n in
                                                                ("scraper.py", "requirements.txt", "README.md", ".env.esempio")]:
            if f.exists() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(radice_motore))
    schede = cartella_desktop() / "Siti_API" / "schede_testate"
    dest = cartella / "07_schede"
    shutil.rmtree(dest, ignore_errors=True)
    if schede.exists():
        shutil.copytree(schede, dest, ignore=shutil.ignore_patterns("*.docx", "~$*"))
    # tutte le schede in un solo file, più comodo da caricare
    md = sorted(dest.glob("*.md"), key=lambda f: (f.name != "README.md", f.name))
    (cartella / "07_schede_testate.md").write_text(
        "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in md), encoding="utf-8")
    # cartella con i soli file da caricare, nell'ordine dei passi del LEGGIMI
    pronti = cartella / "da_caricare_in_chat"
    shutil.rmtree(pronti, ignore_errors=True)
    (pronti / "2_conoscenze_del_progetto").mkdir(parents=True)
    (pronti / "3_da_allegare_in_chat").mkdir()
    shutil.copy(cartella / "01_ISTRUZIONI_PER_CLAUDE.md", pronti / "1_istruzioni_del_progetto.md")
    for n in ("02_regole_testate.json", "03_regole_testate.md", "04_interfaccia_motore.md", "05_esiti_prove.json",
              f"06_motore_{versione_file}.zip", "07_schede_testate.md"):
        shutil.copy(cartella / n, pronti / "2_conoscenze_del_progetto" / n)
    if (dest / "riepilogo_testate.xlsx").exists():
        shutil.copy(dest / "riepilogo_testate.xlsx", pronti / "2_conoscenze_del_progetto" / "07_riepilogo_testate.xlsx")
    if (cartella / "caricamento_piattaforma.zip").exists():
        shutil.copy(cartella / "caricamento_piattaforma.zip", pronti / "3_da_allegare_in_chat" / "caricamento_piattaforma.zip")
    # un unico zip da dare a Claude (chat): istruzioni, conoscenze e stato attuale della piattaforma
    for vecchio in cartella.glob("per_la_piattaforma_*.zip"):
        vecchio.unlink()
    unico = cartella / f"per_la_piattaforma_{versione_file}.zip"
    with zipfile.ZipFile(unico, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(cartella / "00_LEGGIMI.md", "00_LEGGIMI.md")
        z.write(cartella / "01_ISTRUZIONI_PER_CLAUDE.md", "01_ISTRUZIONI_PER_CLAUDE.md")
        for f in sorted((pronti / "2_conoscenze_del_progetto").iterdir()):
            z.write(f, f.name)
        if (cartella / "caricamento_piattaforma.zip").exists():
            z.write(cartella / "caricamento_piattaforma.zip", "caricamento_piattaforma.zip")
    log(f"Pacchetto scritto in {cartella}: {len(nuove)} testate nuove rispetto alla piattaforma online "
        f"({on['versione']}), {len(senza_logo)} loghi mancanti")
    return cartella
