# Fase 3 Retail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar el módulo Retail de KORVEXCIO en seis slices verificables: atributos configurables, FEFO, verificación de edad, cafetería de mostrador, reportes aislados por Company y dashboard consolidado.

**Architecture:** La app `korvexcio` extenderá ERPNext mediante DocTypes propios, hooks y reportes, sin editar upstream. La configuración específica del negocio vivirá en el site y el servidor derivará siempre la Company autorizada desde la sesión/permisos; los reportes propios recibirán y filtrarán `company` explícitamente.

**Tech Stack:** Frappe/ERPNext v16 instalado en el bench, Python, MariaDB, DocTypes estándar de Item/Batch/BOM/Sales Invoice y tests `IntegrationTestCase`.

**Spec:** `docs/08-BLUEPRINT.md` §6, Fase 3, S3.1–S3.6.

## Global Constraints

- Upstream no se toca; todo cambio va dentro de `korvexcio/` o configuración versionada.
- Un default del vertical no puede activarse en un site limpio; se habilita por configuración del site.
- Toda operación con Company filtra explícitamente por `company`; no usar `ignore_permissions=True` ni `frappe.db.sql()` crudo.
- Datos de edad/identidad, si se persisten, usan AES-256-GCM con IV por registro y nunca aparecen completos en logs.
- Cada slice termina con tests ejecutados, documentación en `PROGRESO.md` y `HANDOFF.md`, y un commit propio.

---

### Task 1: S3.1 — atributos configurables del vertical

**Files:**
- Create: `korvexcio/retail/item_attributes.py`
- Create: `korvexcio/retail/test_item_attributes.py`
- Create: `korvexcio/retail/site_config.py`
- Modify: `korvexcio/hooks.py`
- Modify: `korvexcio/install.py`

**Deliverable:** una configuración opt-in del site que crea `Item Attribute` para Sabor, Nicotina (mg), Tamaño (ml) y Ohmiaje, además de una utilidad para crear un Item Template y sus variantes usando APIs de Frappe. Un site limpio no crea esos atributos.

- [ ] Test de site limpio: `retail_vertical_enabled` ausente o falso no crea atributos.
- [ ] Test opt-in: la configuración habilitada crea los cuatro atributos con valores permitidos y es idempotente.
- [ ] Test de variantes: un template con dos combinaciones crea variantes y conserva los atributos.
- [ ] Ejecutar la suite específica y luego la suite completa del app.
- [ ] Documentar evidencia, decisión y deuda; commit `feat: add configurable retail item attributes`.

### Task 2: S3.2 — FEFO y alertas de vencimiento

**Files:**
- Create: `korvexcio/retail/fefo.py`
- Create: `korvexcio/retail/test_fefo.py`
- Modify: `korvexcio/hooks.py`

**Deliverable:** selección de lotes por fecha de vencimiento ascendente, ignorando lotes agotados y vencidos según la política configurada, más alertas 90/60/30 días.

- [ ] Test con dos lotes verifica que se elige primero el que vence antes.
- [ ] Test de agotado/vencido verifica que no se recomiende inventario inválido.
- [ ] Test de alertas verifica exactamente los umbrales 90, 60 y 30.
- [ ] Ejecutar tests y lint; documentar y commit `feat: add FEFO batch selection and expiry alerts`.

### Task 3: S3.3 — verificación de edad y protección de PII

**Files:**
- Create: `korvexcio/retail/age_verification.py`
- Create: `korvexcio/retail/test_age_verification.py`
- Create or modify: `korvexcio/custom/customer.json`
- Modify: `korvexcio/hooks.py`
- Modify: `.env.example`

**Deliverable:** validación server-side de edad para Items cuyo `Item Group` esté marcado, con almacenamiento cifrado solo si el flujo necesita conservar el dato. La llave se lee del entorno; el ciphertext incluye IV único por registro y el logger enmascara cédulas/teléfonos.

