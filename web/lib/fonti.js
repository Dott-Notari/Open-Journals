const GENERICA = 'Ricerca per periodo, da una pagina elenco (sezione, tag, rubrica) o da link.';

export const FONTI = [
  { chiave: 'ilgiornale', nome: 'il Giornale', dominio: 'ilgiornale.it' },
  { chiave: 'avvenire', nome: 'Avvenire', dominio: 'avvenire.it',
    nota: "Archivio online dal 2000; per gli anni meno recenti è una selezione. La data esatta si legge in ogni articolo." },
  { chiave: 'fatto', nome: 'Il Fatto Quotidiano', dominio: 'ilfattoquotidiano.it' },
  { chiave: 'ansa', nome: 'ANSA', dominio: 'ansa.it',
    nota: "Ricerca per periodo attraverso l'indice quotidiano della piattaforma, disponibile dal giorno della sua attivazione." },
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
  if (f.esito === 'mai') return { testo: 'In attesa di collaudo', colore: '#8792A2' };
  return { testo: 'Solo scraper locale', colore: 'var(--attenzione)' };
}
