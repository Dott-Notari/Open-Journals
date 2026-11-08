// Intestazioni di sicurezza fisse; la Content-Security-Policy con nonce la imposta proxy.js.
const sicurezza = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains' },
];

export default {
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: sicurezza }];
  },
};
