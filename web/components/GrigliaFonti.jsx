'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { ArrowUpRight, Search } from 'lucide-react';
import LogoFonte from './LogoFonte';
import { statoFonte, GRUPPI } from '@/lib/fonti';

const ridotto = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// Tessera di vetro: la lastra con il logo segue di poco il puntatore e si avvicina.
function Tessera({ f, onApri, children, href = `/fonti/${f.chiave}`, largo }) {
  const el = useRef(null);
  const giri = useRef(null);
  useEffect(() => {
    if (ridotto()) return;
    const faccia = el.current.querySelector('.faccia');
    giri.current = { x: gsap.quickTo(faccia, 'x', { duration: 0.6, ease: 'power3.out' }),
      y: gsap.quickTo(faccia, 'y', { duration: 0.6, ease: 'power3.out' }),
      s: gsap.quickTo(faccia, 'scale', { duration: 0.6, ease: 'power3.out' }) };
  }, []);
  function muovi(e) {
    const r = el.current.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width - 0.5, ny = (e.clientY - r.top) / r.height - 0.5;
    el.current.style.setProperty('--mx', `${(nx + 0.5) * 100}%`);
    el.current.style.setProperty('--my', `${(ny + 0.5) * 100}%`);
    giri.current?.x(nx * 8); giri.current?.y(ny * 6); giri.current?.s(1.03);
  }
  const fuori = () => { giri.current?.x(0); giri.current?.y(0); giri.current?.s(1); };
  const s = statoFonte(f);
  const video = f.chiave === 'youtube';
  return (
    <Link ref={el} href={href} className={`tessera vetro${video || largo ? ' video' : ''}`} data-tessera=""
      onPointerMove={muovi} onPointerLeave={fuori} onClick={(e) => onApri(e, el.current, href)}
      aria-label={`${f.nome}, ${s.testo.toLowerCase()}`}>
      <span className="faccia">{children ?? <LogoFonte chiave={f.chiave} nome={f.nome} area={video ? 9000 : 3800} massimo={video ? 72 : 60} />}</span>
      <span className="piede">
        {largo ? (
          <>
            <span className="titolo-3">Rassegna stampa</span>
            <span className="tenue">La stessa ricerca, per periodo, su più testate insieme: un solo archivio con una scheda per testata</span>
            <span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>
          </>
        ) : video ? (
          <>
            <span className="titolo-3">Video da YouTube</span>
            <span className="tenue">Video singoli, playlist e canali, con il testo del parlato</span>
            <span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>
          </>
        ) : (
<span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>
        )}
      </span>
      <ArrowUpRight size={18} aria-hidden="true" style={{ position: 'absolute', top: 18, right: 18, opacity: 0.35 }} />
      <span className="lucido" aria-hidden="true" />
    </Link>
  );
}

export default function GrigliaFonti({ fonti }) {
  const router = useRouter();
  const box = useRef(null);
  useEffect(() => {
    if (ridotto()) return;
    const ctx = gsap.context(() => {
      gsap.from('[data-tessera]', { autoAlpha: 0, y: 26, duration: 0.8, ease: 'expo.out', stagger: 0.02, delay: 0.2, clearProps: 'opacity,visibility' });
    }, box);
    return () => ctx.revert();
  }, []);
  function apri(e, el, href) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 || ridotto()) return;
    e.preventDefault();
    const altre = [...box.current.querySelectorAll('[data-tessera]')].filter((t) => t !== el);
    gsap.timeline({ onComplete: () => router.push(href) })
      .to(altre, { autoAlpha: 0, scale: 0.94, duration: 0.28, ease: 'power2.in', stagger: 0.008 }, 0)
      .to(el, { scale: 1.06, duration: 0.42, ease: 'expo.out' }, 0);
  }
  const [cerca, setCerca] = useState('');
  const q = cerca.trim().toLowerCase();
  const passa = (f) => !q || f.nome.toLowerCase().includes(q) || f.dominio?.includes(q);
  const gruppi = GRUPPI.map(([k, titolo]) => [k, titolo, fonti.filter((f) => f.gruppo === k && passa(f))]).filter(([, , l]) => l.length);
  const yt = fonti.find((f) => f.chiave === 'youtube');
  const rassegna = fonti.find((f) => f.chiave === 'rassegna');
  const campione = fonti.filter((f) => ['corriere', 'elmundo', 'ilnapolista', 'runrunes'].includes(f.chiave));
  return (
    <div ref={box} style={{ display: 'flex', flexDirection: 'column', gap: 44 }}>
      <label className="cerca-fonti vetro">
        <Search size={18} aria-hidden="true" />
        <input type="search" value={cerca} onChange={(e) => setCerca(e.target.value)} placeholder={`Cerca tra ${fonti.filter((f) => f.dominio && f.chiave !== 'youtube').length} testate…`}
          aria-label="Cerca una testata" autoComplete="off" spellCheck={false} />
      </label>
      {gruppi.map(([k, titolo, lista]) => (
        <section key={k} aria-labelledby={`gruppo-${k}`} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <h2 id={`gruppo-${k}`} className="spaziato tenue" style={{ margin: 0 }}>{titolo} <span className="conta">{lista.length}</span></h2>
          <div className="griglia">{lista.map((f) => <Tessera key={f.chiave} f={f} onApri={apri} />)}</div>
        </section>
      ))}
      {q && !gruppi.length && <p className="tenue">Nessuna testata con «{cerca.trim()}».</p>}
      {!q && (
        <section aria-labelledby="insieme" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <h2 id="insieme" className="spaziato tenue" style={{ margin: 0 }}>Più testate insieme</h2>
          <div className="griglia">
            <Tessera f={rassegna} onApri={apri} href="/rassegna" largo>
              <span className="mazzo" aria-hidden="true">
                {campione.map((f) => <span key={f.chiave} className="placca"><LogoFonte chiave={f.chiave} nome={f.nome} area={1500} massimo={30} /></span>)}
              </span>
            </Tessera>
          </div>
        </section>
      )}
      {!q && (
        <section aria-labelledby="video" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <h2 id="video" className="spaziato tenue" style={{ margin: 0 }}>Video</h2>
          <div className="griglia"><Tessera f={yt} onApri={apri} /></div>
        </section>
      )}
    </div>
  );
}
