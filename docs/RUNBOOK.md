# 🛠 RUNBOOK — KORVEXCIO (Producción en korvex-node1)

> **Qué hacer cuando se cae algo. Comandos exactos, probados.**
> *Ubicación: `docs/RUNBOOK.md` — copia en el servidor si quieres: `/home/korvex/RUNBOOK.md`*

---

## 📍 INFORMACIÓN VITAL DEL NODO

| Qué | Valor |
|-----|-------|
| **Servidor** | `korvex-node1` (mini PC, i5-9500, 14GB RAM, 98GB SSD) |
| **Acceso** | `ssh korvex-host` (Tailscale) · `sudo` pide contraseña |
| **Directorio KORVEXCIO** | `/home/korvex/frappe_docker-korvexcio-s05` |
| **Directorio KORVIS** | `/opt/korvex/app` (NO tocar) |
| **Sites** | `korvexcio.korvexdev.cc` (VLJ + ESE), `demo.korvexdev.cc` |
| **MariaDB** | Solo `127.0.0.1:3306` (Docker interno) |
| **Redis KORVEXCIO** | Solo `127.0.0.1:6379/6380` (Docker interno) |
| **Backup timer** | `korvexcio-backup.timer` (03:30 diario, retención 14d) |
| **Cloudflare Tunnel** | `cloudflared` systemd service |

---

## 🔴 ESCENARIO 1 — DGII CAÍDA / e-CF EN "PENDIENTE" HORAS

### Síntoma
- Facturas en **e-CF Pendientes** con estado "Pendiente" o "Reintentando" > 30 min
- Badge en POS: "X facturas por sincronizar" no baja

### Diagnóstico
```bash
# 1. ¿Hay internet en el nodo?
ssh korvex-host 'curl -s -o /dev/null -w "%{http_code}\n" https://github.com'
# Debe dar 200. Si 000 = IPv4 caído (ya pasó)

# 2. ¿El proveedor responde? (ej: ECF SSD / Alanube)
ssh korvex-host 'curl -s -o /dev/null -w "%{http_code}\n" https://api.ecf-ssd.com/health'
# O el endpoint de tu proveedor

# 3. Ver cola de jobs de Frappe
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
jobs = frappe.get_all(\"RQ Job\", filters={\"status\": [\"queued\", \"started\"]}, fields=[\"name\", \"job_name\", \"exc_info\"], limit=10)
for j in jobs: print(j.name, j.job_name, j.exc_info[:200] if j.exc_info else \"\")
"'
```

### Acción
```bash
# 1. Reintentar manual desde UI (dueño)
# Menú → Fiscal → e-CF Pendientes → "Reintentar todas"

# 2. Si falla: forzar reintento por consola
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
from korvexcio.ecf.tasks import emitir_ecf

pendientes = frappe.get_all(\"ECF\", filters={\"estado\": [\"Pendiente\", \"Error\"]}, pluck=\"name\")
for ecf_name in pendientes:
    frappe.enqueue(emitir_ecf, queue=\"short\", ecf_name=ecf_name, enqueue_after_commit=True)
    print(f\"Reencolado: {ecf_name}\")
"'

# 3. Si el proveedor está caído: activar CONTINGENCIA
# (Las facturas nuevas usarán e-CF pre-computados automáticamente)
# Verificar que existan contingencias:
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
cont = frappe.get_all(\"ECF Contingencia\", filters={\"company\": [\"in\", [\"VAPERIA LA J Y EL JALAPEÑO\", \"EL SABOR DE LAS 5 ESQUINAS\"]], \"estado\": \"Disponible\"}, fields=[\"company\", \"tipo_ecf\", \"encf\"], limit=20)
for c in cont: print(c.company, c.tipo_ecf, c.encf)
"'
```

### Verificación
```bash
# Verificar que pasan a "Aceptado"
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
estados = frappe.get_all(\"ECF\", fields=[\"estado\", \"count(*) as cnt\"], group_by=\"estado\")
for e in estados: print(e.estado, e.cnt)
"'
# Debe mostrar: Aceptado: XX, Pendiente: 0 (o bajando)
```

---

## 🔴 ESCENARIO 2 — INTERNET DEL LOCAL CAÍDO (POS OFFLINE)

### Síntoma
- POS muestra badge amarillo: **"OFFLINE — Se sincronizará al reconectar"**
- Cajeros reportan que "no hay internet"

