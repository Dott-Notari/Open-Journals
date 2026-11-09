'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LoaderCircle, MailCheck, ArrowRight } from 'lucide-react';
import Segmenti from './Segmenti';
import { Controlli } from './Nav';
import { supabase } from '@/lib/supabase';

// Messaggi di Supabase Auth, per codice (più stabile del testo) e per testo.
const MESSAGGI = {
  invalid_credentials: 'Email o password non corretti.',
  email_not_confirmed: "Conferma prima l'indirizzo dal link ricevuto per email.",
  unexpected_failure: 'Indirizzo non ammesso: usa la tua email istituzionale.',
  user_already_exists: 'Questo indirizzo ha già un account: accedi.',
  email_exists: 'Questo indirizzo ha già un account: accedi.',
  over_email_send_rate_limit: "Troppe registrazioni in poco tempo: riprova più tardi o avvisa il docente.",
  email_address_not_authorized: "La piattaforma non riesce ancora a inviare email a questo indirizzo: avvisa il docente.",
  email_address_invalid: 'Indirizzo email non valido: controlla di averlo scritto bene.',
  validation_failed: 'Controlla email e password.',
  weak_password: 'Password troppo debole: usa almeno 10 caratteri.',
  over_request_rate_limit: 'Troppi tentativi: aspetta qualche minuto.',
  'Invalid login credentials': 'Email o password non corretti.',
  'Database error saving new user': 'Indirizzo non ammesso: usa la tua email istituzionale.',
};
const traduci = (e) => MESSAGGI[e.code] || MESSAGGI[e.message] || `Registrazione non riuscita (${e.code || e.message}): avvisa il docente.`;

export default function Accesso() {
  const router = useRouter();
  const [scheda, setScheda] = useState('accedi');
  const [attesa, setAttesa] = useState(false);
  const [msg, setMsg] = useState(null);

  async function invia(e) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    setAttesa(true); setMsg(null);
    const sb = supabase();
    if (scheda === 'accedi') {
      const { error } = await sb.auth.signInWithPassword({ email: d.get('email'), password: d.get('password') });
      if (!error) { router.replace('/'); router.refresh(); return; }
      setMsg({ tipo: 'errore', testo: traduci(error) });
    } else {
      const { data: reg, error } = await sb.auth.signUp({
        email: d.get('email'), password: d.get('password'),
        options: { data: { nome: `${d.get('nome')} ${d.get('cognome')}`.trim() }, emailRedirectTo: `${location.origin}/auth/conferma` },
      });
      if (!error && reg.session) { router.replace('/'); router.refresh(); return; } // conferma email disattivata
      setMsg(error ? { tipo: 'errore', testo: traduci(error) }
        : { tipo: 'blu', testo: "Ti abbiamo mandato un'email per confermare l'indirizzo. Dopo, il docente deve approvare l'account." });
    }
    setAttesa(false);
  }

  const registra = scheda === 'registrati';
  return (
    <form onSubmit={invia} className="modulo vetro" style={{ width: 'min(440px, 100%)' }}>
      <div className="riga" style={{ justifyContent: 'space-between' }}>
        <Segmenti voci={[['accedi', 'Accedi'], ['registrati', 'Registrati']]} valore={scheda} onCambio={(k) => { setScheda(k); setMsg(null); }} etichetta="Accesso o registrazione" />
        <span className="voci"><Controlli /></span>
      </div>
      {registra && (
        <div className="due" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <label className="etichetta">Nome<input className="campo" name="nome" autoComplete="given-name" required maxLength={60} /></label>
          <label className="etichetta">Cognome<input className="campo" name="cognome" autoComplete="family-name" required maxLength={60} /></label>
        </div>
      )}
      <label className="etichetta">Email
        <input className="campo" type="email" name="email" required autoComplete={registra ? 'email' : 'username'} spellCheck={false} inputMode="email" />
      </label>
      <label className="etichetta">Password
        <input className="campo" type="password" name="password" required minLength={registra ? 10 : undefined} autoComplete={registra ? 'new-password' : 'current-password'}
          placeholder={registra ? 'Almeno 10 caratteri' : undefined} />
      </label>
      <button type="submit" className="pulsante" disabled={attesa}>
        {attesa ? <LoaderCircle size={19} className="gira" aria-hidden="true" /> : null}
        {registra ? 'Crea account' : 'Entra'}{!attesa && <ArrowRight size={19} aria-hidden="true" />}
      </button>
      <div aria-live="polite">
        {msg && <p className={`avviso ${msg.tipo}`} style={{ display: 'flex', gap: 10 }}>
          {msg.tipo === 'blu' && <MailCheck size={20} aria-hidden="true" style={{ flexShrink: 0 }} />}{msg.testo}</p>}
      </div>
    </form>
  );
}
