'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Segmenti from './Segmenti';
import Riepilogo from './Riepilogo';
import { inviaEstrazione, lista } from '@/lib/invia';

const MODI = [['data', 'Per periodo'], ['elenco', 'Da una pagina elenco'], ['link', 'Da link']];
const FORMATI = [['docx', 'Word, un file per articolo'], ['txt', 'Testo semplice'], ['html', 'HTML'],
  ['xlsx', 'Indice Excel'], ['jsonl', 'JSONL'], ['tlab', 'Corpus T-LAB']];

export default function ModuloTestata({ fonte, tetto, minuti, attive }) {
  const router = useRouter();
  const [modo, setModo] = useState('data');
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
    if (parole.length) Object.assign(p, { parole, tutte: d.get('tutte') === 'si', cerca_in: d.get('dove') });
    p.formati = d.getAll('formati');
    if (d.get('max')) p.max_articoli = Number(d.get('max'));
    setInvio(true); setErrore('');
    const msg = await inviaEstrazione(fonte.chiave, modo, p);
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  return (
    <div className="riga" style={{ alignItems: 'flex-start', gap: 24 }}>
      <form id="modulo" onSubmit={invia} className="modulo vetro" style={{ flex: '999 1 560px', minWidth: 0 }}>
        <fieldset>
          <legend>Come cercare gli articoli</legend>
          <Segmenti voci={MODI} valore={modo} onCambio={setModo} etichetta="Modalità di ricerca" />
          {modo === 'elenco' && (
            <label className="etichetta">Indirizzo della pagina elenco (sezione, tag o rubrica)
              <input className="campo" type="url" name="elenco" required inputMode="url" autoComplete="off" spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
            </label>
          )}
          {modo === 'link' && (
            <label className="etichetta">Link degli articoli, uno per riga (al massimo 50)
              <textarea className="campo" name="link" rows={6} required spellCheck={false} placeholder={`https://www.${fonte.dominio}/…`} />
              <span className="aiuto">Sono accettati solo indirizzi di {fonte.nome}.</span>
            </label>
          )}
          {modo !== 'link' && (
            <div className="due">
              <label className="etichetta">Dal<input className="campo" type="date" name="dal" required={modo === 'data'} /></label>
              <label className="etichetta">Al<input className="campo" type="date" name="al" required={modo === 'data'} /></label>
            </div>
          )}
          {modo === 'elenco' && <span className="aiuto">Date facoltative: servono a fermare lo scorrimento delle pagine.</span>}
        </fieldset>

        <fieldset>
          <legend>Parole chiave</legend>
          <label className="etichetta">Parole separate da virgole, facoltative
            <input className="campo" name="parole" autoComplete="off" placeholder="migrant*, accoglienza…" />
            <span className="aiuto">L'asterisco tronca la parola: migrant* trova migrante e migranti, non migrazione.</span>
          </label>
          <div className="riga" style={{ gap: 32, alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontWeight: 550 }}>Corrispondenza</span>
              <label className="scelta"><input type="radio" name="tutte" value="no" defaultChecked />almeno una parola</label>
              <label className="scelta"><input type="radio" name="tutte" value="si" />tutte le parole</label>
            </div>
            <div>
              <span style={{ fontWeight: 550 }}>Cerca in</span>
              <label className="scelta"><input type="radio" name="dove" value="testo" defaultChecked />titolo, sommario e testo</label>
              <label className="scelta"><input type="radio" name="dove" value="titolo" />solo titolo e sommario, più rapido</label>
            </div>
          </div>
        </fieldset>

        <fieldset>
          <legend>Formati dell'archivio</legend>
          <div className="due" style={{ gap: 2 }}>
            {FORMATI.map(([k, t]) => <label key={k} className="scelta"><input type="checkbox" name="formati" value={k} defaultChecked />{t}</label>)}
          </div>
          <label className="etichetta" style={{ maxWidth: 260 }}>Numero massimo di articoli
            <input className="campo" type="number" name="max" min={1} max={tetto} inputMode="numeric" placeholder={String(tetto)} />
            <span className="aiuto">Al massimo {tetto}, tetto fissato dal docente.</span>
          </label>
        </fieldset>
      </form>
      <Riepilogo invio={invio} errore={errore} attive={attive}
        righe={[['Fonte', fonte.nome], ['Ricerca', MODI.find((m) => m[0] === modo)[1]], ['Limite', `${tetto} articoli, ${minuti} minuti`]]}
        nota="Oltre il limite di tempo ricevi ciò che è stato raccolto. Gli articoli riservati agli abbonati sono inclusi e segnalati nella scheda." />
    </div>
  );
}
