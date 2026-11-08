-- =============================================================================
-- Aggiornamento 0002: nessun limite alle estrazioni degli studenti
-- Da eseguire una sola volta nell'editor SQL, dopo 0001_schema.sql.
-- Restano solo i vincoli tecnici: durata massima di un'esecuzione (GitHub ferma
-- un job dopo 6 ore), durata massima di un video (35 minuti), conservazione dei file.
-- =============================================================================

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
  select email into new.email_utente from public.profiles where id = new.utente and approvato;
  if not found then
    raise exception 'Account non approvato: nessuna estrazione possibile';
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
    ammesse := array['dal', 'al', 'elenco', 'link', 'parole', 'tutte', 'cerca_in', 'formati', 'max_articoli'];
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


alter table public.impostazioni
  drop column max_articoli_tetto,
  drop column max_giorni_intervallo,
  drop column max_link,
  drop column max_attive_per_utente,
  drop column max_giornaliere_per_utente,
  drop column yt_max_video,
  drop column yt_max_altezza;
alter table public.stato_testate drop column max_giorni;

alter table public.impostazioni drop constraint impostazioni_tempo_max_minuti_check;
alter table public.impostazioni add constraint impostazioni_tempo_max_minuti_check check (tempo_max_minuti between 5 and 330);
alter table public.impostazioni alter column tempo_max_minuti set default 330;
alter table public.impostazioni alter column yt_max_durata_minuti set default 35;
update public.impostazioni set tempo_max_minuti = 330, yt_max_durata_minuti = 35;

-- file fino a 5 GB (alzare allo stesso valore il limite globale in Storage > Settings)
update storage.buckets set file_size_limit = 5368709120 where id = 'estrazioni';

-- numeri della piattaforma per la pagina iniziale, senza esporre il registro
create or replace function public.statistiche()
returns table (estrazioni bigint, articoli bigint, video bigint)
language sql stable security definer set search_path = '' as $$
  select count(*) filter (where stato in ('completata', 'interrotta')),
         coalesce(sum(articoli) filter (where fonte <> 'youtube'), 0),
         coalesce(sum(articoli) filter (where fonte = 'youtube'), 0)
    from public.estrazioni
   where public.e_approvato();
$$;
revoke execute on function public.statistiche() from public, anon;
grant execute on function public.statistiche() to authenticated;
revoke execute on function public.valida_estrazione() from public, anon, authenticated;
