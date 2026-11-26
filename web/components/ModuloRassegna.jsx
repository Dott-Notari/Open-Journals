'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, Minus } from 'lucide-react';
import Segmenti from './Segmenti';
import Azioni from './Azioni';
import Info from './Info';
import { inviaEstrazione, lista } from '@/lib/invia';
import { GRUPPI, fuoriArchivio, oggi } from '@/lib/fonti';
import CampoData from './CampoData';

const FORMATI = [['docx', 'Word'], ['txt', 'Testo'], ['html', 'HTML'], ['xlsx', 'Excel'], ['jsonl', 'JSONL'], ['tlab', 'T-LAB']];
const LINGUE = { it: 'italiano', es: 'spagnolo', en: 'inglese', fr: 'francese', ca: 'catalano' };

// Casella del gruppo: piena se tutte le testate sono scelte, a metà se solo alcune.
function CasellaGruppo({ stato, onCambio, etichetta }) {
  const el = useRef(null);
  useEffect(() => { el.current.indeterminate = stato === 'parte'; }, [stato]);
  return (
    <label className="casella-gruppo">
      <input ref={el} type="checkbox" checked={stato === 'tutte'} onChange={onCambio} aria-label={etichetta} />
      <span aria-hidden="true">{stato === 'tutte' ? <Check size={15} strokeWidth={3} /> : stato === 'parte' ? <Minus size={15} strokeWidth={3} /> : null}</span>
      Tutte
    </label>
  );
}

