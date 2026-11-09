'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

// Ingresso della pagina di una fonte: il logo si «stampa» da sinistra, poi salgono i blocchi.
export default function Rivela({ children, style }) {
  const r = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const ctx = gsap.context(() => {
      gsap.timeline({ defaults: { ease: 'expo.out' } })
        .from('[data-placca]', { scale: 0.9, autoAlpha: 0, duration: 0.7 })
        .fromTo('[data-placca] img', { clipPath: 'inset(0% 100% 0% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 0.9, ease: 'power3.inOut', clearProps: 'clipPath' }, 0.15)
        .from('[data-sale]', { autoAlpha: 0, y: 22, duration: 0.8, stagger: 0.07 }, 0.25);
    }, r);
    return () => ctx.revert();
  }, []);
  return <div ref={r} style={style}>{children}</div>;
}
