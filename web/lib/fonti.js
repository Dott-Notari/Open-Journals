import REGOLE from './regole_testate.json';
import { GUIDA } from './guida';

// larghezza / altezza dei file in public/loghi (le testate senza file mostrano il nome)
export const RAPPORTI = { ansa: 1, corriere: 12.93, fatto: 2.45, ilgiornale: 6.64, manifesto: 6, mattino: 7, messaggero: 5.64,
  ilpost: 2.82, sole24ore: 4.52, repubblica: 5.21, lastampa: 8.28, verita: 4.62, libero: 4.84, avvenire: 3.58, youtube: 4.47,
  independent: 4.29, mirror: 2.64, elmundo: 7.5,
  tuttonapoli: 1, calcionapoli24: 3, areanapoli: 5.7, calcionapoli1926: 7.22, spazionapoli: 1.12, ilnapolista: 4.29,
  elnacional: 7.01, ultimasnoticias: 7.68, eldiario: 5.25, '2001online': 1, correodelorinoco: 1.45, diariovea: 2.21, elpitazo: 1.9,
  runrunes: 6.3, cronicauno: 5.48, elestimulo: 5.65, caraotadigital: 3.05, informe21: 0.85, avn: 1.34, telesur: 0.93,
  venezuelanalysis: 7.56, caracaschronicles: 2.84, elcarabobeno: 5.52, primicia: 4.9 };

// testate la cui ricerca per data copre solo gli ultimi giorni (avviso sulle date)
const SOLO_RECENTE = { mattino: 1, messaggero: 1, independent: 90, '2001online': 3 };
// date da cui l'archivio è affidabile quando il JSON non le mette in copertura_dal (si leggono nel testo della copertura)
const AFFIDABILE_DAL = { elpitazo: '2025-12-01', telesur: '2024-07-01', avn: '2024-04-01', eldiario: '2019-01-01', primicia: '2019-01-01' };
// archivi che si fermano prima di oggi
const COPERTURA_FINO = { telesur: '2025-11-19' };

export const GRUPPI = [['italiane', 'Testate italiane'], ['estere', 'Testate estere'], ['napoli', 'Napoli, testate sportive'], ['venezuela', 'Venezuela']];

// Elenco delle fonti: le testate attive del motore (regole_testate.json) più YouTube
export const FONTI = [
  ...REGOLE.testate.filter((t) => t.stato === 'attiva').map((t) => ({
    chiave: t.chiave, nome: t.nome, dominio: t.dominio, gruppo: t.gruppo, lingua: t.lingua,
    coperturaDal: t.modalita.data.copertura_dal || AFFIDABILE_DAL[t.chiave] || null,
    coperturaFino: COPERTURA_FINO[t.chiave] ?? null, recenteGiorni: SOLO_RECENTE[t.chiave] ?? null,
    fonti: t.modalita.data.fonti_consentite, ricerca: t.modalita.parole_con_ricerca_del_sito.disponibile,
    primaPagina: t.modalita.elenco.solo_prima_pagina, guida: GUIDA[t.chiave], nota: GUIDA[t.chiave]?.periodo ?? '',
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
