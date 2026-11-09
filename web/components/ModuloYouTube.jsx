'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Link2, Search, Clapperboard, Film, Music, FileText } from 'lucide-react';
import Segmenti from './Segmenti';
import Azioni from './Azioni';
import Info from './Info';
import { inviaEstrazione, lista } from '@/lib/invia';

const MODI = [['sorgenti', 'Link', Link2], ['ricerca', 'Ricerca', Search]];
const TESTO = [['auto', 'Automatico'], ['sottotitoli', 'Sottotitoli'], ['whisper', 'Whisper']];
const MEDIA = [['entrambi', 'Video e audio', Clapperboard], ['video', 'Video', Film], ['audio', 'Audio', Music], ['nessuno', 'Solo testo', FileText]];

export default function ModuloYouTube() {
  const router = useRouter();
  const [modo, setModo] = useState('sorgenti');
  const [testo, setTesto] = useState('auto');
  const [media, setMedia] = useState('entrambi');
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState('');

  async function invia(e) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    const p = modo === 'sorgenti' ? { sorgenti: lista(d.get('sorgenti'), '\n') }
      : { cerca: d.get('cerca').trim(), ordina_per_data: d.get('per_data') === 'on' };
    if (d.get('dal') || d.get('al')) Object.assign(p, { dal: d.get('dal'), al: d.get('al') });
    const parole = lista(d.get('parole'));
    if (parole.length) p.parole = parole;
    if (d.get('max')) p.max_video = Number(d.get('max'));
    if (d.get('lingua')) p.lingua = d.get('lingua');
    if (d.get('altezza')) p.max_altezza = Number(d.get('altezza'));
    Object.assign(p, { trascrizione: testo, media, timecode_docx: d.get('timecode') === 'on' });
    setInvio(true); setErrore('');
    const msg = await inviaEstrazione('youtube', modo, p);
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  return (
    <form onSubmit={invia} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="modulo vetro">
        <fieldset>
          <legend>Video</legend>
          <Segmenti voci={MODI} valore={modo} onCambio={setModo} etichetta="Origine dei video" />
          {modo === 'sorgenti' ? (
            <label className="etichetta">Video, playlist o canali, un link per riga
              <textarea className="campo" name="sorgenti" rows={5} required spellCheck={false} placeholder="https://www.youtube.com/watch?v=…" />
            </label>
          ) : (
            <div className="riga" style={{ alignItems: 'flex-end', gap: 14 }}>
              <label className="etichetta" style={{ flex: '1 1 320px' }}>Cerca
                <input className="campo" type="search" name="cerca" required minLength={2} maxLength={100} autoComplete="off" placeholder="seconde generazioni scuola…" />
              </label>
              <label className="gettone"><input type="checkbox" name="per_data" />Più recenti prima</label>
            </div>
          )}
          <div className="due">
            <label className="etichetta">Dal<input className="campo" type="date" name="dal" /></label>
            <label className="etichetta">Al<input className="campo" type="date" name="al" /></label>
            <label className="etichetta">Numero massimo<input className="campo" type="number" name="max" min={1} inputMode="numeric" placeholder="Tutti" /></label>
          </div>
          <label className="etichetta">Parole nel titolo o nella descrizione
            <input className="campo" name="parole" autoComplete="off" placeholder="separate da virgole…" />
          </label>
        </fieldset>

        <fieldset>
          <legend>Trascrizione <Info etichetta="Modalità di trascrizione">Con Automatico si usano i sottotitoli quando ci sono, altrimenti il parlato viene trascritto con Whisper. Scegliendo sempre Whisper i testi sono più uniformi tra un video e l'altro, ma ci vuole qualche minuto per ogni video.</Info></legend>
          <Segmenti voci={TESTO} valore={testo} onCambio={setTesto} etichetta="Trascrizione" />
          <div className="riga" style={{ alignItems: 'flex-end', gap: 14 }}>
            <label className="etichetta" style={{ width: 240 }}>Lingua
              <select className="campo" name="lingua" defaultValue="it">
                <option value="it">Italiano</option><option value="en">Inglese</option><option value="">Riconoscimento automatico</option>
              </select>
            </label>
            <label className="gettone"><input type="checkbox" name="timecode" />Tempi nel file Word</label>
          </div>
        </fieldset>

        <fieldset>
          <legend>File</legend>
          <Segmenti voci={MEDIA} valore={media} onCambio={setMedia} etichetta="File multimediali" />
          {media !== 'nessuno' && media !== 'audio' && (
            <label className="etichetta" style={{ width: 240 }}>Risoluzione
              <select className="campo" name="altezza" defaultValue="">
                <option value="">Migliore disponibile</option>
                {[1080, 720, 480, 360].map((h) => <option key={h} value={h}>{h}p</option>)}
              </select>
            </label>
          )}
        </fieldset>
      </div>
      <Azioni invio={invio} errore={errore} sintesi={`YouTube, ${modo === 'sorgenti' ? 'da link' : 'da ricerca'}, ${MEDIA.find((m) => m[0] === media)[1].toLowerCase()}`} />
    </form>
  );
}
