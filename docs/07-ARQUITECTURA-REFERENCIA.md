# 07 — Arquitectura de referencia: cómo lo hacen los que ya lo hicieron

> Barrido exhaustivo del 2026-08-31: **~45 repos de RD** y **9 localizaciones
> fiscales de Frappe/ERPNext** en LATAM, India y Arabia Saudí.
>
> ## ⚠️ Nivel de confianza de este documento
>
> Este documento sale de **dos barridos automatizados**. Se agotó el límite de
> fetch de la sesión antes de poder verificar de segunda mano los hallazgos
> principales. **Trátalo como un mapa de dónde buscar, no como hecho probado.**
>
> **Lo primero que hace Claude Code es abrir los 4 repos marcados ⭐ y
> confirmar licencia, actividad y alcance.** Son 20 minutos y evitan construir
> sobre una suposición.

---

## Lo más importante que salió del barrido

**No existe ninguna librería Python open source que haga e-CF end-to-end contra
la DGII.** Existe en TypeScript y en PHP. En Python solo hay wrappers de
proveedor, un firmador muerto y sin licencia, y una app monolítica.

Eso significa dos cosas:
1. La decisión #2 (proveedor certificado por API) **no era una preferencia —
   era la única salida sensata en Python**, y el barrido lo confirma.
2. Si algún día se hace la integración directa, hay **dos implementaciones
   completas y con licencia permisiva** de las que aprender.

---

## 1. El mapa de licencias — qué puedes copiar y qué solo puedes leer

Esto va primero porque es lo que te puede costar el producto.

| Licencia | Qué significa para KORVEXCIO | Repos |
|---|---|---|
| **MIT / Apache-2.0** | ✅ **Puedes copiar código.** Solo mantén el aviso | `victors1681/dgii-ecf` · `platinum-place/*` · `wilmerm/alanube-python` · `erpnext_mexico_compliance` · `nexo-do/aura-node` |
| **GPL-3.0** | ⚠️ Contagiosa — pero **ERPNext ya es GPLv3**, así que tu app va a ser GPL de todos modos. En la práctica no te cambia nada | `india-compliance` · `dgii-compliance` · `factura_electronica_gt` |
| **AGPL-3.0** | ⚠️ Contagiosa **incluso sirviendo como SaaS**. **Leer sí, copiar no** | `ksa_compliance` · `posnext` |
| **CC BY-NC-ND 4.0** | ⛔ **Prohíbe uso comercial Y obras derivadas.** Ni lo abras como referencia | `erpnext_chile_factura` |
| **OPL-1** | ⛔ Propietaria | `rob-erply/dgii_facturacion_electronica` *(y el repo ahora da 404)* |
| **SIN LICENCIA** | ⛔ **Legalmente inusable.** Sin licencia, "público" no es "libre" | `angelpimentell/python-dgii-signer` · `DeJesusEstevez/contafacil` · `yirbz/fintral-app` |

> 🩸 **La ironía del ecosistema dominicano:** varios de los repos más útiles no
> tienen licencia, incluido el **único firmador XML en Python** (11★) y el mejor
> validador de 606/607/608. Y el API del propio gobierno
> (`ogticrd/dgii-services-api`) está marcado `UNLICENSED`.

---

## 2. Repos de RD que importan

### ⭐ Los cuatro a verificar primero

