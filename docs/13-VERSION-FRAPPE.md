# 13 — Decisión de versión de Frappe

> Slice **S0.5**, ejecutado el 31/08/2026 sobre `korvex-node1`.
> Este documento cierra D2 con evidencia operativa. No crea sites; eso es S0.6.

---

## Decisión

**D2 — KORVEXCIO arranca en Frappe/ERPNext v16.**

La imagen v16 construyó ERPNext, POSNext y URY sin un error de compatibilidad. El
stack aislado arrancó, sus nueve servicios de runtime quedaron arriba, MariaDB
quedó healthy y `bench version` reconoció las cuatro apps.

No se probó v15. El plan ordena bajar a v15 **solo si alguna app revienta en v16**;
esa condición no ocurrió. Probarla de todos modos habría sido adelantar trabajo sin
cambiar la decisión.

---

## Matriz real del intento v16

| Componente | Referencia probada | Resultado dentro de la imagen |
|---|---|---|
| `frappe/frappe` | `version-16` · SHA `5cba016e86b54b57f34a3864282b92300ef20fb0` | `frappe 16.32.0` |
| `frappe/erpnext` | `version-16` · SHA `b24c9eba551905e256e336ff170a91a92d197a2f` | `erpnext 16.33.0` |
| `DeeloaSociety/posnext` | `develop` · SHA `4c4f13bc118defcd783a5571b9e71748e5bd6a03` | `pos_next 1.12.0` |
| `ury-erp/ury` | `develop` · SHA `f6d49430df2328df037e1dc53afe0b8b18efab2c` | `ury v3.0.0-beta.1` |

`frappe_docker` se clonó fuera del repo, en un directorio temporal, con SHA
`ba450260c52eb1b186fe7ba0bec8b61299bb9037`. La imagen resultante fue:

```text
ID=sha256:6ed8f523d2795fdc4c7a808b7cfe8cb50c572d2cabc8f2e6b2485d5e1f4b2ee2
SIZE=1101763085
```

### Una rareza que no se debe olvidar

POSNext y URY no publican branch `version-16`. Ambos se probaron desde `develop`,
tal como reportó su upstream el día del spike. URY tampoco publicaba branch
`version-15`; su documentación de instalación todavía mencionaba ERPNext v15.

Esto no impidió el build ni el arranque, pero una rama `develop` es mutable. Antes
del go-live, S1.2 debe construir desde referencias inmutables o desde mirrors de
Korvex con el SHA probado. **No se actualiza una app de producción siguiendo el
HEAD de `develop`.**

---

## Configuración de aislamiento aplicada

- Proyecto Compose: `korvexcio`.
- Red propia: `korvexcio_default`.
- Volúmenes propios: `korvexcio_db-data`, `korvexcio_sites` y
  `korvexcio_redis-queue-data`.
- Imagen propia: `korvexcio:16`.
- Publicación host: solo `127.0.0.1:8080`.
- MariaDB y los dos Redis: sin puertos publicados al host.
- Límites sumados: 5,504 MiB, por debajo del tope aproximado de 6 GiB.
- `.env` temporal en el nodo: modo `600`; la contraseña se generó allí y no
  apareció en consola, repo ni este documento.

Límites por servicio:

| Servicio | Límite |
|---|---:|
| MariaDB | 1,536 MiB |
| backend | 768 MiB |
| queue-long | 768 MiB |
| configurator | 512 MiB |
| queue-short | 512 MiB |
| scheduler | 384 MiB |
| frontend | 256 MiB |
| websocket | 256 MiB |
| redis-cache | 256 MiB |
| redis-queue | 256 MiB |

---

## Evidencia de verificación

### Build

Comando:

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps.json \
  --tag=korvexcio:16 \
  --file=images/layered/Containerfile .
```

Salida decisiva:

```text
#16 exporting manifest list sha256:6ed8f523d2795fdc4c7a808b7cfe8cb50c572d2cabc8f2e6b2485d5e1f4b2ee2
#16 naming to docker.io/library/korvexcio:16 done
#16 unpacking to docker.io/library/korvexcio:16 30.7s done
#16 DONE 104.1s
Exit code: 0
```

### Servicios y versiones

Comandos:

```bash
docker compose -p korvexcio --project-directory . \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f compose.s05.yaml ps -a

docker compose -p korvexcio --project-directory . \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f compose.s05.yaml exec -T backend bench version
```

Salida decisiva:

```text
korvexcio-backend-1        Up
korvexcio-configurator-1   Exited (0)
korvexcio-db-1             Up (healthy)
korvexcio-frontend-1       Up   127.0.0.1:8080->8080/tcp
korvexcio-queue-long-1     Up
korvexcio-queue-short-1    Up
korvexcio-redis-cache-1    Up
korvexcio-redis-queue-1    Up
korvexcio-scheduler-1      Up
korvexcio-websocket-1      Up

