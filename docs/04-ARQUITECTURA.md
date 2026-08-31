# 04 — Arquitectura

---

## Multi-tenancy: un site por cliente

Frappe trae **DNS-based multitenancy** nativo. No hay que construirla.

```bash
bench config dns_multitenant on
bench new-site vapeland.korvexdev.cc --install-app erpnext
bench new-site cliente2.korvexdev.cc --install-app erpnext
bench setup nginx && sudo service nginx reload
```

Cada site = **una base de datos MariaDB propia** = **aislamiento físico real**.

### Comparado con el multi-tenant de KORVIS

| | KORVIS | KORVEXCIO |
|---|---|---|
| **Mecanismo** | `organization_id` en cada tabla + filtro por JWT | Un site = una DB |
| **Aislamiento** | Lógico (depende de que ninguna query se olvide del filtro) | Físico |
| **Riesgo de fuga entre tenants** | Real — pasó en producción el 06/08/2026 | Estructuralmente imposible por consulta |
| **Costo de un tenant nuevo** | Una fila + un `config.yml` | Una DB + entrada nginx + recursos |
| **Escala** | Miles de tenants en una DB | Decenas por servidor |

👉 **El modelo de Frappe es más seguro y menos escalable.** Para el volumen de
KORVEX (decenas de clientes, no miles) es el trade-off correcto.

⚠️ **Pero la lección de KORVIS sigue aplicando al canal de salida.** Cuando se
integre WhatsApp o correo por tenant, las credenciales se resuelven **por
mensaje**, no una sola vez al arrancar. Ver `ADAP/docs/LECCIONES-MULTI-TENANT.md`.

---

## Hosting

### Lo que hay hoy: `korvex-node1`
Mini PC en casa. **14 GB RAM · 84 GB libres de 98.** Ya corre KORVIS: PostgreSQL
16 + pgvector, Redis 7, `apps/api` (Express), `apps/dashboard` y `apps/ops`
(Next.js 15). Salida por Cloudflare Tunnel a `*.korvexdev.cc`.

### Lo que pide ERPNext

| Usuarios activos | RAM | vCPU |
|---|---|---|
| 5–15 | 4 GB | 2 |
| 15–50 | 8 GB | 4 |
| 50–150 | 16 GB | 8 |

Disco: **50–100 GB NVMe SSD**. Consumo por proceso: worker Gunicorn 150–250 MB
c/u · worker de fondo 150–250 MB c/u · Redis 256–512 MB · MariaDB 1–3 GB.

### El cálculo honesto

| Escenario | ¿Cabe en el nodo 1? |
|---|---|
| **1 bench, 1–2 sites (VAPELAND + demo)** | ✅ Sí, con holgura razonable |
| 1 bench, 3–5 sites | 🟡 Justo. Vigilar RAM y disco de cerca |
| 10+ tenants | ❌ No. Requiere segundo nodo o VPS |

El `ROADMAP.md` de `_KORVEX-OPS` ya lo dice: **el techo del nodo 1 no es RAM,
es disco (84 GB libres)**, y el criterio es *"este nodo es lo que le cobras a
clientes"*. ERPNext califica. Pero llenar el disco tumba las bases de datos —
que es la plataforma que se cobra.

### Recomendación
1. **Desarrollo:** Docker Compose local (`frappe_docker`).
2. **VAPELAND en producción:** bench en el nodo 1, un site.
3. **Al tercer cliente:** VPS dedicado para el bench de ERPNext. Presupuestarlo
   ahora, no cuando esté ardiendo.

⚠️ Regla no negociable de `CONVENCIONES.md` §6: **nunca editar código en el
servidor.** Commit y push en DEV → `git pull` en el HOST → `bench restart`.

---

## Estructura de apps

```
korvex-bench/
├── apps/
│   ├── frappe                 # framework (upstream)
│   ├── erpnext                # ERP (upstream)
│   ├── posnext                # POS (upstream, fork propio si hace falta)
│   ├── korvexcio          ⭐  # PROPIA — LA app: módulos `ecf` y `retail`
│   ├── crm                    # Frappe CRM (post-MVP)
│   └── ury                    # cafetería (post-MVP)
└── sites/
    ├── vapeland.korvexdev.cc
    └── demo.korvexdev.cc
```

**Regla de oro:** los upstream **no se tocan**. Todo lo propio va en
`korvex_*` usando hooks, custom fields y overrides. Un `git pull` de ERPNext
no puede romper el proyecto. Esto es lo que hace mantenible el fork.

> ⚠️ **Corregido el 31/08:** antes decía dos apps (`korvex_ecf` +
> `korvex_retail`). Es **UNA** app `korvexcio` con dos **módulos** internos —
> `apps.json` instala un repo = una app. Ver `docs/06-COMO-SE-TRABAJA.md`.
>
> ⭐ **La estructura de abajo quedó superada.** El barrido del 31/08 (noche)
> destiló una estructura de DocTypes de tres localizaciones fiscales de Frappe
> **en producción** (Arabia Saudí/ZATCA, India/GST, México/CFDI). Está en
> **`docs/07-ARQUITECTURA-REFERENCIA.md` §4** e incluye lo que este borrador no
> tenía: `ecf_integration_log`, `ecf_contingencia` (el patrón *Precomputed
> Invoice* de ZATCA), `acecf`, `enqueue_after_commit=True`, y el `docstatus`
> nativo como máquina de estados. **Usa esa, no esta.**

### Módulo `ecf` — lo fiscal

