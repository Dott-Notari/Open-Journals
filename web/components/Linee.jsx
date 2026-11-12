'use client';
import { useEffect, useRef } from 'react';

// Fondale: righe di stampa che ondeggiano e si piegano al passaggio del puntatore.
export default function Linee() {
  const tela = useRef(null);
  useEffect(() => {
    const c = tela.current, ctx = c.getContext('2d');
    const html = document.documentElement;
    const fermo = () => html.hasAttribute('data-pausa') || matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w, h, colore, raf, px = -1e4, py = -1e4;
    const misura = () => {
      const d = Math.min(devicePixelRatio || 1, 2);
      w = innerWidth; h = innerHeight; c.width = w * d; c.height = h * d; ctx.setTransform(d, 0, 0, d, 0, 0);
      colore = getComputedStyle(html).getPropertyValue('--trama').trim() || '#9C9C9C';
    };
    const disegna = (t) => {
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = colore; ctx.lineWidth = 1;
      for (let i = 0, y0 = 18; y0 < h + 20; i++, y0 += 26) {
        ctx.globalAlpha = 0.16 + 0.1 * Math.sin(i * 0.7);
        ctx.beginPath();
        for (let x = -10; x <= w + 10; x += 18) {
          const dist = Math.hypot(x - px, y0 - py);
          const spinta = Math.exp(-(dist * dist) / 18000) * 22;
          const y = y0 + Math.sin(x * 0.006 + t * 0.00045 + i * 0.37) * 5 + Math.sin(x * 0.0021 - t * 0.0003 + i) * 7 - spinta;
          x < 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
    };
    const ciclo = (t) => { disegna(t); raf = fermo() ? 0 : requestAnimationFrame(ciclo); };
    const riparti = () => { cancelAnimationFrame(raf); misura(); fermo() ? disegna(0) : (raf = requestAnimationFrame(ciclo)); };
    const muovi = (e) => { px = e.clientX; py = e.clientY; };
    misura(); riparti();
    addEventListener('resize', riparti);
    addEventListener('pointermove', muovi, { passive: true });
    const osserva = new MutationObserver(riparti);
    osserva.observe(html, { attributes: true, attributeFilter: ['data-pausa', 'data-tema'] });
    const schema = matchMedia('(prefers-color-scheme: dark)');
    schema.addEventListener('change', riparti);
    return () => { cancelAnimationFrame(raf); removeEventListener('resize', riparti); removeEventListener('pointermove', muovi); osserva.disconnect(); schema.removeEventListener('change', riparti); };
  }, []);
  return <canvas ref={tela} className="linee" aria-hidden="true" />;
}
