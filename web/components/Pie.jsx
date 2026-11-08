import LogoFonte from './LogoFonte';

export default function Pie() {
  return (
    <footer className="pie vetro">
      <div className="riga" style={{ gap: 18 }}>
        <LogoFonte chiave="unisa" nome="Università degli Studi di Salerno" altezza={48} />
        <span className="tenue piccolo">Corso di Sociologia della comunicazione interculturale</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span className="tenue piccolo" style={{ fontWeight: 600 }}>Responsabili scientifici</span>
        <span style={{ fontWeight: 650 }}>Vincenzo Esposito</span>
        <span style={{ fontWeight: 650 }}>Francesco Notari</span>
      </div>
      <p className="tenue piccolo" style={{ margin: 0, maxWidth: 340 }}>
        Materiali raccolti per finalità di studio e ricerca, da non ridistribuire. I file restano disponibili per un periodo limitato.
      </p>
    </footer>
  );
}