| Repo | Lenguaje | Licencia reportada | Por qué importa |
|---|---|---|---|
| ⭐ **`wilmerm/alanube-python`** | **Python** | MIT | Cliente de **Alanube** (proveedor certificado). Reporta los **10 tipos** (31–47). Vivo (may-2026), con tests. **Candidato #1 para el módulo `ecf`** — es Python, entra en Frappe como un `import` |
| ⭐ **`victors1681/dgii-ecf`** | TypeScript | MIT | **La implementación open source más completa que existe** del protocolo directo con la DGII. 90★/68 forks, release ago-2026. Reporta: semilla→token, `P12Reader`, `signXml`, `sendElectronicDocument`, **`sendSummary` (RFCE)**, **`convertECF32ToRFCE`**, `voidENCF`, `sendCommercialApproval`, `statusTrackId`, QR. **Con tests.** No es Python, pero bajo MIT es una **especificación ejecutable** legal de la que portar |
| ⭐ **`platinum-place/laravel-dgii`** | PHP | MIT | Habla **directo con la DGII** (`testecf`/`certecf`/`ecf`). Lo valioso: **plantillas Blade que renderizan el XML del e-CF y del RFCE**. Traducirlas a Jinja2 es mecánico. Con tests |
| ⭐ **`LewisMojica/dgii-compliance`** | **Python/Frappe v15** | GPL-3.0 | **La única app Frappe de RD que existe.** Solo NCF, cero e-CF — pero ya resuelve: ciclo de vida de secuencias, asignación en `before_submit` de Sales Invoice **y POS Invoice**, facturas enmendadas, exclusión de consolidadas de cierre POS, y **sync diario del padrón RNC** desde el ZIP de la DGII. Sin tests ni CI |

### Otros que suman

| Repo | Para qué |
|---|---|
| `platinum-place/php-dgii-xml-signer` (MIT) | Solo la firma XMLDSig, con la canonicalización C14N específica que exige la DGII. Referencia del detalle que más duele |
| `SSD.../ecf_dgii` (Apache-2.0) | Monorepo multi-lenguaje de ECF SSD. ⚠️ El PyPI `ecf-dgii` declara MIT y el monorepo Apache-2.0 — **discrepancia a resolver** |
| `franklinmdev/dgii-ts` (MIT) | Validación de dígito verificador de RNC, cédula, NCF y **e-NCF serie E** |
| `JoelStalin/easycount-legacy` (MIT) | App FastAPI con XMLDSIG y `DGII_SIGN_TARGET_TAG` para `ECF`/`RFCE`. Hay servicio que extraer |
| `nexo-do/aura-node` (Apache-2.0) | SDK de otro proveedor (Aura). Buen ejemplo de webhooks HMAC + `Idempotency-Key` |
| `eriktaveras/facturas-opensource` (MIT, 92★) | **Exporta el 606 en el TXT oficial de la DGII.** Útil cuando toque contabilidad |

### ⛔ Lo que NO sirve

- `indexa-git/l10n-dominicana` (109★, el estándar de facto de Odoo) — **solo NCF y muerto desde ene-2025.**
- `angelpimentell/python-dgii-signer` — el único firmador Python, **sin licencia y muerto** (feb-2025).
- `rob-erply/dgii_facturacion_electronica` — el repo **da 404**. Lo que el doc 03 citaba como referencia de Odoo 18 ya no es verificable.
- `jeiyel/*-sdk-dotnet` — su README admite que **no tiene código**.

---

## 3. El patrón: cómo construyen las localizaciones fiscales maduras de Frappe

Se estudiaron 9. Las tres que valen: **KSA/ZATCA** (mejor arquitectura),
**India/GST** (únicos con tests reales), **México/CFDI** (única MIT, y la única
de la que puedes copiar código).

### 3.1 La lección que más ahorra: crea un DocType para el documento electrónico

| App | Qué hace |
|---|---|
| **KSA** | `Sales Invoice Additional Fields` — **submittable** |
| **India** | `e-Invoice Log` — `autoname: field:irn` |
| **México** | ❌ **Nada.** Mete el XML en custom fields de Sales Invoice |

👉 **Sigue a KSA e India, no a México.** Meter el XML en custom fields de la
factura te cuesta: pierdes el `docstatus` como máquina de estados, no puedes
reintentar limpio, y **no puedes representar la Anulación ni la Aprobación
Comercial como documentos propios** — que en RD son XML separados con su propio
ciclo.

### 3.2 Enganche a Sales Invoice — `doc_events`, no override de clase

| Escuela | Quién | Veredicto |
|---|---|---|
| `doc_events` en `hooks.py` | KSA, India, Guatemala, Argentina, RD | ✅ **Este** |
| `override_doctype_class` | México, Chile | ❌ Solo **una app** puede reclamar cada DocType. Colisiona con cualquier otra localización o personalización del cliente |

