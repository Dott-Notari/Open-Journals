'use client';
import { useEffect, useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';

// Il cursore di vetro scivola sotto la scelta. Si riallinea quando cambiano i caratteri o la larghezza.
export default function Segmenti({ voci, valore, onCambio, etichetta }) {
  const box = useRef(null), cursore = useRef(null), pronto = useRef(false);
  const misura = () => {
    const b = box.current?.querySelector('[aria-pressed="true"]');
    return b && { x: b.offsetLeft, width: b.offsetWidth };
  };
  useLayoutEffect(() => {
    const meta = misura();
    if (!meta) return;
    if (!pronto.current || matchMedia('(prefers-reduced-motion: reduce)').matches) { gsap.set(cursore.current, meta); pronto.current = true; return; }
    gsap.timeline()
      .to(cursore.current, { ...meta, duration: 0.55, ease: 'expo.out', overwrite: 'auto' }, 0)
      .fromTo(cursore.current, { scaleY: 0.86 }, { scaleY: 1, duration: 0.5, ease: 'elastic.out(1, 0.5)' }, 0);
  }, [valore]);
  useEffect(() => {
    const allinea = () => { const m = misura(); if (m) gsap.set(cursore.current, m); };
    const ro = new ResizeObserver(allinea);
    ro.observe(box.current);
    box.current.querySelectorAll('button').forEach((b) => ro.observe(b));
    document.fonts?.ready.then(allinea);
    return () => ro.disconnect();
  }, []);
  return (
    <div ref={box} role="group" aria-label={etichetta} className="segmenti vetro">
      <span ref={cursore} className="cursore" aria-hidden="true" />
      {voci.map(([k, testo, Icona]) => (
        <button key={k} type="button" className="segmento" aria-pressed={k === valore} onClick={() => onCambio(k)}>
          {Icona && <Icona size={17} aria-hidden="true" />}{testo}
        </button>
      ))}
    </div>
  );
}
