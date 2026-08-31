# PROGRESO — KORVEXCIO (VAPELAND)

> Bitácora del proyecto. **Se escribe por hito, no por día ni por sesión**
> (`CONVENCIONES.md` §8). Un hito es: algo se cerró, algo se rompió, algo se
> decidió, o algo cambió de estado en el mapa.
>
> Una entrada que solo dice "trabajé en X" no sirve para nada.

---

## 2026-08-31 — Descubrimiento

**Qué se hizo:** sesión de descubrimiento en Cowork. Research de facturación
electrónica en RD, benchmark de ERP/POS open source, hardware de punto de
venta, y regulación fiscal del rubro. Se leyeron `_KORVEX-OPS` (convenciones,
roadmap, inventario) y `KORVIS` (arquitectura multi-tenant, lecciones, categorías
de negocio) como referencias.

**Qué se decidió:**
- **D1** — Base: **ERPNext/Frappe v15**. Se descartaron el stack de KORVIS, Odoo
  CE y el híbrido. *(Decisión de Yedin. Las tres facturas están escritas en
  `HANDOFF.md`.)*
- **D2** — v15, no v16: el ecosistema de apps de terceros no ha migrado.
- **D3** — e-CF vía **proveedor certificado** (`ecf-dgii`/ECF SSD, MIT, Python),
  detrás de una interfaz `FiscalProvider`.
- **D4** — **MVP: POS + inventario + e-CF.** Sin cafetería, sin CRM, sin
  asistente de IA. ⚠️ **Marcado por Yedin para revisar con el cliente.**
- **D5** — Posicionamiento: **retail + food genérico con módulos**, no vertical
  vape-only.

**Qué se encontró que cambia el proyecto:**
- 🔴 **15/11/2026** — e-CF obligatorio para pequeños/micro/no clasificados.
  **76 días.** Multa: 5 a 50 salarios mínimos.
- 🔴 **El e-CF de RD no existe en Frappe.** `dgii-compliance` (3 estrellas)
  solo hace NCF tradicional. Hay que escribir `korvex_ecf`.
- 🟢 **`ecf-dgii`** (PyPI, MIT, mayo 2026) es Python y es de un proveedor
  certificado. Es lo que hace coherentes las decisiones D1 y D3.
- 🟠 **Ley 30-26** (19/06/2026): ISC **55% ad-valorem** a vapes. Puede mover el
  margen de todo el rubro del cliente.
- 🟠 **El cliente no ha confirmado RNC.** Sin RNC + certificado digital no hay
  e-CF posible. El certificado tarda 3–10 días hábiles.

**Deuda que nace con el proyecto:**
- La carpeta `VAPELAND` viola §1 de `CONVENCIONES.md` (carpeta = cliente = repo;
  esto es un producto de KORVEX). Mismo error que `KORVIS`.
- Sin repo ni remote (§6).
- Sin entrada en `data/korvex.json` ni en `BITACORA.md` de `_KORVEX-OPS` (§7.2).

**Entregado:** `HANDOFF.md` · `README.md` · `PRD.md` · `TECH_STACK.md` ·
`CLAUDE.md` · `PROGRESO.md` · `docs/01` a `docs/05`.

**Siguiente:** ver "Lo primero que se hace en Claude Code" en `HANDOFF.md`.
El paso 2 (spike de `ecf-dgii` contra TesteCF, timebox 2 días) es el que
decide si el proyecto mantiene su forma.

---

## 2026-08-31 (tarde) — Nomenclatura y cliente en movimiento

**Qué se decidió:**
- **El producto se llama KORVEXCIO** (juego con *comerCIO*). **Sin guion** —
  `KORVEX-CIO` parte la palabra y mata el juego. Descartados: KORVEX ERP ("ERP"
  espanta a un colmadero), KORVEX POS (se queda corto y compite en precio),
  KORVEX CAJA, KORVEX COMERCIO, KORVEX RETAIL OPS.
- **El asistente de WhatsApp se llama KORVIS** — *the AI Assistant by Korvex*.
  Marca propia dentro de la casa KORVEX. `ADAP` es su **primer cliente**, no el
  nombre del producto. ⚠️ Yedin escribió "KORVIS" y "KORVIX" — se adoptó
  **KORVIS**; si es con X, es un `sed` de un minuto.
- **La familia de marcas:** KORVEX (la casa) · KORVEXCIO (este producto) ·
  KORVIS (el asistente). VAPELAND y ADAP son **clientes**.
