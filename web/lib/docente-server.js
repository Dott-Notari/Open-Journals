import { NextResponse } from 'next/server';
import { supabaseServer } from './supabase-server';

// Controlli comuni alle route del docente: stessa origine, sessione valida, ruolo docente attivo.
export async function soloDocente(request) {
  const origine = request.headers.get('origin');
  if (origine && new URL(origine).host !== request.headers.get('host')) {
    return { errore: NextResponse.json({ errore: 'origine non ammessa' }, { status: 403 }) };
  }
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return { errore: NextResponse.json({ errore: 'accesso richiesto' }, { status: 401 }) };
  const { data: p } = await sb.from('profiles').select('ruolo,approvato,sospeso').eq('id', user.id).single();
  if (p?.ruolo !== 'docente' || !p.approvato || p.sospeso) {
    return { errore: NextResponse.json({ errore: 'riservato al docente' }, { status: 403 }) };
  }
  return { user };
}

export const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
