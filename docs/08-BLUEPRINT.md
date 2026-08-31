# KORVEXCIO — Plan maestro de desarrollo

> Fase 0 verificada + plan de fases y microslices hasta producción.
> Escrito 2026-08-31, actualizado con la **luz verde de instalación en
> `korvex-node1`** dada por la sesión de KORVIS con números medidos en vivo.
> Estructura tomada de `C:\PROYECTOS\the-architect` (plantilla de blueprint),
> adaptada de web-app a app de Frappe.

---

## 1. Contexto — por qué existe este plan

KORVEXCIO estaba en estado ⚪ Semilla: cero código, decisiones tomadas, y **tres
huecos de información** que el `HANDOFF.md` marcaba como capaces de cambiarle la
forma al proyecto. Los documentos `docs/07` y el `HANDOFF.md` venían de barridos
de subagente **sin verificar de segunda mano** — un mapa de dónde buscar, no
hechos probados.

El reloj: **15 de noviembre de 2026**, e-CF obligatorio para pequeños/micro/no
clasificados. **76 días.** Multa 5–50 salarios mínimos.

Este plan hace tres cosas:
1. **Cierra el paso 1 de Fase 0** — los 4 repos ⭐ verificados con evidencia (§2).
2. **Resuelve el hosting** — instalación en `korvex-node1` con luz verde y números
   medidos, y las reglas del nodo incorporadas como restricciones de diseño (§5.1).
3. **Entrega el plan completo** en fases y microslices verificables hasta el
   go-live, con seguridad y revisiones repartidas por fase (§7.1).

**Resultado esperado:** dos tenants vendiendo con e-CF válido antes del
15/11/2026, sobre una app propia que sobrevive un `git pull` de ERPNext, en un
nodo que ya tiene un banco en producción y no se puede romper.

---

## 2. Lo verificado — evidencia, no barrido

### 2.1 Los 4 repos ⭐ (paso 1 de Fase 0 — **CERRADO**)

| Repo | Licencia | ★ / forks | E32 | RFCE | Veredicto |
|---|---|---|---|---|---|
| `wilmerm/alanube-python` | **MIT** ✅ | 3 / 4 | ✅ tipo 32 en la tabla del README | ❌ **no documentado** | Python nativo, pero sin RFCE |
| `victors1681/dgii-ecf` | **MIT** ✅ (`package.json`, v1.8.5) | 99 / 72 | ✅ | ✅ **`sendSummary`, `convertECF32ToRFCE`** | Única implementación de RFCE copiable. Es TypeScript |
| `platinum-place/laravel-dgii` | **MIT** ✅ | 8 / 3 | ✅ plantillas Blade e-CF / consumo / anulación / acuse; `testecf`·`certecf`·`ecf` | 🟡 no confirmado explícito | Plantillas XML traducibles a Jinja2 |
| `LewisMojica/dgii-compliance` | GPL-3.0 | 3 / 0 · 84 commits · 0 releases | ❌ solo NCF | ❌ | Confirmado: referencia, **no** dependencia |

### 2.2 Verificaciones extra

| Cosa | Resultado |
|---|---|
| `ecf-dgii` (PyPI, ECF SSD) | **MIT**, v1.0.0 del **7-may-2026**, Python ≥3.10, ambientes **test/cert/prod** ✅ — pero **solo documenta Factura de Crédito Fiscal (E31)**. Ni E32 ni RFCE |
| `erpnext_mexico_compliance` | **MIT**, `--branch version-15`, guarda el XML en **custom fields** de Sales Invoice → confirma el "no copies a México" del doc 07 |
| `DeeloaSociety/posnext` | **AGPL-3.0**, Frappe/ERPNext **15+**, **Vue 3 Composition API**, offline-first con IndexedDB + background sync. **2★ / 1 fork** |
| `yrestom/POS-Awesome` | GPL-3.0, 509★ / 725 forks, pero **README declara v14**, **Vue 2 + Vuetify**, **offline no mencionado** |
| Alanube (proveedor) | Aprobado por DGII desde 2021. Sandbox: `https://sandbox.alanube.co/dom/v1` |
| RFCE — spec oficial | DGII publica **"Formato Resumen Factura Consumo Electrónica v1.0"** (PDF). Endpoint: `fc.dgii.gov.do/recepcionfc` *(de `docs/02`)* |

### 2.3 Estado del entorno

**Máquina DEV** (medido):
```
git 2.53.0.windows.2 ✅   Python 3.12.10 ✅   node v25.9.0 ✅
RAM_GB: 15.8   CPU: i7-1165G7 / 8 hilos   C_Free_GB: 210.9
docker / wsl: no instalados        ✅ ya no son blocker — ver D11
tailscale                          ✅ INSTALADO Y FUNCIONANDO
```
```
$ tailscale status
100.99.101.14   yeyow          windows  -
100.102.203.91  korvex-node1   linux    -      ← en línea
```
```
$ cd C:/PROYECTOS/KORVEXCIO && git rev-parse --is-inside-work-tree
fatal: not a git repository (or any of the parent directories): .git
```

**Nodo `korvex-node1`** — medido **por esta sesión, vía Tailscale**, no de documento:
```
$ ssh -i ~/.ssh/korvex_server korvex@100.102.203.91
korvex-node1   up 1 day, 18:14   load average: 0.10, 0.20, 0.23
               total   used   free   shared  buff/cache  available
Mem:            14Gi   2.7Gi   10Gi    150Mi       2.5Gi        12Gi
Swap:          4.0Gi      0B  4.0Gi
Filesystem                         Size  Used Avail Use%  Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   21G   73G  23%  /
nproc: 6
curl -o /dev/null -w "%{http_code}" https://github.com -> 200      ← IPv4 sano
```
```
$ docker compose ls
korvex      running(6)   /opt/korvex/app/docker/docker-compose.yml
openwa      running(1)   /opt/korvex/openwa/docker-compose.yml
plausible   running(3)   /opt/korvex/stacks/plausible/compose.yml

$ docker system df
Images  6.07GB   Build Cache  4.455GB  (2.168GB RECLAIMABLE)
```
Consumo real de los contenedores: ~1.8 GB en total. **GlitchTip y OpenWA ya tienen
`mem_limit` (512M/256M/2G); Plausible y los Postgres/Redis de KORVIS no** — aparecen
con `14.89GiB`, o sea sin tope. La pila de KORVEXCIO sí lo lleva (regla 4 del nodo).

Alarma de disco activa desde el 31/08: avisa al **80%**, crítico al **90%**, por correo.

🟡 **Deuda menor pendiente:** el `~/.ssh/config` todavía dice `HostName 10.0.0.193`
(la red vieja), así que `ssh korvex-host` falla y hay que ir por la IP de Tailscale a
mano. Se corrige en S0.2 — un renglón.

### 2.4 El hueco del camino crítico — precisado, no cerrado

**RFCE no está documentado en ninguna vía Python.** Existe en TypeScript bajo MIT
(`victors1681/dgii-ecf`) y contra el endpoint directo de la DGII.

Y RFCE **no es un caso borde**: los E32 bajo RD$250,000 no se transmiten uno a
uno — se acumulan y van en resumen. En un vape shop y una cafetería eso es
**~100% del volumen**. Sin RFCE, cada venta de RD$300 sería una transmisión
individual. Por eso es el gate.

---

## 3. Decisiones nuevas (D10–D18) y correcciones

Las D1–D9 viven en `TECH_STACK.md`. Estas se agregan ahí al cerrar Fase 0.

| # | Decisión | Por qué |
|---|---|---|
| **D10** | **Hosting: `korvex-node1` + Cloudflare Tunnel. Luz verde dada** por la sesión de KORVIS con números medidos el 31/08 | 72.4 GB libres y 12 GB de RAM disponible contra ~4 GB / 5–8 GB que pide un bench de 2 sites. Coincide con `docs/04`: *"1 bench, 1–2 sites → ✅ Sí, con holgura razonable"*. **Techo = disco, no RAM.** Salida documentada: VPS con el mismo compose, o Frappe Cloud Servers (US$40/mo) |
| **D11** | **El bench vive en el nodo, no en la laptop.** Se descarta instalar WSL2 + Docker Desktop en DEV como prerrequisito | El nodo ya tiene Docker Engine nativo + systemd. Montar una segunda pila en Windows es trabajo que no compra nada contra 76 días. **DEV escribe código y hace push; el nodo lo consume** (regla 1 del nodo). Un bench local queda como mejora opcional si el ciclo de iteración duele |
| **D12** | **Dos negocios desde v1.** Vape shop y cafetería arrancan juntos. *Corrección de Yedin* | **Deroga D4.** El MVP ya no es "un POS"; es la plataforma con los dos negocios |
| **D13** | **Se planifica para DOS RNC** (caso conservador): dos `Company` con su `tax_id`, dos `.p12`, dos juegos de secuencias e-NCF, dos configuraciones de proveedor | Sin confirmar si son una o dos entidades. Con Companies, colapsar a una es trivial y partir a dos también — a diferencia de los sites |
| **D19** ⭐ | **Un site por CLIENTE. Una `Company` de ERPNext por NEGOCIO dentro del site.** *Propuesta de Yedin, adoptada con una condición.* Este cliente = `korvexcio.korvexdev.cc` con Companies **VAPELAND** y **Cafetería**. El login decide qué ves; el dueño ve las dos y administra sus usuarios | **Revisa D6, no la deroga.** Ver §5.2 |
| **D14** | **Cafetería en modo mostrador.** Sin mesas, sin comandas, sin KDS. URY se difiere a Fase 7 | Confirmado por Yedin — coincide con el supuesto 3 del `PRD.md`, que deja de ser supuesto. El modelo de datos se deja sin bloquear para que mesas entren después sin migración |
| **D15** | **POS Awesome descartado** | Vue 2 (**EOL desde dic-2023**) + README en **v14** + sin offline documentado. Producto nuevo en 2026 sobre Vue 2 es deuda de nacimiento |
| **D16** | **POS: decisión diferida al spike S0.8**, entre **POS nativo de ERPNext** y **POSNext**. Sesgo declarado hacia el nativo | El giro: **la cola offline la escribes tú de todos modos.** La contingencia de la DGII necesita documentos pre-computados y pre-firmados (patrón `ZATCA Precomputed Invoice`), y el offline de POSNext no sabe nada de e-CF. Si la contingencia vive en el módulo `ecf`, el POS solo tiene que ser una pantalla extensible — y la nativa no se forkea, no es AGPL, y la mantiene Frappe |
| **D17** | **Spike fiscal: proveedores primero, en paralelo.** Correos el día 0; el spike técnico arranca con la respuesta | No se queman 2 días esperando. Plan B (portar RFCE de `dgii-ecf`) queda armado por si ambos dicen que no |
| **D18** | **v15 vs v16 se decide con el bench levantado, no en el papel** — es el **primer slice del proyecto** (S0.5) | D2 está marcada *"preliminar, NO verificada"*. Si POSNext y URY instalan limpio en v16, se arranca en v16 y se ahorra una migración. Si no, v15 **y queda escrito por qué** |

