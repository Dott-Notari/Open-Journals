"""Schede delle testate: modalità di estrazione possibili, coperture, limiti, risorse non usate.

Fonti: ricognizione dell'8 novembre 2026 (motore originale), mappatura con reverse-api-engineer e
verifica dei robots.txt del 12 novembre 2026 (cartelle Siti_API/<testata>/), esiti di «prova».
python scraper.py schede  scrive una scheda Word e Markdown per testata, più un riepilogo Excel."""
import json
from pathlib import Path

from .config import cartella_desktop

# modalità comuni a tutte le testate (si ripetono nelle schede solo se c'è qualcosa di specifico)
MODALITA = {
    "archivio": "data <testata> --dal --al: tutti gli articoli del periodo dall'archivio della testata",
    "ricerca": "data <testata> --parole: motore di ricerca della testata, poi verifica sul testo",
    "filtro": "data <testata> --parole --fonte archivio: tutto l'archivio del periodo, filtrato sulle parole",
    "titolo": "--cerca-in titolo: filtro rapido sull'indirizzo, senza scaricare gli articoli scartati",
    "elenco": "elenco <url>: pagine di sezione, tag, autore o rubrica, con salto alla data",
    "link": "link <url…>: articoli singoli o da elenco incollato",
    "wayback": "data <testata> --fonte wayback: indirizzi dall'Internet Archive per periodi fuori archivio",
    "gdelt": "data <testata> --fonte gdelt --parole-gdelt: indice GDELT, parole in inglese",
}

S = {}

