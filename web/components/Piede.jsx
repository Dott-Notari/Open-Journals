import { Orizzontale } from './Logo';
import LogoSSS from './LogoSSS';

export default function Piede() {
  return (
    <footer className="piede-pagina vetro">
      <div className="piede-colonna">
        <Orizzontale style={{ '--onm-dx': '121.94px', height: 22 }} />
        <span className="tenue piccolo">Sociologia della comunicazione interculturale</span>
      </div>
      <div className="piede-colonna">
        <span className="tenue piccolo">Responsabili scientifici</span>
        <span className="piccolo">Vincenzo Esposito, Francesco Notari</span>
      </div>
      <div className="piede-colonna">
        <span className="tenue piccolo">Sviluppo della piattaforma</span>
        <LogoSSS style={{ height: 34, width: 'auto', maxWidth: '100%', marginLeft: -2 }} />
      </div>
      <p className="tenue piccolo piede-nota">I testi raccolti servono per studio e ricerca e non vanno ridistribuiti.</p>
    </footer>
  );
}
