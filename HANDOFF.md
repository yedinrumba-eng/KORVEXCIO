# HANDOFF — KORVEXCIO (cliente 1: VAPELAND)

> **Actualización 2026-08-31 — auditoría de continuación.** El nodo está en
> S2.9 (`bb9d006`). S2.10 existe solo como cambios sin commit en DEV y queda
> pausado. S2.9 fue devuelto por dos bloqueantes: el RNC se leía de la fuente
> equivocada (`tax_id` en vez de `Customer.rnc`) y la creación de ECF exigía
> permisos directos que un Cajero no tiene. Se corrigieron ambos en DEV, pero
> falta desplegar y correr la suite en el nodo. S2.7 sigue siendo el próximo
> gate formal: proveedor real, RNC y certificado. No avanzar a S2.11.

> **Lo primero que se lee al retomar.** Escrito el 2026-08-31 en sesión de
> descubrimiento (Cowork). Estado: **🟢 Fase 2 en curso: S2.1 COMPLETADO y
> auditado (code-review + security-review, APROBADO, cero críticos/altos).**
> Siguiente: S2.2. La app `korvexcio` existe de verdad: GPLv3,
> módulos `ECF`/`Retail`, custom fields en `Customer`, roles por Company
> probados con un usuario real, y **la barrera de aislamiento de D19
> funcionando y verificada** (`bench run-tests` verde, dos corridas).
>
> **S0.9 (el gate fiscal) y S0.3 (correos) siguen en deuda técnica** —
> decisión de Yedin del 31/08. Ya no bloquean código, pero **paran de
> verdad en S2.7** (elegir proveedor real) si para entonces siguen sin
> resolver.
>
> **Nombres reales (31/08, confirmados por Yedin):** la vapería es
> **VAPERIA LA J Y EL JALAPEÑO** (abbr `VLJ`), la cafetería es
> **EL SABOR DE LAS 5 ESQUINAS** (abbr `ESE`). El codename interno del
> cliente en la cabecera de este repo sigue siendo "VAPELAND" — es shorthand
> del proyecto, no el nombre de ninguna `Company`.
>
> **S0.7b (site `demo.korvexdev.cc`) queda FUERA** — decisión explícita de
> Yedin. **S0.8 recomienda POSNext**, revirtiendo el sesgo hacia el nativo
> de D16 — con evidencia de código, pendiente OK explícito de Yedin
> (`docs/10-SPIKE-POS.md`).
>
> 🟡 **`LICENSE` (el archivo de la raíz del repo) sigue diciendo MIT** y
> tiene que ser GPLv3 — sin resolver. El `hooks.py` de la app `korvexcio`
> ya quedó en GPLv3; el archivo `LICENSE` de la raíz es aparte y sigue en
> deuda. **Cámbialo antes de empujar código público.**
>
> **Fase 1, resumen de lo que existe hoy:** app `korvexcio` instalada ·
> `apps.json` con el repo propio (SHA de POSNext/URY sigue sin fijar —
> imposible sin un mirror, confirmado en el código de `bench`) · 6
> workflows de CI + regla propia de Semgrep, probada de verdad · `custom
> fields` en Customer · roles y User Permissions por Company · **la
> barrera de aislamiento** (`korvexcio/isolation.py`, `freeze_company`) con
> 9 de 12 escenarios reales verificados y 3 diferidos a Fase 2 con motivo
> explícito. Detalle completo, slice por slice, en `PROGRESO.md`.
>
> Próximo paso: **S2.2** — `DGII Digital Certificate` (bloqueado en la
> práctica sin certificado real, S0.9/S0.3). Fase 2 no puede cerrarse sin
> resolver S0.9/S2.7 primero.
> Evidencia de versión y operación: `docs/13-VERSION-FRAPPE.md`.
>
> ### Los tres documentos que se leen, en este orden
>
> 1. **`docs/08-BLUEPRINT.md`** — el plan maestro: fases, microslices, la
>    verificación de cada uno, las reglas del ejecutor y la seguridad por fase.
>    **Es la fuente de verdad del qué y del orden.**
> 2. **`PROGRESO.md`** — la bitácora: qué se cerró, con qué comando se verificó, y
>    **exactamente dónde quedó el trabajo**. Al final lleva la deuda técnica abierta.
> 3. **Este documento** — el porqué del proyecto y las trampas del terreno.
>
> El prompt listo para pegar en una sesión nueva (Claude Code o Codex) está en
> **`PROMPT-CLAUDE-CODE.md`**.

---

## Estado técnico al retomar — Fase 2 en curso, S2.1 completado

- Imagen en `korvex-node1`: `korvexcio:16`, sitio `korvexcio.korvexdev.cc`,
  `frappe 16.32.0` + `erpnext 16.33.0` + **`korvexcio 0.0.1` (rama
  `feat/ecf`)**. Nueve servicios de runtime arriba, MariaDB healthy. D21
  cambió el host del usuario DB de una IP efímera a `172.18.%`, limitado a
  la red Docker privada de KORVEXCIO; MariaDB sigue sin puerto al host.
- **Companies:** `VAPERIA LA J Y EL JALAPEÑO` (`VLJ`) y
  `EL SABOR DE LAS 5 ESQUINAS` (`ESE`), con `tax_id` placeholder (RNC
  pendiente, D13), almacenes, cost centers y Chart of Accounts completos.
  Más dos Companies de prueba (`_Test Company KORVEXCIO A/B`) para la
  suite automatizada — no tocan datos reales.
- **Catálogo:** 24 Items (S0.11). **Backup:** probado en vivo, falta el
  `sudo systemctl enable` de Yedin (S0.10).
