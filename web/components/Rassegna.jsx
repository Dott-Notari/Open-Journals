import LogoFonte from './LogoFonte';
import { FONTI } from '@/lib/fonti';

// Due nastri di testate che scorrono in versi opposti; si fermano al passaggio del puntatore.
const testate = FONTI.filter((f) => f.chiave !== 'youtube');
const nastro = (lista) => [...lista, ...lista].map((f, i) => (
  <span className="placca" key={f.chiave + i}><LogoFonte chiave={f.chiave} nome={f.nome} area={2200} massimo={40} /></span>
));

export default function Rassegna() {
  return (
    <div className="rassegna" aria-hidden="true">
      <div className="nastro">{nastro(testate.slice(0, 7))}</div>
      <div className="nastro inverso">{nastro(testate.slice(7))}</div>
    </div>
  );
}
