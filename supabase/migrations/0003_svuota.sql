-- =============================================================================
-- Aggiornamento 0003: lo studente può svuotare le proprie estrazioni concluse.
-- I file vengono cancellati e la riga sparisce dalla sua pagina, ma resta nel
-- registro del docente. La cancellazione dei file la fa la route /api/svuota
-- con la chiave di servizio, dopo aver controllato che l'estrazione sia sua.
-- =============================================================================
alter table public.estrazioni add column if not exists nascosta boolean not null default false;
create index if not exists estrazioni_visibili_idx on public.estrazioni (utente, nascosta, creata_il desc);
