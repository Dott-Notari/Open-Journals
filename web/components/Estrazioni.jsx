'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import Link from 'next/link';
import { Clock, LoaderCircle, CheckCircle2, PauseCircle, AlertTriangle, XCircle, FileArchive, Film, Music, Newspaper } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { trovaFonte, data, giorno, peso } from '@/lib/fonti';
import LogoFonte from './LogoFonte';

const STATI = {
  in_coda: ['In coda', Clock, '#475467'], avviata: ['In avvio', LoaderCircle, '#0A57C2'], in_corso: ['In corso', LoaderCircle, '#0A57C2'],
  completata: ['Completata', CheckCircle2, 'var(--ok)'], interrotta: ['Interrotta', PauseCircle, 'var(--attenzione)'],
  errore: ['Errore', AlertTriangle, 'var(--errore)'], annullata: ['Annullata', XCircle, '#475467'],
};
const ICONE_FILE = { zip: FileArchive, video: Film, audio: Music };

function sintesi(e) {
  const p = e.parametri || {};
  const pezzi = [];
  if (p.dal) pezzi.push(`dal ${giorno.format(new Date(p.dal))} al ${giorno.format(new Date(p.al))}`);
  if (p.link) pezzi.push(`${p.link.length} link`);
  if (p.elenco) pezzi.push('da una pagina elenco');
  if (p.sorgenti) pezzi.push(`${p.sorgenti.length} link YouTube`);
  if (p.cerca) pezzi.push(`ricerca «${p.cerca}»`);
  if (p.parole?.length) pezzi.push(`parole: ${p.parole.join(', ')}`);
  return pezzi.join('; ') || e.modalita;
}

export default function Estrazioni() {
  const [righe, setRighe] = useState(null);
  const [giorni, setGiorni] = useState(5);
  const [errore, setErrore] = useState('');
  const lista = useRef(null);
  const entrata = useRef(false);
  useEffect(() => {
    if (!righe?.length || entrata.current || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    entrata.current = true;
    gsap.from(lista.current.children, { autoAlpha: 0, y: 18, duration: 0.7, ease: 'expo.out', stagger: 0.05 });
  }, [righe]);

  const carica = useCallback(async () => {
    const sb = supabase();
    const { data: { user } } = await sb.auth.getUser();
    if (!user) return;
    const { data: r, error } = await sb.from('estrazioni')
      .select('id,fonte,modalita,parametri,stato,creata_il,conclusa_il,articoli,esaminati,errore,scheda,file_cancellati_il,estrazione_file(id,nome,tipo,dimensione,percorso)')
      .eq('utente', user.id).order('creata_il', { ascending: false }).limit(50);
    if (error) setErrore('Impossibile caricare le estrazioni: ricarica la pagina.');
    else setRighe(r);
  }, []);

  useEffect(() => {
    supabase().from('impostazioni').select('giorni_conservazione').single().then(({ data: i }) => i && setGiorni(i.giorni_conservazione));
    carica();
    const t = setInterval(() => document.visibilityState === 'visible' && carica(), 10000);
    return () => clearInterval(t);
  }, [carica]);

  async function scarica(f) {
    const { data: s, error } = await supabase().storage.from('estrazioni').createSignedUrl(f.percorso, 120, { download: f.nome });
    if (error) setErrore('File non disponibile.');
    else location.assign(s.signedUrl);
  }
  async function annulla(id) {
    await supabase().rpc('annulla_estrazione', { p_id: id });
    carica();
  }

  if (righe === null) return <p className="tenue" aria-live="polite">Caricamento…</p>;
  if (!righe.length) {
    return (
      <div className="vetro" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'flex-start' }}>
        <h2 className="titolo-3">Nessuna estrazione</h2>
        <Link href="/" className="pulsante"><Newspaper size={20} aria-hidden="true" />Scegli una fonte</Link>
      </div>
    );
  }
  return (
    <>
      <div aria-live="polite">{errore && <p className="avviso errore">{errore}</p>}</div>
      <ul ref={lista} style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {righe.map((e) => {
          const [etichetta, Icona, colore] = STATI[e.stato];
          const scadenza = e.conclusa_il && new Date(new Date(e.conclusa_il).getTime() + giorni * 864e5);
          const inCorso = e.stato === 'in_corso' || e.stato === 'avviata';
          return (
            <li key={e.id} className="vetro" data-riga="" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="riga" style={{ alignItems: 'center', gap: 16 }}>
                <span style={{ width: 112, height: 56, borderRadius: 12, background: 'var(--carta-logo)', display: 'grid', placeItems: 'center', padding: 8, flexShrink: 0 }}>
                  <LogoFonte chiave={e.fonte} nome={trovaFonte(e.fonte)?.nome ?? e.fonte} area={1500} massimo={36} />
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0, flex: '1 1 340px' }}>
                  <span style={{ fontSize: '1.12rem', fontWeight: 600 }} translate="no">{trovaFonte(e.fonte)?.nome ?? e.fonte}</span>
                  <span className="tenue" style={{ overflowWrap: 'anywhere' }}>{sintesi(e)}</span>
                  <span className="tenue piccolo numeri">
                    {data.format(new Date(e.creata_il))}
                    {scadenza && !e.file_cancellati_il && `, file fino al ${giorno.format(scadenza)}`}
                    {e.file_cancellati_il && ', file scaduti'}
                  </span>
                </div>
                <span className="riga" style={{ gap: 6, fontWeight: 600, color: colore, marginLeft: 'auto' }}>
                  <Icona size={20} aria-hidden="true" className={inCorso ? 'gira' : undefined} />{etichetta}
                </span>
              </div>
              {inCorso && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div className="barra" role="progressbar" aria-label="Estrazione in corso"><i /></div>
                  <span className="tenue piccolo numeri">{e.articoli} raccolti su {e.esaminati} esaminati</span>
                </div>
              )}
              {e.errore && <p className={`avviso ${e.stato === 'errore' ? 'errore' : 'giallo'}`} style={{ margin: 0 }}>{e.errore}</p>}
              <div className="riga" style={{ gap: 8 }}>
                {!e.file_cancellati_il && e.estrazione_file.map((f) => {
                  const IconaFile = ICONE_FILE[f.tipo];
                  return (
                    <button key={f.id} type="button" className="pulsante compatto" onClick={() => scarica(f)}>
                      <IconaFile size={18} aria-hidden="true" />{f.tipo === 'zip' ? 'Archivio' : f.nome}
                      <span style={{ fontWeight: 400, opacity: 0.8 }} className="numeri">{peso(f.dimensione)}</span>
                    </button>
                  );
                })}
                {e.stato === 'in_coda' && <button type="button" className="pulsante compatto secondario" onClick={() => annulla(e.id)}>Annulla</button>}
              </div>
              {e.scheda && (
                <details>
                  <summary style={{ cursor: 'pointer', minHeight: 32 }}>Scheda</summary>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem', margin: '10px 0 0', maxHeight: 360, overflow: 'auto' }}>{e.scheda}</pre>
                </details>
              )}
            </li>
          );
        })}
      </ul>
    </>
  );
}
