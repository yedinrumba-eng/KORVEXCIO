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

## Fases

### Fase 0 — Reducir riesgo *(pendiente)*
- [ ] ERPNext v15 corriendo en Docker local con site `vapeland.localhost`
- [ ] **Spike `ecf-dgii`**: emitir un E32 de prueba contra TesteCF *(timebox 2 días)*
- [ ] Probar POSNext y POS Awesome con catálogo real → decidir cuál
- [ ] Modelar el catálogo: 500–1,000 SKUs con variantes
- [ ] Repo creado con remote *(§6 de `CONVENCIONES.md`)*
- [ ] Entrada en `data/korvex.json` + `BITACORA.md` *(§7.2)*
- [ ] Cliente confirma RNC y arranca el certificado digital

### Fase 1 — MVP
- [ ] `korvex_ecf` — E32, E31, E34, RFCE, secuencias, contingencia
- [ ] `korvex_retail` — atributos del vertical, FEFO, verificación de edad
- [ ] POS con escáner e impresión térmica con QR
- [ ] Catálogo e inventario inicial cargados
- [ ] Reportes del dueño
- [ ] Certificación como emisor ante DGII
- [ ] **Producción antes del 15/11/2026**

### Fase 2 — Producto
- [ ] Segundo site de demo
- [ ] Frappe CRM
- [ ] Módulo de cafetería (URY)
- [ ] Planes y precios validados contra el mercado RD

### Fase 3 — Integración
- [ ] VAPELAND como tenant de KORVIS *(checklist completo de `LECCIONES-MULTI-TENANT.md`)*
- [ ] Sincronización de catálogo ERPNext → base de conocimiento de KORVIS
- [ ] Cotización y cobro dentro del chat
