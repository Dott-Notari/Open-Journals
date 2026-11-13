-- =============================================================================
-- Aggiornamento 0006: motore 1.13. Fonte degli indirizzi per testata (archivio,
-- ricerca del sito, Wayback, GDELT), ricerca del sito attivabile, nuove testate
-- estere. Si può rieseguire senza danni.
-- =============================================================================
alter table public.stato_testate add column if not exists fonti text[] not null default '{auto,archivio,wayback,gdelt}';
alter table public.stato_testate add column if not exists gruppo text not null default 'italiane' check (gruppo in ('italiane', 'estere', 'video'));

insert into public.stato_testate (chiave, nome, tipo, domini, ordine, fonti, gruppo) values
  ('independent', 'The Independent', 'testata', '{independent.co.uk}', 16, '{auto,archivio,wayback,gdelt}', 'estere'),
  ('mirror', 'Daily Mirror', 'testata', '{mirror.co.uk}', 17, '{auto,archivio,wayback,gdelt}', 'estere'),
  ('elmundo', 'El Mundo', 'testata', '{elmundo.es}', 18, '{auto,archivio,wayback,gdelt}', 'estere')
on conflict (chiave) do nothing;
update public.stato_testate set ordine = 30, gruppo = 'video', fonti = '{}' where chiave = 'youtube';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'ilgiornale';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'avvenire';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'fatto';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'ansa';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'ilpost';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'libero';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'manifesto';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'mattino';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'corriere';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'repubblica';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'lastampa';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'italiane' where chiave = 'messaggero';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'verita';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'italiane' where chiave = 'sole24ore';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'estere' where chiave = 'independent';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'estere' where chiave = 'mirror';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'estere' where chiave = 'elmundo';

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