S["fatto"] = dict(
    nome="Il Fatto Quotidiano", sito="https://www.ilfattoquotidiano.it", piattaforma="WordPress dietro Cloudflare",
    archivio=("sì, completo", "archivi per giorno /AAAA/MM/GG/page/N/ dal 2009; la data è nell'indirizzo, "
                              "quindi gli articoli fuori periodo non vengono scaricati"),
    ricerca=("sì, fino a fine 2024 circa", "feed RSS della ricerca di WordPress (/?s=…&feed=rss2&paged=N), consentito "
                   "dal robots.txt per questo strumento; trova la parola anche come parte di parola; il feed si ferma "
                   "dopo 150-200 pagine (circa due anni): per periodi precedenti lo strumento passa da solo "
                   "all'archivio per giorno"),
    elenchi="sezioni, rubriche e tag paginati con /page/N/ (es. /cronaca/, /cervelli-fuga/)",
    rss="/feed/ (ultimi 25), /category/<sezione>/feed/, /tag/<tag>/feed/, commenti /comments/feed/",
    testo="integrale per gli articoli liberi; i contenuti per sostenitori possono risultare parziali",
    robots="consente archivi, ricerca e articoli a questo User-Agent; blocca diversi bot di intelligenza artificiale",
    wayback="efficiente: un prefisso per giorno (/AAAA/MM/GG/)", gdelt="copertura parziale",
    altre=["API proprie /wp-json/mia/v1/: edizioni cartacee del giorno (copertina, PDF per abbonati), menu, "
           "editoriale del giorno: non usate perché non sono articoli web",
           "/wp-json/wp/v2/posts risponde 401 (chiusa): per questo si usano archivi e feed",
           "oEmbed /wp-json/oembed/1.0/embed?url=…: metadati di un articolo (autore, titolo)"],
    consigli="Per periodi lunghi con parole chiave la ricerca è la via più rapida; per un corpus completo "
             "di un periodo, l'archivio per giorno.",
)
S["avvenire"] = dict(
    nome="Avvenire", sito="https://www.avvenire.it", piattaforma="Nuxt con API propria (Naxos CMS)",
    archivio=("sì, dal 2000", "sitemap mensili delle storie; la data esatta si legge in ogni articolo "
                              "(un mese intero richiede circa 40 minuti)"),
    ricerca=("sì", "API /api/naxos/search con parola (qs) e filtro per date (dateFrom/dateTo); trova anche "
                   "parti di parola; molto più veloce delle sitemap"),
    elenchi="tag (/tag/migranti_4439), sezioni, redazione/autori; paginazione /N",
    rss="nessun feed RSS pubblico", testo="integrale per gli articoli liberi; segnalati quelli riservati",
    robots="consente sitemap, API e articoli; esclude le pagine di ricerca HTML (/ricerca), non l'API",
    wayback="possibile ma lento (data non nell'indirizzo)", gdelt="copertura parziale (pochi articoli)",
    altre=["API per tag (/api/naxos/tag/stories/<id>) e per giornalista (/api/naxos/journalist/<id>): "
           "equivalenti alle pagine tag e autore già usabili con «elenco»",
           "API della storia (/api/naxos/story/<id>) con testo strutturato: non serve, la pagina HTML basta",
           "santo del giorno (/api/saints), configurazione della home: non pertinenti"],
    consigli="Le pagine tag sono corpora tematici già pronti; per parole chiave la ricerca con filtro date.",
)
S["ilgiornale"] = dict(
    nome="il Giornale", sito="https://www.ilgiornale.it", piattaforma="Arc XP (Fusion)",
    archivio=("parziale", "sitemap giornaliere recenti; per i periodi precedenti si scorrono tag e macrosezioni "
                          "con ricerca binaria della pagina, ogni elenco è consultabile per circa 10.000 articoli"),
    ricerca=("no", "nessun motore pubblico (il sito usa un widget esterno, /cerca.html è escluso dal robots.txt); "
                   "le parole chiave attivano anche le pagine /tag/<parola>/"),
    elenchi="tag (/tag/immigrazione/), sezioni (/politica/, /cronache/…), autori (/autore/<slug>/); paginazione /N/",
    rss="/arc/outboundfeeds/rss/ (ultimi 100), /rss/category/<sezione>/, /rss/tag/<tag>/, /rss/autore/<slug>/",
    testo="integrale nel JSON della pagina (Fusion.globalContent)",
    robots="consente sitemap, elenchi e articoli; esclude /cerca.html, /agenzie/, /news/adnkronos/",
    wayback="possibile ma lento (data non nell'indirizzo)", gdelt="copertura parziale",
    altre=["API Arc /pf/api/v3/content/fetch/ei-feed-paginated-api con filtri per sezione, tag e autore "
           "(fino a 9.900 risultati, senza testo): utile per elenchi, ma equivale alle pagine tag già usate",
           "sitemap giornaliere /arc/outboundfeeds/sitemap2/AAAA-MM-GG/ (circa 150 articoli al giorno): "
           "da valutare per estendere l'archivio per data",
           "sitemap delle dirette (/diretta/…): i liveblog sono esclusi dal motore"],
    consigli="Per periodi lontani partire da un tag tematico con «elenco».",
)
S["ansa"] = dict(
    nome="ANSA", sito="https://www.ansa.it", piattaforma="CMS proprio, pagine statiche",
    archivio=("solo recente", "sitemap di sezione con le uscite degli ultimi due giorni circa; nessun archivio per data"),
    ricerca=("no", "la ricerca /ricerca/ansait/ è esclusa dal robots.txt"),
    elenchi="pagine di sezione non paginate", rss="per sezione e per regione (elenco in /sito/static/ansa_rss.html)",
    testo="integrale (contenitore .news-txt); molti lanci sono brevi",
    robots="consente sitemap e articoli; vieta i bot di intelligenza artificiale (ClaudeBot, GPTBot…) ma non questo User-Agent",
    wayback="consigliata per i periodi passati: data nell'indirizzo, un prefisso per sezione e giorno",
    gdelt="copertura buona sulle notizie di agenzia",
    altre=["67 sitemap tematiche e regionali: già usate dal motore",
           "lanci in inglese e in altre lingue (english, nuovaeuropa): esclusi dal motore"],
    consigli="Per il passato usare --fonte wayback (lento: circa un minuto per giorno di indice) o GDELT; "
             "per l'attualità l'archivio recente, eventualmente ogni giorno.",
)
S["ilpost"] = dict(
    nome="Il Post", sito="https://www.ilpost.it", piattaforma="Next.js su WordPress",
    archivio=("sì, dal 2009", "sitemap mensili degli articoli; le brevi «flashes» sono escluse"),
    ricerca=("sì", "API api.ilpost.org (ordinata per data, solo articoli); cerca parole intere, quindi migrant* "
                   "viene cercato come migrante, migranti…"),
    elenchi="sezioni e tag paginati /page/N/", rss="/<sezione>/feed/ (10 articoli); nessun feed generale",
    testo="integrale, salvo gli articoli riservati agli abbonati", robots="consente; esclude /cerca/ (pagina HTML) ma non l'API",
    wayback="possibile (data nell'indirizzo)", gdelt="copertura parziale",
    altre=["filtri della ricerca per categoria (category:politica) e periodo: utilizzabili in futuro per "
           "ricerche per sezione", "sitemap delle «flashes» (brevi): escluse per scelta"],
    consigli="Ricerca per parole chiave; archivio mensile per corpus completi.",
)
S["libero"] = dict(
    nome="Libero Quotidiano", sito="https://www.liberoquotidiano.it", piattaforma="Arc XP (dal novembre 2026, come il Giornale)",
    archivio=("sì, con limiti", "sitemap giornaliere dalla migrazione (11 novembre 2026); per i periodi precedenti "
                                "l'elenco API del sito (circa tre mesi e mezzo) e poi sezione per sezione (alcuni mesi "
                                "o anni, 9.900 articoli per sezione); le vecchie sitemap mensili dal 2006 non esistono più"),
    ricerca=("no", "/search/?keyword= è escluso dal robots.txt"),
    elenchi="le pagine HTML di sezione e tag mostrano solo pochi articoli e non si sfogliano; per le sezioni lo "
            "strumento usa l'elenco API",
    rss="non verificati sul nuovo sito",
    testo="integrale", robots="consente sitemap, API ed articoli; esclude le notizie di agenzia (adnkronos, italpress) e la ricerca",
    wayback="consigliata per i periodi più vecchi degli elenchi API (gli indirizzi vecchi reindirizzano ai nuovi)",
    gdelt="copertura parziale",
    altre=["API Arc ei-feed-paginated-api con filtri per sezione, tag e autore: usata per l'archivio per data",
           "sitemap per sezione (/arc/outboundfeeds/sitemap/category/<sezione>/, ultimi 100 articoli)",
           "Attenzione: libero.it (mappato con reverse-api-engineer) è il portale Italiaonline, non il quotidiano"],
    consigli="Per periodi recenti l'archivio per data; per anni passati Wayback. La migrazione è di questi giorni: "
             "struttura da ricontrollare fra qualche settimana.",
)
S["manifesto"] = dict(
    nome="il manifesto", sito="https://ilmanifesto.it", piattaforma="Next.js su Directus",
    archivio=("sì", "sitemap degli articoli filtrate per data di modifica e verificate articolo per articolo"),
    ricerca=("no (non usata)", "il backend Directus ha una ricerca a testo pieno con filtri per data, sezione, "
                               "autore e argomento, ma richiede la chiave che il sito invia ai visitatori anonimi: "
                               "non usata per scelta"),
    elenchi="sezioni (/sezioni/politica), argomenti, autori: solo la prima pagina, nessuna paginazione funziona", rss="nessuno",
    testo="spesso parziale: molti articoli sono riservati agli abbonati; tolto il riassunto generato da IA",
    robots="consente; dichiara ai-train=no (nessun uso per addestrare IA)",
    wayback="possibile ma lento", gdelt="copertura parziale",
    altre=["API Directus pulse.ilmanifesto.it: metadati (titolo, sommario, argomenti, autori) di tutto "
           "l'archivio dal 2002, senza testo integrale; utile per contare e selezionare articoli, da usare "
           "solo con il consenso della testata"],
    consigli="Corpus con testo pieno solo sugli articoli liberi; per analisi su titoli e sommari i metadati bastano.",
)
S["mattino"] = dict(
    nome="Il Mattino", sito="https://www.ilmattino.it", piattaforma="CMS Caltagirone, HTML",
    archivio=("solo recente", "sitemap news con le ultime cento uscite circa"),
    ricerca=("no", "la ricerca /ricerca/ è esclusa dal robots.txt"),
    elenchi="sezioni e sottosezioni con ?p=N (es. /napoli/cronaca/), tag /t/<slug>", rss="non trovati",
    testo="integrale per gli articoli liberi (JSON-LD)", robots="consente sitemap ed elenchi; esclude ricerca e sez=JSON",
    wayback="possibile ma lento (data non nell'indirizzo)", gdelt="copertura parziale",
    altre=["chiamate interne sez=JSON (notifiche, utente): escluse dal robots.txt e non pertinenti"],
    consigli="Per periodi passati partire da una sezione con «elenco»; Wayback come alternativa.",
)
S["messaggero"] = dict(
    nome="Il Messaggero", sito="https://www.ilmessaggero.it", piattaforma="CMS Caltagirone, HTML",
    archivio=("solo recente", "sitemap news con le uscite degli ultimi giorni"),
    ricerca=("no", "la ricerca /ricerca/ è esclusa dal robots.txt"),
    elenchi="sezioni con ?p=N (es. /roma/), tag /t/<slug>, autori /autore/<slug>",
    rss="/rss/<sezione>.xml (circa 20 articoli, codifica ISO-8859-1)", testo="integrale per gli articoli liberi",
    robots="consente sitemap, elenchi, feed; esclude ricerca, sez=JSON e sez=AJAX",
    wayback="possibile ma lento", gdelt="copertura parziale",
    altre=["archivio storico archivio.ilmessaggero.it: per abbonati, non esplorato",
           "video su JW Player: fuori dal perimetro"],
    consigli="Come Il Mattino: elenchi di sezione per il passato.",
)
S["corriere"] = dict(
    nome="Corriere della Sera", sito="https://www.corriere.it", piattaforma="CMS RCS, HTML con API di ricerca",
    archivio=("sì, dal maggio 2020", "sitemap giornaliere; per gli ultimi giorni le sitemap di sezione"),
    ricerca=("sì", "API searchapiservice.corriere.it (dal più recente, edizioni locali comprese); cerca parole intere"),
    elenchi="sezioni (/cronache/…): solo la prima pagina, nessuna forma di paginazione funziona (collaudo del 12 novembre)",
    rss="/rss/<sezione>.xml (indice in /rss/)",
    testo="integrale per gli articoli liberi; per i riservati spesso solo l'avvio",
    robots="consente; vieta i bot di intelligenza artificiale ma non questo User-Agent",
    wayback="possibile (data nell'indirizzo in forma 26_novembre_12)", gdelt="copertura buona",
    altre=["classifica dei più letti (toprated.rcs.it, per giorno): utile per studi sulla salienza, non integrata",
           "filtro per sezione della ricerca (section=Politica…): utilizzabile in futuro",
           "blocchi della home (appservice.corriere.it): non pertinenti"],
    consigli="Ricerca per parole chiave (anche anni prima del 2020, dove le sitemap non arrivano).",
)
S["repubblica"] = dict(
    nome="la Repubblica", sito="https://www.repubblica.it", piattaforma="GEDI (Kataweb)",
    archivio=("sì", "sitemap mensili (anche di anni fa); quella del mese in corso elenca solo gli ultimi giorni, "
                    "lo strumento lo segnala"),
    ricerca=("no", "ricerca.repubblica.it (con filtro date) e l'archivio giornaliero sono esclusi dal robots.txt"),
    elenchi="sezioni con ?page=N (es. /cronaca/), autori /autori/<slug>", rss="/rss/<sezione>/rss2.0.xml",
    testo="quasi sempre parziale: gli articoli riservati espongono circa 400 caratteri", robots="consente sitemap ed elenchi",
    wayback="possibile (data nell'indirizzo)", gdelt="copertura buona",
    altre=["sitemap tematiche (Italian Tech, Il Gusto, Salute, Green&Blue, video): non integrate"],
    consigli="Per il testo pieno serve un accesso concordato con l'editore; per titoli e sommari il corpus è completo.",
)
S["lastampa"] = dict(
    nome="La Stampa", sito="https://www.lastampa.it", piattaforma="GEDI (Kataweb)",
    archivio=("sì", "sitemap mensili compresse (circa 50 mesi); il mese in corso come Repubblica"),
    ricerca=("no", "la ricerca del sito restituisce l'archivio di Repubblica, non usabile"),
    elenchi="sezioni con ?page=N, argomenti /argomenti/<slug>/ (solo prima pagina), autori",
    rss="/<sezione>/rss (circa 100 articoli)", testo="parziale per gli articoli riservati (content_plan=locked)",
    robots="consente; vieta i bot di intelligenza artificiale", wayback="possibile (data nell'indirizzo)",
    gdelt="copertura parziale",
    altre=["sitemap video e La Zampa: non integrate"],
    consigli="Come Repubblica.",
)
S["verita"] = dict(
    nome="La Verità", sito="https://www.laverita.info", piattaforma="WordPress (Yoast)",
    archivio=("sì, dal dicembre 2018", "API REST di WordPress con filtro per date, archivio completo dal dicembre 2018; "
                                       "le vecchie sitemap non sono ordinate per data e non si usano; prima del 2019 Wayback"),
    ricerca=("sì", "API REST di WordPress (/wp-json/wp/v2/posts) con parola e filtro date after/before; "
                   "trova anche parti di parola"),
    elenchi="sezioni /<sezione>/page/N/, autori /u/<slug>", rss="/feed (10, paginabile ?paged=N)",
    testo="integrale, salvo gli articoli con paywall (campo laverita_paywall)", robots="consente quasi tutto",
    wayback="possibile ma lento", gdelt="copertura parziale",
    altre=["la stessa API permette elenchi per categoria (143 sezioni), tag e autore con date: utilizzabili "
           "in futuro per selezioni per sezione senza parole chiave",
           "sitemap news delle ultime 48 ore"],
    consigli="La testata più completa da interrogare: ricerca e date funzionano dal lato del sito.",
)
S["sole24ore"] = dict(
    nome="Il Sole 24 Ore", sito="https://www.ilsole24ore.com", piattaforma="Next.js con GraphQL",
    archivio=("parziale", "sitemap news per sezione, profondità diversa per sezione"),
    ricerca=("sì", "argomenti.ilsole24ore.com (GraphQL), solo notizie, dal più recente, al massimo circa "
                   "12.500 risultati per parola; parole intere"),
    elenchi="sezioni /sez/<sezione>: solo la prima pagina; gli archivi /archivi/<sezione>/<N> sono paginati "
            "ma non ancora usati dallo strumento", rss="/rss/<sezione>.xml",
    testo="integrale per gli articoli liberi; i 24+ non espongono testo", robots="consente; vieta alcuni bot di IA",
    wayback="possibile ma lento", gdelt="copertura buona",
    altre=["archivi paginati /archivi/<sezione>/<N> (circa 10 articoli per pagina, dal più recente): "
           "alternativa per periodi recenti",
           "quotazioni e meteo: non pertinenti"],
    consigli="Ricerca per parole chiave; per periodi senza parole, elenchi o archivi di sezione.",
)
S["independent"] = dict(
    nome="The Independent", sito="https://www.independent.co.uk", piattaforma="React SSR",
    archivio=("solo 90 giorni", "sitemap giornaliere sitemap-articles-AAAA-MM-GG (circa 500 articoli al giorno)"),
    ricerca=("no", "nessun motore pubblico; /search/ è escluso dal robots.txt"),
    elenchi="sezioni, argomenti, autori: solo la prima pagina (il robots.txt esclude ?page=)",
    rss="/<sezione>/rss (es. /news/world/europe/rss), /rss per tutto", testo="integrale, salvo alcuni contenuti per iscritti",
    robots="consente sitemap e articoli; esclude ?page=, /search/, /api/", wayback="consigliata oltre i 90 giorni",
    gdelt="copertura buona",
    altre=["sitemap di sezioni, argomenti e autori (elenchi di indirizzi): non integrate"],
    consigli="Entro 90 giorni archivio con --cerca-in titolo; prima, Wayback o GDELT.",
)
S["mirror"] = dict(
    nome="Daily Mirror", sito="https://www.mirror.co.uk", piattaforma="Escenic (Reach plc)",
    archivio=("sì, dal 1998", "sitemap mensili map_art_AAAA-MM-01.xml filtrate per data di ultima modifica (periodo "
                              "più sette giorni), poi verifica sull'articolo; gli articoli aggiornati molto dopo possono sfuggire"),
    ricerca=("no", "la ricerca /search/ è esclusa dal robots.txt"),
    elenchi="sezioni (solo prima pagina utile)", rss="/<sezione>/?service=rss, /rss.xml",
    testo="integrale (articleBody nel JSON-LD)", robots="consente; Crawl-delay 10 secondi, rispettato",
    wayback="possibile ma lento", gdelt="copertura buona",
    altre=["notizie dell'ultima ora (JSON di breaking news): non pertinenti"],
    consigli="Per la pausa di 10 secondi usare sempre --cerca-in titolo e periodi brevi.",
)
S["elmundo"] = dict(
    nome="El Mundo", sito="https://www.elmundo.es", piattaforma="CMS Unidad Editorial, HTML",
    archivio=("sì", "emeroteca giornaliera /elmundo/hemeroteca/AAAA/MM/GG/ (pagine index consentite)"),
    ricerca=("no", "la ricerca ariadna.elmundo.es è esclusa dal robots.txt"),
    elenchi="sezioni (/espana.html…) senza paginazione", rss="/rss/<sezione>.xml (50 articoli)",
    testo="spesso integrale anche negli articoli dichiarati premium (testo presente nella pagina pubblica)",
    robots="consente emeroteca e articoli; esclude ricerca, JSON delle dirette, forum",
    wayback="possibile (data nell'indirizzo)", gdelt="copertura buona",
    altre=["elenco delle sezioni in JSON (/ue-nydus/nydus-feeder.php): non necessario"],
    consigli="Archivio per giorno; parole chiave come filtro, eventualmente --cerca-in titolo.",
)
S["guardian"] = dict(
    nome="The Guardian (non attivata)", sito="https://www.theguardian.com", piattaforma="API ufficiale Open Platform",
    archivio=("sì, dal 1999", "API content.guardianapis.com con filtro per date; serve una chiave gratuita"),
    ricerca=("sì", "ricerca dell'API ufficiale nel testo (operatori AND, OR, NOT)"),
    elenchi="sezioni e tag (es. /world/migration) con ?page=N", rss="/<sezione>/rss",
    testo="integrale", robots="consente", wayback="non necessaria", gdelt="non necessaria",
    altre=["l'API offre anche sezioni, tag e campi strutturati (bodyText, byline, wordcount): si potrebbe "
           "evitare lo scaricamento delle pagine; per ora si usa la pagina, come per le altre testate"],
    consigli="Non attivata in questo progetto (si è scelto di non richiedere la chiave). Per attivarla: chiave "
             "gratuita su open-platform.theguardian.com/access, nel file .env come GUARDIAN_API_KEY.",
)