- **La app `korvexcio` — qué existe hoy, todo con evidencia real en
  `PROGRESO.md`:**
  - `hooks.py` — GPLv3, módulos `ECF`/`Retail`, `after_migrate` (custom
    fields + roles), `doc_events["*"]["validate"]` (la barrera).
  - `install.py` — `before_tests()`, dos Companies de prueba.
  - `custom_fields.py` + `custom/customer.json` — `Customer.rnc` y
    `Customer.tipo_identificacion`, patrón KSA.
  - `roles.py` — 4 Roles (`Cajero VLJ`, `Cajero ESE`, `Dueño`, `Contador`),
    Dueño sin System Manager pero puede crear cajeros con rol acotado.
  - **`isolation.py`** — `freeze_company()`, el `WITH CHECK` de D19.
    Aplica a `Warehouse`, `Cost Center`, `Sales Invoice`, `Sales Order`,
    `Delivery Note`, `Payment Entry`, `Item Price`, `DGII Settings`; los
    doctypes propios de `korvexcio` se agregan al crearse.
  - `ecf/doctype/dgii_settings/` — S2.1: una configuración por Company,
    timeouts validados, sin certificados, providers funcionales ni secretos.
  - `tests/test_isolation.py` — 9 escenarios reales verdes; quedan S2.2/S2.7
    diferidos con `skipTest` explícito. La suite completa dio 13 tests, OK
    (skipped=1) después del migrate y restart de S2.1.
- **🔴 Hallazgo de S1.8 que aplica a TODO lo que se escriba en Fase 2:**
  `frappe.get_doc(doctype, name)` **no chequea permisos de lectura**.
  Lo que sí los chequea, porque es lo que responde de verdad
  `/api/resource/<doctype>/<name>`, es `frappe.client.get()`. **Todo
  método `@frappe.whitelist()` de `korvexcio/ecf` que lea un documento
  tiene que usar `doc.check_permission("read")` explícito, o pasar por
  `frappe.client.get()`/`frappe.get_list()` — nunca fiarse de
  `get_doc()` a secas.**
- 🟡 **S1.2, `apps.json`:** tiene la entrada de `korvexcio`, pero **fijar
  SHA de POSNext/URY es técnicamente imposible sin un mirror** — confirmado
  leyendo el código de `bench` (`git clone --branch <X> --depth 1` no
  acepta un SHA arbitrario). Mirror propio = crear un repo nuevo y
  pushear ahí, acción externa que necesita el OK de Yedin.
- 🟡 **`MASTER_ENCRYPTION_KEY`** generado en el nodo (S1.6), 600, nunca
  visto por nadie fuera del servidor. Los secretos de e-CF (.p12, tokens)
  siguen sin existir — bloqueados en S0.9/S2.7.
- Password de Administrator del site real: generado random en el nodo
  (`/home/korvex/frappe_docker-korvexcio-s05/.korvexcio-admin-pw`, 600).
  **Nunca pasó por el chat ni por este repo.**
- **S0.8 (POS):** recomienda **POSNext** (revierte D16, evidencia de
  código en `docs/10-SPIKE-POS.md`). Pendiente OK de Yedin + prueba en
  vivo (S4.1).
- 🔴 **S0.9/S0.3 (fiscal):** deuda técnica por decisión de Yedin (D20),
  ya no bloquea código. **Para de verdad en S2.7** si sigue sin resolver.
- **D21 (operación):** el usuario MariaDB del site acepta conexiones desde
  `172.18.%`, la subred privada de KORVEXCIO. Yedin lo autorizó después de
  que el restart moviera `backend` de `.5` a `.9` y rompiera el grant.
- Deuda menor: build cache reclamable 7.154 GB · SHA-pin de GitHub Actions
  (`@v6` en vez de SHA fijo, detectado por `/security-review`, no urgente
  porque nada ha corrido todavía sin push).
- **Push de S2.1 hecho a `origin/feat/ecf` en `e1b8edc`;** el nodo ejecutó
  ese SHA durante la verificación. `origin/main` sigue en `74048e4` porque
  `docs/08-BLUEPRINT.md` §7.2 ordena mergear a `main` solo en gates de fase.

---

## En una línea

**KORVEXCIO** — ERP + POS multi-tenant sobre **ERPNext/Frappe** para negocios
de retail y food en República Dominicana, vendible como producto de la casa
**KORVEX**. Primer cliente: **VAPELAND**, tienda de vapes/hookah/tabaco con
cafetería adjunta.

**La familia:** KORVEX (la casa) · **KORVEXCIO** (este producto, de *comerCIO*)
· **KORVIS** (*the AI Assistant by Korvex*, el bot de WhatsApp) · VAPELAND y
ADAP son **clientes**, no productos.

---

## Las 4 decisiones ya tomadas (2026-08-31, Yedin)

| # | Decisión | Qué se descartó |
|---|---|---|
| 1 | **Base: ERPNext / Frappe** | Construir sobre el stack de KORVIS (Node/TS/Postgres) · Odoo CE · híbrido |
| 2 | **e-CF vía proveedor certificado por API** | Integración directa a DGII · diferir el fiscal |
| 3 | **MVP = POS + inventario + e-CF, nada más** | ⚠️ *Marcado por Yedin: revisar con el cliente antes de cerrar el alcance* |
| 4 | **Posicionamiento: retail + food genérico con módulos** | Vertical vape-only · "POS legal 15/11" · cliente único |

