import REGOLE from './regole_testate.json';
import { GUIDA, guidaDaRegole } from './guida';

// larghezza / altezza dei file in public/loghi (le testate senza file mostrano il nome)
export const RAPPORTI = { ansa: 1, corriere: 12.93, fatto: 2.45, ilgiornale: 6.64, manifesto: 6, mattino: 7, messaggero: 5.64,
  ilpost: 2.82, sole24ore: 4.52, repubblica: 5.21, lastampa: 8.28, verita: 4.62, libero: 4.84, avvenire: 3.58, youtube: 4.47,
  independent: 4.29, mirror: 2.64, elmundo: 7.5,
  tuttonapoli: 1, calcionapoli24: 3, areanapoli: 5.7, calcionapoli1926: 7.22, spazionapoli: 1.12, ilnapolista: 4.29,
  elnacional: 7.01, ultimasnoticias: 7.68, eldiario: 5.25, '2001online': 1, correodelorinoco: 1.45, diariovea: 2.21, elpitazo: 1.9,
  runrunes: 6.3, cronicauno: 5.48, elestimulo: 5.65, caraotadigital: 3.05, informe21: 0.85, avn: 1.34, telesur: 0.93,
  venezuelanalysis: 7.56, caracaschronicles: 2.84, elcarabobeno: 5.52, primicia: 4.9,
  '20minutesfr': 0.98, '20minutoses': 1.0, '3djuegos': 1.0, abc: 1.0, ara: 2.0, bfmtv: 1.0, canard: 3.45, cnews: 5.16, courrier: 3.39,
  diariosur: 4.44, diariovasco: 10.11, efe: 1.49, elconfidencial: 5.0, elcorreo: 7.68, eldiarioes: 5.25, elespanol: 1.0, eurogamer: 8.81,
  eurogameres: 8.81, europapress: 8.28, everyeye: 5.32, france24: 1.0, franceinfo: 6.53, gamedeveloper: 5.58, gameinformer: 11.71, gamerant:
  7.25, gamereactor: 8.95, gamereactores: 8.95, gamesindustry: 3.31, gamesource: 4.82, gamesradar: 5.67, hobbyconsolas: 12.15, humanite: 4.68,
  ideal: 5.33, ign: 3.32, ignespana: 3.32, ignitalia: 3.32, kotaku: 5.43, lacroix: 5.27, larazon: 6.44, latribune: 5.08, lci: 5.75, lefigaro:
  7.44, lemonde: 4.49, lexpress: 4.75, libertaddigital: 6.9, lobs: 6.08, mediapart: 7.32, multiplayer: 8.07, nintendolife: 7.16, okdiario:
  1.52, pcgamer: 5.22, polygon: 1.0, publico: 0.94, purexbox: 7.27, pushsquare: 4.07, spaziogames: 0.96, surinenglish: 8.73, thegamer: 4.73,
  vandal: 6.19, vgc: 1.0 };

// testate la cui ricerca per data copre solo gli ultimi giorni (avviso sulle date)
const SOLO_RECENTE = { mattino: 1, messaggero: 1, independent: 90, '2001online': 3,
  abc: 3, libertaddigital: 3, elconfidencial: 3, vandal: 3, '20minutoses': 14, hobbyconsolas: 14, mediapart: 120,
  diariovasco: 42, elcorreo: 42, ideal: 42, surinenglish: 42, diariosur: 42 };
// date da cui l'archivio è affidabile quando il JSON non le mette in copertura_dal (si leggono nel testo della copertura)
const AFFIDABILE_DAL = { elpitazo: '2025-12-01', telesur: '2024-07-01', avn: '2024-04-01', eldiario: '2019-01-01', primicia: '2019-01-01',
  gameinformer: '2001-01-01', spaziogames: '2018-06-01', gamesource: '2008-01-01', franceinfo: '2011-01-01', bfmtv: '2006-01-01',
  lci: '2011-01-01', cnews: '2012-01-01', humanite: '1997-01-01', lemonde: '1944-12-01' };
// archivi che si fermano prima di oggi
const COPERTURA_FINO = { telesur: '2025-11-19' };

export const GRUPPI = [['italiane', 'Testate italiane'], ['estere', 'Testate estere'], ['napoli', 'Napoli, testate sportive'], ['venezuela', 'Venezuela'],
  ['videogiochi', 'Videogiochi'], ['francesi', 'Testate francesi'], ['spagnole', 'Testate spagnole']];

