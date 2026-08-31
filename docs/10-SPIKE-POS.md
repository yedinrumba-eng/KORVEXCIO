# 10 — Spike POS (S0.8)

> Ejecutado el 31/08/2026 sobre `korvex-node1`, dentro del contenedor
> `korvexcio-backend-1` (la imagen `korvexcio:16` que ya está de pie desde
> S0.5 — no se instaló nada nuevo, no se tocó nada de KORVIS).

## Metodología — y su límite honesto

Los 8 criterios de `docs/08-BLUEPRINT.md` §6.2 se respondieron **leyendo el
código fuente real** de las dos opciones dentro del contenedor (`grep`/`find`
sobre `apps/erpnext` y `apps/pos_next`), no adivinando ni copiando lo que
dice cada README.

**Lo que NO se hizo, y hay que decirlo (R1):** la prueba dura del plan —
"desconectar la red del compose, 5 ventas, reconectar" — **requiere abrir la
UI del POS en un navegador contra el sitio**, y el frontend está en
`127.0.0.1:8080` del nodo, en loopback puro. Esta sesión no tenía un túnel
armado ni el `hosts` local apuntando a `korvexcio.korvexdev.cc`, y montar
eso no es gratis en tiempo. El criterio 1 de la tabla se responde con
**evidencia de código** (qué mecanismo de offline existe o no existe en el
repo), no con una venta real hecha con la red cortada. Se anota así, sin
maquillar.

## La matriz

| # | Criterio | POS nativo (ERPNext) | POSNext | Evidencia |
|---|---|---|---|---|
| 1 | ¿Vende con la red cortada? | 🔴 **Sin mecanismo de offline en el código.** Cero archivos de service worker, IndexedDB o cola de sync bajo `erpnext/selling/page/point_of_sale/` | 🟢 **Arquitectura de offline real y completa**: `POS/src/workers/offline.worker.js`, `utils/offline/{db,sync,cache,items,workerClient,offlineState}.js`, store dedicado `stores/posSync.js`, diálogo de facturas offline (`OfflineInvoicesDialog.vue`), y un DocType de servidor `Offline Invoice Sync` para reconciliar lo que llega tarde | `grep -rli offline apps/pos_next/POS/src` → 9+ archivos reales de arquitectura, no menciones sueltas. Mismo grep contra `erpnext/selling/page/point_of_sale/` → cero resultados |
| 2 | ¿Se extiende sin forkear? | 🟢 Doctype/hooks/custom fields estándar de Frappe, cero fork necesario | 🔴 **Ya está decidido que se forkea** (`CLAUDE.md` §1, excepción única) — necesita campos fiscales dominicanos por dentro | Precedente ya escrito en el repo antes de este spike |
| 3 | Framework frontend | 🟡 **Página clásica de Frappe Desk** — puro `.js` (`point_of_sale.js`, `pos_controller.js`, etc.), **cero componentes `.vue`** | 🟢 **Vue 3.5.13** (Composition API), SPA independiente con Vite, PWA instalable (`usePWAInstall.js`, `InstallAppBadge.vue`) | `find .../point_of_sale -iname "*.vue" \| wc -l` → `0`. `grep vue apps/pos_next/POS/package.json` → `"vue": "3.5.13"` |
| 4 | ¿POS Invoice o Sales Invoice? | **POS Invoice** — doctype propio, ligero, que se consolida después vía `POS Invoice Merge Log` | **Sales Invoice** directo — `pos_next/overrides/sales_invoice.py` + doctype `Sales Invoice Reference` | `grep -rl "POS Invoice" apps/pos_next --include=*.py` → **cero archivos**. `grep -rl "Sales Invoice" ...` → 7 archivos, incluido un `overrides/sales_invoice.py` dedicado |
| 5 | Turno de caja | 🟢 `POS Opening Entry` / `POS Closing Entry`, con `closing_amount`/reconciliación | 🟢 `POS Opening Shift` / `POS Closing Shift`, mismo patrón de reconciliación | Ambos doctypes con campos de cierre/reconciliación confirmados por `grep` directo en sus `.json` |
| 6 | Escáner keyboard-wedge | 🟢 `pos_item_selector.js` maneja barcode | 🟢 Manejo de barcode presente en `utils/offline/items.js` y afines | `grep -li barcode` en ambos lados, resultado positivo |
| 7 | Licencia | **GPL-3.0** (parte de `erpnext`, ya verificado en Fase 0 §2) | **AGPL-3.0** en el archivo `LICENSE` real — 🟡 pero **el `package.json` dice `"license": "ISC"`**, una inconsistencia de metadata que no cambia la licencia real (gana el archivo `LICENSE`) pero sí es una señal más de mantenimiento descuidado | `head apps/pos_next/LICENSE` → texto AGPLv3 completo. `grep license apps/pos_next/package.json` → `"ISC"` |
| 8 | Costo de mantenimiento | Lo mantiene Frappe Technologies, el core del framework | Repo con pocas estrellas/forks (dato externo ya verificado en `TECH_STACK.md` antes de este spike — `DeeloaSociety/posnext`, 2★/1 fork). **Si gana, el fork es tuyo para siempre** (ya anotado en riesgos) | Ya documentado, no repetido aquí |

## Lo que este spike cambia — y por qué se dice de frente, no se aplica en silencio

**D16 decía:** "sesgo declarado hacia el nativo... la cola offline la
escribes tú de todos modos, así que el offline de POSNext no compra nada."

**Lo que el código real dice:** eso es **falso en la parte que importa**.
POSNext no solo *dice* tener offline en su descripción — tiene un Worker,
una capa de `db`/`cache`/`sync` y un store dedicado, todo ya escrito. El
nativo tiene **cero** de eso: si se elige nativo, alguien construye la cola
offline completa desde cero, no solo "el pedazo de e-CF" que D16 asumía.
Y de regalo, POSNext ya factura contra `Sales Invoice` — el doctype donde
previsiblemente van a vivir los hooks de `ecf` (S2.9) — mientras que el
nativo usa `POS Invoice`, que se consolida en `Sales Invoice` **después**,
con un retraso que complica el momento exacto de emitir el e-CF.

**Esto no se decidió por Claude en silencio.** El propio blueprint pone a
S0.8 como el punto donde el sesgo declarado de D16 se confirma o se revierte
con evidencia — es su trabajo, no un cambio de plan por fuera del proceso.
Lo que sí queda pendiente de tu OK explícito es **actuar** sobre esto (fijar
D16 como "POSNext" en vez de "diferido con sesgo a nativo").

## Veredicto

**POSNext, con la prueba en vivo todavía pendiente.** La evidencia de código
es contundente en el punto que más pesa (offline real vs. cero offline) y en
el punto que más ahorra trabajo futuro (`Sales Invoice` directo). Lo que
falta antes de firmarlo del todo: la prueba dura de "cortar red, 5 ventas,
reconectar" **contra la UI real**, no solo contra el código — eso necesita
15-20 minutos con un túnel SSH + una entrada en el `hosts` local, y no se
hizo en esta sesión por presupuesto de tiempo, no por imposibilidad.

**Recomendación:** cerrar D16 hacia **POSNext** con esta evidencia, y dejar
la prueba en vivo (offline real, 5 ventas, reconectar) como el primer smoke
test de **S4.1** en vez de repetir el spike — para entonces ya hay POS
Profile por Company y tiene sentido probarlo con datos reales, no con el
catálogo de prueba de S0.11.
