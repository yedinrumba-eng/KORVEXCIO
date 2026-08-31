# 05 — Preguntas para el cliente

> Llevar esto a la reunión. Cada pregunta sin responder es una decisión que
> alguien va a tomar por él — y probablemente mal.
>
> Las 🔴 **bloquean el camino crítico** (e-CF antes del 15/11/2026).

---

## 🔴 Bloqueantes — resolver esta semana

| # | Pregunta | Por qué bloquea |
|---|---|---|
| 1 | 🟡 **EN MOVIMIENTO (31/08)** — Yedin ya está hablando con el dueño para que registre la compañía y saque el RNC. Falta confirmar: ¿persona física o jurídica (SRL/EIRL)? ¿fecha estimada? | **Sin RNC no hay e-CF.** Sigue siendo el bloqueante #1 hasta que esté en mano. |
| 2 | **¿Tiene certificado digital?** Si no: hay que sacarlo ya — 3 a 10 días hábiles, US$30–70/año. | Sin certificado no se firma nada. Es tiempo de calendario que no se puede comprimir. |
| 3 | **¿Cómo está clasificado ante la DGII?** Pequeño, micro, o no clasificado. | Define si su fecha es el **15/11/2026** o el **1/11/2026**. |
| 4 | **¿Tiene contador?** Necesitamos hablar con él. | El motor de impuestos se modela con lo que diga el contador, no con lo que asuma un dev. |
| 5 | **¿Va a estar en RST** (Régimen Simplificado)? | Cambia cómo se liquida el ITBIS. |
| 6 | **¿Fecha real de apertura de la tienda?** | Define si corremos contra la apertura o contra el 15/11. |

---

## 🟠 Definen el alcance

| # | Pregunta |
|---|---|
| 7 | **La cafetería: ¿qué es exactamente?** ¿Solo café y bebidas de mostrador, o comida preparada con mesas y meseros? ¿Abre al mismo tiempo que la tienda o después? |
| 8 | **¿Una sola caja o varias?** ¿Caja separada para la cafetería o una sola para todo? |
| 9 | **¿Cuántos empleados van a usar el sistema?** ¿Qué debe poder hacer un cajero que no pueda hacer un empleado normal? (define el modelo de permisos, y el dimensionamiento del servidor) |
| 10 | **¿Una sola tienda o piensa abrir más?** Multi-sucursal cambia el diseño del inventario desde el día 1. |
| 11 | **¿Vende en línea o solo presencial?** ¿Delivery, WhatsApp, Instagram? |
| 12 | **El asistente de IA: ¿para qué exactamente?** ¿Responder horarios y disponibilidad? ¿Tomar pedidos? ¿Atender reclamos? Ver `ADAP/docs/CATEGORIAS-DE-NEGOCIO.md` — hay que agregarle una fila a este rubro. |

---

## 🟡 Definen el modelo de datos

| # | Pregunta | Por qué importa |
|---|---|---|
| 13 | **¿Cuántos productos distintos va a manejar?** ¿Tiene lista de proveedores o catálogo en Excel? | 500–1,000 SKUs es lo típico del rubro. Si tiene el catálogo en Excel, la carga inicial se automatiza. Si no, es semanas de digitación. |
| 14 | **¿Los productos traen código de barras del fabricante?** | Si no, hay que **imprimir etiquetas con SKU interno** — impresora de etiquetas adicional. |
| 15 | **¿Vende tabaco o carbón por peso / fraccionado?** (ej. caja de 250 g → porciones de 50 g) | Si sí, hace falta **conversión de unidades** y probablemente una **balanza**, no solo escáner. |
| 16 | **¿Los líquidos traen fecha de vencimiento?** ¿Le importa controlarla? | Define si se activa control por **lote** (más trabajo en recepción, pero evita vender líquido vencido). |
| 17 | **¿Compra por cartón y vende por unidad?** | Unidad de compra ≠ unidad de venta. Se configura desde el inicio o se arregla nunca. |
| 18 | **¿Va a dar crédito a clientes?** ¿Fiado? | Activa cuentas por cobrar. |
| 19 | **¿Quiere programa de puntos o fidelización?** | Post-MVP, pero define si se captura el cliente en cada venta. |

---

## 🟡 Operación y hardware

| # | Pregunta |
|---|---|
| 20 | **¿Qué medios de pago va a aceptar?** Efectivo, tarjeta (¿Azul o CardNet?), transferencia, tPago. |
| 21 | **¿Ya tiene datáfono?** ⚠️ Aclararle: lo normal es que el datáfono **no se integre** con el POS — se cobra en el terminal y se registra el monto. Integrarlo requiere hablar con el adquirente. **No prometerlo.** |
| 22 | **¿Qué computadora va a usar en la caja?** ¿PC, tablet, celular? |
| 23 | **¿Ya compró escáner e impresora térmica?** Si no, se le recomiendan modelos concretos. |
| 24 | **¿Cómo es el internet del local?** Fibra, 4G, respaldo. → **Define qué tan crítico es el modo offline.** En RD, la respuesta correcta es siempre "muy crítico". |
| 25 | **¿Quién va a hacer el inventario inicial?** ¿Cuándo? |

---

## 🟢 Producto y negocio

| # | Pregunta |
|---|---|
| 26 | **¿Sabe del ISC del 55% a los vapes** (Ley 30-26, junio 2026)? ¿Ya lo tiene en su estructura de costos? Puede cambiarle el margen de todo el rubro. |
| 27 | **¿Quiere verificación de edad en el POS?** ¿Solo un check del cajero o registrar la fecha de nacimiento? (Registrar implica manejo de datos personales.) |
| 28 | **¿Qué reportes quiere ver todos los días?** La respuesta a esto define el dashboard mejor que cualquier suposición nuestra. |
| 29 | **¿Está dispuesto a ser el cliente 1 de un producto?** Es decir: aceptar que va a encontrar bugs a cambio de un precio distinto. Conviene que sea explícito, no implícito. |

---

## Lo que Yedin tiene que decidir (no el cliente)

| # | Decisión |
|---|---|
| A | ✅ **RESUELTO 31/08** — El producto es **KORVEXCIO**. Yedin renombra la carpeta él mismo. Pendiente aparte: la carpeta de **KORVIS** sigue llamándose `ADAP` en disco (mismo error, sin resolver — va en `MUDANZA.md`). |
| B | **¿Se cerró la Parte 0 del `ROADMAP.md`?** (rotar `CLOUDFLARE_API_TOKEN`, arreglar el paging file). La regla del roadmap dice que nada entra a "construir" con algo en 🔴 abierto. |
| C | **¿Repo creado con remote antes del primer commit?** §6 de `CONVENCIONES.md`. DIGIVAL y FRAMERD ya lo violan. |
| D | ✅ **HECHO 31/08** — `korvexcio` en `data/korvex.json` (45 proyectos), SEED re-embebido en `index.html` y verificado, entrada en `BITACORA.md`. `korvex-assistant` renombrado a **KORVIS — AI Assistant by Korvex**. Quedaron `data/korvex.json.bak` e `index.html.bak` en `_KORVEX-OPS` — borrarlos tras verificar el mapa. |
| E | **¿ERPNext en el nodo 1 o VPS desde el inicio?** El nodo aguanta 1–2 sites junto a KORVIS. Al tercer cliente, no. |
| F | **¿Se revisa la decisión del MVP** (POS+inventario+e-CF, sin cafetería ni IA) **con el cliente antes de arrancar?** Él pidió las tres cosas. Marcado por Yedin para revisión. |
