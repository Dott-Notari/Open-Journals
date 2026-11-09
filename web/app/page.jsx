import GrigliaFonti from '@/components/GrigliaFonti';
import Ingresso from '@/components/Ingresso';
import Rassegna from '@/components/Rassegna';
import Contatore from '@/components/Contatore';
import Piede from '@/components/Piede';
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
          <h1 className="titolo">
            <span className="maschera"><span>Open</span></span>
            <span className="maschera"><span className="tenue" style={{ fontStyle: 'italic', fontWeight: 400 }}>Journals</span></span>
          </h1>
          <div className="riga" data-segue="" style={{ gap: 14 }}>
            <img src="/loghi/unisa.webp" alt="" width={44} height={44} />
            <span>Università degli Studi di Salerno<br /><span className="tenue">Sociologia della comunicazione interculturale</span></span>
          </div>
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
