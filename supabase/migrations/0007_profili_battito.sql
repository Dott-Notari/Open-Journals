-- =============================================================================
-- Aggiornamento 0007: battito del motore durante l'estrazione, profilo con foto,
-- sospensione degli utenti, registro in tempo reale. Si può rieseguire senza danni.
-- =============================================================================

-- battito e segnale del motore (li scrive il workflow ogni 15 secondi)
alter table public.estrazioni add column if not exists battito timestamptz;
alter table public.estrazioni add column if not exists segnale text;
alter table public.estrazioni drop constraint if exists estrazioni_segnale_check;
alter table public.estrazioni add constraint estrazioni_segnale_check
  check (segnale is null or segnale in ('ok', 'lento', 'rete', 'fermo', 'bloccato'));
alter table public.estrazioni add column if not exists segnale_testo text check (char_length(segnale_testo) <= 300);

-- profilo: foto e sospensione
alter table public.profiles add column if not exists foto text;
alter table public.profiles drop constraint if exists profiles_foto_check;
alter table public.profiles add constraint profiles_foto_check
  check (foto is null or foto ~ ('^' || id::text || '/foto-[0-9]{1,15}\.webp$'));
alter table public.profiles add column if not exists sospeso boolean not null default false;
alter table public.profiles add column if not exists sospeso_il timestamptz;
grant update (nome, foto) on public.profiles to authenticated;

-- un account sospeso conta come non approvato in tutte le regole
create or replace function public.e_approvato() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and approvato and not sospeso
  );
$$;

create or replace function public.e_docente() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and ruolo = 'docente' and approvato and not sospeso
  );
$$;

-- sospendere: annulla le richieste in coda e ferma quelle in corso
create or replace function public.imposta_sospensione(p_utente uuid, p_sospeso boolean) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.e_docente() then
    raise exception 'Operazione riservata al docente';
  end if;
  if p_utente = (select auth.uid()) then
    raise exception 'Non puoi sospendere il tuo account';
  end if;
  update public.profiles
     set sospeso = p_sospeso, sospeso_il = case when p_sospeso then now() else null end
   where id = p_utente;
  if not found then
    raise exception 'Utente inesistente';
  end if;
  if p_sospeso then
    update public.estrazioni set stato = 'annullata', conclusa_il = now()
     where utente = p_utente and stato = 'in_coda';
    update public.estrazioni set richiesta = 'ferma'
     where utente = p_utente and stato in ('avviata', 'in_corso');
  end if;
end;
$$;
revoke execute on function public.imposta_sospensione(uuid, boolean) from public, anon;
grant execute on function public.imposta_sospensione(uuid, boolean) to authenticated;

-- il registro mostra anche durata e segnale
drop view if exists public.registro_estrazioni;
create view public.registro_estrazioni with (security_invoker = true) as
select e.id, e.creata_il, e.email_utente, p.nome, e.fonte, e.modalita, e.parametri, e.stato,
       e.iniziata_il, e.conclusa_il, e.articoli, e.errore, e.dimensione_totale, e.file_cancellati_il,
       e.battito, e.segnale
  from public.estrazioni e
  left join public.profiles p on p.id = e.utente;
revoke all on public.registro_estrazioni from anon, authenticated;
grant select on public.registro_estrazioni to authenticated;
grant all on public.registro_estrazioni to service_role;

-- foto del profilo: bucket privato, ognuno scrive solo la propria cartella
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('foto', 'foto', false, 1048576, array['image/webp'])
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "foto: lettura" on storage.objects;
drop policy if exists "foto: caricamento della propria" on storage.objects;
drop policy if exists "foto: modifica della propria" on storage.objects;
drop policy if exists "foto: cancellazione della propria" on storage.objects;
create policy "foto: lettura" on storage.objects for select to authenticated using (
  bucket_id = 'foto' and ((storage.foldername(name))[1] = (select auth.uid())::text or public.e_docente()));
