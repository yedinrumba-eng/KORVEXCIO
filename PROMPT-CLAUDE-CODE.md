# Prompt para arrancar una sesión nueva

> Copiar y pegar tal cual al abrir **Claude Code** o **Codex** en esta carpeta.
> Actualizado el 2026-09-01 al cerrar **S4.5 (turno de caja)**. Fase 4 en
> curso: S4.1 y S4.5 cerrados (backend). S4.2/S4.3 esperan el fork de
> POSNext (Yedin lo está haciendo a mano en github.com/DeeloaSociety/posnext
> -> yedinrumba-eng/posnext). S4.4/S4.6 necesitan hardware físico / el local
> real del cliente — no se pueden cerrar en remoto, punto.
>
> **Carril B ya está autorizado y en uso** (Yedin, 2026-09-01): ver §5 para
> el prompt de Codex trabajando en paralelo sobre Fase 5/6 sin tocar nada
> de lo que el carril A (Fase 2/4, `korvexcio/ecf/**` y el POS de
> `korvexcio/retail/**`) está tocando ahora mismo.
>
> **Este archivo se actualiza al cerrar cada slice.** Si el prompt de abajo
> ya no coincide con `PROGRESO.md`, gana `PROGRESO.md` — y hay que corregir
> este archivo.

---

## 1. El prompt — sesión de EDITOR (lo normal)