### Diagnóstico
```bash
# 1. ¿Es el local o el nodo?
ssh korvex-host 'ping -c 3 8.8.8.8'
# Si nodo responde = internet del local caído
# Si nodo NO responde = nodo sin internet (raro, tiene Tailscale)

# 2. Verificar Tailscale
ssh korvex-host 'tailscale status'
# Debe mostrar "active" y peers conectados
```

### Acción (EN EL LOCAL DEL CLIENTE — físico)
```bash
# 1. Reiniciar router/modem del local
# 2. Verificar cable Ethernet / WiFi
# 3. Si es 4G backup: verificar que el router failover funcionó

# 4. EN EL NODO: verificar que POS sigue accesible por Tailscale
ssh korvex-host 'curl -s -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping'
# Debe responder {"message":"pong"}
```

### Cuando vuelve internet (verificación automática)
```bash
# 1. Badge en POS se pone verde: "Sincronizando..."
# 2. Verificar sincronización:
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
# Facturas offline sincronizadas
offline_sync = frappe.get_all(\"ECF\", filters={\"estado\": \"Aceptado\", \"creation\": [\">\", frappe.utils.add_days(frappe.utils.now(), -1)]}, fields=[\"name\", \"encf\", \"track_id\"], limit=5)
for f in offline_sync: print(f.name, f.encf, f.track_id)

# Facturas que quedaron pendientes
pend = frappe.get_all(\"ECF\", filters={\"estado\": [\"Pendiente\", \"Error\"]}, pluck=\"name\")
print(f\"Pendientes: {len(pend)}\")
"'
```

### Verificación
- ✅ Badge POS: "Sincronizado ✓" (verde)
- ✅ e-CF Pendientes: 0 o bajando
- ✅ Stock sincronizado (comparar con conteo físico si hay duda)

---

## 🔴 ESCENARIO 3 — NODO CAÍDO / SERVICIOS DOCKER PARADOS

### Síntoma
- `curl https://korvexcio.korvexdev.cc/api/method/ping` → timeout / connection refused
- `ssh korvex-host` entra pero `docker ps` muestra contenedores "Exited" o "Restarting"

### Diagnóstico
```bash
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose ps -a'
# Buscar contenedores con STATUS != "Up"
# Orden de dependencia: db → redis-queue → redis-cache → backend → queue-short → queue-long → scheduler → websocket → frontend
```

### Acción — Reinicio ordenado (respeta dependencias)
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05

# 1. Parar todo limpio
docker compose stop

# 2. Levantar en orden
docker compose up -d db
sleep 5
docker compose up -d redis-queue redis-cache
sleep 3
docker compose up -d backend
sleep 10
docker compose up -d queue-short queue-long scheduler websocket
sleep 5
docker compose up -d frontend

# 3. Verificar
docker compose ps
'
```

### Verificación
```bash
# Health checks
ssh korvex-host 'curl -s -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping'
# {"message":"pong"}

ssh korvex-host 'curl -s http://127.0.0.1:4000/health'
# {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}

