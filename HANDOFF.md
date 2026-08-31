# HANDOFF — KORVEXCIO (cliente 1: VAPELAND)

> **Lo primero que se lee al retomar.** Escrito el 2026-08-31 en sesión de
> descubrimiento (Cowork). Estado: **⚪ Semilla** — cero código, decisiones
> de arquitectura tomadas, camino crítico identificado.
>
> Próximo paso: abrir Claude Code en `C:\PROYECTOS\KORVEXCIO` y planificar
> las fases sobre este documento.

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

**Multi-tenancy:** DNS-based multitenancy de Frappe (`bench config dns_multitenant on`).
Un **site por cliente** = una base de datos MariaDB por cliente = aislamiento
físico real, más fuerte que el `organization_id` de KORVIS. Cada tenant su
subdominio: `vapeland.korvexdev.cc`, `cliente2.korvexdev.cc`.

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

## Lo primero que se hace en Claude Code

En este orden. Nada de esto es código de producto todavía — es reducir riesgo.

| # | Qué | Por qué primero |
|---|---|---|
| 1 | **Levantar ERPNext v15 en Docker local** y crear el site `vapeland.localhost` | Hasta que no lo veas corriendo, todo lo demás es teoría |
| 2 | **Verificar los 4 repos ⭐ de `docs/07`** — abrir y confirmar licencia, actividad y alcance | El barrido salió de un subagente y **no se pudo verificar de segunda mano**. Son 20 min |
| 3 | **Spike fiscal**: emitir un E32 de prueba contra TesteCF. **Plan A:** `wilmerm/alanube-python` (MIT, Python, los 10 tipos). **Plan B:** `ecf-dgii`/ECF SSD. **Plan C:** portar de `victors1681/dgii-ecf` (MIT, TS, tiene RFCE) | Es el camino crítico. Si ninguno da E32 + RFCE, el proyecto cambia de forma. **Timebox: 2 días.** |
| 4 | **Probar POSNext y POS Awesome** con el catálogo real del cliente | Decidir cuál se adopta antes de construir encima de ninguno |
| 5 | **Modelar el catálogo real**: 500–1,000 SKUs con variantes | Es donde se rompen los POS genéricos, no en el cobro |
| 6 | Recién ahí: scaffold de la app `korvexcio` **con la estructura de DocTypes de `docs/07` §4** | Ya no se diseña desde cero: está destilada de 3 localizaciones en producción |

**Regla del `CONVENCIONES.md` que aplica aquí:** el repo se crea **antes** de
escribir código, y con remote desde el primer commit. `_KORVEX-OPS` ya tiene
dos proyectos violando esto (DIGIVAL, FRAMERD). Que este no sea el tercero.

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
| Todo el inventario de repos y el patrón arquitectónico | 🟡 **Barrido de subagente, SIN verificar de segunda mano.** Se agotó el límite de fetch de la sesión. Es un mapa de dónde buscar, no hecho probado |
| `wilmerm/alanube-python` — MIT, Python, 10 tipos, vivo | ⭐ **Verificar primero.** Es el nuevo candidato #1 |
| `victors1681/dgii-ecf` — MIT, con `sendSummary` (RFCE) y `convertECF32ToRFCE` | ⭐ **Verificar.** Si es cierto, es la especificación ejecutable del RFCE |
| `platinum-place/laravel-dgii` — MIT, plantillas del XML de e-CF y RFCE | ⭐ **Verificar.** Traducir Blade→Jinja2 sería mecánico |
| `erpnext_mexico_compliance` — MIT | ⭐ **Verificar.** La única localización madura de la que se puede copiar código |
| `rob-erply/dgii_facturacion_electronica` | ❌ **El repo da 404.** Retirado del doc 03 |
| No existe librería Python que haga e-CF directo a la DGII | 🟡 Ausencia reportada por el barrido — imposible de probar, pero coherente con lo que ya se sabía |

**Los tres huecos que más duelen:** que el plan fiscal cubra **E32 + RFCE**, que
el cliente tenga **RNC**, y que los 4 repos ⭐ sean lo que el barrido dice. Los
tres se cierran esta semana o el plan cambia de forma.
