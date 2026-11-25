'use client';
import { useState } from 'react';
import '@fontsource/roboto/500.css';
import { supabase } from '@/lib/supabase';

// Pulsante «Accedi con Google» secondo le linee guida di Google Identity: logo G originale a colori,
// Roboto Medium 14/20, bordo #747775 su bianco (tema chiaro) e #8E918F su #131314 (tema scuro).
// Compare solo quando NEXT_PUBLIC_ACCESSO_GOOGLE=1, cioè dopo aver attivato il provider su Supabase.
export const googleAttivo = process.env.NEXT_PUBLIC_ACCESSO_GOOGLE === '1';

function G() {
  return (
    <svg viewBox="0 0 48 48" width="20" height="20" aria-hidden="true" style={{ display: 'block' }}>
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
  );
}

export default function AccessoGoogle({ testo = 'Accedi con Google', onErrore }) {
  const [attesa, setAttesa] = useState(false);
  async function vai() {
    setAttesa(true);
    const { error } = await supabase().auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/conferma`, queryParams: { prompt: 'select_account' } },
    });
    if (error) { setAttesa(false); onErrore?.('Accesso con Google non disponibile in questo momento: usa email e password.'); }
  }
  return (
    <button type="button" className="pulsante-google" onClick={vai} disabled={attesa} aria-busy={attesa || undefined}>
      <span className="pulsante-google-logo"><G /></span>
      <span>{attesa ? 'Apertura di Google…' : testo}</span>
    </button>
  );
}
