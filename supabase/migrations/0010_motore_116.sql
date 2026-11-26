-- =============================================================================
-- Aggiornamento 0010: motore 1.16. Testate di videogiochi, francesi e spagnole (61 nuove)
-- e tempo di estrazione illimitato: un'estrazione lunga prosegue da sola in più parti,
-- ognuna lunga al massimo quanto la durata impostata dal docente.
-- Si può rieseguire senza danni.
-- =============================================================================
alter table public.stato_testate drop constraint if exists stato_testate_gruppo_check;
alter table public.stato_testate add constraint stato_testate_gruppo_check
  check (gruppo in ('italiane', 'estere', 'napoli', 'venezuela', 'videogiochi', 'francesi', 'spagnole', 'video', 'rassegna'));

-- nuove testate: nascono non disponibili, le accende il collaudo
insert into public.stato_testate (chiave, nome, tipo, domini, ordine, fonti, gruppo) values
  ('ign', 'IGN', 'testata', '{ign.com}', 141, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('ignitalia', 'IGN Italia', 'testata', '{it.ign.com}', 142, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('eurogamer', 'Eurogamer', 'testata', '{eurogamer.net}', 143, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('polygon', 'Polygon', 'testata', '{polygon.com}', 144, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('kotaku', 'Kotaku', 'testata', '{kotaku.com}', 145, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('pcgamer', 'PC Gamer', 'testata', '{pcgamer.com}', 146, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('rockpapershotgun', 'Rock Paper Shotgun', 'testata', '{rockpapershotgun.com}', 147, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamesradar', 'GamesRadar+', 'testata', '{gamesradar.com}', 148, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gameinformer', 'Game Informer', 'testata', '{gameinformer.com}', 149, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('vgc', 'Video Games Chronicle', 'testata', '{videogameschronicle.com}', 150, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('thegamer', 'TheGamer', 'testata', '{thegamer.com}', 151, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamerant', 'GameRant', 'testata', '{gamerant.com}', 152, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('multiplayer', 'Multiplayer.it', 'testata', '{multiplayer.it}', 153, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('everyeye', 'Everyeye.it', 'testata', '{everyeye.it}', 154, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('spaziogames', 'Spaziogames', 'testata', '{spaziogames.it}', 155, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamereactor', 'Gamereactor Italia', 'testata', '{gamereactor.it}', 156, '{auto,archivio,ricerca,wayback,gdelt}', 'videogiochi'),
  ('gamesource', 'GameSource', 'testata', '{gamesource.it}', 157, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamesindustry', 'GamesIndustry.biz', 'testata', '{gamesindustry.biz}', 158, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamedeveloper', 'Game Developer', 'testata', '{gamedeveloper.com}', 159, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('eurogameres', 'Eurogamer España', 'testata', '{eurogamer.es}', 160, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('ignespana', 'IGN España', 'testata', '{es.ign.com}', 161, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('gamereactores', 'Gamereactor España', 'testata', '{gamereactor.es}', 162, '{auto,archivio,ricerca,wayback,gdelt}', 'videogiochi'),
  ('3djuegos', '3DJuegos', 'testata', '{3djuegos.com}', 163, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('vandal', 'Vandal', 'testata', '{vandal.elespanol.com}', 164, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('hobbyconsolas', 'Hobby Consolas', 'testata', '{hobbyconsolas.com}', 165, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('pushsquare', 'Push Square', 'testata', '{pushsquare.com}', 166, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('purexbox', 'Pure Xbox', 'testata', '{purexbox.com}', 167, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('nintendolife', 'Nintendo Life', 'testata', '{nintendolife.com}', 168, '{auto,archivio,wayback,gdelt}', 'videogiochi'),
  ('lemonde', 'Le Monde', 'testata', '{lemonde.fr}', 101, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('lefigaro', 'Le Figaro', 'testata', '{lefigaro.fr}', 102, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('20minutesfr', '20 Minutes', 'testata', '{20minutes.fr}', 103, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('franceinfo', 'franceinfo', 'testata', '{franceinfo.fr}', 104, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('bfmtv', 'BFMTV', 'testata', '{bfmtv.com}', 105, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('lci', 'TF1 Info (LCI)', 'testata', '{tf1info.fr}', 106, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('cnews', 'CNews', 'testata', '{cnews.fr}', 107, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('france24', 'France 24', 'testata', '{france24.com}', 108, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('latribune', 'La Tribune', 'testata', '{latribune.fr}', 109, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('humanite', 'L''Humanité', 'testata', '{humanite.fr}', 110, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('lacroix', 'La Croix', 'testata', '{la-croix.com}', 111, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('lobs', 'L''Obs', 'testata', '{nouvelobs.com}', 112, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('lexpress', 'L''Express', 'testata', '{lexpress.fr}', 113, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('mediapart', 'Mediapart', 'testata', '{mediapart.fr}', 114, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('canard', 'Le Canard enchaîné', 'testata', '{lecanardenchaine.fr}', 115, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('courrier', 'Courrier international', 'testata', '{courrierinternational.com}', 116, '{auto,archivio,wayback,gdelt}', 'francesi'),
  ('abc', 'ABC', 'testata', '{abc.es}', 121, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('eldiarioes', 'elDiario.es', 'testata', '{eldiario.es}', 122, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('20minutoses', '20minutos', 'testata', '{20minutos.es}', 123, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('elespanol', 'El Español', 'testata', '{elespanol.com}', 124, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('publico', 'Público', 'testata', '{publico.es}', 125, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('libertaddigital', 'Libertad Digital', 'testata', '{libertaddigital.com}', 126, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('okdiario', 'OkDiario', 'testata', '{okdiario.com}', 127, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('efe', 'Agencia EFE', 'testata', '{efe.com}', 128, '{auto,archivio,ricerca,wayback,gdelt}', 'spagnole'),
  ('europapress', 'Europa Press', 'testata', '{europapress.es}', 129, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('ara', 'Ara', 'testata', '{ara.cat}', 130, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('elconfidencial', 'El Confidencial', 'testata', '{elconfidencial.com}', 131, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('larazon', 'La Razón', 'testata', '{larazon.es}', 132, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('diariovasco', 'El Diario Vasco', 'testata', '{diariovasco.com}', 133, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('elcorreo', 'El Correo', 'testata', '{elcorreo.com}', 134, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('ideal', 'Ideal', 'testata', '{ideal.es}', 135, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('surinenglish', 'Sur in English', 'testata', '{surinenglish.com}', 136, '{auto,archivio,wayback,gdelt}', 'spagnole'),
  ('diariosur', 'Diario Sur', 'testata', '{diariosur.es}', 137, '{auto,archivio,wayback,gdelt}', 'spagnole')
on conflict (chiave) do nothing;

-- rassegna e YouTube restano in fondo all'elenco
update public.stato_testate set ordine = 200 where chiave = 'rassegna';
update public.stato_testate set ordine = 210 where chiave = 'youtube';

-- fonti degli indirizzi e gruppo di tutte le testate attive, dal JSON del motore 1.16
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
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'napoli' where chiave = 'tuttonapoli';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'napoli' where chiave = 'calcionapoli24';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'napoli' where chiave = 'areanapoli';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'napoli' where chiave = 'calcionapoli1926';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'napoli' where chiave = 'spazionapoli';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'napoli' where chiave = 'ilnapolista';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'elnacional';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'ultimasnoticias';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'eldiario';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = '2001online';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'correodelorinoco';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'diariovea';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'elpitazo';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'runrunes';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'cronicauno';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'elestimulo';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'caraotadigital';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'informe21';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'avn';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'telesur';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'venezuelanalysis';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'caracaschronicles';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'elcarabobeno';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'venezuela' where chiave = 'primicia';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'ign';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'ignitalia';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'eurogamer';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'polygon';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'kotaku';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'pcgamer';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'rockpapershotgun';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamesradar';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gameinformer';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'vgc';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'thegamer';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamerant';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'multiplayer';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'everyeye';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'spaziogames';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamereactor';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamesource';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamesindustry';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamedeveloper';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'eurogameres';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'ignespana';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'gamereactores';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = '3djuegos';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'vandal';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'hobbyconsolas';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'pushsquare';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'purexbox';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'videogiochi' where chiave = 'nintendolife';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lemonde';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lefigaro';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = '20minutesfr';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'franceinfo';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'bfmtv';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lci';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'cnews';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'france24';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'latribune';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'humanite';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lacroix';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lobs';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'lexpress';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'mediapart';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'canard';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'francesi' where chiave = 'courrier';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'abc';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'eldiarioes';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = '20minutoses';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'elespanol';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'publico';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'libertaddigital';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'okdiario';
update public.stato_testate set fonti = '{auto,archivio,ricerca,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'efe';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'europapress';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'ara';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'elconfidencial';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'larazon';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'diariovasco';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'elcorreo';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'ideal';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'surinenglish';
update public.stato_testate set fonti = '{auto,archivio,wayback,gdelt}', gruppo = 'spagnole' where chiave = 'diariosur';

-- -----------------------------------------------------------------------------
-- Tempo illimitato (predefinito): alla fine di ogni parte, se l'estrazione non è finita,
-- la piattaforma ne accoda da sola la continuazione dal punto in cui si era fermata.
-- -----------------------------------------------------------------------------
alter table public.impostazioni add column if not exists tempo_illimitato boolean not null default true;
alter table public.impostazioni add column if not exists max_parti integer not null default 40 check (max_parti between 1 and 200);
grant update (tempo_illimitato, max_parti) on public.impostazioni to authenticated;
alter table public.estrazioni add column if not exists parte integer not null default 1 check (parte between 1 and 1000);

-- continuazione automatica: la chiama solo il workflow (service_role) a fine parte
create or replace function public.continua_estrazione(p_id uuid, p_fonte text default null, p_parametri jsonb default null)
returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  r public.estrazioni;
  imp public.impostazioni;
  nuova uuid;
begin
  select * into imp from public.impostazioni where id;
  select * into r from public.estrazioni where id = p_id;
  if not found or r.stato <> 'interrotta' or r.utente is null or r.richiesta = 'ferma'
     or not imp.tempo_illimitato or r.parte >= imp.max_parti then
    return null;
  end if;
  if exists (select 1 from public.estrazioni where riprende_da = p_id and stato not in ('errore', 'annullata')) then
    return null;
  end if;
  insert into public.estrazioni (utente, fonte, modalita, parametri, riprende_da, parte)
  values (r.utente, coalesce(p_fonte, r.fonte), r.modalita, coalesce(p_parametri, r.parametri), p_id, r.parte + 1)
  returning id into nuova;
  return nuova;
end;
$$;
revoke execute on function public.continua_estrazione(uuid, text, jsonb) from public, anon, authenticated;
grant execute on function public.continua_estrazione(uuid, text, jsonb) to service_role;

-- le continuazioni conservano il numero di parte (il trigger di validazione non lo tocca)
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
    'parametri', r.parametri, 'riprende_da', r.riprende_da, 'parte', r.parte,
    'tempo_max_minuti', imp.tempo_max_minuti, 'tempo_illimitato', imp.tempo_illimitato,
    'yt_max_durata_minuti', imp.yt_max_durata_minuti, 'pausa', imp.pausa_secondi);
end;
$$;
revoke execute on function public.inizia_estrazione(uuid, bigint) from public, anon, authenticated;
grant execute on function public.inizia_estrazione(uuid, bigint) to service_role;
