param(
    [string]$Secret,
    [string]$DbPath = "presensi.db",
    [switch]$EnableSeedData,
    [string]$SeedUsersJson
)

if (-not $Secret) {
    $Secret = [guid]::NewGuid().ToString("N")
    Write-Host "Generated FLASK_SECRET for dev session."
}
$env:FLASK_SECRET = $Secret

if (-not $env:OWNER_ADDON_PASSWORD) {
    $env:OWNER_ADDON_PASSWORD = "owner123"
    Write-Host "Using OWNER_ADDON_PASSWORD for dev session: $env:OWNER_ADDON_PASSWORD"
}

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

if ($EnableSeedData) {
    $env:ENABLE_SEED_DATA = "1"
    if ($SeedUsersJson) {
        $env:SEED_USERS_JSON = $SeedUsersJson
    } else {
        Remove-Item Env:\SEED_USERS_JSON -ErrorAction SilentlyContinue
        Write-Host "ENABLE_SEED_DATA=1 tanpa SEED_USERS_JSON; tidak ada user default yang dibuat."
    }
} else {
    $env:ENABLE_SEED_DATA = "0"
    Remove-Item Env:\SEED_USERS_JSON -ErrorAction SilentlyContinue
}

if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing requirements..."
& ".\.venv\Scripts\pip" install -r requirements.txt

Write-Host "Starting Flask dev server..."
& ".\.venv\Scripts\python" app.py
