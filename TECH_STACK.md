# TECH_STACK — KORVEXCIO

> Cada decisión con su razón y con lo que se descartó. Sin razón escrita, la
> decisión se va a re-discutir en tres meses.

---

## El stack

| Capa | Elección | Versión |
|---|---|---|
| Framework | **Frappe Framework** | v15 |
| ERP | **ERPNext** | v15 |
| Base de datos | **MariaDB** | 10.6+ |
| Cache / cola | **Redis** | 7 |
| POS | **POSNext** (Vue 3 + Vite + TS) | v1.6.x |
| App propia | **`korvexcio`** — módulos `ecf` y `retail` | — |
| Fiscal | `ecf-dgii` (PyPI, MIT) dentro del módulo `ecf` | 1.0.0 |
| CRM *(fase 2)* | **Frappe CRM** | — |
| Cafetería *(fase 2)* | **URY** | v0.2.x |
| Contenedores | Docker Compose (`frappe_docker`) en dev · bench en prod | — |
| Ingreso | Cloudflare Tunnel → `*.korvexdev.cc` | — |

---

## D1 — ERPNext/Frappe como base

**Decisión de Yedin, 2026-08-31.** Se evaluaron cuatro caminos: stack de KORVIS,
ERPNext, Odoo CE, e híbrido.

**Lo que se gana:** inventario con variantes y lotes, contabilidad, compras,
multi-almacén, POS, CRM y **multi-tenancy nativa por site** — todo desde el
día 1, contra un deadline de 76 días.

**Lo que se paga:**
1. **El stack queda partido.** Python/MariaDB aquí, Node/TS/Postgres en KORVIS.
   Dos plataformas en el mismo mini-PC. El asistente de WhatsApp **se integra
   por API, no se reusa**.
2. **GPLv3.** Toda modificación distribuida queda GPLv3.
3. **Marca.** "ERPNext" y "Frappe" no pueden ir en el nombre del producto, de
   la empresa, ni en el dominio. Hay que mantener visible el aviso
   `© Frappe Technologies Pvt. Ltd.`
4. **El e-CF de RD no existe en Frappe.** Se escribe.

**Descartado — stack de KORVIS (Node/TS):** habría dado un solo stack, reuso
directo del asistente y del design system "clear glass", y `victors1681/dgii-ecf`
(la mejor librería de e-CF que existe, y es TypeScript). Costo: construir POS +
inventario + contabilidad desde cero, 3–5 meses. **Contra 76 días, no cabía.**

**Descartado — Odoo CE:** LGPLv3 es más amigable, POS maduro. Pero sigue siendo
Python de otro framework, el e-CF también hay que escribirlo, y la presión
comercial hacia Enterprise es permanente.

**Descartado — híbrido:** viola la regla de `CONVENCIONES.md` §9 — *"no mover
la mitad de un sistema"*. Dos sistemas que sincronizar es peor que uno malo.

## D2 — Versión v15, no v16

v16 salió el 12/01/2026 (beta desde nov 2025).

⚠️ **Ojo — esta decisión es preliminar, no verificada.** POSNext declara
"Frappe v15 **o superior**", así que v16 debería servir *en el papel*. No se
encontró evidencia pública de que las apps de terceros (POSNext, URY, POS
Awesome) estén probadas en producción sobre v16.

**Criterio:** contra un deadline de 76 días, la versión con más kilómetros en
el ecosistema gana. Pero **esto se confirma en el paso 1 del `HANDOFF.md`** —
levantar el bench y ver qué instala limpio. Si v16 instala las apps sin
fricción, se arranca en v16 y se ahorra una migración.

## D3 — e-CF vía proveedor certificado, con adaptador

**Decisión de Yedin, 2026-08-31.**

Principal: **ECF SSD** vía `ecf-dgii` (PyPI, **MIT**, v1.0.0 de mayo 2026, de
Smart Software Development SRL). Es **Python**, así que en una app de Frappe es
un `import`, no una integración.

**Pero se construye detrás de una interfaz `FiscalProvider`** con dos
implementaciones (SSD y Alanube). Razón: un tenant futuro puede llegar con
proveedor ya contratado, y cambiarlo no puede significar reescribir la app.

**Descartado — integración directa a DGII:** cero costo por emisión y control
total, pero implica certificarse como emisor, manejar el certificado, los XSD,
la contingencia y **cada cambio normativo de la DGII**. Con 76 días encima, es
riesgo puro.

