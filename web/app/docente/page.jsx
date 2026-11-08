import Docente from '@/components/Docente';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = { title: 'Area docente' };

export default async function PaginaDocente() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const { data: p } = await sb.from('profiles').select('ruolo,approvato').eq('id', user.id).single();
  const docente = p?.ruolo === 'docente' && p.approvato;
  return (
    <main id="contenuto" className="pagina" style={{ gap: 24 }}>
      <h1 className="titolo-2" style={{ fontSize: 'clamp(2.2rem, 5vw, 3.4rem)' }}>Area docente</h1>
      {docente ? <Docente /> : <p className="avviso giallo">Questa sezione è riservata al docente.</p>}
    </main>
  );
}
