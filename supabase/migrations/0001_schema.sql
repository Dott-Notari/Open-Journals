-- =============================================================================
-- Scraper didattico delle testate giornalistiche: schema Supabase, versione 1
-- Da eseguire una sola volta nell'editor SQL del progetto Supabase.
--
-- Principi di sicurezza applicati:
--   1. RLS attiva su tutte le tabelle; anon non ha alcun privilegio.
--   2. Privilegi per colonna: lo studente può inserire solo fonte, modalita e
--      parametri di un'estrazione e modificare solo il proprio nome.
--   3. Validazione dei parametri nel database (trigger), indipendente
--      dall'interfaccia: chiavi ammesse, URL limitati ai domini della fonte,
--      tetti su date, articoli, video e richieste per utente.
--   4. Le operazioni della coda sono eseguibili solo con la chiave di servizio
--      (workflow di GitHub Actions e route lato server di Next.js).
--   5. Le funzioni SECURITY DEFINER hanno search_path vuoto e nomi qualificati.
-- =============================================================================

-- ----------------------------------------------------------------------------- tipi
create type public.ruolo_utente as enum ('studente', 'docente');

create type public.stato_estrazione as enum (
  'in_coda',     -- registrata, in attesa che la fonte sia libera
  'avviata',     -- assegnata e inviata a GitHub Actions, non ancora partita
  'in_corso',    -- il workflow sta lavorando
  'completata',
  'interrotta',  -- fermata dal limite di tempo: i file raccolti sono scaricabili
  'errore',
  'annullata'
);

-- ----------------------------------------------------------------------------- impostazioni
-- Una sola riga, modificabile dal docente dall'area docente.
create table public.impostazioni (
  id boolean primary key default true check (id),
  registrazioni_aperte boolean not null default true,
  domini_email_ammessi text[] not null default '{}',   -- vuoto = qualsiasi dominio
  ansa_estrazioni_attive boolean not null default true,
  ansa_indicizzazione_attiva boolean not null default true,
  tempo_max_minuti integer not null default 45 check (tempo_max_minuti between 5 and 90), -- il job di Actions ha un timeout di 120 minuti
  max_articoli_tetto integer not null default 500 check (max_articoli_tetto between 1 and 5000),
  max_giorni_intervallo integer not null default 366 check (max_giorni_intervallo between 1 and 9000),
  max_link integer not null default 50 check (max_link between 1 and 500),
  max_attive_per_utente integer not null default 2 check (max_attive_per_utente between 1 and 20),
  max_giornaliere_per_utente integer not null default 10 check (max_giornaliere_per_utente between 1 and 200),
  giorni_conservazione integer not null default 5 check (giorni_conservazione between 1 and 30),
  yt_max_video integer not null default 20 check (yt_max_video between 1 and 500),
  yt_max_durata_minuti integer not null default 30 check (yt_max_durata_minuti between 1 and 600),
  yt_max_altezza integer not null default 480 check (yt_max_altezza in (144, 240, 360, 480, 720, 1080)),
  aggiornato_il timestamptz not null default now()
);
insert into public.impostazioni default values;

-- ----------------------------------------------------------------------------- fonti
-- Le quattordici testate e YouTube. disponibile_online nasce falso: diventa vero
-- con l'esito positivo del collaudo da GitHub Actions (o per scelta del docente).
create table public.stato_testate (
  chiave text primary key check (chiave ~ '^[a-z0-9_]{2,30}$'),
  nome text not null,
  tipo text not null check (tipo in ('testata', 'youtube')),
  domini text[] not null check (cardinality(domini) > 0),
  ordine integer not null,
  attiva boolean not null default true,              -- interruttore del docente
  disponibile_online boolean not null default false, -- esito del collaudo da data center
  max_giorni integer check (max_giorni between 1 and 9000), -- tetto specifico, prevale su quello generale
  esito_collaudo text not null default 'mai' check (esito_collaudo in ('mai', 'ok', 'parziale', 'fallito')),
  collaudo_il timestamptz,
  dettaglio_collaudo text,
  note_docente text check (char_length(note_docente) <= 2000),
  aggiornato_il timestamptz not null default now()
);

