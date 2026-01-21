# Android (Capacitor) Wrapper

Folder `mobile-capacitor/` holds a minimal Capacitor project that wraps the hosted HRIS GMI web UI in an Android WebView. Mode A (remote URL) is the primary experience; Mode B (offline bundle) is intentionally light so the Flutter-inspired UI is untouched.

## Quick goals

- Load `https://absensi.gajiku.online` (or a staging/dev URL) inside Capacitor’s WebView.
- Provide runtime permissions for camera (QR/selfie), geolocation, and file uploads.
- Keep the existing Flask web UI untouched.

## Preparation

1. Install Node.js LTS (to get `npm`/`npx`).
2. From repo root run:
   ```bash
   cd mobile-capacitor
   npm install
   ```

## Capacitor remote setup (Mode A)

1. Ensure `capacitor.config.json` uses the production/staging URL you want:
   ```json
   "server": {
     "url": "https://absensi.gajiku.online",
     "cleartext": false
   }
   ```
   - For local development you can change the `url` to `http://127.0.0.1:5020` (or use `npx cap copy` to bundle).
   - If you need to switch at runtime, call `npx cap sync android` after editing the config.
2. Initialize Capacitor (only once):
   ```bash
   npx cap init
   ```
   (If you already ran this, skip.)
3. Add Android platform:
   ```bash
   npx cap add android
   ```
4. Sync the project and open Android Studio:
   ```bash
   npx cap sync android
   npx cap open android
   ```
5. Build APK/debug using Android Studio (Run > Debug) or:
   ```bash
   npx cap run android
   ```

## Runtime permissions (Android 10+)

After `npx cap add android`, ensure `android/app/src/main/AndroidManifest.xml` contains these:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

Capacitor will prompt at runtime for Camera/GPS/File access when the web app requests them. Your Flask frontend already uses `navigator.mediaDevices`, `<input type="file">`, and geolocation APIs; just approve the dialogs.

## Build checklist

1. `npm install`
2. `npm run android:sync`
3. `npm run android:open`
4. Build or run from Android Studio, or `npm run android:run`

## Troubleshooting checklist

- **Kamera blank**: Android WebView requires HTTPS + camera permission; ensure the `server.url` is `https://` and the Manifest grants `CAMERA`. Use Chrome DevTools remote debugging to inspect.
- **GPS denied**: Accept the runtime permission; WebView geolocation needs `ACCESS_FINE_LOCATION`. Set `android:usesCleartextTraffic="false"` if you always use HTTPS.
- **File upload gagal**: Confirm `<input type="file" capture="user">` is allowed by WebView; ensure the Manifest requests storage permission if you intend to read local files.
- **Mixed content blocked**: Avoid loading HTTP resources when `server.url` is HTTPS. Cloudflare already provides SSL for `absensi.gajiku.online`.
- **Cookie/session tidak kebawa**: Capacitor WebView maintains cookies per domain; keep `server.url` consistent between Capacitor and browser. Avoid cross-origin redirects that drop cookies.
- **CSRF nonce/headers**: The Flask app enforces CSRF on POST/PUT/DELETE for form submissions; the wrapped WebView behaves like a browser so tokens stay in session cookies. If you proxy via a different domain, keep cookies and CSRF token logic intact.

## Optional Mode B (offline bundle)

If you bundle the static assets:

1. Set `capacitor.config.json` `server` to `null` and add your built `static`/`templates` output under `src/`.
2. Build with `npm run build` (if you add bundling) then `npx cap sync android`.

This repo intentionally keeps the WebView pointing to the hosted URL for faster updates.