```
Vas de EDITOR en KORVEXCIO (C:\PROYECTOS\KORVEXCIO).

QUÉ ES: ERP + POS multi-tenant sobre ERPNext/Frappe v16 para retail y food en
República Dominicana. Producto de la casa KORVEX. Primer cliente: dos
negocios del mismo dueño — VAPERIA LA J Y EL JALAPEÑO (vapería) y EL SABOR
DE LAS 5 ESQUINAS (cafetería), un solo site, dos Company (D19).
Repo: https://github.com/yedinrumba-eng/KORVEXCIO.git

LEE EN ESTE ORDEN, completo, antes de proponer nada:
  1. HANDOFF.md            — dónde estamos, las trampas del nodo, qué está
                             verificado y qué no
  2. PROGRESO.md           — la bitácora y la deuda técnica abierta. La ÚLTIMA
                             entrada dice exactamente dónde quedó el trabajo
  3. docs/08-BLUEPRINT.md  — EL PLAN. Fases, microslices, la verificación de
                             cada uno, las reglas del ejecutor y la seguridad
                             por fase. Es la fuente de verdad del qué y del orden
  4. CLAUDE.md             — reglas obligatorias y nomenclatura
  5. docs/06-COMO-SE-TRABAJA.md — CÓMO se extiende ERPNext sin tocarlo

EL RELOJ: 15/11/2026, e-CF obligatorio para pequeños/micro/no clasificados
(Ley 32-23). Multa 5-50 salarios mínimos. Todo lo demás se difiere; esto no.

TU ESTADO: S2.10 está cerrado y desplegado en `bc52c49` (suite 54 integration
+ 13 unit verde). S2.7 sigue bloqueado: no inventes proveedor ni emisión de
prueba. Si el proveedor/RNC/certificado todavía no están disponibles, trabaja
solo en documentación o deuda técnica aprobada; no avances a S2.11.

ANTES DE ESCRIBIR CÓDIGO FISCAL: revisa si S0.9/S0.3 se resolvieron
(¿respondió algún proveedor? ¿hay RNC+certificado?). Si NO, sigue de todos
modos con S2.2-S2.6 (estructura, sin necesitar el proveedor real) — pero
**S2.7 (el proveedor real) para de verdad si sigue sin resolver.** No se
inventa un proveedor de prueba para simular que está cerrado.

🔴 REGLA NUEVA DE S1.8, aplica a TODO lo que escribas en `korvexcio/ecf/`:
`frappe.get_doc(doctype, name)` **NO chequea permisos de lectura**. Todo
método `@frappe.whitelist()` que lea un documento necesita
`doc.check_permission("read")` explícito, o pasar por
`frappe.client.get()`/`frappe.get_list()`. Verificado con un test real que
falló hasta que se corrigió — no es una suposición, está en "Lecciones ya
pagadas" de HANDOFF.md.

`DGII Settings` ya existe, está probado y no se rediseña. Para el nuevo
`DGII Digital Certificate`, agrégalo a `COMPANY_SCOPED_DOCTYPES` para que
`freeze_company()` lo proteja. Activa el escenario 10 que quedó diferido:
un usuario de Company A no puede leer ni descargar el `.p12` de Company B.
El test vinculante de S2.2 también debe demostrar que guardar y leer funciona
y que la clave **no sale en texto plano por la API REST**. Recuerda la lección
de S2.1: un fallo de discovery con `Ran 0 tests` NO cuenta como RED de TDD.

DESPUÉS de instalar o reinstalar cualquier app: `docker compose restart
backend queue-short queue-long scheduler websocket`. Pasó en S1.1, está en
"Lecciones ya pagadas" de HANDOFF.md.

OTRA TRAMPA YA PAGADA: el usuario MariaDB del site está limitado a
`172.18.%`, la red Docker privada de KORVEXCIO (D21). No lo vuelvas a fijar
a la IP actual de un contenedor: cambia en cada restart.

Deuda abierta que NO bloquea este slice pero sigue viva: LICENSE de la
raíz en MIT en vez de GPLv3 · D16/POS pendiente de OK explícito de Yedin ·
SHA-pin de POSNext/URY imposible sin mirror (necesita OK de Yedin para
crear el repo).

Verificación con la que se cierra:
  guardar y leer `DGII Digital Certificate` para las dos Company de prueba
  leerlo por la API REST -> `password` nunca aparece en texto plano
  usuario de Company A -> no lee ni descarga el certificado de Company B
  bench --site korvexcio.korvexdev.cc run-tests --app korvexcio -> sigue verde
  systemctl status korvex-api && curl -s http://127.0.0.1:4000/health
  df -h /

EL NODO NO ESTÁ VACÍO. korvex-node1 corre KORVIS en producción: un banco (ADAP)
y dos bots de WhatsApp EN VIVO. Lo que rompas ahí le cuesta credibilidad a Yedin
delante de quien paga. Reglas completas en:
  C:\PROYECTOS\SERVER PROJECTS\homelab\docs\ACCESO-Y-REGLAS-DEL-NODO.md

ACCESO: ssh korvex-host  (korvex@100.102.203.91, llave ~/.ssh/korvex_server).
Es la IP de TAILSCALE, no la de LAN. sudo pide contraseña salvo reiniciar
korvex-api / korvex-dashboard / korvex-ops; cualquier otro sudo lo corre Yedin
con: ssh -t korvex-host "sudo el-comando"

EL BENCH YA EXISTE. No lo vuelvas a construir. Imagen korvexcio:16, proyecto
Compose `korvexcio`, red y volúmenes propios, frontend en 127.0.0.1:8080,
MariaDB y Redis sin puertos al host. Versiones y SHA exactos en
docs/13-VERSION-FRAPPE.md. Los comandos de compose que se usaron están ahí.

REGLAS QUE NO SE ROMPEN (completas en CLAUDE.md y en el blueprint §7):
  - Un slice a la vez. No se adelantan fases.
  - Sin evidencia no existe "funciona": se pega la salida real del comando.
    Si no lo corriste, la frase es "escrito pero SIN verificar - falta correr X".
  - Lo acordado es lo que se hace. Si ves algo mejor: paras, lo dices, esperas.
  - Los upstream NO se tocan. Si te ves editando apps/erpnext/ o apps/frappe/,
    PARA. La forma correcta está en el doc 06.
  - Nunca se edita código en el servidor. Push en DEV -> git pull en el nodo.
    Un `git status` sucio bloquea el pull SIN RUIDO: verifica el SHA, no el
    exit code.
  - Nada del proyecto `korvexcio` toca los recursos de KORVIS: ni su Postgres,
    ni su Redis, ni su red, ni su compose.
  - Puertos solo en 127.0.0.1. Se verifica con `ss -tlnp`, NUNCA leyendo el YAML.
  - Secretos solo en .env (600 en el nodo). Nunca en código, git, logs ni chat.
  - ignore_permissions=True y frappe.db.sql() crudo están PROHIBIDOS en
    korvexcio/. Son los bypass del aislamiento entre Companies.
  - El POS nunca espera a la DGII para cerrar una venta.
  - Commit al cerrar cada slice verificado. Push solo cuando Yedin lo pida.

AL CERRAR EL SLICE: actualiza PROGRESO.md, HANDOFF.md y este prompt. Termina
con el bloque `=== REPORTE PARA COORDINADOR ===` exigido por AGENTS.md.

Habla claro y en español. Si algo de lo que digo no se alinea con el plan,
dímelo de frente en vez de darme la razón.
```

