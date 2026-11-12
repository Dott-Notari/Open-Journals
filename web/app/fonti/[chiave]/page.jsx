import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ChevronLeft, Laptop } from 'lucide-react';
import LogoFonte from '@/components/LogoFonte';
import Rivela from '@/components/Rivela';
import Info from '@/components/Info';
import ModuloTestata from '@/components/ModuloTestata';
import ModuloYouTube from '@/components/ModuloYouTube';
import { trovaFonte, statoFonte } from '@/lib/fonti';
import { supabaseServer } from '@/lib/supabase-server';

export async function generateMetadata({ params }) {
  const f = trovaFonte((await params).chiave);
  return { title: f?.nome };
}

export default async function PaginaFonte({ params }) {
  const { chiave } = await params;
  const fonte = trovaFonte(chiave);
  if (!fonte) notFound();
  const sb = await supabaseServer();
  const [{ data: st }, { data: imp }] = await Promise.all([
    sb.from('stato_testate').select('attiva,disponibile_online,esito_collaudo').eq('chiave', chiave).single(),
    sb.from('impostazioni').select('ansa_estrazioni_attive,yt_max_durata_minuti').single(),
  ]);
  const disponibile = !!(st?.attiva && st?.disponibile_online) && !(chiave === 'ansa' && !imp?.ansa_estrazioni_attive);
  const s = statoFonte({ disponibile, esito: st?.esito_collaudo ?? 'mai' });
  const video = chiave === 'youtube';

  return (
    <main id="contenuto" className="pagina" style={{ maxWidth: 920, gap: 28 }}>
      <Rivela style={{ display: 'flex', flexDirection: 'column', gap: 26 }}>
        <Link href="/" className="pulsante compatto secondario" style={{ alignSelf: 'flex-start' }} data-sale="">
          <ChevronLeft size={18} aria-hidden="true" />Fonti
        </Link>
        <div className="riga" style={{ gap: 22 }}>
          <div data-placca="" className="vetro" style={{ padding: 10 }}>
            <div style={{ width: 200, height: 112, borderRadius: 16, background: 'var(--carta-logo)', display: 'grid', placeItems: 'center', padding: 16 }}>
              <LogoFonte chiave={fonte.chiave} nome={fonte.nome} area={5200} massimo={72} />
            </div>
          </div>
          <div data-sale="" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <h1 className="titolo-2" translate="no">{video ? 'Video da YouTube' : fonte.nome}</h1>
            <span className="riga" style={{ gap: 4 }}>
              <span className="stato" style={{ '--c': s.colore }}>{s.testo}</span>
              <Info etichetta="Copertura della fonte">{video
                ? `Il testo arriva dai sottotitoli o dalla trascrizione con Whisper. Le dirette e i video più lunghi di ${imp?.yt_max_durata_minuti ?? 35} minuti vengono saltati.`
                : `${fonte.nota} Gli articoli per abbonati vengono presi comunque e segnalati nella scheda.`}</Info>
            </span>
          </div>
        </div>
        <div data-sale="">
          {!disponibile ? (
            <div className="vetro riga" style={{ padding: 24, alignItems: 'flex-start', gap: 14, flexWrap: 'nowrap' }}>
              <Laptop size={24} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
              <p>Per ora {fonte.nome} si scarica solo con lo scraper del corso installato sul computer.</p>
            </div>
          ) : video ? <ModuloYouTube /> : <ModuloTestata fonte={fonte} />}
        </div>
      </Rivela>
    </main>
  );
}
