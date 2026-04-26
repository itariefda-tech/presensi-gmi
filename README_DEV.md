# Flask + BrowserSync (Windows dev)

## Prerequisites
- Node.js LTS (npm included)
- Python 3.10+ (or your project version)

Optional:
- Use a virtual environment for Python packages.

## One-time install
```
npm install
```

## Run dev servers
```
npm run dev
```

## Open in browser
- http://localhost:3000

## How it works
- Flask runs on http://127.0.0.1:5000 using the app factory in `app.py`.
- BrowserSync proxies Flask and reloads on changes in templates and static assets.

## Troubleshooting
- Port 5000 already used: edit `package.json` and `bs-config.js` to a free port.
- BrowserSync not reloading: confirm edits are under `templates/` or `static/` and the files match the watch globs.
- Flask debug not enabled: ensure `dev:flask` uses `--debug` and starts without errors.
- PowerShell vs CMD: `npm run dev` works in both; npm runs scripts via CMD on Windows.

## Repo hygiene
- Do not commit local databases, uploads, logs, cache folders, virtualenvs, or installer binaries.
- Download Git/Python installers outside the repository when possible; if they must sit in this workspace temporarily, keep them under ignored `tools/installers/`.
- Keep one-off diagnostic scripts under ignored `tools/local/`, or promote them into `scripts/` only after they are parameterized, documented, and safe to run.
- Keep temporary backup files under ignored `tools/backups/`.
- Docker builds use `.dockerignore`, so runtime files such as `presensi.db`, `static/uploads/`, logs, backups, and installer binaries stay out of the image context.
