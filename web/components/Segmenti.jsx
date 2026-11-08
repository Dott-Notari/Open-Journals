'use client';
import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';

// Controllo a segmenti: il cursore di vetro scivola sotto la scelta attiva.
export default function Segmenti({ voci, valore, onCambio, etichetta }) {
  const box = useRef(null);
  const cursore = useRef(null);
  useLayoutEffect(() => {
    const b = box.current.querySelector('[aria-pressed="true"]');
    if (!b) return;
    const meta = { x: b.offsetLeft, width: b.offsetWidth };
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) gsap.set(cursore.current, meta);
    else gsap.to(cursore.current, { ...meta, duration: 0.5, ease: 'expo.out', overwrite: true });
  }, [valore]);
  return (
    <div ref={box} role="group" aria-label={etichetta} className="segmenti vetro" style={{ alignSelf: 'flex-start' }}>
      <span ref={cursore} className="segmenti-cursore" aria-hidden="true" />
      {voci.map(([k, testo]) => (
        <button key={k} type="button" className="segmento" aria-pressed={k === valore} onClick={() => onCambio(k)}>{testo}</button>
      ))}
    </div>
  );
}
