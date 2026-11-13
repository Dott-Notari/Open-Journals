-- =============================================================================
-- Aggiornamento 0004: fermare un'estrazione in corso (si scarica ciò che è stato
-- raccolto) e riprenderla più tardi dal punto in cui si era fermata.
-- Si può rieseguire senza danni.
-- =============================================================================
alter table public.estrazioni add column if not exists richiesta text check (richiesta in ('ferma'));
alter table public.estrazioni add column if not exists riprende_da uuid references public.estrazioni (id) on delete set null;

-- lo stato di lavoro per la ripresa si salva come file privato, non scaricabile dall'interfaccia
alter table public.estrazione_file drop constraint if exists estrazione_file_tipo_check;
alter table public.estrazione_file add constraint estrazione_file_tipo_check check (tipo in ('zip', 'video', 'audio', 'ripresa'));

-- Fermare: se l'estrazione non è ancora partita viene annullata, altrimenti il
-- workflow se ne accorge entro pochi secondi, chiude e consegna i file.
create or replace function public.ferma_estrazione(p_id uuid) returns text
language plpgsql security definer set search_path = '' as $$
declare
  s public.stato_estrazione;
begin
  select stato into s from public.estrazioni
   where id = p_id and (utente = (select auth.uid()) or public.e_docente());
  if not found then
    raise exception 'Estrazione inesistente';
  end if;
  if s = 'in_coda' then
    update public.estrazioni set stato = 'annullata', conclusa_il = now() where id = p_id;
    return 'annullata';
  end if;
  if s not in ('avviata', 'in_corso') then
    raise exception 'L''estrazione non è in corso';
  end if;
  update public.estrazioni set richiesta = 'ferma' where id = p_id;
  return 'richiesta';
end;
$$;

-- Riprendere: crea una nuova richiesta con gli stessi parametri che riparte dallo
-- stato salvato. Il risultato contiene anche gli articoli già raccolti.
create or replace function public.riprendi_estrazione(p_id uuid) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  r public.estrazioni;
  nuova uuid;
begin
  select * into r from public.estrazioni where id = p_id and utente = (select auth.uid());
  if not found or r.stato <> 'interrotta' then
    raise exception 'Si può riprendere solo un''estrazione interrotta';
  end if;
  if not exists (select 1 from public.estrazione_file where estrazione_id = p_id and tipo = 'ripresa') then
    raise exception 'Il punto di ripresa non è più disponibile';
  end if;
  if exists (select 1 from public.estrazioni where riprende_da = p_id and stato not in ('errore', 'annullata')) then
    raise exception 'Questa estrazione è già stata ripresa';
  end if;
  insert into public.estrazioni (utente, fonte, modalita, parametri, riprende_da)
  values (r.utente, r.fonte, r.modalita, r.parametri, p_id)
  returning id into nuova;
  return nuova;
end;
$$;

-- il workflow riceve anche l'estrazione da cui riprendere
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
    'yt_max_durata_minuti', imp.yt_max_durata_minuti);
end;
$$;

revoke execute on function public.ferma_estrazione(uuid), public.riprendi_estrazione(uuid) from public, anon;
grant execute on function public.ferma_estrazione(uuid), public.riprendi_estrazione(uuid) to authenticated;
revoke execute on function public.inizia_estrazione(uuid, bigint) from public, anon, authenticated;
grant execute on function public.inizia_estrazione(uuid, bigint) to service_role;
