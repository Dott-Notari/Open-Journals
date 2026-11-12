import { headers } from 'next/headers';
import '@fontsource-variable/outfit';
import './globals.css';
import Linee from '@/components/Linee';
import Nav from '@/components/Nav';
import Attesa from '@/components/Attesa';
import { supabaseServer } from '@/lib/supabase-server';

export const metadata = {
  title: { default: "Open New Media", template: "%s · Open New Media" },
  icons: { icon: [{ url: '/favicon.ico', sizes: '48x48' }, { url: '/favicon.svg', type: 'image/svg+xml' }], apple: '/apple-touch-icon.png' },
  manifest: '/site.webmanifest',
  openGraph: { title: 'Open New Media', images: ['/og-image-chiaro.png'] },
  robots: { index: false, follow: false },
};
export const viewport = {
  width: 'device-width', initialScale: 1, viewportFit: 'cover',
  themeColor: [{ media: '(prefers-color-scheme: light)', color: '#F4F4F2' }, { media: '(prefers-color-scheme: dark)', color: '#111111' }],
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
