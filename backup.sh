#!/usr/bin/env bash
# =============================================================================
# Backup diário do banco do FormSurvey.
#
# Eu uso a API de backup do próprio SQLite (via Python), e não um simples
# "cp": ela gera uma cópia consistente mesmo que alguém esteja respondendo ao
# questionário naquele exato momento. Um "cp" no meio de uma escrita pode
# gerar um arquivo corrompido.
#
# As cópias ficam em /var/backups/formsurvey (só o root lê), uma por dia, e as
# com mais de 30 dias são apagadas. Elas contêm os registros de consentimento,
# por isso a pasta é fechada para outros usuários.
#
# Agendamento (feito uma vez, como root):
#   echo "30 2 * * * root /opt/formsurvey/backup.sh" > /etc/cron.d/formsurvey-backup
# =============================================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DB="${APP_DIR}/instance/formsurvey.db"
DEST=/var/backups/formsurvey
KEEP_DAYS=30

install -d -m 700 "$DEST"
OUT="${DEST}/formsurvey-$(date +%F).db"

"${APP_DIR}/venv/bin/python" - "$DB" "$OUT" <<'PY'
import sqlite3, sys
src, dst = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close(); src.close()
PY
chmod 600 "$OUT"

find "$DEST" -name 'formsurvey-*.db' -mtime +"$KEEP_DAYS" -delete
echo "Backup gravado em $OUT"
