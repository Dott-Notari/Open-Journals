import GrigliaFonti from '@/components/GrigliaFonti';
import Ingresso from '@/components/Ingresso';
import Rassegna from '@/components/Rassegna';
import Contatore from '@/components/Contatore';
import Piede from '@/components/Piede';
import { Completo } from '@/components/Logo';
import { FONTI } from '@/lib/fonti';
import { supabaseServer } from '@/lib/supabase-server';

export default async function Home() {
  const sb = await supabaseServer();
  const [{ data: stati }, { data: numeri }] = await Promise.all([
    sb.from('stato_testate').select('chiave,attiva,disponibile_online,esito_collaudo'),
    sb.rpc('statistiche').single(),
  ]);
  const mappa = Object.fromEntries((stati || []).map((s) => [s.chiave, s]));
  const fonti = FONTI.map((f) => ({
    ...f, disponibile: !!(mappa[f.chiave]?.attiva && mappa[f.chiave]?.disponibile_online), esito: mappa[f.chiave]?.esito_collaudo ?? 'mai',
  }));
  return (
    <>
      <main id="contenuto" className="pagina">
        <Ingresso style={{ display: 'flex', flexDirection: 'column', gap: 26, paddingTop: 36 }}>
          <h1 data-logo="" style={{ margin: 0 }}><Completo className="logo-hero" /></h1>
          <p className="spaziato tenue" data-segue="">Sociologia della comunicazione interculturale</p>
          {numeri && (
            <div className="cifre" data-segue="">
              <span className="cifra"><Contatore valore={numeri.articoli} /><span className="tenue">articoli</span></span>
              <span className="cifra"><Contatore valore={numeri.video} /><span className="tenue">video</span></span>
              <span className="cifra"><Contatore valore={numeri.estrazioni} /><span className="tenue">estrazioni</span></span>
            </div>
          )}
          <div data-segue=""><Rassegna /></div>
        </Ingresso>
        <GrigliaFonti fonti={fonti} />
      </main>
      <Piede />
    </>
  );
}
