import { Orizzontale } from './Logo';

export default function Piede() {
  return (
    <footer className="piede-pagina vetro">
      <div className="riga" style={{ gap: 14 }}>
        <Orizzontale style={{ '--onm-dx': '121.94px', height: 22 }} />
        <span className="tenue piccolo">Sociologia della comunicazione interculturale</span>
      </div>
      <span className="piccolo"><span className="tenue">Responsabili scientifici</span><br />Vincenzo Esposito, Francesco Notari</span>
      <span className="tenue piccolo">Materiali per uso di studio e ricerca</span>
    </footer>
  );
}
