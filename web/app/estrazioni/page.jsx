import Estrazioni from '@/components/Estrazioni';
import Entrata from '@/components/Entrata';

export const metadata = { title: 'Le mie estrazioni' };

export default function PaginaEstrazioni() {
  return (
    <main id="contenuto" className="pagina" style={{ gap: 28 }}>
      <Entrata style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h1 className="titolo-2" style={{ fontSize: 'clamp(2.2rem, 5vw, 3.4rem)' }}>Le mie estrazioni</h1>
        <p className="tenue" style={{ margin: 0 }}>Lo stato si aggiorna da solo ogni 10 secondi.</p>
      </Entrata>
      <Estrazioni />
    </main>
  );
}
