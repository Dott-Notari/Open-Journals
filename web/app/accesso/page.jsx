import Accesso from '@/components/Accesso';
import Ingresso from '@/components/Ingresso';

export const metadata = { title: 'Accesso' };

export default function PaginaAccesso() {
  return (
    <main id="contenuto" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '40px 20px' }}>
      <Ingresso style={{ display: 'flex', flexWrap: 'wrap', gap: '40px 64px', alignItems: 'center', justifyContent: 'center', maxWidth: 1100, width: '100%' }}>
        <div style={{ flex: '1 1 420px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          <img src="/loghi/unisa.webp" alt="Università degli Studi di Salerno" width={84} height={84} data-segue="" />
          <h1 className="titolo">
            <span className="maschera"><span>Scraper delle testate</span></span>
            <span className="maschera"><span className="tenue" style={{ fontStyle: 'italic', fontWeight: 400 }}>giornalistiche</span></span>
          </h1>
          <p data-segue="">Sociologia della comunicazione interculturale<br />
            <span className="tenue">Responsabili scientifici Vincenzo Esposito, Francesco Notari</span></p>
        </div>
        <div data-segue=""><Accesso /></div>
      </Ingresso>
    </main>
  );
}