ESCLUSE = {
    "The Times / The Sunday Times": "robots.txt «Disallow: /» per tutti: nessun accesso automatico consentito",
    "Financial Times": "articoli dietro verifica Cloudflare; il robots.txt vieta l'uso dei contenuti per IA; "
                       "solo titoli da sitemap mensili (dal 1995) e RSS",
    "El País": "articoli, ricerca e sitemap dietro verifica DataDome; solo due feed RSS aggiornati",
    "The Economist": "verifica Cloudflare su tutto il sito",
    "The Telegraph": "blocco Akamai su browser e richieste",
    "Daily Mail": "blocco Akamai sulla home",
    "The Sun": "verifica anti-bot e robots.txt «Disallow: /»",
    "libero.it (portale)": "è il portale Italiaonline, non il quotidiano: nel motore c'è Libero Quotidiano",
}

FONTI_NUOVE = [
    ("GDELT (api.gdeltproject.org)", "indice internazionale delle notizie dal 2017, interrogabile per parola e "
     "dominio. Le parole si cercano sulla traduzione inglese, la copertura è parziale e il servizio accetta "
     "una richiesta ogni 5 secondi. Nelle prove del 12 novembre ha risposto solo alle prime richieste e poi ha "
     "rifiutato le successive (errore 429) anche a distanza di ore: da considerare sperimentale. "
     "--fonte gdelt --parole-gdelt."),
    ("Wayback Machine (indice CDX di web.archive.org)", "indirizzi delle pagine catturate dall'Internet "
     "Archive. Recupera periodi che sitemap ed elenchi non raggiungono più (ANSA, Il Mattino, Il Messaggero, "
     "Independent oltre 90 giorni). È lento e dipende da cosa è stato archiviato: --fonte wayback. Si usano "
     "solo gli indirizzi, mai le copie archiviate."),
    ("Feed RSS", "presenti su quasi tutte le testate: utili per un monitoraggio quotidiano programmato "
     "(una raccolta al giorno che accumula il corpus); non ancora un comando dello strumento."),
    ("Solo metadati", "per corpora molto grandi su titoli e sommari bastano sitemap news, ricerche e feed, "
     "senza scaricare gli articoli; non ancora un comando dello strumento."),
    ("Classifiche dei più letti (Corriere)", "per studi sulla salienza delle notizie; non integrate."),
    ("Accesso con licenza", "per il testo integrale degli articoli riservati serve un accesso concordato con "
     "l'editore (credenziali istituzionali, feed o API in licenza, o banche dati come quelle delle "
     "biblioteche universitarie); lo strumento non aggira i paywall."),
]


