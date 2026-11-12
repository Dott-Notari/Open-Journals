import Accesso from '@/components/Accesso';
import Ingresso from '@/components/Ingresso';
import { Completo } from '@/components/Logo';

export const metadata = { title: 'Accesso' };

export default function PaginaAccesso() {
  return (
    <main id="contenuto" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '40px 20px' }}>
      <Ingresso style={{ display: 'flex', flexWrap: 'wrap', gap: '40px 64px', alignItems: 'center', justifyContent: 'center', maxWidth: 1100, width: '100%' }}>
        <div style={{ flex: '1 1 420px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          <h1 data-logo="" style={{ margin: 0 }}><Completo className="logo-hero" /></h1>
          <p data-segue=""><span className="spaziato">Sociologia della comunicazione interculturale</span><br />
            <span className="tenue">Responsabili scientifici: Vincenzo Esposito, Francesco Notari</span></p>
        </div>
        <div data-segue=""><Accesso /></div>
      </Ingresso>
    </main>
  );
}