### Correcciones a decisiones previas

| Decisión | Estado |
|---|---|
| **D2** — "v15, no v16" | 🟡 **Se resuelve en S0.5.** Es el paso 1 real del proyecto |
| **D3** — "principal ECF SSD vía `ecf-dgii`" | 🔴 **REVISADA.** Verificado: `ecf-dgii` solo documenta E31. Pasa a candidato #2. La interfaz `FiscalProvider` **se mantiene y ahora es más necesaria** |
| **D4** — "MVP sin cafetería" | 🔴 **DEROGADA por D12** |
| **D6** — "un site por cliente" | 🟡 **REVISADA por D19.** Sigue vigente **entre clientes** (cliente 2 = site propio, innegociable). Dentro de un cliente, los negocios son `Company`. Ver §5.2 |
| `HANDOFF.md` | 🔴 **Manda abrir Claude Code en `C:\PROYECTOS\VAPELAND`.** Esa carpeta ya se llama `KORVEXCIO`. Se corrige en S0.1 |

---

## 4. Calendario a la inversa

```
15/11  ◄── deadline duro e-CF
        │  ~2 semanas: certificación como emisor + estabilización
01/11  ◄── PRODUCCIÓN ESTABLE (Fase 6 cerrada)
        │  1 semana: carga de datos, permisos, capacitación
25/10  ◄── desarrollo terminado (Fase 5 cerrada)
        │  1 semana: POS + hardware              → Fase 4
17/10   │
        │  1 semana: módulo retail               → Fase 3   ⬅ paralelizable (§7.2)
10/10   │
        │  3 semanas: MÓDULO ECF                 → Fase 2   ⬅ camino crítico
15/09   │
        │  1 semana: esqueleto de la app         → Fase 1
08/09   │
        │  1 semana: REDUCIR RIESGO              → Fase 0   ⬅ empieza hoy
31/08  ◄── hoy
```

**Dos plazos de calendario que no se comprimen y arrancan HOY:** certificado
digital (3–10 días hábiles, US$30–70/año, **por cada RNC**) y el RNC del cliente,
aún sin confirmar. Bloquean la certificación, no el desarrollo.

---

## 5. Arquitectura objetivo

```
        korvex-node1 · Ubuntu Server 26.04 · i5-9500 6c · 14 GB · 98 GB
        ┌──────────────────────────────┬──────────────────────────────┐
        │  PROYECTO COMPOSE `korvexcio`│  KORVIS  (EN PRODUCCIÓN)     │
        │  red propia · tope ~6 GB RAM │  ⚠️ banco ADAP + 2 bots vivos│
        │  ┌────────────────────────┐  │  ┌────────────────────────┐  │
        │  │ MariaDB · Redis×2      │  │  │ Postgres 16 + pgvector │  │
        │  │ (SUYOS — no se reusa   │  │  │ Redis 7                │  │
        │  │  nada de KORVIS)       │  │  │ (Docker, korvex-*)     │  │
        │  ├────────────────────────┤  │  ├────────────────────────┤  │
        │  │ backend · frontend     │  │  │ api·dashboard·ops      │  │
        │  │ websocket · scheduler  │  │  │ (systemd nativo)       │  │
        │  │ queue-short/long       │  │  │ OpenWA · GlitchTip     │  │
        │  ├────────────────────────┤  │  │ Plausible              │  │
        │  │ apps/                  │  │  └────────────────────────┘  │
        │  │  frappe · erpnext      │  │                              │
        │  │  [posnext si gana]     │  └──────────────────────────────┘
        │  │  korvexcio ⭐          │
        │  ├────────────────────────┤     TODO EN LOOPBACK.
        │  │ sites/                 │     Se entra por Tailscale.
        │  │  korvexcio.korvexdev.cc│     Nada al túnel público
        │  │   ├ Company VAPELAND   │     hasta que sea real.
        │  │   └ Company Cafetería  │
        │  │  demo.korvexdev.cc     │
        │  └────────────────────────┘
        └──────────────────────────────┘
                        │
              cloudflared (compartido) → *.korvexdev.cc
```

> **Detalle que importa:** un site llamado `korvexcio.korvexdev.cc` **no está
> publicado** por llamarse así. El nombre es para la multi-tenancy por DNS de
> Frappe. Mientras no exista regla de ingress en Cloudflare, se llega por
> `curl -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080` a través de
> Tailscale. Eso cumple la regla 6 del nodo.

**Estructura del repo** (`docs/06`, con la corrección de `docs/07` §3.7 —
directorio `custom/` en vez de fixtures):

```
KORVEXCIO/
├── korvexcio/                     ← la app de Frappe
│   ├── hooks.py · modules.txt     ← "ECF", "Retail"
│   ├── custom/*.json              ← custom fields del producto (patrón KSA)
│   ├── ecf/
│   │   ├── doctype/               ← dgii_settings · dgii_digital_certificate ·
│   │   │                            secuencia_encf · ecf · ecf_integration_log ·
│   │   │                            ecf_contingencia · acecf
│   │   ├── providers/             ← base.py · alanube.py · ssd.py
│   │   ├── templates/             ← ecf_31.xml · ecf_32.xml · ecf_34.xml · rfce.xml
│   │   ├── tasks.py               ← retry_pending · poll_status · refresh_token
│   │   └── print_format/          ← Representación Impresa con QR
│   └── retail/
│       ├── item_attributes.py · fefo.py · age_verification.py
│       └── report/
├── apps.json                      ← qué upstream se instala y en qué branch
├── docker/                        ← compose propio: `name: korvexcio`, red propia,
│                                    mem_limit por servicio, puertos en 127.0.0.1
├── scripts/                       ← alta de tenant · seeds · carga de catálogo
└── docs/ · HANDOFF.md · CLAUDE.md · PRD.md · TECH_STACK.md · PROGRESO.md
```

---

## 5.2 Un site por cliente, una Company por negocio (D19)

### Lo que se pidió

Una sola URL. El login decide qué ves: usuario de la vapería entra a la vapería,
usuario de la cafetería a la cafetería. El dueño de ambos ve **un dashboard con sus
dos negocios juntos** y **administra sus propios usuarios**. Sin inventar
subdominios por cada cosa.

### Por qué se puede — es el patrón nativo de ERPNext

Un site de Frappe soporta **N `Company`**. Cada `Company` tiene su `tax_id` (el RNC),
sus almacenes, sus cost centers, sus naming series y su POS Profile. El usuario se
restringe con **User Permission sobre Company**. El dueño con acceso a las dos ve el
consolidado. **Cero código nuestro.**

Y encaja con D13: **dos RNC = dos Companies con su `tax_id`**, no dos sites.

### Lo que cambia, dicho sin adornos

| | D6 original (un site por negocio) | D19 (una Company por negocio) |
|---|---|---|
| Aislamiento | **Físico** — una DB por cada uno | **Lógico** — campo `company` + User Permission |
| Riesgo de fuga | Estructuralmente imposible | **Real** si una query o un reporte olvida filtrar |
| Vista consolidada del dueño | **Imposible** sin escribir un agregador cross-DB | **Nativa** |
| Login | Dos URLs, dos sesiones | Una URL, una sesión |
| Costo de un negocio nuevo | Site + DB + nginx + recursos | Una fila |
| Disco | ×2 | ×1 ⭐ *(y el disco es el techo del nodo)* |

Pasar a aislamiento lógico es adoptar **exactamente la clase de riesgo que mordió en
KORVIS el 06/08/2026**. Y en ERPNext no es teórico — hay dos casos documentados:

- **PR [#44695](https://github.com/frappe/erpnext/pull/44695) / backport
  [#44752](https://github.com/frappe/erpnext/pull/44752)** — *"User Permissions are
  not checked in Financial Statements (Profit And Loss Report, Balance Sheet
  Report)"*. Un usuario con permisos restringidos veía datos de todos los cost
  centers. **Merged**, publicado en 14.78.3 el 18/12/2024.
- **Issue [#43652](https://github.com/frappe/erpnext/issues/43652)** (ERPNext v15.37 /
  Frappe v15.43) — *"Admin A can see all the users of Company A and Company B and vice
  versa"*. **Cerrado como `not planned`.** O sea: el DocType `User` **no** está
  aislado por Company, y no lo van a aislar.

### La condición que hace la decisión segura

> **Un site por CLIENTE. Una `Company` por NEGOCIO dentro de ese site.**

Porque una fuga entre la vapería y la cafetería **del mismo dueño** no es una fuga —
son sus propios datos, y él ya tiene acceso a los dos. Una fuga entre **dos clientes
que te pagan** sí lo es, y el issue #43652 (cerrado como *no planeado*) la vuelve
imposible de arreglar después.

| Quién | Dónde vive |
|---|---|
| **Cliente 1** (dueño de vapería + cafetería) | `korvexcio.korvexdev.cc` — 2 Companies |
| **Demo / staging** | `demo.korvexdev.cc` — y es la prueba de que el modelo por cliente funciona, sin necesitar un cliente real todavía |
| **Cliente 2** (otro dueño) | **Su propio site.** Nunca una Company más aquí |

⚠️ **Nota de convención:** `korvexcio` es el nombre del producto, no del cliente. Si
mañana quieres que cada cliente tenga su subdominio propio, `bench rename-site` lo
hace — es barato ahora (2 Companies, sin datos reales) y caro después. **Decisión
diferida a propósito, anotada para no olvidarla.**

### Lo que esto agrega al trabajo

1. **`DGII Settings` deja de ser Single** → DocType con `company` (Link, único). Cada
   Company tiene su ambiente, su proveedor y sus credenciales. *(Cambia S2.1.)*
2. **La regla 10 del `CLAUDE.md` pasa de importante a crítica.** Con dos Companies en
   una base, el cliente HTTP del proveedor de e-CF **se resuelve por operación, desde
   la Company del documento** — nunca se construye una vez al arrancar. Si no se
   puede resolver, **no se envía**.
3. **Test de aislamiento obligatorio** (S1.8): un cajero de la vapería no ve ni una
   factura, ni un ítem, ni un reporte de la cafetería. Y al revés.
4. **Nuestros reportes filtran por `company` explícitamente y se testean.** No se
   confía en que User Permission lo haga solo — el PR #44695 existe justamente porque
   una vez no lo hizo.

---

## 5.1 El nodo — luz verde, y las reglas que la acompañan

### La cuenta, con números medidos

| | Medido 31/08 | Lo que pide KORVEXCIO | Margen |
|---|---|---|---|
| **RAM** | 12 GB disponibles (2.6 en uso) | ~4 GB (bench, 2 sites) · **tope duro 6 GB** | ✅ sobra |
| **Disco** | **72.4 GB libres** de 97.9 | 5–8 GB inicial · 12–30 GB al año 1 | ✅ cabe, 🟡 **es el techo** |
| **CPU** | i5-9500, 6 núcleos, load 0.8 | ráfagas de POS, no carga sostenida | ✅ sobra |
| **Cache Docker** | 4.4 GB, **2.17 recuperables** | `docker builder prune -f` antes de instalar | ✅ |

Coincide con lo que ya decía `docs/04-ARQUITECTURA.md`: *"1 bench, 1–2 sites
(VAPELAND + demo) → ✅ Sí, con holgura razonable"*. Y con el `ROADMAP.md`: *"el
techo del nodo 1 no es RAM, es disco"*.

### ⚠️ Lo que hay ahí y no se puede romper

El nodo corre **KORVIS en producción con un banco (ADAP) y dos bots de WhatsApp
en vivo**. Postgres 16 + pgvector y Redis 7 en Docker · api/dashboard/ops como
servicios systemd desde `/opt/korvex/app` · OpenWA · GlitchTip · Plausible ·
cloudflared. **Lo que se rompa ahí cuesta credibilidad delante de quien paga.**

### Las 6 reglas del nodo — restricciones de diseño, no sugerencias

| # | Regla | Cómo aterriza en KORVEXCIO |
|---|---|---|
| 1 | **Nunca editar código en el servidor** | Push en DEV → `git pull` en el nodo → `bench restart`. ⚠️ **Un `git status` sucio en el nodo bloquea el pull sin ruido**: reinicia con código viejo y el despliegue *parece* haber funcionado. **Todo despliegue verifica el SHA, no el exit code** |
| 2 | **Servicios de datos solo en `127.0.0.1`** | MariaDB y los 2 Redis del bench en loopback. Se verifica con `ss -tlnp`, **nunca leyendo el YAML** |
| 3 | **Proyecto de Compose y red propios** | `name: korvexcio` explícito + `--project-directory .`. **ERPNext trae su MariaDB y su Redis: NO se reusan los de KORVIS.** Dos sistemas compartiendo base es la frontera imposible |
| 4 | **Límites de memoria explícitos** | `mem_limit` por servicio, **tope ~6 GB para toda la pila**. No por falta de RAM: para que un worker desbocado no ahogue a KORVIS |
| 5 | **`docker builder prune -f` antes de instalar** | Devuelve ~2 GB. Va en el checklist previo (S0.4) |
| 6 | **Nada nuevo detrás del túnel público hasta que sea real** | Los dos sites se crean y se prueban por loopback+Tailscale. Cloudflare Access delante de cualquier panel administrativo cuando se publiquen |

### Trampas ya pagadas que aplican a este trabajo

- 🔴 **IPv4 puede estar caído con todo lo demás funcionando.** El nodo viajó con IP
  estática de otra red: IPv6 levantó solo por SLAAC y se llevó el tráfico —
  el túnel, los servicios y las APIs de IA perfectos, **y solo GitHub roto**, por
  ser IPv4-only. **Antes de clonar `frappe_docker`:**
  `ssh korvex-host 'curl -s -o /dev/null -w "%{http_code}\n" https://github.com'`
  → debe dar **200**. Un `000` = IPv4 caído. Verificado en 200 el 31/08.
- **`sudo` pide contraseña** salvo reiniciar los tres servicios de KORVIS. Todo lo
  demás lo corre Yedin con **`ssh -t korvex-host "sudo …"`** — sin `-t` sale
  `sudo: A terminal is required to authenticate`, porque el config tiene `BatchMode yes`.
- **El `ufw` solo abre el 22 desde `10.0.0.0/24` (red vieja) y Tailscale.** Si algún
  día hay que abrir un puerto, se abre para la interfaz de Tailscale, no para la LAN.
- **`netplan` mezcla los `*.yaml` por orden alfabético** y el último pisa al primero.
  No tocarlo en este proyecto.

### Fecha de revisión

**El tercer tenant de pago.** Ese día se compra el segundo nodo o se va a VPS — y
como el artefacto es el mismo `docker compose`, migrar es restaurar un backup.
Por eso arrancar aquí **no cierra ninguna puerta**.

**Lo que sigue sin resolver y no es técnico:** qué pasa con la caja de los dos
locales **los días que la máquina viaje**. La máquina deja de viajar · KORVEXCIO se
muda a VPS al entrar en producción · o se opera en contingencia declarándola por
la OFV. **Decisión de Yedin, y tiene que estar tomada antes del go-live.** Lo que
lo hace sobrevivible es la regla 4 del `CLAUDE.md`: sin internet, el negocio sigue
vendiendo. Un POS que aguanta sin red aguanta sin nodo — **si la contingencia está
construida y probada**, que por eso es gate de Fase 6.

---

## 6. Las fases

Un slice se cierra **solo** con la salida real del comando que lo probó (R1). Sin
evidencia, la frase es *"escrito pero SIN verificar — falta correr X"*.

---

### FASE 0 — Reducir riesgo · 31/08 → 07/09

> Cero código de producto. Objetivo: matar los tres desconocidos y dejar el bench
> de pie sin tocarle un pelo a KORVIS.

**S0.0 · Prerrequisitos de 5 minutos** *(no son slices de producto, son higiene —
sin ellos no hay dónde anotar nada ni cómo llegar al nodo)*

| | Qué | Verificación | Dueño |
|---|---|---|---|
| **S0.1** | **Repo git con remote** antes de la primera línea (§6 `CONVENCIONES`). `git init`, `.gitignore` (`sites/`, `.env`, `__pycache__/`, `node_modules/`, `*.p12`), `.env.example`, commit inicial de los docs. **Y corregir `HANDOFF.md`**, que manda abrir Claude Code en `C:\PROYECTOS\VAPELAND` — esa carpeta ya se llama `KORVEXCIO` | `git remote -v` → `origin  https://github.com/yedinrumba-eng/KORVEXCIO.git`<br>`git log --oneline -1`<br>`grep -r "PROYECTOS.VAPELAND" .` → sin resultados | Claude |
| **S0.1b** | **Secure-Vibe modo A + pre-commit** (§7.3): clonar el repo, instalar la skill `/secure-vibe`, copiar `plantillas/ES/CLAUDE.md` y `AGENTS.md` al repo, y activar `pre-commit` con **gitleaks** | `/secure-vibe` aparece en las skills · `pre-commit run --all-files` pasa · un commit con una clave falsa **es rechazado** | Claude |
| **S0.2** | ✅ Tailscale **ya instalado y verificado**. Queda **corregir `~/.ssh/config`**: `HostName 10.0.0.193` → **`100.102.203.91`** | `ssh korvex-host 'uptime'` responde **sin pasar la IP a mano** | Claude |
| **S0.3** | **Correos a proveedores e-CF** — Alanube y ECF SSD. Texto en §6.1. Se manda **hoy**, en paralelo con todo | Los 2 correos con fecha; respuestas en `docs/09-PROVEEDORES-ECF.md` | **Yedin** |

**S0.4 · Checklist previo del nodo** — el §6 de `ACCESO-Y-REGLAS-DEL-NODO.md`,
corrido tal cual antes de instalar nada:

```bash
ssh korvex-host 'df -h /'                                    # margen real hoy
ssh korvex-host 'docker builder prune -f'                    # ~2 GB de vuelta
ssh korvex-host 'cat /opt/korvex/backups/status.json'        # backup del día ok
ssh korvex-host 'curl -s -o /dev/null -w "%{http_code}\n" https://github.com'   # 200
ssh korvex-host 'systemctl status korvex-api --no-pager | head -3'
ssh korvex-host 'curl -s http://127.0.0.1:4000/health'
```
**Verificación:** las 6 salidas pegadas. El `github.com` **tiene que dar 200** o no
se clona nada (trampa de IPv4). Se guarda como línea base para comparar después.

---

**S0.5 · ⭐ EL PRIMER SLICE REAL — confirmar D2: v16 o v15**

> *"Es el paso 1 real del proyecto, y no se adelanta nada hasta cerrarlo."*

Levantar el bench en el nodo y ver **qué instala limpio**. `apps.json` de prueba
con `erpnext`, `posnext` y `ury` apuntando a v16; si alguna revienta, se baja a v15
y **queda escrito por qué**.

Restricciones que se aplican desde el primer `docker compose`, no después:
- `name: korvexcio` + red propia + `--project-directory .` (regla 3)
- `mem_limit` por servicio, **tope ~6 GB** (regla 4)
- puertos **solo en `127.0.0.1`** (regla 2)
- `frappe_docker` clonado **fuera del repo** — es upstream, no se versiona

**Verificación:**
```bash
docker compose -p korvexcio ps                    # todos up
bench version                                     # versiones reales de cada app
docker stats --no-stream                          # ninguna sobre su mem_limit
ss -tlnp | grep -E '3306|6379|8080'               # todo en 127.0.0.1
systemctl status korvex-api                       # KORVIS intacto
curl -s http://127.0.0.1:4000/health              # KORVIS intacto
df -h /                                           # cuánto se comió
```
**Entregable:** `docs/13-VERSION-FRAPPE.md` con la matriz de qué instaló y qué no,
y **D2 cerrada con su porqué**.

---

**S0.6 · El site del cliente y sus dos Companies**

| | Qué | Verificación |
|---|---|---|
| **S0.6** | Site `korvexcio.korvexdev.cc` con erpnext instalado | `curl -H "Host: korvexcio.korvexdev.cc" http://127.0.0.1:8080/api/method/ping` → `{"message":"pong"}`<br>`bench --site korvexcio.korvexdev.cc list-apps` |
| **S0.7** | Las **dos Companies** (D19): **VAPELAND** y **Cafetería**, cada una con su `tax_id` (RNC), su almacén, su cost center, su naming series y su moneda. *Los RNC reales entran cuando el cliente los confirme; hasta entonces, de prueba* | `frappe.get_all("Company", fields=["name","tax_id","default_currency"])` devuelve las dos<br>Un ítem creado en una **no** aparece en el almacén de la otra |
| **S0.7b** | Site `demo.korvexdev.cc` — **el modelo por cliente se prueba el día 1, no al final.** Es el staging y la prueba de que cliente 2 es posible sin tocar nada | Dos DBs distintas en `SHOW DATABASES`; un cambio en uno **no** aparece en el otro |

---

**S0.8 → S0.12 · Los spikes y el cierre**

| Slice | Qué | Verificación | Dueño |
|---|---|---|---|
| **S0.8** | **Spike POS** *(timebox 2 días)*. Matriz de §6.2 escrita **antes** de instalar. Prueba dura: cortar la red del proyecto compose, 5 ventas, reconectar, verificar las 5 | `docs/10-SPIKE-POS.md` con la tabla llena, evidencia por criterio y veredicto de una línea | Claude |
| **S0.9** | **Spike fiscal** *(timebox 2 días)* — **EL GATE**. Ruta según S0.3: **A)** proveedor con RFCE → sandbox → E32 → TrackID → RFCE · **B)** portar de `victors1681/dgii-ecf` (MIT) + XSD oficial → Jinja2 → firmar → POST a `fc.dgii.gov.do/recepcionfc` en TesteCF · **C)** ninguna funciona → **PARAR Y ESCALAR** | **TrackID real de TesteCF**, pegado en `docs/11-SPIKE-FISCAL.md`. Sin TrackID no se declara nada | Claude |
| **S0.10** | **Cuota de disco de KORVEXCIO.** Retención de `bench backup`, alarma propia, y contraste contra la alarma del nodo (80/90%) que ya existe | La retención configurada + una corrida de `du -sh` sobre los volúmenes del proyecto | Claude |
| **S0.11** | **Catálogo real.** Pedir el Excel; si no hay, modelar 20 SKUs representativos con variantes (Sabor · Nicotina mg · Tamaño ml · Ohmiaje) | `frappe.db.count("Item")` > 0 y un template con sus variantes visible en la UI | Claude |
| **S0.12** | Cerrar Fase 0: `PROGRESO.md` (hitos, D10–D18, derogación de D4, revisión de D3, **cierre de D2**), `TECH_STACK.md`, `docs/07` (quitar el aviso "sin verificar" de los 4 ⭐), `data/korvex.json` ⚪→🔵, y **`MASTERGUIDE.md`** — KORVEXCIO entra como segundo inquilino del nodo | `git log` muestra el commit; el mapa refleja el estado nuevo | Claude |