create policy "foto: caricamento della propria" on storage.objects for insert to authenticated with check (
  bucket_id = 'foto' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "foto: modifica della propria" on storage.objects for update to authenticated using (
  bucket_id = 'foto' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "foto: cancellazione della propria" on storage.objects for delete to authenticated using (
  bucket_id = 'foto' and (storage.foldername(name))[1] = (select auth.uid())::text);

-- aggiornamenti in tempo reale delle estrazioni (le regole RLS valgono anche qui)
do $$ begin
  alter publication supabase_realtime add table public.estrazioni;
exception when duplicate_object or undefined_object then null;
end $$;

create or replace function public.valida_estrazione() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  imp public.impostazioni;
  t public.stato_testate;
  p jsonb := new.parametri;
  ammesse text[];
  k text;
  x jsonb;
  n integer;
  d_dal date;
  d_al date;
  oggi date := (now() at time zone 'Europe/Rome')::date;
begin
  select * into imp from public.impostazioni where id;

  -- chi chiede: con una sessione utente vale sempre l'utente della sessione
  if (select auth.uid()) is not null then
    new.utente := (select auth.uid());
  end if;
  select email into new.email_utente from public.profiles where id = new.utente and approvato and not sospeso;
  if not found then
    raise exception 'Account non approvato o sospeso: nessuna estrazione possibile';
  end if;

  -- campi che solo il sistema può valorizzare
  new.stato := 'in_coda';
  new.creata_il := now();
  new.avviata_il := null;  new.iniziata_il := null;  new.conclusa_il := null;
  new.tentativi := 0;      new.run_id := null;
  new.esaminati := 0;      new.articoli := 0;
  new.avanzamento := null; new.scheda := null; new.log := null; new.errore := null;
  new.dimensione_totale := null; new.file_cancellati_il := null;

  -- fonte disponibile
  select * into t from public.stato_testate where chiave = new.fonte;
  if not found or not t.attiva or not t.disponibile_online then
    raise exception 'Fonte non disponibile sulla piattaforma';
  end if;
  if new.fonte = 'ansa' and not imp.ansa_estrazioni_attive then
    raise exception 'Le estrazioni ANSA sono sospese';
  end if;

  -- forma dei parametri
  if p is null or jsonb_typeof(p) <> 'object' then
    raise exception 'Parametri non validi';
  end if;
  if t.tipo = 'testata' then
    if new.modalita not in ('data', 'elenco', 'link') then
      raise exception 'Modalità non valida per una testata';
    end if;
    ammesse := array['dal', 'al', 'elenco', 'link', 'parole', 'tutte', 'cerca_in', 'formati', 'max_articoli', 'fonte', 'usa_ricerca', 'parole_gdelt'];
  else
    if new.modalita not in ('sorgenti', 'ricerca') then
      raise exception 'Modalità non valida per YouTube';
    end if;
    ammesse := array['sorgenti', 'cerca', 'ordina_per_data', 'dal', 'al', 'parole', 'max_video',
                     'trascrizione', 'lingua', 'media', 'max_altezza', 'timecode_docx'];
  end if;
  for k in select jsonb_object_keys(p) loop
    if not (k = any (ammesse)) then
      raise exception 'Parametro non ammesso: %', k;
    end if;
  end loop;

  -- date
  if p ? 'dal' or p ? 'al' then
    if not (p ? 'dal' and p ? 'al') then
      raise exception 'Indica sia la data iniziale sia quella finale';
    end if;
    if coalesce(p ->> 'dal', '') !~ '^\d{4}-\d{2}-\d{2}$' or coalesce(p ->> 'al', '') !~ '^\d{4}-\d{2}-\d{2}$' then
      raise exception 'Date nel formato AAAA-MM-GG';
    end if;
    begin
      d_dal := (p ->> 'dal')::date;
      d_al := (p ->> 'al')::date;
    exception when others then
      raise exception 'Date non valide';
    end;
    if d_dal > d_al then
      raise exception 'La data iniziale è successiva a quella finale';
    end if;
    if d_al > oggi then
      raise exception 'La data finale è nel futuro';
    end if;
    if d_dal < date '1990-01-01' then
      raise exception 'Data iniziale troppo lontana';
    end if;
  end if;

  -- parole chiave
  if p ? 'parole' then
    if jsonb_typeof(p -> 'parole') <> 'array' or jsonb_array_length(p -> 'parole') > 20 then
      raise exception 'Al massimo 20 parole chiave';
    end if;
    for x in select * from jsonb_array_elements(p -> 'parole') loop
      if jsonb_typeof(x) <> 'string' or (x #>> '{}') !~ '^[[:alnum:]'' *-]{1,60}$' then
        raise exception 'Parola chiave non valida: usa lettere, numeri, spazi, apostrofi, trattini e asterisco';
      end if;
    end loop;
  end if;

  if t.tipo = 'testata' then
    -- modalità
    if new.modalita = 'data' then
      if not p ? 'dal' or p ? 'elenco' or p ? 'link' then
        raise exception 'La ricerca per data richiede solo l''intervallo di date';
      end if;
    elsif new.modalita = 'elenco' then
      if p ? 'link' or jsonb_typeof(p -> 'elenco') is distinct from 'string'
         or not public.url_ammesso(p ->> 'elenco', t.domini) then
        raise exception 'La pagina elenco deve essere un indirizzo di %', t.nome;
      end if;
    else
      if p ? 'elenco' or jsonb_typeof(p -> 'link') is distinct from 'array'
         or jsonb_array_length(p -> 'link') = 0 or jsonb_array_length(p -> 'link') > 10000 then
        raise exception 'Inserisci almeno un link';
      end if;
      for x in select * from jsonb_array_elements(p -> 'link') loop
        if jsonb_typeof(x) <> 'string' or not public.url_ammesso(x #>> '{}', t.domini) then
          raise exception 'Link non valido o non di %', t.nome;
        end if;
      end loop;
    end if;
    -- opzioni
    -- fonte degli indirizzi (motore 1.13): solo con la ricerca per periodo e tra quelle consentite dalla testata
    if p ? 'fonte' then
      if new.modalita <> 'data' then
        raise exception 'La fonte degli indirizzi si sceglie solo nella ricerca per periodo';
      end if;
      if not ((p ->> 'fonte') = any (t.fonti)) then
        raise exception 'Fonte non disponibile per %', t.nome;
      end if;
      if (p ->> 'fonte') = 'ricerca' and coalesce(jsonb_array_length(p -> 'parole'), 0) = 0 then
        raise exception 'La ricerca del sito richiede almeno una parola chiave';
      end if;
    end if;
    if p ? 'usa_ricerca' and jsonb_typeof(p -> 'usa_ricerca') <> 'boolean' then
      raise exception 'Opzione della ricerca del sito non valida';
    end if;
    if p ? 'parole_gdelt' then
      if jsonb_typeof(p -> 'parole_gdelt') <> 'array' or jsonb_array_length(p -> 'parole_gdelt') > 20 then
        raise exception 'Al massimo 20 parole per GDELT';
      end if;
      for x in select * from jsonb_array_elements(p -> 'parole_gdelt') loop
        if jsonb_typeof(x) <> 'string' or (x #>> '{}') !~ '^[[:alnum:]'' *-]{1,60}$' then
          raise exception 'Parola per GDELT non valida';
        end if;
      end loop;
    end if;
    if p ? 'tutte' and jsonb_typeof(p -> 'tutte') <> 'boolean' then
      raise exception 'Opzione «tutte» non valida';
    end if;
    if p ? 'cerca_in' and (p ->> 'cerca_in') is distinct from 'testo' and (p ->> 'cerca_in') is distinct from 'titolo' then
      raise exception 'Opzione «cerca in» non valida';
    end if;
    if p ? 'formati' then
      if jsonb_typeof(p -> 'formati') <> 'array' then
        raise exception 'Formati non validi';
      end if;
      for x in select * from jsonb_array_elements(p -> 'formati') loop
        if (x #>> '{}') is null or not ((x #>> '{}') = any (array['docx', 'txt', 'html', 'xlsx', 'jsonl', 'tlab'])) then
          raise exception 'Formato non disponibile';
        end if;
      end loop;
    end if;
    if p ? 'max_articoli' and (jsonb_typeof(p -> 'max_articoli') <> 'number'
        or (p ->> 'max_articoli') !~ '^\d+$' or (p ->> 'max_articoli')::bigint < 1) then
      raise exception 'Numero massimo di articoli non valido';
    end if;
  else
    -- YouTube
    if new.modalita = 'sorgenti' then
      if p ? 'cerca' or jsonb_typeof(p -> 'sorgenti') is distinct from 'array'
         or jsonb_array_length(p -> 'sorgenti') = 0 or jsonb_array_length(p -> 'sorgenti') > 10000 then
        raise exception 'Inserisci almeno un link di video, playlist o canale';
      end if;
      for x in select * from jsonb_array_elements(p -> 'sorgenti') loop
        if jsonb_typeof(x) <> 'string' or not public.url_ammesso(x #>> '{}', t.domini) then
          raise exception 'Link YouTube non valido';
        end if;
      end loop;
    else
      if p ? 'sorgenti' or jsonb_typeof(p -> 'cerca') is distinct from 'string'
         or char_length(btrim(p ->> 'cerca')) not between 2 and 100
         or (p ->> 'cerca') ~ '[[:cntrl:]]' then
        raise exception 'Testo della ricerca non valido (da 2 a 100 caratteri)';
      end if;
    end if;
    if p ? 'ordina_per_data' and jsonb_typeof(p -> 'ordina_per_data') <> 'boolean' then
      raise exception 'Opzione di ordinamento non valida';
    end if;
    if p ? 'timecode_docx' and jsonb_typeof(p -> 'timecode_docx') <> 'boolean' then
      raise exception 'Opzione dei marcatori temporali non valida';
    end if;
    if p ? 'trascrizione' and not ((p ->> 'trascrizione') = any (array['auto', 'sottotitoli', 'whisper'])) then
      raise exception 'Modalità di trascrizione non valida';
    end if;
    if p ? 'media' and not ((p ->> 'media') = any (array['entrambi', 'video', 'audio', 'nessuno'])) then
      raise exception 'Scelta dei file multimediali non valida';
    end if;
    if p ? 'lingua' and coalesce(p ->> 'lingua', '') !~ '^[a-z]{2}$' then
      raise exception 'Lingua non valida (codice di due lettere, per esempio it)';
    end if;
    if p ? 'max_video' and (jsonb_typeof(p -> 'max_video') <> 'number'
        or (p ->> 'max_video') !~ '^\d+$' or (p ->> 'max_video')::bigint < 1) then
      raise exception 'Numero massimo di video non valido';
    end if;
    if p ? 'max_altezza' and (jsonb_typeof(p -> 'max_altezza') <> 'number'
        or not ((p ->> 'max_altezza') = any (array['144', '240', '360', '480', '720', '1080']))) then
      raise exception 'Risoluzione non valida';
    end if;
  end if;

  return new;
end;
$$;


