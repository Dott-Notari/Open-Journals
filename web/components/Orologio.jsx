'use client';
import { useEffect, useState } from 'react';

const giorno = new Intl.DateTimeFormat('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Rome' });
const ora = new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Rome' });

// Giorno, data e ora di Roma; si aggiorna allo scoccare di ogni minuto.
export default function Orologio() {
  const [adesso, setAdesso] = useState(null);
  useEffect(() => {
    let t;
    const batti = () => { setAdesso(new Date()); t = setTimeout(batti, 60000 - (Date.now() % 60000) + 50); };
    batti();
    return () => clearTimeout(t);
  }, []);
  if (!adesso) return <span className="orologio" aria-hidden="true" />;
  return (
    <time className="orologio" dateTime={adesso.toISOString()}>
      <span className="data">{giorno.format(adesso)}</span>
      <span className="ora numeri">{ora.format(adesso)}</span>
    </time>
  );
}