**🚦 GATE DE FASE 0 — no se pasa a Fase 1 sin esto:**
1. **S0.5 cerrada**: D2 resuelta con evidencia, bench de pie, **KORVIS intacto**.
2. **S0.9** con TrackID real de TesteCF, o el veredicto escrito de por qué fallaron las tres vías.
3. **S0.8** con veredicto de POS escrito y con evidencia.

**Si las tres vías de S0.9 fallan: se para y se escala.** No se improvisa un
reemplazo (R2). El proyecto cambiaría de forma y eso es una conversación.

#### 6.1 — Texto del correo a proveedores (S0.3)

> Asunto: Consulta técnica — soporte de RFCE (Resumen de Factura de Consumo) para POS de alto volumen
>
> Buen día. Estamos integrando un punto de venta para retail en RD y necesitamos
> confirmar por escrito, antes de contratar:
>
> 1. ¿Su API soporta el **Resumen de Factura de Consumo Electrónica (RFCE)** para
>    los e-CF tipo 32 menores a RD$250,000? ¿Con qué endpoint y qué formato?
> 2. ¿Soportan e-CF **tipo 32** (consumo), **31** (crédito fiscal) y **34** (nota de crédito)?
> 3. ¿Tienen ambiente de pruebas contra **TesteCF** de la DGII y cómo se accede?
> 4. **Precio por documento** emitido, y si hay cuota mínima mensual.
> 5. ¿Notifican estado por **webhook**, o hay que hacer polling?
> 6. ¿SLA de disponibilidad y comportamiento ante caída de la DGII?
> 7. ¿Cómo se maneja el **modo contingencia** desde su plataforma?
>
> Vamos a operar **dos RNC distintos** desde el mismo software. Gracias.

#### 6.2 — Matriz del spike POS (S0.8)

Se llena con evidencia, **no con impresiones**:

| # | Criterio | Cómo se prueba | POS nativo | POSNext |
|---|---|---|---|---|
| 1 | ¿Vende con la red cortada? | desconectar la red del compose, 5 ventas, reconectar | | |
| 2 | ¿Se extiende **sin forkear**? | agregar un custom field y verlo en pantalla | | |
| 3 | Estado del framework frontend | versión de Vue / fecha del último commit | | |
| 4 | ¿POS Invoice o Sales Invoice? | qué DocType crea al cobrar (decide dónde enganchan los `doc_events`) | | |
| 5 | Turno de caja | ¿existe POS Closing Entry y cuadra? | | |
| 6 | Escáner keyboard-wedge | escanear sin configurar nada | | |
| 7 | Licencia y obligación | GPL-3.0 vs AGPL-3.0 (AGPL contagia sirviendo como SaaS) | | |
| 8 | Costo de mantenimiento | ¿cuántas manos detrás? ¿qué pasa si el repo muere? | | |

---

### FASE 1 — Esqueleto de la app · 08/09 → 12/09

