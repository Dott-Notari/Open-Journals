import Docente from '@/components/Docente';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = { title: 'Gestione' };

export default async function PaginaDocente() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const { data: p } = await sb.from('profiles').select('ruolo,approvato').eq('id', user.id).single();
  return (
    <main id="contenuto" className="pagina" style={{ gap: 24 }}>
      <h1 className="titolo-2">Gestione</h1>
      {p?.ruolo === 'docente' && p.approvato ? <Docente /> : <p className="avviso giallo">Sezione riservata al docente.</p>}
    </main>
  );
}
