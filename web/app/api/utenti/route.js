import { NextResponse } from 'next/server';
import { supabaseServizio } from '@/lib/supabase-server';
import { soloDocente, RE_UUID } from '@/lib/docente-server';

// Elimina un account: file delle sue estrazioni, foto e utente. Il registro resta, con l'email.
export async function DELETE(request) {
  const { user, errore } = await soloDocente(request);
  if (errore) return errore;
  const { id } = await request.json().catch(() => ({}));
  if (!RE_UUID.test(String(id))) return NextResponse.json({ errore: 'richiesta non valida' }, { status: 400 });
  if (id === user.id) return NextResponse.json({ errore: 'Non puoi eliminare il tuo account' }, { status: 400 });

  const sb = supabaseServizio();
  const { data: attive } = await sb.from('estrazioni').select('id').eq('utente', id).in('stato', ['avviata', 'in_corso']);
  if (attive?.length) {
    await sb.from('estrazioni').update({ richiesta: 'ferma' }).in('id', attive.map((a) => a.id));
    return NextResponse.json({ errore: "L'utente ha estrazioni in corso: le ho fermate, riprova tra un minuto." }, { status: 409 });
  }
  const { data: file } = await sb.from('estrazione_file').select('percorso, estrazioni!inner(utente)').eq('estrazioni.utente', id);
  if (file?.length) await sb.storage.from('estrazioni').remove(file.map((f) => f.percorso));
  const { data: foto } = await sb.storage.from('foto').list(id);
  if (foto?.length) await sb.storage.from('foto').remove(foto.map((f) => `${id}/${f.name}`));
  await sb.from('estrazioni').update({ stato: 'annullata', conclusa_il: new Date().toISOString() }).eq('utente', id).eq('stato', 'in_coda');
  if (file?.length) {
    const { data: righe } = await sb.from('estrazioni').select('id').eq('utente', id);
    await sb.from('estrazione_file').delete().in('estrazione_id', righe.map((r) => r.id));
  }
  const { error } = await sb.auth.admin.deleteUser(id);
  if (error) return NextResponse.json({ errore: 'Eliminazione non riuscita' }, { status: 502 });
  return NextResponse.json({ eliminato: true });
}
