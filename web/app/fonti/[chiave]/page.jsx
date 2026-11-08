import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ChevronLeft, TerminalSquare } from 'lucide-react';
import LogoFonte from '@/components/LogoFonte';
import Entrata from '@/components/Entrata';
import ModuloTestata from '@/components/ModuloTestata';
import ModuloYouTube from '@/components/ModuloYouTube';
import { trovaFonte, statoFonte } from '@/lib/fonti';
import { supabaseServer } from '@/lib/supabase-server';

export default async function PaginaFonte({ params }) {
  const { chiave } = await params;
  const fonte = trovaFonte(chiave);
  if (!fonte) notFound();
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const [{ data: st }, { data: imp }, { count }] = await Promise.all([
    sb.from('stato_testate').select('attiva,disponibile_online,esito_collaudo').eq('chiave', chiave).single(),
    sb.from('impostazioni').select('*').single(),
    sb.from('estrazioni').select('id', { count: 'exact', head: true }).eq('utente', user.id).in('stato', ['in_coda', 'avviata', 'in_corso']),
  ]);
  const disponibile = !!(st?.attiva && st?.disponibile_online) && !(chiave === 'ansa' && !imp?.ansa_estrazioni_attive);
  const s = statoFonte({ disponibile, esito: st?.esito_collaudo ?? 'mai' });
  const attive = `Estrazioni attive: ${count ?? 0} di ${imp?.max_attive_per_utente ?? 2}. Lo stato si aggiorna in Le mie estrazioni.`;

  return (
    <main id="contenuto" className="pagina" style={{ gap: 28 }}>
      <Entrata style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        <Link href="/" className="pulsante compatto secondario vetro" style={{ alignSelf: 'flex-start' }}>
          <ChevronLeft size={18} aria-hidden="true" />Tutte le fonti
        </Link>
        <div className="riga" style={{ gap: 22 }}>
          <div className="vetro" style={{ width: 188, height: 108, display: 'grid', placeItems: 'center', padding: 18 }}>
            <LogoFonte chiave={fonte.chiave} nome={fonte.nome} altezza={56} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <h1 className="titolo-2" style={{ fontSize: 'clamp(2.2rem, 5vw, 3.4rem)' }} translate="no">{fonte.nome}</h1>
            <span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>
          </div>
        </div>
        <p className="vetro" style={{ margin: 0, padding: '16px 20px', maxWidth: 820 }}>{fonte.nota}</p>
      </Entrata>
      {!disponibile ? (
        <div className="vetro" style={{ padding: 28, display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <TerminalSquare size={28} aria-hidden="true" color="var(--inchiostro)" style={{ flexShrink: 0 }} />
          <p style={{ margin: 0 }}>
            {fonte.nome} non risponde alle richieste dai server della piattaforma, oppure il docente l'ha sospesa.
            Per costruire questo corpus usa lo scraper locale del corso, che lavora con lo stesso motore e produce gli stessi file.
          </p>
        </div>
      ) : chiave === 'youtube' ? (
        <ModuloYouTube maxVideo={imp.yt_max_video} maxAltezza={imp.yt_max_altezza} maxDurata={imp.yt_max_durata_minuti} attive={attive} />
      ) : (
        <ModuloTestata fonte={fonte} tetto={imp.max_articoli_tetto} minuti={imp.tempo_max_minuti} attive={attive} />
      )}
    </main>
  );
}
