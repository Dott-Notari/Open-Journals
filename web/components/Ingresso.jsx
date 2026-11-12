'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

// L'unico ingresso orchestrato: il logo sale, la pallina compare, poi il resto.
export default function Ingresso({ children, className, style }) {
  const r = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const ctx = gsap.context(() => {
      gsap.timeline({ defaults: { ease: 'expo.out' } })
        .from('[data-logo]', { autoAlpha: 0, y: 28, scale: 0.97, duration: 1.1, clearProps: 'transform' })
        .from('[data-logo] .onm-knob', { opacity: 0, duration: 0.6 }, 0.45)
        .from('[data-segue]', { autoAlpha: 0, y: 14, duration: 0.8, stagger: 0.06 }, 0.35);
    }, r);
    return () => ctx.revert();
  }, []);
  return <div ref={r} className={className} style={style}>{children}</div>;
}