export default function ModuloRassegna({ testate, iniziali, minuti, illimitato }) {
  const router = useRouter();
  const [scelte, setScelte] = useState(() => new Set(iniziali));
  const [dal, setDal] = useState('');
  const [al, setAl] = useState('');
  const [tutte, setTutte] = useState('no');
  const [dove, setDove] = useState('testo');
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState('');

  const elenco = testate.filter((f) => scelte.has(f.chiave));
  const conRicerca = elenco.filter((f) => f.ricerca).length;
  const lingue = [...new Set(elenco.map((f) => f.lingua))];
  const fuori = elenco.map((f) => [f, fuoriArchivio(f, dal, al)]).filter(([, m]) => m);

  const cambia = (chiavi, accendi) => setScelte((s) => {
    const n = new Set(s);
    chiavi.forEach((k) => (accendi ? n.add(k) : n.delete(k)));
    return n;
  });

  async function invia(e) {
    e.preventDefault();
    if (!elenco.length) { setErrore('Scegli almeno una testata.'); return; }
    const d = new FormData(e.currentTarget);
    const p = { dal: d.get('dal'), al: d.get('al') };
    const parole = lista(d.get('parole'));
    if (parole.length) Object.assign(p, { parole, tutte: tutte === 'si', cerca_in: dove });
    p.formati = d.getAll('formati');
    if (d.get('max')) p.max_articoli = Number(d.get('max'));
    const ricerca = d.get('usa_ricerca') === 'on';
    setInvio(true); setErrore('');
    // con una sola testata è un'estrazione normale, con la sua coda
    const msg = elenco.length === 1
      ? await inviaEstrazione(elenco[0].chiave, 'data', { ...p, fonte: 'auto', ...(elenco[0].ricerca ? { usa_ricerca: ricerca } : {}) })
      : await inviaEstrazione('rassegna', 'data', { ...p, usa_ricerca: ricerca, testate: elenco.map((f) => f.chiave) });
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  const sintesi = !elenco.length ? 'Nessuna testata scelta'
    : elenco.length === 1 ? `${elenco[0].nome}: con una sola testata parte un'estrazione normale`
    : `${elenco.length} testate, ${illimitato ? 'senza limite di tempo' : `${minuti} minuti al massimo in tutto`}`;

  return (
    <form onSubmit={invia} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="modulo vetro">
        <fieldset>
          <legend>Testate <Info etichetta="Quali testate si possono scegliere">
            Ci sono le testate che la piattaforma scarica online. Quelle in grigio, per ora, si scaricano solo con lo scraper installato sul computer.
          </Info><span className="conta">{elenco.length}</span></legend>
          {GRUPPI.map(([g, titolo]) => {
            const membri = testate.filter((f) => f.gruppo === g);
            const libere = membri.filter((f) => f.disponibile).map((f) => f.chiave);
            if (!membri.length) return null;
            const quante = libere.filter((k) => scelte.has(k)).length;
            const stato = !quante ? 'nessuna' : quante === libere.length ? 'tutte' : 'parte';
            return (
              <div key={g} className="gruppo-scelta">
                <div className="riga" style={{ justifyContent: 'space-between' }}>
                  <span className="spaziato tenue">{titolo}</span>
                  {libere.length > 1 && <CasellaGruppo stato={stato} etichetta={`Tutte le ${titolo.toLowerCase()}`} onCambio={() => cambia(libere, stato !== 'tutte')} />}
                </div>
                <div className="gettoni">
                  {membri.map((f) => (
                    <label key={f.chiave} className="gettone" aria-disabled={!f.disponibile || undefined} title={f.disponibile ? undefined : 'Solo con lo scraper sul computer'}>
                      <input type="checkbox" checked={scelte.has(f.chiave)} disabled={!f.disponibile} onChange={(e) => cambia([f.chiave], e.target.checked)} />
                      <span translate="no">{f.nome}</span>
                    </label>
                  ))}
                </div>
              </div>
            );
          })}
        </fieldset>

        <fieldset>
          <legend>Periodo <Info etichetta="Periodo e copertura">
            Ogni testata viene cercata nello stesso periodo, ciascuna con il suo metodo: per alcune l&apos;archivio è completo, per altre arriva solo a certe date. L&apos;esito di ognuna si legge in scheda_rassegna.txt.
          </Info></legend>
          <div className="due">
            <CampoData name="dal" etichetta="Dal" required value={dal} onChange={setDal} max={al || oggi()} />
            <CampoData name="al" etichetta="Al" required value={al} onChange={setAl} min={dal || null} max={oggi()} />
          </div>
          {fuori.length > 0 && (
            <div className="avviso giallo">
              <p style={{ margin: '0 0 6px' }}>Per {fuori.length === 1 ? 'questa testata' : 'queste testate'} il periodo esce da quello che l&apos;archivio copre, quindi potrebbero arrivare pochi articoli:</p>
              <ul style={{ margin: 0, paddingLeft: 18 }}>{fuori.map(([f, m]) => <li key={f.chiave}>{m}</li>)}</ul>
              <p style={{ margin: '6px 0 0' }}>Per arrivare a quelle date fai un&apos;estrazione singola dalla pagina della testata, scegliendo Wayback.</p>
            </div>
          )}
        </fieldset>

        <fieldset>
          <legend>Parole chiave <Info etichetta="Parole chiave nella rassegna">
            Le parole valgono per tutte le testate. L&apos;asterisco tronca la parola: migrant* trova migrante e migranti. Se lasci il campo vuoto arrivano tutti gli articoli del periodo.
          </Info></legend>
          <input className="campo" name="parole" autoComplete="off" aria-label="Parole chiave" placeholder="migrant*, accoglienza…" />
          {lingue.length > 1 && (
            <p className="aiuto">Hai scelto testate in {lingue.map((l) => LINGUE[l] ?? l).join(', ')}: le parole si cercano così come le scrivi, quindi aggiungi anche le traduzioni (migrant*, migrante*, inmigra*).</p>
          )}
          <div className="riga" style={{ gap: 10 }}>
            <Segmenti voci={[['no', 'Almeno una'], ['si', 'Tutte']]} valore={tutte} onCambio={setTutte} etichetta="Corrispondenza" />
            <Segmenti voci={[['testo', 'In tutto il testo'], ['titolo', 'Solo titolo e sommario']]} valore={dove} onCambio={setDove} etichetta="Dove cercare" />
          </div>
          {conRicerca > 0 && (
            <label className="gettone" style={{ alignSelf: 'flex-start' }}>
              <input type="checkbox" name="usa_ricerca" defaultChecked />Usa la ricerca del sito dove c&apos;è ({conRicerca} su {elenco.length})
            </label>
          )}
        </fieldset>

        <fieldset>
          <legend>Formati</legend>
          <div className="gettoni">
            {FORMATI.map(([k, t]) => <label key={k} className="gettone"><input type="checkbox" name="formati" value={k} defaultChecked />{t}</label>)}
          </div>
          <label className="etichetta" style={{ maxWidth: 260 }}>Massimo di articoli per testata
            <input className="campo" type="number" name="max" min={1} inputMode="numeric" placeholder="Tutti" />
          </label>
        </fieldset>
      </div>
      <Azioni invio={invio} errore={errore} sintesi={sintesi} />
    </form>
  );
}
