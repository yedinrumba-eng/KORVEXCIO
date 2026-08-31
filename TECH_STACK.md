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

> ⚠️ **Dónde vive cada decisión, actualizado el 31/08/2026.**
> **D1–D9 están abajo, en este archivo.** **D10–D19 viven en
> `docs/08-BLUEPRINT.md` §3** y se doblan aquí en S0.12; mientras tanto, ese es
> el lugar canónico. Estado de las de aquí: **D2 cerrada en v16** ✅ ·
> **D3 revisada** (el proveedor lo decide S0.9, bloqueada) · **D4 superada**
> por D15+D16 · **D6 revisada** por D19 · **D16 revisada el 31/08 por S0.8**:
> recomienda POSNext, revirtiendo el sesgo hacia el nativo, pendiente OK de
> Yedin.
>
> Y una advertencia que ahorra media hora: `PROGRESO.md` numeró un "D4" distinto
> (el alcance del MVP) en la entrada del descubrimiento. **Ese está derogado por
> D12.** Ver la sección D4 más abajo.

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

## D2 — Versión **v16** ✅ CERRADA el 31/08/2026 con evidencia

**Se arranca en v16.** El slice S0.5 levantó el bench en `korvex-node1` y las
cuatro apps construyeron y arrancaron:

| App | Referencia | Versión que reportó `bench version` |
|---|---|---|
| `frappe/frappe` | `version-16` | `frappe 16.32.0` |
| `frappe/erpnext` | `version-16` | `erpnext 16.33.0` |
| `DeeloaSociety/posnext` | `develop` | `pos_next 1.12.0` |
| `ury-erp/ury` | `develop` | `ury v3.0.0-beta.1` |

**Por qué v16 y no v15:** el plan ordenaba bajar a v15 *solo si alguna app
reventaba en v16*. Esa condición no ocurrió, así que probar v15 de todos modos
habría sido trabajo que no cambia la decisión — y arrancar en v16 ahorra una
migración antes del 15/11.

🟡 **Deuda que nace con esto:** POSNext y URY **no publican rama `version-16`**;
se instalaron desde `develop`, que es mutable. Los SHA exactos que se probaron
están en `docs/13-VERSION-FRAPPE.md`, y **S1.2 los fija** (SHA o mirrors de
Korvex) antes de que esto sea producción. *No se actualiza una app de producción
siguiendo el HEAD de `develop`.*

Evidencia completa — build, servicios, memoria, puertos y KORVIS sano:
`docs/13-VERSION-FRAPPE.md`.

> *Lo que decía antes:* "v15, no v16 — preliminar, no verificada. POSNext declara
> Frappe v15 o superior; no hay evidencia pública de terceros probados en v16."
> Se resolvió levantando el bench, que era exactamente lo que pedía.

## D3 — e-CF vía proveedor certificado, con adaptador · 🟡 REVISADA el 31/08

**Decisión de Yedin, 2026-08-31.** La forma se mantiene; **el proveedor
principal ya no está fijado.**

🔴 **Lo que cambió:** al verificar `ecf-dgii` de segunda mano, se confirmó que
**solo documenta E31 (Factura de Crédito Fiscal)**. Ni E32 ni RFCE. Y E32 bajo
RD$250,000 — que va en **resumen (RFCE)**, no uno a uno — es ~100% del volumen
de un vape shop y una cafetería.

👉 `ecf-dgii` **pasa a candidato #2**. El proveedor lo decide el spike **S0.9**,
que es el gate del proyecto. **La interfaz `FiscalProvider` se mantiene y ahora
es más necesaria, no menos.**

> *Lo que decía antes:* "Principal: **ECF SSD** vía `ecf-dgii` (PyPI, **MIT**,
> v1.0.0 de mayo 2026, de Smart Software Development SRL). Es **Python**, así que
> en una app de Frappe es un `import`, no una integración."

Sigue siendo cierto que es MIT, Python y de un proveedor certificado, con
ambientes `test`/`cert`/`prod`. Lo que no está confirmado es que cubra lo que
este POS necesita.

**Pero se construye detrás de una interfaz `FiscalProvider`** con dos
implementaciones (SSD y Alanube). Razón: un tenant futuro puede llegar con
proveedor ya contratado, y cambiarlo no puede significar reescribir la app.

