'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LogOut, Hourglass } from 'lucide-react';
import { Controlli } from './Nav';
import Rassegna from './Rassegna';
import { supabase } from '@/lib/supabase';

// Sala d'attesa: lo studente registrato aspetta l'approvazione; la pagina controlla da sola ogni 15 secondi.
export default function Attesa({ email }) {
  const router = useRouter();
  useEffect(() => {
    const t = setInterval(async () => {
      const { data } = await supabase().from('profiles').select('approvato').single();
      if (data?.approvato) router.refresh();
    }, 15000);
    return () => clearInterval(t);
  }, [router]);
  async function esci() {
    await supabase().auth.signOut();
    router.replace('/accesso');
    router.refresh();
  }
  return (
    <main id="contenuto" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 40, padding: '48px 20px' }}>
      <section className="modulo vetro" style={{ width: 'min(560px, 100%)', margin: '0 auto', alignItems: 'flex-start' }} aria-labelledby="attesa">
        <div className="riga" style={{ justifyContent: 'space-between', width: '100%' }}>
          <img src="/loghi/unisa.webp" alt="Università degli Studi di Salerno" width={56} height={56} />
          <span className="voci"><Controlli /></span>
        </div>
        <h1 id="attesa" className="titolo-2">Open New Media</h1>
        <p className="riga" style={{ gap: 10, flexWrap: 'nowrap', alignItems: 'flex-start' }}>
          <Hourglass size={20} aria-hidden="true" style={{ flexShrink: 0, marginTop: 3 }} />
          <span>Il tuo account è in attesa di approvazione. Quando il docente lo approva, questa pagina si apre da sola sulla piattaforma.</span>
        </p>
        <p className="tenue piccolo" style={{ overflowWrap: 'anywhere' }}>Registrato come {email}</p>
        <button type="button" className="pulsante secondario compatto" onClick={esci}><LogOut size={18} aria-hidden="true" />Esci</button>
      </section>
      <div style={{ width: 'min(1100px, 100%)', margin: '0 auto' }}><Rassegna /></div>
    </main>
  );
}
