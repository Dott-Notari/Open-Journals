'use client';
import { useState } from 'react';
import { RAPPORTI } from '@/lib/fonti';

// Dimensione ottica: loghi larghi e loghi quadrati occupano un'area simile.
export default function LogoFonte({ chiave, nome, area = 3600, massimo = 64 }) {
  const [manca, setManca] = useState(false);
  const r = RAPPORTI[chiave];
  if (manca || !r) return <span style={{ fontWeight: 650, fontSize: `${Math.max(0.85, Math.min(1.3, massimo / 46))}rem`, lineHeight: 1.1, letterSpacing: '-0.01em', color: '#111111', textAlign: 'center' }} translate="no">{nome}</span>;
  const altezza = Math.round(Math.min(massimo, Math.max(16, Math.sqrt(area / r))));
  return (
    <img src={`/loghi/${chiave}.webp`} alt={nome} height={altezza} width={Math.round(altezza * r)} decoding="async"
      style={{ height: altezza, width: 'auto', maxWidth: '100%' }} onError={() => setManca(true)} />
  );
}
