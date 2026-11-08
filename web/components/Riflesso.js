// Il riflesso del vetro segue il puntatore (variabili CSS lette da .riflesso::after).
export function seguiLuce(e) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty('--mx', `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty('--my', `${e.clientY - r.top}px`);
}
