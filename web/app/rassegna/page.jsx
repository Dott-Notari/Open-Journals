import Link from 'next/link';
import { ChevronLeft, Newspaper } from 'lucide-react';
import Rivela from '@/components/Rivela';
import Info from '@/components/Info';
import ModuloRassegna from '@/components/ModuloRassegna';
import { TESTATE } from '@/lib/fonti';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = { title: 'Rassegna stampa' };

export default async function PaginaRassegna({ searchParams }) {
  const { testate: scelte = '' } = await searchParams;
  const sb = await supabaseServer();
  const [{ data: stati }, { data: imp }] = await Promise.all([
    sb.from('stato_testate').select('chiave,attiva,disponibile_online'),
    sb.from('impostazioni').select('ansa_estrazioni_attive,tempo_max_minuti').single(),
  ]);
  const mappa = Object.fromEntries((stati || []).map((s) => [s.chiave, !!(s.attiva && s.disponibile_online)]));
  const testate = TESTATE.map((f) => ({ ...f, disponibile: !!mappa[f.chiave] && !(f.chiave === 'ansa' && !imp?.ansa_estrazioni_attive) }));
  const iniziali = String(scelte).split(',').filter((k) => testate.some((f) => f.chiave === k && f.disponibile));
  const minuti = imp?.tempo_max_minuti ?? 330;

  return (
    <main id="contenuto" className="pagina" style={{ maxWidth: 920, gap: 28 }}>
      <Rivela style={{ display: 'flex', flexDirection: 'column', gap: 26 }}>
        <Link href="/" className="pulsante compatto secondario" style={{ alignSelf: 'flex-start' }} data-sale="">
          <ChevronLeft size={18} aria-hidden="true" />Fonti
        </Link>
        <div className="riga" style={{ gap: 22 }}>
          <div data-placca="" className="vetro" style={{ padding: 10 }}>
            <div style={{ width: 112, height: 112, borderRadius: 16, background: 'var(--carta-logo)', display: 'grid', placeItems: 'center', color: '#111' }}>
              <Newspaper size={46} strokeWidth={1.6} aria-hidden="true" />
            </div>
          </div>
          <div data-sale="" style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 560 }}>
            <h1 className="titolo-2">Rassegna stampa</h1>
            <span className="riga" style={{ gap: 4 }}>
              <span className="tenue">La stessa ricerca, per periodo, su più testate. Un solo archivio.</span>
              <Info etichetta="Come funziona la rassegna">
                {`Ogni testata viene letta con il suo metodo e ha la sua copertura: un archivio completo, le sitemap o solo gli ultimi giorni. L'esito di ciascuna, con il numero di articoli e i problemi incontrati, è nel file scheda_rassegna.txt dentro lo zip. Il limite di ${minuti} minuti vale per l'intera rassegna, non per ogni testata.`}
              </Info>
            </span>
          </div>
        </div>
        <div data-sale="">
          {!mappa.rassegna ? (
            <div className="vetro" style={{ padding: 24 }}><p>La rassegna stampa al momento è sospesa dal docente. Puoi sempre fare un&apos;estrazione per ogni testata.</p></div>
          ) : <ModuloRassegna testate={testate} iniziali={iniziali} minuti={minuti} />}
        </div>
      </Rivela>
    </main>
  );
}
