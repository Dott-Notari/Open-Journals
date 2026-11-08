const GENERICA = 'Per periodo, da una pagina di sezione, tag o rubrica, oppure da link.';

// larghezza / altezza dei file in public/loghi
export const RAPPORTI = { ansa: 1, corriere: 12.93, fatto: 2.45, ilgiornale: 6.64, manifesto: 6, mattino: 7, messaggero: 5.64,
  ilpost: 2.82, sole24ore: 4.52, repubblica: 5.21, lastampa: 8.28, verita: 4.62, libero: 4.84, avvenire: 3.58, youtube: 4.47, unisa: 1 };

export const FONTI = [
  { chiave: 'ilgiornale', nome: 'il Giornale', dominio: 'ilgiornale.it' },
  { chiave: 'avvenire', nome: 'Avvenire', dominio: 'avvenire.it',
    nota: "Archivio online dal 2000. Per gli anni più lontani è una selezione." },
  { chiave: 'fatto', nome: 'Il Fatto Quotidiano', dominio: 'ilfattoquotidiano.it' },
  { chiave: 'ansa', nome: 'ANSA', dominio: 'ansa.it',
    nota: "La ricerca per periodo usa l'indice quotidiano delle uscite, che parte dal giorno di attivazione della piattaforma." },
  { chiave: 'ilpost', nome: 'Il Post', dominio: 'ilpost.it' },
  { chiave: 'libero', nome: 'Libero', dominio: 'liberoquotidiano.it' },
  { chiave: 'manifesto', nome: 'il manifesto', dominio: 'ilmanifesto.it' },
  { chiave: 'mattino', nome: 'Il Mattino', dominio: 'ilmattino.it' },
  { chiave: 'corriere', nome: 'Corriere della Sera', dominio: 'corriere.it' },
  { chiave: 'repubblica', nome: 'la Repubblica', dominio: 'repubblica.it' },
  { chiave: 'lastampa', nome: 'La Stampa', dominio: 'lastampa.it' },
  { chiave: 'messaggero', nome: 'Il Messaggero', dominio: 'ilmessaggero.it' },
  { chiave: 'verita', nome: 'La Verità', dominio: 'laverita.info' },
  { chiave: 'sole24ore', nome: 'Il Sole 24 Ore', dominio: 'ilsole24ore.com' },
  { chiave: 'youtube', nome: 'YouTube', dominio: 'youtube.com' },
].map((f) => ({ nota: GENERICA, ...f }));

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