> ⚠️ **Estas cuatro son de la mañana del 31/08 y dos ya se movieron.** La numeración
> canónica de decisiones (D1–D19) vive en `TECH_STACK.md` y en `docs/08-BLUEPRINT.md`
> §3. Lo que cambió:
>
> - **D4 ("MVP sin cafetería") está DEROGADA por D12.** Vapería y cafetería entran
>   **juntas en la v1** — son dos negocios del mismo dueño y arrancan a la vez.
> - **D3 ("proveedor certificado vía `ecf-dgii`") está REVISADA.** Verificado:
>   `ecf-dgii` solo documenta E31. La interfaz `FiscalProvider` se mantiene y el
>   proveedor lo decide el spike S0.9.
> - **D6 ("un site por cliente") está REVISADA por D19:** un site por **cliente**,
>   una `Company` de ERPNext por **negocio**. Ver la sección de arquitectura.
> - **D2 ("v15, no v16") está CERRADA en v16** por S0.5, con evidencia.

---

## ⛔ Lo que tienes que saber ANTES de escribir una línea de código

### 1. El reloj: **76 días**

**15 de noviembre de 2026** — fecha en que la facturación electrónica (e-CF)
se vuelve obligatoria para contribuyentes **pequeños, micro y no clasificados**
en RD. Es exactamente la categoría de este cliente.

Los grandes locales y medianos entran antes: los comprobantes **no electrónicos
tipo "B" dejan de ser válidos el 31 de octubre de 2026**.

Multa por incumplir (Ley 32-23): **5 a 50 salarios mínimos**.

👉 El e-CF **no es una fase 3**. Es el camino crítico. Todo lo demás se puede
diferir; esto no.

### 2. Elegir ERPNext tiene tres facturas. Págalas con los ojos abiertos

**a) El stack queda partido en dos.**
ERPNext es **Python / Frappe / MariaDB / Redis**. KORVIS —tu asistente de IA por
WhatsApp, que ya funciona en producción— es **Node 20 / TypeScript / Express /
Drizzle / PostgreSQL+pgvector / Next.js 15**. No comparten nada: ni ORM, ni
auth, ni design system (`packages/ui` "clear glass" no existe en Frappe), ni
modelo de tenant.

El asistente de WhatsApp **no se reusa: se integra por API**. Son dos
plataformas que mantienes en paralelo, en el mismo mini-PC. Eso es real y no
se arregla después.

**b) GPLv3 + marca registrada.**
- Puedes hostearlo y cobrarlo. GPLv3 lo permite explícitamente.
- **Toda modificación que distribuyas queda GPLv3.** Si un cliente pide el
  código de tu app fiscal, se lo das.
- **No puedes usar "ERPNext" ni "Frappe" en el nombre del producto, de la
  empresa, ni en el dominio.** "KORVEXCIO" ✅ · "KorvexNext" ✅ ·
  "ERPNext by Korvex" ❌ · `erpnext.korvexdev.cc` ❌
- Hay que mantener visible el aviso `© Frappe Technologies Pvt. Ltd.` y la
  licencia. White-label sí, pero con atribución.

