# 03 — Benchmark open source

> Todo lo evaluado el 2026-08-31, con licencia verificada y veredicto. La
> licencia importa tanto como las features: este código se va a **revender**.

---

## Resumen del veredicto

| Capa | Elegido | Licencia |
|---|---|---|
| **ERP + inventario + contabilidad** | **ERPNext v15** | GPLv3 |
| **POS** | **POSNext** *(a validar contra POS Awesome)* | AGPL-3.0 |
| **e-CF DGII** | **`korvex_ecf`, app propia** usando `ecf-dgii` | MIT (la lib) |
| **NCF tradicional** | `dgii-compliance` como **referencia**, no dependencia | GPL-3.0 |
| **CRM / leads** *(post-MVP)* | **Frappe CRM** | AGPL-3.0 |
| **Cafetería** *(post-MVP)* | **URY** | AGPL-3.0 |
| **WhatsApp** *(post-MVP)* | Integración por API con **KORVIS**, no app de Frappe | — |

---

## 1. La base: ERPNext / Frappe

**Elegido por decisión de Yedin (2026-08-31).**

### Lo que te da gratis desde el día 1
Inventario con variantes y lotes · multi-almacén · contabilidad de partida
doble · compras y proveedores · POS integrado · CRM básico · multi-moneda ·
sistema de permisos por rol · impresión de formatos · reportes · API REST
completa · **multi-tenancy nativo por site**.

### Lo que cuesta

| Costo | Detalle |
|---|---|
| **Python / MariaDB** | No comparte nada con el stack de KORVIS (Node/TS/Postgres). Dos plataformas que mantener. |
| **GPLv3** | Toda modificación distribuida queda GPLv3. Es aceptable, pero hay que saberlo. |
| **Marca** | "ERPNext" y "Frappe" son marcas registradas de Frappe Technologies. **No pueden ir en el nombre del producto, de la empresa, ni en el dominio.** Proyectos comerciales sí pueden decir "consultoría ERPNext". Hay que mantener el aviso `© Frappe Technologies Pvt. Ltd.` visible. |
| **Curva de Frappe** | DocTypes, hooks, bench, whitelisted methods. No es Django ni Flask; es su propio mundo. |
| **Hardware** | 4 GB RAM mínimo productivo, 50–100 GB NVMe recomendado. |

### Versión: **v15, no v16**

v16 salió el **12 de enero de 2026** (beta desde nov 2025).

⚠️ **Preliminar, no verificado.** POSNext declara "Frappe v15 **o superior**",
o sea que v16 debería funcionar *en el papel*. No se encontró evidencia pública
de apps de terceros corriendo en producción sobre v16.

**Decisión preliminar: v15**, por tener más kilómetros en el ecosistema contra
un deadline de 76 días. **Se confirma en el paso 1 del `HANDOFF.md`:** si el
bench de v16 instala POSNext y URY limpio, se arranca en v16 y se ahorra una
migración futura.

---

## 2. POS

### POSNext — **candidato principal**

| | |
|---|---|
| **Repo** | `DeeloaSociety/posnext` (fork de `BrainWise-DEV/POSNext`) |
| **Licencia** | **AGPL-3.0** |
| **Stack** | Vue 3 · Vite · Tailwind · TypeScript |
| **Requiere** | Frappe v15+ / ERPNext v15+ |
| **Offline** | ✅ IndexedDB + Service Workers + Web Workers, PWA real, sync en background |
| **Escáner** | ✅ Soporte de código de barras (búsqueda F4) |
| **Turnos** | ✅ Apertura/cierre con timer en vivo |
| **Otros** | Múltiples métodos de pago por transacción · pagos parciales · devoluciones con nota de crédito automática · facturas en borrador entre dispositivos · multi-almacén · cupones, "compre X lleve Y", gift cards, descuentos escalonados · multi-moneda |
| **Madurez** | v1.6.1 · 365 commits en develop · **el fork tiene solo 2 estrellas** |
| **Modo restaurante** | ❌ En roadmap, no implementado |

