'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogIn, UserPlus, LoaderCircle, MailCheck } from 'lucide-react';
import Segmenti from './Segmenti';
import { supabase } from '@/lib/supabase';

const MESSAGGI = {
  'Invalid login credentials': 'Email o password non corretti.',
  'Email not confirmed': "Conferma prima l'indirizzo dal link ricevuto per email.",
  'Database error saving new user': "Registrazione non consentita con questo indirizzo: usa l'email istituzionale o scrivi al docente.",
  'User already registered': 'Questo indirizzo ha già un account: accedi.',
};
const traduci = (m) => MESSAGGI[m] || m;

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
      setMsg({ tipo: 'errore', testo: traduci(error.message) });
    } else {
      const { error } = await sb.auth.signUp({
        email: d.get('email'), password: d.get('password'),
        options: { data: { nome: d.get('nome') }, emailRedirectTo: `${location.origin}/auth/conferma` },
      });
      setMsg(error ? { tipo: 'errore', testo: traduci(error.message) }
        : { tipo: 'blu', testo: "Controlla la posta e conferma l'indirizzo. Poi il docente approva l'account e potrai avviare le estrazioni." });
    }
    setAttesa(false);
  }

  const Icona = attesa ? LoaderCircle : scheda === 'accedi' ? LogIn : UserPlus;
  return (
    <form onSubmit={invia} className="modulo vetro" style={{ flex: '1 1 360px', maxWidth: 440 }}>
      <Segmenti voci={[['accedi', 'Accedi'], ['registrati', 'Registrati']]} valore={scheda} onCambio={(k) => { setScheda(k); setMsg(null); }} etichetta="Accesso o registrazione" />
      {scheda === 'registrati' && (
        <label className="etichetta">Nome e cognome<input className="campo" name="nome" autoComplete="name" required maxLength={120} /></label>
      )}
      <label className="etichetta">{scheda === 'accedi' ? 'Email' : 'Email istituzionale'}
        <input className="campo" type="email" name="email" required autoComplete={scheda === 'accedi' ? 'username' : 'email'} spellCheck={false} inputMode="email" />
      </label>
      <label className="etichetta">Password
        <input className="campo" type="password" name="password" required minLength={scheda === 'accedi' ? undefined : 10}
          autoComplete={scheda === 'accedi' ? 'current-password' : 'new-password'} />
        {scheda === 'registrati' && <span className="aiuto">Almeno 10 caratteri.</span>}
      </label>
      <button type="submit" className="pulsante" disabled={attesa}>
        <Icona size={20} aria-hidden="true" className={attesa ? 'gira' : undefined} />
        {attesa ? 'Attendi…' : scheda === 'accedi' ? 'Accedi' : "Crea l'account"}
      </button>
      <div aria-live="polite">
        {msg && <p className={`avviso ${msg.tipo}`} style={{ margin: 0, display: 'flex', gap: 10 }}>
          {msg.tipo === 'blu' && <MailCheck size={20} aria-hidden="true" style={{ flexShrink: 0 }} />}{msg.testo}</p>}
      </div>
    </form>
  );
}
