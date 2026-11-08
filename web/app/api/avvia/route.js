import { NextResponse } from 'next/server';
import { supabaseServer, supabaseServizio } from '@/lib/supabase-server';

// Assegna le estrazioni in coda (una per fonte libera) e avvia il workflow di GitHub per ciascuna.
// Non riceve parametri: le richieste sono già validate dal database al momento dell'inserimento.
export async function POST(request) {
  const origine = request.headers.get('origin');
  if (origine && new URL(origine).host !== request.headers.get('host')) {
    return NextResponse.json({ errore: 'origine non ammessa' }, { status: 403 });
  }
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ errore: 'accesso richiesto' }, { status: 401 });
  const { data: p } = await sb.from('profiles').select('approvato').eq('id', user.id).single();
  if (!p?.approvato) return NextResponse.json({ errore: 'account non approvato' }, { status: 403 });

  const { data: assegnate, error } = await supabaseServizio().rpc('assegna_estrazioni');
  if (error) return NextResponse.json({ errore: 'coda non disponibile' }, { status: 502 });

  let avviate = 0;
  for (const { id, fonte } of assegnate || []) {
    const r = await fetch(`https://api.github.com/repos/${process.env.GITHUB_REPOSITORY}/actions/workflows/estrazione.yml/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
      body: JSON.stringify({ ref: process.env.GITHUB_REF_NAME || 'main', inputs: { id, fonte } }),
    });
    if (r.ok) avviate += 1; // se fallisce, la riga torna in coda da sola e la riprende il controllo programmato
  }
  return NextResponse.json({ avviate });
}
