'use client';
import { supabase } from './supabase';

export const lista = (testo, sep = ',') => (testo || '').split(sep).map((s) => s.trim()).filter(Boolean);

// Registra la richiesta (il database la valida e applica quote e limiti) e chiede l'avvio della coda.
export async function inviaEstrazione(fonte, modalita, parametri) {
  const { error } = await supabase().from('estrazioni').insert({ fonte, modalita, parametri });
  if (error) return error.message;
  await fetch('/api/avvia', { method: 'POST' }).catch(() => {}); // se fallisce, la coda programmata la avvia entro 15 minuti
  return null;
}
