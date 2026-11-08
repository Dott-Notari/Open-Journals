-- Da eseguire nell'editor SQL di Supabase DOPO che il docente si è registrato
-- dalla piattaforma (o è stato creato da Authentication > Users).
-- Sostituire l'indirizzo con quello usato per la registrazione.
update public.profiles
   set ruolo = 'docente', approvato = true, approvato_il = now()
 where email = 'indirizzo.docente@unisa.it';

-- Controllo: deve restituire una riga con ruolo «docente» e approvato «true».
select email, ruolo, approvato from public.profiles where ruolo = 'docente';

-- Facoltativo: limitare la registrazione ai domini istituzionali.
-- update public.impostazioni set domini_email_ammessi = '{unisa.it,studenti.unisa.it}';
