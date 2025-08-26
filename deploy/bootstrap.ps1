# PowerShell bootstrap for Carewhistle dev environment (SQLite)
# Usage: powershell -ExecutionPolicy Bypass -File bootstrap.ps1

Write-Host "Setting up Carewhistle dev environment..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "Python not found. Please install Python 3.11 or later." -ForegroundColor Red
  exit 1
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env -ErrorAction SilentlyContinue
  "SECRET_KEY=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)" | Out-File -Append .env
  "FERNET_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)" | Out-File -Append .env
}

Write-Host "Running migrations (SQLite)..."
python app.py db upgrade

Write-Host "Starting dev server on http://localhost:5000"
python app.py run
