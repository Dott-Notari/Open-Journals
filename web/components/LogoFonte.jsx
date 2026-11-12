'use client';
import { useState } from 'react';
import { RAPPORTI } from '@/lib/fonti';

// Dimensione ottica: loghi larghi e loghi quadrati occupano un'area simile.
export default function LogoFonte({ chiave, nome, area = 3600, massimo = 64 }) {
  const [manca, setManca] = useState(false);
  const r = RAPPORTI[chiave] ?? 4;
  const altezza = Math.round(Math.min(massimo, Math.max(16, Math.sqrt(area / r))));
  if (manca) return <span style={{ fontWeight: 650, fontSize: '1.3rem', color: '#0B1B2B' }} translate="no">{nome}</span>;
  return (
    <img src={`/loghi/${chiave}.webp`} alt={nome} height={altezza} width={Math.round(altezza * r)} decoding="async"
      style={{ height: altezza, width: 'auto', maxWidth: '100%' }} onError={() => setManca(true)} />
  );
}
