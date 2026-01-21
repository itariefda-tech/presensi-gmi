param(
    [string]$Secret,
    [string]$DbPath = "presensi.db"
)

if (-not $Secret) {
    $Secret = [guid]::NewGuid().ToString("N")
    Write-Host "Generated FLASK_SECRET for dev session."
}
$env:FLASK_SECRET = $Secret

$resolvedDb = Resolve-Path -LiteralPath $DbPath -ErrorAction SilentlyContinue
if (-not $resolvedDb) {
    $defaultDb = Resolve-Path -LiteralPath "presensi.db" -ErrorAction SilentlyContinue
    if (-not $defaultDb) {
        Write-Error "Database file 'presensi.db' not found in repo root."
        exit 1
    }
    $resolvedDb = $defaultDb
}
$env:PRESENSI_DB_PATH = $resolvedDb

$seedJson = '[{"email":"hrd@gmi.com","name":"HR Superadmin","role":"hr_superadmin","password":"hrd123"}]'
$env:ENABLE_SEED_DATA = "1"
$env:SEED_USERS_JSON = $seedJson

if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing requirements..."
& ".\.venv\Scripts\pip" install -r requirements.txt

Write-Host "Starting Flask dev server..."
& ".\.venv\Scripts\python" app.py
