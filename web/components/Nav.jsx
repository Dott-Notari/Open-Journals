'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Newspaper, Archive, ShieldCheck, LogOut, Sun, Moon, MonitorSmartphone, Pause, Play } from 'lucide-react';
import { supabase } from '@/lib/supabase';

const TEMI = { sistema: ['Tema di sistema', MonitorSmartphone], chiaro: ['Tema chiaro', Sun], scuro: ['Tema scuro', Moon] };
const PROSSIMO = { sistema: 'chiaro', chiaro: 'scuro', scuro: 'sistema' };

export function Controlli() {
  const [tema, setTema] = useState('sistema');
  const [pausa, setPausa] = useState(false);
  useEffect(() => {
    setTema(document.documentElement.dataset.tema || 'sistema');
    setPausa(document.documentElement.hasAttribute('data-pausa'));
  }, []);
  function cambiaTema() {
    const t = PROSSIMO[tema];
    setTema(t);
    try { t === 'sistema' ? localStorage.removeItem('st.tema') : localStorage.setItem('st.tema', t); } catch {}
    if (t === 'sistema') delete document.documentElement.dataset.tema; else document.documentElement.dataset.tema = t;
  }
  function cambiaPausa() {
    const p = !pausa;
    setPausa(p);
    try { p ? localStorage.setItem('st.pausa', '1') : localStorage.removeItem('st.pausa'); } catch {}
    document.documentElement.toggleAttribute('data-pausa', p);
  }
  const [nomeTema, IconaTema] = TEMI[tema];
  return (
    <>
      <button type="button" className="voce icona" onClick={cambiaPausa} aria-label={pausa ? 'Riprendi le animazioni' : 'Ferma le animazioni'} title={pausa ? 'Riprendi le animazioni' : 'Ferma le animazioni'} aria-pressed={pausa}>
        {pausa ? <Play size={18} aria-hidden="true" /> : <Pause size={18} aria-hidden="true" />}
      </button>
      <button type="button" className="voce icona" onClick={cambiaTema} aria-label={`${nomeTema}: cambia`} title={nomeTema}>
        <IconaTema size={18} aria-hidden="true" />
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
          <img src="/loghi/unisa.webp" alt="" width={36} height={36} />
          <span>Scraper delle testate</span>
        </Link>
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
