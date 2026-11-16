'use client';
import { useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, Check, X } from 'lucide-react';

const LATO = 512; // pixel della foto salvata

// Ritaglio quadrato con anteprima circolare: si trascina per centrare, si ingrandisce con
// il cursore, la rotella o le dita; da tastiera frecce per spostare e + / - per lo zoom.
export default function RitaglioFoto({ file, onFatto, onAnnulla }) {
  const dialogo = useRef(null), area = useRef(null);
  const [img, setImg] = useState(null);
  const [vista, setVista] = useState({ x: 0, y: 0, z: 1 });
  const base = useRef(1), puntatori = useRef(new Map()), distanza = useRef(0);

  useEffect(() => {
    dialogo.current.showModal();
    const url = URL.createObjectURL(file);
    const i = new Image();
    i.onload = () => {
      const lato = area.current.clientWidth;
      base.current = lato / Math.min(i.naturalWidth, i.naturalHeight);
      setImg({ el: i, url, w: i.naturalWidth, h: i.naturalHeight, lato });
      setVista({ z: 1, x: (lato - i.naturalWidth * base.current) / 2, y: (lato - i.naturalHeight * base.current) / 2 });
    };
    i.src = url;
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // l'immagine deve sempre coprire tutto il riquadro
  const limita = (v) => {
    if (!img) return v;
    const s = base.current * v.z, w = img.w * s, h = img.h * s;
    return { z: v.z, x: Math.min(0, Math.max(img.lato - w, v.x)), y: Math.min(0, Math.max(img.lato - h, v.y)) };
  };
  const zoom = (z, cx = img?.lato / 2, cy = img?.lato / 2) => setVista((v) => {
    const nz = Math.min(5, Math.max(1, z));
    const k = nz / v.z;
    return limita({ z: nz, x: cx - (cx - v.x) * k, y: cy - (cy - v.y) * k });
  });

  function giu(e) { area.current.setPointerCapture(e.pointerId); puntatori.current.set(e.pointerId, [e.clientX, e.clientY]); }
  function muovi(e) {
    const p = puntatori.current;
    if (!p.has(e.pointerId)) return;
    const [px, py] = p.get(e.pointerId);
    p.set(e.pointerId, [e.clientX, e.clientY]);
    if (p.size === 2) {
      const [a, b] = [...p.values()];
      const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (distanza.current) zoom(vista.z * (d / distanza.current));
      distanza.current = d;
      return;
    }
    setVista((v) => limita({ ...v, x: v.x + e.clientX - px, y: v.y + e.clientY - py }));
  }
  function su(e) { puntatori.current.delete(e.pointerId); distanza.current = 0; }
  function rotella(e) {
    const r = area.current.getBoundingClientRect();
    zoom(vista.z * (e.deltaY < 0 ? 1.08 : 1 / 1.08), e.clientX - r.left, e.clientY - r.top);
  }
  function tasto(e) {
    const passi = { ArrowLeft: [12, 0], ArrowRight: [-12, 0], ArrowUp: [0, 12], ArrowDown: [0, -12] };
    if (passi[e.key]) { e.preventDefault(); setVista((v) => limita({ ...v, x: v.x + passi[e.key][0], y: v.y + passi[e.key][1] })); }
    if (e.key === '+' || e.key === '=') zoom(vista.z * 1.1);
    if (e.key === '-') zoom(vista.z / 1.1);
  }
  useEffect(() => {
    const el = area.current;
    const blocca = (e) => e.preventDefault(); // la rotella non deve scorrere la pagina
    el.addEventListener('wheel', blocca, { passive: false });
    return () => el.removeEventListener('wheel', blocca);
  }, []);

  function conferma() {
    const s = base.current * vista.z;
    const c = document.createElement('canvas');
    c.width = c.height = LATO;
    c.getContext('2d').drawImage(img.el, -vista.x / s, -vista.y / s, img.lato / s, img.lato / s, 0, 0, LATO, LATO);
    c.toBlob((b) => b && onFatto(b), 'image/webp', 0.9);
  }
  const s = base.current * vista.z;

  return (
    <dialog ref={dialogo} className="ritaglio vetro" onCancel={(e) => { e.preventDefault(); onAnnulla(); }} aria-labelledby="titolo-ritaglio">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <h2 id="titolo-ritaglio" className="titolo-3">Centra la foto</h2>
        <div ref={area} className="ritaglio-area" tabIndex={0} role="application" aria-label="Area di ritaglio: trascina per spostare, frecce per spostare, più e meno per ingrandire"
          onPointerDown={giu} onPointerMove={muovi} onPointerUp={su} onPointerCancel={su} onWheel={rotella} onKeyDown={tasto}>
          {img && <img src={img.url} alt="" style={{ width: img.w, height: img.h, transform: `translate(${vista.x}px, ${vista.y}px) scale(${s})` }} />}
        </div>
        <label className="riga" style={{ gap: 10, flexWrap: 'nowrap' }}>
          <ZoomOut size={18} aria-hidden="true" />
          <input type="range" min={1} max={5} step={0.01} value={vista.z} onChange={(e) => zoom(Number(e.target.value))} aria-label="Ingrandimento" />
          <ZoomIn size={18} aria-hidden="true" />
        </label>
        <div className="riga" style={{ justifyContent: 'flex-end', gap: 8 }}>
          <button type="button" className="pulsante compatto secondario" onClick={onAnnulla}><X size={17} aria-hidden="true" />Annulla</button>
          <button type="button" className="pulsante compatto" onClick={conferma} disabled={!img}><Check size={17} aria-hidden="true" />Usa questa foto</button>
        </div>
      </div>
    </dialog>
  );
}
