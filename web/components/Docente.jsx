'use client';
import { useCallback, useEffect, useState } from 'react';
import { UserCheck, UserX, Save, Stethoscope, CheckCircle2, AlertTriangle, PauseCircle, PlayCircle, Trash2 } from 'lucide-react';
import Segmenti from './Segmenti';
import { supabase } from '@/lib/supabase';
import { trovaFonte, data } from '@/lib/fonti';
import LogoFonte from './LogoFonte';
import Avatar from './Avatar';
import { Cronometro, Spia } from './Tempo';
import { useEstrazioniInTempoReale } from '@/lib/tempoReale';

const SCHEDE = [['richieste', 'Utenti'], ['fonti', 'Fonti'], ['registro', 'Registro'], ['impostazioni', 'Impostazioni']];
const NUMERI = [
  ['tempo_max_minuti', "Durata massima di un'estrazione (minuti)", 5, 330],
  ['yt_max_durata_minuti', 'Durata massima di un video (minuti)', 1, 600],
  ['giorni_conservazione', 'Giorni di conservazione dei file', 1, 30],
  ['parallele_per_fonte', 'Estrazioni contemporanee sulla stessa testata', 1, 4],
  ['pausa_secondi', 'Pausa tra due richieste allo stesso sito (secondi)', 1, 5],
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

  const [foto, setFoto] = useState({});
  const STATI_IT = { in_coda: 'In coda', avviata: 'In avvio', in_corso: 'In corso', completata: 'Completata', interrotta: 'Interrotta', errore: 'Errore', annullata: 'Annullata' };
  const MODI_IT = { data: 'Periodo', elenco: 'Pagina elenco', link: 'Link', sorgenti: 'Link video', ricerca: 'Ricerca' };

  const caricaRegistro = useCallback(async () => {
    const { data: r } = await sb.from('registro_estrazioni').select('*').order('creata_il', { ascending: false }).limit(300);
    setRegistro(r || []);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEstrazioniInTempoReale(caricaRegistro, { ogni: 10000 });

  async function carica() {
    const [s, f, r, i] = await Promise.all([
      sb.from('profiles').select('id,email,nome,ruolo,approvato,sospeso,foto,registrato_il').order('approvato').order('registrato_il', { ascending: false }),
      sb.from('stato_testate').select('*').order('ordine'),
      sb.from('registro_estrazioni').select('*').order('creata_il', { ascending: false }).limit(200),
      sb.from('impostazioni').select('*').single(),
    ]);
    setStudenti(s.data || []); setFonti(f.data || []); setRegistro(r.data || []); setImp(i.data);
    const percorsi = (s.data || []).map((u) => u.foto).filter(Boolean);
    if (percorsi.length) {
      const { data: firmati } = await sb.storage.from('foto').createSignedUrls(percorsi, 3600);
      setFoto(Object.fromEntries((firmati || []).filter((x) => x.signedUrl).map((x) => [x.path, x.signedUrl])));
    }
  }
  async function sospendi(u, valore) {
    const { error } = await sb.rpc('imposta_sospensione', { p_utente: u.id, p_sospeso: valore });
    setEsito(error ? error.message : valore ? `${u.nome || u.email} è sospeso.` : `${u.nome || u.email} è di nuovo attivo.`);
    carica();
  }
  async function elimina(u) {
    if (!confirm(`Eliminare l'account di ${u.nome || u.email}? Spariscono l'accesso, la foto e i file delle sue estrazioni. Il registro resta.`)) return;
    const r = await fetch('/api/utenti', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: u.id }) });
    const j = await r.json().catch(() => ({}));
    setEsito(r.ok ? 'Account eliminato.' : j.errore || 'Eliminazione non riuscita.');
    carica();
  }
  async function cancellaRegistro(corpo, domanda) {
    if (!confirm(domanda)) return;
    const r = await fetch('/api/registro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });
    const j = await r.json().catch(() => ({}));
    setEsito(r.ok ? `Voci cancellate: ${j.cancellate}.` : j.errore || 'Cancellazione non riuscita.');
    caricaRegistro();
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

  const inAttesa = studenti.filter((s) => !s.approvato && !s.sospeso).length;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <Segmenti voci={SCHEDE.map(([k, t]) => [k, k === 'richieste' && inAttesa ? `${t} (${inAttesa} in attesa)` : t])}
        valore={scheda} onCambio={setScheda} etichetta="Sezioni dell'area docente" />
      <p aria-live="polite" className="tenue" style={{ margin: 0, minHeight: 24 }}>{esito}</p>

      {scheda === 'richieste' && (
        <section className="vetro" style={{ padding: '8px clamp(14px, 3vw, 24px)' }} aria-label="Utenti">
          {studenti.map((u) => {
            const io = u.ruolo === 'docente';
            const [stato, rossa] = u.sospeso ? ['Sospeso', true] : !u.approvato ? ['In attesa', true] : io ? ['Docente', false] : ['Attivo', false];
            return (
              <div key={u.id} className="riga" style={{ padding: '14px 0', borderBottom: '1px solid var(--linea)', gap: 14 }}>
                <Avatar url={foto[u.foto]} nome={u.nome} email={u.email} size={44} />
                <div style={{ minWidth: 0, flex: '1 1 240px' }}>
                  <div className="riga" style={{ gap: 8 }}><span style={{ fontWeight: 600 }}>{u.nome || u.email}</span><span className={`etichetta-stato${rossa ? ' rossa' : ''}`}>{stato}</span></div>
                  <div className="tenue piccolo" style={{ overflowWrap: 'anywhere' }}>{u.email}, registrato il {data.format(new Date(u.registrato_il))}</div>
                </div>
                <div className="riga" style={{ gap: 8 }}>
                  {!u.approvato && <button type="button" className="pulsante compatto" onClick={() => approva(u.id, true)}><UserCheck size={18} aria-hidden="true" />Approva</button>}
                  {u.approvato && !io && !u.sospeso && <button type="button" className="pulsante compatto secondario" onClick={() => sospendi(u, true)}><PauseCircle size={18} aria-hidden="true" />Sospendi</button>}
                  {u.sospeso && <button type="button" className="pulsante compatto" onClick={() => sospendi(u, false)}><PlayCircle size={18} aria-hidden="true" />Riattiva</button>}
                  {u.approvato && !io && <button type="button" className="pulsante compatto secondario" onClick={() => approva(u.id, false)} title="Torna nella sala d'attesa"><UserX size={18} aria-hidden="true" />Revoca</button>}
                  {!io && <button type="button" className="pulsante compatto secondario" onClick={() => elimina(u)} aria-label={`Elimina l'account di ${u.nome || u.email}`}><Trash2 size={17} aria-hidden="true" />Elimina</button>}
                </div>
              </div>
            );
          })}
          {!studenti.length && <p className="tenue" style={{ padding: '14px 0' }}>Nessun utente.</p>}
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
        <section className="vetro" style={{ padding: '12px clamp(10px, 3vw, 24px)', display: 'flex', flexDirection: 'column', gap: 10 }} aria-label="Registro delle estrazioni">
          <div className="riga" style={{ justifyContent: 'space-between' }}>
            <span className="spia" style={{ '--c': 'var(--ok)' }}><span className="spia-punto vivo" aria-hidden="true" />Aggiornato in tempo reale</span>
            {registro.some((r) => !['in_coda', 'avviata', 'in_corso'].includes(r.stato)) && (
              <button type="button" className="pulsante compatto secondario" onClick={() => cancellaRegistro({ tutte: true }, 'Cancellare dal registro tutte le estrazioni concluse, con i loro file?')}>
                <Trash2 size={17} aria-hidden="true" />Cancella le concluse
              </button>
            )}
          </div>
          <div className="scorre">
            <table className="tabella-fonti">
              <thead><tr><th scope="col">Data</th><th scope="col">Studente</th><th scope="col">Fonte</th><th scope="col">Modalità</th><th scope="col">Stato</th><th scope="col">Tempo</th><th scope="col" style={{ textAlign: 'right' }}>Raccolti</th><th scope="col"><span className="nascosto">Azioni</span></th></tr></thead>
              <tbody>
                {registro.map((r) => {
                  const attiva = ['avviata', 'in_corso'].includes(r.stato);
                  return (
                    <tr key={r.id}>
                      <td className="numeri" style={{ whiteSpace: 'nowrap' }}>{data.format(new Date(r.creata_il))}</td>
                      <td style={{ overflowWrap: 'anywhere' }}>{r.nome || r.email_utente}</td>
                      <td translate="no">{trovaFonte(r.fonte)?.nome ?? r.fonte}</td>
                      <td>{MODI_IT[r.modalita] ?? r.modalita}</td>
                      <td>{attiva ? <Spia stato={r.stato} battito={r.battito} segnale={r.segnale} /> : STATI_IT[r.stato] ?? r.stato}</td>
                      <td>{r.iniziata_il ? <Cronometro inizio={r.iniziata_il} fine={r.conclusa_il} /> : '-'}</td>
                      <td className="numeri" style={{ textAlign: 'right' }}>{r.articoli}</td>
                      <td style={{ textAlign: 'right' }}>
                        {!attiva && r.stato !== 'in_coda' && (
                          <button type="button" className="voce icona" aria-label="Cancella dal registro" title="Cancella dal registro"
                            onClick={() => cancellaRegistro({ ids: [r.id] }, 'Cancellare questa voce dal registro, con i suoi file?')}><Trash2 size={17} aria-hidden="true" /></button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {!registro.length && <p className="tenue" style={{ padding: '14px 0' }}>Nessuna estrazione.</p>}
        </section>
      )}

      {scheda === 'impostazioni' && imp && (
        <form onSubmit={salva} className="modulo vetro">
          <div className="due">
            {NUMERI.map(([k, t, min, max]) => (
              <label key={k} className="etichetta">{t}
                <input className="campo" type="number" name={k} min={min} max={max} step={k === 'pausa_secondi' ? 0.5 : 1} required defaultValue={imp[k]} inputMode="decimal" />
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