| Slice | Qué | Verificación |
|---|---|---|
| **S1.1** | `bench new-app korvexcio` · `modules.txt` con `ECF` y `Retail` · instalada en **ambos** sites | `bench --site <cada uno> list-apps` incluye `korvexcio` |
| **S1.2** | `apps.json` actualizado con el repo propio · rebuild de imagen · **el despliegue verifica el SHA, no el exit code** (regla 1: un `git status` sucio bloquea el pull en silencio) | `bench version` lista `korvexcio`; `git -C apps/korvexcio rev-parse HEAD` == el SHA que se pusheó |
| **S1.3** | CI en GitHub Actions: server tests + `ruff` (patrón `india-compliance`) **+ los 5 workflows de Secure-Vibe** — gitleaks, Semgrep, osv-scanner, Trivy sobre la imagen — **+ el test de aislamiento de S1.8 en cada push** | Workflow **verde**, link pegado. Un PR que introduce `ignore_permissions=True` **es marcado por Semgrep** |
| **S1.4** | `before_tests` que crea la company de prueba (patrón India) | `bench --site test.localhost run-tests --app korvexcio` corre sin fallar por falta de company |
| **S1.5** | Directorio `custom/*.json` con los primeros campos: `Customer.rnc`, `Customer.tipo_identificacion`. **Patrón KSA — no `export-fixtures`** | `bench migrate` y luego `frappe.get_meta("Customer").get_field("rnc")` no es `None` |
| **S1.6** | `.env.example` + secretos cargados a mano en el nodo (regla 6 del `CLAUDE.md` + regla 5 del nodo, permisos `600`). **Cierra con `/security-review`** | El `.p12` y los tokens **no** aparecen en `git log -p` |
| **S1.7** | **Roles y User Permissions por Company** (D19): perfiles `Cajero VAPELAND`, `Cajero Cafetería`, `Dueño` (las dos), `Contador` (las dos, solo lectura). El dueño puede **crear cajeros** con un rol acotado — no System Manager | Cada usuario entra y aterriza en su Company; el dueño ve el selector con las dos |
| **S1.8** | 🔴 **La barrera de aislamiento + su suite de 12 escenarios** (§7.3) — es lo que hace segura a D19. Dos piezas: **(a)** `permission_query_conditions` y `has_permission` en `hooks.py` para todo doctype de `korvexcio` con `company` — el equivalente en Frappe de `ENABLE RLS` + `FORCE`; **(b)** `validate` que **congela `company`** tras crear el documento (el `WITH CHECK`). Y la regla al `CLAUDE.md`: **`ignore_permissions=True` y `frappe.db.sql()` crudo prohibidos** | La suite de §7.3 **contra la API, no por la pantalla**, corriendo en CI. Incluye el **test de enumeración**: un `name` de la otra Company y un `name` inventado devuelven **el mismo status y el mismo mensaje**. Cierra con `/security-review` + loop de 4 auditores |
| **S1.9** | *(solo si apruebas §7.2)* **Prompt de handoff del carril B** con la frontera de archivos escrita | `docs/12-CARRIL-B.md` existe y la rama `feat/retail` está creada |

---

### FASE 2 — Módulo ECF · 15/09 → 03/10 · ⬅ CAMINO CRÍTICO

> Estructura destilada de KSA, India y México en `docs/07` §4. **No se diseña
> desde cero.** Cada slice cierra con su test.

| Slice | Qué | Verificación |
|---|---|---|
| **S2.1** | DocType **`DGII Settings`** — ⚠️ **NO Single** (cambio por D19): lleva `company` (Link, **único**), ambiente (TesteCF/CerteCF/eCF), proveedor activo, timeouts, `live_sync`. Una config por Company | Se crean **dos** registros, uno por Company, con proveedores/ambientes distintos, y cada uno resuelve el suyo |
| **S2.2** | DocType **`DGII Digital Certificate`**: `certificate` (**Attach**), `password` (**Password**, ⚠️ nunca `Data`), `company`, `valid_until` + aviso de vencimiento en `validate()` | Test: guardar y leer; **la clave no sale en texto plano por la API REST** |
| **S2.3** | DocType **`Secuencia eNCF`**: `tipo_ecf`, `desde`, `hasta`, `siguiente`, `fecha_vencimiento`, `company` + **alerta de agotamiento** | Test: agotar un rango de 3 y confirmar que alerta y bloquea |
| **S2.4** | DocType **`ECF`** — ⭐ el documento, **submittable**. Campos de `docs/07` §4: `sales_invoice` (Dynamic Link), `encf`, `track_id`, `codigo_seguridad`, `signed_xml`, `qr_url`, `estado`, `attempt_count`, `validation_messages` | Test: crear, submit, cambiar estado; el `docstatus` funciona como máquina de estados |
| **S2.5** | DocType **`ECF Integration Log`** (patrón KSA) con **secretos enmascarados** (patrón India `mask_sensitive_info`) | Test: forzar una llamada y confirmar que **el token no aparece en el log** |
| **S2.6** | **`providers/base.py`** — la interfaz: `emitir` · `consultar` · `anular`. Devuelve `Result`/`Ok`/`Err`, **no propaga excepciones desde un job** | Test unitario del contrato con un provider falso |
| **S2.7** | **`providers/<el que gane S0.9>.py`** con **backoff 2/4/8/16/32s, máx 5 intentos**. 🔴 **El cliente HTTP se resuelve por operación, desde la `Company` del documento** — nunca se construye una vez al arrancar. Si no se puede resolver, **no se envía** (regla 10, ahora crítica por D19) | Test con `responses`: 429 y 500 con conteo de reintentos y tiempos · **y un test que emite desde las dos Companies alternando y confirma que cada una usó SU credencial** |
| **S2.8** | Plantillas **Jinja2** `ecf_32.xml` y **`rfce.xml`**. ⚠️ `env.lstrip_blocks = env.trim_blocks = True` **restaurados en un `finally`** — el entorno Jinja es compartido con todo Frappe | Test: el XML generado **valida contra el XSD oficial** de la DGII |
| **S2.9** | **`hooks.py` — `doc_events`, nunca `override_doctype_class`**: `validate` (RNC ≥ RD$250,000) · `before_submit` (reservar eNCF) · `on_submit` (crear ECF) · `before_cancel` (**impedir cancelar un e-CF aceptado — se anula, no se cancela**) | Un test por cada uno. El de RD$250,000 es obligatorio (§9 global) |
| **S2.10** | **Cola asíncrona**: `frappe.enqueue(..., enqueue_after_commit=True)` ⭐ + `scheduler_events` cron `*/5` retry, `*/15` poll, `0 */6` token | Test: emitir factura, confirmar que **el POS no espera** (regla 3) y que el job corre después del commit |
| **S2.11** | DocType **`ECF Contingencia`** — patrón `ZATCA Precomputed Invoice`. **`on_trash` lanza excepción: no se puede borrar** | Test: cortar red, vender, reconectar, confirmar que usó el precomputado y que borrarlo falla |
| **S2.12** | **Print format Representación Impresa** con **QR abajo a la izquierda** (exigencia DGII) | PDF generado; el QR escanea y resuelve |
| **S2.13** | **E31** + **E34** sobre la misma maquinaria | Un e-CF de cada tipo con TrackID en TesteCF |
| **S2.14** | **Panel visible de pendientes** — regla 4: ninguna venta se pierde en silencio, y lo pendiente **no vive solo en un log** | La lista carga y muestra los pendientes de S2.11 |
| **S2.15** | **Suite completa** al estilo India: `IntegrationTestCase` + **`responses`** + **`time_machine`** + `@change_settings` | `bench run-tests --app korvexcio` **verde**, salida pegada |

**🚦 Gate de Fase 2:** un E32 emitido, su RFCE enviado, ambos con respuesta real de
TesteCF, **en los dos sites**, con cola asíncrona y contingencia probadas cortando
la red. **Más: `/secure-vibe` sobre `main` con el `00-checklist-maestro.md` en verde, y
el loop de 4 auditores completo** (§7.1) — esta fase toca datos de personas, dinero,
API keys, multi-tenant e integraciones externas a la vez.

---

### FASE 3 — Módulo Retail · 06/10 → 10/10

| Slice | Qué | Verificación |
|---|---|---|
| **S3.1** | Item Attributes del vertical: Sabor · Nicotina (mg) · Tamaño (ml) · Ohmiaje. **En la config del site, no en el código compartido** (regla 2) | Crear un template y generar variantes; el default en un site limpio está **apagado** |
| **S3.2** | **FEFO** — lotes y vencimiento con alertas a 90/60/30 días (R4 del PRD) | Test: dos lotes, confirmar que sale primero el que vence antes |
| **S3.3** | **Verificación de edad** por `Item Group`. Si se guarda cédula o fecha de nacimiento: **AES-256-GCM con IV por registro**, clave en `.env`, logs enmascarados. **Cierra con `/security-review`** | Test: el dato está cifrado en la DB; el log muestra `***-**45` |
| **S3.4** | Catálogo de **cafetería en modo mostrador** (D14) + recetas/BOM si arma combos | Vender un café que descuenta insumos del inventario |
| **S3.5** | Reportes del dueño: stock muerto 90+ · margen por categoría · rotación · venta del día (R12). ⚠️ **Filtran por `company` explícitamente**, no se confía en User Permission | Cada reporte carga con datos reales de S0.11 · **y corrido como cajero de una Company no devuelve ni una fila de la otra** |
| **S3.6** | **Dashboard consolidado del dueño** (D19): las dos Companies en una pantalla — venta del día, caja, stock por vencer, e-CF pendientes. Es lo que pidió Yedin y es lo que ningún modelo de sites separados podía dar | El dueño lo abre y ve las dos; un cajero **no ve el dashboard**, o lo ve con su Company nada más |

---

### FASE 4 — POS + hardware · 13/10 → 17/10

