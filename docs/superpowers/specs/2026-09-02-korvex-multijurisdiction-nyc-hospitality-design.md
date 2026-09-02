# D22 — Arquitectura multi-jurisdicción y vertical Hospitality NYC

**Fecha:** 2026-09-02
**Estado:** aprobado por Yedin para planificación
**Prioridad:** demo de bar/discoteca en NYC en dos semanas
**Código:** una sola app Korvex; un site y una base por cliente

## 1. Objetivo

Extender Korvex para vender el mismo software a negocios de países y verticales
distintos sin que las reglas de uno puedan activarse en otro. El primer caso nuevo
será un demo con datos ficticios para un bar/discoteca que abrirá en New York City.

Esto no crea dos programas ni un fork por país. La app, sus actualizaciones y el
repositorio siguen siendo uno. Cada cliente recibe una edición determinada por un
perfil de tenant validado exclusivamente por el servidor.

```text
Una app Korvex
├── site VAPELAND        → DO-RD + retail regulado + DGII
├── site cafetería       → DO-RD + café, cuando se reactive
└── site nightlife-demo  → US-NY-NYC + hospitality + alcohol 21+
```

## 2. Decisiones de arquitectura

### D22.1 — Cliente distinto significa site distinto

Cada dueño o entidad cliente vive en un site Frappe con base de datos, usuarios,
configuración, backups y ciclo de vida propios. Varias `Company` solo comparten un
site cuando pertenecen al mismo cliente.

Los sites pueden compartir bench, servidor y versión de la app. Separar el site no
duplica código: duplica únicamente la frontera de datos. Esto permite restaurar,
exportar, facturar o retirar un cliente sin tocar a los demás.

### D22.2 — `Tenant Profile` es la fuente de verdad

Cada site tendrá exactamente un perfil creado por el proceso de provisioning con:

- `client_id` interno inmutable;
- `country`, `region` y `locality` en códigos canónicos;
- `vertical`: `regulated_retail`, `cafe` o `hospitality`;
- moneda y zona horaria;
- `compliance_pack` derivado por el servidor;
- estado `draft`, `validated`, `active` o `blocked`;
- versión de política aplicada y marca de auditoría.

El frontend no puede elegir `country`, `vertical` ni `compliance_pack`. Tampoco se
aceptan desde body, query, URL ni campos que mande un importador. Provisioning
recibe una intención administrativa, la valida contra una allow-list del backend y
persiste el resultado derivado.

Al activar el site, los campos de jurisdicción quedan congelados. Cambiarlos exige
una migración administrativa explícita y auditada; un cambio de entidad o país
normalmente crea un site nuevo.

### D22.3 — Matriz cerrada de paquetes compatibles

La combinación de jurisdicción y vertical se resuelve con un registro cerrado:

| Perfil | Paquetes permitidos | Paquetes prohibidos |
|---|---|---|
| `DO-RD + regulated_retail` | retail, DGII/e-CF, RNC, edad configurada para RD | NY sales tax, NY alcohol |
| `DO-RD + cafe` | retail base, recetas/BOM, fiscal RD cuando corresponda | NY sales tax, NY alcohol |
| `US-NY-NYC + hospitality` | mesas, bar tabs, alcohol 21+, tax profile NYC, tips | DGII/e-CF, RNC, secuencias eNCF |

No existe fallback. Perfil ausente, combinación desconocida, paquete cruzado o
versión de política incompatible dejan el site en `blocked`. Es preferible que el
onboarding pare a que configure silenciosamente el país equivocado.

El código de módulos no activos puede estar instalado como parte de la app, pero
queda inaccesible, sin configuración, sin jobs y sin ejecutar reglas de negocio.

### D22.4 — Dos capas de seguridad

1. **Entre clientes:** base separada por site. Una query defectuosa no puede cruzar
   físicamente a otro cliente.
2. **Dentro del site:** el `Policy Resolver` obtiene el perfil desde el servidor en
   cada operación sensible y aplica default-deny. Nunca confía en un selector UI.

Toda operación fiscal o regulada declara el paquete que necesita. Ejemplos:

- emitir e-CF exige `do_dgii` y rechaza un site `US-NY-NYC`;
- cerrar alcohol exige `us_ny_alcohol` y una verificación 21+ válida;
- crear una mesa exige `hospitality`;
- jobs fiscales consultan la política antes de procesar documentos;
- menús, roles y onboarding muestran únicamente módulos autorizados.