```
korvexcio/ecf/
├── providers/
│   ├── base.py        # emitir(doc)->TrackID · consultar(trackid) · anular(ncf)
│   ├── ssd.py         # ECF SSD vía la librería ecf-dgii (MIT)
│   └── alanube.py     # Alanube REST
├── doctype/
│   ├── ecf_settings/  # RNC, certificado, ambiente, credenciales
│   ├── ecf_sequence/  # rangos e-NCF autorizados + alerta de agotamiento
│   └── ecf_document/  # cola de envío y estado
├── hooks.py           # Sales Invoice on_submit -> encolar
└── print_format/      # Representación Impresa con QR
```

**Máquina de estados de `ecf_document`:**

```
borrador ─► encolado ─► enviado(TrackID) ─► aceptado
                │                       └─► rechazado ─► corregir
                └─► contingencia (sin internet) ─► reenviar al reconectar
```

**Reglas de diseño no negociables:**
1. El POS **nunca** espera respuesta de la DGII para cerrar una venta.
2. Todo envío es asíncrono, por la cola de fondo de Frappe.
3. Reintentos con **backoff exponencial** (mismo patrón que KORVIS: 2/4/8/16/32s,
   máx 5 intentos).
4. Una venta sin e-CF confirmado **queda visible en un panel**, nunca se pierde
   en silencio.
5. Alerta cuando queden menos de N secuencias e-NCF disponibles.

### Módulo `retail` — el vertical

Aquí vive todo lo que hace que esto sea vendible como producto, **no** lo
específico de VAPELAND:

- Atributos de ítem preconfigurados: Sabor, Nivel de Nicotina, Tamaño, Ohmiaje
- Flag `requiere_verificacion_edad` a nivel de **Item Group**
- Política **FEFO** por lote y alertas de vencimiento (90/60/30 días)
- Reportes del vertical: stock muerto, margen por categoría, rotación
- Marca KORVEX (con el aviso de copyright de Frappe visible, ver `03-BENCHMARK`)

**La regla que decide qué va en cuál módulo:** si le sirve a cualquier tienda,
va en `retail`. Si es de VAPELAND, va en la **configuración del site**,
no en código. Mismo principio que `organizations/<tenant>/config.yml` en KORVIS —
y la lección pagada tres veces el 27/08/2026: *ningún default del código
compartido puede servirle solo a un tenant*.

---

## Integración con KORVIS (post-MVP)

```
Cliente por WhatsApp
        │
        ▼
   KORVIS (Node/TS)          ─── REST API ───►   ERPNext
   · conversación                              · ¿tienen X en stock?
   · RAG sobre catálogo                        · precio de Y
   · captura de leads                          · crear cliente
   · escalamiento a humano                     · crear pedido
```

- ERPNext expone su **API REST nativa** (token de API por usuario del sistema).
- KORVIS es el cliente. **No al revés** — ERPNext no debe saber que WhatsApp existe.
- El catálogo se sincroniza a la base de conocimiento de KORVIS con un job
  periódico, no consulta en vivo por cada mensaje.
- **Regla:** el bot **nunca** confirma stock exacto ni cierra una venta sin
  humano. Sugiere y escala. Misma disciplina que los `forbidden_topics` de KORVIS.

---

## Seguridad

Lo que se hereda de `ADAP/CLAUDE.md` y aplica igual aquí:

1. **Nada de PII sensible en texto plano.** Si se guarda cédula para
   verificación de edad, va cifrada (AES-256-GCM, IV por registro).
2. **La clave maestra solo en `.env`**, nunca en el repo, nunca en el panel web.
3. **Tokens del proveedor de e-CF y el certificado `.p12`** se cargan a mano en
   el servidor. **No viajan por un formulario web.** Mismo criterio que la
   Parte 3 de `GUIA-ALTA-DE-TENANT.md`.
4. **Logs con PII enmascarada.**
5. **`.env` y `.gitignore` revisados antes del primer push.**
6. Cloudflare Access delante del panel de administración, como `apps/ops`.

---

## Modelo de producto KORVEX

**Posicionamiento (decisión #4):** núcleo genérico de retail + food, con el
vertical vape/hookah como **paquete de configuración por tenant**.

### Los planes (borrador — validar con precios reales del mercado RD)

| | Base | Pro | Full |
|---|---|---|---|
| POS + inventario + e-CF | ✅ | ✅ | ✅ |
| Multi-almacén / multi-sucursal | — | ✅ | ✅ |
| CRM y leads | — | ✅ | ✅ |
| Módulo cafetería/restaurante | — | opcional | ✅ |
| Asistente de IA por WhatsApp | — | — | ✅ |

**Lo que hay que verificar antes de poner precios:** qué cobran Axentra,
Galileo, ef2, GyleERP y Alegra en RD hoy. No se fija precio contra el costo
propio; se fija contra el mercado.

**El costo variable real por tenant:** emisión de e-CF (pago por documento del
proveedor) + su parte del servidor. Eso define el piso del precio.

### Encaje con el ROADMAP de KORVEX

Esto es **Fase 3 — "Delegar y empaquetar"**: cambiar de "proyecto terminado" a
**retainer**. Y toca directamente el ítem *"Facturación y cobro dentro del
chat"* del backlog, que el propio roadmap describe como *"el salto de te
ahorro tiempo a te traigo dinero"*.

⚠️ **Pero:** el `ROADMAP.md` dice *"nada entra a construir mientras haya algo
en 🔴 sin cerrar"*, y la Parte 0 tenía dos ítems abiertos al 09/08/2026 (rotar
el token de Cloudflare, arreglar el paging file). **Verificar si se cerraron
antes de arrancar.**
