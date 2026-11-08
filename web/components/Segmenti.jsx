'use client';
import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';

// Il cursore di vetro scivola sotto la scelta e si allunga durante lo spostamento.
export default function Segmenti({ voci, valore, onCambio, etichetta }) {
  const box = useRef(null), cursore = useRef(null), primo = useRef(true);
  useLayoutEffect(() => {
    const b = box.current.querySelector('[aria-pressed="true"]');
    if (!b) return;
    const meta = { x: b.offsetLeft, width: b.offsetWidth };
    if (primo.current || matchMedia('(prefers-reduced-motion: reduce)').matches) { gsap.set(cursore.current, meta); primo.current = false; return; }
    gsap.timeline({ overwrite: true })
      .to(cursore.current, { ...meta, duration: 0.55, ease: 'expo.out' }, 0)
      .fromTo(cursore.current, { scaleY: 0.86 }, { scaleY: 1, duration: 0.5, ease: 'elastic.out(1, 0.5)' }, 0);
  }, [valore]);
  return (
    <div ref={box} role="group" aria-label={etichetta} className="segmenti vetro" style={{ alignSelf: 'flex-start' }}>
      <span ref={cursore} className="cursore" aria-hidden="true" />
      {voci.map(([k, testo, Icona]) => (
        <button key={k} type="button" className="segmento" aria-pressed={k === valore} onClick={() => onCambio(k)}>
          {Icona && <Icona size={17} aria-hidden="true" />}{testo}
        </button>
      ))}
    </div>
  );
}
