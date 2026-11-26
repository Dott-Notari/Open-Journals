// Istruzioni per testata, campo per campo. Riscritte a partire da regole_testate.json (motore 1.16):
// quando il motore cambia, si aggiorna il JSON e si rileggono queste righe.
export const GUIDA = {
  ilgiornale: {
    periodo: "Le sitemap coprono solo gli ultimi giorni. Per i mesi e gli anni precedenti la piattaforma passa dalle pagine dei tag delle tue parole chiave e dalle macrosezioni, che online arrivano a circa 10.000 articoli ciascuna.",
    parole: "Il sito non ha una ricerca pubblica utilizzabile. Le parole filtrano gli articoli e aprono anche la pagina del tag con lo stesso nome: immigrazione porta a /tag/immigrazione/.",
    elenco: "Funzionano tag (/tag/immigrazione/), sezioni (/politica/, /cronache/) e autori (/autore/nome-cognome/), con tutte le pagine successive.",
    passato: "Wayback è possibile ma lento, perché la data non compare negli indirizzi.",
    consiglio: "Per periodi lontani conviene partire da un tag tematico con la pagina elenco.",
  },
  avvenire: {
    periodo: "Archivio dal 2000. Per gli anni più vecchi online c'è solo una parte degli articoli.",
    parole: "Con le parole chiave si usa la ricerca del sito, che filtra già per data: è la strada più rapida.",
    elenco: "Le pagine dei tag, come /tag/migranti_4439, sono corpora tematici già pronti. Vanno bene anche sezioni e autori, con tutte le pagine.",
    passato: "Wayback è lento e qui serve di rado.",
    consiglio: "Per un tema usa la pagina del tag; per parole chiave, la ricerca del sito con le date.",
  },
  fatto: {
    periodo: "Archivio completo dal 2009, giorno per giorno.",
    parole: "La ricerca del sito parte dagli articoli più recenti e risale di circa due anni. Per periodi più vecchi togli la spunta «Usa la ricerca del sito»: si scorre l'archivio giorno per giorno.",
    elenco: "Sezioni, rubriche e tag con tutte le pagine, per esempio /cronaca/ o /cervelli-fuga/.",
    passato: "Qui Wayback funziona bene, perché la data è nell'indirizzo.",
    consiglio: "Per un periodo recente con parole chiave usa la ricerca; per un corpus completo di un periodo, l'archivio.",
  },
  ansa: {
    periodo: "Il sito mostra solo le uscite degli ultimi due giorni circa. La piattaforma salva ogni notte l'elenco delle uscite, quindi per periodo arriva fino al giorno in cui è stata attivata; prima di quella data serve Wayback.",
    parole: "La ricerca del sito è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Delle sezioni si legge solo la prima pagina, perché non si sfogliano.",
    passato: "Per i periodi passati usa Wayback: con l'ANSA funziona meglio che altrove, ma richiede circa un minuto per ogni giorno.",
    consiglio: "Molti lanci di agenzia sono brevi: tienilo presente quando confronti la lunghezza dei testi.",
  },
  ilpost: {
    periodo: "Archivio completo dal 2009, escluse le brevi.",
    parole: "La ricerca del sito copre tutto l'archivio. Cerca parole intere: migrant* diventa migrante, migranti e simili.",
    elenco: "Sezioni e tag con tutte le pagine, per esempio /italia/ o /tag/migranti/.",
    passato: "Wayback qui serve raramente.",
    consiglio: "Per un tema la ricerca per parole; per un corpus completo di un mese, l'archivio.",
  },
  libero: {
    periodo: "Il sito è cambiato l'11 novembre 2026. Per i periodi recenti c'è l'archivio per giorno; per i mesi precedenti si usano gli elenchi di sezione, che risalgono da qualche mese a qualche anno a seconda della sezione. Più indietro serve Wayback.",
    parole: "La ricerca del sito è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Le pagine di sezione e di tag mostrano pochi articoli e non si sfogliano: si legge solo la prima.",
    passato: "Per gli anni passati usa Wayback: i vecchi indirizzi portano ai nuovi articoli.",
    consiglio: "Il cambio di sito è recente: se un risultato non torna, segnalalo al docente.",
  },
  manifesto: {
    periodo: "Si cerca per data nelle sitemap del sito, controllando la data di ogni articolo.",
    parole: "Le parole filtrano gli articoli raccolti; la ricerca interna del sito non viene usata.",
    elenco: "Sezioni (/sezioni/politica), argomenti e autori: si legge solo la prima pagina.",
    passato: "Wayback è possibile ma lento.",
    consiglio: "Molti articoli sono per abbonati e arrivano con il solo inizio: per analisi su titoli e sommari il corpus è comunque completo.",
  },
  mattino: {
    periodo: "Per data si trovano solo le uscite del giorno. Per il passato usa una pagina elenco o Wayback.",
    parole: "La ricerca del sito è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Sezioni e sottosezioni con tutte le pagine, per esempio /napoli/cronaca/, e tag come /t/nome-tag.",
    passato: "Wayback è possibile ma lento.",
    consiglio: "Per un periodo passato parti dalla sezione che ti interessa con la pagina elenco e indica le date.",
  },
  corriere: {
    periodo: "Archivio per giorno dal 27 maggio 2020.",
    parole: "La ricerca del sito comprende le edizioni locali e risale anche a prima del 2020. Cerca parole intere: migrant* diventa migrante, migranti e simili.",
    elenco: "Delle sezioni, per esempio /cronache/, si legge solo la prima pagina.",
    passato: "Prima del 2020 conviene la ricerca per parole chiave; Wayback è possibile ma lento.",
    consiglio: "Per periodi anteriori al 2020 usa le parole chiave con la ricerca del sito.",
  },
  repubblica: {
    periodo: "Archivio mensile dal 2010; del mese in corso ci sono solo gli ultimi giorni.",
    parole: "La ricerca del sito è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Sezioni con tutte le pagine, per esempio /cronaca/, e pagine degli autori.",
    passato: "Wayback è possibile, e qui la data è nell'indirizzo.",
    consiglio: "Gran parte degli articoli è per abbonati e arriva con circa 400 caratteri: per titoli e sommari il corpus è completo, per il testo pieno serve un accesso concordato con l'editore.",
  },
  lastampa: {
    periodo: "Archivio mensile dall'agosto 2022; del mese in corso ci sono solo gli ultimi giorni.",
    parole: "La ricerca del sito non è utilizzabile: le parole filtrano gli articoli raccolti.",
    elenco: "Sezioni con tutte le pagine, per esempio /cronaca/; delle pagine argomento si legge solo la prima.",
    passato: "Prima di agosto 2022 serve Wayback.",
    consiglio: "Come per Repubblica, gli articoli per abbonati arrivano con il solo inizio.",
  },
  messaggero: {
    periodo: "Per data si trovano solo le uscite del giorno. Per il passato usa una pagina elenco o Wayback.",
    parole: "La ricerca del sito è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Sezioni con tutte le pagine, per esempio /roma/, tag come /t/nome-tag e autori.",
    passato: "Wayback è possibile ma lento.",
    consiglio: "Per un periodo passato parti da una sezione con la pagina elenco.",
  },
  verita: {
    periodo: "Archivio completo da dicembre 2018.",
    parole: "La ricerca del sito filtra anche per data: è la testata più semplice da interrogare.",
    elenco: "Sezioni con tutte le pagine, per esempio /mondo, e pagine degli autori.",
    passato: "Wayback qui non serve quasi mai.",
    consiglio: "Con parole chiave lascia attiva la ricerca del sito: è rapida e precisa.",
  },
  sole24ore: {
    periodo: "Si cerca per data nelle sitemap delle sezioni, che risalgono più o meno indietro a seconda della sezione.",
    parole: "La ricerca del sito restituisce al massimo circa 12.500 notizie per parola. Cerca parole intere: migrant* diventa migrante, migranti e simili.",
    elenco: "Delle sezioni, per esempio /sez/italia, si legge solo la prima pagina.",
    passato: "Wayback è possibile ma lento.",
    consiglio: "Con parole chiave usa la ricerca; gli articoli 24+ non hanno testo pubblico.",
  },
  independent: {
    periodo: "Per data si risale di circa 90 giorni. Prima serve Wayback.",
    parole: "Il sito non ha una ricerca utilizzabile: le parole, in inglese, filtrano gli articoli raccolti.",
    elenco: "Sezioni, argomenti e autori, per esempio /news/uk/politics: si legge solo la prima pagina.",
    passato: "Oltre i 90 giorni usa Wayback.",
    consiglio: "Entro i 90 giorni cerca solo in titolo e sommario: è molto più veloce.",
  },
  mirror: {
    periodo: "Archivio dal 1998, controllato per data di modifica.",
    parole: "Le parole, in inglese, filtrano gli articoli raccolti; la ricerca del sito è esclusa dal robots.txt.",
    elenco: "Delle sezioni, per esempio /news/politics/, si legge solo la prima pagina.",
    passato: "Wayback è possibile ma lento.",
    consiglio: "Il sito chiede 10 secondi tra una richiesta e l'altra: scegli periodi brevi e cerca solo in titolo e sommario.",
  },
  elmundo: {
    periodo: "Emeroteca per giorno; prima del 2015 la copertura non è stata verificata.",
    parole: "Le parole, in spagnolo, filtrano gli articoli raccolti; la ricerca del sito è esclusa dal robots.txt.",
    elenco: "Delle sezioni, per esempio /espana.html, si legge solo la prima pagina.",
    passato: "Wayback è possibile, e qui la data è nell'indirizzo.",
    consiglio: "Archivio per giorno con le parole come filtro, eventualmente solo in titolo e sommario.",
  },
};

