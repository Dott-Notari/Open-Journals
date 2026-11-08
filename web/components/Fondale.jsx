'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const PAROLE = ['migranti', 'confine', 'accoglienza', 'identità', 'frontiera', 'integrazione', 'diaspora', 'cittadinanza',
  'Mediterraneo', 'lingua', 'comunità', 'dialogo', 'seconde generazioni', 'sbarchi', 'intercultura', 'appartenenza',
  'stranieri', 'religione', 'ospitalità', 'memoria', 'radici', 'viaggio'];

export default function Fondale() {
  const strato = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const x = gsap.quickTo(strato.current, 'x', { duration: 1.4, ease: 'power3.out' });
    const y = gsap.quickTo(strato.current, 'y', { duration: 1.4, ease: 'power3.out' });
    const muovi = (e) => { x((e.clientX / innerWidth - 0.5) * -24); y((e.clientY / innerHeight - 0.5) * -24); };
    addEventListener('pointermove', muovi, { passive: true });
    return () => removeEventListener('pointermove', muovi);
  }, []);
  return (
    <div className="fondale" aria-hidden="true">
      <div className="parole" ref={strato}>{PAROLE.map((p) => <span key={p}>{p}</span>)}</div>
    </div>
  );
}
