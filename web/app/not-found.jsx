import Link from 'next/link';

export default function NonTrovata() {
  return (
    <main id="contenuto" className="pagina">
      <h1 className="titolo-2">Pagina non trovata.</h1>
      <Link href="/" className="pulsante" style={{ alignSelf: 'flex-start' }}>Torna alle fonti</Link>
    </main>
  );
}