- **Carpeta:** Yedin renombra `C:\PROYECTOS\VAPELAND` → `C:\PROYECTOS\KORVEXCIO`
  él mismo. No se mueve a `PLATAFORMAS\` por ahora.

**Qué se movió del lado del cliente:**
- 🟢 **Yedin ya está hablando con el dueño para que registre la compañía y saque
  el RNC.** Era el bloqueante #1 del camino crítico. Sigue abierto hasta que
  haya RNC en mano, pero está en movimiento.

**Qué se profundizó:**
- **Ley 30-26** documentada a fondo en `docs/02-FISCAL-RD.md`: promulgada el
  **18/06/2026**, 55% ad-valorem (párrafo XI art. 375), base = precio de venta
  al por menor sin deducciones, partidas 8543.40.11 / 8543.40.12 / 2404.12.11 /
  3824.99.94, y el art. 44 que exige **registro, fianza y licencia** a
  fabricantes e importadores.
- **Consecuencia para el POS:** una sola línea de impuesto al consumidor
  (ITBIS 18%). El ISC viene dentro del costo. Simplifica el motor.
- ⚠️ **Hueco sin cerrar:** ninguna fuente pública confirma la fecha exacta de
  vigencia del ISC de vapes. Los calendarios de prensa listan casinos, cheques y
  seguros — no los vapes. Pregunta para el contador.

**Actualizado:** los 11 archivos, con `ADAP` → `KORVIS` y
`KORVEX Retail Ops` → `KORVEXCIO`. Las rutas en disco (`C:\PROYECTOS\ADAP`,
`ADAP/docs/...`) se dejaron con el nombre real de hoy a propósito.

---

## 2026-08-31 (noche) — El modelo de trabajo, antes de escribir código

**La pregunta de Yedin, que era la correcta:** *"¿vamos a clonar un repo y
adaptarlo para trabajar más rápido, o qué?"*

**La respuesta: NO.** Clonar `frappe/erpnext` y meterle mano significa que el
día que salga un parche de seguridad o la v16, no lo puedes tomar: tu `git pull`
es un campo de conflictos contra tu propio código. Te quedas congelado en la
versión que clonaste, manteniendo un ERP entero tú solo.

**El modelo correcto**, documentado en `docs/06-COMO-SE-TRABAJA.md`:
el upstream se **instala** (vía `apps.json` con branch fijado), tu código se
escribe **encima**, y el cliente es **configuración**. Igual que no clonas
Next.js para hacer una app de Next.js.

**Corrección de arquitectura:** los documentos decían **dos** apps
(`korvex_ecf` + `korvex_retail`). Pasa a **UNA** app `korvexcio` con dos
**módulos** internos (`ecf` y `retail`). Razón: `apps.json` instala *un repo =
una app*; dos apps son dos repos, dos builds y dos `install-app` por cada alta
de tenant, para separar algo que hoy nadie pide separado. Frappe ya da módulos
dentro de una app. Sacar `ecf/` a su propia app el día que aparezca un cliente
que compre solo el fiscal es un refactor de días.

**Excepción documentada:** **POSNext sí se forkea** — necesita campos fiscales
dominicanos por dentro y no está diseñado para extenderse desde afuera. Fork
propio, rama `korvex`, `upstream` como remote, rebase para traer mejoras.

**Repo creado:** `https://github.com/yedinrumba-eng/KORVEXCIO.git`

**Actualizado:** `CLAUDE.md`, `TECH_STACK.md` (D5), `docs/04-ARQUITECTURA.md`,
`README.md`, `HANDOFF.md` y `PROMPT-CLAUDE-CODE.md` con el nombre de app único y
la regla de no tocar upstream.

---

## 2026-08-31 (cierre) — Barrido de arquitectura de referencia

**Qué pasó.** Antes de mudarse a Claude Code, un último barrido: **~45 repos de
RD** (DGII, e-CF, NCF, 606/607/608, en todos los lenguajes) y **9 localizaciones
fiscales de Frappe/ERPNext** (India, Arabia Saudí, México, Guatemala, Chile,
Ecuador, Argentina, Perú, RD). Resultado en `docs/07-ARQUITECTURA-REFERENCIA.md`.

**⚠️ Nivel de confianza.** Salió de dos subagentes y **se agotó el límite de
fetch antes de poder verificarlo de segunda mano**. Está marcado como tal en el
doc y en el `HANDOFF.md`. **Verificar los 4 repos ⭐ es ahora el paso 1 de la
Fase 0.**

**Lo que cambia el plan:**
- 🟢 **`wilmerm/alanube-python`** (MIT, Python, vivo, reporta los 10 tipos) pasa
  a ser el **candidato #1** del módulo fiscal, por encima de `ecf-dgii`.
- 🟢 **`victors1681/dgii-ecf`** (MIT, TS, 90★) reporta **`sendSummary` (RFCE)** y
  `convertECF32ToRFCE`. Es la primera evidencia de una implementación de RFCE con
  licencia permisiva. Se puede portar legalmente.
- 🟢 **`platinum-place/laravel-dgii`** (MIT) trae **plantillas que renderizan el
  XML del e-CF y del RFCE**. Traducir Blade→Jinja2 es mecánico.
- 🔴 **`rob-erply/dgii_facturacion_electronica` da 404.** Retirado del doc 03.
- 🔴 **No existe ninguna librería Python que haga e-CF directo a la DGII.**
  Confirma que la decisión #2 no era preferencia, era la única salida sensata.
- 🟢 **`korvexcio` sería la primera app de Frappe con e-CF de RD.**

**El aporte más grande — la estructura ya no se diseña desde cero.** De las tres
localizaciones maduras (ZATCA, GST India, CFDI México) salió una estructura de
DocTypes y hooks que el borrador de `04-ARQUITECTURA.md` no tenía:

- **`ecf` como DocType submittable propio**, no custom fields en Sales Invoice
  (el error de México: pierdes `docstatus` como máquina de estados y no puedes
  representar la anulación ni la aprobación comercial).
- **`enqueue_after_commit=True`** — sin eso encolas e-CF de facturas que nunca
  hicieron commit.
- **`ecf_contingencia`**, calcado de `ZATCA Precomputed Invoice`: la única de las
  nueve que resuelve el modo offline de verdad. En RD no es opcional.
- **`doc_events`, nunca `override_doctype_class`** — solo una app puede reclamar
  un DocType.
- **Directorio `custom/*.json`** en vez de `export-fixtures` (corrige el doc 06).
- **Secretos con fieldtype `Password`**, `.p12` como `Attach`, signer en memoria.
- **Jinja2 con el entorno de Frappe** para el XML, con `lstrip_blocks`/
  `trim_blocks` restaurados en `finally`.
- **Tests al estilo India**: `IntegrationTestCase` + `responses` + `time_machine`.
  Es la única de las nueve con cobertura real.

**Mapa de licencias, que es lo que puede costar el producto:** MIT/Apache se
copia · GPL contagia pero ERPNext ya es GPLv3 · **AGPL (`ksa_compliance`,
`posnext`) se lee, no se copia** · **CC BY-NC-ND (Chile) ni se abre** · sin
licencia = inusable, incluido el único firmador XML en Python del ecosistema.

