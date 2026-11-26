'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { CalendarRange, LayoutList, Link2, History, Newspaper, Lightbulb, Timer } from 'lucide-react';
import Segmenti from './Segmenti';
import Azioni from './Azioni';
import Info from './Info';
import { inviaEstrazione, lista } from '@/lib/invia';
import { FONTI_INDIRIZZI } from '@/lib/guida';
import { fuoriArchivio, limitiDate, giorno } from '@/lib/fonti';
import CampoData from './CampoData';

const MODI = [['data', 'Periodo', CalendarRange], ['elenco', 'Pagina elenco', LayoutList], ['link', 'Link', Link2]];
const FORMATI = [['docx', 'Word'], ['txt', 'Testo'], ['html', 'HTML'], ['xlsx', 'Excel'], ['jsonl', 'JSONL'], ['tlab', 'T-LAB']];
const LINGUE = { en: ' (in inglese)', es: ' (in spagnolo)', fr: ' (in francese)', ca: ' (in catalano)' };
const ESEMPI = { es: 'migrante*, frontera…', en: 'migrant*, border…', fr: 'migrant*, frontière…', ca: 'migrant*, frontera…' };

export default function ModuloTestata({ fonte }) {
  const router = useRouter();
  const g = fonte.guida;
  const [modo, setModo] = useState('data');
  const [indirizzi, setIndirizzi] = useState('auto');
  const [dal, setDal] = useState('');
  const [al, setAl] = useState('');
  const [tutte, setTutte] = useState('no');
  const [dove, setDove] = useState('testo');
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState('');
  const vociIndirizzi = fonte.fonti.filter((k) => k !== 'gdelt').map((k) => [k, FONTI_INDIRIZZI[k][0]]);
  // per SpazioNapoli il 2011-2019 è escluso dal robots.txt anche passando da Wayback
  const wb = fonte.fonti.includes('wayback') && fonte.chiave !== 'spazionapoli';
  const lim = modo === 'data' ? limitiDate(fonte, indirizzi) : { max: limitiDate(fonte).max };
  const notaCal = modo === 'data' && wb && !['wayback', 'gdelt'].includes(indirizzi) && lim.min
    ? `Prima del ${giorno.format(new Date(lim.min))} l'archivio non arriva: per quelle date scegli Wayback qui sotto.` : null;
  const avviso = modo === 'data' && ['auto', 'archivio'].includes(indirizzi) ? fuoriArchivio(fonte, dal, al) : null;

  async function invia(e) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    const p = {};
    if (d.get('dal') || d.get('al')) Object.assign(p, { dal: d.get('dal'), al: d.get('al') });
    if (modo === 'elenco') p.elenco = d.get('elenco').trim();
    if (modo === 'link') p.link = lista(d.get('link'), '\n');
    const parole = lista(d.get('parole'));
    if (parole.length) Object.assign(p, { parole, tutte: tutte === 'si', cerca_in: dove });
    if (modo === 'data') {
      p.fonte = indirizzi;
      if (fonte.ricerca && indirizzi === 'auto') p.usa_ricerca = d.get('usa_ricerca') === 'on';
      if (indirizzi === 'gdelt') p.parole_gdelt = lista(d.get('parole_gdelt'));
    }
    p.formati = d.getAll('formati');
    if (d.get('max')) p.max_articoli = Number(d.get('max'));
    setInvio(true); setErrore('');
    const msg = await inviaEstrazione(fonte.chiave, modo, p);
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  return (
    <form onSubmit={invia} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <details className="vetro" style={{ padding: '14px 20px' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, minHeight: 32 }}>Cosa si può fare con {fonte.nome}</summary>
        <dl className="guida">
          <dt>Per periodo</dt><dd>{g.periodo}</dd>
          <dt>Parole chiave</dt><dd>{g.parole}</dd>
          <dt>Pagina elenco</dt><dd>{g.elenco}</dd>
          <dt>Periodi passati</dt><dd>{g.passato}</dd>
          <dt>Consiglio</dt><dd>{g.consiglio}</dd>
        </dl>
      </details>

      <div className="consigli">
        <p><Lightbulb size={18} aria-hidden="true" /><span>{g.consiglio}</span></p>
        {fonte.lenta && <p><Timer size={18} aria-hidden="true" /><span>{fonte.lenta}</span></p>}
      </div>

      <div className="modulo vetro">
        <fieldset>
          <legend>Ricerca <Info etichetta={`Modalità di ricerca su ${fonte.nome}`}>
            {modo === 'data' ? g.periodo : modo === 'elenco' ? g.elenco : 'Incolla gli indirizzi degli articoli, uno per riga: vengono scaricati così come sono.'}
          </Info></legend>
          <Segmenti voci={MODI} valore={modo} onCambio={setModo} etichetta="Modalità di ricerca" />
          {modo === 'elenco' && (
            <>
              <label className="etichetta">Indirizzo della pagina
                <input className="campo" type="url" name="elenco" required inputMode="url" autoComplete="off" spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
                <span className="aiuto">{g.elenco}</span>
              </label>
              {fonte.primaPagina && <p className="avviso giallo">Di questa testata si legge solo la prima pagina dell&apos;elenco.</p>}
            </>
          )}
          {modo === 'link' && (
            <label className="etichetta">Un link per riga
              <textarea className="campo" name="link" rows={6} required spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
            </label>
          )}
          {modo !== 'link' && (
            <div className="due">
              <CampoData name="dal" etichetta="Dal" required={modo === 'data'} value={dal} onChange={setDal} min={lim.min} max={al || lim.max} piede={notaCal} />
              <CampoData name="al" etichetta="Al" required={modo === 'data'} value={al} onChange={setAl} min={dal || lim.min} max={lim.max} piede={notaCal} />
            </div>
          )}
          {avviso && (
            <div className="avviso giallo riga" style={{ justifyContent: 'space-between' }}>
              <span>{avviso} {wb ? 'Per arrivare a quelle date puoi usare Wayback.' : ''}</span>
              {wb && (
                <button type="button" className="pulsante compatto secondario" onClick={() => setIndirizzi('wayback')}><History size={16} aria-hidden="true" />Usa Wayback</button>
              )}
            </div>
          )}
        </fieldset>

        {modo === 'data' && (
          <fieldset>
            <legend>Da dove prendere gli indirizzi <Info etichetta="Fonti degli indirizzi">
              {FONTI_INDIRIZZI[indirizzi][1]} {indirizzi === 'wayback' ? g.passato : ''}
            </Info></legend>
            <Segmenti voci={vociIndirizzi} valore={indirizzi === 'gdelt' ? '' : indirizzi} onCambio={setIndirizzi} etichetta="Fonte degli indirizzi" />
            {fonte.fonti.includes('gdelt') && (
              <details open={indirizzi === 'gdelt'}>
                <summary style={{ cursor: 'pointer', minHeight: 32 }} className="tenue">Opzioni avanzate</summary>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
                  <label className="gettone" style={{ alignSelf: 'flex-start' }}>
                    <input type="checkbox" checked={indirizzi === 'gdelt'} onChange={(e) => setIndirizzi(e.target.checked ? 'gdelt' : 'auto')} />GDELT, sperimentale
                  </label>
                  <span className="aiuto">{FONTI_INDIRIZZI.gdelt[1]}</span>
                  {indirizzi === 'gdelt' && (
                    <label className="etichetta">Parole in inglese, separate da virgole
                      <input className="campo" name="parole_gdelt" required autoComplete="off" lang="en" placeholder="migrants, asylum…" />
                    </label>
                  )}
                </div>
              </details>
            )}
          </fieldset>
        )}

        <fieldset>
          <legend>Parole chiave{LINGUE[fonte.lingua] ?? ''} <Info etichetta="Come usare le parole chiave">
            {g.parole} L&apos;asterisco tronca la parola: migrant* trova migrante e migranti. Se lasci il campo vuoto arrivano tutti gli articoli.
          </Info></legend>
          <input className="campo" name="parole" autoComplete="off" aria-label="Parole chiave" lang={fonte.lingua} required={modo === 'data' && indirizzi === 'ricerca'} placeholder={ESEMPI[fonte.lingua] ?? 'migrant*, accoglienza…'} />
          <div className="riga" style={{ gap: 10 }}>
            <Segmenti voci={[['no', 'Almeno una'], ['si', 'Tutte']]} valore={tutte} onCambio={setTutte} etichetta="Corrispondenza" />
            <Segmenti voci={[['testo', 'In tutto il testo'], ['titolo', 'Solo titolo e sommario']]} valore={dove} onCambio={setDove} etichetta="Dove cercare" />
          </div>
          {fonte.ricerca && modo === 'data' && indirizzi === 'auto' && (
            <label className="gettone" style={{ alignSelf: 'flex-start' }}><input type="checkbox" name="usa_ricerca" defaultChecked />Usa la ricerca del sito</label>
          )}
        </fieldset>

        <fieldset>
          <legend>Formati</legend>
          <div className="gettoni">
            {FORMATI.map(([k, t]) => <label key={k} className="gettone"><input type="checkbox" name="formati" value={k} defaultChecked />{t}</label>)}
          </div>
          <label className="etichetta" style={{ maxWidth: 240 }}>Numero massimo di articoli
            <input className="campo" type="number" name="max" min={1} inputMode="numeric" placeholder="Tutti" />
          </label>
        </fieldset>
      </div>
      <p className="tenue riga" style={{ gap: 8, fontSize: 14 }}>
        <Newspaper size={16} aria-hidden="true" />La stessa ricerca su più testate insieme?
        <Link href={`/rassegna?testate=${fonte.chiave}`}>Componi una rassegna stampa</Link>
      </p>
      <Azioni invio={invio} errore={errore} sintesi={`${fonte.nome}, ${MODI.find((m) => m[0] === modo)[1].toLowerCase()}${modo === 'data' && indirizzi !== 'auto' ? `, ${FONTI_INDIRIZZI[indirizzi][0]}` : ''}`} />
    </form>
  );
}
