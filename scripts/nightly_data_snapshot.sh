#!/bin/bash
set -euo pipefail

notify() {
  /usr/bin/osascript -e "display notification \"$2\" with title \"$1\"" >/dev/null 2>&1 || true
}

REPO_DIR="/Users/davidmirzoyan/Desktop/scheduler_ver_2_backup_1756148817"
BACKUP_DIR="$REPO_DIR/backups"
SNAP_DIR="$REPO_DIR/.snapshot-staging"
DATE_STR=$(date +%Y%m%d)
TS=$(date +%Y%m%d-%H%M%S)
ARCHIVE_BASE="$BACKUP_DIR/data-$DATE_STR.tar.gz"
ARCHIVE="$ARCHIVE_BASE"
SHAFILE="$ARCHIVE.sha256"
if [ -e "$ARCHIVE" ]; then
  ARCHIVE="$BACKUP_DIR/data-$DATE_STR-$TS.tar.gz"
  SHAFILE="$ARCHIVE.sha256"
fi
ARCHIVE_TMP="$ARCHIVE.tmp"

mkdir -p "$BACKUP_DIR"

trap 'notify "Backup FAILED" "See /tmp/nightly_data_snapshot.err"' ERR

{
  rm -rf "$SNAP_DIR"
  mkdir -p "$SNAP_DIR"
  rsync -a --delete "$REPO_DIR/data/" "$SNAP_DIR/data/"
  tar -C "$SNAP_DIR" -czf "$ARCHIVE_TMP" data
  mv -f "$ARCHIVE_TMP" "$ARCHIVE"
  shasum -a 256 "$ARCHIVE" > "$SHAFILE"
  chflags uchg "$ARCHIVE" "$SHAFILE" || true
  rm -rf "$SNAP_DIR"
} 1>>/tmp/nightly_data_snapshot.out 2>>/tmp/nightly_data_snapshot.err

notify "Backup OK" "$(basename \"$ARCHIVE\") created"
