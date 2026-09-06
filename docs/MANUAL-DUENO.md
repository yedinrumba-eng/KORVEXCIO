# 📊 MANUAL DEL DUEÑO — KORVEXCIO POS

> **Para el dueño de VAPERIA LA J Y EL JALAPEÑO + EL SABOR DE LAS 5 ESQUINAS**
> *Todo tu negocio en una pantalla — escrito sin tecnicismos*

---

## 🎯 TU PANEL (DASHBOARD CONSOLIDADO)

Al entrar a `https://korvexcio.korvexdev.cc` y loguearte como **Dueño**, ves **las dos empresas a la vez**:

```
┌─────────────────────────────────────────────────────────────┐
│  KORVEXCIO — Dashboard Dueño                    [VLJ] [ESE] │
├──────────────┬──────────────┬──────────────┬──────────────┤
│  VENTAS HOY  │    CAJA      │   STOCK      │   e-CF       │
│  VLJ: 45,230 │  VLJ: 12,450 │  ⚠️ 3 items  │  ✓ 28/28 OK  │
│  ESE: 8,150  │  ESE: 3,200  │     vencen   │  ⏳ 2 pend   │
│  TOTAL:53,380│  TOTAL:15,650│              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

- **Selector arriba a la derecha:** Cambia entre "Ver las dos", "Solo VLJ", "Solo ESE"
- **Todo en tiempo real:** No hay que recargar

---

## 👥 GENTE (USUARIOS Y PERMISOS)

### Crear un cajero nuevo
1. Menú lateral → **Usuarios** → **Nuevo**
2. Llena:
   - **Correo:** `juan@ejemplo.com` (su login)
   - **Nombre completo:** `Juan Pérez`
   - **Rol:** `Cajero VLJ` **O** `Cajero ESE` (¡no los dos!)
   - **Contraseña:** pulsa **Generar segura** → anótala y dásela en papel
3. **Guardar**
4. El cajero ya puede entrar en `.../pos` con su correo y esa contraseña

> 🔒 **Regla de oro:** Un cajero **solo ve su negocio**. Un cajero VLJ **nunca** ve ventas, stock ni clientes de ESE. El sistema lo impide automáticamente.

### Cambiar contraseña a alguien
1. Usuarios → busca al usuario → **Editar**
2. Pulsa **Cambiar contraseña** → **Generar segura** → dale el papelito

### Bloquear acceso (empleado se va)
1. Usuarios → busca → **Editar**
2. Desmarca **Habilitado** → **Guardar**
3. Ya no puede entrar. Sus turnos y ventas quedan en el histórico.

### Roles — qué puede hacer cada uno

| Quién | Qué ve | Qué puede hacer |
|-------|--------|-----------------|
| **Cajero VLJ** | Solo VLJ | Vender, abrir/cerrar turno, ver sus facturas |
| **Cajero ESE** | Solo ESE | Vender, abrir/cerrar turno, ver sus facturas |
| **Contador** | Las dos | **Solo leer** — reportes, facturas, e-CF, stock |
| **Dueño (tú)** | Las dos | **Todo** — crear usuarios, ver todo, configurar, anular |

> ⚠️ **Tú NO eres "System Manager".** Eso es para soporte técnico. Tu rol "Dueño" tiene todo lo que necesitas para operar el negocio, sin romper la configuración fiscal.

---

## 📦 PRODUCTOS (INVENTARIO)

### Ver stock actual
1. Menú → **Stock** → **Balance de Stock**
2. Filtra por **Almacén** (Stores - VLJ / Stores - ESE)
3. Verás: Item, Cantidad, Valor, Último movimiento

### Agregar producto nuevo
1. **Stock** → **Items** → **Nuevo**
2. **¿Es variante?** (ej: mismo líquido, distinto sabor/nicotina)
   - **SÍ** → Primero crea el **Template** (ej: "E-Liquid 30ml") → luego **Variantes** por Sabor × Nicotina
   - **NO** → Item simple (ej: "Café Americano", "Pod System")
3. Llena lo básico:
   - **Nombre:** `E-Liquid 30ml Menta 3mg`
   - **Grupo:** `Vapes` o `Cafeteria`
   - **Unidad:** `Nos` (unidades)
   - **¿Tiene stock?** Sí/No
4. **Precios:** En "Item Defaults" → pon precio de venta por Company
5. **Almacén:** `Stores - VLJ` o `Stores - ESE`
6. **Guardar**

> 💡 **Variantes en masa:** Si tienes Excel del proveedor, usa **Carga Masiva** (ver abajo).

### Editar precio
1. Busca el item → **Editar**
2. En "Item Defaults" → cambia `Price List Rate` (Standard Selling)
3. **Guardar** → el cajero lo ve al instante

### Stock por vencer (FEFO — First Expired First Out)
El sistema te avisa automáticamente:
- **🟡 90 días:** "Próximo a vencer"
- **🟠 60 días:** "Vence pronto"
- **🔴 30 días:** "URGENTE — Vence este mes"

Ver en: **Stock** → **Reportes** → **Stock por Vencer (FEFO)**

---

## 📥 CARGA MASIVA DE CATÁLOGO (DESDE EXCEL)

Si el proveedor te manda Excel con 500+ items:

1. Prepara el CSV con estas columnas (orden no importa):
   ```
   item_code, item_name, item_group, stock_uom, company, warehouse,
   price_list, price_list_rate, valuation_rate, variant_of,
   sabor, nicotina_mg, tamano_ml, ohmiaje
   ```
2. Menú → **Herramientas** → **Carga Masiva Catálogo**
3. Sube el archivo → **Procesar**
4. Verás resumen: `✓ 432 creados, ↻ 18 actualizados, ⚠️ 5 errores`
5. Revisa errores (suelen ser código duplicado o grupo inexistente)

> 🛠 **Comando técnico (si hace falta):**
> ```bash
> bench --site korvexcio.korvexdev.cc run-script korvexcio.retail.bulk_import --file /ruta/catalogo.csv
> ```

---

## 🧾 FISCAL (e-CF)

### Estados de las facturas
| Estado | Qué significa | Qué haces |
|--------|---------------|-----------|
| **✅ Aceptado** | DGII lo aprobó | Nada, todo bien |
| **⏳ Pendiente** | Enviado, esperando respuesta | Espera (reintenta cada 5 min solo) |
| **🔄 Reintentando** | Falló, volviendo a intentar | Espera (máx 5 intentos en 2+4+8+16+32 min) |
| **❌ Error** | 5 intentos fallidos | **Tú decides:** Reintentar manual / Anular / Contingencia |
| **📴 Contingencia** | Sin internet, pre-firmada | Se envía solo al volver internet |

### Panel de e-CF Pendientes
Menú → **Fiscal** → **e-CF Pendientes**
- Ves **todas** las facturas que no están "Aceptado"
- Botón **Reintentar** por cada una
- Botón **Reintentar todas** (arriba a la derecha)
- Filtra por Company, estado, fecha

### Contingencia (modo offline fiscal)
Si internet se cae **más de 1 hora**:
1. El sistema usa **e-CF pre-computados** (guardados en el servidor)
2. Las facturas salen con estado **Contingencia**
3. Al volver internet: se sincronizan solas a la DGII
4. Tú solo verificas en **e-CF Pendientes** que pasen a "Aceptado"

> 🔑 **Certificados digitales:** Están en el servidor (archivos `.p12` con contraseña). **No los toques.** Si vencen (1 año), el contador te avisa y los renueva.

### Secuencias eNCF (números de factura)
Menú → **Fiscal** → **Secuencias eNCF**
- Una por **Company + Tipo** (VLJ-E32, VLJ-E31, ESE-E32, ESE-E31)
- Verás: `Desde / Hasta / Siguiente / Quedan / Vence`
- **Alerta automática** cuando queden < 100 números
- Para crear nueva: **Nueva Secuencia** → pide rango a DGII (CerteCF) → ingresa aquí

---

## 📈 REPORTES (LO QUE QUIERES VER CADA DÍA)

### 1. Venta del día (resumen ejecutivo)
**Dashboard principal** ya lo tienes. Detalle:
- Menú → **Reportes** → **Venta Diaria Consolidada**
- Por Company, por método de pago, por hora

### 2. Margen por categoría
**Stock** → **Reportes** → **Margen por Categoría**
- Te dice: "Vapes te da 38% margen, Café 52%, Accesorios 25%"
- Útil para decidir qué promocionar

### 3. Stock muerto (90+ días sin moverse)
**Stock** → **Reportes** → **Stock Muerto 90+**
- Items que no se venden → dinero parado
- Decides: ¿descuento? ¿devuelvo a proveedor? ¿regalo?

### 4. Rotación de inventario
**Stock** → **Reportes** → **Rotación**
- Cuántas veces vendes/repones cada item al mes
- Rotación alta = buen negocio, baja = revisar

### 5. e-CF pendientes / fallidos
**Fiscal** → **e-CF Pendientes** (ya visto arriba)

### 6. Arqueos de caja (cierre de turnos)
**POS** → **Turnos de Caja** → **Historial**
- Ves cada cierre de cada cajero
- Diferencias en efectivo marcadas en **rojo**
- Exportable a Excel para el contador

---

## ⚙️ CONFIGURACIÓN BÁSICA (LO QUE TOCAS POCO)

### Métodos de pago
**Cuentas** → **Modos de Pago** → **Nuevo / Editar**
- `Efectivo` (siempre)
- `Tarjeta` (si usas datáfono)
- `Transferencia` / `tPago`
- Cada uno con su **cuenta contable** (el contador la pone)

### Impresora térmica
Cuando la compres (80mm, ESC/POS, USB/Bluetooth/Red):
1. Conéctala al mini PC (servidor) por USB
2. Menú → **Punto de Venta** → **POS Profile** → tu Company
3. En **Impresora**: pon el puerto (ej: `/dev/ttyUSB0` o IP:9100)
4. **Probar impresión** → imprime recibo de prueba

### Respaldos (Backups)
- **Automático:** Todos los días a las 03:30 (timer systemd)
- **Manual:** Menú → **Herramientas** → **Backup** → **Ejecutar ahora**
- **Dónde:** En el servidor (`/home/korvex/frappe_docker-korvexcio-s05/backups`)
- **Retención:** 14 días (se borran solos los viejos)

> 🔴 **IMPORTANTE:** El backup **NO se sube solo a la nube**. Una vez al mes, bájalo y guárdalo en tu Google Drive / OneDrive / disco externo. Ver sección "Si algo falla".

---

## 🆘 SI ALGO FALLA — QUÉ HACER (RUNBOOK RESUMIDO)

| Síntoma | Primer paso | Si no se arregla |
|---------|-------------|------------------|
| **POS no carga / pantalla blanca** | Recarga (F5) → vuelve a login | Reinicia servicios: `ssh korvex-host 'cd /home/korvex/frappe_docker-korvexcio-s05 && docker compose restart backend queue-short queue-long scheduler websocket'` |
| **e-CF se quedan "Pendiente" horas** | Verifica internet en el local → `ping google.com` | Reintenta manual en **e-CF Pendientes** / Revisa `RUNBOOK.md` sección "DGII caída" |
| **Impresora no imprime** | Verifica cable / enciende / papel | `RUNBOOK.md` sección "Impresora" |
| **Se cayó internet del local** | POS entra en **Offline** solo → sigue vendiendo | Al volver, verifica sincronización en badge verde |
| **MariaDB / Redis expuestos a la red** | `ssh korvex-host 'ss -tlnp \| grep -E \"3306|6379\"'` → solo debe salir `127.0.0.1` | `RUNBOOK.md` sección "Superficie de red" |
| **Disco > 80%** | `df -h /` → `docker builder prune -f` | Borra backups viejos / llama a soporte |
| **KORVIS (el bot de WhatsApp) no responde** | `systemctl status korvex-api` + `curl http://127.0.0.1:4000/health` | `RUNBOOK.md` sección "KORVIS roto" |