**Por qué es el candidato:** el **offline-first real** es lo que decide. Un POS
en RD que se cae con el internet no es un POS. Y encaja con la regla de
contingencia de la DGII (seguir vendiendo, drenar la cola al reconectar).

⚠️ **Riesgo:** poca comunidad. Verificar el repo padre (`BrainWise-DEV/POSNext`)
antes de adoptar el fork.

### POS Awesome — **alternativa a comparar**

| | |
|---|---|
| **Repos** | `defendicon/POS-Awesome-V15` · `wahni-green/POS-Awesome-V15` (original: Yrestom) |
| **Stack** | Vue.js + Vuetify |
| **Madurez** | El más veterano del ecosistema Frappe, más comunidad que POSNext |
| **Offline** | Más limitado que POSNext |

👉 **Probar los dos con el catálogo real antes de decidir.** Es un spike de
2–3 días, no una decisión de escritorio.

### Otros vistos
- **TailPOS** (Bailabs) — "offline first", pero el proyecto está frío.
- **X POS** (Kodlyft) — offline-first + escritorio. Menos documentado.
- **POS nativo de ERPNext** — funciona, pero es básico y su offline es débil.

---

## 3. Fiscal DGII

### `ecf-dgii` — **la pieza clave** ⭐

| | |
|---|---|
| **PyPI** | `ecf-dgii` v1.0.0 · **7 de mayo de 2026** |
| **Licencia** | **MIT** — la más permisiva de todo este documento |
| **Repo** | `SSD-Smart-Software-Development-SRL/ecf_dgii` |
| **Autor** | Smart Software Development SRL (dominicana) |
| **Qué hace** | SDK de la plataforma **ECF SSD** (proveedor certificado). Mandas JSON; ellos firman el XML con tu certificado, autentican por semilla ante DGII, envían y reintentan. |
| **Ambientes** | Test · Cert · Prod |
| **Tipos** | ⚠️ **NO VERIFICADO.** La página de PyPI **no documenta E32 ni RFCE.** Una fuente secundaria los menciona; la primaria no lo confirma. |
| **Requiere** | **Cuenta y API key (JWT Bearer) de ECF SSD.** No es una librería autónoma contra la DGII |
| **Actividad** | 2 contribuidores (autor: `dpena`), activa a mayo 2026 |

⚠️ **Lo que esto significa:** que sea Python y MIT es real y verificado. Que
cubra E32 y RFCE **no está verificado** — y **E32 + RFCE son el 95% de las
ventas de este POS.** Es exactamente lo que tiene que responder el spike de 2
días del `HANDOFF.md`, y por eso ese spike va antes que cualquier otra cosa.
Si no los cubre, el plan B es Alanube u otro proveedor local.

👉 **Es Python y es MIT.** En una app de Frappe es un `import`, no una
integración. Esta librería es la que hace que la decisión de ERPNext + la
decisión de proveedor certificado sean coherentes entre sí.

### `dgii-compliance` — referencia, no dependencia

| | |
|---|---|
| **Repo** | `LewisMojica/dgii-compliance` |
| **Licencia** | GPL-3.0 |
| **Qué hace** | App de Frappe: gestión del ciclo de vida de **secuencias NCF**, asignación a facturas, reportes DGII |
| **Qué NO hace** | **e-CF de la Ley 32-23.** Solo NCF tradicional |
| **Madurez** | 84 commits · **3 estrellas · 0 forks · sin releases · 5 issues abiertos** |

**Veredicto:** leerlo para entender cómo modelar secuencias NCF como DocTypes.
**No** depender de él en producción. Un solo mantenedor y cero adopción es
exactamente el perfil de dependencia que se abandona a mitad de camino.

### `victors1681/dgii-ecf` — TypeScript, no aplica aquí

