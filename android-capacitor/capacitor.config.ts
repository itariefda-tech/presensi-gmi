import type { CapacitorConfig } from '@capacitor/cli';

// ===== ENV =====
const DEV_URL = process.env.DEV_URL || 'http://10.0.2.2:5020';
const PROD_URL = 'https://absensi.gajiku.online';

const isDev =
  process.env.NODE_ENV === 'development' ||
  process.env.CAPACITOR_DEV === 'true';

// ===== CONFIG =====
const config: CapacitorConfig = {
  appId: 'online.gajiku.absensi',
  appName: 'Presensi GMI',

  /**
   * Bootstrap directory.
   * HANYA untuk memenuhi requirement Capacitor.
   * Web app asli di-load via server.url (WebView).
   */
  webDir: 'src',

  /**
   * Remote WebView (WAJIB untuk target kamu)
   */
  server: {
    url: isDev ? DEV_URL : PROD_URL,

    /**
     * cleartext TRUE hanya untuk DEV (http)
     * PROD harus HTTPS
     */
    cleartext: isDev,

    /**
     * Domain yang boleh di-navigate di WebView
     */
    allowNavigation: [
      'absensi.gajiku.online',
      '*.gajiku.online',
      '10.0.2.2',
      'localhost'
    ]
  },

  /**
   * Android-specific config
   */
  android: {
    /**
     * Hindari mixed content kecuali DEV
     */
    allowMixedContent: isDev
  }
};

export default config;