| Slice | Qué | Verificación |
|---|---|---|
| **S4.1** | El POS ganador de S0.8 configurado con **un POS Profile por Company** (almacén, métodos de pago, lista de precios propios). El cajero entra y **cae en el de su Company sin escoger nada** | Una venta completa en cada Company; el cajero de una **no puede** seleccionar el POS Profile de la otra |
| **S4.2** | Campos fiscales en la pantalla de caja + aviso del umbral RD$250,000. **Si gana el nativo: custom fields + `doctype_js`. Si gana POSNext: fork con rama `korvex` y `upstream` como remote.** Cierra con `/security-review` | El cajero **no puede** cerrar una venta ≥ RD$250,000 sin RNC |
| **S4.3** | Escáner **keyboard-wedge** (D8) — cero configuración | Escanear agrega el ítem al carrito sin tocar el teclado (R2) |
| **S4.4** | Impresión térmica vía **QZ Tray** (D9) con **QR del e-CF** + apertura de gaveta por RJ11 | Ticket impreso; el QR resuelve en el verificador de la DGII (R7) |
| **S4.5** | Turno de caja / POS Closing Entry con arqueo por método de pago. Cierra con `/security-review` | Abrir turno, vender, cerrar, y que cuadre |
| **S4.6** | **Contingencia end-to-end**: cortar internet, vender 10, reconectar, verificar las 10 sin duplicados (R8) | Las 10 con TrackID; `frappe.db.count` confirma cero duplicados |

---

### FASE 5 — Datos reales + certificación · 20/10 → 25/10

| Slice | Qué | Verificación |
|---|---|---|
| **S5.1** | Carga del catálogo completo (500–1,000 SKUs) por script desde el Excel del cliente | Conteo final coincide con el origen + muestreo manual de 10 |
| **S5.2** | Inventario inicial por almacén (tienda / bodega / cafetería) | Stock Balance cuadra contra el conteo físico |
| **S5.3** | Usuarios, roles y permisos (cajero ≠ dueño) | Un cajero **no** puede ver márgenes ni anular |
| **S5.4** | **Certificación como emisor ante la DGII** para **los dos RNC** — uno por `Company`, cada uno con su `.p12` y sus secuencias (CerteCF) | Sets de prueba aprobados por la DGII para **las dos Companies**, evidencia pegada |
| **S5.5** | **Manual del cajero + manual del dueño**, escritos "como si tuviera 12 años" (§7 global — es producto vendible, no adorno) | Alguien que no es Yedin sigue el manual y vende |

**🚦 Gate de Fase 5:** `/secure-vibe` sobre `main`, sin Críticos ni Altos abiertos.

---

### FASE 6 — Producción · 01/11 → 15/11

| Slice | Qué | Verificación |
|---|---|---|
| **S6.1** | Publicar los dos sites: reglas de ingress en Cloudflare Zero Trust (**config remota por token — no hay `config.yml` en el servidor**) + **Cloudflare Access delante del panel administrativo** (regla 6 del nodo) | Ambos dominios responden por HTTPS; el panel pide Access |
| **S6.2** | **Backups + prueba de restauración real.** Se verifica **contenido**, no que el archivo exista | Restaurar en un site desechable y **contar facturas**, no mirar el tamaño |
| **S6.3** | `docs/RUNBOOK.md`: se cae la DGII · se cae el internet del local · se cae el nodo · se agota una secuencia eNCF · el pull no aplicó porque el `git status` estaba sucio | Cada escenario con su comando |
| **S6.4** | **Go-live** con la contingencia probada **en el local del cliente, con su internet real** | Primera venta real con e-CF aceptado |
| **S6.5** | **Superficie de red cerrada.** MariaDB y los Redis del bench solo en `127.0.0.1` | `ss -tlnp` **en el nodo** + `curl` desde la laptop dando *connection refused*. **Leer el YAML no es prueba** — en este nodo ya pasó que el compose declaraba loopback y lo que corría, no |
| **S6.6** | **KORVIS sigue sano** después de todo | `systemctl status korvex-api` · `curl http://127.0.0.1:4000/health` · los 2 bots responden · `df -h /` bajo el 80% |

**🚦 Gate de Fase 6 — go-live:**
1. Contingencia probada en el local del cliente (S4.6 re-corrido allá).
2. **`/secure-vibe` con el `00-checklist-maestro.md` completo en verde**, y **`cyber-neo` como segunda opinión** — sin Críticos ni Altos en ninguno de los dos.
3. **La suite de aislamiento de S1.8 verde en CI**, con los 12 escenarios.
4. Cuota de disco activa y alarma del nodo sin dispararse.
5. **KORVIS intacto** (S6.6).
6. **Respondido qué pasa con la caja los días que la máquina viaje.**

---

### FASE 7 — Post-lanzamiento (después del 15/11)

Titulares, sin slices hasta cerrar el go-live: cafetería con **mesas/comandas/KDS
(URY)** · Frappe CRM · VAPELAND como tenant de **KORVIS** (checklist de
`LECCIONES-MULTI-TENANT.md`) · sincronizar catálogo ERPNext → base de conocimiento
de KORVIS · site de demo para vender · planes y precios validados contra el mercado
RD · **publicar los XSD + XML golden como repo público** (hueco #3 de `docs/07` §6 —
la carta de presentación técnica más barata que Korvex puede publicar).

---

## 7. Reglas del ejecutor — no negociables

1. **Un slice a la vez.** No se adelantan fases ni se mezclan slices.
2. **Sin evidencia no existe "funciona".** Se pega la salida real del comando (R1).
3. **Lo acordado es lo que se hace.** Si B parece mejor que A: **paras, lo dices, esperas** (R2).
4. **No te sales del slice.** Lo roto fuera del slice va a deuda técnica (R3).
5. **Cero placeholders** (R4).
6. **Si te encuentras editando `apps/erpnext/` o `apps/frappe/`, PARA.**
7. **Nunca editar código en el nodo.** Y el despliegue **verifica el SHA**, no el exit code.
8. **Nada del proyecto `korvexcio` toca los recursos de KORVIS.** Ni su Postgres, ni su Redis, ni su red, ni su compose.
9. **Secretos solo en `.env`** (`600` en el nodo), nunca en código, git, logs ni chat.
10. 🔴 **`ignore_permissions=True` y `frappe.db.sql()` crudo están PROHIBIDOS en `korvexcio/`.** Son los `SECURITY DEFINER` de Frappe: ignoran el aislamiento entero. Si un caso los necesita de verdad, se justifica por escrito y se le escribe su propio test de aislamiento.
11. **Commit al cerrar cada slice verificado.** Push solo cuando Yedin lo pida.
12. **`PROGRESO.md` se escribe por hito**, no por sesión. Cada decisión lleva su `D#` y su porqué.
13. **El POS nunca espera a la DGII.** Un slice que lo viole está mal aunque pase los tests.

---

## 7.1 Seguridad y revisiones — en qué fase entra cada una

Tres herramientas con costos muy distintos. Todas en cada slice quema el rate limit
y no encuentra más. Solo al final encuentra los bugs cuando ya son caros.

| Herramienta | Cuándo corre | Por qué ahí |
|---|---|---|
| **Secure-Vibe modo A + C** | **Siempre.** Plantillas en el repo desde S0.1; gitleaks/Semgrep/osv-scanner/Trivy en cada push desde S1.3 | *"Prevention > detection"*. Lo que se atrapa en el pre-commit no llega ni al review |
| **`/code-review`** | **Al cerrar cada slice que escribe código**, antes del commit. Nivel `medium` | Barato y rápido, con el contexto caliente. Es el que más veces corre |
| **`/security-review`** | **Slices que tocan secretos, PII, dinero o multi-tenant**: S1.6 · S1.7 · **S1.8** · **toda la Fase 2** · S3.3 · S3.5 · S4.2 · S4.5 · Fase 6 | Enfocado en la superficie de ataque del cambio |
| **`/secure-vibe`** (modo B) — ⭐ **el principal** | **Tres gates**: cierre de **Fase 2**, cierre de **Fase 5**, y **antes del go-live**. Produce `SECURITY-AUDIT-REPORT.md` y el `00-checklist-maestro.md` se usa como **release gate sí/no** | Es tuyo, está en español, y sus 13 guías cubren justo este proyecto — incluida la de RLS, que es el riesgo #1 tras D19 |
| **`cyber-neo`** | **Solo una vez: antes del go-live**, como segunda opinión | Solapa mucho con `/secure-vibe` (ambos hacen SCA, SAST, secretos, authz, cripto, supply chain). Correr las dos en cada gate es quemar rate limit sin encontrar más. **Un segundo motor sí aporta en el gate que no se puede repetir** |
| **Loop de 4 auditores** (§3 global) | **Fase 2 completa** y **S1.8 / S4.2 / S4.5** | La regla ya lo dice: solo cuando toca personas, dinero, API keys, multi-tenant o integraciones externas. **La Fase 2 es las cinco a la vez** |

**El loop:** Crítico y Alto bloquean y vuelven al editor. Medio y Bajo van a deuda
técnica. **Máximo 3 rondas** — si a la ronda 3 queda un Crítico, se para y se escala.

### Los seis puntos donde una auditoría paga sola

1. **S2.2 — el certificado.** `password` como fieldtype `Password`, no `Data`, y que
   la clave no salga por la API REST. Guatemala lo hizo mal (`docs/07` §3.5).