**Actualizado:** `docs/07` (nuevo, 333 líneas) · `HANDOFF.md` (Fase 0 de 5 a 7
pasos + tabla de confianza) · `docs/03` (retirado rob-erply) · `docs/04`
(estructura marcada como superada) · `PROMPT-CLAUDE-CODE.md` (reescrito).

---

## 2026-08-31 (sesión de ejecución) — Plan maestro aprobado, Fase 0 arrancada

**Qué pasó.** Se cerró el paso 1 de la Fase 0 (verificar los 4 repos ⭐), llegó la
**luz verde para instalar en `korvex-node1`** con números medidos en vivo, y se
aprobó el plan maestro completo en fases y microslices.

**El plan vive ahora en `docs/08-BLUEPRINT.md`** (916 líneas, dentro del repo).
Ese documento es la fuente de verdad del **qué** y del **orden**. Este
`PROGRESO.md` es la bitácora del **cuándo** y del **con qué se verificó**.

### Decisiones nuevas — D10 a D19

Detalle y porqué completo en `docs/08-BLUEPRINT.md` §3. Resumen:

| # | Decisión |
|---|---|
| **D10** | Hosting: **`korvex-node1` + Cloudflare Tunnel**. Luz verde con números medidos |
| **D11** | El bench vive **en el nodo, no en la laptop**. Se descarta WSL2 + Docker Desktop en DEV |
| **D12** | **Dos negocios desde v1** — vapería y cafetería entran juntas. **Deroga D4** |
| **D13** | Se planifica para **dos RNC** (caso conservador) |
| **D14** | Cafetería en **modo mostrador**. Mesas/comandas/KDS (URY) se difieren a Fase 7 |
| **D15** | **POS Awesome descartado** — Vue 2 (EOL dic-2023), README en v14, sin offline documentado |
| **D16** | POS: decisión **diferida al spike S0.8** entre POS nativo de ERPNext y POSNext. Sesgo declarado hacia el nativo |
| **D17** | Spike fiscal: **proveedores primero, en paralelo**. El técnico arranca con la respuesta |
| **D18** | **v15 vs v16 se decide con el bench levantado** — es S0.5 |
| **D19** ⭐ | **Un site por CLIENTE, una `Company` de ERPNext por NEGOCIO.** Una sola URL `korvexcio.korvexdev.cc`; el login decide qué ves; el dueño ve las dos y administra sus usuarios. **Revisa D6, no la deroga**: cliente 2 = site propio, innegociable |

**Correcciones a decisiones viejas:**
- **D3 revisada** — `ecf-dgii` solo documenta E31. Pasa a candidato #2. La interfaz
  `FiscalProvider` se mantiene y ahora es *más* necesaria.
- **D4 derogada** por D12.
- **D6 revisada** por D19.
- **D2 cerrada en v16** por S0.5, con evidencia y revisión de seguimiento
  completa.

### Lo que trajo D19 y hay que construir

El aislamiento entre los dos negocios pasa de **físico** (una base de datos por
cada uno) a **lógico** (campo `company` + User Permission). Esa es justo la clase
de riesgo que hay que blindar, y por eso entra **Secure-Vibe** como marco de
seguridad del proyecto (`docs/08-BLUEPRINT.md` §7.3):

- **S1.8** construye la barrera: `permission_query_conditions` + `has_permission` +
  `company` congelada tras crear el documento, con una **suite de 12 escenarios
  contra la API, no por la pantalla**, corriendo en CI en cada push.
- **Regla nueva del proyecto:** `ignore_permissions=True` y `frappe.db.sql()` crudo
  quedan **prohibidos** dentro de `korvexcio/`. Son los bypass de Frappe.
- Evidencia de que el riesgo es real en ERPNext, no teórico: PR frappe/erpnext#44695
  (User Permission ignorada en estados financieros, arreglado en 14.78.3) y el issue
  frappe/erpnext#43652 (*admin de Company A ve los usuarios de Company B*),
  **cerrado como `not planned`**.

### Slices cerrados, con su evidencia

| Slice | Qué | Evidencia |
|---|---|---|
| **S0.1** ✅ | Repo git con remote, `.gitignore`, `.env.example`, docs commiteados. Corregidas las dos rutas activas que mandaban a `C:\PROYECTOS\VAPELAND` (`HANDOFF.md:7`, `CLAUDE.md:98`) | commit `80e7693` · `git remote -v` apunta a `yedinrumba-eng/KORVEXCIO` · `git status --porcelain` vacío |
| **S0.1b** ✅ | Secure-Vibe modo A + C: skill `/secure-vibe` instalada, `AGENTS.md` y `docs/SEGURIDAD-SECURE-VIBE.md` en el repo, `pre-commit` con **gitleaks** activo | commit `9f6ad20` · `pre-commit run --all-files` → **7 hooks Passed** · un commit con una clave AWS de ejemplo fue **rechazado**: `RuleID: aws-access-token`, `leaks found: 1`, y `git log` confirmó que no se creó commit |
| **S0.2** ✅ | `~/.ssh/config` corregido: `HostName 10.0.0.193` → `100.102.203.91` (Tailscale). Backup en `~/.ssh/config.bak-<fecha>` | `ssh korvex-host 'hostname && uptime'` → `korvex-node1, up 1 day, 18:42` |
| **S0.4** ✅ | Checklist previo del nodo (§6 de `ACCESO-Y-REGLAS-DEL-NODO.md`), corrido completo | `df -h /` → 73G libres · backup del día `ok: true`, dump verificado y subido a R2 · `curl https://github.com` → **200** (IPv4 sano) · 4 units systemd activas · health de KORVIS `{"status":"ok","checks":{"postgres":"ok","redis":"ok"}}` · `docker builder prune -f` liberó **2.168 GB** → 75G libres, 20% usado |