**Descartado — Facturador Gratuito de la DGII:** 150 comprobantes al mes, solo
web sin API, sin modo offline. No es un POS.

## D4 — POSNext sobre POS Awesome (a validar)

El **offline-first real** (IndexedDB + Service Workers + PWA + sync en
background) es lo que decide: un POS en RD que se cae con el internet no es un
POS, y encaja con la regla de contingencia de la DGII.

⚠️ **No es definitivo.** POS Awesome tiene más comunidad; el fork de POSNext
evaluado tiene 2 estrellas. **Spike de 2–3 días probando los dos con el
catálogo real antes de comprometerse.**

## D5 — Los upstream no se tocan · UNA app, dos módulos

**No se clona ERPNext.** Se instala vía `apps.json` con branch fijado, y todo lo
propio vive en la app `korvexcio`: DocTypes propios, `hooks.py`, custom fields
exportados como fixtures, y overrides solo en último recurso. Un `git pull` de
ERPNext no puede romper el proyecto.

**Una app, no dos** (corregido el 31/08): `apps.json` instala *un repo = una
app*. Dos apps serían dos repos, dos builds y dos `install-app` por tenant, para
separar algo que nadie pide separado. Frappe ya da módulos internos
(`modules.txt`). Sacar `ecf/` a su propia app el día que haya un cliente que
compre solo el fiscal es un refactor de días.

**Excepción — POSNext sí se forkea:** necesita campos fiscales dominicanos por
dentro y no está diseñado para extenderse desde afuera. Fork propio, rama
`korvex`, `upstream` como remote, rebase.

Detalle completo con comandos: `docs/06-COMO-SE-TRABAJA.md`.

## D6 — Multi-tenancy: un site por cliente

DNS-based multitenancy de Frappe. Cada site su propia base MariaDB →
**aislamiento físico**, más fuerte que el `organization_id` de KORVIS.

Trade-off aceptado: **más seguro, menos escalable.** Decenas de tenants por
servidor, no miles. Para el volumen de KORVEX es lo correcto.

⚠️ **Pero la lección del 06/08/2026 sigue aplicando al canal de salida:** las
credenciales de un canal saliente se resuelven **por mensaje**, nunca una vez
al arrancar.

## D7 — El asistente de IA se integra, no se incrusta

No se usa `frappe_whatsapp` ni `waba_integration` — mandan plantillas, no son
asistentes conversacionales con RAG. **KORVIS ya lo resuelve y está en
producción.** ERPNext expone su API REST; KORVIS es el cliente. ERPNext no debe
saber que WhatsApp existe.

## D8 — Escáner: HID keyboard primero, WebHID después

El modo keyboard-wedge funciona con cualquier POS web y cero configuración. Se
arranca ahí. WebHID (`@point-of-sale/webhid-barcode-scanner`, MIT) es una mejora
posterior: el código llega como un solo evento, sin depender del foco, y
decodifica GS1/GTIN automáticamente.

## D9 — Impresión térmica vía QZ Tray

Es la vía probada en el ecosistema Frappe (`aisenyi/ERPNext POS Hardware
Integrations`). WebUSB directo es posible pero frágil entre modelos de
impresora. La gaveta se abre por el RJ11 de la impresora: es un comando ESC/POS
más, no una integración aparte.

---

## Lo que NO se usa, y por qué

| Descartado | Razón |
|---|---|
| **Kubernetes, microservicios, multi-región** | Esto corre en un mini PC en una casa. Mismo criterio que `ADAP/docs/research/12-antipatrones.md` |
| **Twenty CRM / EspoCRM / Chatwoot** | Tercer y cuarto stack. Frappe CRM vive en el mismo bench |
| **Medusa / Vendure / Saleor** | Commerce headless, no ERP. Sin contabilidad ni POS de mostrador |
| **FinOpenPOS** (Next.js 16 + Drizzle, MIT) | Encaje perfecto con el stack de KORVIS — irrelevante tras D1. Anotado por si D1 se revisa |
| **`satisfecho/pos`** (Angular + FastAPI) | Quinto stack, y es restaurante, no retail |
| **`dgii-compliance` como dependencia** | 3 estrellas, 0 forks, sin releases, y solo NCF tradicional. Se lee como referencia |
| **`rob-erply/dgii_facturacion_electronica`** | **OPL-1, licencia propietaria.** Se mira, no se copia |
| **Construir el POS desde cero** | 3–5 meses contra 76 días |
