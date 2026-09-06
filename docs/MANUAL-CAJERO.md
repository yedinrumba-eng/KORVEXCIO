# 📋 MANUAL DEL CAJERO — KORVEXCIO POS

> **Para cajeros de VAPERIA LA J Y EL JALAPEÑO y EL SABOR DE LAS 5 ESQUINAS**
> *Escrito para que lo entienda cualquiera — sin jerga técnica*

---

## 🎯 TU PRIMER DÍA

### 1. Entrar al sistema
1. Abre el navegador (Chrome/Edge/Firefox)
2. Ve a: `https://korvexcio.korvexdev.cc/pos`
3. Verás la pantalla de **login de KORVEXCIO**
4. Escribe tu **usuario** (correo que te dio el dueño)
5. Escribe tu **contraseña**
6. Pulsa **Iniciar sesión** o Enter

> 💡 **Tip:** Si olvidaste la contraseña, avísale al dueño. Él te la resetea desde su panel.

### 2. Abrir tu turno (¡obligatorio antes de vender!)
Al entrar, verás un cuadro: **"Abrir turno"**
1. Verifica que diga tu **nombre** y tu **negocio** (VLJ o ESE)
2. Si hay **efectivo inicial** en la caja, escríbelo en "Monto inicial"
3. Pulsa **Abrir turno**
4. ¡Listo! Ya puedes vender

> ⚠️ **Sin turno abierto no se puede facturar.** El botón de cobrar estará gris.

---

## 🛒 VENDER

### Agregar productos al carrito
**Opción A — Escáner (rápido):**
1. Apunta el escáner al código de barras
2. Pulsa el gatillo
3. El producto cae solo al carrito

**Opción B — Buscar por nombre:**
1. Pulsa en la barra **"Buscar por código, nombre o escanear..."**
2. Escribe parte del nombre (ej: "MENTA", "CAFÉ", "POD")
3. Pulsa Enter o toca el producto en la lista

**Opción C — Botón "+" (productos favoritos):**
1. Toca el botón **+** en la esquina
2. Busca en la cuadrícula por categoría

### Modificar cantidades
- **Más:** Toca el `+` junto al item
- **Menos:** Toca el `-`
- **Borrar:** Desliza el item a la izquierda → papelera

### Aplicar descuentos (solo si el dueño te autorizó)
1. Toca el item en el carrito
2. Pulsa **Descuento**
3. Escribe % o monto fijo
3. Confirma

> 💡 **Regla:** Los descuentos mayores al 10% piden confirmación del dueño.

---

## 💰 COBRAR

### 1. Pulsa el botón grande **COBRAR** (azul, abajo a la derecha)
Se abre la pantalla de pagos.

### 2. Elige cómo paga el cliente

| Método | Qué hacer |
|--------|-----------|
| **Efectivo** | Escribe lo que te da el cliente → el sistema calcula el vuelto |
| **Tarjeta** | Cobras en el datáfono aparte → en el POS marcas "Tarjeta" y el monto |
| **Mixto** | Parte en efectivo, parte en tarjeta → agregas las dos líneas |
| **Transferencia / tPago** | Marca "Transferencia" y el monto → pide comprobante al cliente |

### 3. ¿Cliente con RNC? (Factura de crédito fiscal E31)
**CUÁNDO PEDIRLO:** Si el total **≥ RD$250,000** ( Norma 05-19 )
1. El sistema **bloquea** el cobro y muestra: **"RNC Requerido — Ventas de RD$250,000 o más necesitan el RNC del comprador"**
2. Pide al cliente su **RNC** (11 dígitos: 1-23-45678-9)
3. Escríbelo en el campo **"RNC Cliente"** (aparece automáticamente al bloquear)
4. Pulsa **Reintentar** → ya deja cobrar

> ⚠️ **NUNCA inventes un RNC.** Si el cliente no lo tiene y la venta pasa de RD$250k, no puedes facturar como E31. El cliente debe dar su RNC o la venta se hace como consumo (E32, sin crédito fiscal).

### 4. Imprimir recibo
- Si hay impresora conectada: sale solo
- Si no: pulsa **"Imprimir"** en el diálogo de éxito
- Entrega el recibo al cliente

---

## 📴 SIN INTERNET (MODO OFFLINE)

El POS **sigue vendiendo** aunque se caiga internet.

### Qué verás:
- Badge amarillo arriba: **"OFFLINE — Se sincronizará al reconectar"**
- Número de facturas pendientes (ej: "3 facturas por sincronizar")

