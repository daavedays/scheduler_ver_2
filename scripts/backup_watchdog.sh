#!/bin/bash
set -euo pipefail
notify() {
  /usr/bin/osascript -e "display notification \"$2\" with title \"$1\"" >/dev/null 2>&1 || true
}
BACKUP_DIR="/Users/davidmirzoyan/Desktop/scheduler_ver_2_backup_1756148817/backups"
DATE_STR=$(date +%Y%m%d)
ARCHIVE="$BACKUP_DIR/data-$DATE_STR.tar.gz"
SHAFILE="$ARCHIVE.sha256"

err() { notify "Backup Watchdog" "$1"; echo "$1"; exit 1; }

if [ ! -f "$ARCHIVE" ]; then err "Missing archive: $(basename \"$ARCHIVE\")"; fi
if [ ! -f "$SHAFILE" ]; then err "Missing checksum: $(basename \"$SHAFILE\")"; fi
if ! /usr/bin/shasum -a 256 -c "$SHAFILE" >/dev/null 2>&1; then err "Checksum failed for $(basename \"$ARCHIVE\")"; fi
notify "Backup Watchdog" "OK: $(basename \"$ARCHIVE\")"
