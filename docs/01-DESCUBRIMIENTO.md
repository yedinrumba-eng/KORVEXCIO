# 01 — Descubrimiento: el negocio

> Sesión de descubrimiento 2026-08-31. Todo lo que aquí lleva ⚠️ **no está
> confirmado por el cliente** y hay que preguntarlo (`05-PREGUNTAS-CLIENTE.md`).

---

## Qué es VAPELAND

Un negocio **nuevo** (todavía no abierto) en República Dominicana, con dos
operaciones bajo el mismo techo:

| Operación | Qué vende |
|---|---|
| **Tienda** | Vapes y cigarrillos electrónicos · líquidos (con y sin nicotina) · artículos de hookah · tabaco · carbones · accesorios (resistencias, baterías, mangueras, pinzas, boquillas) |
| **Cafetería** | ⚠️ Alcance sin definir. ¿Solo café y bebidas? ¿Comida preparada? ¿Mesas y meseros o mostrador? |

Lo que pidió el cliente, en sus palabras: **ERP con POS adjunto**, panel de
manejo de **clientes y leads**, y engancharle el proyecto del **asistente de
IA**. Mencionó específicamente el **escáner de productos en el POS**.

Lo que pidió Yedin encima: que sea **multi-tenant** para venderlo a más
clientes como producto **KORVEX**, hosteado en su subdominio.

---

## Los dos negocios son dos POS distintos, no uno

Esta es la trampa del proyecto y conviene verla desde ahora.

| | Tienda (retail) | Cafetería (food service) |
|---|---|---|
| **Unidad de venta** | Producto con código de barras | Ítem de menú, a veces compuesto |
| **Flujo** | Escanear → cobrar → salir | Ordenar → preparar → servir → cobrar |
| **Estado intermedio** | No hay | Sí: comanda abierta, mesa ocupada |
| **Inventario** | Descuento 1:1 por SKU | Receta / lista de materiales (1 café = X gramos de grano + 1 vaso + tapa) |
| **Cocina** | No aplica | KDS o impresora de comanda |
| **Devolución** | Producto físico de vuelta | Prácticamente no existe |
| **Merma** | Rotura, robo, vencimiento | Desperdicio diario, sobras |

En ERPNext esto se resuelve con **dos POS Profiles** sobre la **misma
compañía y el mismo inventario**, no con dos sistemas. Pero el módulo de
restaurante (mesas, KDS, comandas) es una app aparte — ver `03-BENCHMARK`.

**Decisión tomada:** la cafetería queda **fuera del MVP**. La tienda paga las
cuentas primero. ⚠️ Marcado para confirmar con el cliente.

---

## Qué hace especial el inventario de un vape/smoke shop

Esto no es un colmado. Los números y patrones de la industria:

### Volumen de SKUs
Un smoke shop típico maneja **500–1,000 SKUs**, contra menos de 200 de una
boutique normal. La explosión viene de las variantes:

- Un líquido = **20+ sabores × 3–4 niveles de nicotina × 2 tamaños de botella**
- Desechables = marca × sabor × cantidad de puffs
- Resistencias = modelo × ohmiaje
- Hookah = cabeza, manguera, base, plato, pinza, boquilla, cada uno con marcas

👉 En ERPNext esto es **Item Variant + Item Attribute** (Sabor, Nicotina,
Tamaño). Cargar mal el catálogo al inicio es la muerte del proyecto: se hace
con plantillas, nunca a mano ítem por ítem.

### Productos sin código de barras del fabricante
Buena parte del inventario de hookah y accesorios **llega sin GTIN/EAN
impreso**, o con códigos que se repiten entre importadores. El POS necesita:

- Aceptar el código del fabricante cuando existe
- **Generar e imprimir etiquetas con SKU interno** cuando no existe
- Búsqueda rápida por nombre para lo que no tiene etiqueta

### Vencimiento y degradación
- **E-liquid: 1–2 años de vida útil.** Vender líquido viejo no genera una
  devolución, genera un cliente perdido.
- Tabaco saborizado **pierde humedad**.
- Los puros exigen humedad y temperatura controladas (65–70%).

👉 ERPNext: **Batch** con `expiry_date` + política **FEFO** (first expired,
first out). Alerta de vencimiento a 90/60/30 días.

### Venta a granel y por peso
⚠️ **Por confirmar:** el tabaco de hookah y el carbón se venden a veces por
peso o fraccionados (una caja de 250 g → porciones de 50 g). Si es el caso,
hay que modelar **UOM Conversion** (Caja → Gramo) y probablemente una
**balanza**, no solo un escáner.

### Cartón vs unidad
Los cigarrillos se compran por cartón y se venden por cajetilla. El error
clásico: el sistema registra 10 unidades de cartón y el cajero vende
cajetillas sueltas. **UOM de compra ≠ UOM de venta.** ERPNext lo maneja, pero
hay que configurarlo desde el primer día.

### Merma
Rotura de vidrio (hookahs, bases), robo hormiga en accesorios pequeños,
líquido vencido. Sin un flujo de **Stock Reconciliation** periódico y una
razón de ajuste, el inventario se separa de la realidad en 3 meses.

### Reportes que el dueño va a pedir
- Venta por categoría (¿vapes o hookah paga la renta?)
- Margen por producto y por proveedor
- **Stock muerto**: accesorios sin movimiento en 90+ días
- Producto por vencer
- Comparativa tienda vs cafetería

---

## Verificación de edad

En RD **no hay todavía una ley específica** que regule la venta de cigarrillos
electrónicos a menores — hay varios proyectos de ley sometidos desde 2022–2023
que no han sido aprobados. La Ley 30-26 (2026) los grava fiscalmente pero es
una ley tributaria, no sanitaria.

👉 **Recomendación:** construir el prompt de verificación de edad en el POS de
todas formas. Cuesta un día, protege al cliente, y el día que la ley pase el
sistema ya cumple. En ERPNext se resuelve con un flag por **Item Group** que
dispara una confirmación obligatoria en el POS.

⚠️ Confirmar con el cliente si quiere además **registrar** la verificación
(fecha de nacimiento, tipo de documento) o solo un check del cajero. Registrar
datos de identidad implica manejo de PII — misma disciplina que KORVIS.

---

## Métodos de pago en RD

| Medio | Qué implica para el POS |
|---|---|
| **Efectivo** | Turno de caja, fondo inicial, arqueo, diferencia |
| **Tarjeta (Azul / CardNet)** | ⚠️ El datáfono físico normalmente **no se integra**: el cajero cobra en el terminal y registra el monto en el POS. Integración real requiere hablar con el adquirente. |
| **Transferencia / tPago** | Registro manual con referencia |
| **Crédito a cliente** | Cuenta por cobrar — solo si el cliente lo pide |

⚠️ **No prometer integración con el datáfono sin confirmarlo con Azul/CardNet.**
Es el tipo de promesa que después cuesta un cliente.

---

## Lo que el cliente pidió y NO está en el MVP

No es un olvido, es una decisión. Pero hay que decírselo a él, no descubrirlo
él solo:

1. **La cafetería.** Requiere mesas, comandas, KDS y recetas. Es un producto
   dentro del producto.
2. **El panel de clientes y leads.** ERPNext trae CRM básico; Frappe CRM es
   una app aparte y madura.
3. **El asistente de IA por WhatsApp.** Existe y funciona (KORVIS), pero vive en
   otro stack. Se integra por API, en una fase posterior.