### Escalado a Yedin — dos cosas que necesitan su decisión

1. 🟡 **El `LICENSE` del repo dice MIT.** Los documentos del proyecto dicen que la app
   será **GPLv3, porque ERPNext es GPLv3** y una app de Frappe que se distribuye
   hereda esa obligación. Son incompatibles. **No se cambió por cuenta propia (R2/R3).**
   Recomendación: pasar a GPL-3.0 antes de que exista una línea de código de la app.
2. 🟡 **El carril B en paralelo** (`docs/08-BLUEPRINT.md` §7.2) — Fase 3, escáner, QZ
   Tray y manuales en otra sesión (Codex) mientras el carril A hace la Fase 2. Gana
   ~1 semana de colchón. **Es un cambio al modelo "un slice a la vez", así que está
   propuesto, no aplicado. Necesita OK explícito.**

### Pendiente de Yedin, no de código

- **S0.3** — mandar los correos a **Alanube** y **ECF SSD**. El texto listo para pegar
  está en `docs/08-BLUEPRINT.md` §6.1. Va en paralelo; no bloquea el bench, sí bloquea
  el spike fiscal S0.9.
- Empujar el **RNC** del cliente y el **certificado digital** (3–10 días hábiles, por
  cada RNC).

---

## 2026-08-31 — S0.5: COMPLETADO tras revisión de seguimiento

**Estado:** COMPLETADO. Implementación, prueba operativa, revisión de
seguimiento y verificaciones frescas, todo con evidencia. **S0.6 no se ha
iniciado y no hubo push** — eso sigue pendiente para la próxima sesión.

**Qué se hizo:** se construyó una imagen aislada `korvexcio:16` sobre el
`frappe_docker` oficial, con ERPNext, POSNext y URY. El stack usa proyecto y red
propios, límites por servicio por debajo de 6 GiB, frontend en
`127.0.0.1:8080`, y MariaDB/Redis sin puertos publicados al host.

**Decisión cerrada:**
- **D2 — Frappe/ERPNext v16.** v16 construyó y arrancó las cuatro apps: Frappe
  `16.32.0`, ERPNext `16.33.0`, POSNext `1.12.0` y URY `v3.0.0-beta.1`. v15 era
  el fallback si alguna fallaba; esa condición no ocurrió.

**Evidencia operativa ya obtenida:**

```bash
docker compose -p korvexcio --project-directory . -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f compose.s05.yaml ps -a
docker compose -p korvexcio --project-directory . -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f compose.s05.yaml exec -T backend bench version
docker stats --no-stream
ss -tlnp | grep -E '3306|6379|8080'
systemctl status korvex-api --no-pager
curl -s http://127.0.0.1:4000/health
df -h /
```

**Resultado real decisivo:** nueve servicios runtime `Up`, configurator
`Exited (0)`, MariaDB `healthy`; `127.0.0.1:8080->8080/tcp`; los nueve servicios
medidos quedaron bajo su `mem_limit`; KORVIS devolvió
`{"status":"ok","checks":{"postgres":"ok","redis":"ok"}}`; disco en 37%
con 60 GB libres. Evidencia completa en `docs/13-VERSION-FRAPPE.md`.

**Revisión recibida:** `Spec Compliance: ⚠️` y `Task quality: Needs fixes`, sin
hallazgos críticos. Señaló dos huecos documentales: faltaba mostrar `docker stats`
de los nueve servicios runtime y faltaba pegar la salida de `df -h /` previa al
build. Ambos quedaron corregidos en `docs/13-VERSION-FRAPPE.md`.

**Commits:**
- `e119e00` — `feat: bring up isolated Frappe v16 bench on korvex-node1 (S0.5)`.
- `2411f94` — `docs: land master plan in repo and record Fase 0 state for session handoff`.
- `docs: close S0.5 after follow-up review` — este cierre (ver `git log --oneline -3`).

**Revisión de seguimiento (misma sesión, 31/08):** las dos correcciones
pedidas por el primer auditor (docker stats de los nueve servicios runtime +
`df -h /` previo al build con 75 GB) confirmadas en `docs/13-VERSION-FRAPPE.md`,
completas y sin exagerar lo comprobado — el propio doc aclara que `docker
stats` no capturó el pico de `configurator` porque ya había terminado. Sin
hallazgos críticos ni altos. Verificaciones frescas, salida real:

```
python -m json.tool apps.json   -> válido, exit 0
git diff --check                -> limpio, exit 0
git diff --cached --check       -> limpio, exit 0
pre-commit run --all-files      -> 7/7 Passed
git status --short --branch     -> ## main...origin/main [ahead 4]; M HANDOFF.md; M PROGRESO.md
```

**Deuda creada:** 🟡 POSNext y URY solo ofrecen `develop`; fijar referencias
inmutables antes de S1.2. 🟡 El build dejó 7.154 GB de caché reclamable; su
limpieza requiere mantenimiento autorizado. ⚪ Warnings upstream de Vite se
revisan solo si producen un fallo observable en S0.8.

**Plan versionado:** `docs/08-BLUEPRINT.md` entró al repo en `2411f94` como fuente
de verdad. No se modificó su contenido para cerrar S0.5.

**Siguiente al retomar:** S0.6 — crear `korvexcio.korvexdev.cc` e instalar
ERPNext, sin adelantar S0.7. Todavía sin push a `origin/main`: eso lo pide
Yedin cuando quiera.

---

## 2026-08-31 — S0.6: COMPLETADO — site `korvexcio.korvexdev.cc` con ERPNext

**Estado:** COMPLETADO. Site creado sobre el bench v16 ya de pie (S0.5), sin
reconstruir nada. **S0.7 no se ha iniciado.**

