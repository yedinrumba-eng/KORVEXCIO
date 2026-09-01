# Prompt para arrancar una sesión nueva

> Copiar y pegar tal cual al abrir **Claude Code** o **Codex** en esta carpeta.
> Actualizado el 2026-08-31 al cerrar **S2.1 (`DGII Settings`)**. El próximo
> slice es **S2.2 (`DGII Digital Certificate`)**; S2.7 sigue siendo donde
> S0.9/S0.3 paran de verdad si continúan sin resolver.
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

TU SLICE: S2.2 — DocType `DGII Digital Certificate`: `certificate`
(**Attach**), `password` (**Password**, nunca `Data`), `company` (Link) y
`valid_until`, con aviso de vencimiento en `validate()`. NADA MÁS — no
adelantes S2.3 (Secuencia eNCF).

EL CHECKOUT YA TIENE TRABAJO NO COMMITTEADO DE S2.2 dejado por la sesión
anterior: `korvexcio/isolation.py` modificado y
`korvexcio/ecf/doctype/dgii_digital_certificate/` sin trackear. Esos cambios
son de S2.2: revísalos y continúa desde ahí. NO hagas reset, stash, clean ni
cambio de rama que los borre. S2.1 está empujado en `origin/feat/ecf`.

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

Fase 0, Fase 1 y S2.1 cerradas. Tu slice es S2.2: DGII Digital Certificate
con certificate=Attach, password=Password, company y valid_until + aviso en
validate(). El checkout ya contiene trabajo no committeado de S2.2: no lo
borres. Prueba que la clave no sale en texto plano por REST y que Company A
no puede leer/descargar el .p12 de B. frappe.get_doc() no chequea permisos
de lectura: usa doc.check_permission("read") o frappe.client.get() en todo
método whitelisted.

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
| **Carril B en paralelo** (blueprint §7.2) — Fase 3 en otra sesión mientras el carril A hace la Fase 2 | Propuesto, **no aplicado**. Necesita OK explícito |
| **Proveedor de e-CF** | Lo decide el spike S0.9. D3 quedó revisada |
| **POS nativo vs POSNext** | S0.8 ya tiene evidencia y recomienda **POSNext** (revierte D16). Falta el OK explícito de Yedin para fijarlo |
| **Qué pasa con la caja los días que la mini PC viaje** | Sin resolver. Tiene que estar decidido antes del go-live |
| **RNC del cliente: uno o dos** | Sin confirmar. Se planifica para dos (D13) |
