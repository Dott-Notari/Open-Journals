import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase-server';

// Arrivo dal link di conferma o dal ritorno di Google: flusso PKCE (code) o link con token_hash.
export async function GET(request) {
  const url = new URL(request.url);
  // Google ha risposto con un errore (es. il trigger rifiuta un dominio non ammesso)
  const descrizione = url.searchParams.get('error_description') || url.searchParams.get('error');
  if (descrizione) {
    const tipo = /chiuse/i.test(descrizione) ? 'chiuse' : /Database error|istituzionale/i.test(descrizione) ? 'dominio' : 'errore';
    return NextResponse.redirect(new URL(`/accesso?errore=${tipo}`, url.origin));
  }
  const sb = await supabaseServer();
  const code = url.searchParams.get('code');
  const tokenHash = url.searchParams.get('token_hash');
  const { error } = code
    ? await sb.auth.exchangeCodeForSession(code)
    : tokenHash ? await sb.auth.verifyOtp({ token_hash: tokenHash, type: url.searchParams.get('type') || 'email' })
      : { error: true };
  return NextResponse.redirect(new URL(error ? '/accesso?errore=errore' : '/', url.origin));
}
