#!/bin/bash
cd /opt/mn
DUMP="/tmp/project_$(TZ='Europe/Moscow' date +%d%b%Y_%H%M).txt"

echo "===== СТРУКТУРА ПРОЕКТА =====" > "$DUMP"
find . -type f \
  -not -path '*/.venv/*' -not -path '*/__pycache__/*' \
  -not -path '*/.git/*' -not -path '*/.claude/*' \
  -not -path '*/.cache/*' -not -path '*/node_modules/*' \
  -not -path '*/backups/*' -not -path '*/status/*' \
  -not -name '*.db' -not -name '*.db-wal' -not -name '*.db-shm' \
  -not -name '*.bak*' -not -name '*.pyc' -not -name '*.pyo' \
  -not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' \
  -not -name '*.gif' -not -name '*.ico' -not -name '*.svg' \
  -not -name '*.docx' -not -name '*.xlsx' -not -name '*.pdf' \
  -not -name '*.zip' -not -name '*.tar' -not -name '*.gz' \
  -not -name '*.log' \
  -not -name '.env' -not -name '.env.*' \
  -not -name '.htpasswd' \
  -not -name '*.key' -not -name '*.pem' -not -name '*.crt' \
  -not -name '.git-credentials' -not -name '.netrc' \
  -not -name '.DS_Store' \
  | sort | sed 's|^./||' >> "$DUMP"

echo "" >> "$DUMP"
echo "===== СОДЕРЖИМОЕ ФАЙЛОВ =====" >> "$DUMP"
echo "" >> "$DUMP"

find . -type f \
  -not -path '*/.venv/*' -not -path '*/__pycache__/*' \
  -not -path '*/.git/*' -not -path '*/.claude/*' \
  -not -path '*/.cache/*' -not -path '*/node_modules/*' \
  -not -path '*/backups/*' -not -path '*/status/*' \
  -not -name '*.db' -not -name '*.db-wal' -not -name '*.db-shm' \
  -not -name '*.bak*' -not -name '*.pyc' -not -name '*.pyo' \
  -not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' \
  -not -name '*.gif' -not -name '*.ico' -not -name '*.svg' \
  -not -name '*.docx' -not -name '*.xlsx' -not -name '*.pdf' \
  -not -name '*.zip' -not -name '*.tar' -not -name '*.gz' \
  -not -name '*.log' \
  -not -name '.env' -not -name '.env.*' \
  -not -name '.htpasswd' \
  -not -name '*.key' -not -name '*.pem' -not -name '*.crt' \
  -not -name '.git-credentials' -not -name '.netrc' \
  -not -name '.DS_Store' \
  | sort | while read f; do echo "===== $f ====="; cat "$f" 2>/dev/null; echo; done >> "$DUMP"

du -h "$DUMP"
echo "Файл: $DUMP"
echo "Файлов: $(grep -c '^=====' "$DUMP")"
