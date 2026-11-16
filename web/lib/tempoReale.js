'use client';
import { useEffect } from 'react';
import { supabase } from './supabase';

// Ricarica i dati quando una riga di «estrazioni» cambia (Supabase Realtime, con le regole RLS).
// Il controllo periodico resta come rete di sicurezza se la connessione in tempo reale cade.
export function useEstrazioniInTempoReale(ricarica, { filtro, ogni = 20000 } = {}) {
  useEffect(() => {
    let attesa;
    const presto = () => { clearTimeout(attesa); attesa = setTimeout(ricarica, 400); };
    const canale = supabase().channel(`estrazioni-${filtro ?? 'tutte'}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'estrazioni', ...(filtro ? { filter: filtro } : {}) }, presto)
      .subscribe();
    const t = setInterval(() => document.visibilityState === 'visible' && ricarica(), ogni);
    const visibile = () => document.visibilityState === 'visible' && ricarica();
    document.addEventListener('visibilitychange', visibile);
    return () => { supabase().removeChannel(canale); clearInterval(t); clearTimeout(attesa); document.removeEventListener('visibilitychange', visibile); };
  }, [ricarica, filtro, ogni]);
}
