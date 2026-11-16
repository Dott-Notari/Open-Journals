// Foto del profilo; senza foto, le iniziali sul colore del marchio.
export default function Avatar({ url, nome, email, size = 36 }) {
  const base = (nome || email || '?').trim();
  const iniziali = base.split(/\s+/).slice(0, 2).map((p) => p[0]).join('').toUpperCase();
  const stile = { width: size, height: size, borderRadius: '50%', flexShrink: 0 };
  if (url) return <img src={url} alt="" width={size} height={size} style={{ ...stile, objectFit: 'cover' }} />;
  return (
    <span aria-hidden="true" style={{ ...stile, display: 'inline-grid', placeItems: 'center', background: 'var(--primario)', color: 'var(--fondo)',
      fontSize: size * 0.38, fontWeight: 600, letterSpacing: '0.02em' }}>{iniziali}</span>
  );
}