MIT-ish, 90 estrellas, 274 commits, activa. Autenticación semilla, firma P12,
envío, consulta por TrackID, **E32 y RFCE confirmados**, tres ambientes.

**La mejor librería del ecosistema — pero es TypeScript.** Si la decisión #1
hubiera sido el stack de KORVIS, esta era la pieza central. Con ERPNext queda
como **referencia de implementación**, o como base si algún día se hace la
integración directa a DGII desde un servicio Node aparte.

### ⛔ `rob-erply/dgii_facturacion_electronica` — RETIRADO

**El repositorio da 404** (verificado 31/08/2026, barrido). Solo queda su sitio
de documentación en GitHub Pages. No es verificable ni reutilizable.

Lo que decía este documento antes, conservado como registro:

<details><summary>versión anterior</summary>

Módulo de **Odoo 18**, licencia **OPL-1 (propietaria)**. Implementa e-CF 31,
32, 33, 34, 46, 47; firma con .p12/.pfx; validación XSD contra esquemas
oficiales; QR; reintentos con backoff. Sus generadores usan `lxml` y `jinja2`
puros, técnicamente portables.

⚠️ **OPL-1 es propietaria. No se copia código de ahí.** Sirve como mapa de qué
hay que implementar, nada más.

</details>

👉 **Su reemplazo real está en `docs/07-ARQUITECTURA-REFERENCIA.md`:** el barrido
del 31/08 encontró implementaciones **con licencia permisiva y vivas** —
`victors1681/dgii-ecf` (TS, MIT, con RFCE) y `platinum-place/laravel-dgii` (PHP,
MIT, con las plantillas del XML). Esas sí se pueden portar legalmente.

### `SSD.../ecf_dgii` (.NET Core)
Los mismos autores de `ecf-dgii`, en .NET. Fuera de alcance.

---

## 4. CRM y leads (post-MVP)

### Frappe CRM — **elegido**
`frappe/crm` · AGPL-3.0 · **~3,377 estrellas**. App independiente, UI moderna,
gestión de leads y deals, integración nativa con WhatsApp documentada en
`docs.frappe.io/crm/whatsapp`. Corre en el **mismo bench**, comparte usuarios
y permisos.

### Descartados
- **Twenty CRM** (~44k estrellas) — excelente, pero **Node/TS**: tercer stack.
- **EspoCRM** — PHP: cuarto stack.
- **Chatwoot** — es soporte omnicanal, no CRM de ventas, y KORVIS ya cubre el
  canal de WhatsApp.

**Criterio:** con ERPNext ya elegido, meter un CRM de otro stack multiplica la
operación por nada. El CRM que vive en el mismo bench gana por default.

---

## 5. Cafetería (post-MVP)

### URY — **el mejor candidato**

| | |
|---|---|
| **Repo** | `ury-erp/ury` |
| **Licencia** | AGPL-3.0 |
| **Mantenedor** | Tridz Technologies, **con apoyo de Frappe** |
| **Madurez** | **295 estrellas · 174 forks · 386 commits** · v0.2.1 (nov 2025) |
| **Producción real** | ✅ "10+ locales durante 10 meses" |
| **Features** | POS de restaurante (local/takeaway/delivery/agregadores) · gestión de mesas · **KDS multi-cocina con ruteo de impresoras** · comandas KOT · turnos de caja · P&L diario · reportes por personal y sucursal |

Es la app de restaurante más seria del ecosistema Frappe: la única con respaldo
de Frappe y uso productivo verificable.

### Alternativas vistas
`frappe/hospitality` (oficial, orientada a hoteles) · `Rocket-Quack/erpnext_restaurant` ·
`alphabit-technology/erpnext-restaurant` · `techyidiots/Restaurant-POS-ERPNEXT` ·
`Quantumbitcore/Restaurant`. Todas más pequeñas y con menos actividad.

