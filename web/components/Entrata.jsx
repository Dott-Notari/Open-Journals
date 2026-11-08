'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

// Un solo momento di entrata per pagina: i blocchi salgono in sequenza.
export default function Entrata({ children, className, style }) {
  const r = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const ctx = gsap.context(() => {
      gsap.from(r.current.children, { autoAlpha: 0, y: 24, scale: 0.985, duration: 0.7, ease: 'expo.out', stagger: 0.06 });
    }, r);
    return () => ctx.revert();
  }, []);
  return <div ref={r} className={className} style={style}>{children}</div>;
}
