'use client';
import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { ArrowUpRight } from 'lucide-react';
import LogoFonte from './LogoFonte';
import { statoFonte } from '@/lib/fonti';

const ridotto = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// Tessera di vetro che si inclina verso il puntatore: il logo, su una lastra chiara, resta in primo piano.
function Tessera({ f, onApri }) {
  const el = useRef(null);
  const giri = useRef(null);
  useEffect(() => {
    if (ridotto()) return;
    giri.current = { x: gsap.quickTo(el.current, 'rotationX', { duration: 0.5, ease: 'power3.out' }),
      y: gsap.quickTo(el.current, 'rotationY', { duration: 0.5, ease: 'power3.out' }) };
  }, []);
  function muovi(e) {
    const r = el.current.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width - 0.5, ny = (e.clientY - r.top) / r.height - 0.5;
    el.current.style.setProperty('--mx', `${(nx + 0.5) * 100}%`);
    el.current.style.setProperty('--my', `${(ny + 0.5) * 100}%`);
    giri.current?.x(-ny * 9); giri.current?.y(nx * 11);
  }
  const fuori = () => { giri.current?.x(0); giri.current?.y(0); };
  const s = statoFonte(f);
  const video = f.chiave === 'youtube';
  return (
    <Link ref={el} href={`/fonti/${f.chiave}`} className={`tessera vetro${video ? ' video' : ''}`} data-tessera=""
      onPointerMove={muovi} onPointerLeave={fuori} onClick={(e) => onApri(e, el.current, `/fonti/${f.chiave}`)}
      aria-label={`${f.nome}, ${s.testo.toLowerCase()}`}>
      <span className="faccia"><LogoFonte chiave={f.chiave} nome={f.nome} area={video ? 9000 : 3800} massimo={video ? 72 : 60} /></span>
      <span className="piede">
        {video ? (
          <>
            <span className="titolo-3">Video da YouTube</span>
            <span className="tenue">Trascrizioni, mp4 e mp3 da video, playlist, canali o ricerche</span>
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
      gsap.from('[data-tessera]', { autoAlpha: 0, y: 26, rotationX: -12, duration: 0.8, ease: 'expo.out', stagger: 0.02, delay: 0.2 });
    }, box);
    return () => ctx.revert();
  }, []);
  function apri(e, el, href) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 || ridotto()) return;
    e.preventDefault();
    const altre = [...box.current.querySelectorAll('[data-tessera]')].filter((t) => t !== el);
    gsap.timeline({ onComplete: () => router.push(href) })
      .to(altre, { autoAlpha: 0, scale: 0.94, duration: 0.28, ease: 'power2.in', stagger: 0.008 }, 0)
      .to(el, { scale: 1.08, rotationX: 0, rotationY: 0, z: 60, duration: 0.42, ease: 'expo.out' }, 0);
  }
  const testate = fonti.filter((f) => f.chiave !== 'youtube');
  const yt = fonti.find((f) => f.chiave === 'youtube');
  return (
    <div ref={box} style={{ display: 'flex', flexDirection: 'column', gap: 44 }}>
      <section aria-labelledby="testate" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <h2 id="testate" className="titolo-2">Testate</h2>
        <div className="griglia">{testate.map((f) => <Tessera key={f.chiave} f={f} onApri={apri} />)}</div>
      </section>
      <section aria-labelledby="video" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <h2 id="video" className="titolo-2">Video</h2>
        <div className="griglia"><Tessera f={yt} onApri={apri} /></div>
      </section>
    </div>
  );
}
