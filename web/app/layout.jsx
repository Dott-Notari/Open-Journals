import { headers } from 'next/headers';
import './globals.css';
import Fondale from '@/components/Fondale';
import Nav from '@/components/Nav';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = {
  title: 'Scraper didattico delle testate',
  description: 'Corpora giornalistici e video per il corso di Sociologia della comunicazione interculturale.',
  robots: { index: false, follow: false },
};
export const viewport = { themeColor: '#EEF2F7' };

export default async function Radice({ children }) {
  await headers(); // rendering dinamico: serve per il nonce della Content-Security-Policy
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const { data: profilo } = user
    ? await sb.from('profiles').select('ruolo,approvato').eq('id', user.id).single()
    : { data: null };
  return (
    <html lang="it">
      <body>
        <a className="salta" href="#contenuto">Vai al contenuto</a>
        <Fondale />
        {profilo && <Nav docente={profilo.ruolo === 'docente'} />}
        {profilo && !profilo.approvato && (
          <p className="avviso giallo vetro" role="status" style={{ position: 'fixed', bottom: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 40, margin: 0, width: 'min(640px, calc(100% - 24px))' }}>
            Account in attesa di approvazione: potrai avviare le estrazioni quando il docente lo approva.
          </p>
        )}
        {children}
      </body>
    </html>
  );
}
