import { NextResponse } from 'next/server';
import { supabaseServer, supabaseServizio } from '@/lib/supabase-server';

const CONCLUSE = ['completata', 'interrotta', 'errore', 'annullata'];
const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

// Svuota una estrazione conclusa dello studente, oppure tutte ({ id: 'tutte' }):
// cancella i file dallo storage e la nasconde dalla sua pagina. Il registro del docente resta.
export async function POST(request) {
  const origine = request.headers.get('origin');
  if (origine && new URL(origine).host !== request.headers.get('host')) {
    return NextResponse.json({ errore: 'origine non ammessa' }, { status: 403 });
  }
  const { id } = await request.json().catch(() => ({}));
  if (id !== 'tutte' && !RE_UUID.test(String(id))) return NextResponse.json({ errore: 'richiesta non valida' }, { status: 400 });

  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ errore: 'accesso richiesto' }, { status: 401 });

  // la selezione passa dalle regole RLS: solo righe dell'utente, solo concluse
  let q = sb.from('estrazioni').select('id, estrazione_file(percorso)').eq('utente', user.id).eq('nascosta', false).in('stato', CONCLUSE);
  if (id !== 'tutte') q = q.eq('id', id);
  const { data: righe, error } = await q;
  if (error) return NextResponse.json({ errore: 'lettura non riuscita' }, { status: 502 });
  if (!righe.length) return NextResponse.json({ svuotate: 0 });

  const servizio = supabaseServizio();
  const percorsi = righe.flatMap((r) => r.estrazione_file.map((f) => f.percorso));
  const ids = righe.map((r) => r.id);
  if (percorsi.length) {
    const { error: e1 } = await servizio.storage.from('estrazioni').remove(percorsi);
    if (e1) return NextResponse.json({ errore: 'cancellazione dei file non riuscita' }, { status: 502 });
  }
  await servizio.from('estrazione_file').delete().in('estrazione_id', ids);
  await servizio.from('estrazioni').update({ nascosta: true, file_cancellati_il: new Date().toISOString() }).in('id', ids);
  return NextResponse.json({ svuotate: ids.length });
}