## 3. Vertical `hospitality`

El vertical será un módulo nuevo; no se implementará dentro de `retail/cafe.py`.
ERPNext sigue siendo la base contable y `Sales Invoice` el documento final de venta.

### Modelo operativo

- **Hospitality Settings:** Company, ubicación, moneda, zona horaria, perfil fiscal
  validado y banderas del demo.
- **Venue Area:** salón, barra, patio o sección VIP.
- **Venue Table:** código, área, posición visual y estado operativo. Su capacidad no
  representa ni certifica aforo legal.
- **Server Profile:** usuario Frappe y código visible usado para atribuir mesa,
  ventas y propinas. El código no autentica ni sustituye la sesión.
- **Bar Tab:** cuenta abierta con numeración secuencial, mesa, mesero, terminal,
  ítems y snapshots de precios/impuestos.
- **Compliance Event:** historial append-only de verificación/rechazo de edad,
  transferencia de mesa, cambio de mesero, descuento, void, refund y override.
- **Tip Ledger:** propina voluntaria, gratificación automática y distribución por
  mesero/turno como conceptos separados.

Un `Bar Tab` cerrado es inmutable. Corregirlo crea un evento y el documento contable
correspondiente; nunca se reescribe la historia. Un tab puede dividirse por ítems o
montos y producir una o varias facturas enlazadas.

### Flujo del demo

1. Login Korvex y apertura de turno.
2. Plano vivo con mesas libres, abiertas, por cerrar, VIP y barra.
3. Tocar una mesa, asignar mesero por código y abrir/reanudar el tab.
4. Agregar botellas y bebidas desde un menú ficticio.
5. Antes del cierre con alcohol, registrar `21+ verificado` o `venta rechazada`.
6. Dividir la cuenta cuando corresponda.
7. Calcular subtotal, sales tax de demo, gratificación automática opcional y
   propina voluntaria adicional como líneas distintas.
8. Marcar pago ficticio `cash demo` o `card demo`; no capturar datos de tarjeta.
9. Cerrar el tab y generar recibo, factura y eventos auditables.
10. Mostrar cierre nocturno por mesa, mesero, método, impuesto y propinas.

### Lo que no entra al demo

- pagos, preautorizaciones o tarjetas reales;
- nómina, cálculo de tip credit o distribución bancaria;
- KDS, cocina, recetas, reservas, delivery o cover online;
- fotos, escaneos o números de identificación;
- migración histórica, hardware o soporte nocturno;
- certificación de licencia SLA, zoning, aforo, impuestos o cumplimiento legal.

## 4. Reglas NYC que condicionan el software

- Alcohol requiere 21 años y rechazo a personas visiblemente intoxicadas. El demo
  guarda la decisión, el mesero, el momento y el método; no guarda el documento.
- Cada transacción debe conservar detalle suficiente para reconstruir ítems,
  precios, impuesto, fecha, pago, terminal y número de transacción.
- Ventas se diseñan para retención y exportación auditable mínima de tres años.
- Tip pools/shares se diseñan para seis años de trazabilidad por empleado y turno.
- El sales tax es configuración versionada por ubicación. El demo usa 8.875% para
  NYC con una etiqueta que exige confirmación de CPA antes de producción.
- Propina voluntaria, gratificación automática y service charge son tipos distintos.
  El demo incluye las dos primeras; no incluye service charge.
- Si en el futuro se almacena información privada, aplican salvaguardas del SHIELD
  Act. La minimización de datos es el control inicial.

Fuentes primarias consultadas:

- NYS Tax, recordkeeping POS:
  https://www.tax.ny.gov/pubs_and_bulls/tg_bulletins/st/record-keeping_requirements_for_sales_tax_vendors.htm
- NYS Tax, restaurantes y gratuities:
  https://www.tax.ny.gov/pubs_and_bulls/tg_bulletins/st/sales_by_restaurants.htm
- NYS ABC Law §65 y §65-b:
  https://www.nysenate.gov/legislation/laws/ABC/65
  https://www.nysenate.gov/legislation/laws/ABC/65-B
- NYS Hospitality Wage Order:
  https://forms.labor.ny.gov/WP/CR146.pdf
