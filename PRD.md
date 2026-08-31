# PRD — KORVEXCIO (cliente: VAPELAND)

> Versión 0.1 · 2026-08-31 · **Borrador de descubrimiento.**
> ⚠️ **Este documento NO ha sido validado con el cliente.** Todo lo marcado con
> ⚠️ es un supuesto de Yedin, no un acuerdo. Ver `docs/05-PREGUNTAS-CLIENTE.md`.

---

## El problema

Un negocio nuevo en RD que vende vapes, hookah, tabaco, carbones y accesorios,
con una cafetería adjunta, necesita:

1. Vender y cobrar rápido en mostrador
2. Saber qué tiene en inventario, entre 500 y 1,000 SKUs con variantes
3. **Facturar legalmente** — e-CF obligatorio desde el 15/11/2026

Y Korvex necesita que lo construido no sirva solo para este cliente.

## Para quién

| Usuario | Qué necesita |
|---|---|
| **Cajero** | Vender en menos de 30 segundos. Escanear, cobrar, imprimir. Sin pensar en impuestos. |
| **Dueño** | Saber qué se vendió, qué falta, cuánto se ganó, y qué no se está moviendo |
| **Contador** | Reportes 606/607, e-CF transmitidos y aceptados, cierre mensual |
| **Korvex** | Un producto vendible a otros negocios sin reescribirlo |

## Qué es el éxito

1. El cliente abre y **factura legalmente desde el día 1**
2. El cajero no necesita saber qué es un E31 ni un E32
3. El inventario refleja la realidad **sin conteo manual diario**
4. Cuando se cae el internet, **el negocio sigue vendiendo**
5. El segundo cliente se monta en **días, no meses**

---

## Alcance MVP

> ⚠️ **Marcado por Yedin para revisar con el cliente.** Él pidió cafetería y
> asistente de IA desde el inicio; se sacaron del MVP por decisión técnica.
> Es una conversación pendiente, no un hecho consumado.

### Dentro

| # | Requisito | Criterio de aceptación |
|---|---|---|
| R1 | POS de retail | Vender, cobrar (efectivo/tarjeta/transferencia), imprimir recibo, turno de caja con arqueo |
| R2 | Escáner de código de barras | Escanear agrega el ítem al carrito sin tocar el teclado |
| R3 | Catálogo con variantes | Un líquido con 20 sabores × 3 nicotinas se carga por plantilla, no ítem por ítem |
| R4 | Lotes y vencimiento | Alerta a 90/60/30 días. FEFO en la venta |
| R5 | Multi-almacén | Tienda y bodega separadas, con transferencias |
| R6 | **e-CF: E32, E31, E34, RFCE** | Venta emitida obtiene TrackID y queda aceptada por DGII |
| R7 | Recibo térmico con QR del e-CF | El QR resuelve en el verificador de la DGII |
| R8 | **Modo contingencia** | Sin internet el POS sigue vendiendo; al reconectar drena la cola sin perder ninguna venta |
| R9 | Control de secuencias e-NCF | Alerta cuando quedan menos de N disponibles |
| R10 | RNC obligatorio ≥ RD$250,000 | El POS lo exige solo, no depende del cajero |
| R11 | Verificación de edad | Confirmación obligatoria en ítems marcados |
| R12 | Reportes del dueño | Venta por categoría · margen por producto · stock muerto 90+ días · por vencer |

### Fuera del MVP — explícito

| Qué | Cuándo |
|---|---|
| Módulo de cafetería (mesas, KDS, comandas, recetas) | Fase 2 |
| CRM y panel de leads | Fase 2 |
| Asistente de IA por WhatsApp (integración con KORVIS) | Fase 3 |
| Fidelización, puntos, cupones, gift cards | Fase 3 |
| E-commerce / portal del cliente | Sin fecha |
| Integración con datáfono Azul/CardNet | ⚠️ **No prometer.** Requiere hablar con el adquirente |
| App móvil nativa | Sin fecha — el POS web responsive cubre el caso |

---

## Restricciones

| Restricción | Origen |
|---|---|
| **e-CF obligatorio el 15/11/2026** | Ley 32-23. No negociable |
| Base: **ERPNext/Frappe v15** | Decisión de Yedin, 2026-08-31 |
| e-CF vía **proveedor certificado** | Decisión de Yedin, 2026-08-31 |
| **No usar "ERPNext"/"Frappe"** en nombre de producto ni dominio | Marca registrada de Frappe Technologies |
| Hosting inicial en `korvex-node1` | 14 GB RAM, 84 GB libres, compartido con KORVIS |
| El cliente **no ha confirmado RNC** | ⚠️ Bloquea la certificación como emisor |

## Supuestos que hay que confirmar

1. ⚠️ El cliente tiene o va a tener RNC y registro mercantil
2. ⚠️ El ISC de vapes lo paga el importador, no el detallista (llega en el costo)
3. ⚠️ La cafetería es de mostrador, no de servicio de mesa
4. ⚠️ Una sola sucursal
5. ⚠️ No vende tabaco por peso fraccionado
6. ⚠️ El internet del local es inestable → offline es requisito duro
