import Estrazioni from '@/components/Estrazioni';

export const metadata = { title: 'Estrazioni' };

export default function PaginaEstrazioni() {
  return (
    <main id="contenuto" className="pagina" style={{ maxWidth: 980, gap: 24 }}>
      <h1 className="titolo-2">Estrazioni</h1>
      <Estrazioni />
    </main>
  );
}