**Qué se hizo:** Yedin corrió `bench new-site korvexcio.korvexdev.cc
--mariadb-root-password ... --admin-password ... --install-app erpnext
--set-default` por SSH en `korvex-node1`, dentro de
`/home/korvex/frappe_docker-korvexcio-s05`. El `DB_ROOT_PASSWORD` salió del
`.env` del nodo (600); el password de Administrator se generó random con
`openssl rand -base64 24` y quedó en `.korvexcio-admin-pw` (600) en el mismo
directorio — **nunca pasó por el chat**.

**Verificación, salida real:**

```
curl -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping
-> {"message":"pong"}

bench --site korvexcio.korvexdev.cc list-apps
-> frappe  16.32.0 UNVERSIONED
   erpnext 16.33.0 UNVERSIONED

systemctl status korvex-api --no-pager | head -3
-> Active: active (running) since Sat 2026-08-29 10:24:30 AST

curl http://127.0.0.1:4000/health
-> {"status":"ok","checks":{"postgres":"ok","redis":"ok"},"uptime":164572}

df -h /
-> 98G   34G   60G   37% /   (sin cambio frente a S0.5 — el site no engordó el disco)

docker ps --filter "name=korvexcio"
-> los nueve servicios runtime Up, korvexcio-db-1 Up (healthy)
```

KORVIS intacto, disco sin variación, los nueve contenedores del stack siguen
arriba. Ningún hallazgo.

**Nota de proceso:** el clasificador de auto-mode bloqueó dos intentos de
Claude de correr `bench new-site` por SSH directamente — es una acción que
crea una base de datos nueva en un nodo con un banco en producción, y el
bloqueo es correcto por diseño. Yedin lo corrió él mismo con el comando que
Claude preparó.

**Deuda:** ninguna nueva. El password de Administrator vive solo en el nodo;
si se necesita rotar o consultar, es tarea de servidor, no de este repo.

**Siguiente al retomar:** S0.7 — crear las dos `Company` (VAPELAND y
Cafetería) con su `tax_id`, almacén, cost center y naming series. S0.7b
(`demo.korvexdev.cc`) puede ir justo después.

---

## 2026-08-31 — Nombres reales de los dos negocios (corrección de Yedin)

Yedin confirmó los nombres comerciales reales:
- **Vapería:** `VAPERIA LA J Y EL JALAPEÑO` (abbr `VLJ`) — antes referida como
  "VAPELAND" en toda la documentación de planeación.
- **Cafetería:** `EL SABOR DE LAS 5 ESQUINAS` (abbr `ESE`) — antes referida
  genéricamente como "Cafetería".

**Nota de alcance:** el codename interno del cliente (`cliente 1: VAPELAND`
en la cabecera de `CLAUDE.md`, la nomenclatura del proyecto) **no se tocó** —
es un shorthand interno del repo, no el nombre de una `Company`. Lo que
cambió son los nombres reales que entran como registros `Company` en
ERPNext, y así se documentan de aquí en adelante. `docs/08-BLUEPRINT.md` no
se modificó (sigue con los nombres genéricos del plan original, es el
histórico de la decisión D19, no el dato operativo).

---

## 2026-08-31 — S0.7: COMPLETADO — las dos Company con nombre real

**Estado:** COMPLETADO. Las dos `Company` de ERPNext creadas, con su
`tax_id` (RNC de prueba, pendiente el real), almacenes y cost centers
propios. **S0.7b no se ha iniciado.**

**Qué se hizo:** vía `bench --site korvexcio.korvexdev.cc console` (Claude,
sin bloqueo del clasificador — esto es una operación de datos dentro de un
site que ya existe, no una operación de infraestructura), se creó:

- `VAPERIA LA J Y EL JALAPEÑO` (abbr `VLJ`)
- `EL SABOR DE LAS 5 ESQUINAS` (abbr `ESE`)

Las dos con `default_currency=DOP`, `country=Dominican Republic`, y
`tax_id` placeholder (`000-0000000-0`/`-1`, marcado "RNC PENDIENTE" — D13:
se planifica para dos RNC hasta que Yedin confirme).

**Hallazgo real, no cosmético — y ya resuelto:** el primer intento de crear
las Companies falló a medio camino: `LinkValidationError: Could not find
Warehouse Type: Transit`. Causa raíz: `bench new-site --install-app erpnext`
(headless) **no corre el mismo seed de datos que corre el Setup Wizard** de
la interfaz web (`erpnext.setup.setup_wizard.operations.install_fixtures`).
Ese seed es el que crea `Warehouse Type`, UOM, Item Groups, Market Segments
y las plantillas de dirección por país — en un install headless, esa tabla
queda vacía.

**Fix aplicado** (dato maestro, no código — no se tocó nada en
`apps/erpnext/` ni `apps/frappe/`, R6 del CLAUDE.md del repo): se llamó a
`install_fixtures.install(country="Dominican Republic")` y a las funciones
`update_selling_defaults`, `update_buying_defaults`,
`update_item_variant_settings`, `add_uom_data`, `add_market_segments` una
por una desde la consola. Un sub-paso del propio `install()`
(`set_up_address_templates`) chocó con un bug de upstream en
`frappe/locale.py` (`get_locale_value` revienta con `frappe.local.lang` sin
setear fuera de un request) — no se parcheó frappe; se dejó así porque no
bloqueaba el objetivo (la plantilla de Dominican Republic sí quedó creada
antes del choque) y `add_sale_stages()` solo devolvió un duplicado
inofensivo (ya estaban sembradas).

