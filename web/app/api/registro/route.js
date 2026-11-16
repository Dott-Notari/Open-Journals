import { NextResponse } from 'next/server';
import { supabaseServizio } from '@/lib/supabase-server';
import { soloDocente, RE_UUID } from '@/lib/docente-server';

const CONCLUSE = ['completata', 'interrotta', 'errore', 'annullata'];

// Cancella voci del registro (solo estrazioni concluse) insieme ai loro file.
// Corpo: { ids: [...] } oppure { tutte: true } per tutte le concluse.
export async function POST(request) {
  const { errore } = await soloDocente(request);
  if (errore) return errore;
  const corpo = await request.json().catch(() => ({}));
  const ids = Array.isArray(corpo.ids) ? corpo.ids.filter((x) => RE_UUID.test(String(x))).slice(0, 1000) : [];
  if (!corpo.tutte && !ids.length) return NextResponse.json({ errore: 'richiesta non valida' }, { status: 400 });

  const sb = supabaseServizio();
  let q = sb.from('estrazioni').select('id, estrazione_file(percorso)').in('stato', CONCLUSE).limit(5000);
  if (!corpo.tutte) q = q.in('id', ids);
  const { data: righe, error } = await q;
  if (error) return NextResponse.json({ errore: 'lettura non riuscita' }, { status: 502 });
  const percorsi = righe.flatMap((r) => r.estrazione_file.map((f) => f.percorso));
  for (let i = 0; i < percorsi.length; i += 100) await sb.storage.from('estrazioni').remove(percorsi.slice(i, i + 100));
  const rid = righe.map((r) => r.id);
  // le riprese che puntano a queste righe perdono solo il collegamento (on delete set null)
  for (let i = 0; i < rid.length; i += 200) await sb.from('estrazioni').delete().in('id', rid.slice(i, i + 200));
  return NextResponse.json({ cancellate: rid.length, saltate: corpo.tutte ? 0 : ids.length - rid.length });
}