---

## 2. Versión corta

```
Vas de editor en KORVEXCIO (C:\PROYECTOS\KORVEXCIO). Lee HANDOFF.md, la última
entrada de PROGRESO.md y docs/08-BLUEPRINT.md antes de proponer nada.

ERP+POS multi-tenant sobre ERPNext/Frappe v16 para retail y food en RD.
Deadline duro: e-CF de la DGII obligatorio el 15/11/2026.

El bench v16, el site korvexcio.korvexdev.cc, sus dos Company reales
(VAPERIA LA J Y EL JALAPEÑO, EL SABOR DE LAS 5 ESQUINAS), el catálogo, el
backup, la app korvexcio (GPLv3, roles, custom fields) y la barrera de
aislamiento (freeze_company + 9 escenarios verdes) ya están de pie. No los
reconstruyas.

S2.10 está cerrado y desplegado en `bc52c49`; la suite pasó 54 integration +
13 unit. El siguiente paso formal es S2.7, bloqueado hasta tener proveedor
real, RNC y certificado. No avances a S2.11 ni inventes una emisión de prueba.
frappe.get_doc() no chequea permisos de lectura: usa doc.check_permission("read")
o frappe.client.get() en todo método whitelisted.

Un slice a la vez. Sin la salida real del comando, no se declara nada cerrado.
En ese nodo corre KORVIS en producción con un banco en vivo: no se toca su
Postgres, ni su Redis, ni su compose.
```

---

## 3. Si la sesión va de AUDITOR

```
Vas de AUDITOR en KORVEXCIO (C:\PROYECTOS\KORVEXCIO). No reescribes código:
devuelves hallazgos.

Lee HANDOFF.md, PROGRESO.md y docs/08-BLUEPRINT.md (§7 reglas del ejecutor,
§7.1 qué revisión toca en qué fase, §7.3 el sistema de aislamiento).

Formato: archivo:línea — SEVERIDAD: problema. Fix sugerido.
Severidades: CRÍTICO, ALTO, MEDIO, BAJO.
Cierras con una línea: APROBADO o DEVUELTO (n críticos, n altos).

Crítico y Alto bloquean y vuelven al editor. Medio y Bajo van a deuda técnica.
Máximo 3 rondas; si a la ronda 3 queda un Crítico, para y escala.
```

---

## 4. Lo que NO está decidido y no lo decide la sesión

Si el trabajo te lleva a uno de estos, **para y pregúntale a Yedin**:

| Qué | Estado |
|---|---|
| **El `LICENSE` dice MIT** y la app tiene que ser GPLv3 porque ERPNext lo es | Pendiente de decisión. Cambiarlo antes de S1.1 |
| **Proveedor de e-CF** | Lo decide el spike S0.9. D3 quedó revisada |
| **POS nativo vs POSNext** | **Confirmado POSNext** (2026-09-01, OK de Yedin). Fork en curso |
| **Qué pasa con la caja los días que la mini PC viaje** | Sin resolver. Tiene que estar decidido antes del go-live |
| **RNC del cliente: uno o dos** | Sin confirmar. Se planifica para dos (D13) |

---

## 5. El prompt — sesión de CARRIL B (Codex, en paralelo)

> Autorizado por Yedin el 2026-09-01. Frontera de archivos, no buena
> voluntad (blueprint §7.2): el carril A (Claude, esta sesión) está
> tocando `korvexcio/ecf/**`, `korvexcio/retail/pos_profile.py`,
> `korvexcio/retail/cash_shift.py`, `hooks.py`, `roles.py`,
> `isolation.py` — **el carril B NO toca esos archivos, ni ninguno
> dentro de `korvexcio/` que no sea el listado abajo.** Si necesitas un
> hook o un permiso nuevo en `hooks.py`/`roles.py`, lo pides por nota,
> no lo escribes.

