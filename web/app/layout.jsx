import { headers } from 'next/headers';
import '@fontsource-variable/newsreader/standard.css';
import '@fontsource-variable/newsreader/standard-italic.css';
import '@fontsource-variable/bodoni-moda/opsz.css';
import '@fontsource-variable/bodoni-moda/opsz-italic.css';
import './globals.css';
import Linee from '@/components/Linee';
import Nav from '@/components/Nav';
import Attesa from '@/components/Attesa';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = {
  title: { default: "Open Journals", template: "%s · Open Journals" },
  icons: { icon: '/loghi/unisa.webp' },
  robots: { index: false, follow: false },
};
export const viewport = {
  width: 'device-width', initialScale: 1, viewportFit: 'cover',
  themeColor: [{ media: '(prefers-color-scheme: light)', color: '#EEF1F5' }, { media: '(prefers-color-scheme: dark)', color: '#08111C' }],
};

// tema e pausa salvati, applicati prima del primo disegno
const preferenze = "try{var d=document.documentElement,t=localStorage.getItem('st.tema');if(t)d.dataset.tema=t;if(localStorage.getItem('st.pausa'))d.setAttribute('data-pausa','')}catch(e){}";

export default async function Radice({ children }) {
  const nonce = (await headers()).get('x-nonce') ?? undefined;
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const { data: profilo } = user ? await sb.from('profiles').select('ruolo,approvato').eq('id', user.id).single() : { data: null };
  return (
    <html lang="it" suppressHydrationWarning>
      <head><script nonce={nonce} dangerouslySetInnerHTML={{ __html: preferenze }} /></head>
      <body>
        <a className="salta" href="#contenuto">Vai al contenuto</a>
        <Linee />
        {profilo && !profilo.approvato ? <Attesa email={user.email} /> : (
          <>
            {profilo && <Nav docente={profilo.ruolo === 'docente'} />}
            {children}
          </>
        )}
      </body>
    </html>
  );
}