insert into public.stato_testate (chiave, nome, tipo, domini, ordine) values
  ('ilgiornale', 'il Giornale',          'testata', '{ilgiornale.it}',         1),
  ('avvenire',   'Avvenire',             'testata', '{avvenire.it}',           2),
  ('fatto',      'Il Fatto Quotidiano',  'testata', '{ilfattoquotidiano.it}',  3),
  ('ansa',       'ANSA',                 'testata', '{ansa.it}',               4),
  ('ilpost',     'Il Post',              'testata', '{ilpost.it}',             5),
  ('libero',     'Libero',               'testata', '{liberoquotidiano.it}',   6),
  ('manifesto',  'il manifesto',         'testata', '{ilmanifesto.it}',        7),
  ('mattino',    'Il Mattino',           'testata', '{ilmattino.it}',          8),
  ('corriere',   'Corriere della Sera',  'testata', '{corriere.it}',           9),
  ('repubblica', 'la Repubblica',        'testata', '{repubblica.it}',        10),
  ('lastampa',   'La Stampa',            'testata', '{lastampa.it}',          11),
  ('messaggero', 'Il Messaggero',        'testata', '{ilmessaggero.it}',      12),
  ('verita',     'La Verità',            'testata', '{laverita.info}',        13),
  ('sole24ore',  'Il Sole 24 Ore',       'testata', '{ilsole24ore.com}',      14),
  ('youtube',    'YouTube',              'youtube', '{youtube.com,youtu.be}', 15);

-- ----------------------------------------------------------------------------- profili
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  nome text check (char_length(nome) <= 120),
  ruolo public.ruolo_utente not null default 'studente',
  approvato boolean not null default false,
  approvato_il timestamptz,
  approvato_da uuid references public.profiles (id) on delete set null,
  registrato_il timestamptz not null default now()
);

-- ----------------------------------------------------------------------------- estrazioni (registro)
create table public.estrazioni (
  id uuid primary key default gen_random_uuid(),
  utente uuid references public.profiles (id) on delete set null,
  email_utente text not null,                 -- copia per il registro, resta se l'account viene cancellato
  fonte text not null references public.stato_testate (chiave),
  modalita text not null check (modalita in ('data', 'elenco', 'link', 'sorgenti', 'ricerca')),
  parametri jsonb not null,
  stato public.stato_estrazione not null default 'in_coda',
  creata_il timestamptz not null default now(),
  avviata_il timestamptz,
  iniziata_il timestamptz,
  conclusa_il timestamptz,
  aggiornato_il timestamptz not null default now(),
  tentativi integer not null default 0,
  run_id bigint,                              -- identificativo dell'esecuzione su GitHub Actions
  esaminati integer not null default 0,       -- avanzamento: indirizzi esaminati
  articoli integer not null default 0,        -- articoli o video raccolti
  avanzamento text check (char_length(avanzamento) <= 500),
  scheda text,                                -- testo di scheda_estrazione.txt
  log text,                                   -- dettaglio del motore (non va nei log pubblici di Actions)
  errore text,
  dimensione_totale bigint,
  file_cancellati_il timestamptz
);

create index estrazioni_utente_idx on public.estrazioni (utente, creata_il desc);
create index estrazioni_coda_idx on public.estrazioni (fonte, stato, creata_il);
create index estrazioni_stato_idx on public.estrazioni (stato);

-- File prodotti: uno zip per le testate; per YouTube uno zip dei testi
-- più i file video e audio separati (uno zip non ne ridurrebbe il peso).
create table public.estrazione_file (
  id uuid primary key default gen_random_uuid(),
  estrazione_id uuid not null references public.estrazioni (id) on delete cascade,
  percorso text not null unique,              -- <utente>/<estrazione>/<file> nel bucket «estrazioni»
  tipo text not null check (tipo in ('zip', 'video', 'audio')),
  nome text not null,                         -- nome proposto allo scaricamento
  dimensione bigint not null,
  creato_il timestamptz not null default now()
);
create index estrazione_file_estrazione_idx on public.estrazione_file (estrazione_id);

-- ----------------------------------------------------------------------------- indice ANSA
-- Solo metadati, nessun testo.
create table public.ansa_indice (
  url text primary key check (url ~ '^https://www\.ansa\.it/'),
  titolo text,
  pubblicato_il timestamptz not null,
  sezione text,
  regione text,
  inserito_il timestamptz not null default now()
);
create index ansa_indice_data_idx on public.ansa_indice (pubblicato_il);

-- ----------------------------------------------------------------------------- funzioni di supporto
create function public.e_docente() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and ruolo = 'docente' and approvato
  );
$$;

create function public.e_approvato() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and approvato
  );
$$;

-- Vero se l'URL è https o http, senza credenziali né porta, e appartiene a uno dei domini.
create function public.url_ammesso(u text, domini text[]) returns boolean
language plpgsql immutable set search_path = '' as $$
declare
  host text;
  d text;
