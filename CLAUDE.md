# CLAUDE.md — KORVEXCIO (cliente 1: VAPELAND)

ERP + POS multi-tenant sobre **ERPNext/Frappe v15** para retail + food en
República Dominicana.

## Nomenclatura — no confundir nunca

| Nombre | Qué es |
|---|---|
| **KORVEX** | La casa. Korvex Dev · `korvexdev.cc` |
| **KORVEXCIO** | **Este producto.** De *comerCIO*. Sin guion. Repo: `yedinrumba-eng/KORVEXCIO` · app de Frappe: `korvexcio` |
| **KORVIS** | *The AI Assistant by Korvex* — el bot de WhatsApp. Otro producto de la casa |
| **VAPELAND** | **Un cliente/tenant** de KORVEXCIO. NO el nombre del proyecto |
| **ADAP** | **Un cliente** de KORVIS (banco RD). NO el nombre de ese producto |

⚠️ En disco, la carpeta de KORVIS todavía se llama `C:\PROYECTOS\ADAP`. Las
rutas de este documento usan el nombre real de hoy.
El código de las apps propias es agnóstico del rubro: un cliente nuevo = un
site + configuración, **sin tocar código compartido**.

> **Antes de implementar nada:** lee `HANDOFF.md` (estado y decisiones),
> `PROGRESO.md` (bitácora) y `docs/05-PREGUNTAS-CLIENTE.md` (lo que aún no está
> confirmado). Trabajar sobre supuestos no marcados es cómo se construye lo
> equivocado con confianza.

---

## La fecha que manda

**15 de noviembre de 2026** — e-CF obligatorio para pequeños, micro y no
clasificados (Ley 32-23). Multa: 5 a 50 salarios mínimos. **El módulo fiscal es
el camino crítico. Todo lo demás se difiere; esto no.**

## Tech Stack

Frappe Framework v15 · ERPNext v15 · MariaDB · Redis 7 · POSNext (Vue 3 + Vite
+ TS) · `ecf-dgii` (PyPI, MIT) · Docker Compose en dev, bench en prod ·
Cloudflare Tunnel → `*.korvexdev.cc`.

Detalle y razones de cada decisión: `TECH_STACK.md`.

## Arquitectura

```
korvex-bench/
├── apps/
│   ├── frappe · erpnext · posnext     # UPSTREAM — no se tocan
│   ├── korvexcio                  ⭐  # PROPIA — módulos `ecf` y `retail`
│   ├── crm                            # Frappe CRM (fase 2)
│   └── ury                            # cafetería (fase 2)
└── sites/
    ├── korvexcio.korvexdev.cc         # cliente 1 — un site = una DB
    │    ├── Company VAPERIA LA J Y EL JALAPEÑO   # vapería (su RNC, su almacén)
    │    └── Company EL SABOR DE LAS 5 ESQUINAS   # cafetería (su RNC, su almacén)
    └── demo.korvexdev.cc              # staging / demostración
```

---

## Reglas obligatorias

### 1. Los upstream no se tocan. Nunca.
Todo lo propio va en la app `korvexcio`, vía **DocTypes propios, `hooks.py`,
custom fields exportados como fixtures y, en último recurso, overrides**. Un
`git pull` de ERPNext no puede romper el proyecto. Un fork parcheado a mano es
un fork muerto. **Detalle completo en `docs/06-COMO-SE-TRABAJA.md`.**

⛔ **Si te encuentras editando un archivo dentro de `apps/erpnext/` o
`apps/frappe/`, PARA.** Hay una forma correcta de hacer eso y está en el doc 06.

**Excepción única:** POSNext sí se forkea (necesita campos fiscales dominicanos
por dentro). Fork propio, rama `korvex`, `upstream` como remote, rebase para
traer mejoras. Nunca commits en `main` del fork.

### 2. Ningún default del código compartido puede servirle a un solo tenant.
Si un comportamiento es de vape shop (o de cafetería, o de colmado), va en la
**configuración de ESE site**, con su default apagado — nunca al revés.
*Lección pagada tres veces en KORVIS el 27/08/2026.*

