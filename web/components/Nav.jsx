'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Newspaper, Archive, ShieldCheck, LogOut, Pause, Play } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import Orologio from './Orologio';
import { Simbolo, Orizzontale } from './Logo';


export function Controlli() {
  const [scuro, setScuro] = useState(false);
  const [pausa, setPausa] = useState(false);
  useEffect(() => {
    const d = document.documentElement.dataset.tema;
    setScuro(d ? d === 'scuro' : matchMedia('(prefers-color-scheme: dark)').matches);
    setPausa(document.documentElement.hasAttribute('data-pausa'));
  }, []);
  // l'interruttore del logo: la pallina scorre e i colori si invertono, come nel marchio
  function cambiaTema() {
    const t = scuro ? 'chiaro' : 'scuro';
    setScuro(!scuro);
    try { localStorage.setItem('st.tema', t); } catch {}
    document.documentElement.dataset.tema = t;
  }
  function cambiaPausa() {
    const p = !pausa;
    setPausa(p);
    try { p ? localStorage.setItem('st.pausa', '1') : localStorage.removeItem('st.pausa'); } catch {}
    document.documentElement.toggleAttribute('data-pausa', p);
  }
  return (
    <>
      <button type="button" className="voce icona" onClick={cambiaPausa} aria-label={pausa ? 'Riprendi le animazioni' : 'Ferma le animazioni'} title={pausa ? 'Riprendi le animazioni' : 'Ferma le animazioni'} aria-pressed={pausa}>
        {pausa ? <Play size={18} aria-hidden="true" /> : <Pause size={18} aria-hidden="true" />}
      </button>
      <button type="button" className="interruttore-tema" onClick={cambiaTema} aria-pressed={scuro} aria-label="Tema scuro" title={scuro ? 'Passa al tema chiaro' : 'Passa al tema scuro'}>
        <Simbolo titolo="" aria-hidden="true" />
      </button>
    </>
  );
}

export default function Nav({ docente }) {
  const percorso = usePathname();
  const router = useRouter();
  useEffect(() => {
    const segna = () => document.documentElement.toggleAttribute('data-scorre', scrollY > 8);
    segna();
    addEventListener('scroll', segna, { passive: true });
    return () => removeEventListener('scroll', segna);
  }, []);
  const voci = [
    { href: '/', testo: 'Fonti', Icona: Newspaper, attiva: percorso === '/' || percorso.startsWith('/fonti') },
    { href: '/estrazioni', testo: 'Estrazioni', Icona: Archive, attiva: percorso.startsWith('/estrazioni') },
    ...(docente ? [{ href: '/docente', testo: 'Gestione', Icona: ShieldCheck, attiva: percorso.startsWith('/docente') }] : []),
  ];
  async function esci() {
    await supabase().auth.signOut();
    router.replace('/accesso');
    router.refresh();
  }
  return (
    <header className="testata">
      <div className="testata-barra vetro">
        <Link href="/" className="marchio">
          <Orizzontale titolo="Open New Media, pagina iniziale" />
        </Link>
        <Orologio />
        <nav aria-label="Principale" className="voci">
          {voci.map(({ href, testo, Icona, attiva }) => (
            <Link key={href} href={href} className="voce" aria-current={attiva ? 'page' : undefined}>
              <Icona size={18} aria-hidden="true" /><span className="etichetta">{testo}</span>
            </Link>
          ))}
          <Controlli />
          <button type="button" className="voce icona" onClick={esci} aria-label="Esci" title="Esci"><LogOut size={18} aria-hidden="true" /></button>
        </nav>
      </div>
    </header>
  );
}