2. **S2.5 — los logs.** Que el token del proveedor **no** aparezca en `ECF Integration Log`.
3. 🔴 **S1.8 + S2.7 — aislamiento entre Companies.** Es **el punto más caro de D19**,
   porque el aislamiento pasó de físico a lógico. Que un e-CF de la vapería no pueda
   emitirse con las credenciales de la cafetería. **Regla 10 del `CLAUDE.md`: el
   cliente HTTP se resuelve por operación, desde la Company del documento, nunca se
   construye una vez al arrancar.** Si no se puede resolver, **no se envía**. Y los
   reportes propios filtran por `company` a mano — ERPNext ya tuvo el bug de no
   aplicar User Permission en los estados financieros (PR #44695).
4. **S3.3 — la PII.** Cédula y fecha de nacimiento cifradas, logs enmascarados.
5. **S6.5 — la superficie de red.** En este nodo ya pasó: tres apps escuchando en toda
   la LAN una semana porque *"el compose sí declara `127.0.0.1`"* — pero ese compose no
   era el que corría. **Se verifica con `ss -tlnp`, no leyendo el YAML.**
6. **Cualquier slice que toque el compose — el vecino es un banco.** Un `mem_limit` mal
   puesto o un `docker compose down` sin `-p` se lleva a KORVIS por delante.

---

## 7.3 Secure-Vibe — el sistema de aislamiento, traducido a Frappe

`github.com/yedinrumba-eng/Secure-Vibe` (MIT, propio) entra como **el marco de
seguridad del proyecto**, no como una herramienta más. Tiene tres modos y los tres
se usan, cada uno en su fase.

### Antes: la corrección honesta

La fuga de KORVIS fue de **base de conocimiento entre tenants**, no de facturas.
Tienes razón en que es otra cosa. Pero el mecanismo que falla es el mismo —
**aislamiento lógico sin una barrera que lo garantice a nivel de query** — y por eso
la guía `05-rls-tenant-isolation.md` aplica aquí completa. Su propia tabla lo dice:

> *Shared DB + tenant_id + RLS → aislamiento **medio**, RLS **CRÍTICA***
> *Shared-schema **sin RLS** = fallo catastrófico*

### El sistema, en dos capas

**Capa 1 — entre CLIENTES: física. Un site, una base de datos.**
Es más fuerte que cualquier RLS y es lo que responde tu pregunta de los 7 clientes.
La guía la llama *"database-per-tenant → aislamiento **máximo**, RLS opcional"*.
**Con 7 clientes son 7 sites.** ⚠️ Y eso es una decisión de capacidad, no de
seguridad: `docs/04` dice *"3–5 sites → 🟡 justo · 10+ → ❌ no"*. **Al cliente 3–4 se
compra el segundo nodo.**

**Capa 2 — entre NEGOCIOS del mismo cliente: lógica, y aquí sí hace falta el RLS.**
Frappe no usa RLS de Postgres (corre sobre MariaDB), pero tiene los equivalentes
exactos. La traducción:

| Secure-Vibe (Postgres/Supabase) | Equivalente real en Frappe |
|---|---|
| `ENABLE ROW LEVEL SECURITY` + `FORCE` | **`permission_query_conditions` en `hooks.py`** — inyecta el `WHERE` en **toda** list query, reporte y llamada a la API |
| Política `USING` (qué ves) | El mismo hook, filtrando por `company` |
| Política `WITH CHECK` (no puedes mover la fila a otro tenant) | **`has_permission` hook + `validate` que congela `company`** una vez creado el documento |
| `SECURITY DEFINER` que ignora RLS | 🔴 **`ignore_permissions=True`** y **`frappe.db.sql()` crudo**. Son *los* bypass de Frappe |
| Views `security definer` | 🔴 **Query Reports con SQL crudo** — exactamente el bug del PR #44695 |
| Default-deny | Role Permissions cerrados + User Permission obligatoria sobre `Company` |
| Service key nunca en el frontend | API key de sistema solo del lado del servidor |

👉 **La regla que sale de esto, y va al `CLAUDE.md` del repo:**
> **`ignore_permissions=True` y `frappe.db.sql()` crudo están PROHIBIDOS en
> `korvexcio/`.** Si un caso los necesita de verdad, se justifica por escrito en el
> PR y se le escribe un test de aislamiento propio. Sin excepción silenciosa.

### Los 3 modos, repartidos por fase

| Modo | Qué es | Dónde entra |
|---|---|---|
| **A · Prevención** | Plantillas `CLAUDE.md` / `AGENTS.md` que guían el código seguro **mientras se escribe** | **S0.1** — se inyectan en el repo con el primer commit. *"Prevention > detection"* |
| **C · Automatización** | 5 workflows de GitHub Actions: **gitleaks** (secretos), **Semgrep** (SAST), **osv-scanner** (dependencias), **Trivy** (contenedores) + `pre-commit` | **S0.1** (gitleaks en pre-commit, hoy) y **S1.3** (el CI completo). Trivy apunta a **la imagen de Frappe**, que es upstream y no auditamos nosotros |
| **B · Auditoría** | La skill `/secure-vibe` → `SECURITY-AUDIT-REPORT.md`, con el `00-checklist-maestro.md` como **release gate sí/no** | **Gates**: cierre de Fase 2 · cierre de Fase 5 · **antes del go-live** |

⚠️ **La skill no está instalada** — no aparece en `~/.claude/skills/` ni el repo está
clonado. Es **S0.1b**: clonar Secure-Vibe e instalar `skill/secure-vibe/`.

### Las 12 guías que aplican (de 13)

`01` secretos → el `.p12` y los tokens (S1.6, S2.2) · `02` validación de entrada y
`03` inyección → el XML y la carga de catálogo · `04` authz/IDOR → S1.7 ·
**`05` RLS/tenant → S1.8, el núcleo** · `06` rate limiting → S2.7 y §11 global ·
`08` headers/CORS/CSRF → S6.1 al publicar · `09` file uploads → **el `.p12` como
`Attach`** · `10` supply chain y `11` CI/containers → S1.3 y S0.5 ·
`12` logging → S2.5 · `13` webhooks multi-tenant → el webhook del proveedor de e-CF.

**No aplica:** `07` prompt-injection/LLM — KORVEXCIO no tiene LLM. Eso es KORVIS.

### El test de aislamiento (S1.8), con la metodología de la guía

Lo más valioso que aporta el repo no es la lista de vulnerabilidades: es **cómo se
prueba**. Dos reglas de su checklist de 15 escenarios que cambian el test:

1. **Se prueba contra la API directa, NO por la pantalla.** La UI esconde el botón;
   la API no. Todo el test va por `/api/resource/...` y `frappe.client.*`.
2. **Test de enumeración** — *"ID inexistente vs ID que pertenece a B → status y
   mensaje idénticos"*. Si un `name` de la otra Company devuelve `PermissionError` y
   uno inventado devuelve `DoesNotExistError`, **acabas de filtrar qué existe.**

Escenarios adaptados a Frappe, todos automatizados en la suite:

| # | Escenario | Esperado |
|---|---|---|
| 1 | `GET /api/resource/Sales Invoice/<name de la otra Company>` | denegado |
| 2 | `frappe.get_list("Sales Invoice")` como cajero A | cero filas de B |
| 3 | Crear documento forzando `company` = la otra | rechazado en `validate` |
| 4 | `PUT` sobre un documento de la otra Company | denegado, sin efecto |
| 5 | **Cambiar `company` de un documento propio a la otra** | bloqueado (`WITH CHECK`) |
| 6 | Cancelar/borrar documento de la otra Company | cero filas afectadas |
| 7 | Cada **reporte propio** (S3.5) corrido como cajero A | cero filas de B |
| 8 | Cada método `@frappe.whitelist()` de `korvexcio` | respeta permisos |
| 9 | **Enumeración**: `name` inexistente vs `name` de B | **mismo status, mismo mensaje** |
| 10 | Petición sin autenticar | vacío, sin filtrar el error |
| 11 | Descargar el `.p12` de la otra Company (`/private/files/`) | denegado |
| 12 | Emitir e-CF de A y confirmar **qué credencial se usó** | la de A, siempre |

**Corre en CI en cada push** (S1.3), no solo en los gates. Un aislamiento que se
prueba una vez no está probado.

---

## 7.2 Dos carriles en paralelo — cómo se adelanta sin chocar

El camino crítico es la Fase 2. Lo que **no depende de ella** puede correr al mismo
tiempo y recupera ~1 semana de colchón antes del 15/11.

⚠️ **Es un cambio al modelo acordado** (§4.2 global: *un slice a la vez*), así que lo
propongo, no lo aplico. **Necesita tu OK explícito.**

| | **Carril A — crítico** | **Carril B — paralelo** |
|---|---|---|
| **Quién** | Claude Code (editor principal) | Codex u otra sesión |
| **Qué** | **Fase 2 completa** (S2.1 → S2.15) | Fase 3 · S4.3 (escáner) · S4.4 (QZ Tray) · manuales de S5.5 · `RUNBOOK.md` |
| **Toca SOLO** | `korvexcio/ecf/**` · `custom/` fiscales · `hooks.py` | `korvexcio/retail/**` · `scripts/` · `docs/` |
| **Rama** | `feat/ecf` | `feat/retail` |
| **Depende de** | Fase 1 | Fase 1 |

**Lo que hace esto seguro es la frontera de archivos, no la buena voluntad:**

1. **`hooks.py` lo toca SOLO el carril A.** Es el único archivo compartido de verdad.
   Si B necesita un hook, lo **pide por nota**, no lo escribe.
2. **Ningún carril toca `korvexcio/` fuera de su módulo.**
3. **Merge a `main` solo en los gates de fase**, no continuo.
4. **El carril B no toca nada fiscal ni el compose del nodo.** Es el carril de bajo
   riesgo a propósito — por eso puede ir en otra sesión sin el loop de 4 auditores.
5. **`/code-review` corre en los dos carriles.** `cyber-neo` corre sobre `main` después
   del merge, no por rama.

**Gana:** la Fase 3 se colapsa dentro de la ventana de la Fase 2. Desarrollo terminado
~17/10 en vez de 25/10 — **una semana entera de colchón**, que es exactamente lo que
falta cuando algo sale mal.

**Cuesta:** Codex arranca sin contexto. Hay que darle un prompt de handoff apuntando a
`CLAUDE.md`, `docs/06`, `docs/07` §4 y a los slices de Fase 3 — **más el `AGENTS.md` de
Secure-Vibe**, que es justo la plantilla para Cursor/Copilot/Codex. Eso es **S1.9**, y
lo escribo si apruebas el carril.

---

## 8. Archivos que se crean o se tocan

| Archivo | Cuándo | Qué |
|---|---|---|
| `.gitignore` · `.env.example` | S0.1 | Nuevos |
| `HANDOFF.md` | S0.1 y al cerrar cada fase | **Se corrige** la ruta `C:\PROYECTOS\VAPELAND` + tabla de confianza con lo verificado |
| `docs/09-PROVEEDORES-ECF.md` | S0.3 | Nuevo — respuestas de proveedores |
| `docker/` · `apps.json` | S0.5, S1.2 | Nuevos — compose propio con `name:`, red, `mem_limit`, loopback |
| `docs/13-VERSION-FRAPPE.md` | S0.5 | Nuevo — **D2 cerrada con evidencia** |
| `docs/10-SPIKE-POS.md` | S0.8 | Nuevo — la matriz llena |
| `docs/11-SPIKE-FISCAL.md` | S0.9 | Nuevo — **el TrackID** |
| `docs/12-CARRIL-B.md` | S1.9 | Nuevo — *solo si se aprueba §7.2* |
| `plantillas/ES/CLAUDE.md` + `AGENTS.md` de Secure-Vibe | S0.1b | **Se copian al repo** — modo A, prevención |
| `.pre-commit-config.yaml` | S0.1b | Nuevo — gitleaks + los scripts de Secure-Vibe |
| `.github/workflows/` | S1.3 | Nuevos — los 5 de Secure-Vibe + server tests + **el test de aislamiento** |
| `SECURITY-AUDIT-REPORT.md` | Gates de Fase 2, 5 y go-live | Lo genera `/secure-vibe` |
| `PROGRESO.md` | S0.12 y al cerrar cada fase | **Se actualiza** — ya existe, 11 entradas |
| `TECH_STACK.md` | S0.12 | **Se actualiza** — D10–D18, cierre de D2, corrección de D3, derogación de D4 |
| `docs/07-ARQUITECTURA-REFERENCIA.md` | S0.12 | **Se actualiza** — quitar el aviso "sin verificar" de los 4 ⭐ |
| `docs/04-ARQUITECTURA.md` | S0.12 | **Se actualiza** — hosting con números medidos **y la tabla de multi-tenancy reescrita por D19**: un site por cliente, una Company por negocio |
| `CLAUDE.md` (del repo) | S0.12 | **Se actualiza** — la regla 10 sube a crítica y la nomenclatura de sites cambia por D19 |
| `_KORVEX-OPS/data/korvex.json` | S0.12 | Estado ⚪ → 🔵 |
| `SERVER PROJECTS/MASTERGUIDE.md` | S0.12, S6.1 | **Se actualiza** — KORVEXCIO como segundo inquilino, con hostnames y cuota de disco |
| `korvexcio/**` | Fases 1–4 | La app |
| `docs/RUNBOOK.md` | S6.3 | Nuevo |
| `docs/08-BLUEPRINT.md` | S0.12 | Nuevo — este plan, versionado dentro del repo |

---

## 9. Verificación end-to-end

El sistema está listo cuando esto corre limpio **en los dos sites**:

```bash
# 1. El site responde, tiene la app y sus dos Companies
bench --site korvexcio.korvexdev.cc list-apps   # frappe, erpnext, korvexcio
bench --site demo.korvexdev.cc      list-apps   # el modelo por cliente sigue vivo

# 2. Los tests pasan, INCLUIDO el de aislamiento entre Companies (S1.8)
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio

# 3. Cada login aterriza donde debe
#    cajero vapería -> solo vapería · cajero cafetería -> solo cafetería
#    dueño -> las dos + dashboard consolidado

# 4. Una venta real emite e-CF con la credencial de SU Company, devuelve TrackID,
#    y no bloquea la caja

# 5. Contingencia: red abajo, 10 ventas, red arriba, 10 TrackIDs, 0 duplicados

# 6. El backup restaura CONTENIDO, no solo peso
bench --site scratch.localhost restore <dump>   # contar facturas, no mirar el tamaño

# 7. Superficie de red cerrada — desde el nodo Y desde la laptop
ss -tlnp | grep -E '3306|6379'                  # todo en 127.0.0.1

# 8. EL VECINO SIGUE VIVO
systemctl status korvex-api && curl -s http://127.0.0.1:4000/health
df -h /                                          # bajo el 80%
```

---

## 10. Riesgos abiertos y qué los mitiga

| Riesgo | Severidad | Mitigación |
|---|---|---|
| **RFCE no existe por ninguna vía** | 🔴 | S0.3 en paralelo + plan B de portar desde `dgii-ecf` (MIT). Si las tres fallan: **parar y escalar** |
| **El cliente no tiene RNC** | 🔴 | En movimiento. No bloquea desarrollo; **bloquea certificación**. Empujarlo esta semana |
| **Certificado digital: 3–10 días hábiles × 2 RNC** | 🔴 | Arranca hoy, en paralelo con Fase 0 |
| **Romper KORVIS** — un banco y 2 bots en vivo en la misma máquina | 🔴 | Proyecto de compose y red propios · `mem_limit` con tope 6 GB · nunca reusar Postgres/Redis de KORVIS · **S6.6 verifica que sigue sano en cada gate** |
| 🔴 **Fuga entre Companies** — D19 cambió el aislamiento de físico a lógico | 🔴 | **S1.8**: `permission_query_conditions` + `has_permission` + `company` congelada, con la suite de 12 escenarios contra la API corriendo **en CI en cada push** (§7.3) · **S2.7** credencial resuelta por operación · reportes propios que filtran a mano · **`ignore_permissions=True` prohibido y detectado por Semgrep**. **Y la línea que no se cruza: cliente 2 = site propio.** Evidencia de que el riesgo es real: PR #44695 y el issue #43652 cerrado como *not planned* |
| **7 clientes en el nodo** | 🟠 | **No es problema de seguridad, es de capacidad.** 7 clientes = 7 sites; `docs/04` dice *3–5 sites es "justo", 10+ es "no"*. **Al cliente 3–4 se compra el segundo nodo o VPS** — ya está como fecha de revisión en §5.1 |
| ~~DEV no tiene ruta al nodo~~ | ✅ **RESUELTO** | Tailscale instalado y verificado; `ssh` al nodo funciona. Queda el `~/.ssh/config` con la IP vieja — S0.2, un renglón |
| 🔴 **La mini PC viaja con Yedin** | 🔴 | **Sin mitigación técnica.** Se decide antes del go-live: deja de viajar · se muda a VPS · o se opera en contingencia declarándola por la OFV. **Decisión de Yedin** |
| **El disco es el techo** — 72.4 GB libres, compartidos con KORVIS, GlitchTip, Plausible y los backups | 🟠 | `docker builder prune -f` antes de instalar (S0.4) · cuota y retención propias (S0.10) · la alarma del nodo ya avisa al 80% |
| **`git status` sucio en el nodo bloquea el pull en silencio** | 🟠 | El despliegue **verifica el SHA**, no el exit code (S1.2 + regla 7) |
| **IPv4 caído con todo lo demás funcionando** | 🟠 | `curl https://github.com` → 200 en el checklist previo (S0.4). Un `000` es el síntoma |
| **POSNext tiene 1 mantenedor** | 🟠 | S0.8 decide con criterio técnico. Si gana, el fork es tuyo para siempre — y eso pesa en la matriz |
| **Cada cambio de XSD de la DGII es un ticket tuyo** | 🟠 | Con proveedor certificado buena parte la absorbe él. Argumento fuerte para el plan A |
| **Disco del nodo sin cifrar** + POS que puede guardar cédulas | 🟠 | La PII va cifrada a nivel de aplicación (S3.3), no depende de LUKS. Si la máquina viaja, sube a 🔴 |
| **ISC 55% de la Ley 30-26** | 🟡 | Va **dentro del costo**, no como línea al consumidor. Confirmar con el contador antes de modelar impuestos |

---

## 11. Preguntas abiertas que no bloquean arrancar

Van a la reunión con el cliente (`docs/05`), **no detienen la Fase 0**: ¿RNC de
persona física o SRL/EIRL? · ¿clasificación DGII — pequeño, micro, no clasificado?
(decide 15/11 vs 1/11) · ¿RST? · ¿contador? · ¿fecha real de apertura? · ¿el
catálogo está en Excel? · ¿códigos de barras del fabricante? · ¿venta fraccionada
por peso? · ¿fiado? · ¿medios de pago y adquirente? · ¿cómo es el internet del local?
