import { NextResponse } from 'next/server';
import { createServerClient } from '@supabase/ssr';

const PUBBLICHE = ['/accesso', '/auth/'];

export async function proxy(request) {
  const nonce = btoa(crypto.randomUUID());
  const sviluppo = process.env.NODE_ENV === 'development';
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${sviluppo ? " 'unsafe-eval'" : ''}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    `connect-src 'self' ${process.env.NEXT_PUBLIC_SUPABASE_URL}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join('; ');

  const intestazioni = new Headers(request.headers);
  intestazioni.set('x-nonce', nonce);
  intestazioni.set('Content-Security-Policy', csp);
  let risposta = NextResponse.next({ request: { headers: intestazioni } });

  const sb = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (lista) => {
        lista.forEach(({ name, value }) => request.cookies.set(name, value));
        risposta = NextResponse.next({ request: { headers: intestazioni } });
        lista.forEach(({ name, value, options }) => risposta.cookies.set(name, value, options));
      },
    },
  });
  const { data: { user } } = await sb.auth.getUser();

  const percorso = request.nextUrl.pathname;
  if (!user && !PUBBLICHE.some((p) => percorso.startsWith(p))) {
    const verso = NextResponse.redirect(new URL('/accesso', request.url));
    risposta.cookies.getAll().forEach((c) => verso.cookies.set(c));
    return verso;
  }
  risposta.headers.set('Content-Security-Policy', csp);
  return risposta;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|loghi/|favicon.ico).*)'],
};
