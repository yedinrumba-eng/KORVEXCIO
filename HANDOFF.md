# HANDOFF — KORVEXCIO (cliente 1: VAPELAND)

> **Lo primero que se lee al retomar.** Escrito el 2026-08-31 en sesión de
> descubrimiento (Cowork), actualizado al cerrar S0.7. Estado: **🔵 Fase 0 en
> curso** — bench v16 levantado, D2 cerrada, site `korvexcio.korvexdev.cc` con
> ERPNext y las dos `Company` reales creadas.
>
> **Nombres reales (31/08, confirmados por Yedin):** la vapería es
> **VAPERIA LA J Y EL JALAPEÑO** (abbr `VLJ`), la cafetería es
> **EL SABOR DE LAS 5 ESQUINAS** (abbr `ESE`). El codename interno del
> cliente en la cabecera de este repo sigue siendo "VAPELAND" — es shorthand
> del proyecto, no el nombre de ninguna `Company`.
>
> Próximo paso: **S0.7b**, site `demo.korvexdev.cc`.
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

## Estado técnico al retomar — después de S0.7

- Imagen en `korvex-node1`: `korvexcio:16`, digest
  `sha256:6ed8f523d2795fdc4c7a808b7cfe8cb50c572d2cabc8f2e6b2485d5e1f4b2ee2`.
- Stack Compose: proyecto `korvexcio`, nueve servicios runtime arriba,
  configurator terminado con código 0 y MariaDB healthy.
- Versiones: Frappe `16.32.0`, ERPNext `16.33.0`, POSNext `1.12.0`, URY
  `v3.0.0-beta.1`.
- Red: solo frontend en `127.0.0.1:8080`; DB y Redis sin puertos host.
- Recursos: límites sumados 5,504 MiB; 60 GB libres, sin cambio medible desde
  S0.5.
- KORVIS: servicio activo y `/health` con Postgres/Redis `ok`.
- Site: **`korvexcio.korvexdev.cc`**, `frappe 16.32.0` + `erpnext 16.33.0`.
- **Companies:** `VAPERIA LA J Y EL JALAPEÑO` (`VLJ`) y
  `EL SABOR DE LAS 5 ESQUINAS` (`ESE`), cada una con `tax_id` placeholder
  (RNC pendiente, D13), `default_currency=DOP`, 4 almacenes propios, cost
  center propio, 94 cuentas (Chart of Accounts). Creadas por Claude vía
  `bench console` — es operación de datos dentro de un site existente, el
  clasificador **no** la bloqueó (a diferencia de `bench new-site`).
- 🟡 **Hueco de fixtures descubierto en S0.7:** `bench new-site
  --install-app` headless no siembra `Warehouse Type`, UOM, Item Groups ni
  Market Segments — eso solo lo hace el Setup Wizard de la UI. Se corrigió a
  mano llamando `install_fixtures.install()` + funciones sueltas. **Hay que
  repetirlo en S0.7b** (`demo.korvexdev.cc`) y en cualquier tenant nuevo.
  Debe entrar al script de alta de tenant, no repetirse de memoria.
- Password de Administrator: generado random en el nodo
  (`/home/korvex/frappe_docker-korvexcio-s05/.korvexcio-admin-pw`, 600).
  **Nunca pasó por el chat ni por este repo.**
- Commits locales: `e119e00`, `2411f94`, `e611edc`, `4b0027b` (cierre de
  S0.6), más el commit de este cambio (ver `git log --oneline -5`).
  `origin/main` sigue en `e19389f`: **no hubo push**.
- Pendiente inmediato: **S0.7b**, site `demo.korvexdev.cc`.
- Deuda: POSNext/URY están en branches `develop`; fijar referencias inmutables
  antes de S1.2. Build cache reclamable: 7.154 GB.

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

### Lo que sigue, en este orden

| # | Slice | Qué | Verificación |
|---|---|---|---|
| 1 | **S0.7b** ⭐ | Site `demo.korvexdev.cc` — el modelo por cliente se prueba el día 1, no al final. **Recordar el fix de fixtures de S0.7** antes de crear cualquier Company ahí | Dos DBs distintas en `SHOW DATABASES`; un cambio en uno no aparece en el otro |
| 2 | **S0.8** | Spike POS *(timebox 2 días)*: POS nativo vs POSNext, matriz de 8 criterios llena **antes** de instalar | `docs/10-SPIKE-POS.md` con evidencia por criterio y veredicto de una línea |
| 3 | **S0.9** 🔴 | **Spike fiscal — EL GATE.** E32 + RFCE contra TesteCF | **TrackID real** pegado en `docs/11-SPIKE-FISCAL.md`. Sin TrackID no se declara nada |
| 4 | **S0.10 → S0.12** | Cuota de disco, catálogo, cierre de Fase 0 en los documentos | `PROGRESO.md`, `TECH_STACK.md`, `data/korvex.json` ⚪ → 🔵 |

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
