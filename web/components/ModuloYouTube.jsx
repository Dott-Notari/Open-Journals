'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Film, Music, Clapperboard, FileText } from 'lucide-react';
import Segmenti from './Segmenti';
import Riepilogo from './Riepilogo';
import { inviaEstrazione, lista } from '@/lib/invia';

const MODI = [['sorgenti', 'Da link'], ['ricerca', 'Ricerca su YouTube']];
const MEDIA = [['entrambi', 'Video e audio', Clapperboard], ['video', 'Solo video mp4', Film],
  ['audio', 'Solo audio mp3', Music], ['nessuno', 'Solo testo', FileText]];

export default function ModuloYouTube({ maxVideo, maxAltezza, maxDurata, attive }) {
  const router = useRouter();
  const [modo, setModo] = useState('sorgenti');
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState('');
  const altezze = [144, 240, 360, 480, 720, 1080].filter((h) => h <= maxAltezza);

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
    Object.assign(p, { trascrizione: d.get('testo'), media: d.get('media'), max_altezza: Number(d.get('altezza')),
      timecode_docx: d.get('timecode') === 'on' });
    setInvio(true); setErrore('');
    const msg = await inviaEstrazione('youtube', modo, p);
    if (msg) { setErrore(msg); setInvio(false); return; }
    router.push('/estrazioni');
  }

  return (
    <div className="riga" style={{ alignItems: 'flex-start', gap: 24 }}>
      <form id="modulo" onSubmit={invia} className="modulo vetro" style={{ flex: '999 1 560px', minWidth: 0 }}>
        <fieldset>
          <legend>Quali video</legend>
          <Segmenti voci={MODI} valore={modo} onCambio={setModo} etichetta="Origine dei video" />
          {modo === 'sorgenti' ? (
            <label className="etichetta">Link di video, playlist o canali, uno per riga
              <textarea className="campo" name="sorgenti" rows={5} required spellCheck={false} placeholder="https://www.youtube.com/watch?v=…" />
            </label>
          ) : (
            <>
              <label className="etichetta">Testo della ricerca
                <input className="campo" type="search" name="cerca" required minLength={2} maxLength={100} autoComplete="off" placeholder="seconde generazioni scuola…" />
              </label>
              <label className="scelta"><input type="checkbox" name="per_data" />Ordina per data invece che per pertinenza</label>
            </>
          )}
        </fieldset>

        <fieldset>
          <legend>Filtri</legend>
          <div className="due">
            <label className="etichetta">Pubblicati dal<input className="campo" type="date" name="dal" /></label>
            <label className="etichetta">al<input className="campo" type="date" name="al" /></label>
            <label className="etichetta">Massimo di video
              <input className="campo" type="number" name="max" min={1} max={maxVideo} inputMode="numeric" placeholder={String(maxVideo)} />
            </label>
          </div>
          <label className="etichetta">Parole nel titolo o nella descrizione, facoltative
            <input className="campo" name="parole" autoComplete="off" placeholder="separate da virgole…" />
          </label>
        </fieldset>

        <fieldset>
          <legend>Trascrizione</legend>
          <label className="scelta"><input type="radio" name="testo" value="auto" defaultChecked />Automatica: sottotitoli se presenti, altrimenti Whisper</label>
          <label className="scelta"><input type="radio" name="testo" value="sottotitoli" />Solo sottotitoli di YouTube, più rapida</label>
          <label className="scelta"><input type="radio" name="testo" value="whisper" />Sempre Whisper, più lenta ma uniforme</label>
          <div className="riga" style={{ alignItems: 'flex-end', gap: 16 }}>
            <label className="etichetta" style={{ width: 240 }}>Lingua
              <select className="campo" name="lingua" defaultValue="it">
                <option value="it">Italiano</option><option value="en">Inglese</option><option value="">Riconoscimento automatico</option>
              </select>
            </label>
            <label className="scelta"><input type="checkbox" name="timecode" />Marcatori temporali nel file Word</label>
          </div>
        </fieldset>

        <fieldset>
          <legend>File multimediali</legend>
          <div className="due" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))' }}>
            {MEDIA.map(([k, t, Icona]) => (
              <label key={k} className="scelta vetro riflesso" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: 14, borderRadius: 16 }}>
                <Icona size={22} aria-hidden="true" color="var(--inchiostro)" />
                <span className="riga" style={{ gap: 8 }}><input type="radio" name="media" value={k} defaultChecked={k === 'entrambi'} />{t}</span>
              </label>
            ))}
          </div>
          <label className="etichetta" style={{ width: 240 }}>Risoluzione del video
            <select className="campo" name="altezza" defaultValue={String(Math.min(480, maxAltezza))}>
              {altezze.map((h) => <option key={h} value={h}>{h}p</option>)}
            </select>
          </label>
        </fieldset>
      </form>
      <Riepilogo invio={invio} errore={errore} attive={attive}
        righe={[['Video', `${modo === 'sorgenti' ? 'dai link' : 'dalla ricerca'}, al massimo ${maxVideo}`], ['Testo', 'sottotitoli o Whisper'], ['Durata', `fino a ${maxDurata} minuti per video`]]}
        nota="Esclusi le dirette e i video oltre la durata massima. Video e audio si scaricano separati dallo zip con trascrizioni, indice e scheda." />
    </div>
  );
}
