'use client';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const fmt = new Intl.NumberFormat('it-IT');
export default function Contatore({ valore }) {
  const r = useRef(null);
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const o = { v: 0 };
    const tw = gsap.to(o, { v: valore, duration: 1.6, ease: 'expo.out', delay: 0.35, onUpdate: () => { r.current.textContent = fmt.format(Math.round(o.v)); } });
    return () => tw.kill();
  }, [valore]);
  return <b ref={r} className="numeri">{fmt.format(valore)}</b>;
}