### 3. El POS nunca espera a la DGII para cerrar una venta.
Vende → obtiene TrackID → imprime. La confirmación llega asíncrona por la cola
de fondo de Frappe. Un POS que se bloquea porque la DGII tardó es un POS roto.

### 4. Sin internet, el negocio sigue vendiendo.
Modo contingencia obligatorio: se vende offline, se marca pendiente, se drena la
cola al reconectar. **Ninguna venta se pierde en silencio** — lo pendiente vive
en un panel visible, nunca solo en un log.

### 5. Reintentos con backoff exponencial.
2/4/8/16/32s, máximo 5 intentos, para todo lo que salga a la red (proveedor de
e-CF, DGII). Mismo patrón que KORVIS.

### 6. Secretos a mano, en el servidor.
El certificado `.p12`, los tokens del proveedor de e-CF y las credenciales de
DGII **se pegan directo en el servidor**. No viajan por un formulario web, no
se commitean, no entran a un panel. *Mismo criterio que la Parte 3 de
`ADAP/docs/GUIA-ALTA-DE-TENANT.md`.*

### 7. Nunca editar código en el servidor.
Commit y push en DEV (`C:\PROYECTOS\KORVEXCIO`) → `git pull` en el HOST →
`bench restart`. El HOST solo consume. *(`CONVENCIONES.md` §6)*

### 8. PII cifrada, logs enmascarados.
Si se guarda cédula o fecha de nacimiento para verificación de edad: AES-256-GCM
con IV por registro, clave solo en `.env`. Logs con PII enmascarada.

### 9. El RNC se exige solo a partir de RD$250,000.
Norma 05-19. **Lo hace el sistema, no el criterio del cajero.**

### 10. El aislamiento no es solo de datos.
Un site por tenant resuelve la base de datos. **El canal de salida no.**
Cualquier cliente HTTP con credenciales de un tenant (WhatsApp, correo,
proveedor de e-CF) se resuelve **por operación**, nunca se construye una vez al
arrancar. Si no se puede resolver, **no se envía** — nunca caer al cliente de
otro tenant. *Ver `ADAP/docs/LECCIONES-MULTI-TENANT.md`.*

### 11. Marca: no se puede decir "ERPNext".
"ERPNext" y "Frappe" son marcas registradas de Frappe Technologies. **No van en
el nombre del producto, de la empresa, ni en el dominio.** Hay que mantener
visible `© Frappe Technologies Pvt. Ltd.` y el aviso de GPLv3.

### 12b. `ignore_permissions=True` y `frappe.db.sql()` crudo: PROHIBIDOS.
Dentro de `korvexcio/` son los bypass del aislamiento — el equivalente de un
`SECURITY DEFINER` que se salta el RLS. Con dos Companies en una misma base
(D19), una sola query sin filtrar mezcla los datos de los dos negocios.

Si un caso los necesita de verdad: **se justifica por escrito en el PR y se le
escribe su propio test de aislamiento.** Sin excepción silenciosa. Semgrep los
marca en CI desde S1.3.

Y los reportes propios **filtran por `company` explícitamente** — no se confía
en que User Permission lo haga solo. El PR frappe/erpnext#44695 existe justo
porque una vez no lo hizo.

### 12. Licencias: verificar antes de copiar.
`ecf-dgii` es MIT ✅ · `dgii-compliance` es GPL-3.0 (referencia, no dependencia)
· **`rob-erply/dgii_facturacion_electronica` es OPL-1, propietaria — se mira,
no se copia.**

---

## Organización del código

1. Python con type hints. Una entidad por archivo.
2. Ningún nombre de cliente, precio ni regla de negocio hardcodeado — todo en
   la configuración del site.
3. `.env` nunca se commitea (`.env.example` sí).
4. Los DocTypes propios llevan prefijo (`ECF Settings`, `ECF Sequence`,
   `ECF Document`) — nunca chocan con nombres de ERPNext.

## Reglas que no se rompen

*(Heredadas del `MASTERGUIDE.md` de Korvex — valen para todo)*

1. **Leer la documentación antes de "arreglar".**
2. **Verificar contenido, no existencia.** Un dump vacío también pesa más de cero.
3. **Un backup no restaurado es una esperanza.**
4. **No mover la mitad de un sistema.** O todo, o nada.
