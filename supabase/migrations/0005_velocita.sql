-- =============================================================================
-- Aggiornamento 0005: più estrazioni contemporanee sulla stessa testata e pausa
-- tra le richieste regolabile dal docente. Si può rieseguire senza danni.
-- =============================================================================
alter table public.impostazioni add column if not exists parallele_per_fonte integer not null default 1
  check (parallele_per_fonte between 1 and 4);
alter table public.impostazioni add column if not exists pausa_secondi numeric(3, 1) not null default 2.0
  check (pausa_secondi between 1 and 5);
grant update (parallele_per_fonte, pausa_secondi) on public.impostazioni to authenticated;

-- assegna fino a «parallele_per_fonte» estrazioni per fonte
create or replace function public.assegna_estrazioni() returns table (id uuid, fonte text)
language plpgsql security definer set search_path = '' as $$
declare
  imp public.impostazioni;
  f text;
  scelta uuid;
  attive integer;
begin
  select * into imp from public.impostazioni where impostazioni.id;

  update public.estrazioni e
     set stato = 'errore', conclusa_il = now(), errore = 'il workflow non è partito dopo tre tentativi'
   where e.stato = 'avviata' and e.avviata_il < now() - interval '20 minutes' and e.tentativi >= 3;
  update public.estrazioni e
     set stato = 'in_coda', avviata_il = null
   where e.stato = 'avviata' and e.avviata_il < now() - interval '20 minutes';
  update public.estrazioni e
     set stato = 'errore', conclusa_il = now(), errore = 'esecuzione interrotta senza risposta dal workflow'
   where e.stato = 'in_corso' and e.aggiornato_il < now() - make_interval(mins => imp.tempo_max_minuti + 30);

  for f in select distinct q.fonte from public.estrazioni q where q.stato = 'in_coda' loop
    perform pg_advisory_xact_lock(hashtext('coda_estrazioni:' || f));
    select count(*) into attive from public.estrazioni b where b.fonte = f and b.stato in ('avviata', 'in_corso');
    while attive < imp.parallele_per_fonte loop
      scelta := null;
      select q.id into scelta from public.estrazioni q
       where q.fonte = f and q.stato = 'in_coda'
       order by q.creata_il limit 1 for update skip locked;
      exit when scelta is null;
      update public.estrazioni e set stato = 'avviata', avviata_il = now(), tentativi = e.tentativi + 1 where e.id = scelta;
      id := scelta;
      fonte := f;
      return next;
      attive := attive + 1;
    end loop;
  end loop;
end;
$$;

create or replace function public.inizia_estrazione(p_id uuid, p_run_id bigint) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  r public.estrazioni;
  imp public.impostazioni;
begin
  update public.estrazioni e
     set stato = 'in_corso', iniziata_il = now(), run_id = p_run_id
   where e.id = p_id and e.stato = 'avviata'
  returning * into r;
  if not found then
    return null;
  end if;
  select * into imp from public.impostazioni where id;
  return jsonb_build_object(
    'id', r.id, 'utente', r.utente, 'fonte', r.fonte, 'modalita', r.modalita,
    'parametri', r.parametri, 'riprende_da', r.riprende_da, 'tempo_max_minuti', imp.tempo_max_minuti,
    'yt_max_durata_minuti', imp.yt_max_durata_minuti, 'pausa', imp.pausa_secondi);
end;
$$;

revoke execute on function public.assegna_estrazioni(), public.inizia_estrazione(uuid, bigint) from public, anon, authenticated;
grant execute on function public.assegna_estrazioni(), public.inizia_estrazione(uuid, bigint) to service_role;