// Testate su WordPress che espongono l'API con filtro per date e ricerca: stesse regole, cambiano data d'inizio e lingua.
const wp = (dal, lingua, extra = {}) => ({
  periodo: `Archivio completo${dal ? ` ${dal}` : ''}, letto dall'API di WordPress del sito con il filtro per date.`,
  parole: `Con le parole chiave${lingua ? `, ${lingua},` : ''} si usa la ricerca del sito, che filtra già per data. Se nel periodo non trova nulla, la piattaforma passa da sola all'archivio.`,
  elenco: 'Categorie e tag con tutte le pagine successive, per esempio /category/politica/.',
  passato: "Wayback non serve: l'archivio arriva già agli anni passati.",
  consiglio: 'Per un tema, parole chiave con la ricerca del sito; per tutto quello che è uscito in un periodo, togli la spunta della ricerca.',
  ...extra,
});
// Testate che si leggono dalle sitemap filtrate per data di modifica: un articolo ritoccato di recente può comparire fuori periodo.
const mappa = (periodo, lingua, extra = {}) => ({
  periodo,
  parole: `Il sito non ha una ricerca interrogabile: le parole${lingua ? `, ${lingua},` : ''} filtrano gli articoli raccolti.`,
  elenco: "Delle categorie si legge solo la prima pagina.",
  passato: "Wayback è possibile, ma lento.",
  consiglio: 'Periodi brevi, con le parole cercate solo in titolo e sommario per scaricare meno.',
  ...extra,
});

