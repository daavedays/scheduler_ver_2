#!/bin/bash
set -euo pipefail

# Load recipient from config or git
EMAIL_TO=""
[ -f "scripts/notify.conf" ] && . scripts/notify.conf || true
if [ -z "${EMAIL_TO:-}" ]; then
  EMAIL_TO="$(git config --get user.email || true)"
fi

SUBJECT=${1:-"Backup Notification"}
BODY=${2:-""}
RECIPIENT=${3:-"$EMAIL_TO"}

if [ -z "$RECIPIENT" ]; then
  echo "[send_email] No recipient configured. Set EMAIL_TO in scripts/notify.conf" >&2
  exit 0
fi

exec /usr/bin/osascript scripts/email_notify.scpt "$SUBJECT" "$BODY" "$RECIPIENT"