begin
  if u is null or char_length(u) > 2000 or u !~ '^https?://[^[:space:]]+$' then
    return false;
  end if;
  host := lower(substring(u from '^https?://([^/?#]+)'));
  if host is null or host !~ '^[a-z0-9.-]+$' then
    return false;   -- esclude credenziali (@), porte (:), barre rovesciate e caratteri non ASCII
  end if;
  foreach d in array domini loop
    if host = d or host like ('%.' || d) then
      return true;
    end if;
  end loop;
  return false;
end;
$$;

create function public.tocca_aggiornato_il() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.aggiornato_il := now();
  return new;
end;
$$;

create trigger impostazioni_aggiornato before update on public.impostazioni
  for each row execute function public.tocca_aggiornato_il();
create trigger stato_testate_aggiornato before update on public.stato_testate
  for each row execute function public.tocca_aggiornato_il();
create trigger estrazioni_aggiornato before update on public.estrazioni
  for each row execute function public.tocca_aggiornato_il();

-- ----------------------------------------------------------------------------- registrazione
-- Crea il profilo (non approvato) e applica le regole di registrazione.
create function public.gestisci_nuovo_utente() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  imp public.impostazioni;
  dominio text;
begin
  select * into imp from public.impostazioni where id;
  dominio := lower(split_part(new.email, '@', 2));
  if not imp.registrazioni_aperte then
    raise exception 'Le registrazioni sono chiuse';
  end if;
  if cardinality(imp.domini_email_ammessi) > 0 and not (dominio = any (imp.domini_email_ammessi)) then
    raise exception 'Registrazione consentita solo con l''indirizzo email istituzionale';
  end if;
  insert into public.profiles (id, email, nome)
  values (new.id, new.email, left(nullif(btrim(new.raw_user_meta_data ->> 'nome'), ''), 120));
  return new;
end;
$$;

create trigger alla_registrazione after insert on auth.users
  for each row execute function public.gestisci_nuovo_utente();

create function public.sincronizza_email() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  update public.profiles set email = new.email where id = new.id;
  return new;
end;
$$;

create trigger al_cambio_email after update of email on auth.users
  for each row execute function public.sincronizza_email();

-- ----------------------------------------------------------------------------- validazione delle richieste
create function public.valida_estrazione() returns trigger
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

  -- quote per utente
  select count(*) into n from public.estrazioni
   where utente = new.utente and stato in ('in_coda', 'avviata', 'in_corso');
  if n >= imp.max_attive_per_utente then
    raise exception 'Hai già % estrazioni in coda o in corso', n;
  end if;
  select count(*) into n from public.estrazioni
   where utente = new.utente and creata_il > now() - interval '24 hours';
  if n >= imp.max_giornaliere_per_utente then
    raise exception 'Limite giornaliero di estrazioni raggiunto';
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
    if (d_al - d_dal + 1) > coalesce(t.max_giorni, imp.max_giorni_intervallo) then
      raise exception 'Intervallo troppo ampio: al massimo % giorni per questa fonte',
        coalesce(t.max_giorni, imp.max_giorni_intervallo);
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
         or jsonb_array_length(p -> 'link') = 0 or jsonb_array_length(p -> 'link') > imp.max_link then
        raise exception 'Inserisci da 1 a % link', imp.max_link;
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
    -- tetto sempre presente
    new.parametri := p || jsonb_build_object('max_articoli',
      least(coalesce((p ->> 'max_articoli')::bigint, imp.max_articoli_tetto), imp.max_articoli_tetto));

  else
    -- YouTube
    if new.modalita = 'sorgenti' then
      if p ? 'cerca' or jsonb_typeof(p -> 'sorgenti') is distinct from 'array'
         or jsonb_array_length(p -> 'sorgenti') = 0 or jsonb_array_length(p -> 'sorgenti') > imp.max_link then
        raise exception 'Inserisci da 1 a % link di video, playlist o canali', imp.max_link;
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
    new.parametri := p || jsonb_build_object(
      'max_video', least(coalesce((p ->> 'max_video')::bigint, imp.yt_max_video), imp.yt_max_video),
      'max_altezza', least(coalesce((p ->> 'max_altezza')::integer, imp.yt_max_altezza), imp.yt_max_altezza));
  end if;

  return new;
end;
$$;

create trigger valida_prima_di_inserire before insert on public.estrazioni
  for each row execute function public.valida_estrazione();

-- ----------------------------------------------------------------------------- coda (solo chiave di servizio)
-- Assegna al più un'estrazione per fonte libera e restituisce quelle da avviare.
-- La chiamano la route di Next.js dopo ogni richiesta, il workflow alla fine di
-- ogni estrazione e il controllo programmato. Recupera prima le righe bloccate.
create function public.assegna_estrazioni() returns table (id uuid, fonte text)
language plpgsql security definer set search_path = '' as $$
declare
  imp public.impostazioni;
  f text;
  scelta uuid;
