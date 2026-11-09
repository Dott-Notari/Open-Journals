'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LoaderCircle, MailCheck, ArrowRight } from 'lucide-react';
import Segmenti from './Segmenti';
import { Controlli } from './Nav';
import { supabase } from '@/lib/supabase';

const MESSAGGI = {
  'Invalid login credentials': 'Email o password non corretti.',
  'Email not confirmed': "Conferma prima l'indirizzo dal link ricevuto per email.",
  'Database error saving new user': 'Indirizzo non ammesso: usa la tua email istituzionale.',
  'User already registered': 'Questo indirizzo ha già un account.',
};

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
      setMsg({ tipo: 'errore', testo: MESSAGGI[error.message] || error.message });
    } else {
      const { error } = await sb.auth.signUp({
        email: d.get('email'), password: d.get('password'),
        options: { data: { nome: `${d.get('nome')} ${d.get('cognome')}`.trim() }, emailRedirectTo: `${location.origin}/auth/conferma` },
      });
      setMsg(error ? { tipo: 'errore', testo: MESSAGGI[error.message] || error.message }
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
