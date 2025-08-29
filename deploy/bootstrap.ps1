# PowerShell bootstrap for CareWhistle dev environment (MySQL/MariaDB)
# Usage: powershell -ExecutionPolicy Bypass -File bootstrap.ps1

Write-Host "Setting up CareWhistle dev environment..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "Python not found. Please install Python 3.11 or later." -ForegroundColor Red
  exit 1
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path .env)) {
  "DATABASE_URL=mysql+pymysql://careuser:Spaceship234@127.0.0.1:3306/carewhistle?charset=utf8mb4" | Out-File -Encoding UTF8 .env
  "SECRET_KEY=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)" | Out-File -Append -Encoding UTF8 .env
}

Write-Host "Starting dev server on http://localhost:5000"
python app.py
