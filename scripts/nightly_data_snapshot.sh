#!/bin/bash
set -euo pipefail
REPO_DIR="/Users/davidmirzoyan/Desktop/scheduler_ver_2_backup_1756148817"
BACKUP_DIR="$REPO_DIR/backups"
SNAP_DIR="$REPO_DIR/.snapshot-staging"
DATE_STR=$(date +%Y%m%d)
TS=$(date +%Y%m%d-%H%M%S)
ARCHIVE_BASE="$BACKUP_DIR/data-$DATE_STR.zip"
ARCHIVE="$ARCHIVE_BASE"
SHAFILE="$ARCHIVE.sha256"
if [ -e "$ARCHIVE" ]; then
  ARCHIVE="$BACKUP_DIR/data-$DATE_STR-$TS.zip"
  SHAFILE="$ARCHIVE.sha256"
fi
ARCHIVE_TMP="$ARCHIVE.tmp"

mkdir -p "$BACKUP_DIR"
rm -rf "$SNAP_DIR"
mkdir -p "$SNAP_DIR"
rsync -a --delete "$REPO_DIR/data/" "$SNAP_DIR/data/"
cd "$SNAP_DIR"
ditto -c -k --sequesterRsrc --keepParent data "$ARCHIVE_TMP"
mv -f "$ARCHIVE_TMP" "$ARCHIVE"
cd "$REPO_DIR"
/usr/bin/shasum -a 256 "$ARCHIVE" > "$SHAFILE"
chflags uchg "$ARCHIVE" "$SHAFILE" || true
cd "$REPO_DIR"
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  msg="AUTO: nightly data snapshot $TS"
  git commit -m "$msg" || true
  tag="snapshot-$TS"
  git tag -a "$tag" -m "$msg" || true
  git push --follow-tags || true
fi
rm -rf "$SNAP_DIR"
echo "Created $ARCHIVE and $SHAFILE (immutable)"
