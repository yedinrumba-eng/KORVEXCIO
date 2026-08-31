#!/usr/bin/env bash
# S0.10 — backup diario de cada site del bench korvexcio + retención local.
# Corre DENTRO del host (korvex-node1), no dentro de un contenedor.
set -euo pipefail

PROJECT_DIR="/home/korvex/frappe_docker-korvexcio-s05"
RETENTION_DAYS="${KORVEXCIO_BACKUP_RETENTION_DAYS:-14}"
STATUS_FILE="${PROJECT_DIR}/backup-status.json"

COMPOSE=(docker compose -p korvexcio --project-directory "${PROJECT_DIR}" \
  -f "${PROJECT_DIR}/compose.yaml" \
  -f "${PROJECT_DIR}/overrides/compose.mariadb.yaml" \
  -f "${PROJECT_DIR}/overrides/compose.redis.yaml" \
  -f "${PROJECT_DIR}/compose.s05.yaml")

timestamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

write_status() {
  local ok="$1" message="$2"
  printf '{"timestamp": "%s", "ok": %s, "message": "%s"}\n' \
    "$(timestamp)" "${ok}" "${message}" > "${STATUS_FILE}"
}

sites=$("${COMPOSE[@]}" exec -T backend ls sites | grep -v -E '^(apps\.json|apps\.txt|assets|common_site_config\.json)$' || true)

if [ -z "${sites}" ]; then
  write_status false "no sites found under sites/"
  echo "No hay sites — nada que respaldar." >&2
  exit 1
fi

failures=0
for site in ${sites}; do
  echo "== backup ${site} =="
  if ! "${COMPOSE[@]}" exec -T backend bench --site "${site}" backup; then
    failures=$((failures + 1))
    echo "FALLÓ el backup de ${site}" >&2
    continue
  fi

  # retención: borra dumps de DB y config más viejos que RETENTION_DAYS,
  # dentro del contenedor backend (los backups viven en sites/<site>/private/backups)
  "${COMPOSE[@]}" exec -T backend find \
    "sites/${site}/private/backups" -type f -mtime "+${RETENTION_DAYS}" -delete
done

if [ "${failures}" -gt 0 ]; then
  write_status false "${failures} site(s) fallaron el backup"
  exit 1
fi

write_status true "backup completo, retención ${RETENTION_DAYS}d aplicada"
echo "OK."