---

## 📞 CONTACTOS CLAVE

| Qué | Quién | Cómo |
|-----|-------|------|
| **Soporte técnico KORVEXCIO** | Yedin (desarrollador) | WhatsApp / Telegram |
| **Contador / Fiscal** | Tu contador | Tel / Email |
| **Certificado digital / DGII** | Contador / Proveedor (Alanube/ECF SSD) | Portal proveedor |
| **Hardware (impresora, escáner, PC)** | Proveedor local | Tienda donde compraste |
| **Servidor (mini PC) se cae** | Yedin + tú (tienes acceso físico) | Tailscale SSH / Monitor |

---

## ✅ CHECKLIST SEMANAL DEL DUEÑO

- [ ] Revisé **Dashboard** lunes: ventas, caja, stock, e-CF
- [ ] Verifiqué **e-CF Pendientes** — ninguno en "Error" > 24h
- [ ] Miré **Stock por Vencer (FEFO)** — ¿hay que liquidar algo?
- [ ] Revisé **Arqueos de caja** — ¿diferencias en efectivo?
- [ ] Corrí **Backup manual** y me lo llevé a mi nube personal
- [ ] Revisé **Margen por categoría** — ¿ajustar precios/promos?
- [ ] ¿Certificados digitales vigentes? (vencen en 1 año)

---

## 📄 DOCUMENTOS TÉCNICOS (PARA SOPORTE)

| Documento | Dónde está | Para qué |
|-----------|------------|----------|
| `RUNBOOK.md` | `docs/RUNBOOK.md` | **Guía completa de fallos** — comandos exactos |
| `docs/14-ACTIVACION-FISCAL.md` | Repo | Cómo activar e-CF paso a paso |
| `docs/02-FISCAL-RD.md` | Repo | Ley 32-23, Norma 05-19, ISC, ITBIS |
| `docs/08-BLUEPRINT.md` | Repo | Plan maestro técnico completo |

---

**KORVEXCIO** — *Tu negocio, tus reglas, tu control*
*Este manual está en `docs/MANUAL-DUENO.md` del repo. Versión para imprimir: `bench --site korvexcio.korvexdev.cc export-doc MANUAL-DUENO.md`*