# ------------------------------------------------------------------ esiti delle prove
def ultimi_esiti(radice):
    """Esiti più recenti per caso, dai file esiti_*.json di «prova»."""
    esiti = {}
    for f in sorted(Path(radice, "_ricognizione").glob("*/esiti_*.json"), key=lambda p: p.stat().st_mtime):
        try:
            for e in json.loads(f.read_text(encoding="utf-8"))["esiti"]:
                esiti[e["caso"]] = e
        except (ValueError, KeyError):
            continue
    return esiti


def _esito_riga(e):
    if e.get("errore"):
        return f"{e['caso']}: non riuscita, {e['errore'][:160]}"
    r = (f"{e['caso']}: {e['raccolti']} articoli su {e.get('esaminati', '?')} indirizzi esaminati "
         f"({e['dal']} / {e['al']}"
         + (f", parole {', '.join(e['parole'])}" if e.get("parole") else "") + f"), {e['minuti']} min")
    if e.get("raccolti"):
        r += (f"; parole per articolo (mediana) {e.get('parole_mediana', 0):.0f}, coerenza {e.get('coerenza')}, "
              f"parziali {e.get('parziali', 0)}, riservati {e.get('riservati', 0)}")
    if e.get("interrotta"):
        r += "; fermata dal limite di tempo della prova"
    if e.get("avvisi"):
        r += "; avvisi: " + " ".join(e["avvisi"].split())[:200]
    return r


