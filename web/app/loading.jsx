// Mentre il server prepara una pagina: una barra sottile, al posto del contenuto precedente.
export default function Caricamento() {
  return (
    <main id="contenuto" className="pagina" aria-busy="true" style={{ minHeight: '60vh' }}>
      <div className="barra" style={{ maxWidth: 240 }}><i /></div>
      <p className="salta-lettura" role="status">Caricamento…</p>
    </main>
  );
}