- [ ] Test de item regulado sin verificación rechaza el cierre.
- [ ] Test de item no regulado no exige edad.
- [ ] Test criptográfico verifica que DB no contiene la cédula plana y que dos cifrados del mismo valor tienen IV/ciphertext distintos.
- [ ] Ejecutar `/security-review` o el equivalente disponible y registrar salida real.
- [ ] Documentar y commit `feat: protect age verification data`.

### Task 4: S3.4 — cafetería de mostrador y recetas

**Files:**
- Create: `korvexcio/retail/cafe.py`
- Create: `korvexcio/retail/test_cafe.py`
- Modify: `korvexcio/install.py`

**Deliverable:** seed opt-in para catálogo de cafetería y utilidad de creación de BOM/receta, usando DocTypes estándar de ERPNext para que una venta de producto terminado descuente insumos.

- [ ] Test verifica que el seed apagado no crea catálogo.
- [ ] Test opt-in crea producto terminado, insumos y BOM idempotente.
- [ ] Test de movimiento verifica que la receta reduce insumos al vender/entregar el producto.
- [ ] Ejecutar tests, documentar y commit `feat: add counter-service cafe recipes`.

### Task 5: S3.5 — reportes del dueño aislados por Company

**Files:**
- Create: `korvexcio/retail/report/stock_muerto/stock_muerto.json`
- Create: `korvexcio/retail/report/stock_muerto/stock_muerto.py`
- Create: `korvexcio/retail/report/margen_categoria/margen_categoria.json`
- Create: `korvexcio/retail/report/margen_categoria/margen_categoria.py`
- Create: `korvexcio/retail/report/rotacion/rotacion.json`
- Create: `korvexcio/retail/report/rotacion/rotacion.py`
- Create: `korvexcio/retail/report/venta_del_dia/venta_del_dia.json`
- Create: `korvexcio/retail/report/venta_del_dia/venta_del_dia.py`
- Create: `korvexcio/retail/report/test_reports.py`

**Deliverable:** cuatro Script Reports que usan APIs de Frappe, reciben `company`, devuelven columnas estables y nunca mezclan las dos Companies.

- [ ] Tests con datos A/B verifican que cada reporte devuelve solo la Company solicitada.
- [ ] Test default-deny verifica que falta de Company no devuelve datos de negocio.
- [ ] Ejecutar suite de reports y suite total; documentar y commit `feat: add company-scoped retail reports`.

### Task 6: S3.6 — dashboard consolidado del dueño

**Files:**
- Create: `korvexcio/retail/dashboard.py`
- Create: `korvexcio/retail/test_dashboard.py`
- Create: `korvexcio/retail/page/retail_owner_dashboard/retail_owner_dashboard.json`
- Create: `korvexcio/retail/page/retail_owner_dashboard/retail_owner_dashboard.py`
- Create: `korvexcio/retail/page/retail_owner_dashboard/retail_owner_dashboard.js`
- Modify: `korvexcio/hooks.py`

**Deliverable:** página server-backed para el rol Dueño que consolida venta del día, caja, stock por vencer y e-CF pendientes de sus Companies permitidas; cajeros quedan fuera o reciben solo su Company.

- [ ] Test de autorización rechaza Cajero y permite Dueño.
- [ ] Test de datos verifica las dos Companies del Dueño y ausencia de Company ajena.
- [ ] Test de e-CF pendientes reutiliza la consulta segura existente sin bypass de permisos.
- [ ] Ejecutar tests, lint y verificación HTTP/UI disponible; documentar y commit `feat: add consolidated owner dashboard`.

## Self-review

- S3.1 cubre la configuración apagada por defecto y las variantes.
- S3.2 cubre selección FEFO y las tres alertas.
- S3.3 cubre servidor, cifrado, IV y redacción.
- S3.4 cubre catálogo, BOM y descuento de insumos.
- S3.5 cubre los cuatro reportes y aislamiento explícito.
- S3.6 cubre autorización y consolidación multi-Company.
- No se incluye POS, hardware, proveedor e-CF ni certificación: pertenecen a Fases 2, 4 y 5.