Las tres además ponen botones con `doctype_js` + un método `@frappe.whitelist()`.

### 3.3 Envío asíncrono — el detalle que separa lo serio de lo frágil

**KSA tiene el mejor patrón. Cópialo:**

```python
frappe.enqueue(
    _submit_additional_fields,
    doc=ecf_doc,
    enqueue_after_commit=True,   # ⭐ el detalle crítico
)
```

`enqueue_after_commit=True` hace que el job **solo corra si el submit de la
factura hizo commit**. Sin eso, encolas e-CF de facturas que nunca existieron.

Lo demás que hace bien KSA:
- Lotes de 100, `deduplicate=True` con `job_id`
- **Paginación por `creation` datetime, no por offset numérico** — su propio
  código explica por qué: los registros cambian de estado y un offset se salta
  documentos
- `frappe.db.commit()` por documento, `rollback()` en excepción
- **El `docstatus` nativo como máquina de estados:** draft = pendiente o
  reintento, submitted = terminal. Si la DGII dice "reenviar", **se queda en
  draft** y lo recoge el siguiente batch
- Devuelve `Result`/`Ok`/`Err` en vez de propagar excepciones desde un job

**India** complementa con cron `*/5 * * * *` buscando estado `Auto-Retry`.

⚠️ **México, Guatemala, Argentina y Ecuador son 100% síncronos.** Timbran dentro
del `on_submit`, en el hilo de la petición. **No copies eso** — es exactamente lo
que rompe la regla de "el POS nunca espera a la DGII".

### 3.4 Contingencia — solo una de las nueve la resuelve

**KSA: `ZATCA Precomputed Invoice`.** Campos: `invoice_counter`, `invoice_uuid`,
`previous_invoice_hash`, `invoice_hash`, `invoice_qr`, `invoice_xml`,
`device_id`. Un POS offline **pre-computa y pre-firma** el XML con su propio
dispositivo; al sincronizar, el sistema detecta el precomputado y lo usa en vez
de generar uno nuevo. Tiene `on_trash` que lanza excepción: **no se puede
borrar**.

👉 **En RD esto no es opcional.** Es el patrón para el modo contingencia de la
DGII, y ya está inventado.

### 3.5 Certificado y credenciales

**La regla que repiten todas las maduras:**
- Fieldtype **`Password`** para todo secreto (nunca `Data`)
- **`Attach`** para el binario del `.p12`
- Cargar el signer **en memoria**, nunca cachear la clave desencriptada

**India va más lejos:** enmascara secretos en los logs
(`mask_sensitive_info`). Es lo más avanzado del conjunto y encaja con la
disciplina de PII de KORVIS.

⚠️ **Guatemala guarda `llave_pfx`, `clave` y `usuario` como `Data`** — legibles
en la BD y en la API REST. Antipatrón claro.

### 3.6 Generación del XML — ninguna usa print format

| Técnica | Quién |
|---|---|
| **Jinja2 con el entorno de Frappe** | KSA |
| Librería con modelo de objetos | México (`satcfdi`) |
| dict → XML (`xmltodict`) | Guatemala |
| XAdES-BES a mano (`lxml`) | Ecuador |

**Para RD: Jinja2**, patrón KSA. El e-CF tiene esquema fijo; una plantilla por
tipo queda legible y versionable.

⚠️ Detalle que KSA documenta y que rompe XML si se ignora: hay que poner
`env.lstrip_blocks = env.trim_blocks = True` **y restaurarlos en un `finally`**,
porque el entorno Jinja es compartido con todo Frappe.

Los print formats se reservan para la **Representación Impresa** (el PDF con QR).

### 3.7 Custom fields — directorio `custom/`, no fixtures

| Estrategia | Quién | Veredicto |
|---|---|---|
| **Directorio `custom/*.json`** | KSA | ✅ **El más limpio.** Mecanismo nativo: se sincronizan solos en `bench migrate`, sin hook `fixtures` ni `after_install` |
| `fixtures` filtrados por módulo | México, RD, Argentina | Funciona, un paso más |
| Programático desde `after_install` | India | Control fino, mucho más pesado |

