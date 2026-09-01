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

## 2026-08-31 — S0.8: matriz completa, prueba en vivo pendiente

**Estado:** 🟡 **PARCIAL, y honesto sobre por qué.** Los 8 criterios de la
matriz se respondieron con evidencia de código fuente real (no de README,
no de memoria) dentro del contenedor `korvexcio-backend-1`. **La prueba
dura del plan — cortar la red, 5 ventas, reconectar — no se hizo**: requiere
un túnel SSH + `hosts` local para llegar a la UI en `127.0.0.1:8080` del
nodo, y no se armó por presupuesto de tiempo de esta sesión, no por
imposibilidad. Documento completo: `docs/10-SPIKE-POS.md`.

**Hallazgo que revierte el sesgo declarado de D16:** D16 asumía "la cola
offline la escribes tú de todos modos" para justificar el sesgo hacia el
nativo. El código real dice lo contrario — **POSNext ya tiene una
arquitectura de offline completa** (`offline.worker.js` + capa `db`/`cache`/
`sync` + store dedicado), mientras que el POS nativo de ERPNext **no tiene
ningún mecanismo de offline** (cero archivos, `grep` en cero). Además
POSNext crea `Sales Invoice` directo — el doctype donde previsiblemente
enganchan los hooks de `ecf` (S2.9) — mientras el nativo usa `POS Invoice`,
que se consolida después con retraso.

**Esto se dice de frente, no se aplica solo:** el veredicto del documento
recomienda cerrar **D16 hacia POSNext**, pero eso es una recomendación con
evidencia, no una decisión tomada por Claude — D16 sigue "diferida" hasta
que Yedin la confirme.

**Deuda:** la prueba en vivo (offline real, 5 ventas, reconectar) queda
para **S4.1**, contra datos reales y con POS Profile por Company ya
armado — más barato que repetir el spike con el catálogo de prueba de
S0.11.

**Siguiente al retomar:** reportar S0.9 (el gate) y cerrar S0.12.

---

## 2026-08-31 — S0.9: BLOQUEADA — el gate no se puede intentar todavía

**Estado:** 🔴 BLOQUEADA. No es que las tres vías fallaron — es que
**ninguna de las tres se puede ni intentar** sin algo que solo Yedin puede
mover:

- **Vía A** (proveedor certificado con RFCE) necesita respuesta de Alanube
  o ECF SSD. **S0.3 (los correos) sigue sin mandarse** — el texto está listo
  desde el plan maestro, en `docs/08-BLUEPRINT.md` §6.1, y en el checklist
  de abajo sigue `[ ]`.
- **Vía B** (portar RFCE de `victors1681/dgii-ecf`, MIT, contra el XSD
  oficial) necesita pegarle directo a `fc.dgii.gov.do/recepcionfc` en
  TesteCF — y **eso pide RNC + certificado digital**, que tampoco están
  (D13: RNC "en movimiento", certificado "3-10 días hábiles" sin pedirse
  aún).
- **Vía C** es la que toca: **parar y escalar**, tal como dice el propio
  gate del plan (§6, Fase 0).

**No se fabricó un TrackID ni se simuló una respuesta.** R1 del `CLAUDE.md`
global es explícito: sin la salida real de TesteCF, la frase es "escrito
pero SIN verificar — falta correr X", nunca "funciona".

**Lo que sí queda listo para cuando se destrabe:** la interfaz
`FiscalProvider` (D3), el candidato #2 (`ecf-dgii`, solo E31) y el plan B
completo con su repo fuente (D3, `TECH_STACK.md`). El trabajo de código de
la Fase 2 (S2.1 en adelante) puede arrancar en paralelo sin esperar a
S0.9 — lo único que no puede pasar sin TrackID real es **declarar cerrado
el módulo fiscal**.

**Siguiente al retomar:** esto no lo destraba una sesión de Claude Code —
lo destraba Yedin mandando los dos correos de S0.3, o consiguiendo el RNC +
certificado para tirar directo contra TesteCF. Mientras tanto, Fase 0 cierra
con S0.9 abierta y anotada, no fingida.

---

## 2026-08-31 — D20: Fase 0 cierra con S0.9/S0.3 como deuda, arranca Fase 1

**Decisión de Yedin, explícita, en el chat.** No se esperó a que se
resolviera el gate fiscal para seguir. **S0.9 y S0.3 bajan de "gate
bloqueante" a deuda técnica** en la tabla de abajo — siguen abiertas, siguen
🔴, pero ya no paran el trabajo de código.

**Por qué es seguro hacerlo así:** el propio `docs/08-BLUEPRINT.md` (D17)
ya preveía que el módulo `ecf` (Fase 2) puede arrancar en paralelo sin
esperar a S0.9 — lo único que S0.9 bloquea de verdad es **declarar cerrado
el módulo fiscal**, no empezar a escribirlo. Arrancar Fase 1 (el esqueleto
de la app, sin nada fiscal todavía) no choca con nada.

**Lo que NO cambia:** sigue sin existir ningún TrackID, ningún proveedor
elegido, ningún certificado. Cuando la Fase 2 llegue a S2.7 (el provider
real), si S0.9 sigue sin resolverse, **ahí sí para de verdad** — no antes.

**Fase 0, estado final:** cerrada en todo lo que no depende de terceros.
`data/korvex.json` se actualiza a "activo" (ya se hizo en la sesión
anterior). S0.9/S0.3 quedan en la tabla de deuda técnica, no en un gate.

**Siguiente al retomar:** **S1.1** — `bench new-app korvexcio`,
`modules.txt` con `ECF` y `Retail`, instalada en `korvexcio.korvexdev.cc`.

---

## 2026-08-31 — S1.1: COMPLETADO — esqueleto de la app `korvexcio`

**Estado:** COMPLETADO. Primera línea de código propio del proyecto.
**S1.2 no se ha iniciado.**

**Qué se hizo:** `bench new-app korvexcio` en `korvex-node1`, dentro del
bench v16 ya existente (no se reconstruyó nada). `bench new-app` es
interactivo (6 prompts sin flags no-interactivos en esta versión); se
alimentó por stdin:

| Prompt | Respuesta |
|---|---|
| App Title | `KORVEXCIO` |
| App Description | ERP y POS multi-tenant con e-CF para retail y food en RD |
| App Publisher | `Korvex` |
| App Email | `dev@korvexdev.cc` *(placeholder del dominio propio, no el gmail personal de Yedin)* |
| App License | **`gpl-3.0`** — no `mit`. Aplica la regla 11 del `CLAUDE.md` del repo: la app tiene que ser GPLv3 porque hereda de ERPNext. Esto es el `app_license` de `hooks.py`, **no** resuelve el conflicto del archivo `LICENSE` en la raíz del repo, que sigue en deuda |
| Create GitHub Workflow | No — CI es S1.3, slice aparte |
| Branch Name | `main` |

Luego, a mano (no hay `bench make-module` en esta versión):
- `modules.txt` reescrito a `ECF` / `Retail` (reemplazando el `KORVEXCIO`
  genérico por default).
- Carpetas `korvexcio/korvexcio/ecf/__init__.py` y
  `korvexcio/korvexcio/retail/__init__.py` creadas — vacías, listas para los
  DocTypes de Fase 2 y 3.
- `bench --site korvexcio.korvexdev.cc install-app korvexcio`.

**🔴 Hallazgo real en el camino, ya resuelto — anotado porque se va a repetir:**
después de instalar la app, `curl .../api/method/ping` empezó a devolver
`500 Internal Server Error`. El log de `backend` mostró
`ModuleNotFoundError: No module named 'korvexcio'` — los workers de
gunicorn (`backend`, `queue-short`, `queue-long`, `scheduler`, `websocket`)
ya estaban arriba **desde antes de que el paquete Python existiera** en el
venv del bench, y un proceso Python vivo no relee `sys.path`/módulos
nuevos solo. **Fix:** `docker compose restart backend queue-short
queue-long scheduler websocket` (no se tocó `frontend`, `db` ni los dos
`redis`). **Esta regla aplica a cada slice que instale una app o cambie
`modules.txt` de aquí en adelante — reiniciar esos 5 servicios después,
no antes de darlo por bueno.**

**Verificación, salida real:**

```
bench --site korvexcio.korvexdev.cc list-apps
-> frappe 16.32.0, erpnext 16.33.0, korvexcio 0.0.1 (main)

frappe.get_all("Module Def", filters={"app_name": "korvexcio"}, fields=["name","module_name"])
-> [{'name': 'Retail', ...}, {'name': 'ECF', ...}]

curl -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping
-> {"message":"pong"}   (después del restart; antes daba 500)

KORVIS: {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}, uptime nunca se reinició
docker ps --filter name=korvexcio: los 9 contenedores Up, db healthy
df -h /: 60G libres, sin cambio
```

**Sin verificar todavía:** que el `install-app` corriera también sobre un
segundo site (no aplica, `demo.korvexdev.cc` está descartado). Cero
DocTypes propios todavía — `ecf/` y `retail/` son carpetas vacías, es
literal el "esqueleto".

**Deuda que sigue igual:** LICENSE del repo en MIT (el `hooks.py` de la app
ya quedó en GPLv3, pero el archivo raíz no) — sigue pendiente de Yedin.

**Siguiente al retomar:** S1.2 — `apps.json` con el repo propio de
`korvexcio` + fijar SHA/mirrors de POSNext y URY (siguen en `develop`,
mutable).

---

## 2026-08-31 — S1.2: PARCIAL — `apps.json` actualizado, SHA fijo confirmado imposible sin mirror

**Estado:** 🟡 PARCIAL, con la razón técnica confirmada, no supuesta.

**Qué se hizo:** `apps.json` lleva ahora la entrada de `korvexcio`
(`https://github.com/yedinrumba-eng/KORVEXCIO.git`, rama `main`).