// lentezze dichiarate dai siti: pausa chiesta dal robots.txt o controlli in più (la piattaforma le rispetta)
export const LENTE = { vgc: 'Prima di iniziare cerca gli estremi del periodo: 2-3 minuti, con 5 secondi tra le richieste chiesti dal robots.txt.',
  kotaku: 'Controlla tutti gli articoli del mese, circa 300: anche un periodo breve richiede tempo.',
  cnews: 'Il robots.txt chiede 10 secondi tra le richieste: conviene un periodo breve.',
  courrier: 'Il robots.txt chiede 10 secondi tra le richieste: conviene un periodo breve.',
  pushsquare: 'Il robots.txt chiede 5 secondi tra le richieste.', purexbox: 'Il robots.txt chiede 5 secondi tra le richieste.',
  nintendolife: 'Il robots.txt chiede 5 secondi tra le richieste.', publico: 'Il robots.txt chiede 5 secondi tra le richieste.',
  mediapart: 'Il robots.txt chiede 3 secondi tra le richieste.' };

// Elenco delle fonti: le testate attive del motore (regole_testate.json) più YouTube
export const FONTI = [
  ...REGOLE.testate.filter((t) => t.stato === 'attiva').map((t) => ({
    chiave: t.chiave, nome: t.nome, dominio: t.dominio, gruppo: t.gruppo, lingua: t.lingua,
    coperturaDal: t.modalita.data.copertura_dal || AFFIDABILE_DAL[t.chiave] || null,
    coperturaFino: COPERTURA_FINO[t.chiave] ?? null, recenteGiorni: SOLO_RECENTE[t.chiave] ?? null,
    fonti: t.modalita.data.fonti_consentite, ricerca: t.modalita.parole_con_ricerca_del_sito.disponibile,
    primaPagina: t.modalita.elenco.solo_prima_pagina, guida: GUIDA[t.chiave] ?? guidaDaRegole(t),
    consigli: t.consigli, lenta: LENTE[t.chiave] ?? null, nota: (GUIDA[t.chiave] ?? guidaDaRegole(t)).periodo,
  })),
  { chiave: 'youtube', nome: 'YouTube', dominio: 'youtube.com', gruppo: 'video', nota: '' },
];

export const TESTATE = FONTI.filter((f) => f.gruppo !== 'video');

// La rassegna stampa è una fonte a sé per la coda e per il docente, ma non ha pagina propria
export const RASSEGNA = { chiave: 'rassegna', nome: 'Rassegna stampa', gruppo: 'rassegna', nota: '' };

export const trovaFonte = (chiave) => (chiave === 'rassegna' ? RASSEGNA : FONTI.find((f) => f.chiave === chiave));

export const oggi = () => new Date().toLocaleDateString('sv-SE', { timeZone: 'Europe/Rome' });
const giorniFa = (n) => new Date(Date.now() - n * 864e5).toLocaleDateString('sv-SE', { timeZone: 'Europe/Rome' });

// Limiti del calendario per una testata: dal primo giorno che l'archivio copre all'ultimo.
// Con Wayback si arriva fino al 1996 (nascita dell'Internet Archive), tranne SpazioNapoli, escluso dal robots.txt.
export function limitiDate(fonte, indirizzi = 'auto') {
  if (!fonte?.dominio) return { min: null, max: oggi() };
  if (indirizzi === 'wayback' && fonte.chiave !== 'spazionapoli') return { min: '1996-05-10', max: oggi() };
  if (indirizzi === 'gdelt') return { min: null, max: oggi() };
  const min = fonte.recenteGiorni ? giorniFa(fonte.recenteGiorni) : fonte.coperturaDal || null;
  return { min, max: fonte.coperturaFino || oggi() };
}

// Il periodo scelto esce da quello che l'archivio della testata copre? (avviso, non blocca)
export function fuoriArchivio(fonte, dal, al) {
  if (dal && fonte.coperturaDal && dal < fonte.coperturaDal) return `L'archivio di ${fonte.nome} è affidabile dal ${giorno.format(new Date(fonte.coperturaDal))}.`;
  if (al && fonte.coperturaFino && al > fonte.coperturaFino) return `L'archivio di ${fonte.nome} si ferma al ${giorno.format(new Date(fonte.coperturaFino))}.`;
  if (dal && fonte.recenteGiorni) {
    const limite = new Date(Date.now() - fonte.recenteGiorni * 864e5).toISOString().slice(0, 10);
    if (dal < limite) return `Per data ${fonte.nome} copre solo ${fonte.recenteGiorni === 1 ? 'le uscite del giorno' : `gli ultimi ${fonte.recenteGiorni} giorni circa`}.`;
  }
  return null;
}

export const data = new Intl.DateTimeFormat('it-IT', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Europe/Rome' });
export const giorno = new Intl.DateTimeFormat('it-IT', { dateStyle: 'short', timeZone: 'Europe/Rome' });
const mb = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 1 });
export const peso = (byte) => `${mb.format(byte / 1048576)}\u00A0MB`;

export function statoFonte(f) {
  if (f.disponibile) return { testo: 'Disponibile', colore: 'var(--ok)' };
  if (f.esito === 'mai') return { testo: 'In verifica', colore: '#8792A2' };
  return { testo: 'Solo in locale', colore: 'var(--attenzione)' };
}
