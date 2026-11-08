'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CalendarRange, LayoutList, Link2 } from 'lucide-react';
import Segmenti from './Segmenti';
import Azioni from './Azioni';
import Info from './Info';
import { inviaEstrazione, lista } from '@/lib/invia';

const MODI = [['data', 'Periodo', CalendarRange], ['elenco', 'Pagina elenco', LayoutList], ['link', 'Link', Link2]];
const FORMATI = [['docx', 'Word'], ['txt', 'Testo'], ['html', 'HTML'], ['xlsx', 'Excel'], ['jsonl', 'JSONL'], ['tlab', 'T-LAB']];

export default function ModuloTestata({ fonte }) {
  const router = useRouter();
  const [modo, setModo] = useState('data');
  const [tutte, setTutte] = useState('no');
  const [dove, setDove] = useState('testo');
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState('');

  async function invia(e) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    const p = {};
    if (d.get('dal') || d.get('al')) Object.assign(p, { dal: d.get('dal'), al: d.get('al') });
    if (modo === 'elenco') p.elenco = d.get('elenco').trim();
    if (modo === 'link') p.link = lista(d.get('link'), '\n');
    const parole = lista(d.get('parole'));
    if (parole.length) Object.assign(p, { parole, tutte: tutte === 'si', cerca_in: dove });
    p.formati = d.getAll('formati');
    if (d.get('max')) p.max_articoli = Number(d.get('max'));
    setInvio(true); setErrore('');
    const msg = await inviaEstrazione(fonte.chiave, modo, p);
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  return (
    <form onSubmit={invia} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="modulo vetro">
        <fieldset>
          <legend>Ricerca</legend>
          <Segmenti voci={MODI} valore={modo} onCambio={setModo} etichetta="Modalità di ricerca" />
          {modo === 'elenco' && (
            <label className="etichetta">Indirizzo della pagina
              <input className="campo" type="url" name="elenco" required inputMode="url" autoComplete="off" spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
            </label>
          )}
          {modo === 'link' && (
            <label className="etichetta">Un link per riga
              <textarea className="campo" name="link" rows={6} required spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
            </label>
          )}
          {modo !== 'link' && (
            <div className="due">
              <label className="etichetta">Dal<input className="campo" type="date" name="dal" required={modo === 'data'} /></label>
              <label className="etichetta">Al<input className="campo" type="date" name="al" required={modo === 'data'} /></label>
            </div>
          )}
        </fieldset>

        <fieldset>
          <legend>Parole chiave <Info etichetta="Come scrivere le parole chiave">Separale con una virgola. L'asterisco tronca: migrant* trova migrante e migranti. Senza parole si raccoglie tutto.</Info></legend>
          <input className="campo" name="parole" autoComplete="off" aria-label="Parole chiave" placeholder="migrant*, accoglienza…" />
          <div className="riga" style={{ gap: 10 }}>
            <Segmenti voci={[['no', 'Almeno una'], ['si', 'Tutte']]} valore={tutte} onCambio={setTutte} etichetta="Corrispondenza" />
            <Segmenti voci={[['testo', 'In tutto il testo'], ['titolo', 'Solo titolo e sommario']]} valore={dove} onCambio={setDove} etichetta="Dove cercare" />
          </div>
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
      <Azioni invio={invio} errore={errore} sintesi={`${fonte.nome}, ${MODI.find((m) => m[0] === modo)[1].toLowerCase()}`} />
    </form>
  );
}