**c) El e-CF de RD no existe en Frappe. Lo escribes tú.**
Lo único que hay es [`LewisMojica/dgii-compliance`](https://github.com/LewisMojica/dgii-compliance):
GPL-3.0, **3 estrellas, 0 forks, 84 commits, sin releases**, y solo maneja
**NCF tradicional** (secuencias, asignación, reportes DGII). **No hace e-CF.**

No es basura — el manejo de secuencias NCF sirve de punto de partida. Pero
tratarlo como "la solución fiscal ya resuelta" sería mentirte.

### 3. La ventaja real que sí compraste con ERPNext

Frappe es **Python**. Y el ecosistema fiscal dominicano en Python existe:

- **[`ecf-dgii`](https://pypi.org/project/ecf-dgii/)** — PyPI, **licencia MIT**
  ✅ verificado, v1.0.0 (7 mayo 2026), de Smart Software Development SRL. SDK
  del proveedor certificado **ECF SSD**: mandas JSON, ellos firman con tu
  certificado y transmiten a la DGII. Ambientes `test` / `cert` / `prod`
  ✅ verificado. Requiere **cuenta y API key (JWT) de ECF SSD**.
  ⚠️ **PERO: la página oficial de PyPI NO documenta E32 ni RFCE** — y E32 +
  RFCE son el 95% de las ventas de este POS. Una fuente secundaria los
  menciona; la primaria no lo confirma. **Esto es exactamente lo que decide el
  spike de 2 días.**
- **[`rob-erply/dgii_facturacion_electronica`](https://github.com/rob-erply/dgii_facturacion_electronica)** —
  módulo de Odoo 18, licencia **OPL-1 (propietaria — NO copiar código)**, pero
  sus generadores XML y validadores XSD son `lxml`/`jinja2` puro. **Sirve como
  referencia de diseño, no como fuente de la que copiar.**

### 4. El cliente todavía no está registrado

No confirmó RNC ni registro mercantil. Sin **RNC activo + certificado digital**
no hay e-CF posible. El certificado tarda **3–10 días hábiles** y cuesta
**US$30–70/año** (Avansi, Cámara de Comercio de Santo Domingo, y otras 5
entidades autorizadas por INDOTEL).

👉 **Esto no bloquea el desarrollo, pero sí bloquea la certificación como
emisor y las pruebas contra el ambiente real de DGII.** Empújalo esta semana.

### 5. Golpe al negocio del cliente: la Ley 30-26

Promulgada el **19 de junio de 2026**: **ISC ad-valorem del 55% sobre el precio
de venta al detalle** de cigarrillos electrónicos, dispositivos de vaporización
y líquidos con o sin nicotina.

El ISC en RD lo declaran **fabricantes, productores e importadores** — no el
detallista. Es decir: probablemente le llega **dentro del costo**, no como un
impuesto que él cobra en caja. **Pero eso hay que confirmarlo con su contador
antes de modelar el motor de impuestos.** No lo asumas.

El tabaco tradicional va por otra vía: **20% del PVP + monto específico por
cajetilla** (jul–sep 2026: RD$64.65 la cajetilla de 20, RD$32.33 la de 10).

---

## La arquitectura decidida

```
                    ┌─────────────────────────────────────┐
                    │  korvex-node1 (mini PC, homelab)    │
                    │  14 GB RAM · 84 GB libres           │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
┌───────▼────────────────────────┐          ┌──────────────────▼──────────────┐
│  KORVEXCIO (nuevo)     │          │  KORVIS · AI Assistant by Korvex  │
│  ERPNext v15 + Frappe          │   API    │  (existente, en producción)     │
│  MariaDB · Redis · bench       │◄────────►│  Node/TS · Postgres · Next.js   │
│                                │  REST    │                                 │
│  Apps:                         │          │  El asistente de WhatsApp NO    │
│   · erpnext                    │          │  vive dentro de ERPNext.        │
│   · posnext / POS Awesome      │          │  Se integra por API.            │
│   · korvex_ecf   ◄── ESCRIBES  │          └─────────────────────────────────┘
│   · korvex_retail ◄── ESCRIBES │
│   · frappe/crm (opcional)      │          Cloudflare Tunnel
│   · ury (si entra cafetería)   │          *.korvexdev.cc
└────────────────────────────────┘
```

**Multi-tenancy (D19 — actualizado 31/08):** DNS-based multitenancy de Frappe
(`bench config dns_multitenant on`), con **dos capas**:

| Capa | Entre quién | Mecanismo | Fuerza |
|---|---|---|---|
| **1** | Entre **CLIENTES** | **Un site = una base de datos MariaDB** | Aislamiento **físico**. Innegociable: cliente 2 = site propio |
| **2** | Entre **NEGOCIOS del mismo cliente** | **Una `Company` de ERPNext por negocio** + User Permission | Aislamiento **lógico**. Hay que blindarlo (S1.8) |

Los sites de este cliente: **`korvexcio.korvexdev.cc`** (Companies
**VAPERIA LA J Y EL JALAPEÑO** y **EL SABOR DE LAS 5 ESQUINAS**) y
**`demo.korvexdev.cc`** (staging, y la prueba de que el modelo por cliente
funciona sin necesitar un cliente real todavía).

**Por qué una sola URL:** el login decide qué ves. El cajero de la vapería entra a la
vapería, el de la cafetería a la cafetería, y **el dueño ve las dos con un dashboard
consolidado** y administra sus propios usuarios. Eso ningún modelo de sites separados
lo da sin escribir un agregador entre bases de datos.

🔴 **Lo que cuesta, dicho claro:** la capa 2 cambia el aislamiento de físico a lógico.
En ERPNext eso no es teórico — PR frappe/erpnext#44695 (User Permission ignorada en
los estados financieros, arreglado en 14.78.3) e issue frappe/erpnext#43652 (*admin de
Company A ve los usuarios de Company B*, **cerrado como `not planned`**). Por eso
existe **S1.8**: `permission_query_conditions` + `has_permission` + `company`
congelada, con una suite de **12 escenarios contra la API**, en CI en cada push. Y por
eso `ignore_permissions=True` y `frappe.db.sql()` crudo quedan **prohibidos** en
`korvexcio/`. Detalle en `docs/08-BLUEPRINT.md` §5.2 y §7.3.

⚠️ **Realidad del hardware:** ERPNext pide **4 GB RAM mínimo** por instalación
productiva (5–15 usuarios) y **50–100 GB de disco NVMe**. El nodo tiene 14 GB y
84 GB libres, **y ya corre KORVIS** (Postgres + Redis + 3 apps Next). MariaDB
solo pide 1–3 GB. Un bench con 2–3 sites cabe; **10 tenants no caben.** El
`ROADMAP.md` de KORVEX-OPS ya dice que el techo del nodo 1 es el disco.

---

## Alcance del MVP (decisión #3 — ⚠️ MARCADA PARA REVISAR CON EL CLIENTE)

**Dentro:**
1. POS de retail: venta, cobro, múltiples métodos de pago, turno de caja
2. Escáner de código de barras
3. Inventario: variantes (sabor / nivel de nicotina), lotes y vencimiento de
   e-liquid, multi-almacén (tienda / bodega)
4. e-CF: E32 (consumo) + E31 (crédito fiscal) + RFCE, vía proveedor certificado
5. Impresión de recibo térmico con QR del e-CF

**Fuera del MVP, explícitamente:**
- CRM / panel de leads
- Asistente de IA por WhatsApp
- Módulo de cafetería (mesas, KDS, comandas)
- Portal del cliente / e-commerce
- Fidelización, cupones, gift cards

> ⚠️ **Yedin marcó esto para revisión.** El cliente pidió cafetería y asistente
> de IA desde el principio. Sacarlos del MVP es una decisión técnica correcta,
> pero **es una conversación que hay que tener con él, no un hecho consumado.**
> Ver `docs/05-PREGUNTAS-CLIENTE.md`.

---

## Dónde estamos y qué sigue

> Reemplaza al viejo "Lo primero que se hace en Claude Code". El orden completo está
> en `docs/08-BLUEPRINT.md` §6; el estado con evidencia, en `PROGRESO.md`.

### Cerrado

| Slice | Qué |
|---|---|
| **Paso 1 de Fase 0** ✅ | Los 4 repos ⭐ verificados. Ver la tabla de confianza al final |
| **S0.1** ✅ | Repo con remote, `.gitignore`, `.env.example`, docs commiteados (`80e7693`) |
| **S0.1b** ✅ | Secure-Vibe modo A + `pre-commit` con **gitleaks** (`9f6ad20`). Un commit con una clave falsa fue rechazado |
| **S0.2** ✅ | Acceso al nodo por Tailscale arreglado |
| **S0.4** ✅ | Checklist previo del nodo, todo verde |
| **S0.5** ✅ | **Bench v16 de pie en `korvex-node1`. D2 cerrada.** Implementado, probado, revisado en seguimiento (dos correcciones documentales aplicadas) y commiteado |
| **S0.6** ✅ | **Site `korvexcio.korvexdev.cc` con ERPNext instalado.** `bench new-site` lo corrió Yedin (el clasificador bloqueó a Claude); `ping` responde `pong`, `list-apps` lista `frappe`+`erpnext`, KORVIS intacto |
| **S0.7** ✅ | Las dos `Company` reales — **VAPERIA LA J Y EL JALAPEÑO** (`VLJ`) y **EL SABOR DE LAS 5 ESQUINAS** (`ESE`) — con `tax_id`, almacenes y cost centers propios. Reparado un hueco de fixtures de ERPNext en el camino (ver deuda) |
| **S0.10** ✅ | Script de backup+retención probado en vivo (905.4 KiB). Falta solo el `sudo systemctl enable` de Yedin |
| **S0.11** ✅ | Catálogo representativo: 24 Items, template con 9 variantes, item_defaults por Company |
| **S0.8** 🟡 | Matriz de 8 criterios con evidencia de código; recomienda POSNext. Falta prueba en vivo (se hace en S4.1) y OK de Yedin |
| ~~**S0.7b**~~ | **Descartada por Yedin** ("perder el tiempo") — no bloqueaba nada, comando queda listo en `PROGRESO.md` por si algún día hace falta |
| **S0.12 (D20)** ✅ | Fase 0 cerrada por decisión explícita de Yedin: **S0.9/S0.3 bajan a deuda técnica**, no bloquean más. `data/korvex.json` en "activo" |
| **S1.1** ✅ | App `korvexcio` creada — GPLv3, módulos `ECF`/`Retail`, instalada en el site |
| **S1.2** 🟡 | `apps.json` con el repo propio. SHA de POSNext/URY **imposible de fijar sin mirror** (confirmado en el código de `bench`) |
| **S1.3** ✅ | 6 workflows de CI + regla propia de Semgrep, probada de verdad contra un fixture |
| **S1.4** ✅ | `before_tests` — dos Companies de prueba, idempotente |
| **S1.5** ✅ | `Customer.rnc` + `Customer.tipo_identificacion`, verificado con `bench migrate` real |
| **S1.6** 🟡 | `MASTER_ENCRYPTION_KEY` generado · `/security-review` sin hallazgos. Secretos de e-CF siguen sin existir |
| **S1.7** ✅ | Roles + User Permissions por Company, probado como el usuario real |
| **S1.8** ✅ | **La barrera de aislamiento** (`freeze_company`) + 8/12 escenarios reales verdes, 4 diferidos a Fase 2 |
| **S1.9** N/A | Carril B condicional, no aprobado — correctamente cerrado como "no aplica" |
| ~~**S0.7b**~~ | **Descartada por Yedin** ("perder el tiempo") |

**Fase 1 CERRADA el 31/08/2026.** Detalle completo, comando por comando, en
`PROGRESO.md`.

### Lo que sigue — Fase 2, el módulo `ecf`

| # | Slice | Qué |
|---|---|---|
| 1 | **S2.1** ✅ | `DGII Settings` — código, migrate, suite y auditorías completados |
| 2 | **S2.2** | `DGII Digital Certificate` — `.p12` como Attach, password como Password (nunca Data) |
| 3 | **S2.3 → S2.6** | Secuencia eNCF, DocType `ECF`, `ECF Integration Log`, interfaz `providers/base.py` |
| 4 | **S2.7** 🔴 | El proveedor real. **Aquí es donde S0.9/S0.3 paran de verdad** si siguen sin resolver |

**🔴 Deuda que sigue abierta, sin resolver — no bloquea Fase 2, pero para
de verdad en S2.7:**
- **S0.9/S0.3** (fiscal) — necesita correos de Yedin o RNC+certificado.
- **LICENSE de la raíz** — MIT, tiene que ser GPLv3. Decisión de Yedin,
  antes de que haya código público que se distribuya.
- **D16/POS** — recomienda POSNext, falta el OK explícito de Yedin.
- **SHA-pin de POSNext/URY** — imposible sin mirror propio (acción externa,
  necesita OK de Yedin para crear el repo y pushear).

### Reglas del nodo que aplican a cada uno de esos slices

`korvex-node1` **no está vacío**: corre KORVIS en producción con un banco (ADAP) y dos
bots de WhatsApp en vivo. Detalle en
`C:\PROYECTOS\SERVER PROJECTS\homelab\docs\ACCESO-Y-REGLAS-DEL-NODO.md`.

1. **Nunca se edita código en el servidor.** Push en DEV → `git pull` en el nodo. Un
   `git status` sucio **bloquea el pull sin ruido**: verifica el **SHA**, no el exit code.
2. **Proyecto Compose y red propios** (`name: korvexcio`). No se reusa el Postgres ni
   el Redis de KORVIS.
3. **`mem_limit` por servicio**, tope ~6 GiB para toda la pila. Hoy suma 5,504 MiB.
4. **Puertos solo en `127.0.0.1`.** Se entra por Tailscale. Se verifica con
   `ss -tlnp`, **nunca leyendo el YAML**.
5. **Nada detrás del túnel público** hasta que sea real. El site se llama
   `korvexcio.korvexdev.cc` por la multi-tenancy DNS de Frappe, **no porque esté
   publicado**: se llega con `curl -H "Host: ..." http://127.0.0.1:8080`.
6. **Al cerrar cualquier slice que toque el nodo:** `systemctl status korvex-api` y
   `curl -s http://127.0.0.1:4000/health` — **KORVIS tiene que seguir sano.**
7. `sudo` pide contraseña salvo reiniciar los tres servicios de KORVIS. Cualquier otro
   `sudo` lo corre Yedin con `ssh -t korvex-host "sudo ..."`.

### Dos cosas que necesitan decisión de Yedin

1. 🟡 **`LICENSE` dice MIT, y la app tiene que ser GPLv3** porque ERPNext lo es.
   Cambiarlo **antes** de que exista código de la app (S1.1).
2. 🟡 **Carril B en paralelo** (`docs/08-BLUEPRINT.md` §7.2): Fase 3 + hardware +
   manuales en otra sesión (Codex) mientras el carril A hace la Fase 2. Gana ~1 semana
   de colchón. **Propuesto, no aplicado — necesita OK explícito.**

### Y lo que no depende de código

- **S0.3** — los correos a **Alanube** y **ECF SSD**. Texto listo para pegar en
  `docs/08-BLUEPRINT.md` §6.1. Bloquea el spike fiscal S0.9.
- **RNC del cliente** y **certificado digital** (3–10 días hábiles **por cada RNC**).

**Regla del `CONVENCIONES.md` que ya se cumplió:** el repo se creó **antes** de
escribir código, con remote desde el primer commit.

---

## Lecciones ya pagadas

Cada una costó tiempo real en esta sesión. Se listan para no volver a
pagarlas — el detalle completo con comandos está en la entrada de
`PROGRESO.md` del slice donde pasó.

| Qué pasó | Por qué engañaba | El fix |
|---|---|---|
| **`bench new-site --install-app` headless no siembra datos maestros** (`Warehouse Type`, UOM, Item Groups, Market Segments). Crear la primera `Company` reventó con `LinkValidationError: Could not find Warehouse Type: Transit` (S0.7) | El sitio se veía sano — `list-apps` mostraba `erpnext` instalado, el `ping` respondía. El hueco solo aparece cuando algo intenta usar ese dato maestro, y eso normalmente pasa recién al crear la primera `Company` | Llamar `erpnext.setup.setup_wizard.operations.install_fixtures.install(country=...)` (+ las funciones sueltas si `set_up_address_templates` revienta por el bug de `frappe.local.lang`, ver abajo) **antes** de crear cualquier `Company`, en todo tenant nuevo |
| **Un proceso Python vivo no se entera de una app nueva.** Tras `bench new-app` + `install-app`, el site respondía `500 Internal Server Error` — `ModuleNotFoundError: No module named 'korvexcio'` (S1.1) | `install-app` terminó "sin errores" en la consola. El paquete se instaló bien en el venv (`uv pip install -e`). El problema es que `backend`/`queue-*`/`scheduler`/`websocket` ya estaban corriendo **desde antes** de que el paquete existiera, y un proceso vivo no relee `sys.path` solo | `docker compose restart backend queue-short queue-long scheduler websocket` **después** de instalar cualquier app nueva o cambiar `modules.txt`. No hace falta tocar `frontend`, `db` ni los `redis` |
| **`frappe/locale.py:get_locale_value` revienta si `frappe.local.lang` no está seteado** fuera de un request HTTP (bug de upstream, no de este proyecto) — pasó corriendo `install_fixtures.install()` desde `bench console` (S0.7) | El traceback apunta a Jinja/`Address Template`, parece un problema de plantillas cuando en realidad es que falta un dato de contexto | No se parchea Frappe. Se evita ejecutando solo las funciones de `install_fixtures` que hacen falta (no el `install()` completo), o seteando `frappe.local.lang` a mano antes de llamar algo que dependa de plantillas Jinja desde consola. **Volvió a pasar en S1.4** (una `Notification` estándar al crear un `Fiscal Year` de prueba) — desde entonces `before_tests()` lo blinda al principio: `if not frappe.local.lang: frappe.local.lang = "en"` |
| **Un `Role` recién creado no tiene NINGÚN permiso, ni siquiera leer** (S1.7) | Se probó el aislamiento y reventó con `PermissionError: Insufficient Permission for Company` **antes** de llegar a evaluar el `User Permission` — es el comportamiento correcto de Frappe (sin `DocPerm` no hay acceso), pero fácil de no anticipar si uno asume que un Role "básico" trae algo por default | Todo `Role` nuevo necesita su `Custom DocPerm` explícito en cada doctype que va a tocar — aunque sea solo lectura, como `Company` |
| **`frappe.get_doc(doctype, name)` NO chequea permisos de lectura** — es una llamada de ORM de bajo nivel (S1.8) | Un test que usa `get_doc()` para simular "¿puede leer esto un usuario sin permiso?" da falso negativo: parece que hay un hueco de seguridad cuando en realidad el test está mal escrito | Usar `frappe.client.get(doctype, name)` — la función real detrás de `/api/resource/<doctype>/<name>` — para probar lectura. Y en código propio: todo `@frappe.whitelist()` que lea un doc debe llamar `doc.check_permission("read")` explícito, nunca confiar en `get_doc()` solo |
| **Frappe distingue "existe pero no es tuyo" de "no existe"** — `PermissionError` vs `DoesNotExistError` (S1.8) | Es comportamiento nativo de la plataforma, no algo que introdujo este proyecto — pero sí es la fuga de enumeración exacta que el blueprint pedía probar (§7.3, escenario 9) | Documentado como deuda menor en `PROGRESO.md`. No se intentó parchear Frappe para unificar los errores — cambio de mayor alcance que este slice |
| **El checkout del nodo quedó sucio antes de consumir Git** (S2.1) | Un `git pull --ff-only` puede quedar bloqueado o mezclar cambios manuales con el artefacto versionado; el exit code solo no prueba qué SHA corre | Antes de conectar el nodo a Git: crear backup recuperable del árbol, verificarlo y hacer `git stash` de todo cambio local. Luego el nodo solo hace pull de commits conocidos y se verifica el SHA |
| **`Ran 0 tests` no es un RED válido de TDD** (S2.1) | Un fallo de import/discovery puede parecer el rojo esperado, pero ninguna aserción se ejecutó | El test inicial tiene que ser descubrible y fallar dentro del caso. En S2.1 la desviación quedó documentada; no se fingió evidencia retroactiva |
| **Frappe creó el usuario MariaDB atado a la IP efímera del contenedor** (S2.1, D21) | `migrate` funcionó antes del restart; después Docker movió `backend` de `172.18.0.5` a `.9` y la suite murió con `1045 Access denied`, aunque DB y contenedores parecían sanos | Con autorización explícita de Yedin, se conservó usuario/clave/privilegios y se cambió solo el host a `172.18.%`, la red Docker privada y aislada de KORVEXCIO. Verificar el grant después de cualquier recreación de DB/site |

---

## Deuda que nace con el proyecto

| Qué | Por qué duele |
|---|---|
| ~~La carpeta se llama `VAPELAND`~~ ✅ **RESUELTO 2026-08-31** | El producto se llama **KORVEXCIO**. Yedin renombra `C:\PROYECTOS\VAPELAND` → `C:\PROYECTOS\KORVEXCIO`. VAPELAND queda como lo que es: **el primer cliente/tenant**, no el proyecto. |
| **La carpeta de KORVIS sigue llamándose `ADAP` en disco** | Mismo error, sin resolver. El producto es **KORVIS**; `ADAP` es su primer cliente. Las rutas de estos documentos apuntan al nombre real de hoy. Va en `_KORVEX-OPS/MUDANZA.md`. |

### ⛔ Antes de "arreglar" el nombre dentro del repo de KORVIS

**`adap` es load-bearing en ese código. Un find-replace rompe producción.**

Verificado el 31/08/2026 en `C:\PROYECTOS\ADAP`:

| Dónde vive | Qué es |
|---|---|
| `organizations/adap/` | La carpeta del tenant. Su `config.yml` y su base de conocimiento |
| `ADAP_WHATSAPP_TOKEN` · `ADAP_PHONE_NUMBER_ID` · `ADAP_WABA_ID` · `ADAP_VERIFY_TOKEN` · `ADAP_WEBHOOK_SECRET` · `ADAP_NOTIFY_EMAIL` | Variables de entorno del servidor |
| `resolveBySlug('adap')`, el seed, los tests | Resolución del tenant en runtime |

Y la propia `ADAP/docs/GUIA-ALTA-DE-TENANT.md` lo dice: *"Slug del tenant —
**No** [se puede cambiar] — queda fijo, es la carpeta y el prefijo de las
variables."*

👉 **El rebranding ahí es solo de prosa** (README, CLAUDE.md, docs), con git
abierto y commit aparte. **El slug `adap` se queda como está, para siempre.**
| **Dos plataformas, un solo mini PC** | KORVIS (Node+Postgres) y ERPNext (Python+MariaDB) compartiendo 14 GB y 84 GB. Funciona con 2–3 sites. No escala a la visión de "venderlo a más clientes" sin un segundo nodo o un VPS. |
| **`korvex_ecf` = tú eres el responsable de cada cambio normativo de la DGII** | La DGII actualiza XSD (última vuelta: octubre 2025). Con proveedor certificado, buena parte de eso lo absorbe él. Con app propia, cada cambio es un ticket tuyo. |
| **No hay entrada en `data/korvex.json`** | §7.2 de `CONVENCIONES.md`: el proyecto se agrega al mapa **antes** de seguir. Pendiente. |

---

## Índice de la documentación

| Archivo | Qué contiene |
|---|---|
| `PROMPT-CLAUDE-CODE.md` | **El prompt listo para pegar** en la primera sesión de Claude Code |
| `docs/01-DESCUBRIMIENTO.md` | El negocio, los dos rubros, qué hace especial un vape shop |
| `docs/02-FISCAL-RD.md` | e-CF, tipos de comprobante, ISC, ITBIS, RST, certificado digital, contingencia |
| `docs/03-BENCHMARK-OPENSOURCE.md` | Todos los repos evaluados, con licencia, madurez y veredicto |
| `docs/04-ARQUITECTURA.md` | Multi-tenancy Frappe, hosting, módulos, hardware POS |
| `docs/05-PREGUNTAS-CLIENTE.md` | Lo que falta confirmar. Llevarlo a la reunión |
| `docs/06-COMO-SE-TRABAJA.md` | **Cómo se extiende ERPNext sin tocarlo.** Leer antes de escribir la primera línea |
| `docs/07-ARQUITECTURA-REFERENCIA.md` | **Barrido de ~45 repos de RD + 9 localizaciones fiscales de Frappe.** El mapa de licencias y la estructura de DocTypes ya destilada |
| `docs/08-BLUEPRINT.md` | ⭐ **El plan maestro.** Fases, microslices, verificación de cada uno, seguridad por fase, riesgos. **La fuente de verdad del qué y del orden** |
| `docs/13-VERSION-FRAPPE.md` | **D2 cerrada con evidencia:** el build de v16, las versiones, los SHA probados, los límites de memoria y los puertos |
| `docs/SEGURIDAD-SECURE-VIBE.md` | La plantilla de Secure-Vibe tal cual. Su traducción a Frappe está en el blueprint §7.3 |
| `AGENTS.md` | La misma plantilla, para Codex / Cursor / Copilot |
| `apps.json` · `docker/compose.s05.yaml` | Qué upstream se instala y en qué branch · los `mem_limit` y el puerto en loopback |
| `PRD.md` · `TECH_STACK.md` · `CLAUDE.md` · `PROGRESO.md` | Los obligatorios de `_PLANTILLA` |


---

## Nivel de confianza de este documento

Regla de `_KORVEX-OPS`: **cero datos inventados.** Lo que no se pudo verificar
va marcado. Estado al cierre de la sesión de descubrimiento:

| Afirmación | Estado |
|---|---|
| **15/11/2026** — e-CF obligatorio para pequeños/micro/no clasificados | ✅ Verificado en dos fuentes independientes |
| **31/10/2026** — mueren los comprobantes tipo "B" para grandes locales y medianos | ✅ Verificado |
| **76 días** de hoy al 15/11/2026 | ✅ Calculado |
| Sanción 5–50 salarios mínimos (Ley 32-23) | ✅ Verificado |
| Reglas operativas del e-CF (contingencia, TrackID, QR, secuencias, RI) | ✅ FAQ oficial de la DGII |
| Umbral RD$250,000 para exigir RNC en E32 (Norma 05-19) | ✅ Verificado |
| El ISC lo pagan fabricantes/importadores, no el detallista | ✅ DGII — 🟡 **pero el caso vapes con Ley 30-26 hay que confirmarlo con el contador** |
| Ley 30-26, 55% ad-valorem a vapes, promulgada 19/06/2026 | ✅ Verificado en dos fuentes |
| ERPNext GPLv3 + restricción de marca Frappe | ✅ Documento legal oficial de Frappe |
| `ecf-dgii` es MIT, Python, ambientes test/cert/prod | ✅ Verificado en PyPI |
| **`ecf-dgii` soporta E32 y RFCE** | ❌ **NO VERIFICADO.** PyPI no lo documenta. **Riesgo del camino crítico** |
| POSNext: AGPL-3.0, offline-first, escáner, requiere v15+ | ✅ Verificado en el repo |
| **v15 mejor que v16 para arrancar** | 🟡 **Opinión, no dato.** POSNext dice "v15 o superior". Se confirma levantando el bench |
| Requisitos de RAM/disco de ERPNext | 🟡 Fuente secundaria (blog de hosting), no documentación oficial |
| Alanube soporta E32/RFCE | ❌ **No confirmado.** Preguntarlo por escrito |
| Costos por documento e-CF en RD | ❌ **Nadie publica cifras.** Hay que pedir cotización |
| Todo lo marcado ⚠️ en `docs/01` y `docs/05` | ❌ Supuestos sobre el negocio del cliente, sin confirmar con él |

### Del barrido del 31/08 (noche) — `docs/07-ARQUITECTURA-REFERENCIA.md`

| Afirmación | Estado |
|---|---|
| El resto del inventario de repos y el patrón arquitectónico | 🟡 **Barrido de subagente, SIN verificar de segunda mano.** Mapa de dónde buscar, no hecho probado |
| `rob-erply/dgii_facturacion_electronica` | ❌ **El repo da 404.** Retirado del doc 03 |
| No existe librería Python que haga e-CF directo a la DGII | 🟡 Ausencia reportada por el barrido — imposible de probar, pero coherente con lo que ya se sabía |

### ✅ Los 4 repos ⭐ — VERIFICADOS el 2026-08-31 (paso 1 de Fase 0, cerrado)

| Repo | Licencia | E32 | RFCE | Veredicto |
|---|---|---|---|---|
| `wilmerm/alanube-python` | **MIT** ✅ | ✅ tipo 32 en el README | ❌ **no documentado** | Python nativo, pero sin RFCE |
| `victors1681/dgii-ecf` | **MIT** ✅ (v1.8.5) | ✅ | ✅ **`sendSummary`, `convertECF32ToRFCE`** | **Única implementación de RFCE copiable.** Es TypeScript |
| `platinum-place/laravel-dgii` | **MIT** ✅ | ✅ plantillas Blade e-CF / consumo / anulación / acuse | 🟡 no confirmado explícito | Plantillas XML traducibles a Jinja2 |
| `LewisMojica/dgii-compliance` | GPL-3.0 | ❌ solo NCF | ❌ | Confirmado: **referencia, no dependencia** |

Verificaciones extra de esa misma pasada:

| Cosa | Resultado |
|---|---|
| `ecf-dgii` (ECF SSD) | **MIT**, v1.0.0 del 7-may-2026, ambientes test/cert/prod ✅ — pero **solo documenta E31**. Ni E32 ni RFCE. **Esto revisó D3** |
| `erpnext_mexico_compliance` | **MIT**, pero guarda el XML en **custom fields** de Sales Invoice → confirma el "no copies a México" del doc 07 |
| `DeeloaSociety/posnext` | **AGPL-3.0**, Frappe 15+, **Vue 3**, offline con IndexedDB. 🟡 **Sin rama `main` ni `version-16`** — solo `develop` y `version-1.12`. Se instaló desde `develop` en S0.5 |
| `yrestom/POS-Awesome` | GPL-3.0, pero **README en v14**, **Vue 2** (EOL dic-2023), sin offline documentado → **descartado (D15)** |
| Alanube (proveedor) | Aprobado por DGII desde 2021. Sandbox `https://sandbox.alanube.co/dom/v1` |

🔴 **El hueco del camino crítico, precisado — no cerrado:** **RFCE no está documentado
en ninguna vía Python.** Existe en TypeScript bajo MIT (`victors1681/dgii-ecf`) y
contra el endpoint directo de la DGII (`fc.dgii.gov.do/recepcionfc`). Y no es un caso
borde: los E32 bajo RD$250,000 van en resumen, no uno a uno — en un vape shop y una
cafetería eso es **~100% del volumen**. Por eso **S0.9 es el gate del proyecto**.

**Los dos huecos que quedan:** que el plan fiscal cubra **E32 + RFCE** (S0.9), y que el
cliente tenga **RNC**. Se cierran esta semana o el plan cambia de forma.