👉 Esto **corrige** lo que decía `docs/06-COMO-SE-TRABAJA.md`: el directorio
`custom/` es mejor que `export-fixtures` para campos que son parte del producto.
`export-fixtures` sigue sirviendo para lo que se configura en la UI.

### 3.8 Tests — solo India tiene de verdad

- **India ✅** — 76 archivos `test_*.py`. Patrón: `IntegrationTestCase` de Frappe
  + **`responses`** para mockear el HTTP + **`time_machine`** para vencimientos
  + `@change_settings(...)` + `before_tests` que crea la company de prueba. CI
  con server-tests, linters y CodeQL.
- **KSA ❌** — sus 8 `test_*.py` son stubs de 9 líneas.
- **México ❌ · Guatemala ❌** — stubs.

> **La arquitectura madura y los tests maduros no van juntos en este ecosistema.**
> Toma la estructura de KSA y la disciplina de pruebas de India. En una app
> fiscal, un bug silencioso cuesta multas.

---

## 4. La estructura recomendada para el módulo `ecf`

Destilado de las tres maduras. **Reemplaza el borrador de `docs/04-ARQUITECTURA.md`.**

```
korvexcio/ecf/
├── doctype/
│   ├── dgii_settings/              # ambiente (TesteCF/CerteCF/eCF), URLs, timeouts,
│   │                               #   live_sync on/off, proveedor activo
│   ├── dgii_digital_certificate/   # ← patrón México
│   │     certificate  Attach       #   el .p12
│   │     password     Password     #   ⚠️ NUNCA Data
│   │     company      Link
│   │     valid_until  Date         #   + aviso de vencimiento en validate()
│   ├── secuencia_encf/             # ← patrón dgii-compliance
│   │     tipo_ecf, desde, hasta, siguiente, fecha_vencimiento, company
│   ├── ecf/                        # ⭐ EL DOCUMENTO. Submittable
│   │     sales_invoice      Dynamic Link   # Sales Invoice / POS Invoice
│   │     encf              Data
│   │     track_id          Data            # lo que devuelve la DGII
│   │     codigo_seguridad  Data
│   │     signed_xml        Long Text
│   │     qr_url            Small Text
│   │     estado            Select          # Pendiente/Enviado/Aceptado/
│   │                                       #   Aceptado Condicional/Rechazado/
│   │                                       #   En Proceso/Reenviar/Contingencia
│   │     attempt_count     Int
│   │     validation_messages Small Text
│   ├── ecf_integration_log/        # ← patrón KSA: http_status, request, response
│   ├── ecf_contingencia/           # ← patrón ZATCA Precomputed Invoice
│   └── acecf/                      # aprobación comercial recibida
├── providers/
│   ├── base.py                     # emitir · consultar · anular
│   ├── alanube.py                  # vía wilmerm/alanube-python (MIT, Python)
│   └── ssd.py                      # vía ecf-dgii
├── templates/
│   ├── ecf_31.xml   ecf_32.xml   ecf_34.xml   rfce.xml    # Jinja2
└── print_format/                   # Representación Impresa con QR
```

```python
# hooks.py
doc_events = {
    "Sales Invoice": {
        "validate":      "korvexcio.ecf.overrides.sales_invoice.validate",      # RNC, ITBIS
        "before_submit": "korvexcio.ecf.overrides.sales_invoice.assign_encf",   # reserva secuencia
        "on_submit":     "korvexcio.ecf.overrides.sales_invoice.create_ecf",
        "before_cancel": "korvexcio.ecf.overrides.sales_invoice.prevent_cancel",
    },
    "POS Invoice": { ... },   # los mismos
}

doctype_js = {"Sales Invoice": "public/js/sales_invoice.js"}

scheduler_events = {
    "cron": {
        "*/5 * * * *":  ["korvexcio.ecf.tasks.retry_pending"],
        "*/15 * * * *": ["korvexcio.ecf.tasks.poll_status"],
        "0 */6 * * *":  ["korvexcio.ecf.tasks.refresh_token"],
    }
}

before_tests = "korvexcio.tests.before_tests"
```