**Por qué NO se pudo "fijar SHA" de POSNext/URY — verificado en el código
real de `bench`, no supuesto:** el `get()` de `bench/app.py` construye el
clone así:

```python
branch = f"--branch {self.tag}" if self.tag else ""
shallow = "--depth 1" if self.bench.shallow_clone else ""
cmd = "git clone"
args = f"{self.url} {branch} {shallow} --origin upstream"
```

`git clone --branch <X> --depth 1` **solo acepta una rama o un tag que el
remoto publique** — no un SHA arbitrario. `apps.json` no tiene forma de
pedir un commit exacto tal como está diseñado. No es una limitación de
este proyecto, es cómo funciona el shallow clone de git.

**Las únicas dos curas reales, ninguna ejecutable hoy sin Yedin:**
1. Esperar a que POSNext/URY publiquen un tag `version-16` (no está en
   nuestro control).
2. **Mirror propio en un repo de Korvex**, pinneado al SHA exacto que ya
   está probado (`docs/13-VERSION-FRAPPE.md`). Esto es crear un repo nuevo
   y pushear código ahí — **acción externa visible, no se hace sin OK
   explícito.**

**Lo que NO se hizo, y por qué:** no se rebuildeó la imagen. La entrada de
`korvexcio` en `apps.json` no se puede probar todavía porque el repo no
está pusheado a GitHub (regla: push solo cuando Yedin lo pida) — sin push,
`git clone` de esa entrada fallaría. El bench de `korvex-node1` ya tiene
`korvexcio` instalado por `bench new-app` directo (S1.1), así que nada deja
de funcionar por esto; lo que queda pendiente es la **reproducibilidad**
desde cero, no el funcionamiento actual.

**Verificación:**
```
python -m json.tool apps.json -> válido, 4 entradas
```

**Deuda:** SHA de POSNext/URY sigue sin fijar — misma deuda de S0.5, ahora
con la causa técnica exacta documentada. Rebuild de imagen con
`korvexcio` real, pendiente de que Yedin autorice el push.

**Siguiente al retomar:** S1.3 — CI en GitHub Actions.

---

## 2026-08-31 — S1.3: COMPLETADO — CI escrito, la regla crítica probada de verdad

**Estado:** COMPLETADO en lo que se puede probar sin push. **La verificación
completa (workflow verde en GitHub) queda pendiente del push — no
existía antes de esta sesión y sigue sin existir.**

