'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LogOut, Hourglass, PauseCircle } from 'lucide-react';
import { Controlli } from './Nav';
import Rassegna from './Rassegna';
import { supabase } from '@/lib/supabase';
import { Completo } from './Logo';

// Sala d'attesa: lo studente registrato aspetta l'approvazione; la pagina controlla da sola ogni 15 secondi.
export default function Attesa({ email, sospeso }) {
  const router = useRouter();
  useEffect(() => {
    const t = setInterval(async () => {
      const { data } = await supabase().from('profiles').select('approvato,sospeso').single();
      if (data?.approvato && !data.sospeso) router.refresh();
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
          <Completo style={{ '--onm-dx': '121.94px', height: 96 }} />
          <span className="voci"><Controlli /></span>
        </div>
        <h1 id="attesa" className="titolo-2">{sospeso ? 'Account sospeso' : 'Account in attesa'}</h1>
        <p className="riga" style={{ gap: 10, flexWrap: 'nowrap', alignItems: 'flex-start' }}>
          {sospeso ? <PauseCircle size={20} aria-hidden="true" style={{ flexShrink: 0, marginTop: 3 }} /> : <Hourglass size={20} aria-hidden="true" style={{ flexShrink: 0, marginTop: 3 }} />}
          <span>{sospeso
            ? 'Il docente ha sospeso il tuo account. Per chiarimenti scrivigli: quando lo riattiva, questa pagina si apre da sola.'
            : 'Quando il docente approva il tuo account, questa pagina si apre da sola sulla piattaforma.'}</span>
        </p>
        <p className="tenue piccolo" style={{ overflowWrap: 'anywhere' }}>Registrato come {email}</p>
        <button type="button" className="pulsante secondario compatto" onClick={esci}><LogOut size={18} aria-hidden="true" />Esci</button>
      </section>
      <div style={{ width: 'min(1100px, 100%)', margin: '0 auto' }}><Rassegna /></div>
    </main>
  );
}
