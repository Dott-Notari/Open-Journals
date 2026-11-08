'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Newspaper, Archive, ShieldCheck, LogOut } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import LogoFonte from './LogoFonte';

export default function Nav({ docente }) {
  const percorso = usePathname();
  const router = useRouter();
  const voci = [
    { href: '/', etichetta: 'Fonti', Icona: Newspaper, attiva: percorso === '/' || percorso.startsWith('/fonti') },
    { href: '/estrazioni', etichetta: 'Le mie estrazioni', Icona: Archive, attiva: percorso.startsWith('/estrazioni') },
    ...(docente ? [{ href: '/docente', etichetta: 'Area docente', Icona: ShieldCheck, attiva: percorso.startsWith('/docente') }] : []),
  ];
  async function esci() {
    await supabase().auth.signOut();
    router.replace('/accesso');
    router.refresh();
  }
  return (
    <header className="nav vetro">
      <Link href="/" aria-label="Scraper didattico delle testate, home" style={{ display: 'flex', alignItems: 'center', minHeight: 44 }}>
        <LogoFonte chiave="unisa" nome="Università degli Studi di Salerno" altezza={36} />
      </Link>
      <nav aria-label="Navigazione principale" className="nav-voci">
        {voci.map(({ href, etichetta, Icona, attiva }) => (
          <Link key={href} href={href} className="nav-voce" aria-current={attiva ? 'page' : undefined} aria-label={etichetta}>
            <Icona size={18} aria-hidden="true" /><span>{etichetta}</span>
          </Link>
        ))}
        <button type="button" className="nav-voce" onClick={esci} aria-label="Esci">
          <LogOut size={18} aria-hidden="true" /><span>Esci</span>
        </button>
      </nav>
    </header>
  );
}
