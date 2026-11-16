import Profilo from '@/components/Profilo';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = { title: 'Profilo' };

export default async function PaginaProfilo() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const [{ data: p }, { count }, { data: somma }] = await Promise.all([
    sb.from('profiles').select('nome,foto,registrato_il').eq('id', user.id).single(),
    sb.from('estrazioni').select('id', { count: 'exact', head: true }).eq('utente', user.id),
    sb.from('estrazioni').select('articoli').eq('utente', user.id).in('stato', ['completata', 'interrotta']),
  ]);
  const { data: firmato } = p?.foto ? await sb.storage.from('foto').createSignedUrl(p.foto, 3600) : { data: null };
  const articoli = (somma || []).reduce((t, r) => t + (r.articoli || 0), 0);
  const fmt = new Intl.NumberFormat('it-IT');
  return (
    <main id="contenuto" className="pagina" style={{ maxWidth: 760, gap: 24 }}>
      <h1 className="titolo-2">Profilo</h1>
      <div className="cifre">
        <span className="cifra"><b className="numeri">{fmt.format(count ?? 0)}</b><span className="tenue">estrazioni</span></span>
        <span className="cifra"><b className="numeri">{fmt.format(articoli)}</b><span className="tenue">elementi raccolti</span></span>
      </div>
      <Profilo id={user.id} email={user.email} nome={p?.nome} fotoPercorso={p?.foto} fotoUrl={firmato?.signedUrl ?? null} />
    </main>
  );
}