Object.assign(GUIDA, {
  // Napoli, testate sportive
  tuttonapoli: {
    periodo: "Archivio completo dal 2010. Gli articoli hanno un numero progressivo: prima di cominciare la piattaforma cerca il primo e l'ultimo del periodo, e ci vuole circa un minuto.",
    parole: "La ricerca del sito c'è, ma il robots.txt chiude le pagine dopo la prima: le parole filtrano gli articoli raccolti.",
    elenco: "Delle sezioni, come /notizie/ o /calciomercato-napoli/, si legge solo la prima pagina.",
    passato: "Wayback non serve: l'archivio arriva già agli anni passati.",
    consiglio: "Per periodi lunghi cerca le parole solo in titolo e sommario: si scarica molto meno.",
  },
  calcionapoli24: mappa("Archivio completo dal marzo 2011, dalle sitemap numerate in ordine cronologico.", '', {
    parole: "La pagina di ricerca è esclusa dal robots.txt: le parole filtrano gli articoli raccolti.",
    elenco: "Delle sezioni, come /calcio_mercato/ o /le_interviste/, si legge solo la prima pagina.",
    passato: "Wayback non serve: l'archivio arriva già agli anni passati.",
    consiglio: "Archivio per data, con le parole come filtro.",
  }),
  areanapoli: mappa("Le sitemap raccolgono 25.000 articoli ciascuna, circa un anno, dal più recente. Si leggono solo quelle che coprono il periodo scelto.", '', {
    elenco: "Delle sezioni, come /calciomercato/ o /interviste/, si legge solo la prima pagina.",
    passato: "Wayback non serve: le sitemap arrivano già agli anni passati.",
    consiglio: "Archivio per data, con le parole come filtro.",
  }),
  calcionapoli1926: wp("dall'ottobre 2016", '', {
    elenco: 'Categorie con tutte le pagine successive, per esempio /category/news/.',
  }),
  spazionapoli: mappa("Sitemap annuali dal 2020. Gli articoli dal 2011 al 2019 sono esclusi dal robots.txt e non si possono raccogliere.", '', {
    parole: "Il robots.txt esclude la ricerca e ogni indirizzo con «&», quindi anche l'API con i filtri: le parole filtrano gli articoli raccolti.",
    elenco: "Degli archivi per giorno (/2024/03/15/) e delle categorie si legge solo la prima pagina.",
    passato: "Per il 2011-2019 nemmeno Wayback aiuta: il robots.txt esclude comunque quegli articoli.",
    consiglio: "Archivio per data dal 2020, con le parole come filtro.",
  }),
  ilnapolista: wp('dal marzo 2010', '', {
    periodo: "Archivio completo dal marzo 2010, letto dall'API di WordPress. Si interroga tutto il sito: Napoli, ma anche altro calcio, altri sport e cultura.",
    elenco: 'Categorie con tutte le pagine successive. Per il solo Napoli: /category/napoli/.',
    consiglio: "Per avere solo il Napoli usa la pagina elenco /category/napoli/; per un tema, le parole chiave sul sito intero.",
  }),
  // Venezuela
  elnacional: mappa("Circa 316 sitemap in ordine cronologico, filtrate per data di modifica. L'API di WordPress è esclusa dal robots.txt.", 'in spagnolo'),
  ultimasnoticias: wp('', 'in spagnolo', { periodo: "Archivio letto dall'API di WordPress con il filtro per date, circa 200.000 articoli." }),
  eldiario: mappa("Sitemap dal 2019, con la data nell'indirizzo. L'API di WordPress risponde ma ignora il filtro per date, quindi non si usa.", 'in spagnolo', {
    passato: "Prima del 2019 serve Wayback, che è lento.",
  }),
  '2001online': mappa("Solo la sitemap delle notizie, cioè gli ultimi giorni.", 'in spagnolo', {
    parole: "La ricerca /buscar/ è esclusa dal robots.txt: le parole, in spagnolo, filtrano gli articoli raccolti.",
    elenco: "Delle sezioni si legge solo la prima pagina.",
    passato: "Per il passato usa Wayback: qui funziona bene, perché la data è nell'indirizzo degli articoli.",
    consiglio: "Va bene per seguire i giorni correnti; per periodi passati scegli Wayback.",
  }),
  correodelorinoco: mappa("Sitemap in ordine cronologico, 2000 articoli per file. Le pagine non dichiarano la data, quindi vale quella della sitemap: il giorno, senza l'ora. Con link e pagina elenco la data resta vuota.", 'in spagnolo'),
  diariovea: wp('dal settembre 2020', 'in spagnolo'),
  elpitazo: mappa("Sitemap filtrate per data di modifica, affidabili dal dicembre 2025. Gli articoli più vecchi risultano modificati in blocco (gennaio 2019 e fine 2025), quindi per quei periodi la ricerca per data resta incompleta.", 'in spagnolo', {
    passato: "Per i periodi prima del dicembre 2025 conviene Wayback, anche se è lento.",
  }),
  runrunes: wp('dal 2006', 'in spagnolo'),
  cronicauno: wp('dal 2015', 'in spagnolo'),
  elestimulo: wp("dall'aprile 2014", 'in spagnolo'),
  caraotadigital: mappa("Sitemap in ordine cronologico, filtrate per data di modifica. L'API di WordPress e lo scorrimento delle pagine sono esclusi dal robots.txt.", 'in spagnolo'),
  informe21: mappa("Sitemap del blog (il sito è su Wix), filtrate per data di modifica.", 'in spagnolo'),
  avn: mappa("Sitemap dall'aprile 2024, filtrate per data di modifica. L'API di WordPress è esclusa dal robots.txt.", 'in spagnolo', {
    passato: "Prima dell'aprile 2024 serve Wayback, che è lento.",
  }),
  telesur: mappa("Sitemap dal luglio 2024 al 19 novembre 2025, filtrate per data di modifica. Dopo quella data le sitemap non sono più aggiornate.", 'in inglese', {
    passato: "Per i periodi dopo il 19 novembre 2025 usa Wayback.",
  }),
  venezuelanalysis: wp("dall'agosto 2003", 'in inglese'),
  caracaschronicles: wp('dal settembre 2002', 'in inglese'),
  elcarabobeno: wp('dal giugno 2014', 'in spagnolo'),
  primicia: mappa("Circa 176 sitemap in ordine cronologico dal 2019, filtrate per data di modifica. L'API di WordPress richiede l'accesso.", 'in spagnolo', {
    passato: "Prima del 2019 serve Wayback, che è lento.",
  }),
});

