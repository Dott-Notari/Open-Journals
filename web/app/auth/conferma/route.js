import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase-server';

// Arrivo dal link di conferma: flusso PKCE (code) o link con token_hash.
export async function GET(request) {
  const url = new URL(request.url);
  const sb = await supabaseServer();
  const code = url.searchParams.get('code');
  const tokenHash = url.searchParams.get('token_hash');
  const { error } = code
    ? await sb.auth.exchangeCodeForSession(code)
    : tokenHash ? await sb.auth.verifyOtp({ token_hash: tokenHash, type: url.searchParams.get('type') || 'email' })
      : { error: true };
  return NextResponse.redirect(new URL(error ? '/accesso?conferma=errore' : '/', url.origin));
}
