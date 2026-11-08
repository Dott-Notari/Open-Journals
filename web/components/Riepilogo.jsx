import { Rocket, LoaderCircle } from 'lucide-react';

export default function Riepilogo({ righe, nota, invio, errore, attive }) {
  return (
    <aside className="vetro" style={{ flex: '1 1 300px', padding: 24, display: 'flex', flexDirection: 'column', gap: 16, position: 'sticky', top: 96 }}>
      <h2 style={{ fontSize: '1.15rem' }}>Riepilogo</h2>
      <dl style={{ margin: 0, display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px' }}>
        {righe.map(([k, v]) => [<dt key={k} className="tenue">{k}</dt>, <dd key={k + 'v'} style={{ margin: 0 }}>{v}</dd>])}
      </dl>
      <p className="avviso blu" style={{ margin: 0 }}>{nota}</p>
      <div aria-live="polite">{errore && <p className="avviso errore" style={{ margin: 0 }}>{errore}</p>}</div>
      <button type="submit" form="modulo" className="pulsante" disabled={invio}>
        {invio ? <LoaderCircle size={20} className="gira" aria-hidden="true" /> : <Rocket size={20} aria-hidden="true" />}
        {invio ? 'Avvio in corso…' : 'Avvia estrazione'}
      </button>
      <span className="aiuto">{attive}</span>
    </aside>
  );
}
