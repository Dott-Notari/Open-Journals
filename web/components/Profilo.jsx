'use client';
import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Camera, Trash2, Save, LoaderCircle } from 'lucide-react';
import Avatar from './Avatar';
import RitaglioFoto from './RitaglioFoto';
import { supabase } from '@/lib/supabase';

const MAX_ORIGINALE = 15 * 1048576;

export default function Profilo({ id, email, nome, fotoPercorso, fotoUrl }) {
  const router = useRouter();
  const scelta = useRef(null);
  const [file, setFile] = useState(null);
  const [anteprima, setAnteprima] = useState(fotoUrl);
  const [attesa, setAttesa] = useState(false);
  const [esito, setEsito] = useState('');

  function scegli(e) {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;
    if (!f.type.startsWith('image/')) return setEsito('Scegli un file immagine (JPG, PNG, WebP o HEIC).');
    if (f.size > MAX_ORIGINALE) return setEsito("L'immagine supera i 15 MB.");
    setEsito(''); setFile(f);
  }

  async function salvaFoto(blob) {
    setFile(null); setAttesa(true);
    const sb = supabase();
    const percorso = `${id}/foto-${Date.now()}.webp`;
    const { error } = await sb.storage.from('foto').upload(percorso, blob, { contentType: 'image/webp' });
    if (!error) {
      const { error: e2 } = await sb.from('profiles').update({ foto: percorso }).eq('id', id);
      if (!e2) {
        if (fotoPercorso) await sb.storage.from('foto').remove([fotoPercorso]);
        setAnteprima(URL.createObjectURL(blob));
        setEsito('Foto aggiornata.');
        router.refresh();
      } else setEsito('Foto non salvata: riprova.');
    } else setEsito('Caricamento non riuscito: riprova.');
    setAttesa(false);
  }

  async function togliFoto() {
    if (!confirm('Togliere la foto del profilo?')) return;
    const sb = supabase();
    await sb.from('profiles').update({ foto: null }).eq('id', id);
    if (fotoPercorso) await sb.storage.from('foto').remove([fotoPercorso]);
    setAnteprima(null); setEsito('Foto rimossa.');
    router.refresh();
  }

  async function salvaNome(e) {
    e.preventDefault();
    const n = new FormData(e.currentTarget).get('nome').trim();
    const { error } = await supabase().from('profiles').update({ nome: n || null }).eq('id', id);
    setEsito(error ? 'Nome non salvato: riprova.' : 'Nome aggiornato.');
    router.refresh();
  }

  return (
    <div className="modulo vetro" style={{ maxWidth: 640 }}>
      <div className="riga" style={{ gap: 22 }}>
        <div style={{ position: 'relative' }}>
          <Avatar url={anteprima} nome={nome} email={email} size={112} />
          {attesa && <span style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', borderRadius: '50%', background: 'rgba(0,0,0,.45)', color: '#fff' }}>
            <LoaderCircle size={28} className="gira" aria-label="Caricamento" /></span>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input ref={scelta} type="file" accept="image/*" onChange={scegli} hidden />
          <button type="button" className="pulsante compatto" onClick={() => scelta.current.click()} disabled={attesa}>
            <Camera size={17} aria-hidden="true" />{anteprima ? 'Cambia foto' : 'Carica una foto'}
          </button>
          {anteprima && <button type="button" className="pulsante compatto secondario" onClick={togliFoto} disabled={attesa}><Trash2 size={17} aria-hidden="true" />Togli la foto</button>}
        </div>
      </div>
      <form onSubmit={salvaNome} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <label className="etichetta">Nome e cognome
          <input className="campo" name="nome" defaultValue={nome ?? ''} maxLength={120} autoComplete="name" />
        </label>
        <label className="etichetta">Email
          <input className="campo" value={email} readOnly aria-readonly="true" style={{ color: 'var(--tenue)' }} />
        </label>
        <button type="submit" className="pulsante compatto" style={{ alignSelf: 'flex-start' }}><Save size={17} aria-hidden="true" />Salva</button>
      </form>
      <p aria-live="polite" className="tenue" style={{ minHeight: 24 }}>{esito}</p>
      {file && <RitaglioFoto file={file} onFatto={salvaFoto} onAnnulla={() => setFile(null)} />}
    </div>
  );
}
