import { createServerClient } from '@supabase/ssr';
import { createClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';

export async function supabaseServer() {
  const c = await cookies();
  return createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, {
    cookies: {
      getAll: () => c.getAll(),
      // nei componenti server i cookie sono in sola lettura: li aggiorna proxy.js
      setAll: (lista) => { try { lista.forEach(({ name, value, options }) => c.set(name, value, options)); } catch {} },
    },
  });
}

// Solo lato server (route API): chiave segreta, mai nel browser.
export function supabaseServizio() {
  return createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
