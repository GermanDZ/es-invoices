#!/usr/bin/env bash
# Local development setup for FacturaSimple.
# Run once after cloning: bash scripts/setup_local.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- helpers -----------------------------------------------------------------
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
die()    { red "ERROR: $*"; exit 1; }

# --- 1. Python version check -------------------------------------------------
green "==> Checking Python version..."
python3 -c "
import sys
if sys.version_info < (3, 10):
    print('Python 3.10+ required, found ' + sys.version)
    sys.exit(1)
print('Python', sys.version.split()[0], 'OK')
"

# --- 2. Virtual environment --------------------------------------------------
green "==> Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    green "    Created .venv"
else
    yellow "    .venv already exists, skipping creation"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
green "    Activated .venv"

# --- 3. Install dependencies -------------------------------------------------
green "==> Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
green "    Dependencies installed"

# --- 4. Environment file -----------------------------------------------------
green "==> Configuring .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    green "    Created .env from .env.example"
fi

# Inject CERT_ENCRYPTION_KEY if not set
if ! grep -qE '^CERT_ENCRYPTION_KEY=.+' .env; then
    KEY="$(python3 -c "from certificates.crypto import generate_key; print(generate_key())")"
    # Replace blank/missing CERT_ENCRYPTION_KEY line, or append
    if grep -q '^CERT_ENCRYPTION_KEY=' .env; then
        # Use sed to replace the line (works on both GNU and BSD sed)
        sed -i.bak "s|^CERT_ENCRYPTION_KEY=.*|CERT_ENCRYPTION_KEY=${KEY}|" .env && rm -f .env.bak
    else
        echo "CERT_ENCRYPTION_KEY=${KEY}" >> .env
    fi
    green "    Generated and saved CERT_ENCRYPTION_KEY"
else
    yellow "    CERT_ENCRYPTION_KEY already set"
fi

# --- 5. Migrate --------------------------------------------------------------
green "==> Running database migrations..."
python manage.py migrate --no-input
green "    Migrations applied (SQLite: db.sqlite3)"

# --- 6. Seed dev user --------------------------------------------------------
green "==> Seeding dev user..."
python manage.py seed_dev_owner

# --- 7. Done -----------------------------------------------------------------
echo ""
green "========================================"
green "  Setup complete!"
green "========================================"
echo ""
echo "  Start the server:    python manage.py runserver"
echo "  Dev login URL:       http://localhost:8000/dev/login/"
echo "  Run all tests:       python manage.py test"
echo "  Run smoke tests:     python manage.py test devtools.tests.test_smoke"
echo ""
yellow "  Note: AEAT_SUBMISSION_LIVE=0 — no real tax submissions will occur."
echo ""
