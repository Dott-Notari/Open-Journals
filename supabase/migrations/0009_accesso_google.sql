-- Accesso con Google: il nome arriva dai metadati di Google (full_name o name) invece che dal modulo.
-- Le regole restano quelle di sempre: registrazioni aperte, domini ammessi, approvazione del docente.
-- Si può rieseguire senza danni.
create or replace function public.gestisci_nuovo_utente() returns trigger
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
  values (new.id, new.email, left(coalesce(
    nullif(btrim(new.raw_user_meta_data ->> 'nome'), ''),
    nullif(btrim(new.raw_user_meta_data ->> 'full_name'), ''),
    nullif(btrim(new.raw_user_meta_data ->> 'name'), '')), 120));
  return new;
end;
$$;