- NY Attorney General, SHIELD Act:
  https://ag.ny.gov/resources/organizations/data-breach-reporting/shield-act
- NYC Finance, sales tax:
  https://www.nyc.gov/site/finance/business/business-nys-sales-tax.page

La app facilita controles y evidencia; abogado de NY, CPA/payroll y autoridades
validan licencia, configuración fiscal, employment/tips, zoning y producción.

## 5. Seguridad y pruebas obligatorias

### Matriz negativa de onboarding

- `US-NY-NYC + hospitality` nunca crea configuración DGII, RNC ni secuencias eNCF.
- `DO-RD + regulated_retail` nunca activa NY alcohol ni tax profile NYC.
- Perfil ausente, manipulado o con combinación no permitida bloquea activación.
- Enviar jurisdicción por request no altera la política efectiva.
- Un Manager del site no puede cambiar jurisdicción ni vertical.
- Un job DGII ejecutado en el site NYC termina sin procesar documentos y deja evento
  de seguridad; una llamada DGII explícita es rechazada.

### Aislamiento y autorización

- API directa del site A jamás devuelve filas del site B.
- Dentro del site, mesa, tab, factura y eventos filtran por Company autorizada.
- Cajero/mesero no puede reasignar Company, borrar eventos ni alterar un tab cerrado.
- Solo Manager puede void/refund/override, siempre con razón y auditoría.
- El código visible de mesero nunca autoriza acciones.

### Escenarios end-to-end del demo

- abrir mesa, agregar botella, verificar 21+, dividir y cerrar;
- rechazar alcohol sin verificación o con decisión `refused`;
- aplicar auto-gratuity y propina voluntaria sin mezclarlas;
- transferir mesa/mesero preservando historial;
- void/refund deja el ticket original intacto;
- recibo y export contienen campos fiscales/auditables esperados;
- smoke responsive en 1440×900, 840×760 y 375×812;
- VAPELAND conserva e-CF, RNC y sus pruebas sin regresión.

## 6. Demo, comercialización y límites

La oferta inicial se vende como `Founding Partner`, no como POS productivo:

- discovery + demo personalizado: **US$750**;
- onboarding de piloto: **US$1,500**, acreditando los US$750 si avanza;
- piloto: **US$299/mes por 12 meses**, un local y soporte asíncrono;
- producción con pagos reales: nuevo SOW desde **US$499/mes**, más hardware,
  procesamiento e integraciones del proveedor.

Comparables oficiales consultados:

- Square Restaurants: https://squareup.com/us/en/point-of-sale/restaurants/pricing
- Toast: https://pos.toasttab.com/pricing
- Lightspeed Restaurant: https://www.lightspeedhq.com/pos/restaurant/

El contrato del demo debe decir: datos ficticios, sin pagos reales, sin SLA nocturno,
sin sustitución del POS del negocio y sin declaración de cumplimiento.

## 7. Orden de entrega en dos semanas

1. Cerrar el microslice visual S4.UI.1 ya escrito y aislar su commit.
2. Implementar `Tenant Profile`, registro de políticas y tests fail-closed.
3. Crear el site demo NYC y probar que DGII queda imposible de activar.
4. Implementar modelo hospitality y permisos con tests de negocio/aislamiento.
5. Implementar plano vivo, tabs, edad 21+, split y cierre ficticio.
6. Agregar auditoría, tips, recibo, exportación y cierre nocturno.
7. Ejecutar suite backend, build/lint frontend, smoke responsive y regresión RD.
8. Preparar datos ficticios, guion comercial y walkthrough del demo.

Cada punto se parte en microslices verificables antes de implementación. No se
mezcla cafetería, pagos ni hardware para alcanzar la demostración en dos semanas.

## 8. Supuestos bloqueantes para pasar a producción

- entidad y ubicación legal exactas del bar;
- licencia SLA, Certificate of Occupancy y permisos aplicables;
- revisión de abogado NY y CPA/payroll;
- procesador, terminales y alcance PCI;
- política escrita de edad/intoxicación y capacitación del personal;
- reglas finales de gratuity/tip pool, taxes y retención;
- soporte, monitoreo, backup restaurado y respuesta a incidentes.

Ninguno bloquea el demo ficticio. Todos bloquean afirmar `production-ready`.