⚠️ **Antes de adoptar URY:** verificar que convive con POSNext en el mismo
bench. Dos POS compitiendo por el mismo Sales Invoice es una fuente real de
conflictos. Puede que la respuesta correcta sea **URY para todo** (retail +
cafetería) en vez de dos apps.

---

## 6. WhatsApp / asistente de IA

### La decisión: **NO se usa app de Frappe**

Existen `shridarpatil/frappe_whatsapp`, `frappe/waba_integration` y otras.
Funcionan, pero mandan plantillas y notificaciones — **no son un asistente
conversacional con RAG**.

👉 **KORVIS ya resuelve esto y está en producción.** Se integra por **API REST**
entre ERPNext y KORVIS: catálogo y stock salen de ERPNext, la conversación y el
RAG viven en KORVIS.

⚠️ **Recordar la lección del 06/08/2026** (`ADAP/docs/LECCIONES-MULTI-TENANT.md`):
el aislamiento multi-tenant no es solo de datos, también del **canal de salida**.
Cuando VAPELAND sea un tenant de KORVIS, hay que correr el checklist completo,
incluida la prueba de dos vías desde un teléfono real.

---

## 7. Hardware del POS

### Escáner de código de barras

| Modo | Cómo funciona | Veredicto |
|---|---|---|
| **HID Keyboard (keyboard wedge)** | El escáner se comporta como teclado. Cero configuración. Requiere que el campo tenga el foco. | ✅ **Empezar aquí.** Funciona con cualquier POS web. |
| **WebHID (HID POS)** | El código llega como **un solo evento**, sin depender del foco. Decodifica GS1/GTIN automáticamente. Reconexión automática. | Mejora posterior. Librería: `@point-of-sale/webhid-barcode-scanner` (Niels Leenheer, **MIT**). Soporta Honeywell, Zebra, DataLogic. |
| **Cámara del celular** | Sin hardware extra | Solo para inventario y conteos, no para caja |

### Impresión de recibos térmicos
ESC/POS. Dos caminos:
- **QZ Tray** — la vía probada. Existe `aisenyi/ERPNext POS Hardware Integrations`
  con impresión raw vía QZ Tray. Requiere agente instalado en la máquina.
- **`roquegv/Silent Print`** — app de Frappe para imprimir sin diálogo.
- WebUSB directo desde el navegador — posible, pero frágil entre modelos.

### Gaveta de dinero
Se abre por el puerto RJ11 de la impresora térmica con un comando ESC/POS. No
necesita integración propia: es un comando más en el ticket.

---

## Lo que se descartó y por qué

| Descartado | Razón |
|---|---|
| **Stack de KORVIS (Node/TS)** para el POS | Decisión de Yedin. Costo: 3–5 meses de construir POS + inventario + contabilidad desde cero. Beneficio que se pierde: un solo stack y reuso directo del asistente. |
| **Odoo Community** | LGPLv3 es más amigable que GPLv3 para módulos propios, y el POS es maduro — pero sigue siendo Python de otro framework, el e-CF también hay que escribirlo, y la presión comercial hacia Enterprise es constante. |
| **Medusa / Vendure / Saleor** | Son commerce headless, no ERP. Sin contabilidad, sin compras, sin POS de mostrador. |
| **FinOpenPOS** (Next.js 16 + Drizzle, **MIT**) | Excelente encaje con el stack de KORVIS y con módulo fiscal brasileño (NF-e/NFC-e) de referencia — **pero irrelevante tras elegir ERPNext.** Anotado por si la decisión #1 se revisa. |
| **`satisfecho/pos`** (Angular + FastAPI, MIT, multi-tenant, 7,070 commits) | Buen proyecto pero **quinto stack** (Angular + Python FastAPI), y es restaurante, no retail. |
| **Construir el POS desde cero** | 3–5 meses. Contra un deadline de 76 días, no es una opción. |
