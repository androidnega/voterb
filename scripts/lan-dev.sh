#!/usr/bin/env bash
# Start VoterB for access from other devices on the same Wi‑Fi / LAN.
# Serves the frontend over plain HTTP (no TLS certificate warnings).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

get_lan_ip() {
  ipconfig getifaddr en0 2>/dev/null \
    || ipconfig getifaddr en1 2>/dev/null \
    || (hostname -I 2>/dev/null | awk '{print $1}') \
    || echo "127.0.0.1"
}

LAN_IP="$(get_lan_ip)"
LAN_ORIGIN="http://${LAN_IP}:5173"
export LAN_DEV=1
export LAN_ORIGIN
export ALLOWED_HOSTS="localhost,127.0.0.1,${LAN_IP}"
export VITE_BACKEND_URL="http://127.0.0.1:8000"
export LAN_HOST=1
# Plain HTTP for LAN. Do not force Vite TLS.
unset VITE_HTTPS || true
export VITE_HTTPS=0

echo ""
echo "=============================================="
echo "  VoterB — local network mode (HTTP)"
echo "=============================================="
echo "  Your IP:     ${LAN_IP}"
echo "  On this Mac: http://localhost:5173"
echo "  On LAN:      ${LAN_ORIGIN}"
echo ""
echo "  Note: browsers may block camera access on"
echo "  non-HTTPS LAN IPs. Login and admin UI work"
echo "  normally over HTTP."
echo "=============================================="
echo ""

cleanup() {
  echo ""
  echo "Stopping servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$BACKEND"
source venv/bin/activate
python manage.py runserver "0.0.0.0:8000" &
BACKEND_PID=$!

cd "$FRONTEND"
npm run dev:lan &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