⚠️ **Regla de RD que ninguna de las nueve tiene:** una factura con e-CF
**aceptado no se cancela — se anula** con un e-CF de anulación. El
`before_cancel` tiene que impedirlo.

---

## 5. Qué cambia respecto a los documentos anteriores

| Antes decía | Ahora | Por qué |
|---|---|---|
| `ecf-dgii` (PyPI) es el candidato #1 | **`wilmerm/alanube-python` es el #1**, `ecf-dgii` el #2 | Alanube documenta los 10 tipos; el PyPI de SSD no documenta E32 ni RFCE |
| RFCE sin confirmar en ningún lado | **`victors1681/dgii-ecf` (MIT) reporta `sendSummary` y `convertECF32ToRFCE`** | Existe implementación de referencia legal para portar |
| Custom fields vía `export-fixtures` | **Directorio `custom/*.json`** para lo que es del producto | Patrón KSA: se sincroniza solo en `bench migrate` |
| Estructura de DocTypes "a diseñar" | **Estructura destilada de 3 localizaciones en producción** | Ya no se diseña desde cero |
| `rob-erply` como referencia de Odoo 18 | **El repo da 404** | Retirado |

---

## 6. Los huecos del ecosistema — y qué significan

1. **Ninguna librería Python hace e-CF directo a la DGII.** Confirma que la
   decisión #2 era la correcta.
2. **No hay app Frappe con e-CF de RD.** `korvexcio` sería **la primera.**
3. **No existe repo público con los XSD oficiales + XML golden de prueba.** Cada
   implementación reinventa sus fixtures. *Sacar eso a público sería la carta de
   presentación técnica más barata que Korvex puede publicar — y el `ROADMAP.md`
   ya pide sacar repos a público.*
4. **Cero plugins de e-commerce con NCF/e-CF.** WooCommerce, Shopify, Magento:
   nada.
5. **No hay librería de 606/607/608 instalable con `pip`.**
6. **Nada de Representación Impresa conforme a la especificación.**

---

## Fuentes

Repos RD: [victors1681/dgii-ecf](https://github.com/victors1681/dgii-ecf) ·
[wilmerm/alanube-python](https://github.com/wilmerm/alanube-python) ·
[platinum-place/laravel-dgii](https://github.com/platinum-place/laravel-dgii) ·
[platinum-place/php-dgii-xml-signer](https://github.com/platinum-place/php-dgii-xml-signer) ·
[LewisMojica/dgii-compliance](https://github.com/LewisMojica/dgii-compliance) ·
[SSD/ecf_dgii](https://github.com/SSD-Smart-Software-Development-SRL/ecf_dgii) ·
[franklinmdev/dgii-ts](https://github.com/franklinmdev/dgii-ts) ·
[JoelStalin/easycount-legacy](https://github.com/JoelStalin/easycount-legacy) ·
[nexo-do/aura-node](https://github.com/nexo-do/aura-node) ·
[eriktaveras/facturas-opensource](https://github.com/eriktaveras/facturas-opensource) ·
[indexa-git/l10n-dominicana](https://github.com/indexa-git/l10n-dominicana)

Localizaciones Frappe: [lavaloon-eg/ksa_compliance](https://github.com/lavaloon-eg/ksa_compliance) ·
[resilient-tech/india-compliance](https://github.com/resilient-tech/india-compliance) ·
[TI-Sin-Problemas/erpnext_mexico_compliance](https://github.com/TI-Sin-Problemas/erpnext_mexico_compliance) ·
[sihaysistema/factura_electronica_gt](https://github.com/sihaysistema/factura_electronica_gt) ·
[beebtech-net/erpnext_ec](https://github.com/beebtech-net/erpnext_ec) ·
[finbyz/argentina_compliance](https://github.com/finbyz/argentina_compliance)