# KORVIS intacto
systemctl status korvex-api --no-pager
curl -s http://127.0.0.1:4000/health
```

---

## 🔴 ESCENARIO 4 — SECUENCIA eNCF AGOTADA

### Síntoma
- Al facturar: **"No hay una Secuencia eNCF configurada para [Company], tipo E32"**
- O alerta en dashboard: "Quedan < 100 números en secuencia VLJ-E32"

### Diagnóstico
```bash
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
seqs = frappe.get_all(\"Secuencia eNCF\", fields=[\"company\", \"tipo_ecf\", \"desde\", \"hasta\", \"siguiente\", \"fecha_vencimiento\"], order_by=\"company, tipo_ecf\")
for s in seqs:
    quedan = s.hasta - s.siguiente + 1
    alerta = \" ⚠️ AGOTADA\" if quedan <= 0 else (\" ⚠️ <100\" if quedan < 100 else \"\")
    print(f\"{s.company} {s.tipo_ecf}: {s.siguiente}/{s.hasta} = {quedan} quedan{alerta}\")
"'
```

### Acción
```bash
# 1. Pedir nuevo rango a DGII (CerteCF) — el contador lo hace
# 2. En UI: Menú → Fiscal → Secuencias eNCF → Nueva
#    Company: VLJ (o ESE)
#    Tipo: E32 (o E31/E34)
#    Desde: [nuevo desde DGII]
#    Hasta: [nuevo hasta DGII]
#    Siguiente: [igual a Desde]
#    Vencimiento: [fecha DGII, usualmente 1 año]
#    Guardar

# 3. Verificar
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
s = frappe.get_doc(\"Secuencia eNCF\", \"VAPERIA LA J Y EL JALAPEÑO-E32\")
print(f\"Nueva: {s.desde} - {s.hasta}, siguiente: {s.siguiente}\")
"'
```

---

## 🔴 ESCENARIO 5 — GIT PULL NO APLICÓ (GIT STATUS SUCIO EN SERVIDOR)

### Síntoma
- Hiciste `git push` en DEV
- En servidor: `git pull` dice "Already up to date" pero el código NO cambió
- O `git pull` falla silenciosamente

### Diagnóstico
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05
git status --short
# Si muestra algo (M, ??, etc.) = STATUS SUCIO
git log --oneline -1
# Compara con el SHA que empujaste en DEV
'
```

### Acción
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05

# 1. Backup de cambios locales (por si acaso)
git stash push -m "auto-stash before pull $(date +%F-%H%M)"

# 2. Pull limpio
git pull --ff-only origin feat/ecf

# 3. Verificar SHA
git log --oneline -1
# Debe coincidir con el commit que empujaste

# 4. Rebuild imagen si cambió Dockerfile / compose / requirements
docker compose build backend

# 5. Reiniciar servicios Python (regla: después de cualquier cambio de código/app)
docker compose restart backend queue-short queue-long scheduler websocket

# 6. Migrate (por si hay migraciones nuevas)
docker compose exec -T backend bench --site korvexcio.korvexdev.cc migrate

# 7. Verificar
curl -s -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping
'
```

---

## 🔴 ESCENARIO 6 — MARIADB / REDIS EXPUESTOS EN 0.0.0.0 (PELIGRO)

### Síntoma
- `ss -tlnp` en el nodo muestra `0.0.0.0:3306` o `0.0.0.0:6379`
- **Esto es CRÍTICO** — expone bases de datos a la LAN/Internet

### Diagnóstico
```bash
ssh korvex-host 'ss -tlnp | grep -E "3306|6379|6380"'
# MALO:  0.0.0.0:3306  LISTEN
# BUENO: 127.0.0.1:3306 LISTEN
```

### Acción
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05

# 1. Verificar compose actual
grep -A5 "ports:" docker/compose.s05.yaml
# NO debe haber "3306:3306" ni "6379:6379" sin "127.0.0.1:"

# 2. Corregir compose (puertos solo en loopback)
# En compose.s05.yaml, servicios db, redis-queue, redis-cache:
# ports:
#   - "127.0.0.1:3306:3306"    # MariaDB
#   - "127.0.0.1:6379:6379"    # Redis queue
#   - "127.0.0.1:6380:6379"    # Redis cache

# 3. Recrear contenedores
docker compose up -d --force-recreate db redis-queue redis-cache

# 4. Verificar
ss -tlnp | grep -E "3306|6379|6380"
# Debe mostrar SOLO 127.0.0.1:
'
```

### Verificación
```bash
# Desde laptop (fuera del nodo) — DEBE FALLAR
curl -v telnet://korvex-node1.local:3306 2>&1 | head -5
# Connection refused / timeout = BIEN

# Desde dentro del nodo — DEBE FUNCIONAR
ssh korvex-host 'mysql -h 127.0.0.1 -u root -p"$DB_ROOT_PASSWORD" -e "SELECT 1"'
redis-cli -h 127.0.0.1 -p 6379 ping
# PONG = BIEN
```

---

## 🔴 ESCENARIO 7 — DISCO > 80%

### Síntoma
- Alarma del nodo: "Disco 85% usado"
- `df -h /` muestra > 80%

### Diagnóstico
```bash
ssh korvex-host '
df -h /
echo "--- Docker ---"
docker system df
echo "--- Volúmenes KORVEXCIO ---"
docker volume ls --filter name=korvexcio
for v in $(docker volume ls --filter name=korvexcio -q); do
  echo "Volume: $v"
  docker run --rm -v $v:/vol alpine du -sh /vol
done
'
```

### Acción
```bash
ssh korvex-host '
# 1. Limpiar build cache de Docker (seguro, no borra datos)
docker builder prune -f

# 2. Limpiar contenedores parados
docker container prune -f

# 3. Limpiar imágenes sin usar (TAGGED, no untagged)
docker image prune -f

# 4. Verificar backups viejos (>14 días los borra el timer, pero revisar)
ls -lh /home/korvex/frappe_docker-korvexcio-s05/backups/

# 5. Verificar logs de contenedores (a veces crecen sin rotar)
docker system df -v | head -30
'
```

### Verificación
```bash
ssh korvex-host 'df -h /'
# Debe bajar a < 70%
```

---

## 🔴 ESCENARIO 8 — KORVIS ROTO TRAS DEPLOY KORVEXCIO

### Síntoma
- Bot de WhatsApp (ADAP) no responde
- `systemctl status korvex-api` muestra "failed" o "activating"
- `curl http://127.0.0.1:4000/health` falla o da `{"status":"degraded",...}`

### Diagnóstico
```bash
ssh korvex-host '
# 1. Estado servicios KORVIS
systemctl status korvex-api korvex-dashboard korvex-ops --no-pager

# 2. Logs recientes
journalctl -u korvex-api -n 50 --no-pager

# 3. Health check
curl -s http://127.0.0.1:4000/health

# 4. ¿Chocó puertos? (KORVEXCIO usa 8080, 3306, 6379, 6380 — KORVIS usa 4000, 5432, 6379 propio)
ss -tlnp | grep -E "4000|5432|8080|3306|6379"
'
```

### Acción
```bash
ssh korvex-host '
# 1. Reiniciar solo KORVIS (NO tocar KORVEXCIO)
systemctl restart korvex-api korvex-dashboard korvex-ops

# 2. Esperar y verificar
sleep 10
systemctl status korvex-api --no-pager
curl -s http://127.0.0.1:4000/health

# 3. Si sigue fallando: revisar logs de Postgres/Redis de KORVIS
systemctl status postgresql --no-pager
systemctl status redis --no-pager

# 4. Rollback KORVEXCIO si fue el deploy el que lo rompió
cd /home/korvex/frappe_docker-korvexcio-s05
git log --oneline -3
git checkout HEAD~1  # vuelta al commit anterior
docker compose build backend
docker compose restart backend queue-short queue-long scheduler websocket
docker compose exec -T backend bench --site korvexcio.korvexdev.cc migrate
'
```

### Verificación
```bash
# KORVIS
curl -s http://127.0.0.1:4000/health
# {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}

# KORVEXCIO
curl -s -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping
# {"message":"pong"}

# Los 2 bots de WhatsApp responden (probar desde WhatsApp real)
```

---

## 🔴 ESCENARIO 9 — BACKUP FALLÓ / RESTAURACIÓN NECESARIA

### Síntoma
- `backup-status.json` muestra `"ok": false`
- O necesitas restaurar a punto anterior

### Diagnóstico
```bash
ssh korvex-host '
cat /home/korvex/frappe_docker-korvexcio-s05/backup-status.json
# {"timestamp": "...", "ok": false, "message": "..."}

# Ver logs del timer
journalctl -u korvexcio-backup -n 20 --no-pager
'
```

### Acción — Backup manual
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05
docker compose exec -T backend bench --site korvexcio.korvexdev.cc backup
# Output: Backup Summary... database.sql.gz XXX KiB... OK
'
```

### Acción — Restauración (EN SITE DESECHABLE, NUNCA EN PRODUCCIÓN DIRECTO)
```bash
ssh korvex-host '
cd /home/korvex/frappe_docker-korvexcio-s05

# 1. Crear site de prueba
ADMIN_PW=$(openssl rand -base64 24)
docker compose exec -T backend bench new-site restore-test.korvexdev.cc \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_PW" \
  --install-app erpnext

# 2. Restaurar backup MÁS RECIENTE
BACKUP_FILE=$(ls -t backups/*database.sql.gz | head -1)
docker compose exec -T backend bench --site restore-test.korvexdev.cc restore "$BACKUP_FILE"

# 3. VERIFICAR CONTENIDO (no tamaño)
docker compose exec -T backend bench --site restore-test.korvexdev.cc console -c "
import frappe
print(\"Companies:\", frappe.get_all(\"Company\", pluck=\"name\"))
print(\"Sales Invoices:\", frappe.db.count(\"Sales Invoice\"))
print(\"ECFs:\", frappe.db.count(\"ECF\"))
print(\"Items:\", frappe.db.count(\"Item\"))
print(\"Users:\", frappe.get_all(\"User\", filters={\"enabled\": 1}, pluck=\"email\"))
"

# 4. Si todo bien → borrar site de prueba
docker compose exec -T backend bench drop-site restore-test.korvexdev.cc --force
'
```

---

## 🔴 ESCENARIO 10 — CERTIFICADO DIGITAL VENCIDO / POR VENCER

### Síntoma
- Alerta en dashboard: "Certificado digital vence en X días"
- e-CF pasan a "Error" por certificado inválido

### Diagnóstico
```bash
ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc console -c "
import frappe
certs = frappe.get_all(\"DGII Digital Certificate\", fields=[\"company\", \"valid_until\", \"certificate\"], filters={\"valid_until\": [\"<\", frappe.utils.add_days(frappe.utils.nowdate(), 30)]})
for c in certs:
    dias = (c.valid_until - frappe.utils.nowdate()).days
    print(f\"{c.company}: vence en {dias} días ({c.valid_until})\")
"'
```

### Acción
```bash
# 1. Contador / proveedor (Alanube, Cámara de Comercio, etc.) renueva certificado
# 2. Te entregan: archivo .p12 nuevo + contraseña
# 3. EN SERVIDOR (a mano, secretos no viajan por web):
ssh -t korvex-host "sudo -u korvex bash -c '
cd /home/korvex/frappe_docker-korvexcio-s05
# Subir .p12 por scp desde tu máquina, luego:
docker compose cp nuevo_certificado.p12 backend:/tmp/nuevo_certificado.p12
'"

# 4. En UI (Dueño): Menú → Fiscal → DGII Digital Certificate → Editar → Adjuntar nuevo .p12 + contraseña
# 5. Verificar que "valid_until" se actualizó
```

---

## 📋 COMANDOS DE REFERENCIA RÁPIDA

```bash
# ===== ACCESO =====
ssh korvex-host                    # Entrar al nodo (Tailscale)
ssh -t korvex-host "sudo ..."      # Comandos con sudo (pide contraseña)

# ===== ESTADO GENERAL =====
ssh korvex-host "cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose ps"
ssh korvex-host "systemctl status korvex-api --no-pager"
ssh korvex-host "curl -s http://127.0.0.1:4000/health"
ssh korvex-host "curl -s -H \"Host: korvexcio.korvexdev.cc\" http://127.0.0.1:8080/api/method/ping"

# ===== LOGS =====
ssh korvex-host "journalctl -u korvexcio-backend -n 50 --no-pager"
ssh korvex-host "cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose logs backend --tail=50"

# ===== BENCH COMANDOS =====
ssh korvex-host "cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose exec -T backend bench --site korvexcio.korvexdev.cc [comando]"
# Ejemplos:
#   migrate
#   run-tests --app korvexcio
#   console -c \"import frappe; print(frappe.db.count('Sales Invoice'))\"
#   clear-cache
#   clear-website-cache

# ===== REINICIOS =====
# Solo KORVEXCIO Python services (después de code changes):
ssh korvex-host "cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose restart backend queue-short queue-long scheduler websocket"

# Todo KORVEXCIO stack:
ssh korvex-host "cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose restart"

# Solo KORVIS:
ssh korvex-host "systemctl restart korvex-api korvex-dashboard korvex-ops"

# ===== VERIFICACIÓN RED =====
ssh korvex-host "ss -tlnp | grep -E \"3306|6379|6380|8080|4000|5432\""
# Solo 127.0.0.1 para 3306/6379/6380

# ===== DISCO =====
ssh korvex-host "df -h / && docker system df"

# ===== BACKUP =====
ssh korvex-host "cat /home/korvex/frappe_docker-korvexcio-s05/backup-status.json"
```

---

## 📞 ESCALACIÓN

| Nivel | Qué | Quién | Tiempo |
|-------|-----|-------|--------|
| **1** | Reinicios, verificaciones básicas | Dueño / Encargado local | Inmediato |
| **2** | Logs, diagnóstico profundo, contingencia | Yedin (dev) | < 30 min |
| **3** | Infraestructura (disco, red, hardware) | Yedin + proveedor hosting | < 2 h |
| **4** | DGII / Proveedor fiscal caído | Contador + Proveedor (Alanube/ECF SSD) | Según SLA proveedor |

---

## ✅ CHECKLIST POST-INCIDENTE

Después de **CUALQUIER** incidente:

- [ ] ¿Se resolvió la causa raíz o fue parche?
- [ ] ¿Se documentó en `PROGRESO.md` / bitácora?
- [ ] ¿Quedó deuda técnica? → Anotar en `HANDOFF.md` sección "Deuda técnica"
- [ ] ¿KORVIS sigue sano? (`systemctl status korvex-api` + health check)
- [ ] ¿Backup de esa noche corrió OK? (`backup-status.json`)
- [ ] ¿Hay que avisar al contador/cliente? (si afectó facturas)

---

**Última actualización:** 2026-09-05
**Versión KORVEXCIO:** `feat/ecf` (commit actual)
**Probado en:** korvex-node1 (mini PC, Tailscale, Docker Compose)

*Este RUNBOOK vive en `docs/RUNBOOK.md` del repo. Mantén una copia impresa en el local del cliente.*