import { NextResponse } from 'next/server';
import { supabaseServer, supabaseServizio } from '@/lib/supabase-server';

// Controlli per il docente: variabili d'ambiente, accesso a Supabase con la chiave segreta,
// token e repository di GitHub. Non restituisce mai i valori delle chiavi.
export async function GET() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ errore: 'accesso richiesto' }, { status: 401 });
  const { data: p } = await sb.from('profiles').select('ruolo,approvato').eq('id', user.id).single();
  if (p?.ruolo !== 'docente' || !p.approvato) return NextResponse.json({ errore: 'riservato al docente' }, { status: 403 });

  const esiti = [];
  const voce = (nome, ok, testo) => esiti.push({ nome, ok, testo });
  const mancanti = ['SUPABASE_SERVICE_ROLE_KEY', 'GITHUB_TOKEN', 'GITHUB_REPOSITORY'].filter((k) => !process.env[k]);
  voce('Variabili su Vercel', !mancanti.length, mancanti.length ? `Mancano: ${mancanti.join(', ')}` : 'Presenti');

  const { error } = await supabaseServizio().from('impostazioni').select('id').single();
  voce('Chiave segreta di Supabase', !error, error ? 'Rifiutata: controlla SUPABASE_SERVICE_ROLE_KEY' : 'Funziona');

  const repo = process.env.GITHUB_REPOSITORY || '';
  if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) {
    voce('Repository GitHub', false, 'GITHUB_REPOSITORY deve avere la forma utente/nome-repository');
  } else {
    const r = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/estrazione.yml`, {
      headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
    });
    const testi = {
      200: 'Il token vede il workflow Estrazione. Deve avere anche il permesso Actions in scrittura.',
      401: 'Token non valido o scaduto: creane uno nuovo e aggiornalo su Vercel',
      403: 'Il token non ha accesso: serve il permesso Actions sul repository',
      404: 'Repository o workflow non trovati: controlla GITHUB_REPOSITORY e che estrazione.yml sia in .github/workflows',
    };
    voce('Token e workflow di GitHub', r.status === 200, testi[r.status] || `Risposta inattesa di GitHub (${r.status})`);
  }
  return NextResponse.json({ esiti });
}
