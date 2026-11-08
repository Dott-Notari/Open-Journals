import Accesso from '@/components/Accesso';
import Entrata from '@/components/Entrata';
import LogoFonte from '@/components/LogoFonte';

export const metadata = { title: 'Accesso' };

export default function PaginaAccesso() {
  return (
    <main id="contenuto" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '48px 24px' }}>
      <Entrata className="riga" style={{ gap: 48, maxWidth: 1040, width: '100%', alignItems: 'center' }}>
        <div style={{ flex: '999 1 420px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          <LogoFonte chiave="unisa" nome="Università degli Studi di Salerno" altezza={64} />
          <h1 className="titolo" style={{ fontSize: 'clamp(2.5rem, 6vw, 4.5rem)' }}>Dai giornali<br />al corpus.</h1>
          <p className="sottotitolo">Scraper didattico delle testate per il corso di Sociologia della comunicazione interculturale. Accesso riservato agli studenti approvati dal docente.</p>
          <p className="tenue" style={{ margin: 0 }}>Responsabili scientifici: Vincenzo Esposito e Francesco Notari</p>
        </div>
        <Accesso />
      </Entrata>
    </main>
  );
}