**También se corrigió, sobre la marcha:** el app package `korvexcio/` (creado
en S1.1 vía `bench new-app` directo en el nodo) **no existía todavía en este
repo DEV** — vivía solo en `korvex-node1`. Eso rompía la regla 7 del
`CLAUDE.md` ("nunca se edita código en el servidor") sin que nadie lo hubiera
notado. Se corrigió: `docker compose cp` sacó `apps/korvexcio` del
contenedor al host, `scp` lo bajó a `C:\PROYECTOS\KORVEXCIO\korvexcio\` +
`pyproject.toml`. **De aquí en adelante el repo es la fuente de verdad, como
manda la regla — el nodo consume, no genera.**

**Qué se escribió:**
- `.github/workflows/server-tests.yml` — el template oficial que `bench
  new-app` genera (se leyó del código fuente de
  `frappe/utils/boilerplate.py`, no se inventó), adaptado para instalar
  `erpnext` antes que `korvexcio` (nuestra app depende de sus doctypes).
- `.github/workflows/lint.yml` — ruff, config real en `pyproject.toml`
  (line-length 110, la que trae el boilerplate de Frappe — no el 100 de
  Carril C, porque esto es una app de Frappe, no una herramienta standalone).
- `.github/workflows/gitleaks.yml`, `semgrep.yml`, `osv-scanner.yml`,
  `trivy.yml` — los 4 automatizados de Secure-Vibe (modo C).
- **`.semgrep/korvexcio-isolation.yml`** — regla propia para la línea 10 del
  `CLAUDE.md` del repo: `ignore_permissions=True` y `frappe.db.sql()` crudo
  prohibidos en `korvexcio/`.

**🔴 Bug real en la regla de Semgrep, encontrado probándola de verdad, no
asumiendo que estaba bien:** el primer intento dio **0 hallazgos** contra un
archivo de prueba con las dos violaciones a propósito. La causa: el patrón
de paths (`korvexcio/**/*.py`) duplicaba el prefijo del directorio que ya se
pasaba como target del scan (`.../korvexcio`), así que nunca matcheaba nada
fuera de un solo archivo. Se corrigió a `**/*.py`. **Sin copiar el código
real a `korvexcio/` (arriba) esto nunca se hubiera descubierto** — la regla
llevaba escrita "bien" desde el punto de vista de YAML válido, pero rota en
la práctica.

**Verificación, salida real** (corrida en `korvex-node1` vía Docker, contra
un archivo de prueba temporal — borrado al terminar, nunca tocó el bench ni
el repo real):

```
python -c "import yaml, glob; ..." -> las 7 piezas (6 workflows + regla semgrep) YAML válido

docker run --rm -v /tmp/semgrep-test:/src semgrep/semgrep semgrep scan \
  --config /src/.semgrep/korvexcio-isolation.yml /src/korvexcio --json
-> ANTES del fix: 0 findings (bug)
-> DESPUÉS del fix: 2 findings exactos —
     korvexcio-no-ignore-permissions  isolation_check.py:5  (doc.insert(ignore_permissions=True))
     korvexcio-no-raw-sql             isolation_check.py:8  (frappe.db.sql(...))
   Las dos funciones "buenas" (sin ignore_permissions, con frappe.get_all) NO dispararon nada.
```

**Sin verificar todavía:** ningún workflow ha corrido en GitHub Actions de
verdad — eso necesita push, y push sigue siendo decisión de Yedin. La
prueba del semgrep fue standalone contra un fixture, no dentro del pipeline
real de CI.

**Deuda:** el test de aislamiento (S1.8, todavía sin escribir) no está
referenciado explícitamente en `server-tests.yml` — no hace falta, correrá
automático en cuanto exista un archivo de test bajo `korvexcio/`, pero
conviene revisarlo cuando S1.8 cierre.

**Siguiente al retomar:** S1.4 — `before_tests` que crea la company de
prueba.

---

## 2026-08-31 — S1.4: COMPLETADO — `before_tests` con DOS Companies, idempotente

**Estado:** COMPLETADO y verificado en vivo, no solo escrito.

**Qué se hizo:** `korvexcio/install.py` con `before_tests()`, enganchado en
`hooks.py`. Un detalle real que casi se pasa por alto: `frappe.utils.
install.before_tests()` (el de frappe core) **se sale sin hacer nada si hay
más de una app instalada** (`len(frappe.get_installed_apps()) > 1: return`)
— con frappe+erpnext+korvexcio son 3, así que korvexcio necesita su propio
fixture, no puede apoyarse en el de frappe.

**Por qué DOS Companies y no una (patrón India, adaptado):** `_Test Company
KORVEXCIO A` / `B`, prefijo `_Test` para no chocar nunca con datos reales
(VLJ/ESE quedan intactas). S1.8 va a probar aislamiento **entre** Companies
— con una sola no hay nada que aislar.

**🔴 El mismo bug de `frappe.local.lang` de S0.7, esta vez disparado por
otra vía:** crear el `Fiscal Year` de prueba dispara la Notification
estándar "Notification for new fiscal year", que evalúa una condición Jinja,
que pega con el mismo `UnboundLocalError` de `frappe/locale.py`. **Ya no se
trata caso por caso** — se blindó en el propio `before_tests()`: `if not
frappe.local.lang: frappe.local.lang = "en"` al principio de la función. No
es un parche a Frappe, es setear el dato de contexto que un proceso fuera de
un request HTTP no tiene solo.

**Verificación, salida real:**

```
frappe.get_hooks("before_tests")
-> ['frappe.utils.install.before_tests', 'korvexcio.install.before_tests']

before_tests()  # primera corrida
Companies _Test: [
  {'name': '_Test Company KORVEXCIO A', 'abbr': '_TCKA', 'tax_id': '000-0000001-1'},
  {'name': '_Test Company KORVEXCIO B', 'abbr': '_TCKB', 'tax_id': '000-0000002-2'}
]

before_tests()  # segunda corrida, prueba de idempotencia
-> Segunda corrida OK, count: 2   (no duplicó nada)

KORVIS: {"status":"ok","checks":{"postgres":"ok","redis":"ok"}}
df -h /: 58G libres (37->38%, ~2GB consumidos por las imágenes docker de
  semgrep/gitleaks descargadas en S1.3 — no por esto)
```

**Sin verificar todavía:** no se corrió `bench run-tests` completo (no hay
tests que corran todavía — eso empieza a llenarse en S1.5+ y sobre todo en
S1.8). Este slice solo prueba que el fixture en sí funciona.

**Siguiente al retomar:** S1.5 — `custom/*.json` con `Customer.rnc` y
`Customer.tipo_identificacion`.

---

## 2026-08-31 — S1.5: COMPLETADO — custom fields, patrón KSA, verificado con `bench migrate` real

**Estado:** COMPLETADO. Primer custom field del proyecto, con el mecanismo
correcto desde el día uno (no algo para migrar después).

**Qué se hizo:**
- `korvexcio/korvexcio/custom/customer.json` — el par de campos en formato
  dict-por-doctype: `tipo_identificacion` (Select: RNC/Cedula/Pasaporte,
  default RNC) y `rnc` (Data, después de `tipo_identificacion`).
- `korvexcio/korvexcio/custom_fields.py` — `sync_custom_fields()` que lee
  todos los `.json` bajo `custom/` y llama a
  `frappe.custom.doctype.custom_field.custom_field.create_custom_fields()`
  (la función real de Frappe para esto — **no `bench export-fixtures`**,
  que es monolítico y genera conflictos de merge).
- Enganchado en `hooks.py` vía `after_migrate` — corre en cada `bench
  migrate`, no solo al instalar. `create_custom_fields()` ya es idempotente
  por diseño (actualiza si el campo existe).

**Verificación, salida real — se corrió `bench migrate` completo, no un
atajo:**

```
bench --site korvexcio.korvexdev.cc migrate
-> ... Executing `after_migrate` hooks... -> sin errores, terminó limpio

frappe.get_meta("Customer").get_field("rnc")
-> DocField (Customer-rnc)                    # no es None
frappe.get_meta("Customer").get_field("tipo_identificacion")
-> DocField (Customer-tipo_identificacion)    # no es None

frappe.get_all("Custom Field", filters={"dt":"Customer","fieldname":["in",["rnc","tipo_identificacion"]]}, fields=["fieldname","fieldtype","insert_after"])
-> rnc (Data, después de tipo_identificacion)
-> tipo_identificacion (Select, después de tax_id)

KORVIS: {"status":"ok",...}
site ping: {"message":"pong"}
df -h /: 58G libres, sin cambio
```

**Sin verificar todavía:** que el campo se vea bien en la UI del formulario
de Customer (no se abrió navegador esta sesión, mismo motivo que S0.11 —
frontend en loopback puro del nodo). Verificado por API/meta, no visualmente.

**Siguiente al retomar:** S1.6 — `.env.example` + secretos a mano en el
nodo.

---

## 2026-08-31 — S1.6: PARCIAL — lo que no depende de un proveedor fiscal, cerrado

**Estado:** 🟡 PARCIAL, honesto sobre por qué. `.env.example` ya estaba
bien escrito desde S0.1 (no hacía falta tocarlo). Lo que faltaba y sí se
hizo: generar el único secreto que **no depende de nada externo**.

**Qué se hizo:**
- **`MASTER_ENCRYPTION_KEY`** generado en el nodo con
  `secrets.token_hex(32)` y agregado al `.env` de `korvex-node1` (600,
  nunca pasó por el chat). Hace falta para S3.3 (cifrado de cédula/fecha de
  nacimiento) — generarlo ahora evita tener que acordarse después.
- Confirmado que `DB_ROOT_PASSWORD` ya estaba (desde S0.5) y que no hay
  `.env` trackeado nunca en `git log --all -- .env`.
- Corrido **`/security-review`** contra el diff completo de los 11 commits
  sin pushear (S1.1→S1.6): **cero hallazgos por encima del 80% de
  confianza.** El scaffold no tiene endpoints (`@frappe.whitelist()`), no
  hay `ignore_permissions=True`, no hay `frappe.db.sql()` crudo, los 6
  workflows de CI no interpolan contexto no confiable (`github.event.*`) en
  bloques `run:` de shell.
- 🟡 Nota del propio `/security-review`, no bloqueante: los workflows de
  CI usan tags de versión mayor (`@v6`, `@v2`) en vez de SHA fijo — el
  propio `docs/SEGURIDAD-SECURE-VIBE.md` lo marca como señal de alerta.
  Va a deuda técnica, no es un hallazgo de seguridad real hoy (nada corre
  todavía, sin push).

**Lo que NO se hizo, y por qué:** "secretos a mano en el nodo" para el
`.p12` y los tokens del proveedor de e-CF — **no existen todavía**. Es la
misma deuda de S0.9: sin proveedor elegido no hay nada que cargar. No se
inventó un secreto de prueba para simular que esto está cerrado.

**Verificación, salida real:**

```
ls -la .env (en el nodo) -> -rw------- (600)
grep -oE "^[A-Z_]+=" .env -> incluye MASTER_ENCRYPTION_KEY= (valor nunca visto)
git log -p --all | grep -iE "password=.+|MASTER_ENCRYPTION_KEY=[0-9a-f]" -> vacío
git log --all --oneline -- .env -> vacío, nunca trackeado

/security-review sobre 11 commits sin pushear -> 0 hallazgos >80% confianza
```

**Deuda:** SHA-pin de las GitHub Actions (menor). El `.p12`/tokens de e-CF
siguen bloqueados en S0.9/S2.7.

**Siguiente al retomar:** S1.7 — roles y User Permissions por Company.

---

## 2026-08-31 — S1.7: COMPLETADO — aislamiento por Role+User Permission, probado como el usuario real, no como Administrator

**Estado:** COMPLETADO, con la prueba más honesta que se le puede pedir a
este slice: **cambiar de sesión (`frappe.set_user`) y consultar como el
cajero de verdad ve**, no inferir desde los permisos de Administrator.

**Qué se hizo — `korvexcio/roles.py`:**
- 4 Roles: `Cajero VLJ`, `Cajero ESE`, `Dueño`, `Contador`.
- `Dueño` con `Custom DocPerm` en `User` (read/write/create, sin delete) +
  `Role` (read) + **`User Permission`** (read/write/create) — sin esto
  último el dueño podía crear el usuario pero no restringirlo a su
  Company, y el flujo se quedaba a medias.
- Los 4 roles con `Custom DocPerm` de solo-lectura en `Company` —
  **hallazgo real, no anticipado:** un Role recién creado no tiene NINGÚN
  permiso por default en Frappe (ni siquiera leer). El primer intento de
  probar el aislamiento reventó con `PermissionError: Insufficient
  Permission for Company` **antes** de llegar a evaluar el `User
  Permission` — el DocPerm base se chequea primero.
- `assign_company_user_permission(user, company)` — llamable varias veces
  para el mismo usuario con distintas Companies (caso Dueño: una fila por
  Company).
- Enganchado en `hooks.py` vía `after_migrate` (lista, junto al de custom
  fields): `["korvexcio.custom_fields.sync_custom_fields",
  "korvexcio.roles.sync_roles"]`.

**🔴 Auto-corrección antes de subir nada: usé `ignore_permissions=True`
dos veces al escribir el archivo.** Exactamente lo que prohíbe la regla
12b del `CLAUDE.md` y lo que caza mi propia regla de Semgrep de S1.3. Las
dos sobraban — `bench console`/`bench migrate` corren como Administrator,
que ya salta todos los checks de permisos sin necesitar el flag. Se
quitaron las dos antes de desplegar nada. Ninguna llegó a un commit.

**Verificación, salida real — usuarios de prueba creados, sesión
cambiada de verdad:**

```
bench --site korvexcio.korvexdev.cc migrate
-> Executing `after_migrate` hooks... -> limpio, sin errores

# cajero.vlj.test@korvexdev.cc, rol "Cajero VLJ", User Permission -> VLJ
frappe.set_user("cajero.vlj.test@korvexdev.cc")
frappe.get_list("Company", pluck="name")
-> ['VAPERIA LA J Y EL JALAPEÑO']          # SOLO la suya

# dueno.test@korvexdev.cc, rol "Dueño", User Permission -> VLJ Y ESE
frappe.set_user("dueno.test@korvexdev.cc")
frappe.get_list("Company", pluck="name")
-> ['EL SABOR DE LAS 5 ESQUINAS', 'VAPERIA LA J Y EL JALAPEÑO']   # las dos

frappe.has_permission("User", "create")   # como cajero VLJ -> False
frappe.has_permission("User", "create")   # como Dueño      -> True
"System Manager" in frappe.get_roles(dueño)                  -> False

KORVIS: {"status":"ok",...}   df -h /: 58G libres, sin cambio
```

**Sin verificar todavía:** esto es aislamiento de **datos maestros vía el
mecanismo nativo de Frappe** (Role + User Permission) — funciona, y es real.
Pero **no es todavía la barrera de S1.8** (`permission_query_conditions` +
`has_permission` + `company` congelada). User Permission por sí solo tiene
huecos conocidos — el PR frappe/erpnext#44695 (estados financieros
ignorando User Permission) es la evidencia de por qué S1.8 hace falta
igual, con su propia suite de 12 escenarios contra la API.

**Deuda:** el permiso completo de cada Role (Sales Invoice, Item,
Customer, etc.) no se armó todavía — eso es Fase 4 (S4.1, POS Profile por
Company). Hoy solo se probó que el mecanismo de dos capas (Role DocPerm +
User Permission) funciona de verdad.

**Siguiente al retomar:** S1.8 — la barrera de aislamiento real
(`permission_query_conditions` + `has_permission` + `company` congelada) y
su suite de 12 escenarios. El slice más importante de seguridad del
proyecto hasta ahora.

---

## 2026-08-31 — S1.8: COMPLETADO — la barrera de aislamiento, con 8 de 12 escenarios reales y 4 diferidos a Fase 2

**Estado:** COMPLETADO para lo que existe hoy. **No se fingió cobertura de
lo que no existe** — 4 de los 12 escenarios del blueprint necesitan el
módulo `ecf` (certificados, providers, endpoints propios), que es Fase 2 y
todavía son carpetas vacías. Se marcaron `skipTest` con el motivo exacto,
no se inventó infraestructura para poder marcarlos en verde.

**Qué se escribió:**
- **`korvexcio/isolation.py`** — `freeze_company()`, el equivalente al
  `WITH CHECK` de una política RLS: si un documento ya existía y alguien le
  cambia el campo `company`, se rechaza. Aplica hoy a `Warehouse`, `Cost
  Center`, `Sales Invoice`, `Sales Order`, `Delivery Note`, `Payment
  Entry`, `Item Price` — los doctypes de ERPNext con `company` que ya
  tienen datos reales. Los propios de `korvexcio` (ECF, etc.) se agregan a
  la lista cuando existan.
- Enganchado en `hooks.py` vía `doc_events = {"*": {"validate":
  "korvexcio.isolation.freeze_company"}}` — seguro porque la función
  filtra por doctype adentro; en cualquier doctype sin `company` no hace
  nada.
- **`korvexcio/tests/test_isolation.py`** — 8 escenarios reales + 1
  `skipTest` documentado que cubre los 4 restantes.

**🔴 El hallazgo más importante del slice, y por qué casi se reporta mal:**
la primera corrida de la suite dio **3 fallos** en los escenarios de
lectura (2, 6, 7). La causa no era un bug de la barrera — era que el test
estaba mal escrito: usaba `frappe.get_doc(doctype, name)` para simular una
lectura, y **`frappe.get_doc()` NO chequea permisos de lectura por
diseño** — es una llamada de ORM de bajo nivel para código de servidor que
ya decidió que tiene derecho a leer. Lo que sí los chequea, porque es lo
que responde de verdad `/api/resource/<doctype>/<name>`, es
`frappe.client.get()`. Se verificó la diferencia a mano contra la consola
antes de "arreglar" nada — confirmar el hallazgo antes de tocar el test,
no al revés. **Implicación real para Fase 2:** cualquier método
`@frappe.whitelist()` propio de `korvexcio/ecf` que use `frappe.get_doc()`
para leer un documento sin llamar `doc.check_permission("read")` primero
**se salta el aislamiento sin darse cuenta.** Esto se anota como regla
para S2.x, no solo como nota de test.

**🟡 Segundo hallazgo real, documentado como deuda, no ocultado:** el
escenario 6 (enumeración) muestra que Frappe **sí distingue** "existe pero
no es tuyo" (`PermissionError`) de "no existe" (`DoesNotExistError`) — una
fuga de información menor (confirma qué `name`s existen en la otra
Company). Es comportamiento nativo de la plataforma, no algo que este
proyecto introdujo, y arreglarlo a nivel global es un cambio de mayor
alcance que este slice. Queda anotado, el test lo confirma explícitamente
en vez de esconderlo detrás de un assert flojo.

**Verificación, salida real — corrida DOS veces (prueba de idempotencia):**

```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio

Running 9 integration tests for korvexcio
 ✔ test_scenario_1_list_filtered_by_company
 ✔ test_scenario_2_direct_get_other_company_denied      (corregido: client.get, no get_doc)
 ✔ test_scenario_3_create_in_other_company_denied
 ✔ test_scenario_4_company_frozen_after_create            <- la pieza nueva de S1.8
 ✔ test_scenario_5_delete_other_company_denied_no_effect
 ✔ test_scenario_6_enumeration_same_error_shape           (confirma la fuga menor, no la oculta)
 ✔ test_scenario_7_unauthenticated_denied
 ✔ test_scenario_8_owner_sees_both_companies
 = test_scenario_9_to_12_deferred_to_fase2                (skip explícito, motivo documentado)

Ran 9 tests in 0.924s  ->  OK (skipped=1)
# segunda corrida, idéntica: OK (skipped=1) — no dejó basura, no rompió en repetición

KORVIS: {"status":"ok",...}
df -h /: 58G libres, sin cambio
```

**Limpieza:** los usuarios manuales de prueba de S1.7
(`cajero.vlj.test@korvexdev.cc`, `dueno.test@korvexdev.cc`) se borraron —
la suite automatizada crea y gestiona los suyos propios
(`_test.isolation.*@korvexdev.cc`), no hacía falta duplicar.

**Deuda:**
- 4 escenarios diferidos a Fase 2 (S2.2 certificados, S2.7 providers,
  endpoints propios de `korvexcio/ecf`) — el archivo de test es donde se
  completan cuando esa infraestructura exista, no un archivo nuevo.
- La fuga de enumeración (`PermissionError` vs `DoesNotExistError`) queda
  documentada, sin arreglar — es comportamiento de plataforma.
- `has_permission` custom **no hizo falta escribirlo todavía**: el
  mecanismo nativo de User Permission (S1.7) + el nuevo `freeze_company`
  (S1.8) cubren los 8 escenarios reales de hoy. Se revisará si algún
  doctype propio de `korvexcio` (Fase 2) necesita reglas más finas que lo
  que User Permission da solo.

**Siguiente al retomar:** S1.9 (Carril B — condicional, no aplicado sin
aprobación explícita de Yedin) o cerrar Fase 1.

---

## 2026-08-31 — S2.1: DGII Settings por Company, barrera D19 extendida

**Estado:** implementación y suite verde. `DGII Settings` es un DocType
estándar del módulo `ECF`, no un Single: su nombre deriva de `company` y el
campo conserva `unique: 1`. Solo se persistieron dos configuraciones de
prueba bajo `_Test Company KORVEXCIO A/B`; las dos Companies reales quedaron
sin configuración fiscal falsa.

**Qué se escribió:**
- `korvexcio/ecf/doctype/dgii_settings/` — DocType con `company`, ambiente
  (`TesteCF`, `CerteCF`, `eCF`), proveedor (`Alanube`, `ECF SSD`), timeouts
  obligatorios de 10/30 segundos y `live_sync` apagado. No hay default de
  provider, adapter HTTP, certificado ni secreto: S2.2/S2.7 siguen fuera.
- `dgii_settings.py` rechaza ambos timeouts fuera de 1–300 segundos con
  mensajes para usuario en español.
- Permisos: `System Manager` administra; `Dueño` lee/escribe/crea sin borrar;
  `Contador` solo lee; ningún cajero recibe permiso.
- `DGII Settings` entró a `COMPANY_SCOPED_DOCTYPES`, por lo que D19 congela
  la Company después de crear el documento. El escenario 9 de aislamiento
  confirma que un Contador limitado a A lista/lee A, no B, y no puede moverla.

**Intento RED — no cuenta como RED válido de TDD:** el commit `74a5205` se
aplicó al nodo, pero la importación del controlador inexistente falló durante
discovery (`ModuleNotFoundError`, `Ran 0 tests`, exit 1). Ninguna aserción llegó
a ejecutarse. Se conserva esta evidencia por honestidad: la cobertura final sí
prueba el comportamiento, pero S2.1 **no tiene evidencia cronológica de un test
descubrible fallando antes del código de producción**. Después del primer GREEN
apareció otra trampa de Frappe:
un test ubicado dentro de `doctype/dgii_settings/` infiere ese DocType y trata
de sembrar toda la cadena de Links antes de `setUpClass`; la cadena de Company
terminó en `DoesNotExistError: DocType Payment Gateway not found`. El arreglo
oficial y mínimo fue `IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]`: no
siembra esa dependencia rota, pero `before_tests()` crea explícitamente las
Companies A/B que los tres tests necesitan.

**GREEN y operación, salida real:**

```text
bench --site korvexcio.korvexdev.cc migrate
Updating DocTypes for korvexcio [100%]
after_migrate ejecutado
exit 0

docker compose restart backend queue-short queue-long scheduler websocket
backend Started
queue-short Started
queue-long Started
scheduler Started
websocket Started

bench --site korvexcio.korvexdev.cc run-tests --app korvexcio --module korvexcio.ecf.doctype.dgii_settings.test_dgii_settings
Ran 3 tests in 0.263s
OK

bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Running 13 integration tests for korvexcio
Ran 13 tests in 0.940s
OK (skipped=1)

frappe.get_all("DGII Settings", fields=["company", "ambiente"])
[{"company":"_Test Company KORVEXCIO B","ambiente":"CerteCF"},
 {"company":"_Test Company KORVEXCIO A","ambiente":"TesteCF"}]

systemctl status korvex-api --no-pager
Active: active (running)
curl -s http://127.0.0.1:4000/health
{"status":"ok","checks":{"postgres":"ok","redis":"ok"},"uptime":207091}
df -h /
98G total, 36G used, 58G avail, 39%
```

**D21 — el usuario MariaDB del site se limita a la subred Docker privada de
KORVEXCIO (`172.18.%`), no a una IP de contenedor.** El reinicio obligatorio
movió `backend` de `172.18.0.5` a `172.18.0.9`; Frappe había creado el grant
solo para la IP vieja y la primera suite post-restart murió antes de ejecutar
tests con `OperationalError 1045`. Yedin autorizó explícitamente ampliar el
host a la subred aislada `172.18.0.0/16`; MariaDB no publica puertos al host.
Se conservó el mismo usuario, contraseña y privilegios.

```text
SELECT User, Host ...
_2121ada3306b29ac  172.18.0.5

docker inspect ... korvexcio-backend-1
/korvexcio-backend-1 172.18.0.9

RENAME USER ...@'172.18.0.5' TO ...@'172.18.%'
exit 0

SELECT User, Host ...
_2121ada3306b29ac  172.18.%

bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 13 tests in 0.940s
OK (skipped=1)
```

**Evidencia adicional recapturada, salida real:**

```text
frappe.get_all("DGII Settings", fields=["company", "ambiente", "provider"])
[{"company":"_Test Company KORVEXCIO B","ambiente":"CerteCF","provider":"ECF SSD"},
 {"company":"_Test Company KORVEXCIO A","ambiente":"TesteCF","provider":"Alanube"}]
exit 0

python -m compileall -f korvexcio\ecf\doctype\dgii_settings korvexcio\isolation.py korvexcio\tests\test_isolation.py
exit 0; compiló los 5 archivos

python -m json.tool korvexcio\ecf\doctype\dgii_settings\dgii_settings.json
exit 0

git diff --check f0e7301..HEAD
exit 0

rg "ignore_permissions=True|frappe\.db\.sql\(" korvexcio
NO MATCHES: ignore_permissions=True / frappe.db.sql(
```

No se instaló una dependencia solo para lint: `compileall` es el mecanismo
equivalente disponible. S2.1 quedó cerrado con suite y auditorías verdes; la
desviación de TDD descrita arriba queda registrada, no rebautizada como éxito.

**Deuda que no cambió:** S0.3/S0.9 siguen abiertas por D20. No bloquean la
estructura de S2.1, pero detienen S2.7 si siguen sin correo de proveedor,
RNC y certificado real.

---

## 2026-08-31 — Auditoría de S2.1: APROBADO

**Quién:** Claude, en rol de auditor — Codex dejó S2.1 explícitamente
pendiente de esto ("no se declara cerrada antes de sus veredictos").
**No se confió en lo escrito**: cada comando de evidencia de Codex se
volvió a correr de forma independiente antes de dar veredicto.

**Verificación independiente, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 13 tests in 0.940s -> OK (skipped=1)          # confirma el 13/13 de Codex

rg "ignore_permissions=True|frappe\.db\.sql\(" korvexcio/ -> sin resultados

docker run --rm semgrep/semgrep scan --config .semgrep/korvexcio-isolation.yml korvexcio/
FINDINGS: 0

docker run --rm ghcr.io/astral-sh/ruff:latest check korvexcio/
1 error (formato de imports en test_dgii_settings.py) -> corregido y reverificado, 0 errores

frappe.get_all("DGII Settings") -> solo las dos _Test Company, VLJ/ESE reales sin config falsa

KORVIS: {"status":"ok",...}, uptime nunca se reinició
docker ps: 9 contenedores Up, db healthy
```

**`/code-review` (nivel medium):** 0 hallazgos. Revisadas las 8 aristas
(correctitud, comportamiento removido, cruce de archivos, reuso,
simplificación, eficiencia, altitud, convenciones de `CLAUDE.md`) contra el
diff completo. Un candidato descartado tras análisis (timeout `None` vía
API): Frappe castea campos `Int` con `cint()` antes de `validate()`, así
que `None` llega como `0` — el validador ya lo atrapa, no hay excepción sin
manejar.

**`/security-review`:** 0 hallazgos con confianza >80%. Revisado el modelo
de permisos (ningún cajero tiene acceso a `DGII Settings`, `Contador`
solo lectura, `Dueño` sin borrar), la validación de timeouts (server-side,
no evadible por API), y el mensaje de error de `freeze_company()` (expone
`company_en_db`, pero como `autoname` deriva de `company`, quien ya puede
disparar ese error ya conocía el valor — sin fuga nueva).

**No se corrió `/secure-vibe` (modo B) completo — a propósito, según la
propia regla del proyecto:** `docs/08-BLUEPRINT.md` §7.1 reserva el loop de
4 auditores y `/secure-vibe` para el **cierre** de Fase 2, Fase 5, y
pre-go-live — no para cada slice individual. Correrlo aquí sería quemar
rate limit sin ganar rigor extra; `/security-review` es exactamente lo que
la tabla del blueprint pide para slices dentro de Fase 2.

**Hallazgo positivo, no un problema:** Codex montó un checkout de git real
en `apps/korvexcio` del nodo (`feat/ecf`, limpio, `HEAD` verificado) — el
nodo ahora consume por `git pull`, no por `scp`/`docker cp` manual como en
sesiones anteriores. Es una mejora real sobre el flujo previo, más fiel a
la regla 7 del `CLAUDE.md` ("nunca se edita código en el servidor").
También confirmado: la rama `feat/ecf` es la que el propio blueprint §7.2
ya tenía reservada para el carril crítico de Fase 2 — no es una desviación
del plan, aunque el Carril B (paralelo) nunca se aprobó.

**Un lint real, arreglado en el camino:** import mal formateado en
`test_dgii_settings.py` (ruff I001) — no estaba en el radar de Codex porque
`ruff` no está instalado en el bench; se corrió vía contenedor Docker,
corregido, reverificado limpio en todo `korvexcio/`. Commit `2ceef25`.

**Veredicto: APROBADO.** S2.1 pasa a `COMPLETADO`. Cero críticos, cero
altos. Un lint menor, ya corregido.

**Siguiente al retomar:** S2.2 — `DGII Digital Certificate` (`.p12` como
Attach, password como Password). Sigue bloqueado en la práctica por
S0.9/S0.3 — se puede escribir la estructura del DocType, pero sin
certificado real no hay nada que cargar.

---

## 2026-08-31 — Branding: logo en el login real, README actualizado

**Estado:** COMPLETADO, fuera de la secuencia de slices — pedido directo de
Yedin, no bloquea Fase 2.

**Qué se hizo:** Yedin trajo el logo de KORVEXCIO (concepto "validación
fiscal"). Se subió como `File` de Frappe y se seteó en
`Website Settings.app_logo` — aparece de verdad en `/login`, no solo
guardado en disco. Se usó la versión **transparente 4K**
(`assets/branding/final/korvexcio-logo-transparent-4k.png`), mejor que el
primer intento con la versión de fondo blanco. Los archivos sueltos que
llegaron a la raíz del repo se organizaron bajo `assets/branding/{concepts,final}/`.

**README.md reescrito** — seguía diciendo "⚪ Semilla, cero código" desde el
día 1. Ahora refleja Fase 0+1 cerradas, los nombres reales de las dos
Companies, y el logo arriba.

**Se investigó y se descartó, con motivo:** Yedin pidió agregar el logo
también en el repo de ADAP (`C:\PROYECTOS\ADAP`, el proyecto de KORVIS),
usando de referencia cómo `aiassistant.korvexdev.cc` maneja su login. Un
subagente exploró ese repo a fondo: el login del dashboard de KORVIS
(`apps/dashboard/src/app/login/page.tsx`) usa un componente `KorvexWordmark`
con un PNG fijo — y **su propio `CLAUDE.md` prohíbe explícitamente meterle
marca de un tenant o producto**: *"El dashboard es el producto de la
PLATAFORMA, no del tenant. Lleva marca Korvex y NO los colores de la
institución."* No existe ningún registro de productos hermanos ni carpeta
de assets compartida entre repos donde el logo de KORVEXCIO tuviera un
lugar real. **No se tocó el repo de ADAP** — hacerlo habría violado una
regla escrita de ese proyecto sin ganar nada, porque no hay dónde
engancharlo.

**Verificación, salida real:**

```
curl -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/login | grep korvexcio-logo
-> korvexcio-logo-finalffac59.png  (aparece 3 veces en el HTML)

KORVIS: {"status":"ok",...}
df -h /: 58G libres, sin cambio
```

**Deuda:** el login sigue siendo el genérico de Frappe con el logo
cambiado — no hay una pantalla de login propia con la paleta de marca
completa (azul `#2b44e6`-ish + gris acero, viendo el logo). Eso es trabajo
de frontend que no está en ningún slice todavía; se anota para cuando
haya UI propia (Fase 4+).

**Siguiente al retomar:** Fase 2 — S2.2, `DGII Digital Certificate`.
**Esta sesión para aquí** — el prompt para continuar queda en
`PROMPT-CLAUDE-CODE.md`, listo para pegar en Codex.

---

## 2026-08-31 — Cierre operativo final de S2.1 y handoff a S2.2

S2.1 quedó desplegado desde `feat/ecf` y probado en el nodo sobre el commit
`e1b8edc`. No se mezcló a `main`: `docs/08-BLUEPRINT.md` §7.2 manda hacer
merge solo en los gates de fase. El push correcto de este slice es
`origin/feat/ecf`.

El restart obligatorio reveló y cerró el incidente D21: el usuario MariaDB
estaba amarrado a la IP efímera `.5`, `backend` pasó a `.9` y la primera suite
murió con `1045 Access denied`. Con autorización explícita de Yedin, el host
quedó limitado a `172.18.%`, la red privada `korvexcio_default`; la DB sigue
sin puerto publicado al host.

**Verificación fresca de cierre, salida real:**

```text
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Running 13 integration tests for korvexcio
Ran 13 tests in 0.940s
OK (skipped=1)

frappe.get_all("DGII Settings", fields=["company","ambiente"])
[{"company":"_Test Company KORVEXCIO B","ambiente":"CerteCF"},
 {"company":"_Test Company KORVEXCIO A","ambiente":"TesteCF"}]

systemctl status korvex-api --no-pager
Active: active (running)

curl -s http://127.0.0.1:4000/health
{"status":"ok","checks":{"postgres":"ok","redis":"ok"},"uptime":207091}

df -h /
/dev/mapper/ubuntu--vg-ubuntu--lv  98G  36G  58G  39% /
```

La auditoría de seguridad y la de fiabilidad devolvieron **APROBADO**, sin
Críticos ni Altos. Sus hallazgos Medios/Bajos quedaron en deuda técnica. La
revisión de spec detectó que `Ran 0 tests` estaba mal descrito como RED real;
la bitácora ahora lo registra correctamente como desviación de TDD, sin
fabricar evidencia retroactiva.

**Siguiente:** S2.2 — `DGII Digital Certificate`. El checkout conserva el
trabajo no committeado que Claude ya empezó en `isolation.py` y
`ecf/doctype/dgii_digital_certificate/`; no se reseteó, movió ni incluyó en
el commit de S2.1. `PROMPT-CLAUDE-CODE.md` quedó actualizado para retomarlo.

---

## 2026-08-31 — S2.2: COMPLETADO — DGII Digital Certificate, password nunca en texto plano

**Estado:** COMPLETADO, verificado. `DGII Digital Certificate`: `certificate`
(Attach), `password` (**Password**, nunca Data), `company` (único), `valid_until`
+ aviso configurable (`expiry_warning_days`). Un registro por Company.
Agregado a `COMPANY_SCOPED_DOCTYPES`. Permisos: solo `System Manager` y
`Dueño` — ni `Contador` ni ningún `Cajero` lo ven, a propósito (más sensible
que `DGII Settings`).

**Hallazgo real corrigiendo el propio test:** el primer intento del
escenario 10 de aislamiento usó un usuario `Cajero` y reventó — no por bug
de la barrera, sino porque `Cajero` no tiene *ningún* `DocPerm` en este
doctype (correcto: un cajero no debe ver el certificado). Se corrigió
usando un `Dueño` acotado a una sola Company vía `User Permission` — el
único rol, aparte de System Manager, con acceso real.

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 18 tests in 1.258s -> OK (skipped=1)

# password nunca en texto plano — probado dos veces, distinto:
frappe.db.get_value(...,"password") != valor real puesto
frappe.client.get(...)["password"] no contiene el valor real

ruff check korvexcio/ -> All checks passed!
semgrep (regla propia) -> FINDINGS: 0
KORVIS: {"status":"ok",...}   df -h /: 58G libres, sin cambio
```

**Deuda:** ningún `.p12` real cargado — el cliente no está registrado
todavía (S0.9/S0.3). El campo `certificate` acepta el Attach; probarlo con
un archivo real es cuando haya certificado de verdad.

**Siguiente:** S2.3 — Secuencia eNCF.

---

## 2026-08-31 — S2.3: COMPLETADO — Secuencia eNCF, reserva atómica, y un error operativo real

**Estado:** COMPLETADO. `Secuencia eNCF`: `company` + `tipo_ecf` (E31/E32/E34)
con nombre compuesto vía `autoname: format:{company}-{tipo_ecf}` — dos
secuencias del mismo tipo en la misma Company chocan por nombre duplicado
directo, sin necesitar un campo `unique` compuesto. `desde`/`hasta`/`siguiente`
validados, aviso configurable cuando quedan pocos números.

**Dos bugs reales, corregidos en el camino, no ocultados:**

1. **`Document.lock()` no es un mutex de propósito general.** El primer
   `reserve_next()` usaba `self.lock()` alrededor de leer-incrementar-guardar
   — reventó con `DocumentLockedError` en la segunda llamada, porque
   `Document.save()` de Frappe **rechaza guardar un doc que está lockeado**
   (el lock es para "esto está en cola para un job en background, no lo
   toques", no un mutex de aplicación). Se corrigió con
   `frappe.db.get_value(..., for_update=True)` — un `SELECT ... FOR UPDATE`
   real, pero vía el query builder de Frappe, **no** `frappe.db.sql()` crudo
   (eso sigue prohibido, regla 12b).

2. **Error operativo propio: un `migrate` borró el `DocType` de S2.2 de la
   base.** Al limpiar el checkout del nodo entre S2.2 y S2.3 (para no
   dejarlo sucio para Git), el siguiente despliegue de S2.3 solo copió los
   archivos NUEVOS (`secuencia_encf/` + `isolation.py`), no el árbol
   completo — `bench migrate` vio que faltaba
   `dgii_digital_certificate.json` en disco y lo registró como "orphan
   doctype", **borrando el registro `DocType` de la base** (la tabla SQL
   sobrevivió, sin pérdida de datos reales — solo había fixtures de test).
   Se corrigió resincronizando el árbol `korvexcio/` completo y corriendo
   `migrate` de nuevo, que restauró el registro. **Lección: cualquier
   despliegue de prueba tiene que llevar el árbol completo, nunca un
   subconjunto** — un `migrate` parcial puede borrar estructura de un
   slice anterior sin avisar más que "Removing orphan doctypes" en el log,
   fácil de no notar.

**Verificación, salida real (después de corregir los dos bugs):**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 24 tests in 1.260s -> OK (skipped=1)     # corrida 1
Ran 24 tests in 1.237s -> OK (skipped=1)     # corrida 2, idempotencia

frappe.db.exists("DocType", "DGII Digital Certificate") -> "DGII Digital Certificate"  (restaurado)

ruff check korvexcio/ -> All checks passed!
semgrep (regla propia) -> FINDINGS: 0
KORVIS: {"status":"ok",...}   df -h /: 58G libres, sin cambio
```

**Cambio de flujo, a partir de aquí:** en vez de seguir desplegando por
`tar`/`docker cp` ad-hoc (la causa raíz del bug #2), se vuelve al patrón de
Codex: commit + push a `origin/feat/ecf`, y el nodo hace `git pull` — un
árbol completo y consistente siempre, verificado por SHA, no por bultos
parciales.

**Siguiente:** S2.4 — DocType `ECF` (el documento principal, submittable).

---

## 2026-08-31 — S2.4: COMPLETADO — DocType ECF, submittable, "se anula no se cancela"

**Estado:** COMPLETADO, primer intento sin bugs (aprendida la lección de S2.3
sobre desplegar el árbol completo). `ECF`: submittable (`docstatus` como
máquina de estados de emisión), `reference_doctype`/`reference_name`
(Dynamic Link genérico — no atado a `Sales Invoice` todavía, cualquier
documento origen sirve), `tipo_ecf`, `encf`, `estado` (Pendiente/Aceptado/
Rechazado/Contingencia/Anulado — la respuesta real de la DGII, distinta del
docstatus), `track_id`, `codigo_seguridad`, `qr_url`, `signed_xml`,
`validation_messages`, `attempt_count`. Sin lógica de emisión (S2.6/S2.7
siguen sin existir) — este slice modela el documento y dos reglas de
negocio: **un e-CF Aceptado no se cancela ni se borra, se anula** (regla 3
del blueprint), verificado incluso contra un `delete_doc(force=True)`.

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc migrate -> limpio
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 28 tests in 2.001s -> OK (skipped=1)

ruff check korvexcio/ -> All checks passed!
semgrep (regla propia) -> FINDINGS: 0
KORVIS: {"status":"ok",...}   df -h /: 58G libres, sin cambio
```

**Siguiente:** S2.5 — `ECF Integration Log` con secretos enmascarados.

---

## 2026-08-31 — S2.5: COMPLETADO — ECF Integration Log, enmascarado real (con un bug real de regex)

**Estado:** COMPLETADO. `ECF Integration Log` (patrón KSA): registra cada
llamada a un proveedor (`emitir`/`consultar`/`anular`/`token`), con
`mask_sensitive_info()` — función pública, reusable desde `providers/`
cuando existan (S2.6/S2.7) — que enmascara `password`/`token`/`secret`/
`api_key`/`authorization`/etc. tanto en JSON (`"token": "..."`) como en
headers HTTP (`Authorization: Bearer ...`). Se aplica siempre en
`validate()`, sin depender de que el caller se acuerde de enmascarar antes.

**Bug real encontrado por el propio test, no por revisión:** la regex de
headers usaba `\S+` para capturar el valor — que solo agarra UNA palabra.
`"Authorization: Bearer xyz789"` son DOS palabras después de los dos
puntos; el resultado enmascaraba "Bearer" y **dejaba el token real
intacto**. Se corrigió a `[^\n]+` (el resto de la línea). El test que lo
atrapó es exactamente el que pide el blueprint: "forzar una llamada y
confirmar que el token no aparece en el log" — si no se hubiera escrito
ese test específico, el bug se habría ido a producción.

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio
Ran 31 tests in 2.012s -> OK (skipped=1)

ruff check korvexcio/ -> All checks passed!
semgrep (regla propia) -> FINDINGS: 0
KORVIS: {"status":"ok",...}   df -h /: 58G libres, sin cambio
```

**Siguiente:** S2.6 — `providers/base.py`, la interfaz.

---

## 2026-08-31 — S2.6: COMPLETADO — interfaz `FiscalProvider`, Result/Ok/Err

**Estado:** COMPLETADO. `korvexcio/ecf/providers/base.py` — la interfaz
abstracta que cualquier proveedor real (Alanube, ECF SSD) va a implementar
cuando S2.7 lo desbloquee. Tres métodos (`emitir`, `consultar`, `anular`),
cada uno devuelve `Result[T]` (`Ok[T] | Err`) en vez de levantar
excepciones — así un fallo del proveedor real, corriendo dentro de un job
en background (S2.10), nunca tumba el worker de la cola: quien llama
recibe un `Err` tipado y decide si reintenta.

**Sin implementación real todavía** — sigue bloqueado por S0.9/S0.3 (D20):
sin proveedor elegido, sin RNC ni certificado del cliente. Este slice es
solo la base/estructura que el resto del módulo `ecf` puede empezar a
depender, tal como pidió Yedin explícitamente en el `/goal` de esta sesión.

**Test:** `providers/test_base.py` con un `FakeProvider` de prueba (nunca
toca la red) que ejercita el contrato completo — instanciar la clase
abstracta directamente falla (`TypeError`), y cada método responde tanto
`Ok` como `Err` sin levantar. Exactamente lo que pedía el blueprint: "Test
unitario del contrato con un provider falso."

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio --test-category all
Ran 31 tests in 2.056s -> OK (skipped=1)
Ran 5 tests in 0.001s -> OK
(36 tests totales entre ambas corridas del runner, todas verdes)

semgrep (regla propia korvexcio-isolation.yml) -> Findings: 0
KORVIS: {"status":"ok",...}   df -h /: 58G libres, 39%, sin cambio
git rev-parse HEAD (nodo) == 88c940e == origin/feat/ecf (SHA verificado)
```

**Deuda encontrada, NO tocada (fuera del scope de este slice, R3):** el
mismo `ruff check` sobre el árbol completo dio 6 hallazgos en código de
slices anteriores — `korvexcio/ecf/providers/base.py` y `test_base.py`
(los archivos de S2.6) salieron limpios:
- `DTZ011` (×5) en `dgii_digital_certificate.py`/su test (S2.2): usan
  `date.today()` sin timezone explícito — regla de `flake8-datetimez`.
- `BLE001` (×1) en `tests/test_isolation.py:231` (S1.8): un
  `except Exception as e` deliberado, para comparar el *tipo* de error
  entre escenarios de aislamiento (el punto del test es que da igual cuál
  excepción sea, todas las Company-cruzadas tienen que dar el mismo
  status/mensaje — escenario 6 de enumeración).

En S2.5 el `ruff check` sobre el mismo árbol había dado "All checks
passed!" — lo más probable es que `ghcr.io/astral-sh/ruff:latest` haya
subido de versión entre una corrida y la otra y promovido reglas nuevas a
default (la imagen no está fijada por SHA). No se investigó más a fondo
porque no es parte de este slice. Se anota en la tabla de deuda técnica.

**Siguiente:** S2.8 — plantillas Jinja2 `ecf_32.xml`/`rfce.xml` (S2.7 sigue
bloqueado por D20; se salta directo al siguiente slice desbloqueado, tal
como indica el `/goal` activo: dejar la base lista, sin forzar S2.7 sin
proveedor real).

---

## 2026-08-31 — S2.8: COMPLETADO — plantillas Jinja2 de e-CF (SIN el XSD oficial)

**Estado:** COMPLETADO con una desviación real, dicha de una vez: el
blueprint pide "el XML generado valida contra el XSD oficial de la DGII".
**No tenemos ese XSD.** Bajarlo del portal de la DGII pide exactamente el
mismo acceso que sigue bloqueado por D20 (S0.9/S2.7): RNC y certificado del
cliente. No se inventó un XSD ni se fingió una validación — se reporta
como bloqueo (R2), no se improvisa un reemplazo.

**Lo que sí se pudo hacer, con evidencia real, no de memoria:** en vez de
adivinar la estructura del e-CF 32/RFCE, se bajó el archivo real del repo
MIT `platinum-place/laravel-dgii` (ya verificado como referencia real en
`docs/08-BLUEPRINT.md` §2.1) — `resources/views/ecf/ecf_32.blade.php` (727
líneas) y `resources/views/rfce/xml.blade.php` (120 líneas) — vía `curl`
directo a `raw.githubusercontent.com` (WebFetch normal resume con un
modelo chico y no entrega el contenido verbatim; para traducir una
estructura fielmente hace falta el archivo real, no un resumen). Se
tradujo 1:1 — mismos tags, mismo anidamiento, mismo orden — a
`korvexcio/ecf/templates/ecf_32.xml` y `rfce.xml`.

**`korvexcio/ecf/xml_render.py`:**
- `render_ecf_32(context)` / `render_rfce(context)` — reciben un dict
  (`IdDoc`/`Emisor`/`Comprador`/`Totales`/`DetallesItems`/etc, mismos
  nombres de campo del e-CF oficial). El mapeo real desde `Sales Invoice`
  vive en S2.9, no aquí.
- Todo string del contexto se escapa (XML) antes de renderizar — un nombre
  de cliente o de item con `&`/`<` no puede romper el documento.
- `env.trim_blocks`/`env.lstrip_blocks` del Jinja compartido de Frappe se
  prenden solo dentro de un `try/finally` — exactamente la advertencia del
  blueprint: no restaurarlo rompe cualquier otro template (print formats,
  correos) que se renderice en la misma request.
- `validate_well_formed()` — lo único que se puede verificar de verdad sin
  el XSD: que el XML resultante parsea. No es lo mismo que "válido contra
  el schema oficial", y el docstring lo dice así de claro.

**Bugs reales encontrados por los tests, no por revisión:**
1. `TEMPLATES_DIR` apuntaba a `korvexcio/ecf/` en vez de
   `korvexcio/ecf/templates/` — `FileNotFoundError` en 6 de 8 tests al
   primer intento. Corregido.
2. `ruff` (sobre archivos SÍ de este slice, no deuda vieja): `B017` por un
   `assertRaises(Exception)` deliberadamente amplio (el test prueba que el
   `try/finally` restaura el entorno compartido sin importar QUÉ excepción
   reviente, no una excepción específica) — resuelto con `# noqa: B017` y
   el porqué en un comentario; y `DTZ005` por `datetime.now()` sin
   timezone — resuelto con `zoneinfo.ZoneInfo("America/Santo_Domingo")`
   explícito (la DGII quiere hora local de RD en `FechaHoraFirma`, no UTC).

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio --test-category all
Ran 31 tests in 2.032s -> OK (skipped=1)
Ran 13 tests in 0.444s -> OK
(44 tests totales: 31 integration + 13 unit -- 8 de xml_render + 5 de providers)

ruff check (solo archivos de S2.8) -> All checks passed!
semgrep (regla propia) -> Findings: 0 (28 archivos escaneados)
KORVIS: {"status":"ok",...}   df -h /: 58G libres, 39%, sin cambio
git rev-parse HEAD (nodo) == 17f5611 == origin/feat/ecf (SHA verificado)
```

**Deuda que esto abre:** re-validar `ecf_32.xml`/`rfce.xml` contra el XSD
real de la DGII en cuanto S0.9/S2.7 se desbloqueen (D20) — antes de S5.4
(certificación). La fidelidad de tags/orden es alta (viene de una
implementación MIT en producción, no inventada), pero "alta fidelidad a
una referencia no oficial" no es lo mismo que "validado contra el schema
oficial", y esta entrada existe para que esa diferencia no se pierda.

**Siguiente:** S2.9 — `hooks.py` (`doc_events`, nunca
`override_doctype_class`): `validate` (umbral RD$250,000), `before_submit`
(reservar eNCF), `on_submit` (crear `ECF`), `before_cancel`.

---

## 2026-08-31 — S2.9: COMPLETADO — Sales Invoice conectada a eNCF/ECF

**Estado:** COMPLETADO. `korvexcio/ecf/sales_invoice_hooks.py` conecta
`Sales Invoice` (de ERPNext, nunca tocada — regla 1) con la maquinaria de
S2.2-S2.8, toda por `doc_events` en `hooks.py`, nunca por
`override_doctype_class`:
- `validate` → exige RNC a partir de RD$250,000 (Norma 05-19, regla 9)
- `before_submit` → reserva el próximo eNCF de la `Secuencia eNCF` de esa
  Company + tipo
- `on_submit` → crea el `ECF` (estado Pendiente), apuntando a la Sales
  Invoice vía `reference_doctype`/`reference_name`
- `before_cancel` → bloquea cancelar si el `ECF` ya está Aceptado (espejo
  de `ECF.before_cancel` de S2.4 — se anula, no se cancela)

**D21 (nueva):** el tipo de e-CF se decide con la única señal que existe
hoy sin proveedor real — si la factura resolvió `tax_id` → **E31**
(crédito fiscal); si no → **E32** (consumo, el 95% del volumen). El flujo
completo de E31 (sus propias validaciones) se termina en S2.13; aquí solo
hacía falta elegir el tipo correcto para reservar la secuencia correcta.

**Todo esto es local** — cero llamadas de red, cero contacto con
`FiscalProvider`. El POS nunca espera a la DGII para cerrar una venta
(regla 3): la llamada real al proveedor es el job en background de
S2.10, que sigue bloqueado por S2.7/D20.

**Bug real encontrado por el test, no por revisión:** `Sales
Invoice.tax_id` tiene `fetch_from: customer.tax_id` y es `read_only` —
ponerlo a mano en una factura sin guardar se pisa solo durante
`validate()`, volviendo al valor (vacío) del Customer. El primer intento
de test fallaba silenciosamente (E31 nunca se disparaba). Se corrigió
dándole el RNC a un Customer de prueba dedicado en vez de a la factura.

**Verificación, salida real:**
```
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio --test-category all
Ran 38 tests in 3.863s -> OK (skipped=1)
Ran 13 tests in 0.469s -> OK
(51 tests totales: 38 integration + 13 unit, subiendo de 44 tras S2.8)

ruff check (archivos de S2.9) -> All checks passed!
semgrep (regla propia) -> Findings: 0 (29 archivos)
KORVIS: {"status":"ok",...}   df -h /: 58G libres, 39%, sin cambio
git rev-parse HEAD (nodo) == bb9d006 == origin/feat/ecf (SHA verificado)
```

**Siguiente:** S2.10 — cola asíncrona (`frappe.enqueue(...,
enqueue_after_commit=True)` + `scheduler_events` de retry/poll/refresh).

---

## Fases

> El detalle de cada slice, con su verificación y su entregable, está en
> **`docs/08-BLUEPRINT.md` §6**. Aquí solo el estado.

### Fase 0 — Reducir riesgo · 31/08 → 07/09 *(CERRADA 31/08 — con deuda conocida, D20)*
- [x] **S0.1** — repo con remote, `.gitignore`, `.env.example`, rutas corregidas
- [x] **S0.1b** — Secure-Vibe modo A + pre-commit con gitleaks
- [x] **S0.2** — acceso al nodo por Tailscale arreglado
- [ ] **S0.3** — correos a proveedores e-CF *(Yedin — bajó a deuda técnica por D20, ya no bloquea)*
- [x] **S0.4** — checklist previo del nodo, todo verde
- [x] **S0.5** — **bench v16 de pie en `korvex-node1`. D2 cerrada.**
- [x] **S0.6** ⭐ — site `korvexcio.korvexdev.cc` con ERPNext instalado
- [x] **S0.7** — las dos `Company`: **VAPERIA LA J Y EL JALAPEÑO** y **EL SABOR DE LAS 5 ESQUINAS**, cada una con su `tax_id` (RNC pendiente)
- [ ] **S0.7b** — site `demo.korvexdev.cc` *(descartada por Yedin, no bloquea nada)*
- [~] **S0.8** — matriz completa con evidencia de código, recomienda POSNext (revierte D16); prueba de red cortada pendiente → `docs/10-SPIKE-POS.md`
- [ ] **S0.9** 🔴 *(bajó a deuda técnica por D20)* — necesita S0.3 o RNC+certificado. Ninguna de las 3 vías se puede intentar sin eso. **Para de verdad en S2.7**, no antes
- [x] **S0.10** — script de backup+retención probado; falta solo el `sudo systemctl enable` de Yedin
- [x] **S0.11** — 24 SKUs representativos (16 VLJ con 1 template+9 variantes, 8 ESE)
- [x] **S0.12** — Fase 0 cerrada por **D20** (decisión explícita de Yedin en el chat, 31/08): S0.9/S0.3 bajan a deuda técnica en vez de gate. `data/korvex.json` actualizado a "activo"

**🚦 Gate original — NO se esperó a que se cumpliera (D20).** S0.5 ✅ ·
S0.8 con veredicto escrito (POSNext, pendiente confirmar) ✅ · S0.9 sin
TrackID, movida a deuda con el OK explícito de Yedin. **No se fingió que
está resuelto — está anotado como abierto y sigue así.**

### Fase 1 — Esqueleto de la app · 08/09 → 12/09 *(CERRADA 31/08/2026)*
- [x] S1.1 `bench new-app korvexcio` con módulos `ECF` y `Retail` — GPLv3, instalada, verificada
- [~] S1.2 `apps.json` con el repo propio · **fijar SHA imposible sin mirror** (confirmado
      en el código de `bench`, git shallow clone no acepta SHA arbitrario) — deuda documentada,
      no resuelta
- [x] S1.3 CI: 6 workflows (server-tests, lint, gitleaks, semgrep, osv-scanner, trivy) +
      regla propia de aislamiento en Semgrep, probada de verdad (2 hallazgos exactos en un
      fixture con las 2 violaciones a propósito)
- [x] S1.4 `before_tests` — DOS companies de prueba (`_Test Company KORVEXCIO A/B`), idempotente
- [x] S1.5 `custom/customer.json` — `tipo_identificacion` + `rnc`, verificado con `bench migrate` real
- [~] S1.6 `MASTER_ENCRYPTION_KEY` generado (600, nunca visto) · `/security-review` sin hallazgos ·
      secretos de e-CF siguen bloqueados en S0.9/S2.7 (no existen, no se inventaron)
- [x] S1.7 roles y User Permissions por Company — probado como el usuario real (`frappe.set_user`),
      no como Administrator
- [x] S1.8 🔴 **la barrera de aislamiento** (`freeze_company`) + 9 de 12 escenarios reales;
      S2.1 habilitó el escenario de DGII Settings y dejó S2.2/S2.7 diferidos
- [ ] S1.9 **N/A** — condicional a aprobar el carril B (§7.2), Yedin no lo aprobó. Correctamente
      cerrado como "no aplica", no como pendiente

### Fase 2 — Módulo ECF · 15/09 → 03/10 · ⬅ CAMINO CRÍTICO
- [x] S2.1 `DGII Settings` — código, migrate, suites, evidencia y auditoría (code-review + security-review, APROBADO)
- [x] S2.2 `DGII Digital Certificate` — password nunca en texto plano, aviso de vencimiento
- [x] S2.3 `Secuencia eNCF` — reserva atómica con `for_update=True`
- [x] S2.4 `ECF` submittable — "se anula, no se cancela"
- [x] S2.5 `ECF Integration Log` — secretos enmascarados de verdad (bug real de regex atrapado por el test)
- [x] S2.6 `providers/base.py` — interfaz `FiscalProvider`, Result/Ok/Err, test con fake provider
- [ ] S2.7 🔴 bloqueado por D20 (S0.9/S0.3) — el proveedor real
- [~] S2.8 plantillas Jinja2 `ecf_32.xml`/`rfce.xml` — traducidas de laravel-dgii (MIT), SIN validar contra el XSD oficial (no lo tenemos, D20)
- [~] S2.9 `hooks.py` de Sales Invoice — implementación auditada; correcciones de fuente RNC, permisos POS y moneda base escritas en DEV, pendientes de deploy y verificación
- [ ] S2.10 → S2.15 (`docs/08-BLUEPRINT.md` §6)

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

### Auditoría y corrección S2.9 — 2026-08-31

La auditoría independiente confirmó la suite existente (38 integration + 13
unit, verde en el nodo `bb9d006`) y encontró dos bloqueantes en S2.9: la lógica
leía `Customer.tax_id` en vez del campo acordado `Customer.rnc`, y `on_submit`
creaba `ECF` con permisos del usuario POS aunque el Cajero no tiene create.
El parche está escrito en DEV pero **SIN verificar en el nodo**: usa
`Customer.rnc` con fallback de migración, compara el umbral contra
`base_grand_total` y crea el registro interno con `ignore_permissions=True`.

S2.10 queda pausado, sin commit ni deploy. En DEV se escribió el primer
microslice (estado `Enviando` + claim atómico, TrackID conservado como
`Pendiente`, guard de XML, validación de factura origen, redacción de errores,
resolver por `company`, throttle Redis y cron de tokens), todavía **SIN
verificar en Frappe**. La auditoría también dejó abiertos
XML vacío, cancelación durante cola, idempotencia, aceptación prematura,
rate-limit y pruebas reales de `enqueue_after_commit`; no se deben cerrar como
resueltos hasta corregirlos. S2.8 permanece **PARCIAL** porque falta la
validación contra el XSD oficial. S2.7 continúa bloqueado por D20/S0.9.

## Deuda técnica abierta

Ordenada por lo que más duele.

| Sev | Qué | Qué la mitiga hoy | La cura de verdad |
|---|---|---|---|
| 🔴 | **S0.9/S0.3 — degradado de gate a deuda por D20 (OK de Yedin, 31/08).** RFCE no está documentado en ninguna vía Python (~100% del volumen del POS, E32 bajo RD$250,000), y ninguna de las 3 vías se puede intentar sin correos a proveedores o RNC+certificado | Nada — sigue exactamente igual de sin resolver que antes, solo que ya no bloquea Fase 1 | Yedin manda los correos de S0.3 (texto en `docs/08-BLUEPRINT.md` §6.1) o consigue RNC+certificado → entonces S0.9 con TrackID real. **Para de verdad en S2.7** si sigue sin resolverse ahí |
| 🔴 | **Aislamiento entre Companies es lógico, no físico** (D19) | Nada todavía | **S1.8**: la barrera + su suite de 12 escenarios en CI |
| 🟡 | **`LICENSE` dice MIT y la app tiene que ser GPLv3.** S1.1 arranca sin resolverlo — Yedin no lo mencionó al dar el OK para Fase 1 | Nada — no hay código de la app todavía | Cambiarlo **antes de empujar código real a `korvexcio/`**. Decisión de Yedin, sigue pendiente |
| 🟡 | **POSNext y URY se instalaron desde `develop`**, que es mutable. Ninguno publica `version-16` | El SHA probado quedó escrito en `docs/13-VERSION-FRAPPE.md` | **S1.2**: fijar SHA o mirrors de Korvex |
| 🟡 | **D16 (POS) recomendado hacia POSNext por S0.8, sin confirmar** | Evidencia de código en `docs/10-SPIKE-POS.md` | OK explícito de Yedin, o prueba en vivo en S4.1 |
| 🟡 | **7.154 GB de caché de build reclamable en el nodo** | La alarma de disco avisa al 80% | Mantenimiento autorizado con `docker builder prune` |
| 🟡 | **La mini PC viaja con Yedin** | Ninguna mitigación técnica | Decisión de Yedin antes del go-live: deja de viajar · VPS · contingencia por OFV |
| 🟡 | **Un `Contador` con permiso de lectura pero sin `User Permission` de Company puede quedar sin filtro efectivo** — hallazgo MEDIO de la auditoría de S2.1 | El aprovisionamiento actual asigna Company y el escenario 9 prueba un Contador acotado | En el slice de aprovisionamiento de usuarios, impedir `Contador`/`Dueño` sin Company y agregar un test default-deny que espere cero `DGII Settings` |
| ⚪ | **Falta probar creación/escritura cross-Company de `DGII Settings` con `Dueño`** — hallazgo BAJO de la auditoría de S2.1 | `freeze_company()` cubre el DocType y el escenario 9 ya prueba lectura y mutación de Company con Contador | Añadir el caso cuando vuelva a ampliarse la suite de aislamiento |
| ⚪ | **Fixtures de S2.1 reutilizan usuarios/registros persistentes sin normalizar todos sus valores** | Los helpers garantizan existencia y la suite actual pasó limpia | Normalizar roles/valores cuando el registro ya existe, o crear fixtures aislados con limpieza explícita |
| ⚪ | **Los resolvers futuros no deben asumir `DGII Settings.name == company`** — un rename de Company puede volver obsoleto el nombre físico | `company` también es único y es la fuente de verdad | Buscar por el campo `company` y añadir esa regresión cuando se implemente el resolver fiscal |
| ⚪ | Warnings de Vite en el build de POSNext/URY | No producen fallo observable | Se revisan solo si rompen algo observable |
| 🟡 | **`ecf_32.xml`/`rfce.xml` (S2.8) NO están validados contra el XSD oficial de la DGII** — solo confirmado bien-formado y fiel a la estructura de una referencia MIT en producción (laravel-dgii), no al schema real | `validate_well_formed()` confirma que parsea; la fidelidad de tags/orden viene de una implementación real, no inventada | Bajar el XSD oficial del portal de la DGII y re-validar en cuanto S0.9/S2.7 se desbloqueen (D20) — antes de S5.4 |
| ⚪ | **6 hallazgos de `ruff` en código de S2.2/S1.8** (`DTZ011` ×5 en `dgii_digital_certificate.py`/su test, `BLE001` ×1 en `test_isolation.py:231`) — aparecieron entre S2.5 y S2.6 sin cambiar ese código, probablemente por `ruff:latest` sin fijar por SHA | Ninguna — el código funciona, es solo lint | Fijar la imagen de ruff por digest y limpiar los 6 hallazgos en un slice de mantenimiento, no mezclado con fiscal |
