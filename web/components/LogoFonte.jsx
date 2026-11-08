'use client';
import { useEffect, useRef, useState } from 'react';

// Mostra /loghi/<chiave>.svg; se il file non c'è ancora, il nome della fonte.
export default function LogoFonte({ chiave, nome, altezza = 52 }) {
  const img = useRef(null);
  const [manca, setManca] = useState(false);
  useEffect(() => {
    const i = img.current; // l'errore può arrivare prima dell'idratazione
    if (i && i.complete && i.naturalWidth === 0) setManca(true);
  }, []);
  if (manca) return <span className="logo-testo" translate="no">{nome}</span>;
  return (
    <img ref={img} src={`/loghi/${chiave}.svg`} alt={nome} height={altezza} width={altezza * 3}
      style={{ height: altezza, width: 'auto', maxWidth: '100%', objectFit: 'contain' }} onError={() => setManca(true)} />
  );
}
