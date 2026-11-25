'use client';
import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { oggi } from '@/lib/fonti';

const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
const GIORNI = ['lu', 'ma', 'me', 'gi', 've', 'sa', 'do'];
const lungo = new Intl.DateTimeFormat('it-IT', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

// Le date viaggiano come testo AAAA-MM-GG, lo stesso formato del database: niente fusi orari di mezzo.
const iso = (a, m, g) => `${a}-${String(m + 1).padStart(2, '0')}-${String(g).padStart(2, '0')}`;
const parti = (s) => { const [a, m, g] = s.split('-').map(Number); return [a, m - 1, g]; };
const giorniNel = (a, m) => new Date(Date.UTC(a, m + 1, 0)).getUTCDate();
const sposta = (s, n) => new Date(Date.parse(s) + n * 864e5).toISOString().slice(0, 10);
export const formatoLungo = (s) => (s ? lungo.format(new Date(s)) : '');

// Campo data con calendario di vetro. min e max sono i limiti della fonte: il calendario si apre
// sull'ultimo mese disponibile e non lascia scegliere i giorni fuori dall'archivio.
export default function CampoData({ name, etichetta, value, onChange, min, max, required, aiuto, piede }) {
  const [aperto, setAperto] = useState(false);
  const [vista, setVista] = useState('giorni');
  const [mese, setMese] = useState(null); // [anno, mese] mostrato
  const [fuoco, setFuoco] = useState(null);
  const [pos, setPos] = useState(null);
  const [manca, setManca] = useState(false);
  const pulsante = useRef(null), pannello = useRef(null), griglia = useRef(null);
  const id = useId();
  const fuori = (s) => (min && s < min) || (max && s > max);

  function apri() {
    const base = value || (max && max < oggi() ? max : oggi());
    const partenza = fuori(base) ? (min && base < min ? min : max) : base;
    const [a, m] = parti(partenza);
    setMese([a, m]); setFuoco(partenza); setVista('giorni'); setAperto(true);
  }
  function scegli(s) { onChange(s); setManca(false); setAperto(false); pulsante.current?.focus(); }

  const colloca = () => {
    const b = pulsante.current.getBoundingClientRect();
    const w = pannello.current?.offsetWidth ?? 320, h = pannello.current?.offsetHeight ?? 380;
    const sotto = b.bottom + 8 + h < innerHeight || b.top < h + 16;
    setPos({ left: Math.max(12, Math.min(b.left, innerWidth - w - 12)), top: sotto ? b.bottom + 8 : b.top - 8 - h, origine: sotto ? 'top' : 'bottom' });
  };
  useLayoutEffect(() => { if (aperto) colloca(); }, [aperto, vista]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!aperto) return;
    const via = (e) => { if (!pannello.current?.contains(e.target) && !pulsante.current.contains(e.target)) setAperto(false); };
    const esc = (e) => { if (e.key === 'Escape') { setAperto(false); pulsante.current.focus(); } };
    document.addEventListener('pointerdown', via); document.addEventListener('keydown', esc);
    addEventListener('scroll', colloca, { passive: true, capture: true }); addEventListener('resize', colloca);
    return () => {
      document.removeEventListener('pointerdown', via); document.removeEventListener('keydown', esc);
      removeEventListener('scroll', colloca, { capture: true }); removeEventListener('resize', colloca);
    };
  }, [aperto]); // eslint-disable-line react-hooks/exhaustive-deps
  // il giorno attivo prende il fuoco, così le frecce funzionano subito
  useEffect(() => { if (aperto && vista === 'giorni') griglia.current?.querySelector('[data-fuoco="1"]')?.focus(); }, [aperto, vista, fuoco]);

  function tasti(e) {
    const passi = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
    if (!passi || !fuoco) return;
    e.preventDefault();
    let n = sposta(fuoco, passi);
    if (fuori(n)) return;
    const [a, m] = parti(n);
    setMese([a, m]); setFuoco(n);
  }

  const [aMin] = min ? parti(min) : [1996];
  const [aMax] = parti(max || oggi());
  let corpo = null;
  if (aperto && mese) {
    const [a, m] = mese;
    const primoMese = min && iso(a, m, 1) <= min, ultimoMese = max && iso(a, m, giorniNel(a, m)) >= max;
    if (vista === 'anni') {
      const anni = []; for (let x = aMax; x >= aMin; x--) anni.push(x);
      corpo = (
        <div className="cal-scelte anni" role="listbox" aria-label="Anno">
          {anni.map((x) => <button key={x} type="button" role="option" aria-selected={x === a} onClick={() => { setMese([x, m]); setVista('mesi'); }}>{x}</button>)}
        </div>
      );
    } else if (vista === 'mesi') {
      corpo = (
        <div className="cal-scelte" role="listbox" aria-label={`Mese del ${a}`}>
          {MESI.map((nome, i) => {
            const vuoto = (min && iso(a, i, giorniNel(a, i)) < min) || (max && iso(a, i, 1) > max);
            return <button key={nome} type="button" role="option" aria-selected={i === m} disabled={vuoto} onClick={() => { setMese([a, i]); setVista('giorni'); }}>{nome.slice(0, 3)}</button>;
          })}
        </div>
      );
    } else {
      const vuote = (new Date(Date.UTC(a, m, 1)).getUTCDay() + 6) % 7;
      const celle = [...Array(vuote).fill(null), ...Array.from({ length: giorniNel(a, m) }, (_, i) => iso(a, m, i + 1))];
      const attivo = fuoco && parti(fuoco)[1] === m && parti(fuoco)[0] === a ? fuoco : celle.find((s) => s && !fuori(s));
      corpo = (
        <div ref={griglia} className="cal-giorni" role="grid" aria-label={`${MESI[m]} ${a}`} onKeyDown={tasti}>
          {GIORNI.map((g) => <span key={g} className="cal-intestazione" aria-hidden="true">{g}</span>)}
          {celle.map((s, i) => s === null ? <span key={`v${i}`} /> : (
            <button key={s} type="button" disabled={fuori(s)} aria-pressed={s === value} aria-label={formatoLungo(s)}
              data-oggi={s === oggi() ? '1' : undefined} data-fuoco={s === attivo ? '1' : undefined} tabIndex={s === attivo ? 0 : -1}
              onClick={() => scegli(s)}>{parti(s)[2]}</button>
          ))}
        </div>
      );
    }
    corpo = (
      <div id={id} ref={pannello} role="dialog" aria-label={`Scegli: ${etichetta}`} className="calendario vetro"
        style={{ left: pos?.left ?? -9999, top: pos?.top ?? 0, transformOrigin: pos?.origine }}>
        <div className="cal-testa">
          <button type="button" className="cal-titolo" onClick={() => setVista(vista === 'giorni' ? 'anni' : 'giorni')} aria-label="Cambia mese e anno">
            {vista === 'anni' ? 'Scegli l’anno' : vista === 'mesi' ? a : `${MESI[m]} ${a}`}
          </button>
          {vista === 'giorni' && (
            <span className="riga" style={{ gap: 2, flexWrap: 'nowrap' }}>
              <button type="button" className="cal-freccia" aria-label="Mese precedente" disabled={!!primoMese} onClick={() => setMese(m ? [a, m - 1] : [a - 1, 11])}><ChevronLeft size={18} aria-hidden="true" /></button>
              <button type="button" className="cal-freccia" aria-label="Mese successivo" disabled={!!ultimoMese} onClick={() => setMese(m === 11 ? [a + 1, 0] : [a, m + 1])}><ChevronRight size={18} aria-hidden="true" /></button>
            </span>
          )}
        </div>
        {corpo}
        <div className="cal-piede">
          {min && <button type="button" onClick={() => scegli(min)}>Primo giorno</button>}
          <button type="button" onClick={() => scegli(max && max < oggi() ? max : oggi())}>{max && max < oggi() ? 'Ultimo giorno' : 'Oggi'}</button>
          {value && !required && <button type="button" onClick={() => scegli('')}>Cancella</button>}
        </div>
        {piede && <p className="cal-nota">{piede}</p>}
      </div>
    );
  }

  return (
    <div className="etichetta campo-data">
      <span id={`${id}-et`}>{etichetta}</span>
      <span style={{ position: 'relative' }}>
        <button ref={pulsante} type="button" className="campo scelta-data" aria-haspopup="dialog" aria-expanded={aperto} aria-invalid={manca || undefined}
          aria-labelledby={`${id}-et ${id}-val`} onClick={() => (aperto ? setAperto(false) : apri())}>
          <span id={`${id}-val`} className={value ? undefined : 'tenue'}>{value ? formatoLungo(value) : 'Scegli un giorno'}</span>
          <CalendarDays size={18} aria-hidden="true" />
        </button>
        {/* campo vero per il modulo: porta il valore e il controllo «obbligatorio» del browser */}
        <input name={name} value={value} required={required} onChange={() => {}} tabIndex={-1} aria-hidden="true" className="data-nascosta"
          onInvalid={(e) => { e.preventDefault(); setManca(true); }} />
      </span>
      {manca && <span className="aiuto" style={{ color: 'var(--errore)' }} role="alert">Scegli un giorno.</span>}
      {aiuto && <span className="aiuto">{aiuto}</span>}
      {aperto && createPortal(corpo, document.body)}
    </div>
  );
}