```
Vas de CARRIL B (Codex) en KORVEXCIO (C:\PROYECTOS\KORVEXCIO), rama
feat/ecf, EN PARALELO con otra sesión (Claude Code) que está cerrando
Fase 4 (POS). Tu trabajo NO depende del suyo y el suyo no depende del
tuyo -- por diseño.

QUÉ ES: ERP + POS multi-tenant sobre ERPNext/Frappe v16 para retail y food
en República Dominicana. Cliente 1: VAPERIA LA J Y EL JALAPEÑO (vapería) +
EL SABOR DE LAS 5 ESQUINAS (cafetería), un site, dos Company (D19).
Repo: https://github.com/yedinrumba-eng/KORVEXCIO.git

LEE PRIMERO, completo: HANDOFF.md, PROGRESO.md (la última entrada dice
dónde quedó todo), docs/08-BLUEPRINT.md (el plan completo, Fases 5 y 6
son tu territorio), CLAUDE.md (reglas obligatorias -- en particular regla
12b: ignore_permissions=True y frappe.db.sql() crudo PROHIBIDOS).

TU FRONTERA -- toca SOLO esto:
  - docs/RUNBOOK.md              (nuevo -- S6.3)
  - docs/15-MANUAL-CAJERO.md     (nuevo -- S5.5)
  - docs/16-MANUAL-DUENO.md      (nuevo -- S5.5)
  - scripts/**                   (nuevo -- S5.1, carga de catálogo)
NO toques korvexcio/ por ningún motivo. Si algo ahí parece que necesita
cambiar para que tu trabajo tenga sentido, anótalo y pregunta -- no lo
edites.

TAREA 1 -- docs/RUNBOOK.md (S6.3): un escenario por sección, cada uno con
el comando real que se corre. Mínimo estos cinco: se cae la DGII, se cae
el internet del local (modo contingencia, S2.11), se cae el nodo, se
agota una Secuencia eNCF (S2.3, hay alerta ya escrita), y "el git pull no
aplicó porque el `git status` del nodo estaba sucio" (regla 7 del
CLAUDE.md -- el despliegue verifica el SHA, no el exit code). Formato:
qué pasó / cómo se detecta / comando exacto para resolver / cómo se
verifica que quedó resuelto.

TAREA 2 -- docs/15-MANUAL-CAJERO.md y docs/16-MANUAL-DUENO.md (S5.5):
"como si tuviera 12 años" (regla del CLAUDE.md, sección 7) -- claro, con
analogías, sin jerga. Cubre SOLO lo que ya existe y está probado:
- Cajero: cómo entra, que cae directo en su Company sin escoger nada
  (S4.1), cómo abre y cierra su turno con arqueo (S4.5) -- describe el
  FLUJO de datos (abrir con el efectivo que hay en caja, vender, cerrar
  contando lo que hay), no una pantalla específica todavía -- la pantalla
  real del POS (S4.2, POSNext) no existe aún, dilo explícito con una nota
  "se actualiza cuando el POS tenga pantalla real".
- Dueño: dashboard consolidado (S3.6), los 4 reportes (S3.5: stock
  muerto, margen por categoría, rotación, venta del día), cómo crea un
  cajero con rol acotado (S1.7), panel de e-CF pendientes (S2.14).
NO inventes pantallas o botones que no existen. Si no estás seguro de que
algo existe, revisa el código antes de describirlo (grep en
korvexcio/retail/ y korvexcio/ecf/), no asumas.

TAREA 3 -- scripts/ (S5.1): un script Python que lea un CSV con columnas
mínimas (item_code, item_name, item_group, rate, uom) y cree Items reales
vía la API de Frappe (frappe.client.insert o REST), CON reintentos con
backoff 2/4/8/16/32s máx 5 intentos para cualquier llamada de red (regla
5 del CLAUDE.md, S2.10 tiene el patrón exacto en korvexcio/ecf/tasks.py
-- cópialo, no lo reinventes). No necesita datos reales todavía -- el
catálogo real llega después del cliente. Este slice es la ESTRUCTURA:
correr con un CSV de 5 filas de prueba y confirmar que crea 5 Items.

CIERRA CADA TAREA CON:
- Verificación real pegada (R1) -- no "debería funcionar".
- `PROGRESO.md` actualizado con una entrada nueva (no reescribas las
  existentes).
- Commit por tarea cerrada, mensaje en inglés, formato convencional.
  NO hagas push -- eso lo decide Yedin.

Si algo del blueprint no está claro o parece chocar con lo que la otra
sesión está tocando en korvexcio/, PARA y pregunta. No lo improvises.
```