# ------------------------------------------------------------------ scrittura
def _righe(k, d, esiti):
    a_si, a_det = d["archivio"]
    r_si, r_det = d["ricerca"]
    R = [f"# {d['nome']}", "", f"Sito: {d['sito']}  ·  chiave nello strumento: `{k}`  ·  piattaforma: {d['piattaforma']}", "",
         "## Modalità di estrazione", "",
         "| Modalità | Disponibile | Come funziona |", "|---|---|---|",
         f"| Per data (archivio della testata) | {a_si} | {a_det} |",
         f"| Per parole con la ricerca del sito | {r_si} | {r_det} |",
         "| Per parole come filtro sull'archivio | " + ("sì" if a_si != "no" else "no") +
         " | scarica il periodo e tiene gli articoli con le parole (`--fonte archivio`); con `--cerca-in titolo` "
         "il filtro sull'indirizzo evita di scaricare gli scartati |",
         f"| Da pagine elenco (sezione, tag, autore) | sì | {d['elenchi']} |",
         "| Da link | sì | qualsiasi articolo della testata, anche da file |",
         f"| Wayback Machine (indirizzi) | sì | {d['wayback']} |",
         f"| GDELT (indirizzi) | sì | {d['gdelt']} |",
         f"| Feed RSS (non ancora un comando) | {'sì' if not d['rss'].startswith(('nessun', 'non')) else 'no'} | {d['rss']} |",
         "", "## Testo, paywall e regole del sito", "",
         f"- Testo: {d['testo']}", f"- robots.txt: {d['robots']}",
         "- Lo strumento rispetta il robots.txt, dichiara la finalità di ricerca e non aggira paywall né protezioni.",
         "", "## Risorse individuate e non usate", ""] + [f"- {x}" for x in d["altre"]] + [
         "", "## Consigli d'uso", "", d["consigli"], "", "## Comandi di esempio", "", "```",
         f"python scraper.py data {k} --dal 2026-10-01 --al 2026-10-07",
         f"python scraper.py data {k} --dal 2026-01-01 --al 2026-06-30 --parole \"migrant*,sbarc*\"",
         f"python scraper.py data {k} --dal 2024-03-01 --al 2024-03-07 --fonte wayback",
         f"python scraper.py data {k} --dal 2024-03-01 --al 2024-03-31 --fonte gdelt --parole-gdelt migrants --parole \"migrant*\"",
         f"python scraper.py elenco <pagina di sezione o tag di {d['sito']}> --dal 2026-01-01",
         "```", "", "## Esito delle prove", ""]
    casi = [e for c, e in esiti.items() if e.get("testata") == k]
    R += [f"- {_esito_riga(e)}" for e in casi] or ["- nessuna prova registrata: `python scraper.py prova " + k + "`"]
    return R