**🔴 Deuda para S0.7b:** el site `demo.korvexdev.cc` va a pegar con el mismo
hueco (`bench new-site` headless no siembra `install_fixtures`). Antes de
crear cualquier Company ahí, correr la misma secuencia. Vale también para
cualquier tenant nuevo en producción — **esto tiene que quedar como paso
explícito del script de alta de tenant**, no repetirse a mano cada vez.

**Verificación, salida real:**

```
frappe.get_all("Company", fields=["name","tax_id","default_currency","country"])
-> VAPERIA LA J Y EL JALAPEÑO | 000-0000000-0 (RNC PENDIENTE) | DOP | Dominican Republic
-> EL SABOR DE LAS 5 ESQUINAS | 000-0000000-1 (RNC PENDIENTE) | DOP | Dominican Republic

Warehouses VLJ: Finished Goods - VLJ, Work In Progress - VLJ, Stores - VLJ, All Warehouses - VLJ
Warehouses ESE: Finished Goods - ESE, Work In Progress - ESE, Stores - ESE, All Warehouses - ESE
-> cero solapamiento entre las dos listas

Cost centers: 'Main - VLJ' / 'Main - ESE' (más el cost center raíz de cada Company)
Accounts (Chart of Accounts): 94 por Company

frappe.db.exists("Warehouse", {"name": "Stores - VLJ", "company": "EL SABOR DE LAS 5 ESQUINAS"})
-> None  (un almacén de una Company no existe bajo la otra)

KORVIS: {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}
df -h /: 60G libres, sin cambio
```

**Sin verificar todavía:** naming series con sufijo de abbr para documentos
transaccionales (Sales Invoice, etc.) — no se probó crear un documento real
todavía; eso llega naturalmente en S0.8/Fase 2. El aislamiento que se probó
aquí es de **datos maestros** (almacenes, cuentas), no el de
`permission_query_conditions` — ese sigue siendo **S1.8**, sin construir.

**Siguiente al retomar:** S0.7b — site `demo.korvexdev.cc`. Aplica la misma
deuda de fixtures de arriba.

---

## 2026-08-31 — S0.7b: DIFERIDA — no bloquea nada más de Fase 0

**Estado:** BLOQUEADA técnicamente (ver abajo), y **diferida por decisión de
Yedin** al preguntar "¿para qué sirve esto?" en caliente. Respuesta corta:
`demo.korvexdev.cc` es la prueba barata de que "un site por cliente" (D19)
funciona antes de que llegue un cliente 2 real — staging y demo de venta,
nada más. **No la usa S0.8, S0.9 ni S0.11** — esos tres trabajan sobre
`korvexcio.korvexdev.cc`. Se crea cuando Yedin tenga 2 minutos por SSH, o
cuando aparezca un cliente 2 real, lo que pase primero. No es parte del gate
de Fase 0.

**Por qué además está bloqueada técnicamente:** `bench new-site
demo.korvexdev.cc` es la misma operación que en S0.6 (crea una base de datos
nueva en el nodo) y el clasificador de auto-mode volvió a bloquear a Claude
al intentarlo directo por SSH — correcto por diseño, mismo motivo que S0.6.

**No se improvisó un rodeo.** Por R2 del `CLAUDE.md` global, esto se reporta
como bloqueo y se sigue con lo que no depende de él (S0.10, S0.11), no se
inventa un reemplazo.

**Comando listo para que Yedin lo corra por SSH** (mismo patrón que S0.6):

```bash
ssh korvex-host
cd /home/korvex/frappe_docker-korvexcio-s05
set -a; source .env; set +a
ADMIN_PW=$(openssl rand -base64 24)
docker compose -p korvexcio --project-directory . \
  -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f compose.s05.yaml \
  exec -T backend bench new-site demo.korvexdev.cc \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_PW" \
  --install-app erpnext \
  --set-default
echo "$ADMIN_PW" > .demo-admin-pw
chmod 600 .demo-admin-pw
```

**Siguiente al retomar:** cuando Yedin corra ese comando, Claude verifica
con `curl -H "Host: demo.korvexdev.cc" ...` y cierra S0.7b. Mientras tanto,
sigue con S0.8/S0.10/S0.11, que no dependen de este site.

---

## 2026-08-31 — S0.10: COMPLETADO (con un paso pendiente de sudo)

**Estado:** COMPLETADO en lo que Claude puede hacer sin `sudo` — que es casi
todo. Falta un `systemctl enable` que solo puede correr Yedin (regla del
nodo: sudo fuera de reiniciar los 3 servicios de KORVIS lo corre Yedin).

**Qué se hizo:**
1. Medido el consumo real de los volúmenes de KORVEXCIO: `korvexcio_db-data`
   268.5M, `korvexcio_sites` 768K, `korvexcio_redis-queue-data` 92K. Total
   bajo 300 MB — lejísimos del 80%/90% de alarma del nodo (60 GB libres de
   98G, 37% uso).
2. Escrito [scripts/backup-retention.sh](../scripts/backup-retention.sh):
   corre `bench backup` por cada site del bench y borra dumps con más de 14
   días (`KORVEXCIO_BACKUP_RETENTION_DAYS`, configurable). Escribe
   `backup-status.json` con el mismo formato que ya usa KORVIS
   (`{"timestamp","ok","message"}`) para que la alarma existente del nodo lo
   pueda leer igual si algún día se conecta.
3. **Probado de verdad, no solo escrito:** corrido en `korvex-node1`, backup
   real de `korvexcio.korvexdev.cc` completado (905.4 KiB, no vacío — R2
   global: "se verifica contenido, no que el archivo exista").
4. Escritos `docker/systemd/korvexcio-backup.service` y `.timer` (corre a
   las 03:30, después del backup de KORVIS a las 03:00). Copiados al nodo en
   `/home/korvex/korvexcio-backup.{service,timer}`, listos para instalar.

**Verificación, salida real:**