**Descartado — integración directa a DGII:** cero costo por emisión y control
total, pero implica certificarse como emisor, manejar el certificado, los XSD,
la contingencia y **cada cambio normativo de la DGII**. Con 76 días encima, es
riesgo puro.

**Descartado — Facturador Gratuito de la DGII:** 150 comprobantes al mes, solo
web sin API, sin modo offline. No es un POS.

## D4 — POSNext sobre POS Awesome · 🟡 SUPERADA por D15 + D16

⚠️ **Colisión de numeración, resuelta aquí:** en `PROGRESO.md` la entrada del
descubrimiento numeró como "D4" al *alcance del MVP sin cafetería*. **Ese D4 está
DEROGADO por D12** (los dos negocios entran juntos en la v1). El D4 de este
documento es otra cosa: la elección de POS. Para no arrastrar el enredo,
**a partir de D10 la numeración canónica es la de `docs/08-BLUEPRINT.md` §3.**

Sobre la elección de POS, lo que hay hoy:

- **D15 — POS Awesome descartado**, y no por popularidad: **Vue 2 (EOL desde
  diciembre de 2023)**, README declarando **v14**, y **offline no documentado**.
  Un producto nuevo en 2026 sobre Vue 2 nace endeudado.
- **D16 — 🟡 REVISADA el 31/08 por el spike S0.8, con evidencia de código.**
  El sesgo original hacia el nativo asumía "la cola offline la escribes tú de
  todos modos" — **el spike encontró que eso es falso**: POSNext ya tiene una
  arquitectura de offline completa y funcionando en su código fuente
  (`offline.worker.js` + capa `db`/`cache`/`sync` + store dedicado), mientras
  que el POS nativo de ERPNext **no tiene ningún mecanismo de offline** (cero
  archivos, verificado por `grep`). Además POSNext factura contra `Sales
  Invoice` directo — el doctype donde previsiblemente enganchan los hooks de
  `ecf` (S2.9) — mientras el nativo usa `POS Invoice`, que se consolida
  después con retraso. **Recomendación del spike: POSNext.** Sigue pendiente
  el OK explícito de Yedin y la prueba en vivo (red cortada, 5 ventas), que
  se hace en **S4.1** con datos reales en vez de repetir el spike. Detalle
  completo con la matriz de 8 criterios: `docs/10-SPIKE-POS.md`.

> *Lo que decía antes:* "POSNext sobre POS Awesome (a validar). El offline-first
> real (IndexedDB + Service Workers + PWA + sync en background) es lo que decide."
> El criterio sigue en pie; lo que cambió es quién puede ganarlo — y ganó
> POSNext, al revés de lo que el sesgo original de D16 asumía.

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

## D6 — Multi-tenancy: un site por cliente · 🟡 REVISADA por D19

DNS-based multitenancy de Frappe. Cada site su propia base MariaDB →
**aislamiento físico**, más fuerte que el `organization_id` de KORVIS.

Trade-off aceptado: **más seguro, menos escalable.** Decenas de tenants por
servidor, no miles. Para el volumen de KORVEX es lo correcto.

**D19 (31/08) precisa el "por cliente":** un site por **CLIENTE**, y una
`Company` de ERPNext por **NEGOCIO** dentro de ese site. VAPELAND y la cafetería
son dos negocios del mismo dueño, así que viven en un solo site
(`korvexcio.korvexdev.cc`) como dos Companies: una URL, el login decide qué ves,
y el dueño obtiene un **dashboard consolidado** que dos sites separados no podrían
dar sin un agregador entre bases de datos.

🔴 **La línea que no se cruza:** **cliente 2 = site propio.** Entre clientes el
aislamiento se queda físico. Entre negocios del mismo dueño pasa a lógico — y
eso hay que blindarlo en **S1.8** (`permission_query_conditions` +
`has_permission` + `company` congelada, con 12 escenarios contra la API en CI).
Razón para no confiarse: PR frappe/erpnext#44695 (User Permission ignorada en los
estados financieros) e issue frappe/erpnext#43652 (*admin de Company A ve los
usuarios de Company B*), **cerrado como `not planned`**.

Detalle completo: `docs/08-BLUEPRINT.md` §5.2.

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
