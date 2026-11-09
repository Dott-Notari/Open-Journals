'use client';
import { useEffect, useState } from 'react';
import { UserCheck, UserX, Save, Stethoscope, CheckCircle2, AlertTriangle } from 'lucide-react';
import Segmenti from './Segmenti';
import { supabase } from '@/lib/supabase';
import { trovaFonte, data } from '@/lib/fonti';
import LogoFonte from './LogoFonte';

const SCHEDE = [['richieste', 'Studenti'], ['fonti', 'Fonti'], ['registro', 'Registro'], ['impostazioni', 'Impostazioni']];
const NUMERI = [
  ['tempo_max_minuti', "Durata massima di un'estrazione (minuti)", 5, 330],
  ['yt_max_durata_minuti', 'Durata massima di un video (minuti)', 1, 600],
  ['giorni_conservazione', 'Giorni di conservazione dei file', 1, 30],
];
const INTERRUTTORI = [['registrazioni_aperte', 'Registrazioni aperte'], ['ansa_estrazioni_attive', 'Estrazioni ANSA'],
  ['ansa_indicizzazione_attiva', 'Indice quotidiano ANSA']];

export default function Docente() {
  const sb = supabase();
  const [scheda, setScheda] = useState('richieste');
  const [studenti, setStudenti] = useState([]);
  const [fonti, setFonti] = useState([]);
  const [registro, setRegistro] = useState([]);
  const [imp, setImp] = useState(null);
  const [esito, setEsito] = useState('');
  const [diagnosi, setDiagnosi] = useState(null);
  async function verifica() {
    setDiagnosi('attesa');
    const r = await fetch('/api/diagnostica').then((x) => x.json()).catch(() => ({ esiti: [{ nome: 'Diagnostica', ok: false, testo: 'Non raggiungibile' }] }));
    setDiagnosi(r.esiti || [{ nome: 'Diagnostica', ok: false, testo: r.errore }]);
  }

  async function carica() {
    const [s, f, r, i] = await Promise.all([
      sb.from('profiles').select('id,email,nome,ruolo,approvato,registrato_il').order('approvato').order('registrato_il', { ascending: false }),
      sb.from('stato_testate').select('*').order('ordine'),
      sb.from('registro_estrazioni').select('*').order('creata_il', { ascending: false }).limit(200),
      sb.from('impostazioni').select('*').single(),
    ]);
    setStudenti(s.data || []); setFonti(f.data || []); setRegistro(r.data || []); setImp(i.data);
  }
  useEffect(() => { carica(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function approva(id, valore) {
    const { error } = await sb.rpc('imposta_approvazione', { p_utente: id, p_approvato: valore });
    setEsito(error ? error.message : valore ? 'Studente approvato.' : 'Approvazione revocata.');
    carica();
  }
  async function cambiaFonte(chiave, campo, valore) {
    setFonti((l) => l.map((x) => (x.chiave === chiave ? { ...x, [campo]: valore } : x)));
    const { error } = await sb.from('stato_testate').update({ [campo]: valore }).eq('chiave', chiave);
    if (error) { setEsito(error.message); carica(); }
  }
  async function salva(e) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    const valori = Object.fromEntries(NUMERI.map(([k]) => [k, Number(d.get(k))]));
    INTERRUTTORI.forEach(([k]) => { valori[k] = d.get(k) === 'on'; });
    valori.domini_email_ammessi = (d.get('domini') || '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
    const { error } = await sb.from('impostazioni').update(valori).eq('id', true);
    setEsito(error ? error.message : 'Salvato.');
  }

  const inAttesa = studenti.filter((s) => !s.approvato).length;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <Segmenti voci={SCHEDE.map(([k, t]) => [k, k === 'richieste' && inAttesa ? `${t} (${inAttesa} in attesa)` : t])}
        valore={scheda} onCambio={setScheda} etichetta="Sezioni dell'area docente" />
      <p aria-live="polite" className="tenue" style={{ margin: 0, minHeight: 24 }}>{esito}</p>

      {scheda === 'richieste' && (
        <section className="vetro" style={{ padding: '8px 24px' }} aria-label="Studenti">
          {studenti.filter((s) => s.ruolo === 'studente').map((s) => (
            <div key={s.id} className="riga" style={{ justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid rgba(14,42,71,.08)' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 650 }}>{s.nome || s.email}</div>
                <div className="tenue piccolo" style={{ overflowWrap: 'anywhere' }}>{s.email}, {data.format(new Date(s.registrato_il))}</div>
              </div>
              {s.approvato
                ? <button type="button" className="pulsante compatto secondario" onClick={() => approva(s.id, false)}><UserX size={18} aria-hidden="true" />Revoca</button>
                : <button type="button" className="pulsante compatto" onClick={() => approva(s.id, true)}><UserCheck size={18} aria-hidden="true" />Approva</button>}
            </div>
          ))}
          {!studenti.some((s) => s.ruolo === 'studente') && <p className="tenue" style={{ padding: '14px 0' }}>Nessuno studente.</p>}
        </section>
      )}

      {scheda === 'fonti' && (
        <section className="vetro scorre" style={{ padding: '12px clamp(6px, 3vw, 24px)' }} aria-label="Fonti">
          <table className="tabella-fonti">
            <thead><tr><th scope="col">Fonte</th><th scope="col">Collaudo</th><th scope="col">Online</th><th scope="col">Attiva</th></tr></thead>
            <tbody>
              {fonti.map((f) => (
                <tr key={f.chiave}>
                  <td><span className="riga" style={{ gap: 12, flexWrap: 'nowrap' }}>
                    <span className="placca-tabella" style={{ width: 96, height: 44, flexShrink: 0, borderRadius: 10, background: 'var(--carta-logo)', display: 'grid', placeItems: 'center', padding: 6 }}>
                      <LogoFonte chiave={f.chiave} nome={f.nome} area={1100} massimo={30} />
                    </span>
                    <span style={{ fontWeight: 600 }} translate="no">{trovaFonte(f.chiave)?.nome ?? f.nome}</span>
                  </span></td>
                  <td>
                    <details>
                      <summary style={{ cursor: 'pointer' }}>{f.esito_collaudo}{f.collaudo_il ? `, ${data.format(new Date(f.collaudo_il))}` : ''}</summary>
                      <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: '0.78rem', margin: '8px 0 0' }}>{f.dettaglio_collaudo || '-'}</pre>
                    </details>
                  </td>
                  <td><input type="checkbox" role="switch" className="interruttore" aria-label={`Disponibile online: ${f.nome}`}
                    checked={f.disponibile_online} onChange={(e) => cambiaFonte(f.chiave, 'disponibile_online', e.target.checked)} /></td>
                  <td><input type="checkbox" role="switch" className="interruttore" aria-label={`Attiva: ${f.nome}`}
                    checked={f.attiva} onChange={(e) => cambiaFonte(f.chiave, 'attiva', e.target.checked)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {scheda === 'registro' && (
        <section className="vetro scorre" style={{ padding: '12px 24px' }} aria-label="Registro delle estrazioni">
          <table className="tabella-fonti">
            <thead><tr><th scope="col">Data</th><th scope="col">Studente</th><th scope="col">Fonte</th><th scope="col">Modalità</th><th scope="col">Stato</th><th scope="col" style={{ textAlign: 'right' }}>Raccolti</th></tr></thead>
            <tbody>
              {registro.map((r) => (
                <tr key={r.id}>
                  <td className="numeri" style={{ whiteSpace: 'nowrap' }}>{data.format(new Date(r.creata_il))}</td>
                  <td style={{ overflowWrap: 'anywhere' }}>{r.nome || r.email_utente}</td>
                  <td translate="no">{trovaFonte(r.fonte)?.nome ?? r.fonte}</td>
                  <td>{r.modalita}</td><td>{r.stato}</td>
                  <td className="numeri" style={{ textAlign: 'right' }}>{r.articoli}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!registro.length && <p className="tenue" style={{ padding: '14px 0' }}>Nessuna estrazione.</p>}
        </section>
      )}

      {scheda === 'impostazioni' && imp && (
        <form onSubmit={salva} className="modulo vetro">
          <div className="due">
            {NUMERI.map(([k, t, min, max]) => (
              <label key={k} className="etichetta">{t}
                <input className="campo" type="number" name={k} min={min} max={max} required defaultValue={imp[k]} inputMode="numeric" />
              </label>
            ))}
          </div>
          <div>
            {INTERRUTTORI.map(([k, t]) => (
              <label key={k} className="riga" style={{ justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid rgba(14,42,71,.08)', cursor: 'pointer' }}>
                <span style={{ fontWeight: 550 }}>{t}</span>
                <input type="checkbox" role="switch" className="interruttore" name={k} defaultChecked={imp[k]} />
              </label>
            ))}
          </div>
          <label className="etichetta">Domini email ammessi, separati da virgole
            <input className="campo" name="domini" autoComplete="off" spellCheck={false} defaultValue={imp.domini_email_ammessi.join(', ')} placeholder="unisa.it, studenti.unisa.it…" />
          </label>
          <button type="submit" className="pulsante" style={{ alignSelf: 'flex-start' }}><Save size={20} aria-hidden="true" />Salva</button>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, borderTop: '1px solid var(--linea)', paddingTop: 20 }}>
            <button type="button" className="pulsante compatto secondario" style={{ alignSelf: 'flex-start' }} onClick={verifica} disabled={diagnosi === 'attesa'}>
              <Stethoscope size={17} aria-hidden="true" />Verifica i collegamenti
            </button>
            <div aria-live="polite">
              {Array.isArray(diagnosi) && diagnosi.map((d) => (
                <p key={d.nome} className="riga" style={{ gap: 8, flexWrap: 'nowrap', alignItems: 'flex-start', margin: '6px 0' }}>
                  {d.ok ? <CheckCircle2 size={18} color="var(--ok)" aria-hidden="true" style={{ flexShrink: 0, marginTop: 3 }} />
                    : <AlertTriangle size={18} color="var(--errore)" aria-hidden="true" style={{ flexShrink: 0, marginTop: 3 }} />}
                  <span><b style={{ fontWeight: 600 }}>{d.nome}</b>: {d.testo}</span>
                </p>
              ))}
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
