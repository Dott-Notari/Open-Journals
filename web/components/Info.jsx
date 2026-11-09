'use client';
import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Info as Icona } from 'lucide-react';

// Nota su richiesta. Vive in un livello sopra la pagina (portale), così nessun riquadro la copre;
// si posiziona sotto l'icona o sopra se manca spazio, e si chiude con Esc o cliccando fuori.
export default function Info({ children, etichetta = 'Informazioni' }) {
  const [aperta, setAperta] = useState(false);
  const [pos, setPos] = useState(null);
  const pulsante = useRef(null), nota = useRef(null);
  const id = useId();

  const colloca = () => {
    const b = pulsante.current.getBoundingClientRect();
    // misure senza trasformazioni: l'animazione di comparsa non deve falsarle
    const n = nota.current ? { width: nota.current.offsetWidth, height: nota.current.offsetHeight } : { width: 320, height: 120 };
    const sotto = b.bottom + 8 + n.height < innerHeight;
    setPos({
      left: Math.max(12, Math.min(b.left - 8, innerWidth - n.width - 12)),
      top: sotto ? b.bottom + 8 : b.top - 8 - n.height,
      origine: sotto ? 'top left' : 'bottom left',
    });
  };
  useLayoutEffect(() => { if (aperta) colloca(); }, [aperta]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!aperta) return;
    const fuori = (e) => { if (!nota.current?.contains(e.target) && !pulsante.current.contains(e.target)) setAperta(false); };
    const esc = (e) => { if (e.key === 'Escape') { setAperta(false); pulsante.current.focus(); } };
    const segui = () => colloca();
    document.addEventListener('pointerdown', fuori);
    document.addEventListener('keydown', esc);
    addEventListener('scroll', segui, { passive: true, capture: true });
    addEventListener('resize', segui);
    return () => {
      document.removeEventListener('pointerdown', fuori); document.removeEventListener('keydown', esc);
      removeEventListener('scroll', segui, { capture: true }); removeEventListener('resize', segui);
    };
  }, [aperta]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <span className="info">
      <button ref={pulsante} type="button" aria-label={etichetta} aria-expanded={aperta} aria-controls={aperta ? id : undefined} onClick={() => setAperta((a) => !a)}>
        <Icona size={17} aria-hidden="true" />
      </button>
      {aperta && createPortal(
        <span id={id} ref={nota} role="note" className="nota vetro"
          style={{ left: pos?.left ?? -9999, top: pos?.top ?? 0, transformOrigin: pos?.origine }}>{children}</span>,
        document.body)}
    </span>
  );
}
