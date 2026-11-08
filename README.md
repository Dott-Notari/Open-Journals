# Scraper didattico delle testate giornalistiche: piattaforma web

Piattaforma del corso di Sociologia della comunicazione interculturale per costruire corpora giornalistici e video destinati all'analisi in un contesto di studio e ricerca. Gli studenti approvati dal docente scelgono una testata o YouTube, avviano un'estrazione e scaricano il risultato con la stessa struttura prodotta dallo scraper locale. I testi raccolti non vengono ripubblicati né ridistribuiti e gli archivi restano disponibili solo per pochi giorni.

## Struttura

```
scraper-testate-piattaforma/
├── scraper_testate/            motore Python 1.12, identico alla versione locale
├── piattaforma/                collegamento tra motore, Supabase e GitHub Actions
│   ├── esegui_estrazione.py         esegue un'estrazione registrata (testate o YouTube)
│   ├── testate_piattaforma.py       motore con ZipMemoria, indice per l'ANSA, nota di piattaforma
│   ├── youtube_piattaforma.py       metadati, testo, mp4 e mp3; limiti di tempo e di durata
│   ├── coda.py                      assegna le estrazioni in coda e avvia i workflow
│   ├── indice_ansa.py               indice quotidiano delle uscite ANSA (senza testi)
│   ├── pulizia.py                   cancellazione dei file scaduti
│   ├── collaudo_online.py           collaudo delle fonti dai server di Actions
│   ├── servizi.py, stato.py, nota.py
├── .github/workflows/
│   ├── estrazione.yml               una estrazione, avviata solo dalla coda
│   ├── coda.yml                     controllo ogni 15 minuti
│   ├── indice-ansa.yml              ogni giorno
│   ├── pulizia.yml                  ogni giorno
│   └── collaudo.yml                 a mano e ogni lunedì
├── web/                        interfaccia Next.js 16, cartella radice del progetto Vercel
│   ├── app/                         pagine: fonti, scraper per fonte, estrazioni, area docente, accesso
│   ├── components/                  vetro, griglia delle fonti, moduli, animazioni GSAP
│   ├── lib/                         client Supabase, elenco delle fonti
│   ├── public/loghi/                loghi delle testate, di YouTube e dell'Università (WebP)
│   └── proxy.js                     sessione, accesso obbligatorio, Content-Security-Policy con nonce
└── supabase/
    ├── migrations/0001_schema.sql   tabelle, coda, validazione, regole di sicurezza, storage
    ├── migrations/0002_senza_limiti.sql  nessun tetto per gli studenti, video fino a 35 minuti, file fino a 5 GB
    └── docente_iniziale.sql         assegnazione del ruolo di docente dopo la prima registrazione
```

La cartella scraper_testate non viene modificata dalla piattaforma: per aggiornare il motore si sostituisce l'intera cartella con la nuova versione. Tutto ciò che serve alla messa in linea sta in piattaforma, che importa il motore e chiama motore.esecuzione.esegui() con ZipMemoria per le testate e motore.youtube.esegui_youtube() in una cartella temporanea per YouTube.

## Come funziona

Lo studente compila il modulo di una sezione e la richiesta viene scritta nella tabella estrazioni. Il database controlla da sé chi la invia, i parametri, i domini dei link e le quote, indipendentemente dall'interfaccia. La funzione assegna_estrazioni sceglie al più un'estrazione per fonte libera, così le estrazioni sulla stessa testata non girano mai in parallelo, e il workflow di estrazione la esegue su GitHub Actions, carica i file nel bucket privato «estrazioni» e aggiorna stato, avanzamento e scheda. A fine lavoro il workflow assegna la richiesta successiva della stessa fonte; un controllo programmato recupera quelle rimaste ferme.

## Sicurezza

Le regole di sicurezza a livello di riga sono attive su tutte le tabelle e l'utente anonimo non ha accesso a nulla. Lo studente vede solo il proprio profilo, le proprie estrazioni e i propri file, può inserire soltanto fonte, modalità e parametri di una nuova estrazione e modificare soltanto il proprio nome. Approvazione degli account, ruoli, fonti e impostazioni sono riservati al docente. La chiave di servizio di Supabase e il token di GitHub stanno solo nei segreti di GitHub Actions e nelle variabili lato server di Vercel. Il repository è pubblico: per questo i log di Actions riportano solo fasi e conteggi, mentre il dettaglio delle estrazioni resta su Supabase.

## Segreti di GitHub Actions

SUPABASE_URL (indirizzo del progetto, https://…supabase.co) e SUPABASE_SERVICE_ROLE_KEY (chiave segreta o service_role). Il token per avviare i workflow successivi è quello automatico del job, con il solo permesso actions: write. Le action esterne sono fissate a un commit preciso.

## Workflow programmati

Nei repository pubblici GitHub sospende i workflow programmati dopo 60 giorni senza attività nel repository (per esempio durante la pausa estiva): GitHub avvisa per email e basta riattivarli dalla scheda Actions. Senza il workflow quotidiano l'indice ANSA ha un buco nei giorni di sospensione.

## Variabili d'ambiente su Vercel

NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (visibili al browser, protette dalle regole RLS); SUPABASE_SERVICE_ROLE_KEY, GITHUB_TOKEN (token a grana fine con il solo permesso Actions in lettura e scrittura su questo repository) e GITHUB_REPOSITORY (nella forma utente/scraper-testate-piattaforma), solo lato server.

## Limiti

Gli studenti non hanno tetti su articoli, video, periodi, link o numero di estrazioni. Restano solo vincoli tecnici: un'estrazione si ferma dopo 330 minuti (GitHub interrompe ogni job a 6 ore) e consegna ciò che ha raccolto; i video oltre 35 minuti sono esclusi; le estrazioni sulla stessa testata procedono una alla volta, in coda.
