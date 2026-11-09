import { ArrowRight, LoaderCircle } from 'lucide-react';

// Barra d'azione sospesa in fondo al modulo.
export default function Azioni({ sintesi, invio, errore }) {
  return (
    <>
      <div aria-live="polite">{errore && <p className="avviso errore">{errore}</p>}</div>
      <div className="azioni vetro">
        <span className="tenue" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>{sintesi}</span>
        <button type="submit" className="pulsante" disabled={invio}>
          {invio ? <LoaderCircle size={19} className="gira" aria-hidden="true" /> : null}
          {invio ? 'Avvio…' : 'Avvia'}{!invio && <ArrowRight size={19} aria-hidden="true" />}
        </button>
      </div>
    </>
  );
}
