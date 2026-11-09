'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

// L'unico ingresso orchestrato: le righe del titolo salgono dalla loro maschera, poi il resto.
export default function Ingresso({ children, className, style }) {
  const r = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const ctx = gsap.context(() => {
      gsap.timeline({ defaults: { ease: 'expo.out' } })
        .from('.maschera > span', { yPercent: 110, duration: 1.1, stagger: 0.08 })
        .from('[data-segue]', { autoAlpha: 0, y: 14, duration: 0.8, stagger: 0.06 }, 0.35);
    }, r);
    return () => ctx.revert();
  }, []);
  return <div ref={r} className={className} style={style}>{children}</div>;
}