begin
  select * into imp from public.impostazioni where impostazioni.id;

  -- inviate ad Actions ma mai partite: si rimettono in coda, al terzo tentativo errore
  update public.estrazioni e
     set stato = 'errore', conclusa_il = now(),
         errore = 'il workflow non è partito dopo tre tentativi'
   where e.stato = 'avviata' and e.avviata_il < now() - interval '20 minutes' and e.tentativi >= 3;
  update public.estrazioni e
     set stato = 'in_coda', avviata_il = null
   where e.stato = 'avviata' and e.avviata_il < now() - interval '20 minutes';

  -- in corso ma senza segnali oltre il limite di tempo più un margine: esecuzione persa
  update public.estrazioni e
     set stato = 'errore', conclusa_il = now(),
         errore = 'esecuzione interrotta senza risposta dal workflow'
   where e.stato = 'in_corso'
     and e.aggiornato_il < now() - make_interval(mins => imp.tempo_max_minuti + 30);

  for f in select distinct q.fonte from public.estrazioni q where q.stato = 'in_coda' loop
    perform pg_advisory_xact_lock(hashtext('coda_estrazioni:' || f));
    if not exists (select 1 from public.estrazioni b
                    where b.fonte = f and b.stato in ('avviata', 'in_corso')) then
      select q.id into scelta from public.estrazioni q
       where q.fonte = f and q.stato = 'in_coda'
       order by q.creata_il
       limit 1
       for update skip locked;
      if scelta is not null then
        update public.estrazioni e
           set stato = 'avviata', avviata_il = now(), tentativi = e.tentativi + 1
         where e.id = scelta;
        id := scelta;
        fonte := f;
        return next;
      end if;
    end if;
  end loop;
end;
$$;

-- Il workflow la chiama appena parte: passa da «avviata» a «in corso» una sola volta
-- e restituisce ciò che serve per eseguire (null se l'estrazione non è più da fare).
create function public.inizia_estrazione(p_id uuid, p_run_id bigint) returns jsonb
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
    'parametri', r.parametri, 'tempo_max_minuti', imp.tempo_max_minuti,
    'yt_max_durata_minuti', imp.yt_max_durata_minuti);
end;
$$;

-- ----------------------------------------------------------------------------- azioni degli utenti
create function public.annulla_estrazione(p_id uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  update public.estrazioni e
     set stato = 'annullata', conclusa_il = now()
   where e.id = p_id
     and e.stato = 'in_coda'
     and (e.utente = (select auth.uid()) or public.e_docente());
  return found;
end;
$$;

create function public.imposta_approvazione(p_utente uuid, p_approvato boolean) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.e_docente() then
    raise exception 'Operazione riservata al docente';
  end if;
  if p_utente = (select auth.uid()) then
    raise exception 'Non puoi modificare la tua approvazione';
  end if;
  update public.profiles
     set approvato = p_approvato,
         approvato_il = case when p_approvato then now() else null end,
         approvato_da = case when p_approvato then (select auth.uid()) else null end
   where id = p_utente;
  if not found then
    raise exception 'Utente inesistente';
  end if;
  if not p_approvato then
    update public.estrazioni set stato = 'annullata', conclusa_il = now()
     where utente = p_utente and stato = 'in_coda';
  end if;
end;
$$;

create function public.imposta_ruolo(p_utente uuid, p_ruolo public.ruolo_utente) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.e_docente() then
    raise exception 'Operazione riservata al docente';
  end if;
  if p_utente = (select auth.uid()) then
    raise exception 'Non puoi modificare il tuo ruolo';
  end if;
  update public.profiles set ruolo = p_ruolo where id = p_utente;
  if not found then
    raise exception 'Utente inesistente';
  end if;
end;
$$;

-- Da quale giorno l'ANSA è interrogabile sulla piattaforma (senza esporre l'indice).
create function public.copertura_ansa()
returns table (dal timestamptz, al timestamptz, articoli bigint)
language sql stable security definer set search_path = '' as $$
  select min(pubblicato_il), max(pubblicato_il), count(*)
    from public.ansa_indice
   where public.e_approvato();
$$;

-- ----------------------------------------------------------------------------- registro per il docente
create view public.registro_estrazioni with (security_invoker = true) as
select e.id, e.creata_il, e.email_utente, p.nome, e.fonte, e.modalita, e.parametri, e.stato,
       e.iniziata_il, e.conclusa_il, e.articoli, e.errore, e.dimensione_totale, e.file_cancellati_il
  from public.estrazioni e
  left join public.profiles p on p.id = e.utente;

