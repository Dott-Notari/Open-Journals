import GrigliaFonti from '@/components/GrigliaFonti';
import Entrata from '@/components/Entrata';
import Pie from '@/components/Pie';
import { FONTI } from '@/lib/fonti';
import { supabaseServer } from '@/lib/supabase-server';

export default async function Home() {
  const sb = await supabaseServer();
  const { data: stati } = await sb.from('stato_testate').select('chiave,attiva,disponibile_online,esito_collaudo');
  const mappa = Object.fromEntries((stati || []).map((s) => [s.chiave, s]));
  const fonti = FONTI.map((f) => ({
    ...f, disponibile: !!(mappa[f.chiave]?.attiva && mappa[f.chiave]?.disponibile_online), esito: mappa[f.chiave]?.esito_collaudo ?? 'mai',
  }));
  return (
    <>
      <main id="contenuto" className="pagina">
        <Entrata style={{ display: 'flex', flexDirection: 'column', gap: 20, paddingTop: 24 }}>
          <h1 className="titolo">Dai giornali<br />al corpus.</h1>
          <p className="sottotitolo">
            Scegli una fonte, indica periodo e parole chiave, avvia l'estrazione. Ricevi articoli o video con trascrizioni
            in Word, testo, Excel e T-LAB, insieme alla scheda che documenta come è stato costruito il corpus.
          </p>
          <p className="tenue" style={{ margin: 0 }}>Responsabili scientifici: Vincenzo Esposito e Francesco Notari</p>
        </Entrata>
        <section aria-labelledby="scegli" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="riga" style={{ justifyContent: 'space-between', alignItems: 'baseline' }}>
            <h2 id="scegli" className="titolo-2">Scegli la fonte</h2>
            <span className="tenue">Una estrazione alla volta per fonte, le altre attendono in coda.</span>
          </div>
          <GrigliaFonti fonti={fonti} />
        </section>
      </main>
      <Pie />
    </>
  );
}