### Qué SÍ funciona:
- ✅ Agregar items al carrito
- ✅ Cobrar (efectivo, tarjeta, mixto)
- ✅ Imprimir recibo (si la impresora es local/USB)
- ✅ Abrir/cerrar turno

### Qué NO funciona (hasta que vuelva internet):
- ❌ Enviar e-CF a la DGII (quedan "Pendientes")
- ❌ Sincronizar stock con la nube
- ❌ Ver reportes en tiempo real del dueño

### Cuando vuelva internet:
1. El badge se pone verde: **"Sincronizando..."**
2. Las facturas offline se envían solas a la DGII
3. Verás **"Sincronizado ✓"** cuando terminen
4. Si alguna falla: vuelve a "Pendiente" y reintenta solo cada 5 min

> 💡 **Tranquilo:** **Ninguna venta se pierde.** Todo queda guardado en el navegador (IndexedDB) y en el servidor local.

---

## 🔚 CERRAR TURNO

### 1. Al final de tu jornada:
1. Pulsa tu **nombre/avatar** (arriba a la derecha)
2. Elige **"Cerrar turno"**

### 2. Arqueo de caja (cuadrar el dinero)
Verás una tabla por **método de pago**:

| Método | Sistema dice | Tú cuentas | Diferencia |
|--------|--------------|------------|------------|
| Efectivo | RD$15,420.00 | RD$15,420.00 | RD$0.00 ✓ |
| Tarjeta | RD$8,500.00 | RD$8,500.00 | RD$0.00 ✓ |
| Transferencia | RD$2,100.00 | RD$2,100.00 | RD$0.00 ✓ |

1. Cuenta **físicamente** el efectivo en la gaveta
2. Compara con "Sistema dice"
3. Si hay diferencia: escríbela en "Tú cuentas" → el sistema anota el descuadre
3. Pulsa **Cerrar turno**

> ⚠️ **No cierres turno si hay diferencia grande sin avisar al dueño.** Él lo ve en su panel.

### 3. ¡Ya está!
- El turno queda **cerrado** en el sistema
- El dueño ve tu arqueo en su dashboard
- Puedes irte tranquilo

---

## ❓ PROBLEMAS COMUNES — QUÉ HACER

| Problema | Qué hacer |
|----------|-----------|
| **"RNC Requerido" y el cliente no tiene RNC** | Venta < RD$250k: normal. Venta ≥ RD$250k: no puedes facturar E31. Dile al cliente que necesita RNC para crédito fiscal. |
| **Impresora no imprime** | 1. Verifica cable USB / Bluetooth. 2. Reinicia la impresora. 3. Si nada: avisa al dueño — la factura ya está en el sistema, se puede reimprimir después. |
| **"Stock insuficiente"** | El item no tiene stock en tu almacén. Dile al cliente que no hay. No puedes vender lo que no existe. |
| **Se cayó internet** | Sigue vendiendo normal (modo offline). Las facturas se sincronizan solas al volver. |
| **Error raro / pantalla blanca** | 1. Recarga la página (F5 / Ctrl+R). 2. Vuelve a login. 3. Tu turno sigue abierto. 4. Si persiste: avisa al dueño. |
| **Olvidé cerrar turno ayer** | El dueño lo ve en "Turnos abiertos". Él puede cerrarlo por ti (con tu arqueo) o tú lo cierras hoy y anotas la fecha real. |

---

## 🆘 CONTACTOS

| Qué pasa | A quién avisar |
|----------|----------------|
| Error fiscal (RNC, DGII) | Dueño / Contador |
| Impresora / escáner / hardware | Dueño / Soporte técnico |
| Olvidé contraseña | Dueño (te la resetea) |
| Duda sobre producto/precio | Dueño / Encargado de inventario |
| Cliente reclama factura | Dueño / Contador |

---

## ✅ CHECKLIST DIARIO

- [ ] Llegué, abrí turno, verifiqué monto inicial
- [ ] Vendí normal (escaneo / búsqueda)
- [ ] Pedí RNC cuando correspondía (≥ RD$250k)
- [ ] Cobré bien (efectivo = vuelto correcto, tarjeta = monto exacto)
- [ ] Imprimí y entregué recibo a cada cliente
- [ ] Si se cayó internet: seguí vendiendo, no me asusté
- [ ] Al final: cerré turno, arqueé por método, verifiqué que cuadra
- [ ] ¿Diferencia en efectivo? Avisé al dueño
- [ ] Me voy tranquilo 😌

---

**KORVEXCIO** — *Punto de venta que entiende tu negocio*
*¿Dudas? Pregúntale al dueño. Este manual está en `docs/MANUAL-CAJERO.md` del repo.*