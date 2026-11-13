import REGOLE from './regole_testate.json';
import { GUIDA } from './guida';

// larghezza / altezza dei file in public/loghi (le testate senza file mostrano il nome)
export const RAPPORTI = { ansa: 1, corriere: 12.93, fatto: 2.45, ilgiornale: 6.64, manifesto: 6, mattino: 7, messaggero: 5.64,
  ilpost: 2.82, sole24ore: 4.52, repubblica: 5.21, lastampa: 8.28, verita: 4.62, libero: 4.84, avvenire: 3.58, youtube: 4.47,
  independent: 4.29, mirror: 2.64, elmundo: 7.5 };

// testate la cui ricerca per data copre solo gli ultimi giorni (avviso sulle date)
const SOLO_RECENTE = { mattino: 1, messaggero: 1, independent: 90 };

// Elenco delle fonti: le testate attive del motore (regole_testate.json) più YouTube
export const FONTI = [
  ...REGOLE.testate.filter((t) => t.stato === 'attiva').map((t) => ({
    chiave: t.chiave, nome: t.nome, dominio: t.dominio, gruppo: t.gruppo, lingua: t.lingua,
    coperturaDal: t.modalita.data.copertura_dal, recenteGiorni: SOLO_RECENTE[t.chiave] ?? null,
    fonti: t.modalita.data.fonti_consentite, ricerca: t.modalita.parole_con_ricerca_del_sito.disponibile,
    primaPagina: t.modalita.elenco.solo_prima_pagina, guida: GUIDA[t.chiave], nota: GUIDA[t.chiave]?.periodo ?? '',
  })),
  { chiave: 'youtube', nome: 'YouTube', dominio: 'youtube.com', gruppo: 'video', nota: '' },
];

export const trovaFonte = (chiave) => FONTI.find((f) => f.chiave === chiave);

export const data = new Intl.DateTimeFormat('it-IT', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Europe/Rome' });
export const giorno = new Intl.DateTimeFormat('it-IT', { dateStyle: 'short', timeZone: 'Europe/Rome' });
const mb = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 1 });
export const peso = (byte) => `${mb.format(byte / 1048576)}\u00A0MB`;

export function statoFonte(f) {
  if (f.disponibile) return { testo: 'Disponibile', colore: 'var(--ok)' };
  if (f.esito === 'mai') return { testo: 'In verifica', colore: '#8792A2' };
  return { testo: 'Solo in locale', colore: 'var(--attenzione)' };
}
