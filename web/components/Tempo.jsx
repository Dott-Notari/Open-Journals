'use client';
import { useEffect, useState } from 'react';

// Un solo orologio al secondo condiviso da tutti i contatori della pagina.
const ascoltatori = new Set();
let timer;
function iscrivi(fn) {
  ascoltatori.add(fn);
  timer ??= setInterval(() => ascoltatori.forEach((f) => f(Date.now())), 1000);
  return () => { ascoltatori.delete(fn); if (!ascoltatori.size) { clearInterval(timer); timer = undefined; } };
}
export function useAdesso() {
  const [adesso, setAdesso] = useState(() => Date.now());
  useEffect(() => iscrivi(setAdesso), []);
  return adesso;
}

export function durata(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  const due = (n) => String(n).padStart(2, '0');
  return h ? `${h}:${due(m)}:${due(r)}` : `${m}:${due(r)}`;
}

// Tempo trascorso dall'inizio; a estrazione conclusa resta fermo sulla durata finale.
export function Cronometro({ inizio, fine }) {
  const adesso = useAdesso();
  if (!inizio) return null;
  const ms = (fine ? new Date(fine).getTime() : adesso) - new Date(inizio).getTime();
  return <span className="numeri cronometro" aria-label={`Tempo trascorso ${durata(ms)}`}>{durata(ms)}</span>;
}

const SEGNALI = {
  ok: ['Motore attivo', 'var(--ok)'],
  lento: ['Il sito rallenta', 'var(--attenzione)'],
  rete: ['Rete instabile', 'var(--attenzione)'],
  fermo: ['Nessun progresso', 'var(--errore)'],
  bloccato: ['Bloccato dal sito', 'var(--errore)'],
};

// Spia del motore: legge il battito che il workflow invia ogni 15 secondi.
export function Spia({ stato, battito, segnale, testo, avviata }) {
  const adesso = useAdesso();
  let etichetta, colore, dettaglio = testo, vivo = false;
  if (stato === 'avviata' || (stato === 'in_corso' && !battito)) {
    const attesa = adesso - new Date(avviata ?? adesso).getTime();
    [etichetta, colore] = attesa > 300000 ? ['Avvio lento', 'var(--attenzione)'] : ['Il server si prepara', 'var(--tenue)'];
    dettaglio = attesa > 300000 ? 'Il server non ha ancora iniziato: se resta così, la richiesta torna in coda da sola.' : null;
  } else {
    const silenzio = adesso - new Date(battito).getTime();
    if (silenzio > 90000) {
      [etichetta, colore] = ['Nessun segnale', 'var(--errore)'];
      dettaglio = `Il motore non risponde da ${durata(silenzio)}. Se il silenzio continua, l'estrazione verrà chiusa con un errore.`;
    } else {
      [etichetta, colore] = SEGNALI[segnale] ?? SEGNALI.ok;
      vivo = true;
    }
  }
  return (
    <span className="spia" style={{ '--c': colore }} title={dettaglio ?? undefined} role="status">
      <span className={`spia-punto${vivo ? ' vivo' : ''}`} aria-hidden="true" />{etichetta}
      {dettaglio && <span className="nascosto">: {dettaglio}</span>}
    </span>
  );
}
