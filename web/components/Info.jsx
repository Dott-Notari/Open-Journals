'use client';
import { useEffect, useId, useRef, useState } from 'react';
import gsap from 'gsap';
import { Info as Icona } from 'lucide-react';

// Spiegazione su richiesta: nasce dall'icona, si chiude con Esc o cliccando fuori.
export default function Info({ children, etichetta = 'Informazioni' }) {
  const [aperta, setAperta] = useState(false);
  const box = useRef(null), nota = useRef(null);
  const id = useId();
  useEffect(() => {
    if (!aperta) return;
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches)
      gsap.fromTo(nota.current, { scale: 0.85, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.32, ease: 'back.out(1.6)' });
    const fuori = (e) => { if (!box.current.contains(e.target)) setAperta(false); };
    const esc = (e) => { if (e.key === 'Escape') setAperta(false); };
    document.addEventListener('pointerdown', fuori);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('pointerdown', fuori); document.removeEventListener('keydown', esc); };
  }, [aperta]);
  return (
    <span className="info" ref={box}>
      <button type="button" aria-label={etichetta} aria-expanded={aperta} aria-controls={id} onClick={() => setAperta((a) => !a)}>
        <Icona size={17} aria-hidden="true" />
      </button>
      {aperta && <span id={id} ref={nota} role="note" className="nota vetro">{children}</span>}
    </span>
  );
}
