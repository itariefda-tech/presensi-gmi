# QR Secret Setup

`QR_SECRET` is required for generating the QR codes in the admin dashboard. It is a shared secret that the application uses to sign and later verify each QR payload so scanning cannot be spoofed.

## Local development

1. Choose a random string (32+ characters, mix letters/numbers). Example:
   ```
   QR_SECRET=V8kP9m2Lr3Hs4Qy6Xe7Bt1Uz0Cp5Nw4F
   ```
2. Store it somewhere private on your machine:
   * You can export it in the shell before starting Flask (`$env:QR_SECRET="..."` on PowerShell or `export QR_SECRET="..."` on bash).
   * Or create a local `.env` (ignored by Git) and have your start script load it via `python-dotenv` or similar.
3. Restart the app so it sees the new environment variable. Verify by hitting `/dashboard/admin/qr` and ensuring the payload request returns `ok: true`.

## Deployment

1. Do **not** commit the actual secret. Instead, set `QR_SECRET` via your deployment environment (container config, hosting control panel, systemd service file, etc.).
2. Example for a systemd unit:
   ```
   Environment=QR_SECRET=V8kP9m2Lr3Hs4Qy6Xe7Bt1Uz0Cp5Nw4F
   ```
3. Restart the deployed app after adding the variable so the new value is loaded.

## Rotating the secret

1. Pick a new random string.
2. Deploy it (local or production) by updating the environment and restarting the app.
3. Because QR codes are timestamped (`QR_WINDOW_SECONDS`), rotation takes effect immediately.