erpnext 16.33.0  ()
frappe 16.32.0  ()
pos_next 1.12.0  ()
ury v3.0.0-beta.1  ()
```

`configurator` es un job de configuración de una sola corrida; `Exited (0)` es
su estado correcto, no un servicio caído.

### Memoria

Comando:

```bash
docker stats --no-stream
```

Salida real de todos los servicios que seguían en ejecución:

```text
korvexcio-frontend-1       6.668MiB / 256MiB   2.60%
korvexcio-websocket-1      35.52MiB / 256MiB  13.87%
korvexcio-queue-short-1    46.55MiB / 512MiB   9.09%
korvexcio-scheduler-1      49.47MiB / 384MiB  12.88%
korvexcio-queue-long-1     46.54MiB / 768MiB   6.06%
korvexcio-backend-1      143.3MiB / 768MiB   18.66%
korvexcio-redis-cache-1     5.543MiB / 256MiB   2.17%
korvexcio-redis-queue-1     5.406MiB / 256MiB   2.11%
korvexcio-db-1           103.6MiB / 1.5GiB    6.75%
```

Ninguno de esos nueve servicios superó su límite. `configurator` ya había
terminado con `Exited (0)`, así que `docker stats` no capturó su pico de runtime;
su límite configurado de 512 MiB sí quedó validado por `docker compose config`.

### Sockets y puertos publicados

Comandos:

```bash
ss -tlnp | grep -E '3306|6379|8080'
docker port korvexcio-frontend-1
docker port korvexcio-db-1
docker port korvexcio-redis-cache-1
docker port korvexcio-redis-queue-1
```

Salida real:

```text
LISTEN 0 4096 127.0.0.1:6379 0.0.0.0:*
LISTEN 0 4096 127.0.0.1:8080 0.0.0.0:*
8080/tcp -> 127.0.0.1:8080
```

El `6379` visible ya pertenecía a KORVIS. Los tres `docker port` de MariaDB y
Redis de KORVEXCIO no devolvieron salida: no publican puertos al host.

### KORVIS y disco

Comandos:

```bash
systemctl status korvex-api --no-pager
curl -s http://127.0.0.1:4000/health
df -h /
docker system df
```

Salida real:

```text
Active: active (running) since Sat 2026-08-29 10:24:30 AST
{"status":"ok","checks":{"postgres":"ok","redis":"ok"},"uptime":159537}
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   34G   60G   37% /
Build Cache   42   0   14.84GB   7.154GB
```

La línea base se tomó antes del build con:

```bash
df -h /
```

Salida real previa:

```text
Filesystem                         Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   19G   75G  20% /
```

Antes del build había 75 GB libres. Después quedaron 60 GB: el ensayo consumió
aproximadamente 15 GB entre imagen y caché de build. Sigue bajo la alarma de 80%,
pero el consumo fue mayor que el estimado de 5–8 GB.

---

## Advertencias y deuda

1. **🟡 Branches mutables de POSNext y URY.** Mitigación actual: SHAs probados
   registrados arriba e imagen identificada por digest. Cura: mirrors/tags inmutables
   antes de S1.2. Estimado: 1 hora.
2. **🟡 Caché de build: 7.154 GB reclamables.** No se podó limpiar dentro de
   S0.5 porque borrar caché no es parte del slice. Cura: revisar y ejecutar
   `docker builder prune` como mantenimiento autorizado. Estimado: 15 minutos.
3. **⚪ Warnings upstream durante assets.** Vite reportó chunks mayores de 500 kB,
   imports no compatibles con su futuro loader nativo y una duplicidad de rango de
   `autoprefixer`. No impidieron el build ni el arranque. Se revisan si causan un fallo
   observable en S0.8; no se modifica upstream.

## No verificado en este slice

- Crear un site e instalar las apps dentro de su base: corresponde a S0.6.
- Login, POS, ventas u operación offline: corresponde a S0.8.
- Compatibilidad funcional de URY/POSNext juntos: S0.8 hace la prueba dura.
- v15: no se ejecutó porque v16 no activó la condición de fallback.

---

## D23 — Parche de seguridad 22/10/2026 (excepción a la versión congelada por D2)

> Aprobado por Yedin el 22/10/2026. D2 fijó la línea **v16** el 31/08 y desde
> entonces no se movió la versión. D23 es una **excepción explícita por
> seguridad**, no una reapertura de D2: seguimos en v16, solo se sube el parche.

**Por qué:** la versión desplegada (Frappe 16.32.0 + ERPNext 16.33.0) estaba
afectada por **GHSA-9pp9-wgp9-3p3j** (RCE en Frappe por path traversal, corregido
en 16.34.0) y **GHSA-v38v-9h2p-hr8v** (SQL injection en ERPNext, corregido en
16.34.0), más ~15 advisories más de Frappe/ERPNext. Que el stack no sea público
reduce la exposición, no la elimina.

**Decisión:** subir a los últimos parches v16 publicados el 22/10/2026:

| Componente | Antes | Después | Referencia usada en el build |
|---|---|---|---|
| `frappe/frappe` | 16.32.0 | **16.53.0** | `version-16` = tag `v16.53.0` (`e8d41dd`, verificado igual antes del build) |
| `frappe/erpnext` | 16.33.0 | **16.52.1** | tag `v16.52.1` (`ade850b`) |
| `pos_next` | 1.12.0 (fork, `92b5c93`) | 1.12.0 (fork, `92b5c93`) | `yedinrumba-eng/posnext` rama `korvex` (HEAD = `92b5c93` al construir) |
| `korvexcio` | 0.0.1 (`c0373b1`) | 0.0.1 (`c0373b1`) | tag `node-deploy-2026-10-22` → `c0373b1` |
| `ury` (en la imagen, **no instalada en el site**) | 3.0.0-beta.1 | 3.0.0-beta.1 | tag `v3.0.0-beta.1` |

`pos_next` y `korvexcio` se mantuvieron en los commits que estaban corriendo; se
comprobó archivo por archivo (sha256 de todos los archivos versionados en git) que
la imagen nueva trae exactamente esos commits.

**Imagen:** `korvexcio:16.53.0-erpnext16.52.1`
(`sha256:0edb0d4954ec211738f494f236a7850987109a2c164f17fcecc027781e5dd530`),
construida con la misma receta de arriba (`images/layered/Containerfile`,
`apps.json` como secreto de BuildKit, `FRAPPE_BRANCH=version-16`). El `apps.json`
de este repo es el que se usó, ya con referencias fijas (tags) en vez de `develop`.
`FRAPPE_BRANCH` sigue en `version-16` porque la imagen base `frappe/build` todavía
no publica tag `v16.53.0`; la versión real se confirmó dentro de la imagen.

### Lo que se encontró al prepararlo (lección pagada)

El contenedor `backend` no corría lo mismo que la imagen: `apps/korvexcio` y
`apps/pos_next` se habían re-clonado **a mano dentro del contenedor** (capa
escribible), mientras los workers seguían con el código horneado en la imagen, y la
imagen original (`596354fb51a1`) ya no existía en el almacén de Docker. Un
`docker commit` falló por eso. **Recrear el contenedor habría borrado el estado
real sin vuelta atrás.** Desde este parche todos los servicios corren el mismo
código horneado en la imagen — se acabó el "arreglo en caliente" dentro del
contenedor (regla 7 de `CLAUDE.md`).

### Rollback

- Imagen de rollback: `korvexcio:rollback-20261022`
  (`sha256:75469083d5cffbdd196d991483f5c33a61328492ac8a0894db1e623ed9e8d565`),
  snapshot exacto del filesystem del `backend` viejo (`docker export` →
  `docker import`, con entrypoint/cmd/user/env restaurados). Contiene Frappe
  16.32.0, ERPNext 16.33.0, `korvexcio` `c0373b1`, `pos_next` `92b5c93`.
- Respaldo fresco tomado antes del cambio con `bench backup --with-files`
  (BD 1.2 MiB gz con 765 tablas y `Dump completed`; públicos 4.3 MiB; privados
  10 KiB), además del backup nocturno del nodo del 22/10 (KORVEXCIO DB OK + archivos OK).
- Cómo volver: poner `FRAPPE_VERSION=rollback-20261022` en el `.env` del compose,
  `up -d`, y **restaurar el respaldo** (la migración ya alteró el esquema).

### Verificación (22/10/2026)

```text
bench migrate                       -> EXIT=0, 0 tracebacks
bench version                       -> erpnext 16.52.1 · frappe 16.53.0 · korvexcio 0.0.1 · pos_next 1.12.0 · ury 3.0.0-beta.1
compose ps                          -> 9 servicios Up, db (healthy), configurator Exited (0)
GET /login · /pos · /api/method/ping -> 200 · 200 · 200 ({"message":"pong"})
bench doctor                        -> Workers online: 2 (scheduler deshabilitado, igual que antes)
logs backend/queue/scheduler        -> 0 tracebacks desde el cambio · Error Log nuevos: 0
mem_limit                           -> sin cambios (768/512/768/384/256/256 MiB, db 1536)
```

`bench build` no hizo falta: la receta hornea los assets en la imagen y el
entrypoint los enlaza al volumen al arrancar.

### No verificado

- Suite `bench run-tests --app korvexcio` sobre 16.53 (no se corrió en este parche).
- Flujo de venta real en el POS (login de cajero + venta E32) sobre la versión nueva.
- El scheduler del site estaba y sigue deshabilitado; no se probó con scheduler activo.