// Per le testate senza una voce scritta a mano (videogiochi, francesi, spagnole del motore 1.16) la guida si
// ricava dal JSON delle regole: copertura, ricerca, pagine elenco, Wayback e consigli della testata.
const LINGUE = { it: '', en: 'in inglese', es: 'in spagnolo', fr: 'in francese', ca: 'in catalano' };
const ripulisci = (t) => {
  if (!t) return '';
  const x = t.replace(/--fonte wayback/g, 'Wayback').replace(/--cerca-in titolo/g, 'la ricerca solo in titolo e sommario')
    .replace(/--fonte (\w+)/g, '$1').replace(/\s+/g, ' ').trim();
  return x.charAt(0).toUpperCase() + x.slice(1) + (/[.!?]$/.test(x) ? '' : '.');
};
export function guidaDaRegole(t) {
  const m = t.modalita, lingua = LINGUE[t.lingua] ? `, ${LINGUE[t.lingua]},` : '';
  const r = m.parole_con_ricerca_del_sito;
  return {
    periodo: ripulisci(m.data.copertura),
    parole: r.disponibile
      ? `Con le parole chiave${lingua} si usa la ricerca del sito, che filtra già per data. Se nel periodo non trova nulla, la piattaforma passa da sola all'archivio.`
      : `Il sito non ha una ricerca interrogabile: le parole${lingua} filtrano gli articoli raccolti. Cercarle solo in titolo e sommario fa scaricare molto meno.`,
    elenco: m.elenco.solo_prima_pagina || /solo la prima pagina/.test(m.elenco.pagine || '') ? 'Delle sezioni si legge solo la prima pagina.' : ripulisci(m.elenco.pagine),
    passato: /solo le uscite recenti|solo le notizie recenti|ultimi giorni/.test(m.data.copertura)
      ? "Per i periodi passati usa Wayback: prende gli indirizzi dall'Internet Archive e scarica gli articoli dal sito. È lento."
      : 'Wayback è possibile, ma lento: serve solo dove l\'archivio non arriva.',
    consiglio: ripulisci(t.consigli),
  };
}

export const FONTI_INDIRIZZI = {
  auto: ['Automatica', 'Con parole chiave usa la ricerca del sito quando la testata la offre, altrimenti l\'archivio.'],
  archivio: ['Archivio', 'Sitemap, archivi ed elenchi della testata.'],
  ricerca: ['Ricerca del sito', 'Solo il motore di ricerca della testata. Servono parole chiave.'],
  wayback: ['Wayback', 'Prende gli indirizzi dall\'Internet Archive e scarica gli articoli dal sito della testata. Raggiunge periodi che l\'archivio non copre, ma è lento.'],
  gdelt: ['GDELT', 'Indice internazionale delle notizie, interrogato con parole in inglese. Sperimentale: copertura parziale e risposte non sempre disponibili.'],
};
