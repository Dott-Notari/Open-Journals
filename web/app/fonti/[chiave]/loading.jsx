// Scheletro della pagina di una fonte: compare subito al clic, mentre il server legge stato e limiti.
export default function Caricamento() {
  return (
    <main id="contenuto" className="pagina" style={{ maxWidth: 920, gap: 28 }} aria-busy="true">
      <span className="pulsante compatto secondario scheletro" style={{ width: 96 }} aria-hidden="true" />
      <div className="riga" style={{ gap: 22 }}>
        <div className="vetro" style={{ padding: 10 }}><div className="scheletro" style={{ width: 200, height: 112, borderRadius: 16 }} /></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <span className="scheletro" style={{ width: 260, height: 40, borderRadius: 12 }} />
          <span className="scheletro" style={{ width: 120, height: 16, borderRadius: 8 }} />
        </div>
      </div>
      <div className="vetro" style={{ height: 420, borderRadius: 28 }} />
      <p className="salta-lettura" role="status">Caricamento della fonte…</p>
    </main>
  );
}