```
docker volume ls --filter name=korvexcio
-> korvexcio_db-data, korvexcio_redis-queue-data, korvexcio_sites

du -sh de cada volumen: 268.5M / 92.0K / 768.0K

./backup-retention.sh
-> Backup Summary for korvexcio.korvexdev.cc ...
   Database: .../database.sql.gz 905.4KiB
   Backup for Site korvexcio.korvexdev.cc has been successfully completed
   OK.  (exit 0)

cat backup-status.json
-> {"timestamp": "2026-08-31T12:29:54Z", "ok": true, "message": "backup completo, retención 14d aplicada"}
```

**Pendiente — solo esto, y solo Yedin puede correrlo:**

```bash
ssh korvex-host
sudo cp /home/korvex/korvexcio-backup.service /home/korvex/korvexcio-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korvexcio-backup.timer
systemctl list-timers korvexcio-backup.timer   # confirma la próxima corrida
```

**Deuda:** no se conectó con el backup a R2 (eso es para cuando haya datos
reales que valga la pena sacar del nodo — prematuro con 268 MB de prueba).
No se probó restauración — eso es **S6.2**, con contenido real, no antes.

**Sin verificar todavía:** que el timer corra solo a las 03:30 (no se puede
probar sin esperar 19 horas ni sin el `sudo` de instalación).

**Siguiente al retomar:** S0.11 — catálogo.

---

## 2026-08-31 — S0.11: COMPLETADO — catálogo representativo, 24 SKUs

**Estado:** COMPLETADO. Sin Excel real del cliente todavía (S0.3/catálogo son
de Yedin); se modeló un catálogo representativo como pide el plan.

**Qué se hizo, en `korvexcio.korvexdev.cc`:**

- 2 `Item Group` nuevos: `Vapes`, `Cafeteria`.
- 2 `Item Attribute`: `Sabor` (Menta/Fresa/Mango), `Nicotina mg`
  (3mg/6mg/12mg). (`Colour` y `Size` ya venían del seed base de ERPNext —
  no se usaron.)
- **VAPERIA LA J Y EL JALAPEÑO (VLJ)** — 16 items:
  - 1 template `ELIQ-30ML` (E-Liquid 30ml, `has_variants=1`) con sus **9
    variantes** generadas por `erpnext.controllers.item_variant.create_variant`
    (Sabor × Nicotina, 3×3).
  - 6 sueltos: Pod System, Mod Kit 80W, Coil 0.3ohm, Coil 0.5ohm, Cargador
    USB-C, Tanque de repuesto.
- **EL SABOR DE LAS 5 ESQUINAS (ESE)** — 8 items de mostrador (D14: sin
  mesas/comandas): Café Americano, Cappuccino, Croissant, Empanada de queso,
  Agua embotellada, Jugo natural, Brownie, Sandwich.
- Cada Item lleva su `Item Default` con la `Company` y el almacén
  (`Stores - VLJ` / `Stores - ESE`) correctos — no quedaron huérfanos.

**Bug propio, no de upstream, encontrado y arreglado en el camino:** asignar
`variant.item_defaults = [dict, ...]` directamente sobre un doc ya
construido revienta con `AttributeError: 'dict' object has no attribute
'is_new'` — Frappe no envuelve la child table si se asigna por atributo
plano después de construir el doc. Fix: `variant.set("item_defaults", [...])`
en vez de la asignación directa. Anotado aquí para no volver a pisarlo.

**Verificación, salida real:**

```
frappe.db.count("Item") -> 24
frappe.get_all("Item", filters={"variant_of": "ELIQ-30ML"}, pluck="item_code")
-> ELIQ-30ML-MEN-3mg, ELIQ-30ML-MEN-6mg, ELIQ-30ML-MEN-12mg,
   ELIQ-30ML-FRE-3mg, ELIQ-30ML-FRE-6mg, ELIQ-30ML-FRE-12mg,
   ELIQ-30ML-MAN-3mg, ELIQ-30ML-MAN-6mg, ELIQ-30ML-MAN-12mg
frappe.db.count("Item Default", {"company": "VAPERIA LA J Y EL JALAPEÑO"}) -> 16
frappe.db.count("Item Default", {"company": "EL SABOR DE LAS 5 ESQUINAS"}) -> 8

KORVIS: {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}
df -h /: 60G libres, sin cambio
```

**Sin verificar todavía:** que el template se vea bien **en la UI** (solo se
probó por API/console, no se abrió el navegador contra el sitio — el
frontend está en loopback del nodo, sin túnel abierto desde esta sesión).
Tampoco se pusieron precios/valuation — eso es de Fase 3/5, no de este
smoke test. Solo dos atributos de los cuatro que menciona el plan (Sabor,
Nicotina) — Tamaño (ml) y Ohmiaje quedan para el modelado real de **S3.1**,
cuando haya catálogo real o al menos una decisión de variantes definitiva.

**Siguiente al retomar:** S0.8 — spike POS.

---

## Fases

> El detalle de cada slice, con su verificación y su entregable, está en
> **`docs/08-BLUEPRINT.md` §6**. Aquí solo el estado.