def scrivi_schede(cartella=None, radice_estrazioni=None, log=print):
    from docx import Document
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from .testate import TESTATE
    from .config import radice_locale
    cartella = Path(cartella or cartella_desktop() / "Siti_API" / "schede_testate")
    cartella.mkdir(parents=True, exist_ok=True)
    esiti = ultimi_esiti(radice_estrazioni or radice_locale())
    indice = ["# Schede delle testate", "",
              "Una scheda per testata con le modalità di estrazione possibili, le coperture, i limiti e le "
              "risorse individuate ma non usate. Generate con `python scraper.py schede`.", "",
              "| Testata | Per data | Ricerca del sito | Testo | Scheda |", "|---|---|---|---|---|"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Testate"
    ws.append(["Chiave", "Testata", "Per data", "Dettaglio archivio", "Ricerca del sito", "Dettaglio ricerca",
               "Elenchi", "RSS", "Testo", "robots.txt", "Wayback", "GDELT", "Prove riuscite", "Prove totali"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for k, d in S.items():
        if k not in TESTATE:
            continue
        righe = _righe(k, d, esiti)
        (cartella / f"{k}.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
        doc = Document()
        for riga in righe:
            if riga.startswith("# "):
                doc.add_heading(riga[2:], 0)
            elif riga.startswith("## "):
                doc.add_heading(riga[3:], 1)
            elif riga.startswith("|---"):
                continue
            elif riga.startswith("| "):
                celle = [x.strip() for x in riga.strip("|").split("|")]
                if celle[0] == "Modalità":
                    tab = doc.add_table(rows=1, cols=3)
                    tab.style = "Light Grid Accent 1"
                    for i, x in enumerate(celle):
                        tab.rows[0].cells[i].text = x
                else:
                    cs = tab.add_row().cells
                    for i, x in enumerate(celle):
                        cs[i].text = x.replace("`", "")
            elif riga.startswith("- "):
                doc.add_paragraph(riga[2:].replace("`", ""), style="List Bullet")
            elif riga and riga != "```":
                doc.add_paragraph(riga.replace("`", ""))
        doc.save(cartella / f"{k}.docx")
        casi = [e for e in esiti.values() if e.get("testata") == k]
        ws.append([k, d["nome"], d["archivio"][0], d["archivio"][1], d["ricerca"][0], d["ricerca"][1], d["elenchi"],
                   d["rss"], d["testo"], d["robots"], d["wayback"], d["gdelt"],
                   sum(1 for e in casi if e.get("raccolti")), len(casi)])
        indice.append(f"| {d['nome']} | {d['archivio'][0]} | {d['ricerca'][0]} | {d['testo'][:60]} | [{k}.md]({k}.md) |")
    indice += ["", "## Testate escluse", ""] + [f"- **{n}**: {m}" for n, m in ESCLUSE.items()]
    indice += ["", "## Modalità e fonti da valutare", ""] + [f"- **{n}**: {m}" for n, m in FONTI_NUOVE]
    (cartella / "README.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
    ws2 = wb.create_sheet("Escluse")
    ws2.append(["Testata", "Motivo"])
    for n, m in ESCLUSE.items():
        ws2.append([n, m])
    ws3 = wb.create_sheet("Prove")
    ws3.append(["Caso", "Testata", "Fonte", "Dal", "Al", "Parole", "Raccolti", "Esaminati", "Parziali",
                "Riservati", "Minuti", "Esito"])
    for e in esiti.values():
        ws3.append([e["caso"], e.get("testata"), e.get("fonte"), e.get("dal"), e.get("al"), ", ".join(e.get("parole") or []),
                    e.get("raccolti"), e.get("esaminati"), e.get("parziali"), e.get("riservati"), e.get("minuti"),
                    e.get("errore") or ("interrotta dal limite di tempo" if e.get("interrotta") else "ok")])
    for foglio in (ws, ws2, ws3):
        for col in foglio.columns:
            foglio.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col)))
    wb.save(cartella / "riepilogo_testate.xlsx")
    log(f"Schede scritte in {cartella} ({len(S)} testate)")
    return cartella