-- ----------------------------------------------------------------------------- RLS
alter table public.impostazioni enable row level security;
alter table public.stato_testate enable row level security;
alter table public.profiles enable row level security;
alter table public.estrazioni enable row level security;
alter table public.estrazione_file enable row level security;
alter table public.ansa_indice enable row level security;

create policy "impostazioni: lettura" on public.impostazioni
  for select to authenticated using (true);
create policy "impostazioni: modifica del docente" on public.impostazioni
  for update to authenticated using (public.e_docente()) with check (public.e_docente());

create policy "fonti: lettura" on public.stato_testate
  for select to authenticated using (true);
create policy "fonti: modifica del docente" on public.stato_testate
  for update to authenticated using (public.e_docente()) with check (public.e_docente());

create policy "profili: il proprio o tutti per il docente" on public.profiles
  for select to authenticated using (id = (select auth.uid()) or public.e_docente());
create policy "profili: modifica del proprio nome" on public.profiles
  for update to authenticated using (id = (select auth.uid())) with check (id = (select auth.uid()));

create policy "estrazioni: le proprie o tutte per il docente" on public.estrazioni
  for select to authenticated using (utente = (select auth.uid()) or public.e_docente());
create policy "estrazioni: nuove richieste degli approvati" on public.estrazioni
  for insert to authenticated with check (utente = (select auth.uid()) and public.e_approvato());

create policy "file: delle proprie estrazioni o tutti per il docente" on public.estrazione_file
  for select to authenticated using (
    public.e_docente() or exists (
      select 1 from public.estrazioni e
       where e.id = estrazione_id and e.utente = (select auth.uid())));

create policy "indice ANSA: solo docente" on public.ansa_indice
  for select to authenticated using (public.e_docente());

-- ----------------------------------------------------------------------------- privilegi
-- Supabase concede per impostazione tutto ad anon e authenticated: si revoca e si
-- concede solo il necessario, colonna per colonna dove serve.
revoke all on public.impostazioni, public.stato_testate, public.profiles, public.estrazioni,
              public.estrazione_file, public.ansa_indice, public.registro_estrazioni
  from anon, authenticated;

grant select on public.impostazioni, public.stato_testate, public.profiles, public.estrazioni,
                public.estrazione_file, public.ansa_indice, public.registro_estrazioni
  to authenticated;
grant update (nome) on public.profiles to authenticated;
grant insert (fonte, modalita, parametri) on public.estrazioni to authenticated;
grant update (attiva, disponibile_online, max_giorni, note_docente) on public.stato_testate to authenticated;
grant update (registrazioni_aperte, domini_email_ammessi, ansa_estrazioni_attive, ansa_indicizzazione_attiva,
              tempo_max_minuti, max_articoli_tetto, max_giorni_intervallo, max_link, max_attive_per_utente,
              max_giornaliere_per_utente, giorni_conservazione, yt_max_video, yt_max_durata_minuti, yt_max_altezza)
  on public.impostazioni to authenticated;

grant all on public.impostazioni, public.stato_testate, public.profiles, public.estrazioni,
             public.estrazione_file, public.ansa_indice, public.registro_estrazioni
  to service_role;

revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.e_docente(), public.e_approvato(), public.annulla_estrazione(uuid),
                          public.imposta_approvazione(uuid, boolean), public.imposta_ruolo(uuid, public.ruolo_utente),
                          public.copertura_ansa()
  to authenticated;
grant execute on function public.assegna_estrazioni(), public.inizia_estrazione(uuid, bigint)
  to service_role;

-- ----------------------------------------------------------------------------- storage
-- Bucket privato, piano Pro: 1 GB per file (un video a 480p di 30 minuti resta ben sotto).
-- Il limite globale del progetto (Storage > Settings) va portato almeno allo stesso valore.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('estrazioni', 'estrazioni', false, 1073741824,
        array['application/zip', 'video/mp4', 'audio/mpeg', 'audio/mp4'])
on conflict (id) do update
  set public = false,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Lettura (e quindi link firmati) solo per i file nella cartella del proprio utente;
-- nessuna scrittura dal browser: carica e cancella solo il workflow con la chiave di servizio.
create policy "estrazioni: lettura dei propri file" on storage.objects
  for select to authenticated using (
    bucket_id = 'estrazioni' and (
      public.e_docente()
      or ((storage.foldername(name))[1] = (select auth.uid())::text and public.e_approvato())));