### Fase 0 — Reducir riesgo · 31/08 → 07/09 *(en curso)*
- [x] **S0.1** — repo con remote, `.gitignore`, `.env.example`, rutas corregidas
- [x] **S0.1b** — Secure-Vibe modo A + pre-commit con gitleaks
- [x] **S0.2** — acceso al nodo por Tailscale arreglado
- [ ] **S0.3** — correos a proveedores e-CF *(Yedin)*
- [x] **S0.4** — checklist previo del nodo, todo verde
- [x] **S0.5** — **bench v16 de pie en `korvex-node1`. D2 cerrada.**
- [x] **S0.6** ⭐ — site `korvexcio.korvexdev.cc` con ERPNext instalado
- [x] **S0.7** — las dos `Company`: **VAPERIA LA J Y EL JALAPEÑO** y **EL SABOR DE LAS 5 ESQUINAS**, cada una con su `tax_id` (RNC pendiente)
- [ ] **S0.7b** — site `demo.korvexdev.cc` *(diferida, no bloquea el resto de Fase 0 — comando listo para Yedin)*
- [ ] **S0.8** — spike POS *(timebox 2 días)* → `docs/10-SPIKE-POS.md`
- [ ] **S0.9** 🔴 — spike fiscal, **el gate**: TrackID real de TesteCF → `docs/11-SPIKE-FISCAL.md`
- [x] **S0.10** — script de backup+retención probado; falta solo el `sudo systemctl enable` de Yedin
- [x] **S0.11** — 24 SKUs representativos (16 VLJ con 1 template+9 variantes, 8 ESE)
- [ ] **S0.12** — cerrar Fase 0 en los documentos y en `data/korvex.json` (⚪ → 🔵)

**🚦 Gate:** S0.5 cerrada con KORVIS intacto ✅ · S0.9 con TrackID real o el veredicto
escrito de por qué fallaron las tres vías · S0.8 con veredicto de POS.
**Si las tres vías de S0.9 fallan: se para y se escala.** No se improvisa (R2).

### Fase 1 — Esqueleto de la app · 08/09 → 12/09
- [ ] S1.1 `bench new-app korvexcio` con módulos `ECF` y `Retail`
- [ ] S1.2 `apps.json` con el repo propio · **fijar SHA o mirrors** para POSNext y URY
      (hoy están en `develop`, que es mutable) · el despliegue verifica el **SHA**, no
      el exit code
- [ ] S1.3 CI: server tests + ruff + los 5 workflows de Secure-Vibe + el test de aislamiento
- [ ] S1.4 `before_tests` que crea la company de prueba
- [ ] S1.5 `custom/*.json` con `Customer.rnc` y `Customer.tipo_identificacion`
- [ ] S1.6 secretos cargados a mano en el nodo, permisos `600`
- [ ] S1.7 roles y User Permissions por Company
- [ ] S1.8 🔴 **la barrera de aislamiento + su suite de 12 escenarios**
- [ ] S1.9 *(solo si se aprueba el carril B)* prompt de handoff con la frontera de archivos

### Fase 2 — Módulo ECF · 15/09 → 03/10 · ⬅ CAMINO CRÍTICO
- [ ] S2.1 → S2.15 (`docs/08-BLUEPRINT.md` §6)

**🚦 Gate:** un E32 emitido + su RFCE, con respuesta real de TesteCF, en los dos
sites, con cola asíncrona y contingencia probadas cortando la red. Más `/secure-vibe`
en verde y el loop de 4 auditores completo.

### Fase 3 — Módulo Retail · 06/10 → 10/10
- [ ] S3.1 → S3.6 — atributos del vertical, FEFO, verificación de edad, cafetería
      mostrador, reportes del dueño, **dashboard consolidado de los dos negocios**

### Fase 4 — POS + hardware · 13/10 → 17/10
- [ ] S4.1 → S4.6 — POS Profile por Company, campos fiscales en caja, escáner,
      impresión térmica con QR, turno de caja, **contingencia end-to-end**

### Fase 5 — Datos reales + certificación · 20/10 → 25/10
- [ ] S5.1 → S5.5 — catálogo completo, inventario inicial, usuarios,
      **certificación ante la DGII para los dos RNC**, manuales

### Fase 6 — Producción · 01/11 → 15/11
- [ ] S6.1 → S6.6 — publicar los dos sites, backups con restauración probada,
      `RUNBOOK.md`, **go-live**, superficie de red cerrada, **KORVIS sano**

### Fase 7 — Post-lanzamiento *(después del 15/11)*
Cafetería con mesas/comandas/KDS (URY) · Frappe CRM · VAPELAND como tenant de
KORVIS · sincronizar catálogo → base de conocimiento · planes y precios validados
contra el mercado RD · publicar los XSD + XML golden como repo público.

---

## Deuda técnica abierta

Ordenada por lo que más duele.

| Sev | Qué | Qué la mitiga hoy | La cura de verdad |
|---|---|---|---|
| 🔴 | **RFCE no está documentado en ninguna vía Python.** Es ~100% del volumen del POS (E32 bajo RD$250,000) | S0.3 pregunta a los proveedores en paralelo; plan B es portar de `victors1681/dgii-ecf` (MIT, TS) | **S0.9.** Si las tres vías fallan, se para y se escala |
| 🔴 | **Aislamiento entre Companies es lógico, no físico** (D19) | Nada todavía | **S1.8**: la barrera + su suite de 12 escenarios en CI |
| 🟡 | **POSNext y URY se instalaron desde `develop`**, que es mutable. Ninguno publica `version-16` | El SHA probado quedó escrito en `docs/13-VERSION-FRAPPE.md` | **S1.2**: fijar SHA o mirrors de Korvex |
| 🟡 | **`LICENSE` dice MIT y la app tiene que ser GPLv3** | Nada — no hay código de la app todavía | Cambiarlo **antes** de S1.1. Decisión de Yedin |
| 🟡 | **7.154 GB de caché de build reclamable en el nodo** | La alarma de disco avisa al 80% | Mantenimiento autorizado con `docker builder prune` |
| 🟡 | **La mini PC viaja con Yedin** | Ninguna mitigación técnica | Decisión de Yedin antes del go-live: deja de viajar · VPS · contingencia por OFV |
| ⚪ | Warnings de Vite en el build de POSNext/URY | No producen fallo observable | Se revisan solo si rompen S0.8 |
| ⚪ | **No hay entrada en `data/korvex.json`** (§7.2 de `CONVENCIONES.md`) | — | S0.12 |
