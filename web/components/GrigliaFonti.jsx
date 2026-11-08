'use client';
import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { PlayCircle } from 'lucide-react';
import LogoFonte from './LogoFonte';
import { seguiLuce } from './Riflesso';
import { statoFonte } from '@/lib/fonti';

export default function GrigliaFonti({ fonti }) {
  const griglia = useRef(null);
  const router = useRouter();
  const ridotto = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    if (ridotto()) return;
    const ctx = gsap.context(() => {
      gsap.from('.tessera', { autoAlpha: 0, y: 18, duration: 0.6, ease: 'expo.out', stagger: 0.03 });
    }, griglia);
    return () => ctx.revert();
  }, []);

  function apri(e, href) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 || ridotto()) return; // nuova scheda: comportamento normale
    e.preventDefault();
    const scelta = e.currentTarget;
    const altre = [...griglia.current.querySelectorAll('.tessera')].filter((t) => t !== scelta);
    gsap.timeline({ onComplete: () => router.push(href) })
      .to(altre, { autoAlpha: 0.25, scale: 0.96, duration: 0.3, ease: 'power2.out' }, 0)
      .to(scelta, { scale: 1.06, y: -6, duration: 0.35, ease: 'expo.out' }, 0);
  }

  return (
    <div className="griglia" ref={griglia}>
      {fonti.map((f) => {
        const s = statoFonte(f);
        const yt = f.chiave === 'youtube';
        return (
          <Link key={f.chiave} href={`/fonti/${f.chiave}`} className={`tessera vetro riflesso${yt ? ' larga' : ''}`}
            onPointerMove={seguiLuce} onClick={(e) => apri(e, `/fonti/${f.chiave}`)}
            aria-label={`Apri lo scraper di ${f.nome}, ${s.testo.toLowerCase()}`}>
            <span className="tessera-logo">
              {yt ? (
                <span className="riga" style={{ gap: 18 }}>
                  <LogoFonte chiave={f.chiave} nome={f.nome} altezza={44} />
                  <span className="tenue piccolo" style={{ maxWidth: 220, textAlign: 'left' }}>
                    Video, playlist e canali: trascrizioni, video mp4 e audio mp3
                  </span>
                </span>
              ) : <LogoFonte chiave={f.chiave} nome={f.nome} />}
            </span>
            <span className="tessera-piede">
              <span style={{ fontWeight: 650, fontSize: '0.95rem' }} translate="no">{f.nome}</span>
              {yt ? <PlayCircle size={20} aria-hidden="true" color="var(--segnale)" />
                : <span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>}
            </span>
          </Link>
        );
      })}
    </div>
  );
}
