export default function Piede() {
  return (
    <footer className="piede-pagina vetro">
      <div className="riga" style={{ gap: 14 }}>
        <img src="/loghi/unisa.webp" alt="Università degli Studi di Salerno" width={52} height={52} />
        <span>Scraper delle testate giornalistiche<br /><span className="tenue piccolo">Sociologia della comunicazione interculturale</span></span>
      </div>
      <span className="piccolo"><span className="tenue">Responsabili scientifici</span><br />Vincenzo Esposito, Francesco Notari</span>
      <span className="tenue piccolo">Materiali per uso di studio e ricerca</span>
    </footer>
  );
}
