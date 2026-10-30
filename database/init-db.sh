#!/bin/bash
set -e

echo "Restoring LoL database..."

pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-owner \
  --no-acl \
  --exit-on-error \
  /backup/lol-data.dump

echo "Database restored successfully."